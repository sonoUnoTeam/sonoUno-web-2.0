# -*- coding: utf-8 -*-
"""
Módulo LHC mejorado para integración con Django web app.
Proporciona funciones seguras y optimizadas para procesar datos LHC.

MEJORAS IMPLEMENTADAS:
- Validación exhaustiva de inputs
- Manejo robusto de errores con logging
- Gestión mejorada de recursos y memoria
- Thread-safety para operaciones críticas
- Optimizaciones de rendimiento

Funciones principales:
- load_particle_data(): Carga y valida archivos de datos LHC (mejorada)
- get_available_data_files(): Lista archivos disponibles (thread-safe)
- validate_particle_data(): Valida estructura de datos (robusta)
- process_files(): Interfaz compatible con muongraphy (optimizada)
- process_single_event(): Procesa eventos individuales (thread-safe)
- get_total_events(): Obtiene número total de eventos (cacheada)
- cleanup_temp_files(): Limpieza mejorada de archivos temporales

Compatible tanto para uso web (Django) como script independiente.
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
TEMP_FILE_TIMEOUT = 3600  # 1 hora
DEFAULT_OUTPUT_SIZE = (1200, 600)  # Tamaño estándar para videos

def get_output_directory():
    """
    Obtiene el directorio de salida para archivos LHC (data_lhc/lhc_output).
    Crea el directorio si no existe de forma thread-safe.
    
    Returns:
        str: Ruta absoluta al directorio de salida
        
    Raises:
        OSError: Si no se puede crear el directorio
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'data_lhc', 'lhc_output')
    
    with _global_lock:
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Directorio de salida creado: {output_dir}")
            except OSError as e:
                logger.error(f"Error creando directorio de salida: {e}")
                raise
    
    return output_dir


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


def plot_to_output_file(fig, filename_prefix, event_index, element_type, element_index=None):
    """
    Guarda una figura de matplotlib en el directorio de salida con nombre descriptivo.
    Versión mejorada con manejo robusto de errores y validación.
    
    Args:
        fig: Figura de matplotlib
        filename_prefix (str): Prefijo del nombre del archivo (nombre del dataset)
        event_index (int): Índice del evento
        element_type (str): Tipo de elemento ('track', 'cluster', 'complete')
        element_index (int, optional): Índice del elemento específico
        
    Returns:
        str: Ruta al archivo creado
        
    Raises:
        ValueError: Si los parámetros son inválidos
        OSError: Si hay error escribiendo el archivo
    """
    if not fig:
        raise ValueError("Figure requerida")
    
    if not filename_prefix or not isinstance(filename_prefix, str):
        raise ValueError("filename_prefix debe ser un string no vacío")
    
    if not isinstance(event_index, int) or event_index < 0:
        raise ValueError("event_index debe ser un entero no negativo")
    
    if element_type not in ['track', 'cluster', 'complete']:
        raise ValueError("element_type debe ser 'track', 'cluster' o 'complete'")
    
    try:
        output_dir = get_output_directory()
        
        # Generar nombre de archivo seguro
        safe_prefix = "".join(c for c in filename_prefix if c.isalnum() or c in "._-")
        if element_index is not None:
            filename = f"plot_{safe_prefix}_event_{event_index}_{element_type}_{element_index}.png"
        else:
            filename = f"plot_{safe_prefix}_event_{event_index}_{element_type}.png"
        
        output_path = os.path.join(output_dir, filename)
        
        # Configurar figura con dimensiones estándar
        fig.set_size_inches(DEFAULT_OUTPUT_SIZE[0]/100, DEFAULT_OUTPUT_SIZE[1]/100)
        fig.tight_layout(pad=2.0)
        
        # Guardar con configuración optimizada
        fig.savefig(
            output_path, 
            format='png', 
            dpi=100, 
            bbox_inches='tight',
            facecolor='white', 
            edgecolor='none', 
            pad_inches=0.1
        )
        
        # Verificar que el archivo se creó correctamente
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise OSError(f"Error creando archivo de imagen: {output_path}")
        
        # Optimizar imagen usando PIL
        _optimize_image_file(output_path)
        
        logger.debug(f"Imagen guardada: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error guardando imagen: {e}")
        raise


