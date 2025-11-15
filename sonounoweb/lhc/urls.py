from django.urls import path
from . import views

app_name = "lhc"
urlpatterns = [
    # Vista principal
    path("", views.index, name="index"),
    path("index/", views.index, name="index"),
    
    # Visualización de eventos 
    path('evento/<str:file_name>/', views.LHCEventView.as_view(), name='evento'),    
    
    # Estadísticas de caché (solo en DEBUG)
    path('cache/stats/', views.cache_stats, name='cache_stats'),
]