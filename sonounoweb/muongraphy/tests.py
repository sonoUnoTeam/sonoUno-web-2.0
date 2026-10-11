import os
from unittest import mock

import numpy as np
from django.test import SimpleTestCase
from django.urls import reverse
from scipy.io import wavfile

from utils.muongraphy_lib.muon_bash import (
    MAX_INT16_PEAK,
    OUTPUT_GAIN,
    cleanup_temp_audio,
    cleanup_temp_files,
    limit_amplitude,
    process_files,
    process_sound_array,
)
from utils.muongraphy_lib.sound_module import sonification as sd

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), 'sample_data', 'Muongraphy-1')


def dominant_frequencies(path, count):
    rate, data = wavfile.read(path)
    spectrum = np.abs(np.fft.rfft(data.astype(np.float64)))
    freqs = np.fft.rfftfreq(len(data), 1 / rate)
    return {round(f) for f in freqs[np.argsort(spectrum)[-count:]]}


class LimitAmplitudeTests(SimpleTestCase):
    def test_quiet_sound_is_unchanged(self):
        sound = sd.get_waveform('sine', 440, 0.1)
        np.testing.assert_allclose(limit_amplitude(sound), sound)

    def test_loud_chord_is_scaled_below_int16_range(self):
        # 20 notas superpuestas de amplitud 2000 superan 32767
        chord = sum(sd.get_waveform('sine', 220 + 10 * n, 0.1) for n in range(20))
        self.assertGreater(np.max(np.abs(chord)), np.iinfo(np.int16).max)

        limited = limit_amplitude(chord)
        self.assertAlmostEqual(np.max(np.abs(limited)), MAX_INT16_PEAK, places=3)

    def test_written_wav_does_not_wrap_around(self):
        chord = sum(sd.get_waveform('sine', 220 + 10 * n, 0.1) for n in range(20))
        path = process_sound_array(chord)
        try:
            _, data = wavfile.read(path)
            # Sin limitar, el desborde int16 invierte el signo de los picos
            peak_index = np.argmax(np.abs(chord))
            self.assertEqual(np.sign(data[peak_index]), np.sign(chord[peak_index]))
            self.assertLessEqual(np.max(np.abs(data.astype(np.int32))), MAX_INT16_PEAK)
        finally:
            cleanup_temp_audio([path])

    def test_output_gain_applies_to_written_wav(self):
        note = sd.get_waveform('sine', 440, 0.1)
        path = process_sound_array(note)
        try:
            _, data = wavfile.read(path)
            self.assertAlmostEqual(np.max(np.abs(data)) / np.max(np.abs(note)), OUTPUT_GAIN, places=2)
        finally:
            cleanup_temp_audio([path])

    def test_empty_sound(self):
        self.assertEqual(limit_amplitude([]).size, 0)


class ProcessFilesSyncTests(SimpleTestCase):
    def setUp(self):
        self.images, self.sounds, self.all_images = process_files(
            SAMPLE_DIR, 'Example_1.csv', 'csv', plot_flag=True
        )

    def tearDown(self):
        cleanup_temp_audio(set(self.sounds or []))
        cleanup_temp_files(self.all_images or [])

    def test_one_image_per_sound(self):
        self.assertEqual(len(self.images), 9)
        self.assertEqual(len(self.sounds), len(self.images))
        self.assertEqual(len(set(self.images)), len(self.images))
        self.assertTrue(set(self.images) <= set(self.all_images))

    def test_sound_order_follows_plot_order(self):
        bip = self.sounds[0]
        # Bip al inicio, entre la parte izquierda y la derecha, y al cierre
        self.assertEqual(self.sounds[4], bip)
        self.assertEqual(self.sounds[8], bip)

        notes = sd.get_piano_notes()
        expected = [
            (1, {'A3', 'B3'}),  # ax1 top_x
            (2, {'A4'}),        # ax3 mid_x
            (3, {'G5'}),        # ax5 bot_x
            (5, {'B4'}),        # ax2 top_y
            (6, {'C5', 'E5'}),  # ax4 mid_y
            (7, {'A5'}),        # ax6 bot_y
        ]
        for index, note_names in expected:
            freqs = dominant_frequencies(self.sounds[index], len(note_names))
            self.assertEqual(freqs, {round(notes[n]) for n in note_names}, f'clip {index}')

    def test_example_5_matches_original_desktop_recording(self):
        # Example_5 reconstruye el evento 5793328_1297611 desde una grabación de
        # la versión de escritorio; estas son las notas medidas en ese audio.
        images, sounds, all_images = process_files(SAMPLE_DIR, 'Example_5.csv', 'csv', plot_flag=True)
        try:
            notes = sd.get_piano_notes()
            expected = [
                (1, {'A3', 'B3', 'C4', 'F4'}),  # ax1 top_x
                (2, {'E5', 'F5'}),              # ax3 mid_x
                (3, {'E5', 'F5'}),              # ax5 bot_x
                (5, {'G5'}),                    # ax2 top_y
                (6, {'E5'}),                    # ax4 mid_y
                (7, {'A3', 'G5'}),              # ax6 bot_y
            ]
            for index, note_names in expected:
                freqs = dominant_frequencies(sounds[index], len(note_names))
                self.assertEqual(freqs, {round(notes[n]) for n in note_names}, f'clip {index}')
        finally:
            cleanup_temp_audio(set(sounds))
            cleanup_temp_files(all_images)

    def test_missing_file_returns_none(self):
        self.assertEqual(process_files(SAMPLE_DIR, 'no_existe.csv', 'csv', True), (None, None, None))


