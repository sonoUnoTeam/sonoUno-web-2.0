from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
from django.conf import settings
import base64
import subprocess
import os
from django.contrib import messages
from utils.muon_bash import process_files, cleanup_temp_audio, cleanup_temp_audio
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, AudioClip, concatenate_audioclips
from PIL import Image
from scipy.io.wavfile import write
import numpy as np
import tempfile

def index(request):
    return render(request, "muongraphy/index.html")

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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=temp_dir) as temp_video_file:
        temp_video_file_path = temp_video_file.name

    # Set higher permissions (e.g., read/write/execute for owner and group)
    os.chmod(temp_video_file_path, 0o777)

    #with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
    #    temp_video_file_path = temp_video_file.name

    # Write and encode video
    final_clip.write_videofile(
        temp_video_file_path, 
        codec='libx264',
        fps=24,
        audio_codec='aac',
        verbose=True,           # <--- agrega esto
        logger='bar'            # <--- y esto para barra de progreso
    )
    
    # Read video into memory
    with open(temp_video_file_path, 'rb') as video_file:
        video_bytes = BytesIO(video_file.read())
    
    # Cleanup
    os.remove(temp_video_file_path)
    final_clip.close()
    
    # Convert video bytes to base64
    video_bytes.seek(0)
    video_base64 = base64.b64encode(video_bytes.read()).decode('utf-8')
    
    return video_base64

def grafico(request, file_name):
    path = os.path.join(settings.MEDIA_ROOT, 'muongraphy', 'sample_data','Muongraphy-1')
    
    if file_name.endswith('.csv'):
        file_type = 'csv'
    else:
        file_type = 'txt'
    
    plot_flag = True

    video_base64 = None
    try:
        image_paths, sound_paths = process_files(path, file_name, file_type, plot_flag) # Retorna una lista de buffers de imágenes y una lista de arrays de sonidos
        if image_paths and sound_paths is not None:
            video_base64 = create_video_from_paths(image_paths, sound_paths)
            cleanup_temp_audio(sound_paths)
            cleanup_temp_audio(image_paths)
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

