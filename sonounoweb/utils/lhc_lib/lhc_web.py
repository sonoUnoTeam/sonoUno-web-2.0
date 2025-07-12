# -*- coding: utf-8 -*-
"""
Módulo LHC optimizado para integración con Django web app.

OPTIMIZACIONES REALIZADAS:
- Eliminadas funciones innecesarias para plots de salida (get_output_directory, plot_to_output_file, etc.)
- Removido soporte para data_lhc/lhc_output (nunca usado en la web app)
- Simplificada interfaz process_files (parámetros path, plot_flag, save_to_output siempre tienen valores fijos)
- Optimizado process_single_event para usar solo archivos temporales
- Eliminadas funciones de debug y main

Funciones principales:
- load_particle_data(): Carga y valida archivos de datos LHC 
- get_available_data_files(): Lista archivos disponibles 
- validate_particle_data(): Valida estructura de datos 
- process_files(): Interfaz principal para la web app (siempre usa archivos temporales)
- get_total_events(): Obtiene número total de eventos 
- cleanup_temp_files(): Limpieza de archivos temporales

Interfaz simplificada optimizada para uso exclusivo con archivos temporales.
La función process_files() ignora parámetros innecesarios:
- path: siempre None (usa sample_data fija)
- plot_flag: nunca genera plots de salida
- save_to_output: siempre False (solo archivos temporales)
"""

import os
import sys
import tempfile
import numpy as np
from scipy.io import wavfile
import matplotlib
matplotlib.use('Agg')  # Usar backend sin GUI para web
import matplotlib.pyplot as plt
import logging
import threading
import time
from typing import Optional, Tuple, List, Dict, Any
from functools import lru_cache

# Configurar logging
logger = logging.getLogger(__name__)

# Lock para operaciones thread-safe
_global_lock = threading.RLock()

# Cache para total de eventos
_events_cache = {}
_cache_lock = threading.Lock()

# Agregar el directorio actual al path para importar sonouno_lhc
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from sonouno_lhc import lhc_data
except ImportError as e:
    logger.error(f"Error importando sonouno_lhc: {e}")
    raise ImportError("No se pudo importar sonouno_lhc. Verifique la instalación.")

# Configuración y límites
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_EVENTS_PER_FILE = 10000
DEFAULT_OUTPUT_SIZE = (1200, 600)  # Tamaño estándar para videos

