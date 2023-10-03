"""
URL configuration for sonounoweb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from sonounoweb.views import index
from sonounoweb.views import sonido
from sonounoweb.views import grafico
from sonounoweb.views import funciones_matematicas
from sonounoweb.views import inicio
from sonounoweb.views import ayuda

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path("sonif1D/", include("sonif1D.urls")),
    path('admin/', admin.site.urls),
    # de aquí en adelante se borrará
    path('index', index),
    path('sonido', sonido),
    path('grafico', grafico),
    path('funciones_matematicas', funciones_matematicas),
    path('inicio', inicio),
    path('ayuda', ayuda),
       
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