def _optimize_image_file(image_path: str) -> None:
    """
    Optimiza un archivo de imagen para dimensiones estándar de video.
    
    Args:
        image_path: Ruta al archivo de imagen
    """
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            # Asegurar dimensiones exactas
            if img.size != DEFAULT_OUTPUT_SIZE:
                # Redimensionar manteniendo proporción y centrando
                img_resized = Image.new('RGB', DEFAULT_OUTPUT_SIZE, 'white')
                
                # Calcular escala para mantener proporción
                scale = min(
                    DEFAULT_OUTPUT_SIZE[0] / img.size[0], 
                    DEFAULT_OUTPUT_SIZE[1] / img.size[1]
                )
                new_size = (
                    int(img.size[0] * scale), 
                    int(img.size[1] * scale)
                )
                
                # Redimensionar y centrar
                img_scaled = img.resize(new_size, Image.Resampling.LANCZOS)
                x_offset = (DEFAULT_OUTPUT_SIZE[0] - new_size[0]) // 2
                y_offset = (DEFAULT_OUTPUT_SIZE[1] - new_size[1]) // 2
                img_resized.paste(img_scaled, (x_offset, y_offset))
                
                # Sobrescribir archivo optimizado
                img_resized.save(image_path, 'PNG', optimize=True)
                img_resized.close()
                img_scaled.close()
                
    except Exception as e:
        logger.warning(f"Error optimizando imagen {image_path}: {e}")


def process_sound_to_output_file(sound_array, filename_prefix, event_index, element_type, element_index=None):
    """
    Convierte un array de numpy a archivo WAV en el directorio de salida.
    
    Args:
        sound_array (numpy.array): Array de datos de audio
        filename_prefix (str): Prefijo del nombre del archivo (nombre del dataset)
        event_index (int): Índice del evento
        element_type (str): Tipo de elemento ('track', 'cluster', 'complete')
        element_index (int, optional): Índice del elemento específico
        
    Returns:
        str: Ruta al archivo WAV creado
    """
    if sound_array is None or len(sound_array) == 0:
        # Crear silencio de 2 segundos si no hay datos
        sound_array = np.zeros(44100 * 2, dtype=np.int16)
    
    output_dir = get_output_directory()
    
    if element_index is not None:
        filename = f"sound_{filename_prefix}_event_{event_index}_{element_type}_{element_index}.wav"
    else:
        filename = f"sound_{filename_prefix}_event_{event_index}_{element_type}.wav"
    
    output_path = os.path.join(output_dir, filename)
    
    # Asegurar formato correcto (44.1kHz, 16-bit)
    wavfile.write(
        output_path,
        rate=44100,
        data=sound_array.astype(np.int16)
    )
    
    return output_path

def plot_to_temp_file(fig):
    """
    Guarda una figura de matplotlib como archivo temporal.
    
    Args:
        fig: Figura de matplotlib
        
    Returns:
        str: Ruta al archivo temporal creado
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
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
    
    Args:
        sound_array (numpy.array): Array de datos de audio
        
    Returns:
        str: Ruta al archivo WAV temporal creado
    """
    if sound_array is None or len(sound_array) == 0:
        # Crear silencio de 2 segundos si no hay datos
        sound_array = np.zeros(44100 * 2, dtype=np.int16)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
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
    
    for path in file_paths:
        if path and os.path.exists(path):
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    os.remove(path)
                    break  # Éxito, salir del loop de reintentos
                except PermissionError as e:
                    if attempt < max_attempts - 1:
                        # Esperar un poco antes del siguiente intento
                        time.sleep(0.5)
                        print(f"Reintentando eliminar archivo temporal {path} (intento {attempt + 2}/{max_attempts})")
                    else:
                        print(f"No se pudo eliminar archivo temporal {path} después de {max_attempts} intentos: {e}")
                except OSError as e:
                    print(f"Error al eliminar archivo temporal {path}: {e}")
                    break  # Para otros errores, no reintentar

