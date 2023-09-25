from django.http import HttpResponse
from django.template import Template, Context


def index (request):
	plantillaExterna = open ('/home/belen/Escritorio/projects/sonounoweb/sonounoweb/plantilla/index.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	
def sonido (request):
	plantillaExterna = open ('/home/belen/Escritorio/projects/sonounoweb/sonounoweb/plantilla/sonido.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	
def grafico (request):
	plantillaExterna = open ('/home/belen/Escritorio/projects/sonounoweb/sonounoweb/plantilla/grafico.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	
def funciones_matematicas (request):
	plantillaExterna = open ('/home/belen/Escritorio/projects/sonounoweb/sonounoweb/plantilla/funciones_matematicas.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
		
def inicio (request):
	plantillaExterna = open ('/home/belen/Escritorio/projects/sonounoweb/sonounoweb/plantilla/inicio.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	
def ayuda (request):
	plantillaExterna = open ('/home/belen/Escritorio/projects/sonounoweb/sonounoweb/plantilla/ayuda.html')
	template = Template (plantillaExterna.read())
	plantillaExterna.close()
	contexto = Context()
	documento = template.render (contexto)
	return HttpResponse (documento)
	

