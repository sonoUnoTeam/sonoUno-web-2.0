# -*- coding: utf-8 -*-
"""
Vistas para la aplicación de sonificación de imágenes.
Inspirado en la arquitectura de la app LHC.
"""

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.http import require_http_methods
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import uuid
import time
import json

from .services import ImageSonificationVideoService, ImageCacheService, ImageSonificationInfoService
from .validators import ImageRateLimiter, ImageProcessingValidator

# Configurar logging
logger = logging.getLogger('imagesonif')

def index(request):
    """Vista principal de sonificación de imágenes."""
    context = {}
    return render(request, "imagesonif/index.html", context)


def get_client_ip(request):
    """Obtiene la IP del cliente de forma segura."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@method_decorator(csrf_exempt, name='dispatch')
class ImageSonificationView(View):
    """Vista principal para procesamiento de sonificación de imágenes."""
    
    def __init__(self):
        super().__init__()
        self.video_service = ImageSonificationVideoService()
        self.cache_service = ImageCacheService()
    
    def post(self, request):
        """
        Maneja requests POST para sonificación de imágenes.
        
        Args:
            request: Request de Django con imagen y configuraciones
            
        Returns:
            JsonResponse: Respuesta con video, audio e información
        """
        # Generar ID único para este request
        request_id = str(uuid.uuid4())
        client_ip = get_client_ip(request)
        start_time = time.time()
        
        # Log detallado para debugging
        logger.info(f"POST received - FILES: {list(request.FILES.keys())}, POST: {list(request.POST.keys())}, Content-Type: {request.content_type}")
        
        try:
            # Control de rate limiting
            if not ImageRateLimiter.check_rate_limit(client_ip):
                return JsonResponse({
                    'success': False,
                    'error': 'Demasiados requests concurrentes. Por favor espere un momento.',
                    'rate_limit_exceeded': True
                }, status=429)
            
            # Registrar request
            ImageRateLimiter.add_request(client_ip, request_id)
            
            # Validar que se subió una imagen
            if 'image' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'No se encontró archivo de imagen'
                }, status=400)
            
            image_file = request.FILES['image']
            
            # Usar configuraciones fijas por defecto
            validated_settings = {
                'min_freq': 500,
                'max_freq': 1500,
                'time_base': 0.09,  # Aumentado para mayor duración
                'volume': 0.85,  # Actualizado para coincidir con services.py
                'waveform': 'celesta'
            }
            
            # Procesar sonificación
            video_base64, audio_base64, sonification_info, status_message = \
                self.video_service.process_image_sonification(
                    image_file,
                    validated_settings,
                    use_cache=True
                )
            
            processing_time = time.time() - start_time
            
            if video_base64 is None or audio_base64 is None:
                # Log error
                self._log_sonification_attempt(
                    client_ip, None, processing_time, False, status_message
                )
                
                return JsonResponse({
                    'success': False,
                    'error': status_message or 'Error procesando sonificación'
                }, status=500)
            
            # Preparar respuesta exitosa
            response_data = {
                'success': True,
                'video_base64': video_base64,
                'audio_base64': audio_base64,
                'sonification_info': sonification_info,
                'status_message': status_message,
                'processing_time': round(processing_time, 2)
            }
            
            # Log exitoso
            self._log_sonification_attempt(
                client_ip, 
                sonification_info.get('image_dimensions'),
                processing_time, 
                True,  # success = True
                status_message
            )
            
            return JsonResponse(response_data)
            
        except ValidationError as e:
            processing_time = time.time() - start_time
            self._log_sonification_attempt(
                client_ip, None, processing_time, False, str(e)
            )
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
        except PermissionDenied as e:
            processing_time = time.time() - start_time
            self._log_sonification_attempt(
                client_ip, None, processing_time, False, str(e)
            )
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=403)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error inesperado en ImageSonificationView: {e}")
            self._log_sonification_attempt(
                client_ip, None, processing_time, False, str(e)
            )
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)
            
        finally:
            # Limpiar request del rate limiter
            ImageRateLimiter.remove_request(request_id)
    
    def _log_sonification_attempt(self, client_ip: str, image_dimensions, 
                                 processing_time: float, success: bool, 
                                 error_message: str = None):
        """Log del intento de sonificación para estadísticas."""
        try:
            # Preparar información para el log
            dimensions_str = str(image_dimensions) if image_dimensions else 'Unknown'
            
            # Log básico del resultado
            if success:
                logger.info(
                    f"Sonificación completada exitosamente - "
                    f"IP: {client_ip}, "
                    f"Dimensiones: {dimensions_str}, "
                    f"Tiempo: {processing_time:.2f}s"
                )
            else:
                logger.error(
                    f"Error en sonificación - "
                    f"IP: {client_ip}, "
                    f"Dimensiones: {dimensions_str}, "
                    f"Tiempo: {processing_time:.2f}s, "
                    f"Error: {error_message}"
                )
        except Exception as e:
            logger.error(f"Error registrando log de sonificación: {e}")


@require_http_methods(["GET"])
def cache_stats(request):
    """
    Vista para mostrar estadísticas del caché (solo en DEBUG).
    """
    if not settings.DEBUG:
        return HttpResponse("No disponible en producción", status=403)
    
    try:
        cache_service = ImageCacheService()
        stats = cache_service.get_cache_stats()
        
        # Limpiar caché si se solicita
        cache_cleared = False
        if request.GET.get('clear') == 'true':
            cache_cleared = cache_service.clear_cache()
        
        context = {
            'stats': stats,
            'cache_cleared': cache_cleared,
        }
        
        return render(request, 'imagesonif/cache_stats.html', context)
        
    except Exception as e:
        logger.error(f"Error en cache_stats de imagesonif: {e}")
        return HttpResponse(f"Error obteniendo estadísticas: {str(e)}", status=500)


@require_http_methods(["GET"])
def rate_limit_stats(request):
    """Vista para mostrar estadísticas de rate limiting (solo en DEBUG)."""
    if not settings.DEBUG:
        return HttpResponse("No disponible en producción", status=403)
    
    try:
        client_ip = get_client_ip(request)
        stats = ImageRateLimiter.get_stats(client_ip)
        
        return JsonResponse({
            'client_ip': client_ip,
            'rate_limit_stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error en rate_limit_stats: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def help_page(request):
    """Página de ayuda sobre sonificación de imágenes."""
    return render(request, 'imagesonif/help.html')
