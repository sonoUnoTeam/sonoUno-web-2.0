/**
 * tab_matematicas.js - Transformaciones matemáticas y búsqueda de picos
 */

document.addEventListener('DOMContentLoaded', function() {
    // Parámetros de sonido guardados por tab_sonido.js, para conservar el instrumento al transformar
    function getSonidoParams() {
        return {
            waveform: sessionStorage.getItem('saved_wave') || 'sine',
            min_freq: parseFloat(sessionStorage.getItem('saved_min')) || 500,
            max_freq: parseFloat(sessionStorage.getItem('saved_max')) || 5000
        };
    }

    // ==========================================================
    // 1. GESTIÓN DE FUNCIÓN CUADRÁTICA (AJAX)
    // ==========================================================
    const btnCuadratica = document.getElementById('btnCuadraticaAjax');
    if (btnCuadratica) {
        btnCuadratica.addEventListener('click', function(event) {
            event.preventDefault();
            clearFormValidation('formCuadratica');

            const coefAInput = document.getElementById('coef_a');
            const coefBInput = document.getElementById('coef_b');
            const coefCInput = document.getElementById('coef_c');

            const coefA = coefAInput ? parseFloat(coefAInput.value) : 1;
            const coefB = coefBInput ? parseFloat(coefBInput.value) : 0;
            const coefC = coefCInput ? parseFloat(coefCInput.value) : 0;

            let hasError = false;
            let firstInvalid = null;

            [
                { input: coefAInput, val: coefA, id: 'val_msg_coef_a', name: 'a' },
                { input: coefBInput, val: coefB, id: 'val_msg_coef_b', name: 'b' },
                { input: coefCInput, val: coefC, id: 'val_msg_coef_c', name: 'c' }
            ].forEach(item => {
                if (item.input && (isNaN(item.val) || !isFinite(item.val) || Math.abs(item.val) > 1e6)) {
                    setFieldValidation(item.input, false, `El coeficiente ${item.name} debe ser un número real finito.`, item.id);
                    hasError = true;
                    if (!firstInvalid) firstInvalid = item.input;
                } else if (item.input) {
                    setFieldValidation(item.input, true);
                }
            });

            if (hasError) {
                if (firstInvalid) firstInvalid.focus();
                return;
            }

            const datosAEnviar = sessionStorage.getItem('data_json');
            if (!datosAEnviar) {
                alert('No hay datos cargados para transformar.');
                return;
            }

            const textoOriginal = btnCuadratica.innerHTML;
            btnCuadratica.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Calculando...';
            btnCuadratica.disabled = true;

            const endpoint = (window.sonoUnoUrls && window.sonoUnoUrls.aplicarCuadratica) || '/sonif1D/aplicar_cuadratica/';

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    data_json: datosAEnviar,
                    coef_a: coefA,
                    coef_b: coefB,
                    coef_c: coefC,
                    ...getSonidoParams()
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
                    showFeedback('cuadraticaFeedback', 'Función cuadrática aplicada con éxito');
                } else {
                    alert("Error al aplicar función cuadrática: " + (body.error || 'Error desconocido'));
                }
            })
            .catch(error => {
                console.error("Error AJAX cuadrática:", error);
                alert("Error de conexión al aplicar función cuadrática.");
            })
            .finally(() => {
                btnCuadratica.innerHTML = textoOriginal;
                btnCuadratica.disabled = false;
            });
        });
    }

    // ==========================================================
    // 2. GESTIÓN DE FUNCIÓN LOGARÍTMICA (AJAX)
    // ==========================================================
    const btnLogaritmica = document.getElementById('btnLogaritmicaAjax');
    if (btnLogaritmica) {
        btnLogaritmica.addEventListener('click', function(event) {
            event.preventDefault();
            clearFormValidation('formLogaritmica');

            const logAInput = document.getElementById('log_a');
            const logCInput = document.getElementById('log_c');
            const logBInput = document.getElementById('log_b');

            const logA = logAInput ? parseFloat(logAInput.value) : 1;
            const logC = logCInput ? parseFloat(logCInput.value) : 1;
            const logB = logBInput ? parseFloat(logBInput.value) : 0;

            let hasError = false;
            let firstInvalid = null;

            [
                { input: logAInput, val: logA, id: 'val_msg_log_a', name: 'a' },
                { input: logCInput, val: logC, id: 'val_msg_log_c', name: 'c' },
                { input: logBInput, val: logB, id: 'val_msg_log_b', name: 'b' }
            ].forEach(item => {
                if (item.input && (isNaN(item.val) || !isFinite(item.val) || Math.abs(item.val) > 1e6)) {
                    setFieldValidation(item.input, false, `El parámetro ${item.name} debe ser un número real finito.`, item.id);
                    hasError = true;
                    if (!firstInvalid) firstInvalid = item.input;
                } else if (item.input) {
                    setFieldValidation(item.input, true);
                }
            });

            if (hasError) {
                if (firstInvalid) firstInvalid.focus();
                return;
            }

            const datosAEnviar = sessionStorage.getItem('data_json');
            if (!datosAEnviar) {
                alert('No hay datos cargados para transformar.');
                return;
            }

            const textoOriginal = btnLogaritmica.innerHTML;
            btnLogaritmica.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Calculando...';
            btnLogaritmica.disabled = true;

            const endpoint = (window.sonoUnoUrls && window.sonoUnoUrls.aplicarLogaritmica) || '/sonif1D/aplicar_logaritmica/';

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    data_json: datosAEnviar,
                    coef_a: logA,
                    coef_c: logC,
                    coef_b: logB,
                    ...getSonidoParams()
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
                    showFeedback('logaritmicaFeedback', 'Función logarítmica aplicada con éxito');
                } else {
                    alert("Error al aplicar función logarítmica: " + (body.error || 'Error desconocido'));
                }
            })
            .catch(error => {
                console.error("Error AJAX logarítmica:", error);
                alert("Error de conexión al aplicar función logarítmica.");
            })
            .finally(() => {
                btnLogaritmica.innerHTML = textoOriginal;
                btnLogaritmica.disabled = false;
            });
        });
    }

    // ==========================================================
    // 3. GESTIÓN DEL BUSCADOR DE PICOS (AJAX)
    // ==========================================================
    const btnPicos = document.getElementById('btnPicosAjax');
    if (btnPicos) {
        btnPicos.addEventListener('click', function(event) {
            event.preventDefault();
            clearFormValidation('formPicos');

            const prominenciaInput = document.getElementById('prominencia');
            const distanciaInput = document.getElementById('distancia');

            const prominencia = prominenciaInput ? parseFloat(prominenciaInput.value) : 0.1;
            const distancia = distanciaInput ? parseInt(distanciaInput.value, 10) : 5;

            let hasError = false;
            let firstInvalid = null;

            if (isNaN(prominencia) || prominencia < 0.0001 || prominencia > 100000) {
                setFieldValidation(prominenciaInput, false, 'La prominencia debe ser un valor positivo (ej: 0.1).', 'val_msg_prominencia');
                hasError = true;
                if (!firstInvalid) firstInvalid = prominenciaInput;
            } else {
                setFieldValidation(prominenciaInput, true);
            }

            if (isNaN(distancia) || distancia < 1 || distancia > 10000) {
                setFieldValidation(distanciaInput, false, 'La distancia mínima debe ser un entero mayor o igual a 1.', 'val_msg_distancia');
                hasError = true;
                if (!firstInvalid) firstInvalid = distanciaInput;
            } else {
                setFieldValidation(distanciaInput, true);
            }

            if (hasError) {
                if (firstInvalid) firstInvalid.focus();
                return;
            }

            const datosAEnviar = sessionStorage.getItem('data_json');
            if (!datosAEnviar) {
                alert('No hay datos cargados para buscar picos.');
                return;
            }

            const textoOriginal = btnPicos.innerHTML;
            btnPicos.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Buscando...';
            btnPicos.disabled = true;

            const endpoint = (window.sonoUnoUrls && window.sonoUnoUrls.buscarPicos) || '/sonif1D/buscar_picos/';

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    data_json: datosAEnviar,
                    prominencia: prominencia,
                    distancia: distancia
                })
            })
            .then(response => {
                return response.json().then(data => ({ status: response.status, body: data }));
            })
            .then(({ status, body }) => {
                if (status === 200 && body.success) {
                    if (body.cantidad > 0) {
                        const picosData = {
                            x: body.picos_x,
                            y: body.picos_y,
                            cantidad: body.cantidad
                        };
                        if (window.sonoUno1D && typeof window.sonoUno1D.setPeaks === 'function') {
                            window.sonoUno1D.setPeaks(picosData);
                        }
                        const picosText = document.getElementById('picosFeedbackText');
                        if (picosText) picosText.textContent = `Se detectaron ${body.cantidad} pico(s) en la señal.`;
                        showFeedback('picosFeedback');
                    } else {
                        if (window.sonoUno1D && typeof window.sonoUno1D.clearPeaks === 'function') {
                            window.sonoUno1D.clearPeaks();
                        }
                        const picosText = document.getElementById('picosFeedbackText');
                        if (picosText) picosText.textContent = 'No se detectaron picos con los parámetros actuales.';
                        showFeedback('picosFeedback');
                    }
                } else {
                    alert("Error al buscar picos: " + (body.error || 'Error desconocido'));
                }
            })
            .catch(error => {
                console.error("Error AJAX picos:", error);
                alert("Error de conexión al buscar picos.");
            })
            .finally(() => {
                btnPicos.innerHTML = textoOriginal;
                btnPicos.disabled = false;
            });
        });
    }
});
