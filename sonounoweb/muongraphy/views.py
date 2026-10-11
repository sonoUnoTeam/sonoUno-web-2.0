from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
from django.conf import settings
import base64
import logging
import subprocess
import os
from django.contrib import messages
from utils.muongraphy_lib.muon_bash import process_files, cleanup_temp_audio, cleanup_temp_files
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, AudioClip, concatenate_audioclips
from PIL import Image
from scipy.io.wavfile import write
import numpy as np
import tempfile

logger = logging.getLogger(__name__)

# Ejemplos de sample_data/Muongraphy-1 que la interfaz ofrece para elegir
EXAMPLES = [
    {'file_name': f'Example_{number}.csv', 'label': f'Ejemplo {number}'}
    for number in range(1, 6)
]
ALLOWED_FILE_NAMES = {example['file_name'] for example in EXAMPLES}


def index(request):
    return render(request, "muongraphy/index.html", {'examples': EXAMPLES})

def create_video_from_paths(image_paths, sound_paths):
    clips = []

    total_clips = len(image_paths)
    mid_point = total_clips // 2
    
    for i, (image_path, sound_path) in enumerate(zip(image_paths, sound_paths)):
       
        # Create audio clip from WAV file
        audio_clip = AudioFileClip(sound_path)
        
        # Add silence based on clip position
        if i == total_clips - 1:
            # Last clip - only silence
            audio_clip_final = AudioClip(lambda t: 0, duration=1, fps=44100)
        elif i == 0 or i == mid_point:
            # First and middle clips - sound + silence
            silence = AudioClip(lambda t: 0, duration=1, fps=44100)
            audio_clip_final = concatenate_audioclips([audio_clip, silence])
        else:
        # Other clips - only sound\
            audio_clip_final = audio_clip
        
        # Create image clip and set duration to match audio
        image_clip = ImageClip(image_path).set_duration(audio_clip_final.duration)
        clips.append(image_clip.set_audio(audio_clip_final))

    # Concatenate all clips
    final_clip = concatenate_videoclips(clips)
    
    # Create temporary video file
    temp_dir = os.path.join(settings.BASE_DIR, 'temp')
    logger.debug("Directorio temporal: %s", temp_dir)

    # Verificar si existe la carpeta temp y si no la crea
    if not os.path.exists(temp_dir):
        try:
            os.makedirs(temp_dir, mode=0o777, exist_ok=True)  # Crear la carpeta con permisos completos
            logger.debug("Carpeta creada: %s", temp_dir)
        except Exception as e:
            logger.error("Error al crear la carpeta temporal: %s", e)
    else:
        logger.debug("La carpeta temporal ya existe: %s", temp_dir)

    # Captura si existe un error al crear el archivo temporal
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_video_file:
            temp_video_file_path = temp_video_file.name
    except Exception as e:
        logger.error("No se pudo crear un archivo temporal: %s", e)

    logger.debug("Video temporal: %s", temp_video_file_path)
    # Set higher permissions (e.g., read/write/execute for owner and group)
    os.chmod(temp_video_file_path, 0o777)

    #with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
    #    temp_video_file_path = temp_video_file.name

    # Captura si existe un error al crear el archivo de audio temporal
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_audio_file:
            temp_audiopath = temp_audio_file.name
    except Exception as e:
        logger.error("No se pudo crear un archivo temporal: %s", e)

    logger.debug("Audio temporal: %s", temp_audiopath)

    logger.debug("Escribiendo el video")
    # Write and encode video
    final_clip.write_videofile(
        temp_video_file_path, 
        codec='libx264',
        fps=24,
        audio_codec='aac',
        temp_audiofile=temp_audiopath,
        verbose=True,           # <--- agrega esto
        logger='bar'            # <--- y esto para barra de progreso
    )
    logger.debug("Video escrito")
    # Read video into memory
    with open(temp_video_file_path, 'rb') as video_file:
        video_bytes = BytesIO(video_file.read())
    logger.debug("Video cargado en memoria")
    # Cleanup
    os.remove(temp_video_file_path)
    final_clip.close()
    
    # Convert video bytes to base64
    video_bytes.seek(0)
    video_base64 = base64.b64encode(video_bytes.read()).decode('utf-8')
    
    return video_base64

def grafico(request, file_name):
    # Solo se aceptan los ejemplos conocidos: file_name llega de la URL y no debe
    # poder apuntar fuera de sample_data (p. ej. "..\..\manage.py" en Windows)
    if file_name not in ALLOWED_FILE_NAMES:
        logger.warning("Ejemplo de muongrafía no permitido: %.80r", file_name)
        messages.error(request, "El ejemplo solicitado no existe. Elige uno de la lista.")
        return render(request, 'muongraphy/index.html', {'examples': EXAMPLES}, status=404)

    path = os.path.join(settings.MEDIA_ROOT, 'muongraphy', 'sample_data','Muongraphy-1')
    file_type = 'csv'
    plot_flag = True

    video_base64 = None
    sound_paths, all_image_paths = [], []
    try:
        # Ahora recibimos 3 valores: imágenes para video, sonidos, y todas las imágenes para limpieza
        image_paths, sound_paths, all_image_paths = process_files(path, file_name, file_type, plot_flag)
        if image_paths and sound_paths is not None:
            video_base64 = create_video_from_paths(image_paths, sound_paths)
        else:
            raise ValueError("Archivo no encontrado.")
    except Exception:
        # El detalle queda en el log; al usuario solo se le muestra un mensaje genérico
        logger.exception("Error al generar el video de muongrafía para %s", file_name)
    finally:
        # Limpiar sonidos e imágenes temporales también si la generación falló
        cleanup_temp_audio(sound_paths or [])
        cleanup_temp_files(all_image_paths or [])

    context = {'examples': EXAMPLES}

    if video_base64 is None:
        messages.error(request, "No se pudo crear el video. Intenta de nuevo en unos minutos.")
    else:
        context['video_base64'] = video_base64
        context['current_example'] = next(
            example for example in EXAMPLES if example['file_name'] == file_name
        )

    return render(request, 'muongraphy/index.html', context)

