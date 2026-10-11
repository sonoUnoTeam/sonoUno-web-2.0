import io
import base64
import time
import tempfile
import os
import datetime
import glob
import matplotlib.pyplot as plt
from django.conf import settings
from utils.muongraphy_lib.data_import.data_import import DataImportColumns
from utils.muongraphy_lib.sound_module import sonification as sd
from scipy.io import wavfile
import numpy as np

def plot_to_temp_file(fig):
    # Create temporary file 
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        # Save figure to temp file
        fig.savefig(tmp_file.name, format='png')
        return tmp_file.name

def cleanup_temp_files(file_paths):
    # Clean up temporary files after video creation
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)

# Ganancia de salida aplicada a todo el audio (notas y bip). Iguala el nivel de
# la grabación de la versión de escritorio original (Example_5), medido ~2,08x
# más fuerte que la síntesis con amplitud 2000.
OUTPUT_GAIN = 2.08

# Pico máximo permitido al escribir WAV de 16 bits; deja margen bajo 32767
MAX_INT16_PEAK = int(np.iinfo(np.int16).max * 0.9)

def limit_amplitude(sound_array, max_peak=MAX_INT16_PEAK):
    """
    Escala el sonido solo si su pico supera max_peak. Los acordes se forman
    sumando senoidales, así que con muchos canales activos el pico excede el
    rango int16 y, sin esto, la conversión desborda y distorsiona el audio.
    """
    sound_array = np.asarray(sound_array, dtype=np.float64)
    peak = np.max(np.abs(sound_array)) if sound_array.size else 0
    if peak > max_peak:
        sound_array = sound_array * (max_peak / peak)
    return sound_array

def process_sound_array(sound_array):
    """Convert numpy array to temporary WAV file for MoviePy"""
    # Usar directorio temp del proyecto en lugar del sistema
    temp_dir = os.path.join(settings.BASE_DIR, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=temp_dir) as tmp_file:
        # Ensure correct format (44.1kHz, 16-bit)
        wavfile.write(
            tmp_file.name,
            rate=44100,
            data=limit_amplitude(np.asarray(sound_array, dtype=np.float64) * OUTPUT_GAIN).astype(np.int16)
        )
        return tmp_file.name

def cleanup_temp_audio(file_paths):
    """Clean temporary audio files"""
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)

