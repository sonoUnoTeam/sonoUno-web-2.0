# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from .validators import (
    Sonif1DValidator,
    ALLOWED_WAVEFORMS,
    ALLOWED_LINE_STYLES,
    ALLOWED_LINE_COLORS,
    MIN_FREQ_LOWER_BOUND,
    MAX_FREQ_UPPER_BOUND,
    MIN_WINDOW_SIZE,
    MAX_WINDOW_SIZE,
    MIN_POLYNOMIAL_ORDER,
    MAX_POLYNOMIAL_ORDER,
    MIN_PROMINENCIA,
    MAX_PROMINENCIA,
    MIN_DISTANCIA,
    MAX_DISTANCIA,
)


# Formulario para la carga de un archivo
class ArchivoForm(forms.Form):
    archivo = forms.FileField(
        label='Selecciona un archivo',
        help_text='Formatos soportados: .csv o .txt (máximo 10MB)'
    )


# Formulario para la configuración visual del gráfico
class ConfiguracionGraficoForm(forms.Form):
    name_grafic = forms.CharField(
        label='Nombre de Gráfico',
        initial='Gráfico de Datos',
        max_length=100,
        required=False,
        help_text='Título que aparecerá en la parte superior del gráfico'
    )
    name_eje_x = forms.CharField(
        label='Nombre de Eje X',
        initial='Eje X',
        max_length=50,
        required=False,
        help_text='Etiqueta para el eje horizontal'
    )
    name_eje_y = forms.CharField(
        label='Nombre de Eje Y',
        initial='Eje Y',
        max_length=50,
        required=False,
        help_text='Etiqueta para el eje vertical'
    )
    estilo_linea = forms.ChoiceField(
        choices=[
            ('solid', 'Sólido ───'),
            ('dot', 'Punteado ···'),
            ('dash', 'Guion ──'),
            ('longdash', 'Guion Largo —'),
            ('dashdot', 'Guion Punto —·—'),
            ('longdashdot', 'Guion Largo Punto'),
        ],
        label='Estilo de línea',
        initial='solid'
    )
    color_linea = forms.ChoiceField(
        choices=[
            ('blue', 'Azul'),
            ('red', 'Rojo'),
            ('green', 'Verde'),
            ('purple', 'Púrpura'),
            ('orange', 'Naranja'),
            ('black', 'Negro'),
            ('yellow', 'Amarillo')
        ],
        label='Color de línea',
        initial='blue'
    )
    grilla = forms.BooleanField(
        required=False,
        label='Mostrar grilla',
        initial=True,
        help_text='Muestra líneas de cuadrícula en el gráfico'
    )
    escala_grises = forms.BooleanField(
        required=False,
        label='Escala de grises',
        initial=False,
        help_text='Convierte el gráfico a escala de grises'
    )

    def clean(self):
        cleaned_data = super().clean()
        try:
            return Sonif1DValidator.validate_visual_params(
                name_grafic=cleaned_data.get('name_grafic'),
                name_eje_x=cleaned_data.get('name_eje_x'),
                name_eje_y=cleaned_data.get('name_eje_y'),
                estilo_linea=cleaned_data.get('estilo_linea'),
                color_linea=cleaned_data.get('color_linea'),
                grilla=cleaned_data.get('grilla'),
                escala_grises=cleaned_data.get('escala_grises'),
            )
        except ValidationError as e:
            self.add_error(None, e)
            return cleaned_data


# Formulario para la configuración de sonido
class ConfiguracionSonidoForm(forms.Form):
    WAVEFORM_CHOICES = [
        ('sine', 'Seno Pura (Onda Pura)'),
        ('synthwave', 'Synthwave (Sintetizador)'),
        ('flute', 'Flauta'),
        ('piano', 'Piano'),
        ('celesta', 'Celesta'),
        ('pipe organ', 'Órgano de tubos'),
    ]

    instrumento = forms.ChoiceField(
        choices=WAVEFORM_CHOICES,
        label='Timbre / Instrumento',
        initial='sine'
    )
    min_freq = forms.FloatField(
        label='Frecuencia Mínima (Hz)',
        initial=500.0,
        min_value=MIN_FREQ_LOWER_BOUND,
        max_value=MAX_FREQ_UPPER_BOUND
    )
    max_freq = forms.FloatField(
        label='Frecuencia Máxima (Hz)',
        initial=5000.0,
        min_value=MIN_FREQ_LOWER_BOUND,
        max_value=MAX_FREQ_UPPER_BOUND
    )
    logscale = forms.BooleanField(
        required=False,
        label='Frecuencia Logarítmica',
        initial=False
    )

    def clean(self):
        cleaned_data = super().clean()
        try:
            validated = Sonif1DValidator.validate_sonido_params(
                waveform=cleaned_data.get('instrumento'),
                min_freq=cleaned_data.get('min_freq'),
                max_freq=cleaned_data.get('max_freq'),
                logscale=cleaned_data.get('logscale', False)
            )
            cleaned_data.update(validated)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, msgs in e.message_dict.items():
                    target_field = 'instrumento' if field == 'waveform' else field
                    self.add_error(target_field if target_field in self.fields else None, msgs)
            else:
                self.add_error(None, e)
        return cleaned_data


