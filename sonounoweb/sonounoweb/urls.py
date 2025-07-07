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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from sonif1D import views


urlpatterns = [
    path("", views.inicio, name='inicio'),
    path('admin/', admin.site.urls),  
    path("sonif1D/", include("sonif1D.urls")), # Incluye las urls de la app sonif1D
    path('muongraphy/', include('muongraphy.urls')), # Incluye las urls de la app moungraphy
    path('lhc/', include('lhc.urls')), # Incluye las urls de la app lhc
    
] 

# Agrega las URLs para servir archivos estáticos y multimedia
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)