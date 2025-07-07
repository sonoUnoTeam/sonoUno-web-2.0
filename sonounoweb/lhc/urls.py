from django.urls import path
from . import views

app_name = "lhc"
urlpatterns = [
    # Vista principal
    path("", views.index, name="index"),
    path("index/", views.index, name="index"),
    
    # Visualización de eventos (nueva arquitectura)
    path('evento/<str:file_name>/', views.LHCEventView.as_view(), name='evento'),
    path('grafico/<str:file_name>/', views.LHCEventView.as_view(), name='grafico'),  # Mantener esta URL pero usando nueva vista
    
    # APIs para extracción de medios (solo en DEBUG)
    path('api/extract-audio/', views.extract_audio_from_video_api, name='api_extract_audio'),
    path('api/extract-image/', views.extract_image_from_video_api, name='api_extract_image'),
    
    # Estadísticas de caché (solo en DEBUG)
    path('cache/stats/', views.cache_stats, name='cache_stats'),
]