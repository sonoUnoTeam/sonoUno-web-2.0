"""
Comando de gestión para limpiar archivos temporales antiguos.
Útil para ejecutar periódicamente y limpiar archivos que no pudieron ser eliminados
inmediatamente debido a bloqueos del sistema (especialmente en Windows).
"""

from django.core.management.base import BaseCommand
from lhc.services import LHCCleanupService


class Command(BaseCommand):
    help = 'Limpia archivos temporales antiguos que no pudieron ser eliminados anteriormente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la limpieza sin confirmación',
        )

    def handle(self, *args, **options):
        self.stdout.write('Iniciando limpieza de archivos temporales antiguos...')
        
        try:
            result = LHCCleanupService.cleanup_old_temp_files()
            
            if result['status'] == 'completed':
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Limpieza completada: {result["files_cleaned"]} archivos eliminados'
                    )
                )
                if result['files_failed'] > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Advertencia: {result["files_failed"]} archivos no pudieron ser eliminados'
                        )
                    )
            elif result['status'] == 'no_temp_dir':
                self.stdout.write(
                    self.style.WARNING('No se encontró directorio de archivos temporales')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error durante la limpieza: {result.get("error", "Error desconocido")}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error ejecutando comando de limpieza: {e}')
            )
