/**
 * tab_sonido.js - Síntesis acústica y filtro de suavizado de señal
 */

document.addEventListener('DOMContentLoaded', function() {
    // ==========================================================
    // 1. GESTIÓN DE SÍNTESIS DE SONIDO (AJAX)
    // ==========================================================
    const btnSonido = document.getElementById('btnSonidoAjax');
    if (btnSonido) {
        btnSonido.addEventListener('click', function(event) {
            event.preventDefault();
            clearFormValidation('formSonidoConfig');

            const instrumentoInput = document.getElementById('instrumento');
            const minFreqInput = document.getElementById('min_freq');
            const maxFreqInput = document.getElementById('max_freq');
            const logscaleInput = document.getElementById('logscale');

            const instrumento = instrumentoInput ? instrumentoInput.value : 'sine';
            const minFreq = minFreqInput ? parseFloat(minFreqInput.value) : 500;
            const maxFreq = maxFreqInput ? parseFloat(maxFreqInput.value) : 5000;
            const logscale = logscaleInput ? logscaleInput.checked : false;

            // Validación en el cliente
            let hasError = false;
            let firstInvalid = null;

            if (isNaN(minFreq) || minFreq < 20 || minFreq > 20000) {
                setFieldValidation(minFreqInput, false, 'La frecuencia mínima debe estar entre 20 Hz y 20,000 Hz.', 'val_msg_min_freq');
                hasError = true;
                if (!firstInvalid) firstInvalid = minFreqInput;
            } else {
                setFieldValidation(minFreqInput, true);
            }

            if (isNaN(maxFreq) || maxFreq < 20 || maxFreq > 20000) {
                setFieldValidation(maxFreqInput, false, 'La frecuencia máxima debe estar entre 20 Hz y 20,000 Hz.', 'val_msg_max_freq');
                hasError = true;
                if (!firstInvalid) firstInvalid = maxFreqInput;
            } else {
                setFieldValidation(maxFreqInput, true);
            }

            if (!hasError && minFreq >= maxFreq) {
                setFieldValidation(minFreqInput, false, 'La frecuencia mínima debe ser estrictamente menor que la máxima.', 'val_msg_min_freq');
                setFieldValidation(maxFreqInput, false, 'La frecuencia máxima debe ser mayor que la mínima.', 'val_msg_max_freq');
                hasError = true;
                if (!firstInvalid) firstInvalid = minFreqInput;
            } else if (!hasError && (maxFreq - minFreq) < 10) {
                setFieldValidation(maxFreqInput, false, 'La diferencia entre frecuencias debe ser de al menos 10 Hz.', 'val_msg_max_freq');
                hasError = true;
                if (!firstInvalid) firstInvalid = maxFreqInput;
            }

            if (hasError) {
                if (firstInvalid) firstInvalid.focus();
                return;
            }

            const datosAEnviar = sessionStorage.getItem('data_json');
            if (!datosAEnviar) {
                alert('No hay datos cargados para sonorizar. Carga un ejemplo o importa un archivo.');
                return;
            }

            // Persistir parámetros de sonido para que otros módulos puedan utilizarlos
            sessionStorage.setItem('saved_wave', instrumento);
            sessionStorage.setItem('saved_min', String(minFreq));
            sessionStorage.setItem('saved_max', String(maxFreq));

            const textoOriginal = btnSonido.innerHTML;
            btnSonido.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Compilando...';
            btnSonido.disabled = true;

            const endpoint = (window.sonoUnoUrls && window.sonoUnoUrls.configurarSonido) || '/sonif1D/configurar_sonido/';

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    data_json: datosAEnviar,
                    waveform: instrumento,
                    min_freq: minFreq,
                    max_freq: maxFreq,
                    logscale: logscale
                })
            })
            .then(response => {
                return response.json().then(data => ({ status: response.status, body: data }));
            })
            .then(({ status, body }) => {
                if (status === 200 && body.success) {
                    window.audioDataActual = body.audio_base64;
                    const audioPlayer = document.getElementById('audioPlayer') || document.querySelector('audio');
                    if (audioPlayer) {
                        const audioSource = audioPlayer.querySelector('source');
                        if (audioSource) {
                            audioSource.src = "data:audio/wav;base64," + body.audio_base64;
                        } else {
                            audioPlayer.src = "data:audio/wav;base64," + body.audio_base64;
                        }
                        audioPlayer.load();
                    }
                    showFeedback('sonidoFeedback', 'Sonido sintetizado correctamente');
                } else {
                    const errMsg = body.error || 'Error desconocido al configurar sonido';
                    if (body.field_errors) {
                        if (body.field_errors.min_freq) setFieldValidation(minFreqInput, false, body.field_errors.min_freq[0] || body.field_errors.min_freq, 'val_msg_min_freq');
                        if (body.field_errors.max_freq) setFieldValidation(maxFreqInput, false, body.field_errors.max_freq[0] || body.field_errors.max_freq, 'val_msg_max_freq');
                        if (body.field_errors.waveform) setFieldValidation(instrumentoInput, false, body.field_errors.waveform[0] || body.field_errors.waveform, 'val_msg_instrumento');
                    }
                    alert("Error al compilar sonido: " + errMsg);
                }
            })
            .catch(error => {
                console.error("Error AJAX sonido:", error);
                alert("Error de conexión al compilar sonido.");
            })
            .finally(() => {
                btnSonido.innerHTML = textoOriginal;
                btnSonido.disabled = false;
            });
        });
    }

    // ==========================================================
    // 2. GESTIÓN DE SUAVIZADO MATEMÁTICO (AJAX)
    // ==========================================================
    const btnSuavizar = document.getElementById('btnSuavizarAjax');
    if (btnSuavizar) {
        btnSuavizar.addEventListener('click', function(event) {
            event.preventDefault();
            clearFormValidation('formSuavizadoConfig');

            const windowSizeInput = document.getElementById('window_size');
            const orderInput = document.getElementById('order');

            const windowSize = windowSizeInput ? parseInt(windowSizeInput.value, 10) : 31;
            const order = orderInput ? parseInt(orderInput.value, 10) : 4;

            // Validación en el cliente
            let hasError = false;
            let firstInvalid = null;

            if (isNaN(windowSize) || windowSize < 3 || windowSize > 1001) {
                setFieldValidation(windowSizeInput, false, 'El tamaño de ventana debe estar entre 3 y 1001.', 'val_msg_window_size');
                hasError = true;
                if (!firstInvalid) firstInvalid = windowSizeInput;
            } else if (windowSize % 2 === 0) {
                setFieldValidation(windowSizeInput, false, 'El tamaño de ventana debe ser un número impar (ej: 5, 11, 31).', 'val_msg_window_size');
                hasError = true;
                if (!firstInvalid) firstInvalid = windowSizeInput;
            } else {
                setFieldValidation(windowSizeInput, true);
            }

            if (isNaN(order) || order < 1 || order > 10) {
                setFieldValidation(orderInput, false, 'El orden del polinomio debe estar entre 1 y 10.', 'val_msg_order');
                hasError = true;
                if (!firstInvalid) firstInvalid = orderInput;
            } else {
                setFieldValidation(orderInput, true);
            }

            if (!hasError && windowSize < (order + 2)) {
                setFieldValidation(windowSizeInput, false, `La ventana (${windowSize}) debe ser al menos ${order + 2} para orden ${order}.`, 'val_msg_window_size');
                hasError = true;
                if (!firstInvalid) firstInvalid = windowSizeInput;
            }

            if (hasError) {
                if (firstInvalid) firstInvalid.focus();
                return;
            }

            const datosAEnviar = sessionStorage.getItem('data_json');
            if (!datosAEnviar) {
                alert('No hay datos cargados para suavizar.');
                return;
            }

            const textoOriginal = btnSuavizar.innerHTML;
            btnSuavizar.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Procesando...';
            btnSuavizar.disabled = true;

            const endpoint = (window.sonoUnoUrls && window.sonoUnoUrls.aplicarFiltro) || '/sonif1D/aplicar_filtro/';

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    data_json: datosAEnviar,
                    window_size: windowSize,
                    order: order
                })
            })
            .then(response => {
                return response.json().then(data => ({ status: response.status, body: data }));
            })
            .then(({ status, body }) => {
                if (status === 200 && body.success) {
                    sessionStorage.setItem('data_json', body.data_json);
                    window.audioDataActual = body.audio_base64;

                    const audioPlayer = document.getElementById('audioPlayer') || document.querySelector('audio');
                    if (audioPlayer) {
                        const audioSource = audioPlayer.querySelector('source');
                        if (audioSource) {
                            audioSource.src = "data:audio/wav;base64," + body.audio_base64;
                        } else {
                            audioPlayer.src = "data:audio/wav;base64," + body.audio_base64;
                        }
                        audioPlayer.load();
                    }

                    if (window.sonoUno1D) {
                        if (typeof window.sonoUno1D.clearPeaks === 'function') {
                            window.sonoUno1D.clearPeaks();
                        }
                        const parsedData = window.sonoUno1D.convertirData(body.data_json);
                        window.sonoUno1D.renderGraficoWithMarkers(parsedData);
                    }
                    showFeedback('matematicaFeedback', 'Señal filtrada correctamente');
                } else {
                    const errMsg = body.error || 'Error desconocido al aplicar filtro';
                    if (body.field_errors) {
                        if (body.field_errors.window_size) setFieldValidation(windowSizeInput, false, body.field_errors.window_size[0] || body.field_errors.window_size, 'val_msg_window_size');
                        if (body.field_errors.order) setFieldValidation(orderInput, false, body.field_errors.order[0] || body.field_errors.order, 'val_msg_order');
                    }
                    alert("Error al aplicar filtro: " + errMsg);
                }
            })
            .catch(error => {
                console.error("Error AJAX suavizado:", error);
                alert("Error de conexión al procesar filtro.");
            })
            .finally(() => {
                btnSuavizar.innerHTML = textoOriginal;
                btnSuavizar.disabled = false;
            });
        });
    }
});
