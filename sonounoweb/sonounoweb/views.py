# una vez implementada la app se borrará este archivo
from pathlib import Path

from django.http import HttpResponse
from django.template import Template, Context


BASE_DIR = Path(__file__).resolve().parent.parent

def index (request):
	plantillaExterna = open (str(BASE_DIR) + '/sonounoweb/plantilla/index.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	
def sonido (request):
	plantillaExterna = open (str(BASE_DIR) + '/sonounoweb/plantilla/sonido.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	
def grafico (request):
	plantillaExterna = open (str(BASE_DIR) + '/sonounoweb/plantilla/grafico.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	
def funciones_matematicas (request):
	plantillaExterna = open (str(BASE_DIR) + '/sonounoweb/plantilla/funciones_matematicas.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
		
def inicio (request):
	plantillaExterna = open (str(BASE_DIR) + '/sonounoweb/plantilla/inicio.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	
def ayuda (request):
	plantillaExterna = open (str(BASE_DIR) + '/sonounoweb/plantilla/ayuda.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	

