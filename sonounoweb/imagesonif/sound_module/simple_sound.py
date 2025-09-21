# -*- coding: utf-8 -*-
"""
Versión adaptada de simple_sound para Django web.
Optimizada para generar archivos de audio sin reproducción en tiempo real.
"""

import os
import time
import numpy as np
import pygame
import wave
from scipy import signal
from ..data_export.data_export import DataExport as eErr
import tempfile
import logging

# Importar OpenCV para las imágenes de progreso
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV no disponible - las imágenes de progreso estarán deshabilitadas")

# Configurar logging
logger = logging.getLogger('imagesonif')

class reproductorRaw(object):
    """Reproductor de sonido optimizado para web (sin reproducción en tiempo real)."""
    
    def __init__(self,
                 volume=0.8,  # Aumentado de 0.5 a 0.8
                 min_freq=500.0,
                 max_freq=5000.0,
                 fixed_freq=440,
                 time_base=0.09,  # Aumentado de 0.04 a 0.09 para mayor duración
                 duty_cycle=1.0,
                 min_volume=0,
                 max_volume=1,
                 logscale=False):
        
        self.f_s = 44100  # Sampling frequency
        self.volume = volume
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.fixed_freq = fixed_freq
        self.min_volume = min_volume
        self.max_volume = max_volume
        self.logscale = logscale
        self.duty_cycle = duty_cycle
        self.waveform = self.get_available_waveforms()[0]
        
        # Configuración para modo headless (sin audio real)
        os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
        try:
            pygame.mixer.init(self.f_s, -16, channels=1, buffer=1024, 
                            allowedchanges=pygame.AUDIO_ALLOW_FREQUENCY_CHANGE)
        except Exception as e:
            logger.warning(f"No se pudo inicializar pygame.mixer: {e}")
        
        self._last_freq = 0
        self._last_time = 0
        
        self.set_adsr(0.01, 0.15, 25, 0.5)
        self.set_time_base(time_base)
        self.set_discrete()
        self.set_mapping('frequency')
        
        self.sound_buffer = b''
    
    def set_volume(self, volume):
        if volume > 100:
            volume = 100
        self.volume = volume / 100.0
    
    def get_volume(self):
        return self.volume
    
    def set_min_freq(self, freq):
        self.min_freq = freq
    
    def get_min_freq(self):
        return self.min_freq
    
    def set_max_freq(self, freq):
        self.max_freq = freq
    
    def get_max_freq(self):
        return self.max_freq
    
    def set_fixed_freq(self, freq):
        self.fixed_freq = freq
    
    def get_fixed_freq(self):
        return self.fixed_freq
    
    def set_logscale(self, logscale=True):
        self.logscale = logscale
    
    def set_min_volume(self, volume):
        self.min_volume = volume / 100.0
    
    def set_max_volume(self, volume):
        self.max_volume = volume / 100.0
    
    def get_max_volume(self):
        return self.max_volume
    
    def get_min_volume(self):
        return self.min_volume
    
    def set_time_base(self, time_base):
        self.time_base = time_base
        self.n_samples = int(self.duty_cycle * self.time_base * self.f_s)
        self.n = np.arange(0.0, self.n_samples)
        self.env = self._adsr_envelope()
    
    def get_time_base(self):
        return self.time_base
    
    def set_adsr(self, a, d, s, r):
        self._adsr = {'a': a, 'd': d, 's': s, 'r': r}
    
    def get_adsr(self):
        return self._adsr
    
    def set_duty_cycle(self, dc):
        self.duty_cycle = dc
    
    def get_duty_cycle(self):
        return self.duty_cycle
    
    def get_available_waveforms(self):
        return ['sine', 'synthwave', 'flute', 'piano', 'celesta', 'pipe organ']
    
    def set_waveform(self, waveform):
        self.waveform = waveform
    
    def set_mapping(self, mapping):
        if mapping in ['frequency', 'volume']:
            self.mapping = mapping
        else:
            return -1
    
    def get_mapping(self):
        return self.mapping
    
    def set_continuous(self):
        self.set_adsr(0.1, 0.15, 95, 0.1)
        self.continuous = True
    
    def set_discrete(self):
        self.set_adsr(0.01, 0.15, 25, 0.5)
        self.continuous = False
    
    def _generate_tone(self, x, harmonics):
        tone = np.zeros(len(x))
        for n, a in harmonics:
            if self._last_freq * n < 16000:
                tone += a * np.sin(n * x)
        return tone
    
    def generate_waveform(self, freq, delta_t=0):
        wf = self.waveform
        if self._last_freq == 0:
            self._last_freq = freq
        
        f_int = freq
        self._last_freq = freq
        
        fchirp = np.linspace(f_int, freq, len(self.n))
        x = 2 * np.pi * fchirp / self.f_s * self.n
        
        if wf == 'sine':
            return self._generate_tone(x, [(1, 1)])
        elif wf == 'synthwave':
            return np.sin(x) + 0.25 * np.sin(2 * x)
        elif wf == 'flute':
            harmonics = [(1, 0.6), (2.02, 0.06), (3, 0.02), (4, 0.006), (5, 0.004)]
            return self._generate_tone(x, harmonics)
        elif wf == 'piano':
            harmonics = [(1, 0.1884), (2.05, 0.0596), (3.04, 0.0473), (3.97, 0.0631),
                        (5.05, 0.0018), (6, 0.0112), (7, 0.02), (8, 0.005), (9, 0.005),
                        (10, 0.0032), (12, 0.0032), (13, 0.001), (14, 0.001), (15, 0.0018)]
            return self._generate_tone(x, harmonics)
        elif wf == 'celesta':
            harmonics = [(1, 0.316), (4, 0.040)]
            return self._generate_tone(x, harmonics)
        elif wf == 'pipe organ':
            harmonics = [(0.5, 0.05), (1, 0.05), (2, 0.05), (4, 0.05),
                        (6, 0.014), (0.25, 0.014), (0.75, 0.014),
                        (1.25, 0.006), (1.5, 0.006)]
            return self._generate_tone(x, harmonics)
        else:
            return self._generate_tone(x, [(1, 1)])  # fallback to sine
    
    def _adsr_envelope(self):
        a = int(self.n_samples * self._adsr['a'])
        d = int(self.n_samples * self._adsr['d'])
        s = self._adsr['s'] / 100.0
        r = int(self.n_samples * self._adsr['r'])
        env = np.zeros(self.n_samples)
        
        if a > 0:
            env[:a] = np.linspace(0, 1, a)
        if d > 0:
            env[a:a+d] = np.linspace(1, s, d)
        if self.n_samples - a - d - r > 0:
            env[a+d:-r] = s * np.ones(self.n_samples - a - d - r)
        if r > 0:
            env[-r:] = np.linspace(s, 0, r)
        
        return env
    
    def generate_audio_data(self, value):
        """Genera datos de audio sin reproducir (para web)."""
        if self.logscale:
            value = np.log10(100 * value + 1) / 2
        
        if self.mapping == 'frequency':
            freq = self.max_freq * value + self.min_freq
            vol = self.volume
        else:
            vol = self.max_volume * value + self.min_volume
            freq = self.fixed_freq
        
        self.env = self._adsr_envelope()
        # Amplificación más conservadora para evitar clipping
        base_amplitude = self.env * vol * 2**14
        amplified = base_amplitude * 1.3  # Reducido de 1.5 a 1.3
        waveform = self.generate_waveform(freq)
        f = amplified * waveform
        
        # Asegurar que no hay overflow
        f = np.clip(f, -32767, 32767)
        return f.astype('int16')


