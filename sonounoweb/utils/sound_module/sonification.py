#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 07:52:36 2022

@author: sonounoteam

This script is dedicated to sonification based on a muongraphy data set
"""

#import pygame
import os
from scipy.io import wavfile
import numpy as np
from scipy import signal

def sound_init():
    """
    Initializate the sound mixer with pygame to play sounds during plot display
    """
    #pygame.mixer.init(44100, -16, channels = 2, buffer=4095, allowedchanges=pygame.AUDIO_ALLOW_FREQUENCY_CHANGE | pygame.AUDIO_ALLOW_CHANNELS_CHANGE)
    #pygame.mixer.init(22050, -16, channels = 2, buffer=4095, allowedchanges=pygame.AUDIO_ALLOW_FREQUENCY_CHANGE | pygame.AUDIO_ALLOW_CHANNELS_CHANGE)

def set_bip():
    """
    Open the sound bip and store it in a global var to use it later during the
    sonification of particles. The bip represent the beginning of the particle
    track, at the center of the inner detector.
    """
    global bip
    # Set the path to open the tickmark
    bip_path = os.path.abspath(os.path.dirname(__file__)) + '/bip.wav'
    print(bip_path)
    # Open the bip tickmark
    rate1, bip_local = wavfile.read(bip_path, mmap=False)
    bip = bip_local
    
def get_bip():
    return bip

def get_sine_wave(frequency, duration, sample_rate=44100, amplitude=2000):
    """
    Parameters
    ----------
    frequency : float, frequency of the sine wave
    duration : float, duration of the sound
    sample_rate : int, optional: The default is 44100.
    amplitude : int, optional: The default is 4096.
    
    Returns
    -------
    sin_wave : np.array of the sound wave.
    
    """
    t = np.linspace(0, duration, int(sample_rate*duration)) # Time axis
    sin_wave = amplitude*np.sin(2*np.pi*frequency*t)
    return sin_wave
    
def _generate_tone(x, harmonics, freq):
        tone = np.zeros(len(x))
        for n,a in harmonics:
            # A filter would be mor elegant, but the low freq artifact occur
            # anyway so this is the only way I found that really works
            if freq*n < 16000:
                tone += a*np.sin(n*x)
        return tone
    
def get_waveform(wf, freq, duration, sample_rate=44100, amplitude=2000):


        t = np.linspace(0, duration, int(sample_rate*duration) )
        x = 2*np.pi*freq*t
        if wf == 'sine':
            return amplitude*np.sin(x)
        if wf == 'synthwave':
            return amplitude*np.sin(x)+(amplitude+0.25)*np.sin(2*x)
        if wf == 'test_wave':
            return amplitude*np.sin(x)+(amplitude+0.25)*np.cos(7*x)

def get_piano_notes():
    """
    Return the frequency of each 88 piano keys (A0-C8).
    ['C', 'c', 'D', 'd', 'E', 'F', 'f', 'G', 'g', 'A', 'a', 'B'] 
    In the code you can use:
        freq_array = get_piano_notes()
        freq_of_C4 = freq_array['C4']

    """
    # White keys are in Uppercase and black keys (sharps) are in lowercase
    octave = ['C', 'c', 'D', 'd', 'E', 'F', 'f', 'G', 'g', 'A', 'a', 'B'] 
    base_freq = 440 #Frequency of Note A4
    keys = np.array([x+str(y) for y in range(0,9) for x in octave])
    # Trim to standard 88 keys
    start = np.where(keys == 'A0')[0][0]
    end = np.where(keys == 'C8')[0][0]
    keys = keys[start:end+1]
    
    note_freqs = dict(zip(keys, [2**((n+1-49)/12)*base_freq for n in range(len(keys))]))
    note_freqs[''] = 0.0 # stop
    return note_freqs

def get_silence(duration):
    """
    This method generate the sound of a silence given the duration of it and 
    return the array.
    """
    return get_sine_wave(0, duration)

def play_sound(sound, vol_left=1, vol_right=1):
    """
    Use pygame and play the given array, with the possibility to set the volume
    of each left/right speaker.
    Parameters
    ----------
    sound : array, parameter to be sonified
    vol_left : volume of the left speaker, default 1 (max volume)
    vol_right : volume of the right speaker, default 1 (max volume)
    """
    #sound_play = pygame.mixer.Sound(sound.astype('int16'))
    #channel = sound_play.play()
    #channel.set_volume(vol_left,vol_right)
    print("Se reproduce un sonido")
    
def array_savesound(array):
    """
    Parameters
    ----------
    array : array, parameter to be saved (this overwrite the global variable 
            sound_to_save). If you want to add info to the global variable see
            add_array_savesound(array)
    """
    global sound_to_save
    sound_to_save = array
    
def add_array_savesound(array):
    """
    Parameters
    ----------
    array : array, parameter to be saved (this add the information to the global 
            variable sound_to_save). If you want to overwrite the global 
            variable see array_savesound(array)
    """
    global sound_to_save
    sound_to_save = np.append(sound_to_save, array)

def save_sound(sound_path):
    """
    Use the path provided to store the sound file in the computer
    Parameters
    ----------
    sound_path : path where to save sound in wav
    """
    wavfile.write(sound_path, rate=44100, data=sound_to_save.astype(np.int16))
    