def cleanup_output_files(file_paths=None, cleanup_all=False):
    """
    Limpia archivos del directorio de salida data_lhc/lhc_output.
    
    Args:
        file_paths (list, optional): Lista específica de archivos a eliminar
        cleanup_all (bool): Si True, elimina todos los archivos del directorio de salida
    """
    import time
    output_dir = get_output_directory()
    
    if cleanup_all:
        # Eliminar todos los archivos del directorio de salida
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                file_path = os.path.join(output_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Archivo eliminado: {filename}")
                    except Exception as e:
                        print(f"Error al eliminar {filename}: {e}")
    
    elif file_paths:
        # Eliminar archivos específicos con reintentos
        for path in file_paths:
            if path and os.path.exists(path):
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        os.remove(path)
                        print(f"Archivo de salida eliminado: {os.path.basename(path)}")
                        break  # Éxito, salir del loop de reintentos
                    except PermissionError as e:
                        if attempt < max_attempts - 1:
                            # Esperar un poco antes del siguiente intento
                            time.sleep(0.5)
                            print(f"Reintentando eliminar archivo de salida {path} (intento {attempt + 2}/{max_attempts})")
                        else:
                            print(f"No se pudo eliminar archivo de salida {path} después de {max_attempts} intentos: {e}")
                    except OSError as e:
                        print(f"Error al eliminar archivo de salida {path}: {e}")
                        break  # Para otros errores, no reintentar

def list_output_files():
    """
    Lista todos los archivos en el directorio de salida data_lhc/lhc_output.
    
    Returns:
        dict: Diccionario con listas de archivos por tipo ('images', 'sounds', 'other')
    """
    output_dir = get_output_directory()
    files_by_type = {'images': [], 'sounds': [], 'other': []}
    
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    files_by_type['images'].append(filename)
                elif filename.lower().endswith(('.wav', '.mp3')):
                    files_by_type['sounds'].append(filename)
                else:
                    files_by_type['other'].append(filename)
    
    return files_by_type

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
        lines = lhc_data.openfile(full_path)
        
        if not lines:
            raise ValueError(f"El archivo '{filename}' está vacío o no se pudo leer")
        
        # Procesar el contenido del archivo
        particles = lhc_data.read_content(lines)
        
        if not particles:
            raise ValueError(f"No se encontraron datos de partículas válidos en '{filename}'")
        
        # Validar que hay datos suficientes (al menos un evento con tracks y clusters)
        if len(particles) < 2:
            raise ValueError(f"El archivo '{filename}' no contiene suficientes datos (necesita al menos tracks y clusters)")
        
        print(f"Archivo cargado exitosamente: {len(particles)//2} eventos encontrados")
        return lines, particles
        
    except Exception as e:
        print(f"Error al cargar '{filename}': {str(e)}")
        return None, None

def process_lhc_files(filename="sonification_reduced.txt"):
    """
    Procesa datos LHC y retorna listas de archivos temporales de imágenes y sonidos
    para crear videos, compatible con la interfaz de muongraphy.
    
    Args:
        filename (str): Nombre del archivo de datos a procesar
        
    Returns:
        tuple: (image_paths, sound_paths) donde cada uno es una lista de rutas
               a archivos temporales, o (None, None) si hay error
    """
    try:
        # Cargar los datos de partículas
        lines, particles = load_particle_data(filename)
        
        if particles is None:
            return None, None

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
            
            # Procesar cada evento (conjunto de tracks y clusters)
            for i in range(0, len(particles), 2):
                event_num = (i // 2) + 1
                
                # Configurar nueva figura para este evento con tamaño y configuración fijos
                plt.close('all')  # Cerrar todas las figuras anteriores
                fig = plt.figure(figsize=(12, 6), dpi=100)
                fig.clear()  # Limpiar la figura
                
                # Configurar subplot con límites fijos para evitar desplazamientos
                ax = fig.add_subplot(111, projection='3d')
                
                # Establecer límites fijos para evitar que la vista cambie entre frames
                ax.set_xlim([-100, 100])
                ax.set_ylim([-100, 100])
                ax.set_zlim([-100, 100])
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
                
                lhc_data.lhc_plot.plot3D_init(fig)
                
                # Reset sound for the complete dataset
                lhc_data.lhc_sonification.reset_sound_to_save()
                
                # Procesar tracks individualmente
                tracks_data = particles[i] if i < len(particles) else []
                clusters_data = particles[i + 1] if i + 1 < len(particles) else []
                
                # Lista para acumular sonidos del evento (optimización)
                event_accumulated_sounds = []
                
                for track_index, track in enumerate(tracks_data):
                    # Limpiar completamente la figura antes de dibujar nuevo elemento
                    fig.clear()
                    
                    # Recrear el subplot con configuración consistente
                    ax = fig.add_subplot(111, projection='3d')
                    ax.set_xlim([-100, 100])
                    ax.set_ylim([-100, 100])
                    ax.set_zlim([-100, 100])
                    ax.set_xlabel('X')
                    ax.set_ylabel('Y')
                    ax.set_zlabel('Z')
                    
                    # Reinicializar el plot para este elemento específico
                    lhc_data.lhc_plot.plot3D_init(fig)
                    
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
                    
                    # Acumular sonido para el evento completo
                    if last_sound is not None and len(last_sound) > 0:
                        event_accumulated_sounds.append(last_sound.copy())
                    
                    # Crear archivo temporal de sonido
                    if last_sound is not None and len(last_sound) > 0:
                        sound_temp_path = process_sound_array(last_sound)
                        sound_paths.append(sound_temp_path)
                    else:
                        # Crear silencio si no hay sonido
                        silence = np.zeros(44100 * 2, dtype=np.int16)
                        sound_temp_path = process_sound_array(silence)
                        sound_paths.append(sound_temp_path)
                    
                    # Crear archivo temporal de imagen para este track
                    image_temp_path = plot_to_temp_file(fig)
                    image_paths.append(image_temp_path)
                
                # Procesar clusters individualmente
                for cluster_index, cluster in enumerate(clusters_data):
                    # Limpiar completamente la figura antes de dibujar nuevo elemento
                    fig.clear()
                    
                    # Recrear el subplot con configuración consistente
                    ax = fig.add_subplot(111, projection='3d')
                    ax.set_xlim([-100, 100])
                    ax.set_ylim([-100, 100])
                    ax.set_zlim([-100, 100])
                    ax.set_xlabel('X')
                    ax.set_ylabel('Y')
                    ax.set_zlabel('Z')
                    
                    # Reinicializar el plot para este elemento específico
                    lhc_data.lhc_plot.plot3D_init(fig)
                    
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
                    
                    # Acumular sonido para el evento completo
                    if last_sound is not None and len(last_sound) > 0:
                        event_accumulated_sounds.append(last_sound.copy())
                    
                    # Crear archivo temporal de sonido
                    if last_sound is not None and len(last_sound) > 0:
                        sound_temp_path = process_sound_array(last_sound)
                        sound_paths.append(sound_temp_path)
                    else:
                        # Crear silencio si no hay sonido
                        silence = np.zeros(44100 * 2, dtype=np.int16)
                        sound_temp_path = process_sound_array(silence)
                        sound_paths.append(sound_temp_path)
                    
                    # Crear archivo temporal de imagen para este cluster
                    image_temp_path = plot_to_temp_file(fig)
                    image_paths.append(image_temp_path)
                
                # Generar sonido completo del evento de forma optimizada
                try:
                    # En lugar de regenerar todo, concatenar los sonidos ya procesados
                    if event_accumulated_sounds:
                        # Concatenar todos los sonidos acumulados del evento
                        complete_sound = np.concatenate(event_accumulated_sounds)
                        print(f"Evento {event_num}: Audio completo generado por concatenación ({len(complete_sound)} samples)")
                    else:
                        # Si no hay sonidos acumulados, crear silencio
                        complete_sound = np.zeros(44100 * 3, dtype=np.int16)
                        print(f"Evento {event_num}: No hay sonidos acumulados, generando silencio")
                        
                    sound_temp_path = process_sound_array(complete_sound)
                    sound_paths.append(sound_temp_path)
                    
                except Exception as e:
                    print(f"Error generando audio completo para evento {event_num}: {str(e)}")
                    # Fallback: crear silencio
                    silence = np.zeros(44100 * 3, dtype=np.int16)
                    sound_temp_path = process_sound_array(silence)
                    sound_paths.append(sound_temp_path)
                
                # Generar imagen completa del evento con todos los elementos
                try:
                    # Limpiar completamente la figura para la imagen final
                    fig.clear()
                    
                    # Recrear el subplot con configuración consistente
                    ax = fig.add_subplot(111, projection='3d')
                    ax.set_xlim([-100, 100])
                    ax.set_ylim([-100, 100])
                    ax.set_zlim([-100, 100])
                    ax.set_xlabel('X')
                    ax.set_ylabel('Y')
                    ax.set_zlabel('Z')
                    
                    # Reinicializar el plot para la imagen completa
                    lhc_data.lhc_plot.plot3D_init(fig)
                    
                    # Dibujar todos los tracks del evento
                    for track_index in range(len(tracks_data)):
                        lhc_data.particles_sonification(
                            track_index, 'Track', 
                            tracks_data, clusters_data, 
                            individual_sound=False, play_sound_status=False
                        )
                    
                    # Dibujar todos los clusters del evento
                    for cluster_index in range(len(clusters_data)):
                        lhc_data.particles_sonification(
                            cluster_index, 'Cluster', 
                            tracks_data, clusters_data, 
                            individual_sound=False, play_sound_status=False
                        )
                    
                    print(f"Evento {event_num}: Imagen completa generada con {len(tracks_data)} tracks y {len(clusters_data)} clusters")
                    
                except Exception as e:
                    print(f"Error generando imagen completa para evento {event_num}: {str(e)}")
                
                # Guardar imagen completa del evento
                image_temp_path = plot_to_temp_file(fig)
                image_paths.append(image_temp_path)
                
                # Limpiar plot para el siguiente evento
                lhc_data.lhc_plot.plot_reset()
                plt.close(fig)
            
            plt.ion()  # Reactivar modo interactivo
            
            print(f"Procesamiento LHC completado: {len(image_paths)} imágenes y {len(sound_paths)} sonidos generados")
            return image_paths, sound_paths
            
        finally:
            # Restaurar directorio original
            os.chdir(original_dir)
            plt.ion()  # Asegurar que el modo interactivo se reactive
        
    except Exception as e:
        print(f"Error durante el procesamiento LHC: {str(e)}")
        plt.ion()  # Asegurar que el modo interactivo se reactive en caso de error
        return None, None

def get_total_events(filename="sonification_reduced.txt"):
    """
    Obtiene el número total de eventos en un archivo LHC.
    
    Args:
        filename (str): Nombre del archivo de datos a analizar
        
    Returns:
        int: Número total de eventos, o 0 si hay error
    """
    try:
        lines, particles = load_particle_data(filename)
        if particles is None:
            return 0
        return len(particles) // 2
    except Exception as e:
        print(f"Error al obtener total de eventos: {str(e)}")
        return 0

def process_single_event(filename="sonification_reduced.txt", event_index=0, save_to_output=True, display_event_number=None, generate_complete_audio=True):
    """
    Procesa un solo evento LHC y retorna archivos de imágenes y sonidos.
    
    Args:
        filename (str): Nombre del archivo de datos a procesar
        event_index (int): Índice del evento a procesar (empezando desde 0 - interno)
        save_to_output (bool): Si True, guarda en data_lhc/lhc_output; si False, usa archivos temporales
        display_event_number (int, optional): Número de evento para mostrar (1-based). Si es None, usa event_index + 1
        generate_complete_audio (bool): Si True, genera el audio completo del evento; si False, lo omite para optimización
        
    Returns:
        tuple: (image_paths, sound_paths, event_info) donde:
               - image_paths: lista de rutas a archivos de imágenes
               - sound_paths: lista de rutas a archivos de sonidos
               - event_info: dict con información del evento (número, total_tracks, total_clusters)
               - (None, None, None) si hay error
    """
    # Si no se especifica display_event_number, calcular desde event_index (0-based -> 1-based)
    if display_event_number is None:
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
            
            # La función plot3D_init ya configura correctamente los dos subplots (transversal y longitudinal)
            # No necesitamos configuración adicional aquí
            
            # Reset sound for the complete dataset
            lhc_data.lhc_sonification.reset_sound_to_save()
            
            # Obtener datos del evento
            tracks_data = particles[i] if i < len(particles) else []
            clusters_data = particles[i + 1] if i + 1 < len(particles) else []
            
            # Obtener nombre base del archivo sin extensión
            filename_base = os.path.splitext(filename)[0]
            
            # Lista para acumular todos los sonidos del evento (optimización de rendimiento)
            accumulated_sounds = []
            
            # Procesar tracks individualmente - SIN resetear el plot para acumular trayectorias
            for track_index, track in enumerate(tracks_data):
                try:
                    # Reset sound before generating new one (pero mantener plot acumulativo)
                    lhc_data.lhc_sonification.reset_sound_to_save()
                    
                    # Generar sonificación para este track específico
                    lhc_data.particles_sonification(
                        track_index, 'Track', 
                        tracks_data, clusters_data, 
                        individual_sound=True, play_sound_status=False
                    )
                    
                    # Obtener el sonido generado
                    last_sound = lhc_data.get_last_generated_sound()
                    
                    # Acumular sonido para el audio completo (optimización)
                    if last_sound is not None and len(last_sound) > 0:
                        accumulated_sounds.append(last_sound.copy())
                    
                except Exception as e:
                    print(f"Error procesando track {track_index} del evento {display_event_number}: {str(e)}")
                    last_sound = None
                
                # Crear archivo de sonido
                if save_to_output:
                    if last_sound is not None and len(last_sound) > 0:
                        sound_path = process_sound_to_output_file(last_sound, filename_base, display_event_number, 'track', track_index)
                    else:
                        # Crear silencio si no hay sonido
                        silence = np.zeros(44100 * 2, dtype=np.int16)
                        sound_path = process_sound_to_output_file(silence, filename_base, display_event_number, 'track', track_index)
                    sound_paths.append(sound_path)
                else:
                    # Usar archivos temporales para compatibilidad
                    if last_sound is not None and len(last_sound) > 0:
                        sound_temp_path = process_sound_array(last_sound)
                        sound_paths.append(sound_temp_path)
                    else:
                        silence = np.zeros(44100 * 2, dtype=np.int16)
                        sound_temp_path = process_sound_array(silence)
                        sound_paths.append(sound_temp_path)
                
                # Crear archivo de imagen
                if save_to_output:
                    image_path = plot_to_output_file(fig, filename_base, display_event_number, 'track', track_index)
                    image_paths.append(image_path)
                else:
                    # Usar archivos temporales para compatibilidad
                    image_temp_path = plot_to_temp_file(fig)
                    image_paths.append(image_temp_path)
            
            # Procesar clusters individualmente - SIN resetear el plot para acumular trayectorias
            for cluster_index, cluster in enumerate(clusters_data):
                try:
                    # Reset sound before generating new one (pero mantener plot acumulativo)
                    lhc_data.lhc_sonification.reset_sound_to_save()
                    
                    # Generar sonificación para este cluster específico
                    lhc_data.particles_sonification(
                        cluster_index, 'Cluster', 
                        tracks_data, clusters_data, 
                        individual_sound=True, play_sound_status=False
                    )
                    
                    # Obtener el sonido generado
                    last_sound = lhc_data.get_last_generated_sound()
                    
                    # Acumular sonido para el audio completo (optimización)
                    if last_sound is not None and len(last_sound) > 0:
                        accumulated_sounds.append(last_sound.copy())
                    
                except Exception as e:
                    print(f"Error procesando cluster {cluster_index} del evento {display_event_number}: {str(e)}")
                    last_sound = None
                
                # Crear archivo de sonido
                if save_to_output:
                    if last_sound is not None and len(last_sound) > 0:
                        sound_path = process_sound_to_output_file(last_sound, filename_base, display_event_number, 'cluster', cluster_index)
                    else:
                        silence = np.zeros(44100 * 2, dtype=np.int16)
                        sound_path = process_sound_to_output_file(silence, filename_base, display_event_number, 'cluster', cluster_index)
                    sound_paths.append(sound_path)
                else:
                    # Usar archivos temporales para compatibilidad
                    if last_sound is not None and len(last_sound) > 0:
                        sound_temp_path = process_sound_array(last_sound)
                        sound_paths.append(sound_temp_path)
                    else:
                        silence = np.zeros(44100 * 2, dtype=np.int16)
                        sound_temp_path = process_sound_array(silence)
                        sound_paths.append(sound_temp_path)
                
                # Crear archivo de imagen
                if save_to_output:
                    image_path = plot_to_output_file(fig, filename_base, display_event_number, 'cluster', cluster_index)
                    image_paths.append(image_path)
                else:
                    # Usar archivos temporales para compatibilidad
                    image_temp_path = plot_to_temp_file(fig)
                    image_paths.append(image_temp_path)
            
            # Generar sonido completo del evento solo si está habilitado
            if generate_complete_audio:
                try:
                    # En lugar de regenerar todo, concatenar los sonidos ya procesados
                    if accumulated_sounds:
                        # Concatenar todos los sonidos acumulados
                        complete_sound = np.concatenate(accumulated_sounds)
                    else:
                        # Si no hay sonidos acumulados, crear silencio
                        complete_sound = np.zeros(44100 * 3, dtype=np.int16)
                        
                except Exception as e:
                    print(f"Error generando audio completo para evento {event_index}: {str(e)}")
                    # Fallback: intentar el método original solo si la concatenación falla
                    try:
                        lhc_data.lhc_sonification.reset_sound_to_save()
                        
                        # Reproducir todos los tracks y clusters del evento para sonido completo
                        for track_index in range(len(tracks_data)):
                            lhc_data.particles_sonification(
                                track_index, 'Track', 
                                tracks_data, clusters_data, 
                                play_sound_status=False
                            )
                        
                        for cluster_index in range(len(clusters_data)):
                            lhc_data.particles_sonification(
                                cluster_index, 'Cluster', 
                                tracks_data, clusters_data, 
                                play_sound_status=False
                            )
                        
                        complete_sound = lhc_data.get_last_generated_sound()
                        print("Audio completo generado usando método de respaldo")
                        
                    except Exception as e2:
                        print(f"Error en método de respaldo para evento {display_event_number}: {str(e2)}")
                        complete_sound = None
                
                # Guardar audio completo solo si está habilitado
                if save_to_output:
                    if complete_sound is not None and len(complete_sound) > 0:
                        sound_path = process_sound_to_output_file(complete_sound, filename_base, display_event_number, 'complete')
                    else:
                        silence = np.zeros(44100 * 3, dtype=np.int16)
                        sound_path = process_sound_to_output_file(silence, filename_base, display_event_number, 'complete')
                    sound_paths.append(sound_path)
                else:
                    # Usar archivos temporales para compatibilidad
                    if complete_sound is not None and len(complete_sound) > 0:
                        sound_temp_path = process_sound_array(complete_sound)
                        sound_paths.append(sound_temp_path)
                    else:
                        silence = np.zeros(44100 * 3, dtype=np.int16)
                        sound_temp_path = process_sound_array(silence)
                        sound_paths.append(sound_temp_path)
            else:
                print(f"Omitiendo generación de audio completo para evento {display_event_number} (optimización habilitada)")
            
            # Guardar imagen completa del evento
            if save_to_output:
                image_path = plot_to_output_file(fig, filename_base, display_event_number, 'complete')
                image_paths.append(image_path)
            else:
                # Usar archivos temporales para compatibilidad
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
            
            if save_to_output:
                pass
            else:
                print(f"Evento {display_event_number}/{total_events} procesado: {len(tracks_data)} tracks, {len(clusters_data)} clusters")
            
            return image_paths, sound_paths, event_info
            
        finally:
            # Restaurar directorio original
            os.chdir(original_dir)
            plt.ion()  # Asegurar que el modo interactivo se reactive
        
    except Exception as e:
        print(f"Error durante el procesamiento del evento {display_event_number if 'display_event_number' in locals() else event_index + 1}: {str(e)}")
        plt.ion()  # Asegurar que el modo interactivo se reactive en caso de error
        return None, None, None


def process_files(path, target_filename, ext='txt', plot_flag=False, event_index=None, save_to_output=True, generate_complete_audio=True):
    """
    Interfaz compatible con muongraphy para procesar archivos LHC.
    
    Args:
        path (str): Ruta (no utilizada, se usa sample_data fija)
        target_filename (str): Nombre del archivo a procesar
        ext (str): Extensión del archivo (no utilizada para LHC)
        plot_flag (bool): Flag para generar plots (no utilizada para LHC)
        event_index (int, optional): Índice del evento a procesar (1-based). Si es None, procesa el evento 1
        save_to_output (bool): Si True, guarda en data_lhc/lhc_output; si False, usa archivos temporales
        generate_complete_audio (bool): Si True, genera el audio completo del evento; si False, lo omite para optimización
        
    Returns:
        tuple: (image_paths, sound_paths, event_info) o (None, None, None) si hay error
    """
    # Si no se especifica índice, usar el evento 1 (1-based)
    if event_index is None:
        event_index = 1
    
    # Convertir a índice interno (0-based) para process_single_event
    internal_event_index = event_index - 1
    
    # Llamar a process_single_event con índice 0-based interno pero pasar event_index para nombres
    return process_single_event(target_filename, internal_event_index, save_to_output, display_event_number=event_index, generate_complete_audio=generate_complete_audio)

def get_available_data_files():
    """
    Obtiene la lista de archivos de datos LHC disponibles.
    
    Returns:
        list: Lista de nombres de archivos .txt disponibles
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lhc_sample_data_dir = os.path.join(script_dir, '..', '..', 'lhc', 'sample_data', 'lhc')
        lhc_sample_data_dir = os.path.normpath(lhc_sample_data_dir)
        
        if not os.path.exists(lhc_sample_data_dir):
            return []
        
        return [f for f in os.listdir(lhc_sample_data_dir) if f.endswith('.txt')]
    except Exception as e:
        print(f"Error al obtener archivos disponibles: {str(e)}")
        return []

def validate_particle_data(particles):
    """
    Valida que los datos de partículas tengan la estructura correcta.
    
    Args:
        particles: Datos de partículas cargados
        
    Returns:
        bool: True si los datos son válidos, False en caso contrario
    """
    if not particles:
        return False
    
    if len(particles) < 2:
        return False
    
    # Verificar que cada evento tenga tracks y clusters
    for i in range(0, len(particles), 2):
        if i + 1 >= len(particles):
            return False
        
        tracks = particles[i]
        clusters = particles[i + 1]
        
        if not isinstance(tracks, list) or not isinstance(clusters, list):
            return False
    
    return True

def debug_particle_data(filename="sonification_reduced.txt"):
    """
    Función de debugging para analizar la estructura de datos de partículas.
    
    Args:
        filename (str): Nombre del archivo de datos a analizar
    """
    try:
        lines, particles = load_particle_data(filename)
        
        if particles is None:
            print("No se pudieron cargar los datos.")
            return
        
        print(f"Total de elementos en particles: {len(particles)}")
        print(f"Eventos estimados: {len(particles) // 2}")
        
        for i in range(0, len(particles), 2):
            event_index = i // 2
            tracks = particles[i] if i < len(particles) else []
            clusters = particles[i + 1] if i + 1 < len(particles) else []
            
            print(f"Evento {event_index}: {len(tracks)} tracks, {len(clusters)} clusters")
            
            # Mostrar detalle del primer evento
            if event_index == 0:
                print(f"  Tracks detalle: {tracks[:3] if len(tracks) > 3 else tracks}...")
                print(f"  Clusters detalle: {clusters[:3] if len(clusters) > 3 else clusters}...")
                
    except Exception as e:
        print(f"Error en debug: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    Función principal para compatibilidad con script independiente.
    Demuestra el uso de las funciones de carga de datos.
    """
    data_filename = "sonification_reduced.txt"
    
    if len(sys.argv) > 1:
        data_filename = sys.argv[1]
        print(f"Usando archivo especificado: {data_filename}")
    else:
        print(f"Usando archivo por defecto: {data_filename}")
        print("Uso: python lhc_web.py [nombre_archivo.txt]")
    
    # Mostrar archivos disponibles
    print("\nArchivos disponibles:")
    available_files = get_available_data_files()
    for file in available_files:
        print(f"  - {file}")
    
    # Cargar datos
    lines, particles = load_particle_data(data_filename)
    
    if particles is None:
        print("No se pudo cargar el archivo de datos.")
        sys.exit(1)
    
    # Validar datos
    if validate_particle_data(particles):
        print("Datos válidos cargados exitosamente.")
        print(f"Total de eventos: {len(particles)//2}")
        print("Para procesamiento web completo, usar las funciones process_files o process_single_event")
    else:
        print("Los datos cargados no son válidos.")
        sys.exit(1)

# Alias para funciones de limpieza
cleanup_temp_audio = cleanup_temp_files

if __name__ == "__main__":
    main()