def process_files(path, target_filename, ext='txt', plot_flag=False):
    open_csv = DataImportColumns()
    # init sound
    sd.sound_init()
    note_freq = sd.get_piano_notes()
    list_notes = [note_freq['A3'], note_freq['B3'], note_freq['C4'], note_freq['D4'], 
                  note_freq['E4'], note_freq['F4'], note_freq['G4'], note_freq['A4'], 
                  note_freq['B4'], note_freq['C5'], note_freq['D5'], note_freq['E5'], 
                  note_freq['F5'], note_freq['G5'], note_freq['A5'], note_freq['B5']]
    sd.set_bip()
    bip = sd.get_bip()
    loop_number = 0
    # Initialize a counter to show a message during each loop
    i = 1
    # Loop to walk the directory and sonify each data file
    now = datetime.datetime.now()
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2)
    count_wf = 0
    
    # Lista para recopilar TODOS los archivos de imagen generados
    all_image_paths = []

    file_path = os.path.join(path, target_filename)
    if os.path.isfile(file_path):
        file, status, msg = open_csv.set_arrayfromfile(file_path, ext)
        
        if plot_flag:
            fig.suptitle(os.path.basename(target_filename[:-4]))
            ax1.cla()
            ax2.cla()
            ax3.cla()
            ax4.cla()
            ax5.cla()
            ax6.cla()
            ax1.set_xlabel('channel')
            ax2.set_xlabel('channel')
            ax3.set_xlabel('channel')
            ax4.set_xlabel('channel')
            ax5.set_xlabel('channel')
            ax6.set_xlabel('channel')
            
            ax1.plot((file.iloc[1:,0].astype(float)), (file.iloc[1:,1].astype(float)), 'bo')
            ax2.plot((file.iloc[1:,0].astype(float)), (file.iloc[1:,2].astype(float)), 'bo')
            ax3.plot((file.iloc[1:,0].astype(float)), (file.iloc[1:,3].astype(float)), 'bo')
            ax4.plot((file.iloc[1:,0].astype(float)), (file.iloc[1:,4].astype(float)), 'bo')
            ax5.plot((file.iloc[1:,0].astype(float)), (file.iloc[1:,5].astype(float)), 'bo')
            ax6.plot((file.iloc[1:,0].astype(float)), (file.iloc[1:,6].astype(float)), 'bo')
            
            fig0 = plot_to_temp_file(fig)
            all_image_paths.append(fig0)
        
        # Plot ax5
        count = 0
        count1 = 0
        px_ax1, py_ax1, px_ax2, py_ax2, px_ax3, py_ax3 = [], [], [], [], [], []
        px_ax4, py_ax4, px_ax5, py_ax5, px_ax6, py_ax6 = [], [], [], [], [], []
        sound_ax5 = []
        sound_ax6 = []
        sound_ax3 = []
        sound_ax4 = []
        sound_ax1 = []
        sound_ax2 = []
        wf = 'sine'
        for note in list_notes:
            # plot 5
            if not len(sound_ax5):
                if float(file.iloc[count+1,5]) != 0:
                    sound_ax5 = sd.get_waveform(wf, note, 1)
                    px_ax5 = [count+1]
                    py_ax5 = [float(file.iloc[count+1,5])]
                    if float(file.iloc[count+2,5]) != 0:
                        sound_ax5 = sound_ax5 + sd.get_waveform(wf, note, 1)
                        px_ax5.append(count+2)
                        py_ax5.append(float(file.iloc[count+2,5]))
                elif float(file.iloc[count+2,5]) != 0:
                    sound_ax5 = sd.get_waveform(wf, note, 1)
                    px_ax5 = [count+2]
                    py_ax5 = [float(file.iloc[count+2,5])]
            else:
                if float(file.iloc[count+1,5]) != 0:
                    sound_ax5 = sound_ax5 + sd.get_waveform(wf, note, 1)
                    px_ax5.append(count+1)
                    py_ax5.append(float(file.iloc[count+1,5]))
                if float(file.iloc[count+2,5]) != 0:
                    sound_ax5 = sound_ax5 + sd.get_waveform(wf, note, 1)
                    px_ax5.append(count+2)
                    py_ax5.append(float(file.iloc[count+2,5]))
            # plot 6
            if not len(sound_ax6):
                if float(file.iloc[count+1,6]) != 0:
                    sound_ax6 = sd.get_waveform(wf, note, 1)
                    px_ax6 = [count+1]
                    py_ax6 = [float(file.iloc[count+1,6])]
                    if float(file.iloc[count+2,6]) != 0:
                        sound_ax6 = sound_ax6 + sd.get_waveform(wf, note, 1)
                        px_ax6.append(count+2)
                        py_ax6.append(float(file.iloc[count+2,6]))
                elif float(file.iloc[count+2,6]) != 0:
                    sound_ax6 = sd.get_waveform(wf, note, 1)
                    px_ax6 = [count+2]
                    py_ax6 = [float(file.iloc[count+2,6])]
            else:
                if float(file.iloc[count+1,6]) != 0:
                    sound_ax6 = sound_ax6 + sd.get_waveform(wf, note, 1)
                    px_ax6.append(count+1)
                    py_ax6.append(float(file.iloc[count+1,6]))
                if float(file.iloc[count+2,6]) != 0:
                    sound_ax6 = sound_ax6 + sd.get_waveform(wf, note, 1)
                    px_ax6.append(count+2)
                    py_ax6.append(float(file.iloc[count+2,6]))
            # plot 3
            if not len(sound_ax3):
                if float(file.iloc[count1+1,3]) != 0:
                    sound_ax3 = sd.get_waveform(wf, note, 1)
                    px_ax3 = [count1+1]
                    py_ax3 = [float(file.iloc[count1+1,3])]
            else:
                if float(file.iloc[count1+1,3]) != 0:
                    sound_ax3 = sound_ax3 + sd.get_waveform(wf, note, 1)
                    px_ax3.append(count1+1)
                    py_ax3.append(float(file.iloc[count1+1,3]))
            # plot 4
            if not len(sound_ax4):
                if float(file.iloc[count1+1,4]) != 0:
                    sound_ax4 = sd.get_waveform(wf, note, 1)
                    px_ax4 = [count1+1]
                    py_ax4 = [float(file.iloc[count1+1,4])]
            else:
                if float(file.iloc[count1+1,4]) != 0:
                    sound_ax4 = sound_ax4 + sd.get_waveform(wf, note, 1)
                    px_ax4.append(count1+1)
                    py_ax4.append(float(file.iloc[count1+1,4]))
            # plot 1
            if not len(sound_ax1):
                if float(file.iloc[count+1,1]) != 0:
                    sound_ax1 = sd.get_waveform(wf, note, 1)
                    px_ax1 = [count+1]
                    py_ax1 = [float(file.iloc[count+1,1])]
                    if float(file.iloc[count+2,1]) != 0:
                        sound_ax1 = sound_ax1 + sd.get_waveform(wf, note, 1)
                        px_ax1.append(count+2)
                        py_ax1.append(float(file.iloc[count+2,1]))
                elif float(file.iloc[count+2,1]) != 0:
                    sound_ax1 = sd.get_waveform(wf, note, 1)
                    px_ax1 = [count+2]
                    py_ax1 = [float(file.iloc[count+2,1])]
            else:
                if float(file.iloc[count+1,1]) != 0:
                    sound_ax1 = sound_ax1 + sd.get_waveform(wf, note, 1)
                    px_ax1.append(count+1)
                    py_ax1.append(float(file.iloc[count+1,1]))
                if float(file.iloc[count+2,1]) != 0:
                    sound_ax1 = sound_ax1 + sd.get_waveform(wf, note, 1)
                    px_ax1.append(count+2)
                    py_ax1.append(float(file.iloc[count+2,1]))
            # plot 2
            if not len(sound_ax2):
                if float(file.iloc[count+1,2]) != 0:
                    sound_ax2 = sd.get_waveform(wf, note, 1)
                    px_ax2 = [count+1]
                    py_ax2 = [float(file.iloc[count+1,2])]
                    if float(file.iloc[count+2,2]) != 0:
                        sound_ax2 = sound_ax2 + sd.get_waveform(wf, note, 1)
                        px_ax2.append(count+2)
                        py_ax2.append(float(file.iloc[count+2,2]))
                elif float(file.iloc[count+2,2]) != 0:
                    sound_ax2 = sd.get_waveform(wf, note, 1)
                    px_ax2 = [count+2]
                    py_ax2 = [float(file.iloc[count+2,2])]
            else:
                if float(file.iloc[count+1,2]) != 0:
                    sound_ax2 = sound_ax2 + sd.get_waveform(wf, note, 1)
                    px_ax2.append(count+1)
                    py_ax2.append(float(file.iloc[count+1,2]))
                if float(file.iloc[count+2,2]) != 0:
                    sound_ax2 = sound_ax2 + sd.get_waveform(wf, note, 1)
                    px_ax2.append(count+2)
                    py_ax2.append(float(file.iloc[count+2,2]))
            count = count + 2
            count1 = count1 + 1
            
        list_colors = ['tab:red', 'tab:orange', 'yellow', 'tab:olive', 'tab:green', 
                    'tab:cyan', 'tab:blue', 'tab:purple']

        # Un eje sin canales activos suena como silencio en lugar de un WAV vacío
        sound_ax1, sound_ax2, sound_ax3, sound_ax4, sound_ax5, sound_ax6 = [
            sound if len(sound) else sd.get_silence(1)
            for sound in (sound_ax1, sound_ax2, sound_ax3, sound_ax4, sound_ax5, sound_ax6)
        ]

        def highlight_axis(ax, px_list, py_list, channels_per_color):
            """
            Colorea los puntos del eje que suena y guarda una única imagen para
            todo su acorde; luego lo marca en negro como ya reproducido.
            """
            last_px = channels_per_color * len(list_colors)
            for px, py in zip(px_list, py_list):
                color_index = int((px - 1) / channels_per_color) if px == last_px else int(px / channels_per_color)
                ax.plot(px, py, color=list_colors[color_index], marker='o', linestyle='')
            image_path = plot_to_temp_file(fig)
            all_image_paths.append(image_path)
            ax.plot(px_list, py_list, color='k', marker='o', linestyle='')
            return image_path

        # Generar archivos de sonido
        bip_path = process_sound_array(bip)
        sound_ax1_path = process_sound_array(sound_ax1)
        sound_ax2_path = process_sound_array(sound_ax2)
        sound_ax3_path = process_sound_array(sound_ax3)
        sound_ax4_path = process_sound_array(sound_ax4)
        sound_ax5_path = process_sound_array(sound_ax5)
        sound_ax6_path = process_sound_array(sound_ax6)

        # Cada imagen del video se empareja con el sonido que se escucha mientras
        # se muestra: bip inicial, parte izquierda (ax1, ax3, ax5), bip, parte
        # derecha (ax2, ax4, ax6) y cierre. La vista agrega silencios al primer
        # clip, al del medio y reemplaza el último por silencio.
        video_image_paths = [fig0]
        sounds_paths = [bip_path]
        for ax, px_list, py_list, channels_per_color, sound_path in (
            (ax1, px_ax1, py_ax1, 4, sound_ax1_path),
            (ax3, px_ax3, py_ax3, 2, sound_ax3_path),
            (ax5, px_ax5, py_ax5, 4, sound_ax5_path),
        ):
            video_image_paths.append(highlight_axis(ax, px_list, py_list, channels_per_color))
            sounds_paths.append(sound_path)

        left_done = plot_to_temp_file(fig)
        all_image_paths.append(left_done)
        video_image_paths.append(left_done)
        sounds_paths.append(bip_path)

        for ax, px_list, py_list, channels_per_color, sound_path in (
            (ax2, px_ax2, py_ax2, 4, sound_ax2_path),
            (ax4, px_ax4, py_ax4, 2, sound_ax4_path),
            (ax6, px_ax6, py_ax6, 4, sound_ax6_path),
        ):
            video_image_paths.append(highlight_axis(ax, px_list, py_list, channels_per_color))
            sounds_paths.append(sound_path)

        final_image = plot_to_temp_file(fig)
        all_image_paths.append(final_image)
        video_image_paths.append(final_image)
        sounds_paths.append(bip_path)
        plt.close(fig)

        # Retornar: imágenes para video, sonidos para video, y TODAS las imágenes para limpieza
        return video_image_paths, sounds_paths, all_image_paths
    else:
        return None, None, None