def validate_file_size(file_path: str) -> bool:
    """
    Valida que el archivo no exceda el tamaño máximo permitido.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        bool: True si el tamaño es válido
        
    Raises:
        ValueError: Si el archivo es demasiado grande o no existe
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"Archivo demasiado grande: {file_size / (1024*1024):.2f}MB. "
            f"Máximo permitido: {MAX_FILE_SIZE / (1024*1024):.2f}MB"
        )
    
    if file_size == 0:
        raise ValueError("El archivo está vacío")
    
    return True


def safe_figure_cleanup(fig):
    """
    Limpia una figura de matplotlib de forma segura.
    
    Args:
        fig: Figura de matplotlib a limpiar
    """
    try:
        if fig is not None:
            plt.figure(fig.number)
            plt.clf()
            plt.close(fig)
            del fig
    except Exception as e:
        logger.warning(f"Error limpiando figura matplotlib: {e}")


def plot_to_temp_file(fig):
    """
    Guarda una figura de matplotlib como archivo temporal.
    
    Args:
        fig: Figura de matplotlib
        
    Returns:
        str: Ruta al archivo temporal creado
    """
    try:
        # Obtener directorio temporal del proyecto
        from django.conf import settings
        temp_dir = os.path.join(settings.BASE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
    except ImportError:
        # Fallback si Django no está disponible (para uso standalone)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(script_dir, '..', '..', '..', 'temp')
        temp_dir = os.path.normpath(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir=temp_dir) as tmp_file:
        # Asegurar que la figura tenga el tamaño correcto y configuración consistente
        fig.set_size_inches(12, 6)
        
        # Configurar la figura para evitar distorsión
        fig.tight_layout(pad=2.0)
        
        # Guardar con configuración optimizada para video
        fig.savefig(tmp_file.name, format='png', dpi=100, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', pad_inches=0.1)
        
        # Verificar y ajustar dimensiones para compatibilidad con libx264
        from PIL import Image
        img = Image.open(tmp_file.name)
        width, height = img.size
        
        # Establecer dimensiones estándar para video (HD compatible)
        target_width = 1200  # Múltiplo de 2 para libx264
        target_height = 600  # Múltiplo de 2 para libx264
        
        # Redimensionar la imagen a dimensiones estándar
        if width != target_width or height != target_height:
            # Redimensionar manteniendo la relación de aspecto y centrando
            img_resized = Image.new('RGB', (target_width, target_height), 'white')
            
            # Calcular la escala para mantener proporción
            scale = min(target_width / width, target_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Redimensionar imagen
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Centrar la imagen redimensionada
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            img_resized.paste(img, (x_offset, y_offset))
            
            img_resized.save(tmp_file.name, 'PNG')
            img_resized.close()
        
        img.close()
        return tmp_file.name


def process_sound_array(sound_array):
    """
    Convierte un array de numpy a archivo WAV temporal para MoviePy.
    Usa directorio temp del proyecto.
    
    Args:
        sound_array (numpy.array): Array de datos de audio
        
    Returns:
        str: Ruta al archivo WAV temporal creado
    """
    if sound_array is None or len(sound_array) == 0:
        # Crear silencio de 2 segundos si no hay datos
        sound_array = np.zeros(44100 * 2, dtype=np.int16)
    
    try:
        # Obtener directorio temporal del proyecto
        from django.conf import settings
        temp_dir = os.path.join(settings.BASE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
    except ImportError:
        # Fallback si Django no está disponible (para uso standalone)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(script_dir, '..', '..', '..', 'temp')
        temp_dir = os.path.normpath(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=temp_dir) as tmp_file:
        # Asegurar formato correcto (44.1kHz, 16-bit)
        wavfile.write(
            tmp_file.name,
            rate=44100,
            data=sound_array.astype(np.int16)
        )
        return tmp_file.name


def cleanup_temp_files(file_paths):
    """
    Limpia archivos temporales después de la creación del video.
    Incluye reintentos para archivos bloqueados por otros procesos.
    
    Args:
        file_paths (list): Lista de rutas de archivos a eliminar
    """
    import time
    import gc
    
    if not file_paths:
        return
    
    # Forzar garbage collection antes de intentar limpiar archivos
    gc.collect()
    time.sleep(0.1)  # Pequeña pausa para permitir que el GC termine
    
    for path in file_paths:
        if path and os.path.exists(path):
            max_attempts = 5  # Aumentar intentos para Windows
            for attempt in range(max_attempts):
                try:
                    # Verificar si el archivo todavía existe antes de cada intento
                    if not os.path.exists(path):
                        break
                    
                    os.remove(path)
                    break  # Éxito, salir del loop de reintentos
                except PermissionError as e:
                    if attempt < max_attempts - 1:
                        # Esperar progresivamente más tiempo en cada intento
                        wait_time = 0.5 * (attempt + 1)
                        time.sleep(wait_time)
                        
                        # Forzar otro garbage collection
                        gc.collect()
                        
                        logger.debug(f"Reintentando eliminar archivo temporal {path} (intento {attempt + 2}/{max_attempts})")
                    else:
                        logger.warning(f"No se pudo eliminar archivo temporal {path} después de {max_attempts} intentos: {e}")
                except OSError as e:
                    logger.error(f"Error al eliminar archivo temporal {path}: {e}")
                    break  # Para otros errores, no reintentar

def load_particle_data(filename: str) -> Tuple[Optional[List], Optional[List]]:
    """
    Carga y valida un archivo de datos de partículas LHC desde sample_data.
    Versión mejorada con validaciones de seguridad y manejo robusto de errores.
    
    Args:
        filename: Nombre del archivo a cargar
        
    Returns:
        Tuple[lines, particles] si es exitoso, (None, None) si hay error
        
    Raises:
        ValueError: Si el formato del archivo es inválido
        FileNotFoundError: Si el archivo no existe
        OSError: Si hay error de E/O
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("filename debe ser un string no vacío")
    
    # Sanitizar nombre de archivo
    filename = os.path.basename(filename)  # Prevenir path traversal
    
    # Validar extensión
    if not filename.lower().endswith('.txt'):
        raise ValueError(f"El archivo '{filename}' debe ser un archivo de texto (.txt)")
    
    try:
        # Construir ruta segura hacia sample_data
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lhc_sample_data_dir = os.path.join(script_dir, '..', '..', 'lhc', 'sample_data', 'lhc')
        lhc_sample_data_dir = os.path.normpath(lhc_sample_data_dir)
        full_path = os.path.join(lhc_sample_data_dir, filename)
        
        # Validar que la ruta esté dentro del directorio permitido
        if not full_path.startswith(lhc_sample_data_dir):
            raise ValueError("Acceso al archivo no permitido")
        
        # Verificar que el archivo existe
        if not os.path.exists(full_path):
            available_files = get_available_data_files()
            raise FileNotFoundError(
                f"No se encontró el archivo '{filename}'. "
                f"Archivos disponibles: {available_files}"
            )
        
        # Validar tamaño del archivo
        validate_file_size(full_path)
        
        # Leer archivo con timeout y límites
        logger.info(f"Cargando archivo de datos: {full_path}")
        
        with _global_lock:  # Thread-safe file operations
            lines = lhc_data.openfile(full_path)
        
        if not lines:
            raise ValueError(f"El archivo '{filename}' está vacío o no se pudo leer")
        
        # Validar número de líneas
        if len(lines) > 100000:  # Límite razonable
            raise ValueError(f"El archivo '{filename}' es demasiado grande ({len(lines)} líneas)")
        
        # Procesar contenido con validación
        with _global_lock:
            particles = lhc_data.read_content(lines)
        
        if not particles:
            raise ValueError(f"No se encontraron datos de partículas válidos en '{filename}'")
        
        # Validar estructura de datos
        if not validate_particle_data(particles):
            raise ValueError(f"El archivo '{filename}' contiene datos de partículas inválidos")
        
        # Validar número de eventos
        num_events = len(particles) // 2
        if num_events > MAX_EVENTS_PER_FILE:
            raise ValueError(
                f"Demasiados eventos en el archivo: {num_events}. "
                f"Máximo permitido: {MAX_EVENTS_PER_FILE}"
            )
        
        logger.info(f"Archivo cargado exitosamente: {num_events} eventos encontrados")
        return lines, particles
        
    except Exception as e:
        logger.error(f"Error cargando '{filename}': {str(e)}")
        if isinstance(e, (ValueError, FileNotFoundError, OSError)):
            raise
        else:
            raise OSError(f"Error inesperado cargando archivo: {str(e)}")


