from django.apps import AppConfig


class ImagesonifConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'imagesonif'

    def ready(self):
        """Configurar logging cuando la aplicación esté lista."""
        from .logging_config import setup_imagesonif_logging
        setup_imagesonif_logging()
