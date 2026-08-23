# -*- coding: utf-8 -*-
import base64
import json
import numpy as np
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from .validators import (
    Sonif1DValidator,
    ALLOWED_WAVEFORMS,
    ALLOWED_LINE_STYLES,
    ALLOWED_LINE_COLORS
)
from .forms import (
    ConfiguracionGraficoForm,
    ConfiguracionSonidoForm,
    FiltroSuavizadoForm,
    FuncionCuadraticaForm,
    FuncionLogaritmicaForm,
    BuscadorPicosForm
)


class Sonif1DBlackBoxTestHelper:
    """Utilidades para validación de caja negra de artefactos multimedia y datos."""

    @staticmethod
    def assert_valid_wav_base64(test_case, b64_str):
        """Valida que la cadena base64 decodifique en un archivo WAV con encabezado RIFF/WAVE válido."""
        test_case.assertIsInstance(b64_str, str)
        test_case.assertTrue(len(b64_str) > 0, "La cadena de audio base64 no debe estar vacía.")
        raw_bytes = base64.b64decode(b64_str)
        # Un archivo WAV mínimo tiene al menos 44 bytes de encabezado
        test_case.assertGreater(len(raw_bytes), 44, "El archivo WAV decodificado es demasiado pequeño.")
        test_case.assertEqual(raw_bytes[:4], b'RIFF', "El encabezado del audio debe comenzar con 'RIFF'.")
        test_case.assertEqual(raw_bytes[8:12], b'WAVE', "El formato del audio debe ser 'WAVE'.")


