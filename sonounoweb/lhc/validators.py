# -*- coding: utf-8 -*-
"""
Validadores de seguridad para la aplicación LHC.
Implementa validaciones críticas para prevenir vulnerabilidades.
"""

import os
import re
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from typing import List, Optional

# Lista blanca de archivos permitidos
ALLOWED_LHC_FILES = [
    'sonification_reduced.txt',
    'lhc_event_data.txt',
    'particle_collision_data.txt',
    'test_lhc_data.txt'
]

# Límites de seguridad
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VIDEO_DURATION = 300  # 5 minutos
MAX_EVENT_INDEX = 10000  # Máximo número de eventos
MAX_CACHE_SIZE = 100 * 1024 * 1024  # 100MB total cache
MAX_CONCURRENT_REQUESTS = 5

class LHCSecurityValidator:
    """Validador de seguridad para operaciones LHC."""
    
    @staticmethod
    def validate_file_name(file_name: str) -> str:
        """
        Valida que el nombre de archivo sea seguro y esté permitido.
        
        Args:
            file_name: Nombre del archivo a validar
            
        Returns:
            str: Nombre de archivo sanitizado
            
        Raises:
            PermissionDenied: Si el archivo no está permitido
            ValidationError: Si el formato es inválido
        """
        if not file_name:
            raise ValidationError("Nombre de archivo requerido")
        
        # Sanitizar el nombre del archivo
        sanitized_name = os.path.basename(file_name)
        
        # Verificar caracteres peligrosos
        dangerous_chars = ['..', '/', '\\', '|', ';', '&', '$', '`', '(', ')', '{', '}']
        for char in dangerous_chars:
            if char in sanitized_name:
                raise ValidationError(f"Carácter no permitido en nombre de archivo: {char}")
        
        # Verificar extensión
        if not sanitized_name.lower().endswith('.txt'):
            raise ValidationError("Solo se permiten archivos .txt")
        
        # Verificar contra lista blanca
        if sanitized_name not in ALLOWED_LHC_FILES:
            raise PermissionDenied(
                f"Archivo no permitido: {sanitized_name}. "
                f"Archivos permitidos: {', '.join(ALLOWED_LHC_FILES)}"
            )
        
        return sanitized_name
    
    @staticmethod
    def validate_event_index(event_index: int, total_events: int) -> int:
        """
        Valida el índice del evento.
        
        Args:
            event_index: Índice del evento (1-based)
            total_events: Total de eventos disponibles
            
        Returns:
            int: Índice validado
            
        Raises:
            ValidationError: Si el índice es inválido
        """
        if not isinstance(event_index, int):
            raise ValidationError("El índice del evento debe ser un número entero")
        
        if event_index < 1:
            return 1
        
        if event_index > total_events:
            return total_events
        
        if event_index > MAX_EVENT_INDEX:
            raise ValidationError(f"Índice de evento excede el máximo permitido: {MAX_EVENT_INDEX}")
        
        return event_index
    
    @staticmethod
    def validate_file_size(file_path: str) -> bool:
        """
        Valida el tamaño del archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            bool: True si el tamaño es válido
            
        Raises:
            ValidationError: Si el archivo es demasiado grande
        """
        if not os.path.exists(file_path):
            raise ValidationError(f"Archivo no encontrado: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            raise ValidationError(
                f"Archivo demasiado grande: {file_size / (1024*1024):.2f}MB. "
                f"Máximo permitido: {MAX_FILE_SIZE / (1024*1024):.2f}MB"
            )
        
        return True
    
    @staticmethod
    def validate_cache_size(cache_dir: str) -> bool:
        """
        Valida el tamaño total del caché.
        
        Args:
            cache_dir: Directorio del caché
            
        Returns:
            bool: True si el tamaño es válido
        """
        if not os.path.exists(cache_dir):
            return True
        
        total_size = 0
        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        
        if total_size > MAX_CACHE_SIZE:
            # Auto-limpiar caché más antiguo
            LHCSecurityValidator._cleanup_old_cache(cache_dir)
        
        return True
    
    @staticmethod
    def _cleanup_old_cache(cache_dir: str) -> None:
        """Limpia archivos de caché más antiguos."""
        try:
            import time
            import json
            
            files_with_time = []
            for filename in os.listdir(cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(cache_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            cache_data = json.load(f)
                            timestamp = cache_data.get('timestamp', 0)
                            files_with_time.append((timestamp, file_path))
                    except:
                        # Si no se puede leer, eliminar
                        try:
                            os.remove(file_path)
                        except:
                            pass
            
            # Ordenar por timestamp y eliminar los más antiguos
            files_with_time.sort()
            files_to_remove = len(files_with_time) // 2  # Eliminar la mitad más antigua
            
            for i in range(files_to_remove):
                try:
                    os.remove(files_with_time[i][1])
                except:
                    pass
                    
        except Exception:
            # Si falla la limpieza selectiva, limpiar todo
            try:
                import shutil
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir, exist_ok=True)
            except:
                pass

class LHCRateLimiter:
    """Control de rate limiting para prevenir DoS."""
    
    _active_requests = {}
    
    @classmethod
    def check_rate_limit(cls, client_ip: str) -> bool:
        """
        Verifica si el cliente puede hacer más requests.
        
        Args:
            client_ip: IP del cliente
            
        Returns:
            bool: True si puede continuar
        """
        import time
        current_time = time.time()
        
        # Limpiar requests antiguos (más de 5 minutos)
        cls._cleanup_old_requests(current_time)
        
        # Contar requests activos de esta IP
        active_count = len([
            req for req in cls._active_requests.values()
            if req.get('ip') == client_ip and req.get('timestamp', 0) > current_time - 300
        ])
        
        return active_count < MAX_CONCURRENT_REQUESTS
    
    @classmethod
    def add_request(cls, client_ip: str, request_id: str) -> None:
        """Registra un nuevo request."""
        import time
        cls._active_requests[request_id] = {
            'ip': client_ip,
            'timestamp': time.time()
        }
    
    @classmethod
    def remove_request(cls, request_id: str) -> None:
        """Remueve un request completado."""
        cls._active_requests.pop(request_id, None)
    
    @classmethod
    def _cleanup_old_requests(cls, current_time: float) -> None:
        """Limpia requests antiguos."""
        old_requests = [
            req_id for req_id, req_data in cls._active_requests.items()
            if req_data.get('timestamp', 0) < current_time - 300
        ]
        for req_id in old_requests:
            cls._active_requests.pop(req_id, None)
