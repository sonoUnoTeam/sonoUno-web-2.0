import base64
import io
import json
import os
import time
import urllib
import re

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pygame
import wave
from PIL import Image
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.urls import reverse
from io import BytesIO, StringIO

from .forms import ArchivoForm, ConfiguracionGraficoForm
from .sonounolib.data_export.data_export import DataExport
from .sonounolib.data_import.data_import import DataImport
from .sonounolib.data_transform.predef_math_functions import PredefMathFunctions
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

matplotlib.use('Agg')


def index(request):
    return render(request, "sonif1D/index.html")

def inicio(request):
    return render(request,"sonif1D/inicio.html")

def ayuda(request):
    return render(request,"sonif1D/ayuda.html")

def sonido(request):
    return render(request, 'sonif1D/sonido.html')

def funciones_matematicas(request):
    return render(request, 'sonif1D/funciones_matematicas.html')

# Función para mostrar un gráfico de un archivo cargado
def mostrar_grafico(request, nombre_archivo):
    # Ruta al archivo txt dentro de la carpeta sample_data
    ruta_archivo = os.path.join(settings.MEDIA_ROOT, 'sonif1D', 'sample_data', nombre_archivo)

    data = cargar_archivo(ruta_archivo) # Cargar los datos del archivo
    data_json = numpy_to_json(data) # Convertir los datos a JSON
    
    if data is None:
        messages.error(request, "Sin gráfico disponible o archivo no encontrado.")
        return render(request, 'sonif1D/index.html')
    
    grafico_base64 = generar_grafico(data, nombre_archivo)  # Generar el gráfico en base64
    audio_base64 = generar_auido_base64(data, request)  # Generar el archivo de audio en base64

    # Enviar la imagen y el audio en base64 a la plantilla
    context = {
        'grafico_base64': grafico_base64,
        'audio_base64': audio_base64,
        'data_json': data_json,
    }
    return render(request, 'sonif1D/index.html', context)

# Vista para configurar y mostrar un gráfico
class GraficoView(FormView):
    template_name = 'sonif1D/grafico.html'
    form_class = ConfiguracionGraficoForm
    success_url = reverse_lazy('sonif1D:grafico')

    def form_valid(self, form):
        # Procesar los datos del formulario
        name_grafic = form.cleaned_data['name_grafic']
        name_eje_x = form.cleaned_data['name_eje_x']
        name_eje_y = form.cleaned_data['name_eje_y']
        grilla = form.cleaned_data['grilla']
        escala_grises = form.cleaned_data['escala_grises']
        rotar_eje_x = form.cleaned_data['rotar_eje_x']
        rotar_eje_y = form.cleaned_data['rotar_eje_y']
        estilo_linea = form.cleaned_data['estilo_linea']
        color_linea = form.cleaned_data['color_linea']

        # Obtener los datos en json del formulario
        data_json = self.request.POST.get('data_json')

        if not data_json:
            messages.error(self.request, "No se encontraron datos para generar el gráfico.")
            return self.render_to_response(self.get_context_data(form=form))

        # Transformar los datos de json a numpy
        data = json_to_numpy(data_json)
        if data is None:
            messages.error(self.request, "Error al cargar los datos del gráfico.")
            return self.render_to_response(self.get_context_data(form=form))

        new_grafico_base64 = generar_grafico(data, name_grafic, name_eje_x, name_eje_y, grilla, escala_grises, rotar_eje_x, rotar_eje_y, estilo_linea, color_linea)
      
        # Enviar la imagen y el audio en base64 a la plantilla
        context = self.get_context_data(form=form)
        context['grafico_base64'] = new_grafico_base64
        return self.render_to_response(context)

    def form_invalid(self, form):
        messages.error(self.request, "Error al validar el formulario.")
        return self.render_to_response(self.get_context_data(form=form))

