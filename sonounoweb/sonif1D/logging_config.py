# -*- coding: utf-8 -*-
"""
Configuración de logging mejorada para la aplicación sonif1D.
"""

import logging
import logging.handlers
import os
from django.conf import settings

def setup_sonif1D_logging():
    """
    Configura el sistema de logging para la aplicación sonif1D.
    """
    # Crear directorio de logs si no existe
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar formato de logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Logger principal para sonif1D
    sonif1D_logger = logging.getLogger('sonif1D')
    sonif1D_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Handler para archivo (rotativo)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'sonif1D.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para consola (solo en DEBUG)
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        sonif1D_logger.addHandler(console_handler)
    
    sonif1D_logger.addHandler(file_handler)
    
    # Logger para errores críticos
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'sonif1D_errors.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    sonif1D_logger.addHandler(error_handler)
    
    return sonif1D_logger

# Inicializar logging al importar
try:
    setup_sonif1D_logging()
except Exception as e:
    # Fallback a logging básico si hay problemas
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
