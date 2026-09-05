/**
 * tab_grafico.js - Configuración visual del gráfico Plotly en tiempo real
 */

document.addEventListener('DOMContentLoaded', function() {
    const inputNameGrafic = document.getElementById('cfg_name_grafic');
    const inputNameEjeX = document.getElementById('cfg_name_eje_x');
    const inputNameEjeY = document.getElementById('cfg_name_eje_y');
    const selectEstiloLinea = document.getElementById('cfg_estilo_linea');
    const selectColorLinea = document.getElementById('cfg_color_linea');
    const checkGrilla = document.getElementById('cfg_grilla');
    const checkEscalaGrises = document.getElementById('cfg_escala_grises');
    const btnAplicarVisual = document.getElementById('btnAplicarVisual');
    const btnRestablecerVisual = document.getElementById('btnRestablecerVisual');

    // Cargar valores iniciales desde localStorage
    function initVisualConfig() {
        const storedNameGrafic = localStorage.getItem('name_grafic') || 'Gráfico de Datos';
        const storedNameEjeX = localStorage.getItem('name_eje_x') || 'Eje X';
        const storedNameEjeY = localStorage.getItem('name_eje_y') || 'Eje Y';
        const storedEstiloLinea = localStorage.getItem('estilo_linea') || 'solid';
        const storedColorLinea = localStorage.getItem('color_linea') || 'blue';
        const storedGrilla = localStorage.getItem('grilla') === 'true' || localStorage.getItem('grilla') === 'True' || localStorage.getItem('grilla') === true;
        const storedEscalaGrises = localStorage.getItem('escala_grises') === 'true' || localStorage.getItem('escala_grises') === 'True' || localStorage.getItem('escala_grises') === true;

        if (inputNameGrafic) inputNameGrafic.value = storedNameGrafic;
        if (inputNameEjeX) inputNameEjeX.value = storedNameEjeX;
        if (inputNameEjeY) inputNameEjeY.value = storedNameEjeY;
        if (selectEstiloLinea) selectEstiloLinea.value = storedEstiloLinea;
        if (selectColorLinea) selectColorLinea.value = storedColorLinea;
        if (checkGrilla) checkGrilla.checked = storedGrilla;
        if (checkEscalaGrises) checkEscalaGrises.checked = storedEscalaGrises;
    }
    initVisualConfig();

    function aplicarCambiosVisuales() {
        if (!window.sonoUno1D) return;

        let hasError = false;
        const titleVal = inputNameGrafic ? inputNameGrafic.value.trim() : '';
        const ejeXVal = inputNameEjeX ? inputNameEjeX.value.trim() : '';
        const ejeYVal = inputNameEjeY ? inputNameEjeY.value.trim() : '';

        // Validaciones de longitud
        if (titleVal.length > 100) {
            setFieldValidation(inputNameGrafic, false, 'El título no puede exceder 100 caracteres.', 'val_msg_name_grafic');
            hasError = true;
        } else if (inputNameGrafic) {
            setFieldValidation(inputNameGrafic, true);
        }

        if (ejeXVal.length > 50) {
            setFieldValidation(inputNameEjeX, false, 'La etiqueta Eje X no puede exceder 50 caracteres.', 'val_msg_eje_x');
            hasError = true;
        } else if (inputNameEjeX) {
            setFieldValidation(inputNameEjeX, true);
        }

        if (ejeYVal.length > 50) {
            setFieldValidation(inputNameEjeY, false, 'La etiqueta Eje Y no puede exceder 50 caracteres.', 'val_msg_eje_y');
            hasError = true;
        } else if (inputNameEjeY) {
            setFieldValidation(inputNameEjeY, true);
        }

        if (hasError) return;

        const newCfg = {
            name_grafic: titleVal || 'Gráfico de Datos',
            name_eje_x: ejeXVal || 'Eje X',
            name_eje_y: ejeYVal || 'Eje Y',
            estilo_linea: selectEstiloLinea ? selectEstiloLinea.value : 'solid',
            color_linea: selectColorLinea ? selectColorLinea.value : 'blue',
            grilla: checkGrilla ? checkGrilla.checked : true,
            escala_grises: checkEscalaGrises ? checkEscalaGrises.checked : false
        };
        window.sonoUno1D.setConfig(newCfg);
        showFeedback('visualFeedback');
    }

    if (btnAplicarVisual) {
        btnAplicarVisual.addEventListener('click', aplicarCambiosVisuales);
    }

    if (btnRestablecerVisual) {
        btnRestablecerVisual.addEventListener('click', function() {
            clearFormValidation('formVisualConfig');
            if (inputNameGrafic) inputNameGrafic.value = 'Gráfico de Datos';
            if (inputNameEjeX) inputNameEjeX.value = 'Eje X';
            if (inputNameEjeY) inputNameEjeY.value = 'Eje Y';
            if (selectEstiloLinea) selectEstiloLinea.value = 'solid';
            if (selectColorLinea) selectColorLinea.value = 'blue';
            if (checkGrilla) checkGrilla.checked = true;
            if (checkEscalaGrises) checkEscalaGrises.checked = false;
            aplicarCambiosVisuales();
        });
    }
});