# Función para cargar los datos desde un archivo .txt o .csv a un array de NumPy
def cargar_archivo(ruta_archivo):
    try:
        if ruta_archivo.endswith('.csv'):
            data = np.loadtxt(ruta_archivo, delimiter=',')
        else:
            data = np.loadtxt(ruta_archivo)
        
        # Verificar que los datos sean una matriz con al menos dos columnas
        if data.ndim != 2 or data.shape[1] < 2:
            return None
        
        return data
    except Exception as e:
        return None

# Función para cargar los datos desde un string en memoria a un array de NumPy
def cargar_datos_desde_contenido(contenido):
    """
    Procesa los datos desde un string en memoria y retorna un array de NumPy.
    """
    try:
        # Convertir el contenido en un formato procesable (lista de líneas)
        lines = contenido.splitlines()
        
        # Detectar el delimitador (puede ser coma, tabulación, espacio múltiple, etc.)
        delimitadores = [',', '\t', r'\s+']
        for delim in delimitadores:
            try:
                # Intentar convertir las líneas a un array de NumPy
                data = np.array([list(map(float, re.split(delim, line))) for line in lines if line.strip()])
                return data
            except ValueError:
                continue
        
        # Si no se pudo convertir con ninguno de los delimitadores
        raise ValueError("No se pudo determinar el delimitador o los datos no son válidos.")
    except Exception as e:
        print(f"Error procesando datos: {e}")
        return None

# Vista para importar un archivo y generar el gráfico y el audio
class ImportarArchivoView(FormView):
    template_name = 'sonif1D/import_archivo.html'
    form_class = ArchivoForm
    success_url = reverse_lazy('sonif1D:index')

    def form_valid(self, form):
        archivo = self.request.FILES['archivo']
        nombre_archivo = archivo.name.lower()
        
        # Verificar la extensión del archivo
        if nombre_archivo.endswith('.csv') or nombre_archivo.endswith('.txt'):
            # Leer el contenido del archivo cargado
            contenido = archivo.read().decode('utf-8')

            # Procesar el contenido como una lista de líneas o directamente
            data = cargar_datos_desde_contenido(contenido)
            data_json = numpy_to_json(data) # Convertir los datos a JSON

            if data is None:
                messages.error(self.request, "El archivo no contiene datos válidos.")
                return self.render_to_response(self.get_context_data(form=form), template_name='sonif1D/index.html')

            grafico_base64 = generar_grafico(data, archivo.name)
            audio_base64 = generar_auido_base64(data, self.request)
            
            context = self.get_context_data(form=form)
            context.update({
                'grafico_base64': grafico_base64,
                'audio_base64': audio_base64,
                'data_json': data_json,
            })
            return self.render_to_response(context, template_name='sonif1D/index.html')
        else:
            messages.error(self.request, "Formato de archivo no soportado. Por favor, sube un archivo CSV o TXT.")
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def render_to_response(self, context, **response_kwargs):
        template_name = response_kwargs.pop('template_name', self.template_name)
        return self.response_class(
            request=self.request,
            template=template_name,
            context=context,
            using=self.template_engine,
        )

#Función para convertir un array de NumPy a una cadena JSON
def numpy_to_json(data):
    return json.dumps(data.tolist())

#Función para convertir una cadena JSON a un array de NumPy
def json_to_numpy(json_str):
    try:
        # Convertir la cadena JSON a una lista de Python
        data_list = json.loads(json_str)
        # Convertir la lista de Python a un array de NumPy
        numpy_array = np.array(data_list)
        return numpy_array
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
        return None
    