class simpleSound(object):
    """Clase principal para sonificación de imágenes en Django."""
    
    def __init__(self):
        self.expErrSs = eErr(log=True)
        self.reproductor = reproductorRaw()
        self.audio_data_list = []  # Para almacenar todos los datos de audio
    
    def process_image_sonification(self, image_array, progress_callback=None):
        """
        Procesa la sonificación completa de una imagen.
        
        Args:
            image_array: Array numpy de la imagen en escala de grises
            progress_callback: Función callback para reportar progreso
            
        Returns:
            tuple: (audio_data_arrays, normalized_values)
        """
        try:
            audio_data_list = []
            normalized_values = []
            
            total_columns = image_array.shape[1]
            
            for j in range(total_columns):
                # Calcular valor promedio normalizado de la columna
                column = image_array[:, j]
                column_avg = np.mean(column)
                normalized_value = column_avg / 255.0  # Normalizar a 0-1
                
                # Generar datos de audio para esta columna
                audio_data = self.reproductor.generate_audio_data(normalized_value)
                
                audio_data_list.append(audio_data)
                normalized_values.append(normalized_value)
                
                # Reportar progreso si hay callback
                if progress_callback:
                    progress = (j + 1) / total_columns * 100
                    progress_callback(progress)
            
            return audio_data_list, normalized_values
            
        except Exception as e:
            self.expErrSs.writeexception(e)
            return None, None
    
    def save_complete_audio(self, audio_data_list, output_path):
        """
        Guarda el audio completo concatenando todas las columnas.
        
        Args:
            audio_data_list: Lista de arrays de audio
            output_path: Ruta donde guardar el archivo
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            if not audio_data_list:
                return False
            
            # Concatenar todos los datos de audio
            complete_audio = np.concatenate(audio_data_list)
            
            # Normalizar y amplificar el audio para mejor volumen
            if len(complete_audio) > 0:
                # Convertir a float para procesamiento
                complete_audio = complete_audio.astype(np.float32)
                
                # Normalizar para evitar clipping
                max_amplitude = np.max(np.abs(complete_audio))
                if max_amplitude > 0:
                    # Normalizar al 80% del rango máximo para dar espacio para amplificación
                    normalized_audio = (complete_audio / max_amplitude) * 0.8 * 32767
                    
                    # Aplicar amplificación adicional más conservadora
                    amplified_audio = normalized_audio * 1.15  # Reducido de 1.25 a 1.15
                    
                    # Asegurar que no hay clipping y convertir de vuelta a int16
                    complete_audio = np.clip(amplified_audio, -32767, 32767).astype(np.int16)
                else:
                    complete_audio = complete_audio.astype(np.int16)
            
            # Guardar como archivo WAV
            with wave.open(output_path, 'wb') as output_file:
                output_file.setframerate(self.reproductor.f_s)
                output_file.setnchannels(1)
                output_file.setsampwidth(2)
                output_file.writeframesraw(complete_audio.tobytes())
            
            logger.info(f"Audio guardado exitosamente con amplificación mejorada: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando audio: {e}")
            self.expErrSs.writeexception(e)
            return False
    
    def create_progress_images(self, original_image, total_columns, temp_dir):
        """
        Crea secuencia de imágenes mostrando el progreso de sonificación.
        
        Args:
            original_image: Imagen PIL original
            total_columns: Número total de columnas
            temp_dir: Directorio temporal para guardar imágenes
            
        Returns:
            list: Lista de rutas de imágenes generadas
        """
        try:
            # Verificar si OpenCV está disponible
            if not CV2_AVAILABLE:
                self.expErrSs.writeexception(Exception("OpenCV no está disponible"))
                return []
                
            from PIL import Image
            
            image_paths = []
            
            # Convertir PIL a formato OpenCV
            img_array = np.array(original_image)
            if len(img_array.shape) == 3:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            
            # Generar imágenes con línea de progreso
            for j in range(total_columns):
                img_copy = img_cv.copy()
                
                # Dibujar línea roja de progreso
                cv2.line(img_copy, (j, 0), (j, img_copy.shape[0]), (0, 0, 255), 3)
                
                # Guardar imagen
                image_path = os.path.join(temp_dir, f'progress_{j:06d}.png')
                cv2.imwrite(image_path, img_copy)
                image_paths.append(image_path)
            
            return image_paths
            
        except Exception as e:
            self.expErrSs.writeexception(e)
            return []
