# -*- coding: utf-8 -*-
"""
Servicios especializados para sonificación de imágenes.
Inspirado en la arquitectura de la app LHC.
"""

import os
import json
import time
import hashlib
import tempfile
import logging
import base64
from typing import Optional, Tuple, Dict, Any, List
from django.conf import settings
from PIL import Image, ImageOps
import numpy as np

from .validators import ImageSecurityValidator
from .sound_module.simple_sound import simpleSound

# Configurar logging
logger = logging.getLogger('imagesonif')

class ImageCacheService:
    """Servicio especializado para gestión de caché de videos de sonificación de imágenes."""
    
    def __init__(self):
        self.cache_dir = os.path.join(settings.BASE_DIR, 'temp', 'imagesonif_cache')
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Asegura que el directorio de caché existe."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            # Validar tamaño del caché
            ImageSecurityValidator.validate_cache_size(self.cache_dir)
        except Exception as e:
            logger.error(f"Error creando directorio de caché imagesonif: {e}")
            raise
    
    def get_cache_key(self, image_hash: str, settings_hash: str) -> str:
        """
        Genera clave única para caché basada en hash de imagen y configuraciones.
        
        Args:
            image_hash: Hash MD5 de la imagen
            settings_hash: Hash de las configuraciones de sonificación
            
        Returns:
            str: Clave de caché
        """
        cache_data = f"{image_hash}_{settings_hash}_v1.0"
        return hashlib.sha256(cache_data.encode()).hexdigest()
    
    def get_cached_sonification(self, cache_key: str) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
        """
        Obtiene video, audio e info del caché si existe y es válido.
        
        Args:
            cache_key: Clave del caché
            
        Returns:
            Tuple[video_base64, audio_base64, sonification_info] o (None, None, None)
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None, None, None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Verificar integridad
            video_data = cache_data.get('video_base64')
            audio_data = cache_data.get('audio_base64')
            sonification_info = cache_data.get('sonification_info')
            
            if not video_data or not audio_data:
                logger.warning(f"Caché corrupto para imagesonif: {cache_key}")
                self._remove_cache_file(cache_file)
                return None, None, None
            
            logger.info(f"Sonificación obtenida del caché: {cache_key}")
            return video_data, audio_data, sonification_info
            
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error leyendo caché imagesonif {cache_key}: {e}")
            self._remove_cache_file(cache_file)
            return None, None, None
    
    def save_sonification_to_cache(self, cache_key: str, video_base64: str, 
                                  audio_base64: str, sonification_info: Dict = None) -> bool:
        """
        Guarda sonificación completa en caché.
        
        Args:
            cache_key: Clave del caché
            video_base64: Video en base64
            audio_base64: Audio en base64
            sonification_info: Información de la sonificación
            
        Returns:
            bool: True si se guardó exitosamente
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            cache_data = {
                'video_base64': video_base64,
                'audio_base64': audio_base64,
                'sonification_info': sonification_info or {},
                'timestamp': time.time(),
                'version': '1.0'
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            logger.info(f"Sonificación guardada en caché: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando caché imagesonif {cache_key}: {e}")
            return False
    
    def _remove_cache_file(self, cache_file: str) -> None:
        """Elimina archivo de caché corrupto."""
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.info(f"Archivo de caché eliminado: {cache_file}")
        except Exception as e:
            logger.error(f"Error eliminando archivo de caché: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del caché."""
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            total_size = sum(
                os.path.getsize(os.path.join(self.cache_dir, f)) for f in cache_files
            )
            
            return {
                'total_files': len(cache_files),
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'cache_dir': self.cache_dir
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de caché: {e}")
            return {'error': str(e)}
    
    def clear_cache(self) -> bool:
        """Limpia todo el caché."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
            logger.info("Caché de imagesonif limpiado exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error limpiando caché imagesonif: {e}")
            return False


class ImageSonificationVideoService:
    """Servicio especializado para generación de videos de sonificación de imágenes."""
    
    def __init__(self):
        self.cache_service = ImageCacheService()
        self.sound_generator = simpleSound()
    
    def process_image_sonification(self, 
                                  image_file, 
                                  sonification_settings: Dict = None,
                                  use_cache: bool = True) -> Tuple[Optional[str], Optional[str], Optional[Dict], str]:
        """
        Procesa la sonificación completa de una imagen.
        
        Args:
            image_file: Archivo de imagen subido
            sonification_settings: Configuraciones de sonificación
            use_cache: Si usar caché o no
            
        Returns:
            Tuple[video_base64, audio_base64, sonification_info, status_message]
        """
        try:
            # Configuraciones por defecto
            if sonification_settings is None:
                sonification_settings = {
                    'min_freq': 500,
                    'max_freq': 1500,
                    'time_base': 0.09,  # Aumentado de 0.04 a 0.09 para mayor duración
                    'volume': 0.85  # Aumentado de 0.5 a 0.85 para mejor audibilidad
                }
            
            # Validar imagen
            try:
                validated_image = ImageSecurityValidator.validate_uploaded_image(image_file)
            except Exception as e:
                return None, None, None, f"Error validando imagen: {str(e)}"
            
            # Generar hash de imagen y configuraciones para caché
            image_hash = self._get_image_hash(validated_image)
            settings_hash = self._get_settings_hash(sonification_settings)
            
            # Intentar obtener del caché
            if use_cache:
                cache_key = self.cache_service.get_cache_key(image_hash, settings_hash)
                cached_video, cached_audio, cached_info = self.cache_service.get_cached_sonification(cache_key)
                
                if cached_video and cached_audio:
                    logger.info("Sonificación obtenida del caché")
                    cached_info['from_cache'] = True
                    return cached_video, cached_audio, cached_info, "Sonificación generada exitosamente"
            
            # Procesar imagen nueva
            logger.info("Generando nueva sonificación de imagen")
            
            # Preparar imagen
            processed_image = self._prepare_image_for_sonification(validated_image)
            image_array = np.array(processed_image)
            
            # Configurar generador de sonido
            self._configure_sound_generator(sonification_settings)
            
            # Crear directorio temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                # Procesar sonificación
                audio_data_list, normalized_values = self.sound_generator.process_image_sonification(
                    image_array
                )
                
                if not audio_data_list:
                    return None, None, None, "Error procesando sonificación"
                
                # Crear secuencia de imágenes con progreso
                progress_images = self.sound_generator.create_progress_images(
                    processed_image, 
                    len(audio_data_list), 
                    temp_dir
                )
                
                # Si no se pueden generar imágenes de progreso, continuar sin ellas
                if not progress_images:
                    logger.warning("No se pudieron generar imágenes de progreso, continuando sin video")
                    progress_images = []
                
                # Guardar audio completo
                audio_path = os.path.join(temp_dir, 'sonification.wav')
                if not self.sound_generator.save_complete_audio(audio_data_list, audio_path):
                    return None, None, None, "Error guardando audio"
                
                # Crear video solo si hay imágenes de progreso
                video_base64 = None
                if progress_images:
                    video_base64 = self._create_video_from_images_and_audio(
                        progress_images, 
                        audio_path,
                        sonification_settings.get('time_base', 0.09)  # Actualizado valor por defecto
                    )
                    if not video_base64:
                        logger.warning("No se pudo generar video, continuando solo con audio")
                else:
                    logger.info("Sin imágenes de progreso, continuando solo con audio")
                
                # Convertir audio a base64
                with open(audio_path, 'rb') as audio_file:
                    audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
                
                # Preparar información de sonificación
                sonification_info = {
                    'image_dimensions': processed_image.size,
                    'total_columns': len(audio_data_list),
                    'duration_seconds': len(audio_data_list) * sonification_settings.get('time_base', 0.09),  # Actualizado
                    'settings': sonification_settings,
                    'from_cache': False,
                    'timestamp': time.time()
                }
                
                # Guardar en caché
                if use_cache:
                    cache_key = self.cache_service.get_cache_key(image_hash, settings_hash)
                    self.cache_service.save_sonification_to_cache(
                        cache_key, video_base64, audio_base64, sonification_info
                    )
                
                logger.info(f"Sonificación generada exitosamente - {len(audio_data_list)} columnas")
                return video_base64, audio_base64, sonification_info, "Sonificación generada exitosamente"
        
        except Exception as e:
            logger.error(f"Error procesando sonificación de imagen: {e}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            return None, None, None, f"Error: {str(e)}"
    
    def _get_image_hash(self, image: Image.Image) -> str:
        """Genera hash MD5 de la imagen."""
        import hashlib
        
        # Convertir imagen a bytes para hash
        img_bytes = image.tobytes()
        return hashlib.md5(img_bytes).hexdigest()
    
    def _get_settings_hash(self, settings: Dict) -> str:
        """Genera hash de las configuraciones."""
        import hashlib
        
        settings_str = json.dumps(settings, sort_keys=True)
        return hashlib.md5(settings_str.encode()).hexdigest()
    
    def _prepare_image_for_sonification(self, image: Image.Image) -> Image.Image:
        """Prepara la imagen para sonificación."""
        # Convertir a escala de grises
        gray_image = ImageOps.grayscale(image)
        
        # Redimensionar si es muy grande (máximo 960 columnas como en el script original)
        max_width = 960
        if gray_image.width > max_width:
            ratio = max_width / gray_image.width
            new_height = int(gray_image.height * ratio)
            gray_image = gray_image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        return gray_image
    
    def _configure_sound_generator(self, settings: Dict) -> None:
        """Configura el generador de sonido con las configuraciones especificadas."""
        reproductor = self.sound_generator.reproductor
        
        reproductor.set_min_freq(settings.get('min_freq', 500))
        reproductor.set_max_freq(settings.get('max_freq', 1500))
        reproductor.set_time_base(settings.get('time_base', 0.09))  # Actualizado valor por defecto
        reproductor.set_volume(settings.get('volume', 0.5))
        reproductor.set_continuous()
    
    def _create_video_from_images_and_audio(self, image_paths: List[str], 
                                           audio_path: str, time_base: float) -> Optional[str]:
        """
        Crea video MP4 a partir de secuencia de imágenes y audio.
        
        Args:
            image_paths: Lista de rutas de imágenes
            audio_path: Ruta del archivo de audio
            time_base: Duración de cada frame en segundos
            
        Returns:
            Optional[str]: Video en base64 o None si falla
        """
        try:
            from moviepy.editor import ImageSequenceClip, AudioFileClip
            import gc
            
            logger.info(f"Creando video con {len(image_paths)} frames")
            
            # Crear clip de video desde secuencia de imágenes
            video_clip = ImageSequenceClip(image_paths, fps=1/time_base)
            
            # Cargar audio
            audio_clip = AudioFileClip(audio_path)
            logger.info(f"Audio cargado - Duración: {audio_clip.duration}s, FPS: {audio_clip.fps}")
            
            # Sincronizar duración
            if video_clip.duration > audio_clip.duration:
                video_clip = video_clip.subclip(0, audio_clip.duration)
                logger.info(f"Video ajustado a duración del audio: {audio_clip.duration}s")
            elif audio_clip.duration > video_clip.duration:
                audio_clip = audio_clip.subclip(0, video_clip.duration)
                logger.info(f"Audio ajustado a duración del video: {video_clip.duration}s")
            
            # Combinar video y audio
            final_clip = video_clip.set_audio(audio_clip)
            logger.info("Video y audio combinados exitosamente")
            
            # Usar directorio temp del proyecto como en LHC
            from django.conf import settings
            temp_dir = os.path.join(settings.BASE_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Crear archivos temporales en el directorio del proyecto
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_video:
                temp_video_path = temp_video.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Configurar permisos
            os.chmod(temp_video_path, 0o644)
            
            # Renderizar video con configuración optimizada como LHC
            final_clip.write_videofile(
                temp_video_path,
                codec='libx264',
                fps=15,
                audio_codec='aac',
                temp_audiofile=temp_audio_path,
                ffmpeg_params=[
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    '-preset', 'fast',
                    '-crf', '26',
                    '-tune', 'fastdecode',
                    # Parámetros específicos para audio (sin filtro de volumen)
                    '-ac', '2',  # 2 canales (estéreo)
                    '-ar', '44100',  # Sample rate 44.1kHz
                    '-ab', '192k'  # Bitrate de audio aumentado a 192kbps
                ],
                verbose=False,
                logger=None,
                threads=2
            )
            
            # Verificar video generado como en LHC
            if not os.path.exists(temp_video_path) or os.path.getsize(temp_video_path) == 0:
                logger.error("Video generado está vacío o no existe")
                return None
            
            # Leer y convertir a base64
            with open(temp_video_path, 'rb') as video_file:
                video_data = video_file.read()
                video_base64 = base64.b64encode(video_data).decode('utf-8')
            
            logger.info(f"Video convertido a base64 exitosamente ({len(video_data)} bytes)")
            return video_base64
            
        except Exception as e:
            logger.error(f"Error creando video con MoviePy: {e}")
            return None
            
        finally:
            # Limpieza exhaustiva de recursos MoviePy como en LHC
            try:
                if 'final_clip' in locals():
                    final_clip.close()
                if 'video_clip' in locals():
                    video_clip.close()
                if 'audio_clip' in locals():
                    audio_clip.close()
            except:
                pass
            
            # Limpiar archivos temporales
            for temp_file in [temp_video_path, temp_audio_path]:
                try:
                    if temp_file and os.path.exists(temp_file):
                        os.unlink(temp_file)
                except:
                    pass
            
            # Limpiar memoria
            gc.collect()


class ImageSonificationInfoService:
    """Servicio para información y metadatos de sonificación."""
    pass
