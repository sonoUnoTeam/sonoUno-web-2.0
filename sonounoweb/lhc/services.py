# -*- coding: utf-8 -*-
"""
Servicios especializados para operaciones LHC.
Separa la lógica de negocio de las vistas.
"""

import os
import json
import time
import hashlib
import tempfile
import logging
from typing import Optional, Tuple, Dict, Any, List
from django.conf import settings
from io import BytesIO
import base64

from .validators import LHCSecurityValidator
from utils.lhc_lib.lhc_web import process_files, get_total_events

# Configurar logging
logger = logging.getLogger(__name__)

class LHCCacheService:
    """Servicio especializado para gestión de caché de videos LHC."""
    
    def __init__(self):
        self.cache_dir = os.path.join(settings.BASE_DIR, 'temp', 'video_cache')
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Asegura que el directorio de caché existe."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            # Validar tamaño del caché
            LHCSecurityValidator.validate_cache_size(self.cache_dir)
        except Exception as e:
            logger.error(f"Error creando directorio de caché: {e}")
            raise
    
    def get_cache_key(self, file_name: str, event_index: int) -> str:
        """
        Genera clave única para caché.
        
        Args:
            file_name: Nombre del archivo
            event_index: Índice del evento
            
        Returns:
            str: Clave de caché
        """
        # Incluir versión para invalidar caché cuando se actualice código
        cache_data = f"{file_name}_{event_index}_v2.0"
        return hashlib.sha256(cache_data.encode()).hexdigest()
    
    def get_cached_video(self, cache_key: str) -> Optional[str]:
        """
        Obtiene video del caché si existe y es válido.
        
        Args:
            cache_key: Clave del caché
            
        Returns:
            Optional[str]: Video en base64 o None
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Verificar que el caché no sea muy viejo (1 hora)
            if time.time() - cache_data.get('timestamp', 0) > 3600:
                logger.info(f"Caché expirado: {cache_key}")
                self._remove_cache_file(cache_file)
                return None
            
            # Verificar integridad
            video_data = cache_data.get('video_base64')
            if not video_data:
                logger.warning(f"Caché corrupto (sin datos): {cache_key}")
                self._remove_cache_file(cache_file)
                return None
            
            logger.info(f"Video obtenido del caché: {cache_key}")
            return video_data
            
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error leyendo caché {cache_key}: {e}")
            self._remove_cache_file(cache_file)
            return None
    
    def save_video_to_cache(self, cache_key: str, video_base64: str) -> bool:
        """
        Guarda video en caché.
        
        Args:
            cache_key: Clave del caché
            video_base64: Video en base64
            
        Returns:
            bool: True si se guardó exitosamente
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            cache_data = {
                'video_base64': video_base64,
                'timestamp': time.time(),
                'size_mb': len(video_base64) / (1024 * 1024 * 1.33)  # Aproximado sin base64
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            logger.info(f"Video guardado en caché: {cache_key} ({cache_data['size_mb']:.2f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando en caché {cache_key}: {e}")
            return False
    
    def _remove_cache_file(self, cache_file: str) -> None:
        """Remueve archivo de caché de forma segura."""
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
        except OSError as e:
            logger.error(f"Error removiendo archivo de caché {cache_file}: {e}")
    
    def clear_cache(self) -> bool:
        """
        Limpia todo el caché.
        
        Returns:
            bool: True si se limpió exitosamente
        """
        try:
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
            self._ensure_cache_dir()
            logger.info("Caché limpiado exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Dict: Estadísticas del caché
        """
        if not os.path.exists(self.cache_dir):
            return {"files": 0, "size_mb": 0, "oldest": None, "newest": None}
        
        try:
            files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            total_size = 0
            timestamps = []
            
            for file in files:
                file_path = os.path.join(self.cache_dir, file)
                total_size += os.path.getsize(file_path)
                
                # Obtener timestamp del archivo
                try:
                    with open(file_path, 'r') as f:
                        cache_data = json.load(f)
                        timestamps.append(cache_data.get('timestamp', 0))
                except:
                    pass
            
            stats = {
                "files": len(files),
                "size_mb": round(total_size / (1024 * 1024), 2),
                "oldest": None,
                "newest": None
            }
            
            if timestamps:
                stats["oldest"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(min(timestamps)))
                stats["newest"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(max(timestamps)))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de caché: {e}")
            return {"files": 0, "size_mb": 0, "oldest": None, "newest": None}


class LHCVideoService:
    """Servicio especializado para generación de videos LHC."""
    
    def __init__(self):
        self.cache_service = LHCCacheService()
    
    def generate_lhc_video(
        self, 
        file_name: str, 
        event_index: int,
        use_cache: bool = True
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
        """
        Genera video LHC con manejo completo de errores y caché.
        
        Args:
            file_name: Nombre del archivo de datos
            event_index: Índice del evento (1-based)
            use_cache: Si usar caché o no
            
        Returns:
            Tuple[video_base64, event_info, status_message]
        """
        request_id = f"{file_name}_{event_index}_{int(time.time())}"
        
        try:
            # Validaciones de seguridad
            validated_file_name = LHCSecurityValidator.validate_file_name(file_name)
            total_events = get_total_events(validated_file_name)
            
            if total_events == 0:
                return None, None, "No se encontraron eventos en el archivo"
            
            validated_event_index = LHCSecurityValidator.validate_event_index(event_index, total_events)
            
            # Intentar obtener del caché
            if use_cache:
                cache_key = self.cache_service.get_cache_key(validated_file_name, validated_event_index)
                cached_video = self.cache_service.get_cached_video(cache_key)
                
                if cached_video:
                    logger.info(f"Video obtenido del caché para evento {validated_event_index}")
                    
                    # Extraer imagen y audio del video cacheado para descargas
                    final_image_base64 = self._extract_image_from_video_base64(cached_video)
                    audio_data = self._extract_audio_from_video_base64(cached_video)
                    final_audio_base64 = base64.b64encode(audio_data).decode('utf-8') if audio_data else None
                    
                    event_info = {
                        'event_number': validated_event_index,
                        'event_index': validated_event_index,
                        'total_events': total_events,
                        'total_tracks': 0,  # No disponible desde caché
                        'total_clusters': 0,  # No disponible desde caché
                        'from_cache': True,
                        'final_image_base64': final_image_base64,
                        'final_audio_base64': final_audio_base64
                    }
                    return cached_video, event_info, "Video obtenido del caché"
            
            # Generar nuevo video
            logger.info(f"Generando nuevo video para evento {validated_event_index}")
            
            # Procesar con la librería LHC
            image_paths, sound_paths, event_info = process_files(
                None, 
                validated_file_name, 
                'txt', 
                True, 
                validated_event_index, 
                save_to_output=False, 
                generate_complete_audio=True
            )
            
            if not image_paths or not sound_paths:
                return None, None, "Error procesando datos LHC"
            
            # Crear video
            video_base64 = self._create_video_from_paths(image_paths, sound_paths)
            
            if not video_base64:
                return None, None, "Error generando video"
            
            # Extraer imagen y audio para descargas
            logger.info("Extrayendo imagen y audio para descargas...")
            final_image_base64 = self._extract_image_from_video_base64(video_base64)
            audio_data = self._extract_audio_from_video_base64(video_base64)
            final_audio_base64 = base64.b64encode(audio_data).decode('utf-8') if audio_data else None
            
            # Guardar en caché
            if use_cache:
                cache_key = self.cache_service.get_cache_key(validated_file_name, validated_event_index)
                self.cache_service.save_video_to_cache(cache_key, video_base64)
            
            # Actualizar event_info con datos de descarga
            if event_info:
                event_info['event_number'] = validated_event_index
                event_info['event_index'] = validated_event_index
                event_info['from_cache'] = False
                event_info['final_image_base64'] = final_image_base64
                event_info['final_audio_base64'] = final_audio_base64
            
            logger.info(f"Video generado exitosamente para evento {validated_event_index}")
            return video_base64, event_info, f"Video generado exitosamente"
            
        except Exception as e:
            logger.error(f"Error generando video {request_id}: {e}")
            return None, None, f"Error: {str(e)}"
    
    def _create_video_from_paths(self, image_paths: List[str], sound_paths: List[str]) -> Optional[str]:
        """
        Crea video a partir de rutas de imágenes y sonidos.
        Versión optimizada con mejor manejo de recursos.
        
        Args:
            image_paths: Lista de rutas de imágenes
            sound_paths: Lista de rutas de sonidos
            
        Returns:
            Optional[str]: Video en base64 o None si falla
        """
        try:
            from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, AudioClip, concatenate_audioclips
            from PIL import Image
            
            logger.info(f"Creando video con {len(image_paths)} clips")
            
            clips = []
            temp_files_to_cleanup = []
            
            try:
                total_clips = len(image_paths)
                mid_point = total_clips // 2
                
                for i, (image_path, sound_path) in enumerate(zip(image_paths, sound_paths)):
                    # Verificar archivos
                    if not os.path.exists(image_path) or not os.path.exists(sound_path):
                        logger.warning(f"Archivos faltantes en clip {i+1}")
                        continue
                    
                    # Crear clip de audio
                    audio_clip = AudioFileClip(sound_path)
                    
                    # Agregar silencio según posición
                    if i == total_clips - 1:
                        audio_clip_final = AudioClip(lambda t: 0, duration=1, fps=44100)
                    elif i == 0 or i == mid_point:
                        silence = AudioClip(lambda t: 0, duration=1, fps=44100)
                        audio_clip_final = concatenate_audioclips([audio_clip, silence])
                    else:
                        audio_clip_final = audio_clip
                    
                    # Procesar imagen
                    clean_image_path = self._process_image(image_path, temp_files_to_cleanup)
                    
                    # Crear clip de imagen
                    image_clip = ImageClip(clean_image_path, duration=audio_clip_final.duration)
                    final_clip = image_clip.set_audio(audio_clip_final)
                    clips.append(final_clip)
                
                if not clips:
                    logger.error("No se pudieron crear clips válidos")
                    return None
                
                # Concatenar clips
                final_clip = concatenate_videoclips(clips)
                
                # Generar video en memoria
                video_base64 = self._write_video_to_base64(final_clip)
                
                return video_base64
                
            finally:
                # Limpiar recursos
                for clip in clips:
                    try:
                        if hasattr(clip, 'audio') and clip.audio:
                            clip.audio.close()
                        clip.close()
                    except:
                        pass
                
                if 'final_clip' in locals():
                    final_clip.close()
                
                # Limpiar archivos temporales
                for temp_file in temp_files_to_cleanup:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Error creando video: {e}")
            return None
    
    def _process_image(self, image_path: str, temp_files_to_cleanup: List[str]) -> str:
        """
        Procesa imagen para optimizar para video.
        
        Args:
            image_path: Ruta de la imagen original
            temp_files_to_cleanup: Lista para tracking de archivos temporales
            
        Returns:
            str: Ruta de la imagen procesada
        """
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            
            # Redimensionar si es necesario
            max_size = (1200, 600)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Limpiar metadatos EXIF si es problemático
            clean_image_path = image_path
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif = img._getexif()
                if exif and 274 in exif:  # Orientación EXIF
                    img_data = img.getdata()
                    img_clean = Image.new(img.mode, img.size)
                    img_clean.putdata(img_data)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img:
                        img_clean.save(temp_img.name, 'PNG', optimize=True)
                        clean_image_path = temp_img.name
                        temp_files_to_cleanup.append(clean_image_path)
                    img_clean.close()
            
            img.close()
            return clean_image_path
            
        except Exception as e:
            logger.error(f"Error procesando imagen {image_path}: {e}")
            return image_path  # Fallback a imagen original
    
    def _write_video_to_base64(self, final_clip) -> Optional[str]:
        """
        Escribe video a base64 de forma optimizada.
        
        Args:
            final_clip: Clip de MoviePy
            
        Returns:
            Optional[str]: Video en base64
        """
        temp_dir = os.path.join(settings.BASE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_video_path = None
        temp_audio_path = None
        
        try:
            # Crear archivos temporales
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_video:
                temp_video_path = temp_video.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Configurar permisos
            os.chmod(temp_video_path, 0o644)
            
            # Escribir video con configuración optimizada
            final_clip.write_videofile(
                temp_video_path,
                codec='libx264',
                fps=15,
                audio_codec='aac',
                temp_audiofile=temp_audio_path,
                ffmpeg_params=[
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    '-preset', 'fast',  # Balanceado entre velocidad y calidad
                    '-crf', '26',  # Calidad mejorada
                    '-tune', 'fastdecode'
                ],
                verbose=False,
                logger=None,
                threads=2  # Reducido para evitar sobrecarga
            )
            
            # Verificar video generado
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
            logger.error(f"Error escribiendo video a base64: {e}")
            return None
            
        finally:
            # Limpiar archivos temporales
            for temp_path in [temp_video_path, temp_audio_path]:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError as e:
                        logger.error(f"Error eliminando archivo temporal {temp_path}: {e}")
    
    def _extract_image_from_video_base64(self, video_base64: str) -> Optional[str]:
        """
        Extrae una imagen (frame) de un video en base64.
        
        Args:
            video_base64: Video en formato base64
            
        Returns:
            Optional[str]: Imagen en base64 o None si falla
        """
        try:
            from moviepy.editor import VideoFileClip
            from PIL import Image
            import tempfile
            
            temp_dir = os.path.join(settings.BASE_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Crear archivo temporal para el video
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_video:
                video_data = base64.b64decode(video_base64)
                temp_video.write(video_data)
                temp_video_path = temp_video.name
            
            # Crear archivo temporal para la imagen
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir=temp_dir) as temp_image:
                temp_image_path = temp_image.name
            
            try:
                # Cargar video y extraer frame
                video_clip = VideoFileClip(temp_video_path)
                duration = video_clip.duration
                
                # Obtener frame del medio del video para mejor representación
                if duration and duration > 0:
                    frame_time = min(duration * 0.5, duration - 0.1)
                else:
                    frame_time = 0
                
                frame = video_clip.get_frame(frame_time)
                img = Image.fromarray(frame)
                img.save(temp_image_path, 'PNG')
                
                # Leer imagen y convertir a base64
                with open(temp_image_path, 'rb') as img_file:
                    image_data = img_file.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                video_clip.close()
                return image_base64
                
            finally:
                # Limpiar archivos temporales
                try:
                    os.remove(temp_video_path)
                    os.remove(temp_image_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error extrayendo imagen del video: {e}")
            return None
    
    def _extract_audio_from_video_base64(self, video_base64: str) -> Optional[bytes]:
        """
        Extrae audio de un video en base64.
        
        Args:
            video_base64: Video en formato base64
            
        Returns:
            Optional[bytes]: Audio en bytes o None si falla
        """
        try:
            from moviepy.editor import VideoFileClip
            import tempfile
            
            temp_dir = os.path.join(settings.BASE_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Crear archivo temporal para el video
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_video:
                video_data = base64.b64decode(video_base64)
                temp_video.write(video_data)
                temp_video_path = temp_video.name
            
            # Crear archivo temporal para el audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=temp_dir) as temp_audio:
                temp_audio_path = temp_audio.name
            
            try:
                # Cargar video y extraer audio
                video_clip = VideoFileClip(temp_video_path)
                audio_clip = video_clip.audio
                
                if audio_clip is None:
                    logger.warning("El video no contiene pista de audio")
                    video_clip.close()
                    return None
                
                # Escribir audio a archivo temporal
                audio_clip.write_audiofile(
                    temp_audio_path,
                    codec='pcm_s16le',
                    verbose=False,
                    logger=None
                )
                
                # Leer audio como bytes
                with open(temp_audio_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                video_clip.close()
                audio_clip.close()
                return audio_data
                
            finally:
                # Limpiar archivos temporales
                try:
                    os.remove(temp_video_path)
                    os.remove(temp_audio_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error extrayendo audio del video: {e}")
            return None


class LHCEventService:
    """Servicio para manejo de eventos LHC."""
    
    def get_event_navigation(self, current_event: int, total_events: int) -> Dict[str, Optional[int]]:
        """
        Calcula navegación de eventos.
        
        Args:
            current_event: Evento actual (1-based)
            total_events: Total de eventos
            
        Returns:
            Dict: Información de navegación
        """
        return {
            'prev_event': current_event - 1 if current_event > 1 else None,
            'next_event': current_event + 1 if current_event < total_events else None,
            'first_event': 1,
            'last_event': total_events,
            'current_event': current_event,
            'total_events': total_events
        }