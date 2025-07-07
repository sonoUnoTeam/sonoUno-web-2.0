#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de inicialización para las mejoras de la aplicación LHC.
Configura logging, valida archivos y prepara el entorno.
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sonounoweb.settings')
django.setup()

from lhc.logging_config import setup_lhc_logging
from lhc.validators import LHCSecurityValidator
from lhc.services import LHCCacheService
from utils.lhc_lib.lhc_web import get_available_data_files, validate_file_size
import logging

def main():
    """Función principal de inicialización."""
    print("🚀 Iniciando configuración de mejoras LHC...")
    
    # 1. Configurar logging
    try:
        logger = setup_lhc_logging()
        print("✅ Logging configurado correctamente")
        logger.info("Sistema de logging LHC inicializado")
    except Exception as e:
        print(f"❌ Error configurando logging: {e}")
        return False
    
    # 2. Crear directorios necesarios
    try:
        from django.conf import settings
        
        # Directorio temporal
        temp_dir = os.path.join(settings.BASE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Directorio de caché de videos
        cache_dir = os.path.join(temp_dir, 'video_cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Directorio de logs
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        print("✅ Directorios creados correctamente")
        logger.info("Directorios del sistema verificados")
        
    except Exception as e:
        print(f"❌ Error creando directorios: {e}")
        return False
    
    # 3. Validar archivos de datos disponibles
    try:
        available_files = get_available_data_files()
        print(f"📁 Archivos de datos encontrados: {len(available_files)}")
        
        for filename in available_files:
            try:
                # Validar cada archivo
                validated_name = LHCSecurityValidator.validate_file_name(filename)
                print(f"   ✅ {validated_name}")
                logger.info(f"Archivo validado: {validated_name}")
            except Exception as e:
                print(f"   ❌ {filename}: {e}")
                logger.warning(f"Archivo inválido {filename}: {e}")
        
        if not available_files:
            print("⚠️  No se encontraron archivos de datos LHC")
            logger.warning("No hay archivos de datos disponibles")
            
    except Exception as e:
        print(f"❌ Error validando archivos: {e}")
        return False
    
    # 4. Verificar servicios
    try:
        cache_service = LHCCacheService()
        stats = cache_service.get_cache_stats()
        print(f"💾 Caché: {stats['files']} archivos, {stats['size_mb']} MB")
        logger.info(f"Estadísticas de caché: {stats}")
        
    except Exception as e:
        print(f"❌ Error verificando servicios: {e}")
        return False
    
    # 5. Verificar configuración de seguridad
    try:
        from lhc.validators import MAX_FILE_SIZE, MAX_EVENT_INDEX, MAX_CACHE_SIZE
        
        print(f"🔒 Límites de seguridad configurados:")
        print(f"   - Tamaño máximo de archivo: {MAX_FILE_SIZE // (1024*1024)} MB")
        print(f"   - Máximo índice de evento: {MAX_EVENT_INDEX}")
        print(f"   - Tamaño máximo de caché: {MAX_CACHE_SIZE // (1024*1024)} MB")
        
        logger.info("Configuración de seguridad verificada")
        
    except Exception as e:
        print(f"❌ Error verificando seguridad: {e}")
        return False
    
    # 6. Resumen final
    print("\n🎉 Configuración completada exitosamente!")
    print("\n📋 Resumen de mejoras implementadas:")
    print("   ✅ Validación de seguridad para inputs")
    print("   ✅ Sistema de logging estructurado")
    print("   ✅ Servicios separados (Cache, Video, Event)")
    print("   ✅ Rate limiting para prevenir DoS")
    print("   ✅ Gestión mejorada de recursos y memoria")
    print("   ✅ Thread-safety para operaciones críticas")
    print("   ✅ Caché optimizado con TTL")
    print("   ✅ Manejo robusto de errores")
    
    print("\n🔗 URLs disponibles:")
    print("   • /lhc/ - Vista principal")
    print("   • /lhc/evento/<archivo>/ - Nueva arquitectura")
    print("   • /lhc/grafico/<archivo>/ - Compatibilidad")
    print("   • /lhc/cache/stats/ - Estadísticas (DEBUG)")
    
    print("\n💡 Próximos pasos recomendados:")
    print("   1. Ejecutar tests: python manage.py test lhc")
    print("   2. Verificar logs en: logs/lhc.log")
    print("   3. Monitorear caché en: /lhc/cache/stats/")
    print("   4. Considerar implementar Celery para procesamiento asíncrono")
    
    logger.info("Inicialización completada exitosamente")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
