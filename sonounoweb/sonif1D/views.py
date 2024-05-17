from django.conf.urls.static import static
from django.conf import settings

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.urls import reverse

import matplotlib
import matplotlib.pyplot as plt
import io
import urllib, base64
import pandas as pd
import numpy as np
import os

#Local import
from .sonounolib.data_export.data_export import DataExport
from .sonounolib.data_import.data_import import DataImport
from .sonounolib.sound_module.simple_sound import simpleSound
from .sonounolib.data_transform.predef_math_functions import PredefMathFunctions

matplotlib.use('Agg')

def index(request):
    return render(request,"sonif1D/index.html")

def inicio(request):
    return render(request,"sonif1D/inicio.html")

def ayuda(request):
    return render(request,"sonif1D/ayuda.html")

def sonido(request):
    return render(request, "sonif1D/sonido.html")

def grafico(request):
    _dataimport = DataImport()
    _simplesound = simpleSound()
    _math = PredefMathFunctions()
    path = os.getcwd() + '/sonif1D/sample_data/decrease.txt'
    data, status, msg = _dataimport.set_arrayfromfile(path, 'txt')

    if data.shape[1]<2:
        print("Error reading file 1, only detect one column.")

    # Turn to float
    data_float = data.iloc[1:, :].astype(float)

    plt.plot(data_float.loc[:,0], data_float.loc[:,1], label='Graphic Test')

    # Normalize the data to sonify
    x, y, status = _math.normalize(data_float.loc[:,0], data_float.loc[:,1], init=1)

    # Sound configurations, predefined at the moment
    _simplesound.reproductor.set_continuous()
    _simplesound.reproductor.set_waveform('celesta')
    _simplesound.reproductor.set_time_base(0.05)
    _simplesound.reproductor.set_min_freq(300)
    _simplesound.reproductor.set_max_freq(1500)

    # Ordenada to plot the red line
    minval = float(np.abs(data_float.loc[:,1]).min())
    maxval = float(np.abs(data_float.loc[:,1]).max())
    ordenada = np.array([minval, maxval])

    for i in range (1, data_float.loc[:,0].size):
        # Update the plot
        if not i == 1:
            line = red_line.pop(0)
            line.remove()
        abscisa = np.array([float(data_float.loc[i,0]), float(data_float.loc[i,0])])
        red_line = plt.plot(abscisa, ordenada, 'r')
        # Make the sound
        _simplesound.reproductor.set_waveform('sine')
        _simplesound.make_sound(y[i], 1)
        plt.pause(0.001)

    # Save sound
    wav_name = path[:-4] + '_sound.wav'
    _simplesound.save_sound(wav_name, data_float.loc[:,0], y, init=1)

    #xpoints = np.array([1, 2, 6, 8])
    #ypoints = np.array([3, 8, 1, 10])

    #plt.plot(xpoints, ypoints, label='Graphic Test')
    fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf,format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    plt.close()
    return render(request, 'sonif1D/grafico.html', {'data':uri})

def funciones_matematicas(request):
    return render(request, "sonif1D/funciones_matematicas.html")

def test(request):
    return render(request, "sonif1D/test.html")

def test2(request):
    plt.plot(range(10))
    fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf,format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return render(request, 'sonif1D/test2.html', {'data':uri})