# Función para generar el gráfico en base64 con configuraciones
def generar_grafico(data, name_grafic=False, name_eje_x =False, name_eje_y =False, grilla=False, escala_grises=False, rotar_eje_x=False, rotar_eje_y=False, estilo_linea='solid', color_linea='blue'):
    # Verificar que data es un array de NumPy
    if not isinstance(data, np.ndarray):
        raise ValueError("El parámetro 'data' debe ser un array de NumPy")
    
    plt.figure(figsize=(10, 5))
    plt.plot(data[:, 0], data[:, 1], linestyle=estilo_linea, color=color_linea)
    if name_eje_x:
        plt.xlabel(name_eje_x)
    if name_eje_y:    
        plt.ylabel(name_eje_y)
    if name_grafic:
        plt.title(name_grafic)
    if grilla:
        plt.grid(True)
    if escala_grises:
        plt.gray()
    if rotar_eje_x:
        plt.xticks(rotation=90)
    if rotar_eje_y:
        plt.yticks(rotation=90)

    buffer = BytesIO()  # Crear un buffer de Bytes para guardar la imagen
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)  # Mover el cursor al inicio del buffer

    grafico_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')  # Codifica la imagen en base64

    return grafico_base64

# Función para generar el archivo de audio (en formato WAV) en base64
def generar_auido_base64(data, request):
    try:
        # Instancia el generador de sonido
        sonido = simpleSound()

        # Llama al método generate_sound para obtener el sonido generado
        wav_data = sonido.generate_sound(data[:, 0], data[:, 1])  # Usamos x como data_x y y como data_y

        # Codifica el archivo WAV en base64
        audio_base64 = base64.b64encode(wav_data).decode('utf-8')

        return audio_base64
    except Exception as e:
        messages.error(request, f"Error al generar el archivo de audio: {e}")
        return None
        

