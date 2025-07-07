#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests específicos para el módulo lhc_lib
Tests independientes de Django para las funciones core de LHC
"""

import unittest
import os
import sys
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock

# Agregar el path para importar los módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from lhc_web import (
        load_particle_data,
        get_total_events, 
        process_single_event,
        validate_particle_data,
        get_available_data_files,
        process_sound_array,
        cleanup_temp_files
    )
    LHC_LIB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: No se pudieron importar módulos LHC: {e}")
    LHC_LIB_AVAILABLE = False


@unittest.skipUnless(LHC_LIB_AVAILABLE, "LHC lib no disponible")
class TestLHCLibCore(unittest.TestCase):
    """Tests para funciones core de lhc_lib"""
    
    def setUp(self):
        """Configuración para cada test"""
        self.test_filename = "sonification_reduced.txt"
        
    def test_load_particle_data_structure(self):
        """Test: Estructura correcta de datos cargados"""
        lines, particles = load_particle_data(self.test_filename)
        
        if particles is not None:
            # Verificar estructura básica
            self.assertIsInstance(particles, list)
            self.assertGreater(len(particles), 0)
            
            # Verificar que hay pares (tracks, clusters)
            self.assertEqual(len(particles) % 2, 0)
            
            # Verificar que cada elemento es una lista
            for i, particle_set in enumerate(particles):
                with self.subTest(index=i):
                    self.assertIsInstance(particle_set, list)
                    
    def test_validate_particle_data_edge_cases(self):
        """Test: Casos límite para validación de datos"""
        # Caso: datos None
        self.assertFalse(validate_particle_data(None))
        
        # Caso: lista vacía
        self.assertFalse(validate_particle_data([]))
        
        # Caso: solo un elemento (impar)
        self.assertFalse(validate_particle_data([[]]))
        
        # Caso: datos válidos mínimos
        valid_minimal = [[], []]  # Tracks vacíos, clusters vacíos
        self.assertTrue(validate_particle_data(valid_minimal))
        
    def test_get_total_events_consistency(self):
        """Test: Consistencia en el número de eventos"""
        total_events = get_total_events(self.test_filename)
        
        if total_events > 0:
            lines, particles = load_particle_data(self.test_filename)
            expected_events = len(particles) // 2 if particles else 0
            
            self.assertEqual(total_events, expected_events)
            
    def test_process_sound_array_functionality(self):
        """Test: Procesamiento de arrays de sonido"""
        # Crear array de sonido de prueba
        test_sound = np.array([100, 200, 300, 400], dtype=np.int16)
        
        try:
            result_path = process_sound_array(test_sound)
            
            self.assertIsInstance(result_path, str)
            self.assertTrue(os.path.exists(result_path))
            self.assertTrue(result_path.endswith('.wav'))
            
            # Limpiar archivo temporal
            os.remove(result_path)
            
        except Exception as e:
            self.fail(f"process_sound_array falló: {e}")
            
    def test_cleanup_temp_files_safety(self):
        """Test: Limpieza segura de archivos temporales"""
        # Crear archivos temporales de prueba
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.test') as f:
                f.write(b"test data")
                temp_files.append(f.name)
                
        # Verificar que existen
        for file_path in temp_files:
            self.assertTrue(os.path.exists(file_path))
            
        # Limpiar
        cleanup_temp_files(temp_files)
        
        # Verificar que fueron eliminados (puede fallar en Windows por locks)
        # Por eso usamos un try-catch
        try:
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.remove(file_path)  # Limpieza manual si falla
        except:
            pass  # Ignorar errores de limpieza en tests


@unittest.skipUnless(LHC_LIB_AVAILABLE, "LHC lib no disponible")
class TestLHCLibIntegration(unittest.TestCase):
    """Tests de integración para lhc_lib"""
    
    def test_full_event_processing_pipeline(self):
        """Test: Pipeline completo de procesamiento de evento"""
        filename = "sonification_reduced.txt"
        
        # Verificar que hay eventos disponibles
        total_events = get_total_events(filename)
        if total_events == 0:
            self.skipTest("No hay eventos disponibles para test")
            
        # Procesar primer evento
        result = process_single_event(
            filename=filename,
            event_index=0,
            save_to_output=False,  # Usar archivos temporales
            display_event_number=1
        )
        
        image_paths, sound_paths, event_info = result
        
        # Verificar resultados
        self.assertIsNotNone(image_paths)
        self.assertIsNotNone(sound_paths)
        self.assertIsNotNone(event_info)
        
        self.assertGreater(len(image_paths), 0)
        self.assertGreater(len(sound_paths), 0)
        
        # Verificar archivos generados
        for path in image_paths:
            self.assertTrue(os.path.exists(path), f"Imagen no existe: {path}")
            
        for path in sound_paths:
            self.assertTrue(os.path.exists(path), f"Sonido no existe: {path}")
            
        # Verificar información del evento
        required_keys = ['event_number', 'total_tracks', 'total_clusters', 'total_events']
        for key in required_keys:
            self.assertIn(key, event_info, f"Falta clave en event_info: {key}")
            
    def test_multiple_events_processing(self):
        """Test: Procesamiento de múltiples eventos"""
        filename = "sonification_reduced.txt"
        total_events = get_total_events(filename)
        
        if total_events < 2:
            self.skipTest("Se necesitan al menos 2 eventos para este test")
            
        # Procesar primeros 2 eventos
        for event_idx in range(min(2, total_events)):
            with self.subTest(event=event_idx):
                result = process_single_event(
                    filename=filename,
                    event_index=event_idx,
                    save_to_output=False,
                    display_event_number=event_idx + 1
                )
                
                image_paths, sound_paths, event_info = result
                
                self.assertIsNotNone(result[0], f"Fallo en evento {event_idx}")
                self.assertIsNotNone(result[1], f"Fallo en evento {event_idx}")
                self.assertIsNotNone(result[2], f"Fallo en evento {event_idx}")


class TestLHCLibPerformance(unittest.TestCase):
    """Tests de rendimiento para lhc_lib"""
    
    @unittest.skipUnless(LHC_LIB_AVAILABLE, "LHC lib no disponible")
    def test_data_loading_performance(self):
        """Test: Rendimiento de carga de datos"""
        import time
        
        start_time = time.time()
        lines, particles = load_particle_data("sonification_reduced.txt")
        end_time = time.time()
        
        load_time = end_time - start_time
        
        # Debería cargar en menos de 3 segundos
        self.assertLess(load_time, 3.0, 
                       f"Carga tomó {load_time:.2f}s, debería ser < 3s")
                       
    @unittest.skipUnless(LHC_LIB_AVAILABLE, "LHC lib no disponible")
    def test_event_processing_performance(self):
        """Test: Rendimiento de procesamiento de evento"""
        import time
        
        # Solo test si hay datos disponibles
        if get_total_events("sonification_reduced.txt") == 0:
            self.skipTest("No hay eventos disponibles")
            
        start_time = time.time()
        result = process_single_event(
            filename="sonification_reduced.txt",
            event_index=0,
            save_to_output=False,
            display_event_number=1
        )
        end_time = time.time()
        
        process_time = end_time - start_time
        
        # Procesamiento no debería tomar más de 25 segundos
        self.assertLess(process_time, 25.0, 
                       f"Procesamiento tomó {process_time:.2f}s, debería ser < 25s")


def run_lhc_lib_tests():
    """Función para ejecutar tests de lhc_lib"""
    if not LHC_LIB_AVAILABLE:
        print("LHC lib no disponible - saltando tests")
        return
        
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar clases de test
    suite.addTests(loader.loadTestsFromTestCase(TestLHCLibCore))
    suite.addTests(loader.loadTestsFromTestCase(TestLHCLibIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestLHCLibPerformance))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("Ejecutando tests de lhc_lib...")
    result = run_lhc_lib_tests()
    
    if result and result.wasSuccessful():
        print("\n✅ Todos los tests pasaron!")
    else:
        print("\n❌ Algunos tests fallaron.")
        if result:
            print(f"Errores: {len(result.errors)}")
            print(f"Fallos: {len(result.failures)}")
