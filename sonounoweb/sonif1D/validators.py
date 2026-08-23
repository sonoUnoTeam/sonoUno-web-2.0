# -*- coding: utf-8 -*-
"""
Validadores de datos y parámetros para la aplicación sonif1D.
Valida y sanitiza entradas de audio, filtros matemáticos, transformaciones y configuración visual.
"""

import math
from typing import Any, Dict, Optional
from django.core.exceptions import ValidationError

# Constantes y listas blancas permitidas
ALLOWED_WAVEFORMS = ['sine', 'synthwave', 'flute', 'piano', 'celesta', 'pipe organ']
ALLOWED_LINE_STYLES = ['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot']
ALLOWED_LINE_COLORS = ['blue', 'red', 'green', 'purple', 'orange', 'black', 'yellow']

# Rangos de audio (Hz)
MIN_FREQ_LOWER_BOUND = 20.0
MAX_FREQ_UPPER_BOUND = 20000.0
MIN_FREQ_DEFAULT = 500.0
MAX_FREQ_DEFAULT = 5000.0
MIN_FREQ_DIFFERENCE = 10.0

# Rangos de filtro Savitzky-Golay
MIN_WINDOW_SIZE = 3
MAX_WINDOW_SIZE = 1001
MIN_POLYNOMIAL_ORDER = 1
MAX_POLYNOMIAL_ORDER = 10

# Rangos de buscador de picos
MIN_PROMINENCIA = 0.0001
MAX_PROMINENCIA = 100000.0
MIN_DISTANCIA = 1
MAX_DISTANCIA = 10000

# Límites de texto para gráficos
MAX_GRAFIC_NAME_LEN = 100
MAX_AXIS_NAME_LEN = 50


