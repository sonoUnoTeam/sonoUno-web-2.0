from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.urls import reverse


def index(request):
    return render(request,"sonif1D/index.html")

def inicio(request):
    return render(request,"sonif1D/inicio.html")

def ayuda(request):
    return render(request,"sonif1D/ayuda.html")

def sonido(request):
    return render(request, "sonif1D/sonido.html")

def grafico(request):
    return render(request, "sonif1D/grafico.html")

def funciones_matematicas(request):
    return render(request, "sonif1D/funciones_matematicas.html")