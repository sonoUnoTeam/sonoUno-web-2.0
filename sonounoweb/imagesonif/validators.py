# -*- coding: utf-8 -*-
"""
Validadores de seguridad para la aplicación de sonificación de imágenes.
Inspirado en la arquitectura de la app LHC.
"""

import os
import logging
from typing import Dict, Any
from django.core.exceptions import ValidationError, PermissionDenied
from django.conf import settings
from PIL import Image, ImageFile
import time
from collections import defaultdict, deque

# Configurar logging
logger = logging.getLogger('imagesonif')

# Configuración para manejar imágenes truncadas
ImageFile.LOAD_TRUNCATED_IMAGES = True

class ImageSecurityValidator:
    """Validador de seguridad para imágenes y operaciones de sonificación."""
    
    # Extensiones de imagen permitidas
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    
    # Tipos MIME permitidos
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/bmp', 
        'image/gif', 'image/tiff', 'image/webp'
    }
    
    # Límites de seguridad
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_IMAGE_DIMENSIONS = (4000, 4000)  # 4000x4000 píxeles máximo
    MIN_IMAGE_DIMENSIONS = (10, 10)     # 10x10 píxeles mínimo
    MAX_CACHE_SIZE = 500 * 1024 * 1024  # 500MB de caché máximo
    
    @classmethod
    def validate_uploaded_image(cls, image_file) -> Image.Image:
        """
        Valida una imagen subida por el usuario.
        
        Args:
            image_file: Archivo de imagen subido
            
        Returns:
            Image.Image: Imagen PIL validada
            
        Raises:
            ValidationError: Si la imagen no es válida
            PermissionDenied: Si la imagen viola políticas de seguridad
        """
        try:
            # Validar tamaño del archivo
            if hasattr(image_file, 'size') and image_file.size > cls.MAX_IMAGE_SIZE:
                raise ValidationError(
                    f"Imagen demasiado grande. Máximo permitido: {cls.MAX_IMAGE_SIZE // 1024 // 1024}MB"
                )
            
            # Validar extensión
            file_name = getattr(image_file, 'name', '')
            if file_name:
                ext = os.path.splitext(file_name.lower())[1]
                if ext not in cls.ALLOWED_IMAGE_EXTENSIONS:
                    raise ValidationError(
                        f"Tipo de archivo no permitido: {ext}. "
                        f"Permitidos: {', '.join(cls.ALLOWED_IMAGE_EXTENSIONS)}"
                    )
            
            # Validar tipo MIME si está disponible
            content_type = getattr(image_file, 'content_type', '')
            if content_type and content_type not in cls.ALLOWED_MIME_TYPES:
                raise ValidationError(f"Tipo MIME no permitido: {content_type}")
            
            # Intentar abrir y validar la imagen
            try:
                # Seek al inicio del archivo
                if hasattr(image_file, 'seek'):
                    image_file.seek(0)
                
                image = Image.open(image_file)
                
                # Validar dimensiones
                width, height = image.size
                
                if (width < cls.MIN_IMAGE_DIMENSIONS[0] or 
                    height < cls.MIN_IMAGE_DIMENSIONS[1]):
                    raise ValidationError(
                        f"Imagen demasiado pequeña. Mínimo: {cls.MIN_IMAGE_DIMENSIONS[0]}x{cls.MIN_IMAGE_DIMENSIONS[1]}"
                    )
                
                if (width > cls.MAX_IMAGE_DIMENSIONS[0] or 
                    height > cls.MAX_IMAGE_DIMENSIONS[1]):
                    raise ValidationError(
                        f"Imagen demasiado grande. Máximo: {cls.MAX_IMAGE_DIMENSIONS[0]}x{cls.MAX_IMAGE_DIMENSIONS[1]}"
                    )
                
                # Verificar que la imagen se puede procesar
                try:
                    image.verify()
                    # Re-abrir después de verify()
                    if hasattr(image_file, 'seek'):
                        image_file.seek(0)
                    image = Image.open(image_file)
                    
                    # Intentar cargar completamente la imagen
                    image.load()
                    
                except Exception as e:
                    raise ValidationError(f"Imagen corrupta o no válida: {str(e)}")
                
                logger.info(f"Imagen validada exitosamente: {width}x{height}, modo: {image.mode}")
                return image
                
            except ValidationError:
                raise
            except Exception as e:
                logger.error(f"Error validando imagen: {e}")
                raise ValidationError(f"Error procesando imagen: {str(e)}")
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error inesperado validando imagen: {e}")
            raise ValidationError("Error validando imagen")
    
    @classmethod
    def validate_sonification_settings(cls, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida y normaliza configuraciones de sonificación.
        
        Args:
            settings: Diccionario con configuraciones
            
        Returns:
            Dict[str, Any]: Configuraciones validadas y normalizadas
        """
        validated_settings = {}
        
        # Validar forma de onda
        allowed_waveforms = {'sine', 'celesta', 'piano', 'flute', 'synthwave', 'pipe organ'}
        waveform = settings.get('waveform', 'celesta')
        if waveform not in allowed_waveforms:
            waveform = 'celesta'
        validated_settings['waveform'] = waveform
        
        # Validar frecuencias
        min_freq = cls._validate_frequency(settings.get('min_freq', 500), 50, 2000, 500)
        max_freq = cls._validate_frequency(settings.get('max_freq', 1500), 100, 5000, 1500)
        
        # Asegurar que min_freq < max_freq
        if min_freq >= max_freq:
            min_freq = 500
            max_freq = 1500
        
        validated_settings['min_freq'] = min_freq
        validated_settings['max_freq'] = max_freq
        
        # Validar time_base (velocidad)
        time_base = settings.get('time_base', 0.09)  # Actualizado de 0.04 a 0.09
        try:
            time_base = float(time_base)
            if time_base < 0.01 or time_base > 1.0:
                time_base = 0.09  # Actualizado valor por defecto
        except (ValueError, TypeError):
            time_base = 0.09  # Actualizado valor por defecto
        validated_settings['time_base'] = time_base
        
        # Validar volumen
        volume = settings.get('volume', 0.5)
        try:
            volume = float(volume)
            if volume < 0.0 or volume > 1.0:
                volume = 0.5
        except (ValueError, TypeError):
            volume = 0.5
        validated_settings['volume'] = volume
        
        return validated_settings
    
    @classmethod
    def _validate_frequency(cls, freq, min_val: float, max_val: float, default: float) -> float:
        """Valida una frecuencia dentro de rangos permitidos."""
        try:
            freq = float(freq)
            if freq < min_val or freq > max_val:
                return default
            return freq
        except (ValueError, TypeError):
            return default
    
    @classmethod
    def validate_cache_size(cls, cache_dir: str) -> None:
        """
        Valida que el tamaño del caché no exceda los límites.
        
        Args:
            cache_dir: Directorio de caché
            
        Raises:
            PermissionDenied: Si el caché es demasiado grande
        """
        try:
            if not os.path.exists(cache_dir):
                return
            
            total_size = 0
            for root, dirs, files in os.walk(cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        continue
            
            if total_size > cls.MAX_CACHE_SIZE:
                raise PermissionDenied(
                    f"Caché demasiado grande ({total_size // 1024 // 1024}MB). "
                    f"Máximo permitido: {cls.MAX_CACHE_SIZE // 1024 // 1024}MB"
                )
                
        except PermissionDenied:
            raise
        except Exception as e:
            logger.warning(f"Error validando tamaño de caché: {e}")


class ImageRateLimiter:
    """Rate limiter para prevenir abuso en procesamiento de imágenes."""
    
    # Límites por IP - Ajustados para desarrollo
    MAX_REQUESTS_PER_IP = 15  # Aumentado de 5 a 15
    MAX_CONCURRENT_PROCESSING = 3  # Mantener en 3 
    WINDOW_SIZE = 300  # 5 minutos (mantener igual)
    
    # Almacenamiento en memoria (en producción usar Redis)
    _request_counts = defaultdict(deque)
    _active_requests = defaultdict(set)
    
    @classmethod
    def check_rate_limit(cls, client_ip: str) -> bool:
        """
        Verifica si la IP puede hacer una nueva solicitud.
        
        Args:
            client_ip: IP del cliente
            
        Returns:
            bool: True si puede proceder, False si está limitado
        """
        try:
            current_time = time.time()
            
            # Limpiar requests antiguos
            cls._cleanup_old_requests(client_ip, current_time)
            
            # Verificar límite de requests concurrentes
            if len(cls._active_requests[client_ip]) >= cls.MAX_CONCURRENT_PROCESSING:
                logger.warning(f"Rate limit excedido (concurrentes): {client_ip}")
                return False
            
            # Verificar límite de requests en ventana de tiempo
            if len(cls._request_counts[client_ip]) >= cls.MAX_REQUESTS_PER_IP:
                logger.warning(f"Rate limit excedido (ventana): {client_ip}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error en rate limiting: {e}")
            return True  # En caso de error, permitir request
    
    @classmethod
    def add_request(cls, client_ip: str, request_id: str) -> None:
        """
        Registra una nueva solicitud.
        
        Args:
            client_ip: IP del cliente
            request_id: ID único de la solicitud
        """
        try:
            current_time = time.time()
            cls._request_counts[client_ip].append(current_time)
            cls._active_requests[client_ip].add(request_id)
            
        except Exception as e:
            logger.error(f"Error registrando request: {e}")
    
    @classmethod
    def remove_request(cls, request_id: str) -> None:
        """
        Elimina una solicitud activa.
        
        Args:
            request_id: ID de la solicitud a eliminar
        """
        try:
            for ip, requests in cls._active_requests.items():
                if request_id in requests:
                    requests.discard(request_id)
                    break
                    
        except Exception as e:
            logger.error(f"Error eliminando request: {e}")
    
    @classmethod
    def _cleanup_old_requests(cls, client_ip: str, current_time: float) -> None:
        """Limpia requests antiguos fuera de la ventana de tiempo."""
        try:
            cutoff_time = current_time - cls.WINDOW_SIZE
            
            # Limpiar contador de requests
            requests = cls._request_counts[client_ip]
            while requests and requests[0] < cutoff_time:
                requests.popleft()
                
        except Exception as e:
            logger.error(f"Error limpiando requests antiguos: {e}")
    
    @classmethod
    def get_stats(cls, client_ip: str) -> Dict[str, Any]:
        """Obtiene estadísticas de rate limiting para una IP."""
        try:
            current_time = time.time()
            cls._cleanup_old_requests(client_ip, current_time)
            
            return {
                'requests_in_window': len(cls._request_counts[client_ip]),
                'max_requests': cls.MAX_REQUESTS_PER_IP,
                'active_requests': len(cls._active_requests[client_ip]),
                'max_concurrent': cls.MAX_CONCURRENT_PROCESSING,
                'window_size_minutes': cls.WINDOW_SIZE // 60
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de rate limit: {e}")
            return {}


class ImageProcessingValidator:
    """Validador específico para operaciones de procesamiento de imágenes."""
    
    @classmethod
    def validate_processing_parameters(cls, image_size: tuple, settings: Dict[str, Any]) -> bool:
        """
        Valida que los parámetros de procesamiento sean seguros.
        
        Args:
            image_size: Tupla (width, height) de la imagen
            settings: Configuraciones de sonificación
            
        Returns:
            bool: True si es seguro procesar
        """
        try:
            width, height = image_size
            time_base = settings.get('time_base', 0.04)
            
            # Calcular carga de procesamiento estimada
            total_frames = width
            estimated_duration = total_frames * time_base
            
            # Límites de seguridad
            MAX_FRAMES = 2000  # Máximo 2000 columnas
            MAX_DURATION = 120  # Máximo 2 minutos de video
            
            if total_frames > MAX_FRAMES:
                logger.warning(f"Demasiados frames para procesar: {total_frames}")
                return False
            
            if estimated_duration > MAX_DURATION:
                logger.warning(f"Duración estimada demasiado larga: {estimated_duration}s")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando parámetros de procesamiento: {e}")
            return False
