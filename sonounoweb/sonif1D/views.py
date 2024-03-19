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

matplotlib.use('Agg')

#Local import
from sonounolib.data_export.data_export import DataExport
from sonounolib.data_import.data_import import DataImport
from sonounolib.sound_module.simple_sound import simpleSound
from sonounolib.data_transform.predef_math_functions import PredefMathFunctions

def index(request):
    return render(request,"sonif1D/index.html")

def inicio(request):
    return render(request,"sonif1D/inicio.html")

def ayuda(request):
    return render(request,"sonif1D/ayuda.html")

def sonido(request):
    return render(request, "sonif1D/sonido.html")

def grafico(request):
    xpoints = np.array([1, 2, 6, 8])
    ypoints = np.array([3, 8, 1, 10])

    plt.plot(xpoints, ypoints, label='Graphic Test')
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