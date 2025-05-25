from django.urls import path

from django.urls import path,include

from . import views
from .views import mostrar_grafico, GraficoView, ImportarArchivoView

app_name = "sonif1D"
urlpatterns = [
    # ex: /sonif1D/
    path("index", views.index, name="index"),
    # ex: /sonif1D/inicio
    path("inicio", views.inicio, name="inicio"),
    # ex: /sonif1D/ayuda
    path("ayuda", views.ayuda, name="ayuda"),
    # ex: /sonif1D/sonido
    path("sonido", views.sonido, name="sonido"),
    # ex: /sonif1D/grafico
    path('grafico/', GraficoView.as_view(), name='grafico'),
    # ex: /sonif1D/funciones_matematicas
    path("funciones_matematicas", views.funciones_matematicas, name="funciones_matematicas"),
    
    path('grafico/<str:nombre_archivo>/', mostrar_grafico, name='mostrar_grafico'),
    
    path('import_archivo/', ImportarArchivoView.as_view(), name='importar_archivo'),
]