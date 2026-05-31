# -*- coding: utf-8 -*-
"""
Configuración de logging mejorada para la aplicación ImageSonif.
"""

import logging
import logging.handlers
import os
from django.conf import settings

def setup_imagesonif_logging():
    """
    Configura el sistema de logging para la aplicación ImageSonif.
    """
    # Crear directorio de logs si no existe
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Configurar formato de logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )

    # Logger principal para ImageSonif
    imagesonif_logger = logging.getLogger('imagesonif')
    imagesonif_logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)

    # Handler para archivo (rotativo)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'imagesonif.log'),
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
        imagesonif_logger.addHandler(console_handler)

    imagesonif_logger.addHandler(file_handler)

    # Logger para utils
    utils_logger = logging.getLogger('utils.images-lib')
    utils_logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    utils_logger.addHandler(file_handler)

    # Logger para servicios
    services_logger = logging.getLogger('imagesonif.services')
    services_logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    services_logger.addHandler(file_handler)

    # Logger para vistas
    views_logger = logging.getLogger('imagesonif.views')
    views_logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    views_logger.addHandler(file_handler)

    # Logger para validadores
    validators_logger = logging.getLogger('imagesonif.validators')
    validators_logger.setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    validators_logger.addHandler(file_handler)