class Sonif1DViewRoutingTests(TestCase):
    """Pruebas de caja negra sobre rutas públicas, renderizado de plantillas y datasets de ejemplo."""

    def setUp(self):
        self.client = Client()

    def test_index_view_renders_expected_structure(self):
        """Verifica que la página principal cargue status 200 y contenga los componentes modulares."""
        for url_name in ['sonif1D:index', '/sonif1D/', '/sonif1D/index']:
            target = reverse('sonif1D:index') if ':' in url_name else url_name
            response = self.client.get(target)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sonif1D/index.html')
            self.assertTemplateUsed(response, 'sonif1D/base.html')
            # Pestañas modulares en la interfaz
            self.assertContains(response, 'tab-guia-btn')
            self.assertContains(response, 'tab-grafico-btn')
            self.assertContains(response, 'tab-sonido-btn')
            self.assertContains(response, 'tab-matematicas-btn')
            self.assertContains(response, 'tab-marcadores-btn')

    def test_help_view_renders_correctly(self):
        """Verifica que la vista de ayuda cargue con status 200 y use la plantilla correspondiente."""
        response = self.client.get(reverse('sonif1D:help'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/help.html')

    def test_mostrar_grafico_valid_sample(self):
        """Verifica que al solicitar un dataset de ejemplo se devuelvan los datos y el audio generado."""
        response = self.client.get(reverse('sonif1D:mostrar_grafico', args=['sinusoidal.txt']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/index.html')
        self.assertIn('audio_base64', response.context)
        self.assertIn('data_json', response.context)
        
        # Validación de datos estructurados en formato JSON
        raw_data = json.loads(response.context['data_json'])
        self.assertIsInstance(raw_data, list)
        self.assertGreater(len(raw_data), 0)
        self.assertEqual(len(raw_data[0]), 2)  # Columnas [X, Y]
        
        # Validación de integridad del audio WAV generado
        Sonif1DBlackBoxTestHelper.assert_valid_wav_base64(self, response.context['audio_base64'])

    def test_mostrar_grafico_nonexistent_file(self):
        """Verifica que al solicitar un dataset inexistente la app no crashee con error 500."""
        response = self.client.get(reverse('sonif1D:mostrar_grafico', args=['archivo_inexistente_123.txt']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/index.html')


class Sonif1DValidatorUnitTests(TestCase):
    """Pruebas unitarias para Sonif1DValidator en todos los parámetros de las pestañas."""

    def test_validate_sonido_params_valid(self):
        """Verifica que parámetros válidos de sonido pasen correctamente."""
        res = Sonif1DValidator.validate_sonido_params('flute', 300, 4000, True)
        self.assertEqual(res['waveform'], 'flute')
        self.assertEqual(res['min_freq'], 300.0)
        self.assertEqual(res['max_freq'], 4000.0)
        self.assertTrue(res['logscale'])

    def test_validate_sonido_params_invalid_waveform(self):
        """Verifica que un instrumento inválido lance ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_sonido_params(waveform='guitarra_invalida')
        self.assertIn('waveform', ctx.exception.message_dict)

    def test_validate_sonido_params_invalid_frequency_ranges(self):
        """Verifica que frecuencias fuera de límites lancen ValidationError."""
        # Frecuencia mínima por debajo de 20 Hz
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_sonido_params(min_freq=5, max_freq=5000)
        self.assertIn('min_freq', ctx.exception.message_dict)

        # Frecuencia máxima por encima de 20000 Hz
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_sonido_params(min_freq=500, max_freq=25000)
        self.assertIn('max_freq', ctx.exception.message_dict)

        # min_freq mayor que max_freq
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_sonido_params(min_freq=5000, max_freq=1000)
        self.assertIn('min_freq', ctx.exception.message_dict)

    def test_validate_filtro_params_valid(self):
        """Verifica que parámetros válidos de suavizado pasen correctamente."""
        res = Sonif1DValidator.validate_filtro_params(window_size=31, order=4, data_len=100)
        self.assertEqual(res['window_size'], 31)
        self.assertEqual(res['order'], 4)

    def test_validate_filtro_params_even_window(self):
        """Verifica que un tamaño de ventana par sea rechazado."""
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_filtro_params(window_size=30, order=4)
        self.assertIn('window_size', ctx.exception.message_dict)

    def test_validate_filtro_params_window_order_incompatibility(self):
        """Verifica que ventana menor que orden + 2 sea rechazada."""
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_filtro_params(window_size=5, order=5)
        self.assertIn('window_size', ctx.exception.message_dict)

    def test_validate_filtro_params_window_exceeds_data_length(self):
        """Verifica que una ventana mayor al dataset sea rechazada."""
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_filtro_params(window_size=51, order=4, data_len=20)
        self.assertIn('window_size', ctx.exception.message_dict)

    def test_validate_cuadratica_params_valid_and_invalid(self):
        """Verifica validación de coeficientes cuadráticos."""
        res = Sonif1DValidator.validate_cuadratica_params(2.5, -1.0, 0.5)
        self.assertEqual(res['coef_a'], 2.5)
        self.assertEqual(res['coef_b'], -1.0)
        self.assertEqual(res['coef_c'], 0.5)

        # No numérico
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_cuadratica_params(coef_a="invalido", coef_b=0, coef_c=0)
        self.assertIn('coef_a', ctx.exception.message_dict)

    def test_validate_logaritmica_params_valid_and_invalid(self):
        """Verifica validación de coeficientes logarítmicos."""
        res = Sonif1DValidator.validate_logaritmica_params(1.0, 2.0, -0.5)
        self.assertEqual(res['coef_a'], 1.0)
        self.assertEqual(res['coef_c'], 2.0)
        self.assertEqual(res['coef_b'], -0.5)

        # Infinito o NaN
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_logaritmica_params(coef_a=float('inf'), coef_c=1, coef_b=0)
        self.assertIn('coef_a', ctx.exception.message_dict)

    def test_validate_picos_params_valid_and_invalid(self):
        """Verifica validación de parámetros para el buscador de picos."""
        res = Sonif1DValidator.validate_picos_params(prominencia=0.25, distancia=10)
        self.assertEqual(res['prominencia'], 0.25)
        self.assertEqual(res['distancia'], 10)

        # Prominencia menor a cero
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_picos_params(prominencia=-0.1, distancia=5)
        self.assertIn('prominencia', ctx.exception.message_dict)

        # Distancia menor a 1
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_picos_params(prominencia=0.1, distancia=0)
        self.assertIn('distancia', ctx.exception.message_dict)

    def test_validate_visual_params_valid_and_invalid(self):
        """Verifica validación de configuración visual del gráfico."""
        res = Sonif1DValidator.validate_visual_params(
            name_grafic="Mi Gráfico",
            name_eje_x="Tiempo",
            name_eje_y="Voltaje",
            estilo_linea="dot",
            color_linea="red"
        )
        self.assertEqual(res['name_grafic'], "Mi Gráfico")
        self.assertEqual(res['color_linea'], "red")

        # Título excesivamente largo (> 100 caracteres)
        long_title = "A" * 105
        with self.assertRaises(ValidationError) as ctx:
            Sonif1DValidator.validate_visual_params(name_grafic=long_title)
        self.assertIn('name_grafic', ctx.exception.message_dict)


class Sonif1DFormsUnitTests(TestCase):
    """Pruebas unitarias para formularios Django en sonif1D."""

    def test_configuracion_sonido_form_valid(self):
        form = ConfiguracionSonidoForm(data={
            'instrumento': 'piano',
            'min_freq': 440,
            'max_freq': 4400,
            'logscale': True
        })
        self.assertTrue(form.is_valid())

    def test_configuracion_sonido_form_invalid_crossover(self):
        form = ConfiguracionSonidoForm(data={
            'instrumento': 'piano',
            'min_freq': 5000,
            'max_freq': 2000,
            'logscale': False
        })
        self.assertFalse(form.is_valid())
        self.assertIn('min_freq', form.errors)

    def test_filtro_suavizado_form_even_window(self):
        form = FiltroSuavizadoForm(data={'window_size': 20, 'order': 3})
        self.assertFalse(form.is_valid())
        self.assertIn('window_size', form.errors)

    def test_buscador_picos_form_negative_dist(self):
        form = BuscadorPicosForm(data={'prominencia': 0.1, 'distancia': -5})
        self.assertFalse(form.is_valid())
        self.assertIn('distancia', form.errors)


class Sonif1DAjaxEndpointsTests(TestCase):
    """Pruebas de caja negra sobre endpoints AJAX de procesamiento numérico y síntesis sonora."""

    def setUp(self):
        self.client = Client()

    def test_configurar_sonido_sine_and_waveforms(self):
        """Verifica la generación de audio WAV con diferentes timbres e instrumentos."""
        sample_data = [[0.0, 0.0], [0.1, 0.5], [0.2, 0.8], [0.3, 1.0], [0.4, 0.7], [0.5, 0.2]]
        waveforms = ['sine', 'synthwave', 'flute', 'piano', 'celesta', 'pipe organ']

        for wf in waveforms:
            payload = {
                'data_json': json.dumps(sample_data),
                'waveform': wf,
                'min_freq': 400,
                'max_freq': 3000,
                'logscale': False
            }
            response = self.client.post(
                reverse('sonif1D:configurar_sonido'),
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data.get('success'))
            Sonif1DBlackBoxTestHelper.assert_valid_wav_base64(self, data.get('audio_base64'))

    def test_configurar_sonido_validation_error_min_greater_than_max(self):
        """Verifica que min_freq >= max_freq retorne 400 Bad Request con error descriptivo."""
        sample_data = [[0.0, 0.1], [1.0, 0.5]]
        payload = {
            'data_json': json.dumps(sample_data),
            'waveform': 'sine',
            'min_freq': 6000,
            'max_freq': 2000,
            'logscale': False
        }
        response = self.client.post(
            reverse('sonif1D:configurar_sonido'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('field_errors', data)

    def test_configurar_sonido_logscale(self):
        """Verifica la síntesis sonora con escala logarítmica habilitada."""
        sample_data = [[0.0, 0.1], [1.0, 0.5], [2.0, 1.0]]
        payload = {
            'data_json': json.dumps(sample_data),
            'waveform': 'sine',
            'min_freq': 300,
            'max_freq': 4000,
            'logscale': True
        }
        response = self.client.post(
            reverse('sonif1D:configurar_sonido'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        Sonif1DBlackBoxTestHelper.assert_valid_wav_base64(self, data.get('audio_base64'))

    def test_aplicar_filtro_savitzky_golay(self):
        """Verifica que el suavizado de señal retorne datos procesados y un nuevo audio válido."""
        x = np.linspace(0, 10, 50)
        y = np.sin(x) + np.random.normal(0, 0.1, 50)
        sample_data = np.column_stack((x, y)).tolist()

        payload = {
            'data_json': json.dumps(sample_data),
            'window_size': 31,
            'order': 4
        }
        response = self.client.post(
            reverse('sonif1D:aplicar_filtro'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('data_json', data)
        
        filtered_data = json.loads(data['data_json'])
        self.assertEqual(len(filtered_data), len(sample_data))
        Sonif1DBlackBoxTestHelper.assert_valid_wav_base64(self, data.get('audio_base64'))

    def test_aplicar_filtro_even_window_returns_400(self):
        """Verifica que enviar una ventana par retorne 400 Bad Request."""
        sample_data = [[0.0, 1.0], [1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0], [5.0, 6.0], [6.0, 7.0]]
        payload = {
            'data_json': json.dumps(sample_data),
            'window_size': 4,
            'order': 2
        }
        response = self.client.post(
            reverse('sonif1D:aplicar_filtro'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_aplicar_cuadratica_black_box(self):
        """Verifica que la transformación cuadrática y' = a*y^2 + b*y + c devuelva las salidas esperadas."""
        sample_data = [[0.0, 2.0], [1.0, 3.0], [2.0, 4.0]]
        payload = {
            'data_json': json.dumps(sample_data),
            'coef_a': 2.0,
            'coef_b': 1.0,
            'coef_c': 3.0
        }
        response = self.client.post(
            reverse('sonif1D:aplicar_cuadratica'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        
        res_data = json.loads(data['data_json'])
        # y' = 2*(2^2) + 1*(2) + 3 = 8 + 2 + 3 = 13.0
        self.assertAlmostEqual(res_data[0][1], 13.0)
        # y' = 2*(3^2) + 1*(3) + 3 = 18 + 3 + 3 = 24.0
        self.assertAlmostEqual(res_data[1][1], 24.0)
        # y' = 2*(4^2) + 1*(4) + 3 = 32 + 4 + 3 = 39.0
        self.assertAlmostEqual(res_data[2][1], 39.0)
        Sonif1DBlackBoxTestHelper.assert_valid_wav_base64(self, data.get('audio_base64'))

    def test_aplicar_cuadratica_invalid_coef_returns_400(self):
        """Verifica que coeficientes no numéricos retornen 400 Bad Request."""
        sample_data = [[0.0, 2.0], [1.0, 3.0]]
        payload = {
            'data_json': json.dumps(sample_data),
            'coef_a': "no_es_numero",
            'coef_b': 1.0,
            'coef_c': 0.0
        }
        response = self.client.post(
            reverse('sonif1D:aplicar_cuadratica'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_aplicar_logaritmica_domain_protection(self):
        """Verifica la transformación logarítmica y la protección ante valores de dominio no positivos."""
        sample_data = [[0.0, 1.0], [1.0, 2.0], [2.0, -0.99], [3.0, -10.0]]
        payload = {
            'data_json': json.dumps(sample_data),
            'coef_a': 2.0,
            'coef_c': 1.0,
            'coef_b': 0.5
        }
        response = self.client.post(
            reverse('sonif1D:aplicar_logaritmica'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        
        res_data = json.loads(data['data_json'])
        self.assertEqual(len(res_data), 4)
        for point in res_data:
            self.assertFalse(np.isnan(point[1]))
            self.assertFalse(np.isinf(point[1]))
        Sonif1DBlackBoxTestHelper.assert_valid_wav_base64(self, data.get('audio_base64'))

    def test_buscar_picos(self):
        """Verifica que el detector de picos identifique correctamente los máximos locales."""
        x = np.linspace(0, 40, 100)
        y = np.exp(-((x - 10) ** 2) / 4) + np.exp(-((x - 30) ** 2) / 4)
        sample_data = np.column_stack((x, y)).tolist()

        payload = {
            'data_json': json.dumps(sample_data),
            'prominencia': 0.5,
            'distancia': 10
        }
        response = self.client.post(
            reverse('sonif1D:buscar_picos'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('cantidad'), 2)
        self.assertEqual(len(data.get('picos_x')), 2)
        self.assertEqual(len(data.get('picos_y')), 2)

    def test_buscar_picos_invalid_distance_returns_400(self):
        """Verifica que distancia inválida (< 1) retorne 400 Bad Request."""
        sample_data = [[0.0, 1.0], [1.0, 5.0], [2.0, 1.0]]
        payload = {
            'data_json': json.dumps(sample_data),
            'prominencia': 0.5,
            'distancia': 0
        }
        response = self.client.post(
            reverse('sonif1D:buscar_picos'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class Sonif1DFileImportTests(TestCase):
    """Pruebas de caja negra sobre la importación y validación de archivos de usuario."""

    def setUp(self):
        self.client = Client()

    def test_import_view_get(self):
        """Verifica que la vista GET de importación cargue el formulario correctamente."""
        response = self.client.get(reverse('sonif1D:importar_archivo'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/import_archivo.html')

    def test_import_valid_csv(self):
        """Verifica la carga exitosa de un archivo CSV con dos columnas numéricas."""
        csv_content = b"0.0,1.5\n1.0,3.2\n2.0,5.8\n3.0,2.1\n"
        uploaded_file = SimpleUploadedFile("datos.csv", csv_content, content_type="text/csv")
        
        response = self.client.post(reverse('sonif1D:importar_archivo'), {'archivo': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/index.html')
        self.assertIn('data_json', response.context)
        self.assertIn('audio_base64', response.context)
        
        data = json.loads(response.context['data_json'])
        self.assertEqual(len(data), 4)
        Sonif1DBlackBoxTestHelper.assert_valid_wav_base64(self, response.context['audio_base64'])

    def test_import_valid_txt_space_delimited(self):
        """Verifica la carga de un archivo TXT delimitado por espacios/tabulaciones."""
        txt_content = b"0.0   10.0\n1.0   25.0\n2.0   15.0\n3.0   40.0\n"
        uploaded_file = SimpleUploadedFile("datos.txt", txt_content, content_type="text/plain")
        
        response = self.client.post(reverse('sonif1D:importar_archivo'), {'archivo': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/index.html')
        self.assertIn('data_json', response.context)
        self.assertIn('audio_base64', response.context)

    def test_import_subsampling_over_300_points(self):
        """Verifica que archivos con más de 300 puntos se reduzcan adecuadamente a 300 puntos."""
        rows = [f"{i * 0.1},{np.sin(i * 0.1)}" for i in range(500)]
        csv_content = "\n".join(rows).encode('utf-8')
        uploaded_file = SimpleUploadedFile("largo.csv", csv_content, content_type="text/csv")

        response = self.client.post(reverse('sonif1D:importar_archivo'), {'archivo': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/index.html')
        
        data = json.loads(response.context['data_json'])
        self.assertEqual(len(data), 300)
        Sonif1DBlackBoxTestHelper.assert_valid_wav_base64(self, response.context['audio_base64'])

    def test_import_unsupported_extension(self):
        """Verifica que se rechace un archivo con extensión no permitida (.png o .pdf)."""
        file_content = b"fake binary data"
        uploaded_file = SimpleUploadedFile("documento.pdf", file_content, content_type="application/pdf")

        response = self.client.post(reverse('sonif1D:importar_archivo'), {'archivo': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/import_archivo.html')

    def test_import_oversized_file(self):
        """Verifica que se rechace un archivo que exceda el tamaño máximo permitido (10MB)."""
        oversized_content = b"0.0,1.0\n" * ((10 * 1024 * 1024 // 8) + 100)
        uploaded_file = SimpleUploadedFile("gigante.csv", oversized_content, content_type="text/csv")

        response = self.client.post(reverse('sonif1D:importar_archivo'), {'archivo': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/import_archivo.html')

    def test_import_corrupt_non_numeric_file(self):
        """Verifica que un archivo con contenido no numérico sea rechazado elegantemente sin error 500."""
        csv_content = b"encabezado1,encabezado2\ntexto_invalido,otro_texto\nfoo,bar\n"
        uploaded_file = SimpleUploadedFile("corrupto.csv", csv_content, content_type="text/csv")

        response = self.client.post(reverse('sonif1D:importar_archivo'), {'archivo': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/import_archivo.html')

    def test_import_insufficient_rows(self):
        """Verifica que un archivo con menos de 2 filas de datos sea rechazado."""
        csv_content = b"1.0,2.0\n"
        uploaded_file = SimpleUploadedFile("una_fila.csv", csv_content, content_type="text/csv")

        response = self.client.post(reverse('sonif1D:importar_archivo'), {'archivo': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/import_archivo.html')


class Sonif1DErrorHandlingTests(TestCase):
    """Pruebas de caja negra sobre el manejo de errores, códigos HTTP y resiliencia."""

    def setUp(self):
        self.client = Client()
        self.ajax_endpoints = [
            'sonif1D:aplicar_filtro',
            'sonif1D:configurar_sonido',
            'sonif1D:aplicar_cuadratica',
            'sonif1D:aplicar_logaritmica',
            'sonif1D:buscar_picos'
        ]

    def test_ajax_get_method_returns_405(self):
        """Verifica que peticiones GET a endpoints AJAX exclusivos POST retornen 405 Method Not Allowed."""
        for ep in self.ajax_endpoints:
            response = self.client.get(reverse(ep))
            self.assertEqual(response.status_code, 405, f"Endpoint {ep} debió retornar 405 en GET")

    def test_ajax_empty_payload_returns_400(self):
        """Verifica que payloads vacíos retornen 400 Bad Request en todos los endpoints AJAX."""
        for ep in self.ajax_endpoints:
            response = self.client.post(
                reverse(ep),
                data=json.dumps({}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400, f"Endpoint {ep} debió retornar 400 con payload vacío")

    def test_ajax_invalid_json_data_returns_400(self):
        """Verifica que data_json con formato corrupto retorne 400 Bad Request."""
        for ep in self.ajax_endpoints:
            response = self.client.post(
                reverse(ep),
                data=json.dumps({'data_json': '{formato_invalido'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400, f"Endpoint {ep} debió retornar 400 con data_json corrupto")
