# -*- coding: utf-8 -*-
"""
URLs para la aplicación de sonificación de imágenes.
"""

from django.urls import path
from . import views

app_name = 'imagesonif'

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.ImageSonificationView.as_view(), name='process'),
    path('cache-stats/', views.cache_stats, name='cache_stats'),
    path('rate-limit-stats/', views.rate_limit_stats, name='rate_limit_stats'),
    path('help/', views.help_page, name='help'),
]
