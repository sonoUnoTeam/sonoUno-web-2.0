import json
import numpy as np
from django.test import TestCase, Client
from django.urls import reverse


class Sonif1DViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        """Verifica que la página principal index cargue con status 200 y las pestañas modulares."""
        response = self.client.get(reverse('sonif1D:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/index.html')
        self.assertTemplateUsed(response, 'sonif1D/base.html')
        self.assertContains(response, 'tab-guia-btn')
        self.assertContains(response, 'tab-grafico-btn')
        self.assertContains(response, 'tab-sonido-btn')
        self.assertContains(response, 'tab-matematicas-btn')
        self.assertContains(response, 'tab-marcadores-btn')

    def test_root_route_renders_index(self):
        """Verifica que la ruta raíz /sonif1D/ responda correctamente con el template index."""
        response = self.client.get('/sonif1D/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/index.html')

    def test_tab_matematicas_elements_rendered(self):
        """Verifica que la pestaña de Matemáticas incluya los controles de cuadrática, logarítmica y buscador de picos."""
        response = self.client.get(reverse('sonif1D:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'btnCuadraticaAjax')
        self.assertContains(response, 'btnLogaritmicaAjax')
        self.assertContains(response, 'btnPicosAjax')
        self.assertContains(response, 'coef_a')
        self.assertContains(response, 'log_a')
        self.assertContains(response, 'prominencia')

    def test_mostrar_grafico_sinusoidal(self):
        """Verifica que la vista mostrar_grafico cargue el archivo de ejemplo y prepare los datos."""
        response = self.client.get(reverse('sonif1D:mostrar_grafico', args=['sinusoidal.txt']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sonif1D/index.html')
        self.assertIn('audio_base64', response.context)
        self.assertIn('data_json', response.context)

    def test_configurar_sonido_ajax(self):
        """Verifica que el endpoint AJAX de sonido genere un nuevo audio en base64."""
        sample_data = [[0.0, 0.0], [0.1, 0.5], [0.2, 0.8], [0.3, 1.0], [0.4, 0.7], [0.5, 0.2]]
        payload = {
            'data_json': json.dumps(sample_data),
            'waveform': 'sine',
            'min_freq': 500,
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
        self.assertTrue(bool(data.get('audio_base64')))

    def test_aplicar_filtro_ajax(self):
        """Verifica que el endpoint AJAX de filtro aplique el suavizado correctamente."""
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
        self.assertTrue(bool(data.get('data_json')))
        self.assertTrue(bool(data.get('audio_base64')))

    def test_aplicar_cuadratica_ajax(self):
        """Verifica que la función cuadrática transforme los valores Y según y' = a*y^2 + b*y + c."""
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
        self.assertTrue(bool(data.get('audio_base64')))

        res_data = json.loads(data['data_json'])
        # y' = 2*(2^2) + 1*(2) + 3 = 8 + 2 + 3 = 13.0
        self.assertAlmostEqual(res_data[0][1], 13.0)
        # y' = 2*(3^2) + 1*(3) + 3 = 18 + 3 + 3 = 24.0
        self.assertAlmostEqual(res_data[1][1], 24.0)

    def test_aplicar_logaritmica_ajax(self):
        """Verifica que la función logarítmica transforme los datos con protección de dominio."""
        sample_data = [[0.0, 1.0], [1.0, 2.0], [2.0, -0.5]]
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
        self.assertTrue(bool(data.get('audio_base64')))
        self.assertTrue(bool(data.get('data_json')))

    def test_buscar_picos_ajax(self):
        """Verifica que el buscador de picos detecte correctamente los máximos locales."""
        # Creamos una curva con 2 picos claros en x=10 y x=30
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

    def test_ajax_sin_datos_retorna_400(self):
        """Verifica que los endpoints AJAX manejen adecuadamente payloads sin datos."""
        endpoints = [
            'sonif1D:aplicar_filtro',
            'sonif1D:configurar_sonido',
            'sonif1D:aplicar_cuadratica',
            'sonif1D:aplicar_logaritmica',
            'sonif1D:buscar_picos'
        ]
        for ep in endpoints:
            response = self.client.post(
                reverse(ep),
                data=json.dumps({}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)
