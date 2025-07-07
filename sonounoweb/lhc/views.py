from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views import View
import logging
import uuid
import base64
import os
import tempfile

from .services import LHCVideoService, LHCCacheService, LHCEventService
from .validators import LHCSecurityValidator, LHCRateLimiter
from utils.lhc_lib.lhc_web import get_total_events

# Configurar logging
logger = logging.getLogger(__name__)

def index(request):
    """Vista principal de LHC."""
    return render(request, "lhc/index.html")


def get_client_ip(request):
    """Obtiene la IP del cliente de forma segura."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LHCEventView(View):
    """Vista principal para eventos LHC."""
    
    def __init__(self):
        super().__init__()
        self.video_service = LHCVideoService()
        self.cache_service = LHCCacheService()
        self.event_service = LHCEventService()
    
    def get(self, request, file_name):
        """
        Maneja requests GET para visualización de eventos LHC.
        
        Args:
            request: Request de Django
            file_name: Nombre del archivo de datos LHC
            
        Returns:
            HttpResponse: Respuesta renderizada
        """
        # Generar ID único para este request
        request_id = str(uuid.uuid4())
        client_ip = get_client_ip(request)
        
        try:
            # Control de rate limiting
            if not LHCRateLimiter.check_rate_limit(client_ip):
                messages.error(
                    request, 
                    "Demasiados requests concurrentes. Por favor espere un momento."
                )
                return render(request, 'lhc/index.html', {'error': True})
            
            # Registrar request
            LHCRateLimiter.add_request(client_ip, request_id)
            
            # Validar y obtener parámetros
            event_index = self._get_validated_event_index(request)
            
            # Validar nombre de archivo
            try:
                validated_file_name = LHCSecurityValidator.validate_file_name(file_name)
            except (ValidationError, PermissionDenied) as e:
                logger.warning(f"Archivo no válido {file_name}: {e}")
                messages.error(request, f"Archivo no válido: {str(e)}")
                return render(request, 'lhc/index.html', {'error': True})
            
            # Obtener total de eventos para validación
            try:
                total_events = get_total_events(validated_file_name)
                if total_events == 0:
                    messages.error(request, "No se encontraron eventos en el archivo")
                    return render(request, 'lhc/index.html', {'error': True})
            except Exception as e:
                logger.error(f"Error obteniendo total de eventos: {e}")
                messages.error(request, "Error accediendo al archivo de datos")
                return render(request, 'lhc/index.html', {'error': True})
            
            # Validar índice del evento
            validated_event_index = LHCSecurityValidator.validate_event_index(
                event_index, total_events
            )
            
            # Generar o obtener video
            video_base64, event_info, status_message = self.video_service.generate_lhc_video(
                validated_file_name, 
                validated_event_index,
                use_cache=True
            )
            
            if video_base64 is None:
                logger.error(f"Error generando video: {status_message}")
                messages.error(request, f"Error generando visualización: {status_message}")
                return render(request, 'lhc/index.html', {'error': True})
            
            # Preparar contexto
            context = self._prepare_context(
                video_base64=video_base64,
                file_name=validated_file_name,
                event_info=event_info,
                current_event=validated_event_index,
                total_events=total_events
            )
            
            # Log exitoso
            logger.info(
                f"Video LHC generado exitosamente - "
                f"Archivo: {validated_file_name}, "
                f"Evento: {validated_event_index}/{total_events}, "
                f"Status: {status_message}"
            )
            
            return render(request, 'lhc/index.html', context)
            
        except Exception as e:
            logger.error(f"Error inesperado en LHCEventView: {e}")
            messages.error(request, "Error interno del servidor")
            return render(request, 'lhc/index.html', {'error': True})
            
        finally:
            # Limpiar request del rate limiter
            LHCRateLimiter.remove_request(request_id)
    
    def _get_validated_event_index(self, request):
        """
        Obtiene y valida el índice del evento desde los parámetros GET.
        
        Args:
            request: Request de Django
            
        Returns:
            int: Índice del evento validado (1-based)
        """
        event_index = request.GET.get('event', 1)
        try:
            return int(event_index)
        except (ValueError, TypeError):
            logger.warning(f"Índice de evento inválido: {event_index}")
            return 1
    
    def _prepare_context(self, video_base64, file_name, event_info, current_event, total_events):
        """
        Prepara el contexto para el template.
        
        Args:
            video_base64: Video en base64
            file_name: Nombre del archivo
            event_info: Información del evento
            current_event: Evento actual
            total_events: Total de eventos
            
        Returns:
            dict: Contexto para el template
        """
        navigation = self.event_service.get_event_navigation(current_event, total_events)
        
        return {
            'video_base64': video_base64,
            'file_name': file_name,
            'event_info': event_info,
            'current_event': current_event,
            'total_events': total_events,
            'prev_event': navigation['prev_event'],
            'next_event': navigation['next_event'],
            'cache_stats': self.cache_service.get_cache_stats() if settings.DEBUG else None
        }


@require_http_methods(["GET"])
def cache_stats(request):
    """
    Vista para mostrar estadísticas del caché (solo en DEBUG).
    """
    if not settings.DEBUG:
        return HttpResponse("No disponible en producción", status=403)
    
    try:
        cache_service = LHCCacheService()
        stats = cache_service.get_cache_stats()
        
        # Limpiar caché si se solicita
        cache_cleared = False
        if request.GET.get('clear') == 'true':
            cache_cleared = cache_service.clear_cache()
        
        context = {
            'stats': stats,
            'cache_cleared': cache_cleared,
        }
        
        return render(request, 'lhc/cache_stats.html', context)
        
    except Exception as e:
        logger.error(f"Error en cache_stats: {e}")
        return HttpResponse(f"Error obteniendo estadísticas: {str(e)}", status=500)

# ========================================
# APIs PARA EXTRACCIÓN DE MEDIOS
# ========================================

@require_http_methods(["POST"])
def extract_audio_from_video_api(request):
    """
    API para extraer audio de un video en base64.
    Solo disponible en modo DEBUG para desarrollo.
    """
    if not settings.DEBUG:
        return JsonResponse({'error': 'No disponible en producción'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        video_base64 = data.get('video_base64')
        
        if not video_base64:
            return JsonResponse({'error': 'video_base64 requerido'}, status=400)
        
        # Usar servicio para extraer audio
        video_service = LHCVideoService()
        audio_data = video_service._extract_audio_from_video_base64(video_base64)
        
        if audio_data:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return JsonResponse({'audio_base64': audio_base64})
        else:
            return JsonResponse({'error': 'No se pudo extraer audio'}, status=500)
            
    except Exception as e:
        logger.error(f"Error en extract_audio_from_video_api: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def extract_image_from_video_api(request):
    """
    API para extraer imagen de un video en base64.
    Solo disponible en modo DEBUG para desarrollo.
    """
    if not settings.DEBUG:
        return JsonResponse({'error': 'No disponible en producción'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        video_base64 = data.get('video_base64')
        
        if not video_base64:
            return JsonResponse({'error': 'video_base64 requerido'}, status=400)
        
        # Usar servicio para extraer imagen
        video_service = LHCVideoService()
        image_base64 = video_service._extract_image_from_video_base64(video_base64)
        
        if image_base64:
            return JsonResponse({'image_base64': image_base64})
        else:
            return JsonResponse({'error': 'No se pudo extraer imagen'}, status=500)
            
    except Exception as e:
        logger.error(f"Error en extract_image_from_video_api: {e}")
        return JsonResponse({'error': str(e)}, status=500)