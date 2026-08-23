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
        # Creamos una señal sintética de más de 35 puntos para el filtro Savitzky-Golay con ventana 31
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