class reproductorRaw (object):
    def __init__ (self,
            volume=0.5,
            min_freq=500.0,
            max_freq=5000.0,
            fixed_freq=440,
            time_base=0.25,
            duty_cycle=1.0,
            min_volume=0,
            max_volume=1,
            logscale=False):
        self.f_s = 44100 #Sampling frequency
        self.volume = volume
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.fixed_freq = fixed_freq
        self.min_volume = min_volume
        self.max_volume = max_volume
        self.logscale = logscale
        self.duty_cycle = duty_cycle
        self.waveform = self.get_available_waveforms()[0]

        pygame.mixer.init(self.f_s, -16, channels = 1,buffer=1024, allowedchanges=pygame.AUDIO_ALLOW_FREQUENCY_CHANGE)

        self._last_freq = 0
        self._last_time = 0

        self.set_adsr(0.01,0.15,25,0.5)
        self.set_time_base(time_base)
        self.set_discrete()
        self.set_mapping('frequency')

        self.sound_buffer = b''

        """
        use en sonouno.py los metodos:
            get_waveformlist - para recuperar la lista y ponerla en la interfaz
            set_waveform - para devolverte el string de la forma de onda
                que selecciono el usuario
        si te parece bien podes usar esos nombres, sino los podes cambiar
        """

    def set_volume(self, volume):
        if volume > 100:
            volume = 100
        self.volume = volume/100.0

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

    def set__volume(self, volume):
        self.min_volume = volume/100.0

    def set_max_volume(self, volume):
        self.max_volume = volume/100.0

    def get_max_volume(self):
        return self.max_volume

    def get_min_volume(self):
        return self.min_volume

    def set_time_base(self, time_base):
        self.time_base = time_base
        self.n_samples = int(self.duty_cycle*self.time_base*self.f_s)
        self.n = np.arange(0.0, self.n_samples)
        self.env = self._adsr_envelope()

    def get_envelope(self):
        return self._adsr_envelope()

    def get_time_base(self):
        return self.time_base

    def set_adsr(self, a, d, s, r):
        self._adsr = {'a':a,'d':d,'s':s,'r':r}

    def get_adsr(self):
        return self._adsr

    def set_duty_cycle(self, dc):
        self.duty_cycle = dc

    def get_duty_cycle(self):
        return self.duty_cycle

    def get_available_waveforms(self):
        return ['sine', 'synthwave','flute','piano',
            'celesta', 'pipe organ']

    def set_waveform(self, waveform):
        self.waveform = waveform

    def set_mapping(self, mapping):
        if mapping in ['frequency','volume']:
            self.mapping = mapping
        else:
            return -1

    def get_mapping(self):
        return self.mapping

    def set_continuous(self):
        self.set_adsr(0.1,0.15,95,0.1)
        self.continuous = True

    def set_discrete(self):
        self.set_adsr(0.01,0.15,25,0.5)
        self.continuous = False

    def _generate_tone(self, x, harmonics):
        tone = np.zeros(len(x))
        for n,a in harmonics:
            # A filter would be mor elegant, but the low freq artifact occur
            # anyway so this is the only way I found that really works
            if self._last_freq*n < 16000:
                tone += a*np.sin(n*x)
        return tone

    def generate_waveform(self, freq, delta_t=0):
        wf = self.waveform
        if self._last_freq == 0:
            self._last_freq = freq

        if self._last_time+self.get_time_base() > time.time():
            self._last_freq = freq
        f0 = self._last_freq
        f1 = freq

        t = time.time()

        if delta_t == 0:
            t0 = self._last_time
            self._last_time = t
        else:
            t0 = t - delta_t

        t1 = t0+self.get_time_base()

        if self.continuous:
            f_int = freq #(f0*(t1-t)+f1*(t-t0))/(t1-t0)
        else:
            f_int = freq

        fchirp = np.linspace(f_int, freq, len(self.n) )
        self._last_freq = freq
        x = 2*np.pi*fchirp/self.f_s*self.n
        if wf == 'sine':
            return self._generate_tone(x, [(1,1)])
        if wf == 'sawtooth':
            return signal.sawtooth(x)
        if wf == 'square':
            return signal.square(x)
        if wf == 'synthwave':
            return np.sin(x)+0.25*np.sin(2*x)
        if wf == 'flute':
            harmonics=[(1,0.6),(2.02,0.06),(3,0.02),(4,0.006),(5,0.004)]
            self.set_adsr(0.05, 0.2, 95, 0.1)
            return self._generate_tone(x, harmonics)
        if wf == 'piano':
            self.set_adsr(0.05, 0.3, 50, 0.4)
            harmonics = [(1, 0.1884), (2.05, 0.0596), (3.04, 0.0473), (3.97, 0.0631),
                (5.05, 0.0018), (6, 0.0112), (7, 0.02), (8, 0.005), (9, 0.005),
                (10, 0.0032), (12, 0.0032), (13, 0.001), (14, 0.001),
                (15, 0.0018)]
            return self._generate_tone(x, harmonics)
        if wf == 'celesta':
            self.set_adsr(0.1, 0.1, 50, 0.2)
            harmonics = [(1,0.316),(4,0.040)]
            return self._generate_tone(x, harmonics)
        if wf == 'pipe organ':
            self.set_adsr(0.1, 0.3, 20, 0.2)
            harmonics = [(0.5,0.05),(1,0.05),(2,0.05),(4,0.05),
                (6,0.014),(0.25,0.014),(0.75,0.014),
                (1.25,0.006),(1.5,0.006)]

            return self._generate_tone(x, harmonics)

    # Very simple linear AttackDecaySustainRelease implementation
    # These defaults are not meaningful
    def _adsr_envelope(self):
        a = int(self.n_samples*self._adsr['a'])
        d = int(self.n_samples*self._adsr['d'])
        s = self._adsr['s']/100.0
        r = int(self.n_samples*self._adsr['r'])
        env = np.zeros(self.n_samples)
        env[    :a] = np.linspace(0,1,a)
        env[ a:a+d] = np.linspace(1,s,d)
        env[a+d:-r] = s*np.ones(self.n_samples-a-d-r)
        env[   -r:] = np.linspace(s,0,r)
        return env

    #Es el método encargado de generar las notas y reproducirlas
    def pitch (self, value):
        if self.logscale:
            value = np.log10(100*value+1)/2 #This is to achieve reasoable values
            print(value)
        if self.mapping == 'frequency':
            freq = (self.max_freq-self.min_freq)*value+self.min_freq
            vol = self.volume
        else:
            vol = (self.max_volume-self.min_volume)*value+self.min_volume
            freq = self.fixed_freq
        self.env = self._adsr_envelope()
        f = self.env*vol*2**14*self.generate_waveform(freq)
        self.sound = pygame.mixer.Sound(f.astype('int16'))
        self.sound.play()

