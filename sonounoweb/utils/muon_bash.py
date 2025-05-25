import io
import base64
import time
import tempfile
import os
import datetime
import glob
import matplotlib.pyplot as plt
from utils.data_import.data_import import DataImportColumns
from utils.sound_module import sonification as sd
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

def process_sound_array(sound_array):
    """Convert numpy array to temporary WAV file for MoviePy"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        # Ensure correct format (44.1kHz, 16-bit)
        wavfile.write(
            tmp_file.name,
            rate=44100,
            data=sound_array.astype(np.int16)
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

    file_path = os.path.join(path, target_filename)
    if os.path.isfile(file_path):
        print(f"Processing file: {target_filename}")
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
        
        # Plot ax5
        count = 0
        count1 = 0
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
        
        # play bip of the beggining
    
        #play the part on the left

        count = 0
        for px in px_ax1:
            if px == 32:
                color_index = int((px-1)/4)
            else:
                color_index = int(px/4)
            ax1.plot(px,py_ax1[count],color=list_colors[color_index], marker='o', linestyle='')
            fig1 = plot_to_temp_file(fig)
            count = count + 1

        count = 0
        ax1.plot(px_ax1,py_ax1,color='k', marker='o', linestyle='')
        for px in px_ax3:
            if px == 16:
                color_index = int((px-1)/2)
            else:
                color_index = int(px/2)
            ax3.plot(px,py_ax3[count],color=list_colors[color_index], marker='o', linestyle='')
            fig2 = plot_to_temp_file(fig)
            count = count + 1

        count = 0
        ax3.plot(px_ax3,py_ax3,color='k', marker='o', linestyle='')
        for px in px_ax5:
            if px == 32:
                color_index = int((px-1)/4)
            else:
                color_index = int(px/4)
            ax5.plot(px,py_ax5[count],color=list_colors[color_index], marker='o', linestyle='')
            fig3 = plot_to_temp_file(fig)

            count = count + 1

        ax5.plot(px_ax5,py_ax5,color='k', marker='o', linestyle='')
        fig4 = plot_to_temp_file(fig)
        
        # play bip of the beggining
        
        #silence
        
        #play the part on the right

        count = 0
        for px in px_ax2:
            if px == 32:
                color_index = int((px-1)/4)
            else:
                color_index = int(px/4)
            ax2.plot(px,py_ax2[count],color=list_colors[color_index], marker='o', linestyle='')
            fig5 = plot_to_temp_file(fig)
            count = count + 1

        count = 0
        ax2.plot(px_ax2,py_ax2,color='k', marker='o', linestyle='')
        for px in px_ax4:
            if px == 16:
                color_index = int((px-1)/2)
            else:
                color_index = int(px/2)
            ax4.plot(px,py_ax4[count],color=list_colors[color_index], marker='o', linestyle='')
            fig6 = plot_to_temp_file(fig)
            count = count + 1

        count = 0
        ax4.plot(px_ax4,py_ax4,color='k', marker='o', linestyle='')
        for px in px_ax6:
            if px == 32:
                color_index = int((px-1)/4)
            else:
                color_index = int(px/4)
            ax6.plot(px,py_ax6[count],color=list_colors[color_index], marker='o', linestyle='')
            fig7 = plot_to_temp_file(fig)
            count = count + 1

        ax6.plot(px_ax6,py_ax6,color='k', marker='o', linestyle='')
        fig8 = plot_to_temp_file(fig)

        
        image_paths = [
            fig0,
            fig1,
            fig2,
            fig3,
            fig4,
            fig5,
            fig6,
            fig7,
            fig8
        ]
        bip_path = process_sound_array(bip)
        sound_ax1_path = process_sound_array(sound_ax1)
        sound_ax2_path = process_sound_array(sound_ax2)
        sound_ax3_path = process_sound_array(sound_ax3)
        sound_ax4_path = process_sound_array(sound_ax4)
        sound_ax5_path = process_sound_array(sound_ax5)
        sound_ax6_path = process_sound_array(sound_ax6)
        
        sounds_paths = [
            bip_path,
            sound_ax1_path,
            sound_ax2_path,
            sound_ax3_path,
            bip_path,
            sound_ax4_path,
            sound_ax5_path,
            sound_ax6_path,
            bip_path
        ]
        return image_paths, sounds_paths
    else:
        return None, None