class Sonif1DValidator:
    """Validador centralizado para las operaciones y parámetros de sonif1D."""

    @staticmethod
    def validate_sonido_params(
        waveform: Any = 'sine',
        min_freq: Any = MIN_FREQ_DEFAULT,
        max_freq: Any = MAX_FREQ_DEFAULT,
        logscale: Any = False
    ) -> Dict[str, Any]:
        """
        Valida los parámetros de síntesis de sonido.

        Returns:
            Dict con 'waveform', 'min_freq', 'max_freq', 'logscale' tipados y validados.

        Raises:
            ValidationError: Si algún parámetro no cumple con los tipos o rangos permitidos.
        """
        errors = {}

        # 1. Validar waveform
        waveform_str = str(waveform).strip().lower() if waveform is not None else 'sine'
        if waveform_str not in ALLOWED_WAVEFORMS:
            errors['waveform'] = (
                f"Instrumento '{waveform_str}' no válido. "
                f"Opciones disponibles: {', '.join(ALLOWED_WAVEFORMS)}"
            )

        # 2. Validar min_freq
        try:
            min_f = float(min_freq)
            if math.isnan(min_f) or math.isinf(min_f):
                raise ValueError("Valor no finito")
            if min_f < MIN_FREQ_LOWER_BOUND or min_f > MAX_FREQ_UPPER_BOUND:
                errors['min_freq'] = (
                    f"La frecuencia mínima debe estar entre {int(MIN_FREQ_LOWER_BOUND)} Hz "
                    f"y {int(MAX_FREQ_UPPER_BOUND)} Hz."
                )
        except (ValueError, TypeError):
            errors['min_freq'] = "La frecuencia mínima debe ser un número válido."
            min_f = MIN_FREQ_DEFAULT

        # 3. Validar max_freq
        try:
            max_f = float(max_freq)
            if math.isnan(max_f) or math.isinf(max_f):
                raise ValueError("Valor no finito")
            if max_f < MIN_FREQ_LOWER_BOUND or max_f > MAX_FREQ_UPPER_BOUND:
                errors['max_freq'] = (
                    f"La frecuencia máxima debe estar entre {int(MIN_FREQ_LOWER_BOUND)} Hz "
                    f"y {int(MAX_FREQ_UPPER_BOUND)} Hz."
                )
        except (ValueError, TypeError):
            errors['max_freq'] = "La frecuencia máxima debe ser un número válido."
            max_f = MAX_FREQ_DEFAULT

        # 4. Validación cruzada min_freq vs max_freq
        if 'min_freq' not in errors and 'max_freq' not in errors:
            if min_f >= max_f:
                errors['min_freq'] = "La frecuencia mínima debe ser estrictamente menor que la frecuencia máxima."
            elif (max_f - min_f) < MIN_FREQ_DIFFERENCE:
                errors['max_freq'] = (
                    f"La diferencia entre frecuencia mínima y máxima debe ser de al menos {int(MIN_FREQ_DIFFERENCE)} Hz."
                )

        # 5. Validar logscale
        logscale_bool = bool(logscale) if not isinstance(logscale, str) else logscale.lower() in ('true', '1', 'yes')

        if errors:
            raise ValidationError(errors)

        return {
            'waveform': waveform_str,
            'min_freq': min_f,
            'max_freq': max_f,
            'logscale': logscale_bool
        }

    @staticmethod
    def validate_filtro_params(
        window_size: Any = 31,
        order: Any = 4,
        data_len: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Valida los parámetros para el filtro de suavizado Savitzky-Golay.

        Returns:
            Dict con 'window_size' y 'order' enteros validados.

        Raises:
            ValidationError: Si la ventana o el orden no son válidos o son incompatibles.
        """
        errors = {}

        # 1. Validar window_size
        try:
            w_size = int(window_size)
            if w_size < MIN_WINDOW_SIZE:
                errors['window_size'] = f"El tamaño de ventana debe ser al menos {MIN_WINDOW_SIZE}."
            elif w_size > MAX_WINDOW_SIZE:
                errors['window_size'] = f"El tamaño de ventana no puede exceder {MAX_WINDOW_SIZE}."
            elif w_size % 2 == 0:
                errors['window_size'] = "El tamaño de ventana debe ser un número impar (ej: 5, 11, 31, 51)."
            elif data_len is not None and w_size > data_len:
                errors['window_size'] = (
                    f"El tamaño de ventana ({w_size}) no puede ser mayor que el total de puntos de datos ({data_len})."
                )
        except (ValueError, TypeError):
            errors['window_size'] = "El tamaño de ventana debe ser un número entero."
            w_size = 31

        # 2. Validar order
        try:
            p_order = int(order)
            if p_order < MIN_POLYNOMIAL_ORDER:
                errors['order'] = f"El orden del polinomio debe ser al menos {MIN_POLYNOMIAL_ORDER}."
            elif p_order > MAX_POLYNOMIAL_ORDER:
                errors['order'] = f"El orden del polinomio no debe superar {MAX_POLYNOMIAL_ORDER}."
        except (ValueError, TypeError):
            errors['order'] = "El orden del polinomio debe ser un número entero."
            p_order = 4

        # 3. Validación cruzada: window_size >= order + 2
        if 'window_size' not in errors and 'order' not in errors:
            if w_size < (p_order + 2):
                errors['window_size'] = (
                    f"El tamaño de ventana ({w_size}) debe ser al menos {p_order + 2} "
                    f"para un polinomio de orden {p_order} (debe cumplir: ventana >= orden + 2)."
                )

        if errors:
            raise ValidationError(errors)

        return {
            'window_size': w_size,
            'order': p_order
        }

    @staticmethod
    def validate_cuadratica_params(
        coef_a: Any = 1.0,
        coef_b: Any = 0.0,
        coef_c: Any = 0.0
    ) -> Dict[str, float]:
        """
        Valida los coeficientes para la función cuadrática: y' = a*y^2 + b*y + c.

        Returns:
            Dict con 'coef_a', 'coef_b', 'coef_c' de tipo float.
        """
        errors = {}
        cleaned = {}

        for name, val in [('coef_a', coef_a), ('coef_b', coef_b), ('coef_c', coef_c)]:
            try:
                f_val = float(val)
                if math.isnan(f_val) or math.isinf(f_val):
                    errors[name] = f"El coeficiente {name} debe ser un número finito."
                elif abs(f_val) > 1e6:
                    errors[name] = f"El coeficiente {name} excede el rango numérico permitido (±1,000,000)."
                else:
                    cleaned[name] = f_val
            except (ValueError, TypeError):
                errors[name] = f"El coeficiente {name} debe ser un número real válido."

        if errors:
            raise ValidationError(errors)

        return cleaned

    @staticmethod
    def validate_logaritmica_params(
        coef_a: Any = 1.0,
        coef_c: Any = 1.0,
        coef_b: Any = 0.0
    ) -> Dict[str, float]:
        """
        Valida los coeficientes para la función logarítmica: y' = a*ln(y + c) + b.

        Returns:
            Dict con 'coef_a', 'coef_c', 'coef_b' de tipo float.
        """
        errors = {}
        cleaned = {}

        for name, val in [('coef_a', coef_a), ('coef_c', coef_c), ('coef_b', coef_b)]:
            try:
                f_val = float(val)
                if math.isnan(f_val) or math.isinf(f_val):
                    errors[name] = f"El parámetro {name} debe ser un número finito."
                elif abs(f_val) > 1e6:
                    errors[name] = f"El parámetro {name} excede el rango numérico permitido (±1,000,000)."
                else:
                    cleaned[name] = f_val
            except (ValueError, TypeError):
                errors[name] = f"El parámetro {name} debe ser un número real válido."

        if errors:
            raise ValidationError(errors)

        return cleaned

    @staticmethod
    def validate_picos_params(
        prominencia: Any = 0.1,
        distancia: Any = 5
    ) -> Dict[str, Any]:
        """
        Valida los parámetros para la detección de picos (peak finding).

        Returns:
            Dict con 'prominencia' (float) y 'distancia' (int).
        """
        errors = {}

        try:
            p_val = float(prominencia)
            if math.isnan(p_val) or math.isinf(p_val):
                errors['prominencia'] = "La prominencia debe ser un número finito."
            elif p_val < MIN_PROMINENCIA:
                errors['prominencia'] = f"La prominencia debe ser mayor o igual a {MIN_PROMINENCIA}."
            elif p_val > MAX_PROMINENCIA:
                errors['prominencia'] = f"La prominencia no puede superar {MAX_PROMINENCIA}."
        except (ValueError, TypeError):
            errors['prominencia'] = "La prominencia debe ser un número decimal válido."
            p_val = 0.1

        try:
            d_val = int(distancia)
            if d_val < MIN_DISTANCIA:
                errors['distancia'] = f"La distancia mínima entre picos debe ser de al menos {MIN_DISTANCIA}."
            elif d_val > MAX_DISTANCIA:
                errors['distancia'] = f"La distancia no puede superar {MAX_DISTANCIA}."
        except (ValueError, TypeError):
            errors['distancia'] = "La distancia debe ser un número entero válido."
            d_val = 5

        if errors:
            raise ValidationError(errors)

        return {
            'prominencia': p_val,
            'distancia': d_val
        }

    @staticmethod
    def validate_visual_params(
        name_grafic: Any = 'Gráfico de Datos',
        name_eje_x: Any = 'Eje X',
        name_eje_y: Any = 'Eje Y',
        estilo_linea: Any = 'solid',
        color_linea: Any = 'blue',
        grilla: Any = True,
        escala_grises: Any = False
    ) -> Dict[str, Any]:
        """
        Valida los parámetros de visualización y estilo del gráfico Plotly.
        """
        errors = {}

        # Sanitizar títulos
        title = str(name_grafic).strip() if name_grafic is not None else 'Gráfico de Datos'
        if len(title) > MAX_GRAFIC_NAME_LEN:
            errors['name_grafic'] = f"El título del gráfico no puede exceder {MAX_GRAFIC_NAME_LEN} caracteres."

        x_label = str(name_eje_x).strip() if name_eje_x is not None else 'Eje X'
        if len(x_label) > MAX_AXIS_NAME_LEN:
            errors['name_eje_x'] = f"La etiqueta del Eje X no puede exceder {MAX_AXIS_NAME_LEN} caracteres."

        y_label = str(name_eje_y).strip() if name_eje_y is not None else 'Eje Y'
        if len(y_label) > MAX_AXIS_NAME_LEN:
            errors['name_eje_y'] = f"La etiqueta del Eje Y no puede exceder {MAX_AXIS_NAME_LEN} caracteres."

        # Estilo de línea
        style = str(estilo_linea).strip().lower() if estilo_linea is not None else 'solid'
        if style not in ALLOWED_LINE_STYLES:
            errors['estilo_linea'] = f"Estilo de línea '{style}' no válido. Opciones: {', '.join(ALLOWED_LINE_STYLES)}"

        # Color de línea
        color = str(color_linea).strip().lower() if color_linea is not None else 'blue'
        if color not in ALLOWED_LINE_COLORS:
            errors['color_linea'] = f"Color de línea '{color}' no válido. Opciones: {', '.join(ALLOWED_LINE_COLORS)}"

        # Booleans
        grid = bool(grilla) if not isinstance(grilla, str) else grilla.lower() in ('true', '1', 'yes')
        grayscale = bool(escala_grises) if not isinstance(escala_grises, str) else escala_grises.lower() in ('true', '1', 'yes')

        if errors:
            raise ValidationError(errors)

        return {
            'name_grafic': title or 'Gráfico de Datos',
            'name_eje_x': x_label or 'Eje X',
            'name_eje_y': y_label or 'Eje Y',
            'estilo_linea': style,
            'color_linea': color,
            'grilla': grid,
            'escala_grises': grayscale
        }