#Esta clase es la que se comunica con la clase principal.
class simpleSound(object):
    def __init__(self):
        #Se instancia la clase que se genera el sonido usando PyGame.
        self.reproductor = reproductorRaw()
    #Éste método modifica el valor para producir la nota y lo envía a la clase reproductorMidi
    def make_sound(self, data, x):
        try:
            if not (x == -1):
                #Aquí se llama al método que genera y envía la nota a fluidsynth
                self.reproductor.pitch(data)
            else:
                # Creería que no se esta usando, porque estaba mal escrita y
                # no generaba error, se deja por las dudas.
                self.reproductor.pitch(0)
        except Exception as e:
            print(e)
        #En un futuro se puede pedir confirmación al método pitch y devolverla.
    #Aquí se genera el archivo de salida con el sonido, por el momento no depende del tempo seleccionado.

    def save_sound(self, path, data_x, data_y, init=0):
        try:
            #rango, offset = self.reproductor.getRange()
            rep = self.reproductor
            sound_buffer=b''
            for x in range (init, data_x.size):
                freq = (rep.max_freq-rep.min_freq)*data_y[x]+rep.min_freq
                self.env = rep._adsr_envelope()
                #print(self.env.get_adsr())
                f = self.env*rep.volume*2**15*rep.generate_waveform(freq,
                    delta_t = 1)
                s = pygame.mixer.Sound(f.astype('int16'))
                sound_buffer += s.get_raw()
                #localTrack.add_notes(Note(int((dataY[x]*rango)+offset)))

            with wave.open(path,'wb') as output_file:
                output_file.setframerate(rep.f_s)
                output_file.setnchannels(1)
                output_file.setsampwidth(2)
                output_file.writeframesraw(sound_buffer)
                #output_file.close()

        except Exception as e:
            print(e)
            

    # Función para generar el sonido en formato WAV en memoria (sin guardarlo)
    def generate_sound(self, data_x, data_y, init=0):
        try:
            rep = self.reproductor
            sound_buffer = b''

            # Recorremos los datos para generar las ondas
            for x in range(init, data_x.size):
                # Calculamos la frecuencia basándonos en data_y
                freq = (rep.max_freq - rep.min_freq) * data_y[x] + rep.min_freq
                self.env = rep._adsr_envelope()

                # Generamos la onda de la frecuencia calculada
                f = self.env * rep.volume * 2**15 * rep.generate_waveform(freq, delta_t=1)

                # Convertimos la onda en un objeto de sonido de pygame
                s = pygame.mixer.Sound(f.astype('int16'))

                # Acumulamos el buffer de audio
                sound_buffer += s.get_raw()

            # Creamos un archivo WAV en memoria usando BytesIO
            output_wave = io.BytesIO()
            with wave.open(output_wave, 'wb') as wav_file:
                wav_file.setframerate(rep.f_s)  # Tasa de muestreo
                wav_file.setnchannels(1)        # Canal mono
                wav_file.setsampwidth(2)        # 2 bytes (16 bits por muestra)
                wav_file.writeframesraw(sound_buffer)

            # Devolvemos el archivo WAV en formato de bytes
            return output_wave.getvalue()

        except Exception as e:
            print(f"Error al generar el sonido: {e}")
            return None

        
    def save_sound_multicol_stars(self, path, data_x, data_y1, data_y2, init=0):
        rep = self.reproductor
        sound_buffer=b''
        for x in range (init, data_x.size):
            # y1
            rep.set_waveform('sine')
            freq = (rep.max_freq-rep.min_freq)*data_y1[x]+rep.min_freq
            self.env = rep._adsr_envelope()
            f = self.env*rep.volume*2**15*rep.generate_waveform(freq,
                delta_t = 1)
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()
            #y2
            rep.set_waveform('flute')
            freq = (rep.max_freq-rep.min_freq)*data_y2[x]+rep.min_freq
            self.env = rep._adsr_envelope()
            f = self.env*rep.volume*2**15*rep.generate_waveform(freq,
                delta_t = 1)
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()
            # Silence
            f = self.env*rep.volume*2**15*rep.generate_waveform(0,
                delta_t = 1)
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()

        with wave.open(path,'wb') as output_file:
            output_file.setframerate(rep.f_s)
            output_file.setnchannels(1)
            output_file.setsampwidth(2)
            output_file.writeframesraw(sound_buffer)
            #output_file.close()
        
    def save_sound_multicol(self, path, data_x, data_y1, data_y2, init=0):
        rep = self.reproductor
        sound_buffer=b''
        for x in range (init, data_x.size):
            # y1
            rep.set_waveform('sine')
            freq = (rep.max_freq-rep.min_freq)*data_y1[x]+rep.min_freq
            self.env = rep._adsr_envelope()
            f = self.env*rep.volume*2**15*rep.generate_waveform(freq,
                delta_t = 1)
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()
            #y2
            rep.set_waveform('flute')
            freq = (rep.max_freq-rep.min_freq)*data_y2[x]+rep.min_freq
            self.env = rep._adsr_envelope()
            f = self.env*rep.volume*2**15*rep.generate_waveform(freq,
                delta_t = 1)
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()
            # Silence
            f = self.env*rep.volume*2**15*rep.generate_waveform(0,
                delta_t = 1)
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()

        with wave.open(path,'wb') as output_file:
            output_file.setframerate(rep.f_s)
            output_file.setnchannels(1)
            output_file.setsampwidth(2)
            output_file.writeframesraw(sound_buffer)
            #output_file.close()

    def save_sound_withpeaks(self, path, data_x, data_y1, absortion, emission, init=0):
        rep = self.reproductor
        sound_buffer=b''
        freq_status = False
        for x in range (init, data_x.size):
            # y1
            rep.set_waveform('sine')
            freq = (rep.max_freq-rep.min_freq)*data_y1[x]+rep.min_freq
            self.env = rep._adsr_envelope()
            f = self.env*rep.volume*2**15*rep.generate_waveform(freq,
                delta_t = 1)
            s = pygame.mixer.Sound(f.astype('int16'))
            sound_buffer += s.get_raw()
            #y2
            rep.set_waveform('square')
            emission_flag = float(data_x.loc[x]) in emission['x'].unique()
            absortion_flag = float(data_x.loc[x]) in absortion['x'].unique()
            if emission_flag:
                #_simplesound.make_sound(1, 1)
                freq = (rep.max_freq-rep.min_freq)*1+rep.min_freq
                freq_status = True
            if absortion_flag:
                #_simplesound.make_sound(0, 1)
                freq = (rep.max_freq-rep.min_freq)*0+rep.min_freq
                freq_status = True
            if emission_flag and absortion_flag:
                freq = (rep.max_freq-rep.min_freq)*0.5+rep.min_freq
                freq_status = True
            if freq_status:
                self.env = rep._adsr_envelope()
                f = self.env*rep.volume*2**15*rep.generate_waveform(freq,
                    delta_t = 1)
                s = pygame.mixer.Sound(f.astype('int16'))
                sound_buffer += s.get_raw()
                freq_status = False
            # Silence
            #f = self.env*rep.volume*2**15*rep.generate_waveform(0,
            #    delta_t = 1)
            #s = pygame.mixer.Sound(f.astype('int16'))
            #sound_buffer += s.get_raw()
            #s = pygame.mixer.Sound(f.astype('int16'))
            #sound_buffer += s.get_raw()

        with wave.open(path,'wb') as output_file:
            output_file.setframerate(rep.f_s)
            output_file.setnchannels(1)
            output_file.setsampwidth(2)
            output_file.writeframesraw(sound_buffer)
            print('Sound saved')
            #output_file.close()
