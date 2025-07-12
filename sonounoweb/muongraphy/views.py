from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
from django.conf import settings
import base64
import subprocess
import os
import glob
import time
from django.contrib import messages
from utils.muongraphy_lib.muon_bash import process_files, cleanup_temp_audio, cleanup_temp_files
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, AudioClip, concatenate_audioclips
from PIL import Image
from scipy.io.wavfile import write
import numpy as np
import tempfile

def cleanup_old_temp_files():
    """Limpia archivos temporales antiguos (más de 1 hora) de la carpeta temp"""
    temp_dir = os.path.join(settings.BASE_DIR, 'temp')
    if os.path.exists(temp_dir):
        current_time = time.time()
        # Buscar archivos temporales con extensiones comunes
        temp_patterns = ['*.png', '*.wav', '*.mp4', '*.tmp']
        
        for pattern in temp_patterns:
            temp_files = glob.glob(os.path.join(temp_dir, pattern))
            for file_path in temp_files:
                try:
                    # Verificar si el archivo tiene más de 1 hora
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 3600:  # 3600 segundos = 1 hora
                        os.remove(file_path)
                except Exception as e:
                    pass  # Silenciar errores de eliminación

def index(request):
    # Limpiar archivos temporales antiguos al cargar la página
    cleanup_old_temp_files()
    return render(request, "muongraphy/index.html")

def create_video_from_paths(image_paths, sound_paths):
    clips = []
    temp_video_file_path = None
    temp_audiopath = None
    final_clip = None

    try:
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

        # Verificar si existe la carpeta temp y si no la crea
        if not os.path.exists(temp_dir):
            try:
                os.makedirs(temp_dir, mode=0o777, exist_ok=True)  # Crear la carpeta con permisos completos
            except Exception as e:
                pass  # Silenciar errores de creación de carpeta

        # Captura si existe un error al crear el archivo temporal
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_video_file:
                temp_video_file_path = temp_video_file.name
        except Exception as e:
            pass  # Silenciar errores de creación de archivo temporal

        # Set higher permissions (e.g., read/write/execute for owner and group)
        os.chmod(temp_video_file_path, 0o777)

        # Captura si existe un error al crear el archivo de audio temporal
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_audio_file:
                temp_audiopath = temp_audio_file.name
        except Exception as e:
            pass  # Silenciar errores de creación de archivo temporal

        # Write and encode video
        final_clip.write_videofile(
            temp_video_file_path, 
            codec='libx264',
            fps=24,
            audio_codec='aac',
            temp_audiofile=temp_audiopath,
            verbose=False,  # Cambiar a False para reducir logs
            logger=None     # Desactivar logger para reducir output
        )
        # Read video into memory
        with open(temp_video_file_path, 'rb') as video_file:
            video_bytes = BytesIO(video_file.read())
        
        # Convert video bytes to base64
        video_bytes.seek(0)
        video_base64 = base64.b64encode(video_bytes.read()).decode('utf-8')
        
        return video_base64
        
    finally:
        # Cleanup temporal files in all cases
        if temp_video_file_path and os.path.exists(temp_video_file_path):
            os.remove(temp_video_file_path)
        if temp_audiopath and os.path.exists(temp_audiopath):
            os.remove(temp_audiopath)
        if final_clip:
            final_clip.close()

def grafico(request, file_name):
    # Limpiar archivos temporales antiguos antes de procesar
    cleanup_old_temp_files()
    
    path = os.path.join(settings.MEDIA_ROOT, 'muongraphy', 'sample_data','Muongraphy-1')
    
    if file_name.endswith('.csv'):
        file_type = 'csv'
    else:
        file_type = 'txt'
    
    plot_flag = True

    video_base64 = None
    try:
        # Ahora recibimos 3 valores: imágenes para video, sonidos, y todas las imágenes para limpieza
        image_paths, sound_paths, all_image_paths = process_files(path, file_name, file_type, plot_flag)
        if image_paths and sound_paths is not None:
            video_base64 = create_video_from_paths(image_paths, sound_paths)
            
            # Limpiar archivos temporales de sonido
            cleanup_temp_audio(sound_paths)
            
            # Limpiar TODOS los archivos temporales de imágenes (no solo los del video)
            cleanup_temp_files(all_image_paths)
        else:
            raise ValueError("Archivo no encontrado.")
    except Exception as e:
        messages.error(request, e)
        
    context ={}
      
    if video_base64 is None:
        messages.error(request, "No se pudo crear el video.")
    else:
        context = {
            'video_base64': video_base64
        }

    return render(request, 'muongraphy/index.html', context)

