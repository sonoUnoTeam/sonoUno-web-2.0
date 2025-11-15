# -*- coding: utf-8 -*-
"""
Configuración de logging mejorada para la aplicación LHC.
"""

import logging
import logging.handlers
import os
from django.conf import settings

def setup_lhc_logging():
    """
    Configura el sistema de logging para la aplicación LHC.
    """
    # Crear directorio de logs si no existe
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar formato de logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Logger principal para LHC
    lhc_logger = logging.getLogger('lhc')
    lhc_logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    
    # Handler para archivo (rotativo)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'lhc.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola (solo en DEBUG)
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        lhc_logger.addHandler(console_handler)
    
    lhc_logger.addHandler(file_handler)
    
    # Logger para utils
    utils_logger = logging.getLogger('utils.lhc_lib')
    utils_logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    utils_logger.addHandler(file_handler)
    
    if settings.DEBUG:
        utils_logger.addHandler(console_handler)
    
    # Logger para errores críticos
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'lhc_errors.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    lhc_logger.addHandler(error_handler)
    utils_logger.addHandler(error_handler)
    
    return lhc_logger

# Inicializar logging al importar
try:
    setup_lhc_logging()
except Exception as e:
    # Fallback a logging básico si hay problemas
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