@lru_cache(maxsize=32)
def get_available_data_files() -> List[str]:
    """
    Obtiene la lista de archivos de datos LHC disponibles.
    Versión cacheada y thread-safe.
    
    Returns:
        Lista de nombres de archivos .txt disponibles
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lhc_sample_data_dir = os.path.join(script_dir, '..', '..', 'lhc', 'sample_data', 'lhc')
        lhc_sample_data_dir = os.path.normpath(lhc_sample_data_dir)
        
        if not os.path.exists(lhc_sample_data_dir):
            logger.warning(f"Directorio de datos no encontrado: {lhc_sample_data_dir}")
            return []
        
        files = []
        for filename in os.listdir(lhc_sample_data_dir):
            if filename.endswith('.txt') and os.path.isfile(os.path.join(lhc_sample_data_dir, filename)):
                files.append(filename)
        
        logger.debug(f"Archivos disponibles encontrados: {files}")
        return sorted(files)
        
    except Exception as e:
        logger.error(f"Error obteniendo archivos disponibles: {e}")
        return []


def validate_particle_data(particles) -> bool:
    """
    Valida que los datos de partículas tengan la estructura correcta.
    Versión mejorada con validaciones exhaustivas.
    
    Args:
        particles: Datos de partículas cargados
        
    Returns:
        True si los datos son válidos, False en caso contrario
    """
    if not particles or not isinstance(particles, list):
        return False
    
    if len(particles) < 2:
        return False
    
    # Verificar que haya un número par de elementos (tracks + clusters)
    if len(particles) % 2 != 0:
        return False
    
    # Verificar que cada evento tenga tracks y clusters válidos
    for i in range(0, len(particles), 2):
        if i + 1 >= len(particles):
            return False
        
        tracks = particles[i]
        clusters = particles[i + 1]
        
        if not isinstance(tracks, list) or not isinstance(clusters, list):
            return False
        
        # Validar que no haya listas vacías en eventos centrales
        # (primeros y últimos eventos pueden estar vacíos)
        if i > 0 and i < len(particles) - 2:
            if len(tracks) == 0 and len(clusters) == 0:
                logger.warning(f"Evento {i//2} está vacío")
                # No devolver False, solo advertir
    
    return True


@lru_cache(maxsize=128)
def get_total_events(filename: str) -> int:
    """
    Obtiene el número total de eventos en un archivo.
    Versión cacheada para mejor rendimiento.
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        Número total de eventos (0 si hay error)
    """
    cache_key = f"total_events_{filename}"
    
    with _cache_lock:
        # Verificar caché manual con TTL
        if cache_key in _events_cache:
            cache_time, cached_value = _events_cache[cache_key]
            if time.time() - cache_time < 300:  # 5 minutos TTL
                return cached_value
    
    try:
        lines, particles = load_particle_data(filename)
        if particles is None:
            return 0
        
        total_events = len(particles) // 2
        
        # Guardar en caché
        with _cache_lock:
            _events_cache[cache_key] = (time.time(), total_events)
        
        return total_events
        
    except Exception as e:
        logger.error(f"Error obteniendo total de eventos para '{filename}': {e}")
        return 0

def process_single_event(filename, event_index):
    """
    Procesa un solo evento LHC y retorna archivos temporales de imágenes y sonidos.

    Args:
        filename (str): Nombre del archivo de datos a procesar
        event_index (int): Índice del evento a procesar (empezando desde 0 - interno)
        
    Returns:
        tuple: (image_paths, sound_paths, event_info) donde:
               - image_paths: lista de rutas a archivos temporales de imágenes
               - sound_paths: lista de rutas a archivos temporales de sonidos
               - event_info: dict con información del evento
               - (None, None, None) si hay error
    """
    display_event_number = event_index + 1
    
    try:
        # Cargar los datos de partículas
        lines, particles = load_particle_data(filename)
        
        if particles is None:
            return None, None, None

        # Verificar que el índice del evento sea válido
        total_events = len(particles) // 2
        if event_index < 0 or event_index >= total_events:
            return None, None, None

        # Cambiar al directorio del script para asegurar rutas correctas
        script_dir = os.path.dirname(os.path.abspath(__file__))
        original_dir = os.getcwd()
        os.chdir(script_dir)

        try:
            # Configurar matplotlib para generar figuras sin mostrarlas
            plt.ioff()  # Desactivar modo interactivo
            
            # Inicializar sonificación
            lhc_data.lhc_sonification.sound_init()
            lhc_data.lhc_sonification.set_bip()
            
            image_paths = []
            sound_paths = []
            
            # Calcular el índice real en el array de partículas
            i = event_index * 2
            
            # Configurar nueva figura para este evento
            fig = plt.figure(figsize=(12, 6), dpi=100)
            lhc_data.lhc_plot.plot3D_init(fig)
            
            # Reset sound for the complete dataset
            lhc_data.lhc_sonification.reset_sound_to_save()
            
            # Obtener datos del evento
            tracks_data = particles[i] if i < len(particles) else []
            clusters_data = particles[i + 1] if i + 1 < len(particles) else []
            
            # Lista para acumular todos los sonidos del evento
            accumulated_sounds = []
            
            # Procesar tracks individualmente
            for track_index, track in enumerate(tracks_data):
                try:
                    # Reset sound before generating new one
                    lhc_data.lhc_sonification.reset_sound_to_save()
                    
                    # Generar sonificación para este track específico
                    lhc_data.particles_sonification(
                        track_index, 'Track', 
                        tracks_data, clusters_data, 
                        individual_sound=True, play_sound_status=False
                    )
                    
                    # Obtener el sonido generado
                    last_sound = lhc_data.get_last_generated_sound()
                    
                    # Acumular sonido para el audio completo
                    if last_sound is not None and len(last_sound) > 0:
                        accumulated_sounds.append(last_sound.copy())
                    
                except Exception as e:
                    logger.error(f"Error procesando track {track_index} del evento {display_event_number}: {str(e)}")
                    last_sound = None
                
                # Crear archivo temporal de sonido
                if last_sound is not None and len(last_sound) > 0:
                    sound_temp_path = process_sound_array(last_sound)
                    sound_paths.append(sound_temp_path)
                else:
                    silence = np.zeros(44100 * 2, dtype=np.int16)
                    sound_temp_path = process_sound_array(silence)
                    sound_paths.append(sound_temp_path)
                
                # Crear archivo temporal de imagen
                image_temp_path = plot_to_temp_file(fig)
                image_paths.append(image_temp_path)
            
            # Procesar clusters individualmente
            for cluster_index, cluster in enumerate(clusters_data):
                try:
                    # Reset sound before generating new one
                    lhc_data.lhc_sonification.reset_sound_to_save()
                    
                    # Generar sonificación para este cluster específico
                    lhc_data.particles_sonification(
                        cluster_index, 'Cluster', 
                        tracks_data, clusters_data, 
                        individual_sound=True, play_sound_status=False
                    )
                    
                    # Obtener el sonido generado
                    last_sound = lhc_data.get_last_generated_sound()
                    
                    # Acumular sonido para el audio completo
                    if last_sound is not None and len(last_sound) > 0:
                        accumulated_sounds.append(last_sound.copy())
                    
                except Exception as e:
                    logger.error(f"Error procesando cluster {cluster_index} del evento {display_event_number}: {str(e)}")
                    last_sound = None
                
                # Crear archivo temporal de sonido
                if last_sound is not None and len(last_sound) > 0:
                    sound_temp_path = process_sound_array(last_sound)
                    sound_paths.append(sound_temp_path)
                else:
                    silence = np.zeros(44100 * 2, dtype=np.int16)
                    sound_temp_path = process_sound_array(silence)
                    sound_paths.append(sound_temp_path)
                
                # Crear archivo temporal de imagen
                image_temp_path = plot_to_temp_file(fig)
                image_paths.append(image_temp_path)
            
            # Generar sonido completo del evento
            try:
                # Concatenar todos los sonidos acumulados
                if accumulated_sounds:
                    complete_sound = np.concatenate(accumulated_sounds)
                else:
                    complete_sound = np.zeros(44100 * 3, dtype=np.int16)
                    
            except Exception as e:
                logger.error(f"Error generando audio completo para evento {event_index}: {str(e)}")
                complete_sound = np.zeros(44100 * 3, dtype=np.int16)
            
            # Guardar audio completo como archivo temporal
            sound_temp_path = process_sound_array(complete_sound)
            sound_paths.append(sound_temp_path)
            
            # Guardar imagen completa del evento como archivo temporal
            image_temp_path = plot_to_temp_file(fig)
            image_paths.append(image_temp_path)
            
            # Limpiar plot
            lhc_data.lhc_plot.plot_reset()
            plt.close(fig)
            
            plt.ion()  # Reactivar modo interactivo
            
            # Información del evento
            event_info = {
                'event_number': display_event_number,
                'event_index': display_event_number,
                'total_events': total_events,
                'total_tracks': len(tracks_data),
                'total_clusters': len(clusters_data),
                'total_elements': len(tracks_data) + len(clusters_data)
            }
            
            logger.info(f"Evento {display_event_number}/{total_events} procesado: {len(tracks_data)} tracks, {len(clusters_data)} clusters")
            
            return image_paths, sound_paths, event_info
            
        finally:
            # Restaurar directorio original
            os.chdir(original_dir)
            plt.ion()  # Asegurar que el modo interactivo se reactive
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento del evento {display_event_number if 'display_event_number' in locals() else event_index + 1}: {str(e)}")
        plt.ion()  # Asegurar que el modo interactivo se reactive en caso de error
        return None, None, None


def process_files(path, target_filename, ext='txt', plot_flag=False, event_index=None, save_to_output=False):
    """
    Interfaz principal optimizada para la aplicación web LHC.
    
    Args:
        path (str): No utilizado (siempre se usa sample_data)
        target_filename (str): Nombre del archivo a procesar
        ext (str): No utilizado para LHC
        plot_flag (bool): No utilizado (nunca se generan plots)
        event_index (int, optional): Índice del evento a procesar (1-based). Si es None, procesa el evento 1
        save_to_output (bool): No utilizado (siempre usa archivos temporales)
        
    Returns:
        tuple: (image_paths, sound_paths, event_info) o (None, None, None) si hay error
    """
    # Si no se especifica índice, usar el evento 1 (1-based)
    if event_index is None:
        event_index = 1
    
    # Convertir a índice interno (0-based) para process_single_event
    internal_event_index = event_index - 1
    
    # Llamar a process_single_event con índice 0-based interno
    return process_single_event(target_filename, internal_event_index)

# Alias for compatibility
cleanup_temp_audio = cleanup_temp_files