class MuongraphyViewTests(SimpleTestCase):
    def test_index_shows_example_picker_without_player(self):
        response = self.client.get(reverse('muongraphy:index'))
        html = response.content.decode('utf-8')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="videoPlayer"', html)
        self.assertIn('Elige un ejemplo', html)
        for number in range(1, 6):
            url = reverse('muongraphy:grafico', args=[f'Example_{number}.csv'])
            self.assertIn(f'href="{url}"', html)

    def test_grafico_renders_accessible_player_and_marks_current_example(self):
        response = self.client.get(reverse('muongraphy:grafico', args=['Example_1.csv']))
        html = response.content.decode('utf-8')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['video_base64'])
        self.assertIn('playsinline', html)
        self.assertIn('<label for="progressBar"', html)
        self.assertIn('<label for="volumeControl"', html)
        self.assertIn('aria-current="page">Ejemplo 1</a>', html)
        self.assertIn('Muongrafía · Ejemplo 1', html)

    def test_unknown_file_is_rejected_before_touching_the_filesystem(self):
        with mock.patch('muongraphy.views.process_files') as process:
            response = self.client.get(reverse('muongraphy:grafico', args=['no_existe.csv']))
        html = response.content.decode('utf-8')

        process.assert_not_called()
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('id="videoPlayer"', html)
        self.assertIn('El ejemplo solicitado no existe.', html)
        self.assertIn('Elige un ejemplo', html)

    def test_path_traversal_is_rejected(self):
        # El conversor <str:...> bloquea "/", pero no "\\", que en Windows separa rutas
        for name in ['..%5C..%5C..%5Cmanage.py', '..%5Csettings.py', 'Example_1.csv%5C..%5C..%5Cviews.py', '..']:
            with self.subTest(name=name), mock.patch('muongraphy.views.process_files') as process:
                response = self.client.get(f'/muongraphy/grafico/{name}/')
                self.assertEqual(response.status_code, 404)
                process.assert_not_called()

    def test_generation_error_is_not_shown_to_user_and_temp_files_are_cleaned(self):
        with (
            mock.patch('muongraphy.views.process_files', return_value=(['img.png'], ['snd.wav'], ['img.png', 'extra.png'])),
            mock.patch('muongraphy.views.create_video_from_paths', side_effect=RuntimeError('detalle interno de ruta secreta')),
            mock.patch('muongraphy.views.cleanup_temp_audio') as cleanup_audio,
            mock.patch('muongraphy.views.cleanup_temp_files') as cleanup_images,
            self.assertLogs('muongraphy.views', level='ERROR'),
        ):
            response = self.client.get(reverse('muongraphy:grafico', args=['Example_1.csv']))
        html = response.content.decode('utf-8')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('detalle interno', html)
        self.assertNotIn('secreta', html)
        self.assertIn('No se pudo crear el video.', html)
        cleanup_audio.assert_called_once_with(['snd.wav'])
        cleanup_images.assert_called_once_with(['img.png', 'extra.png'])
