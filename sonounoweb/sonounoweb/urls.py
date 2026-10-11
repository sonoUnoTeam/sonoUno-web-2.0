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
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic import RedirectView

from sonif1D import views


class FaviconRedirectView(RedirectView):
    # Temporal y resuelta por request: la URL con hash cambia con cada collectstatic y
    # calcularla al importar falla con el storage de manifiesto si aún no se ejecutó
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return static_url('favicon.ico')


urlpatterns = [
    path("", views.inicio, name='inicio'),
    # Navegadores y buscadores piden /favicon.ico en la raíz aunque la página declare otro ícono
    path('favicon.ico', FaviconRedirectView.as_view()),
    path('admin/', admin.site.urls),  
    path("sonif1D/", include("sonif1D.urls")), # Incluye las urls de la app sonif1D
    path('muongraphy/', include('muongraphy.urls')), # Incluye las urls de la app moungraphy
    path('lhc/', include('lhc.urls')), # Incluye las urls de la app lhc
    path('imagesonif/', include('imagesonif.urls')), # Incluye las urls de la app imagesonif
    ] 

# Agrega las URLs para servir archivos estáticos y multimedia
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)