# Formulario para el filtro de suavizado Savitzky-Golay
class FiltroSuavizadoForm(forms.Form):
    window_size = forms.IntegerField(
        label='Tamaño de Ventana (impar)',
        initial=31,
        min_value=MIN_WINDOW_SIZE,
        max_value=MAX_WINDOW_SIZE,
        help_text='Debe ser un número impar mayor que el orden + 1'
    )
    order = forms.IntegerField(
        label='Orden del Polinomio',
        initial=4,
        min_value=MIN_POLYNOMIAL_ORDER,
        max_value=MAX_POLYNOMIAL_ORDER
    )

    def clean(self):
        cleaned_data = super().clean()
        try:
            validated = Sonif1DValidator.validate_filtro_params(
                window_size=cleaned_data.get('window_size'),
                order=cleaned_data.get('order')
            )
            cleaned_data.update(validated)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, msgs in e.message_dict.items():
                    self.add_error(field if field in self.fields else None, msgs)
            else:
                self.add_error(None, e)
        return cleaned_data


# Formulario para la transformación matemática cuadrática
class FuncionCuadraticaForm(forms.Form):
    coef_a = forms.FloatField(label='Coeficiente a (y²)', initial=1.0)
    coef_b = forms.FloatField(label='Coeficiente b (y)', initial=0.0)
    coef_c = forms.FloatField(label='Coeficiente c (cte)', initial=0.0)

    def clean(self):
        cleaned_data = super().clean()
        try:
            validated = Sonif1DValidator.validate_cuadratica_params(
                coef_a=cleaned_data.get('coef_a'),
                coef_b=cleaned_data.get('coef_b'),
                coef_c=cleaned_data.get('coef_c')
            )
            cleaned_data.update(validated)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, msgs in e.message_dict.items():
                    self.add_error(field if field in self.fields else None, msgs)
            else:
                self.add_error(None, e)
        return cleaned_data


# Formulario para la transformación matemática logarítmica
class FuncionLogaritmicaForm(forms.Form):
    log_a = forms.FloatField(label='Multiplicador a', initial=1.0)
    log_c = forms.FloatField(label='Desplazamiento c', initial=1.0)
    log_b = forms.FloatField(label='Constante b', initial=0.0)

    def clean(self):
        cleaned_data = super().clean()
        try:
            validated = Sonif1DValidator.validate_logaritmica_params(
                coef_a=cleaned_data.get('log_a'),
                coef_c=cleaned_data.get('log_c'),
                coef_b=cleaned_data.get('log_b')
            )
            cleaned_data.update({
                'log_a': validated.get('coef_a'),
                'log_c': validated.get('coef_c'),
                'log_b': validated.get('coef_b'),
            })
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, msgs in e.message_dict.items():
                    target_field = field.replace('coef_', 'log_')
                    self.add_error(target_field if target_field in self.fields else None, msgs)
            else:
                self.add_error(None, e)
        return cleaned_data


# Formulario para el buscador de picos
class BuscadorPicosForm(forms.Form):
    prominencia = forms.FloatField(
        label='Prominencia',
        initial=0.1,
        min_value=MIN_PROMINENCIA,
        max_value=MAX_PROMINENCIA
    )
    distancia = forms.IntegerField(
        label='Distancia Mínima',
        initial=5,
        min_value=MIN_DISTANCIA,
        max_value=MAX_DISTANCIA
    )

    def clean(self):
        cleaned_data = super().clean()
        try:
            validated = Sonif1DValidator.validate_picos_params(
                prominencia=cleaned_data.get('prominencia'),
                distancia=cleaned_data.get('distancia')
            )
            cleaned_data.update(validated)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, msgs in e.message_dict.items():
                    self.add_error(field if field in self.fields else None, msgs)
            else:
                self.add_error(None, e)
        return cleaned_data