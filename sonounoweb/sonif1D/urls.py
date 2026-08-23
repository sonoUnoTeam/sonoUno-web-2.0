from django.urls import path
from . import views
from .views import mostrar_grafico, ImportarArchivoView

app_name = "sonif1D"
urlpatterns = [
    # Vista principal
    path("", views.index, name="index"),
    path("index", views.index, name="index"),
    
    # Ayuda
    path("help/", views.ayuda_sonif1d, name="help"),
    
    # Carga de datos y ejemplos
    path('grafico/<str:nombre_archivo>/', mostrar_grafico, name='mostrar_grafico'),
    path('import_archivo/', ImportarArchivoView.as_view(), name='importar_archivo'),
    
    # Endpoints AJAX
    path('aplicar_filtro/', views.aplicar_filtro_ajax, name='aplicar_filtro'),
    path('configurar_sonido/', views.configurar_sonido_ajax, name='configurar_sonido'),
    path('aplicar_cuadratica/', views.aplicar_cuadratica_ajax, name='aplicar_cuadratica'),
    path('buscar_picos/', views.buscar_picos_ajax, name='buscar_picos'),
    path('aplicar_logaritmica/', views.aplicar_logaritmica_ajax, name='aplicar_logaritmica'),
]