/**
 * tab_navigation.js - Navegación entre pestañas y utilidades de feedback/validación
 */

// Helper para obtener el token CSRF desde las cookies o variable global
function getCsrfToken() {
    if (window.csrfToken) return window.csrfToken;
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue || '';
}

// Helper para mostrar feedback temporal
function showFeedback(elementId, text) {
    const fb = document.getElementById(elementId);
    if (fb) {
        if (text) {
            const textElem = fb.querySelector('span');
            if (textElem) textElem.textContent = text;
        }
        fb.style.display = 'block';
        setTimeout(() => { fb.style.display = 'none'; }, 4000);
    }
}

// Sistema de validación reactiva en tiempo real
function setFieldValidation(inputElem, isValid, message, feedbackElemId) {
    if (!inputElem) return;
    if (isValid) {
        inputElem.classList.remove('is-invalid');
        inputElem.classList.add('is-valid');
    } else {
        inputElem.classList.remove('is-valid');
        inputElem.classList.add('is-invalid');
        if (feedbackElemId) {
            const fb = document.getElementById(feedbackElemId);
            if (fb && message) fb.textContent = message;
        }
    }
}

function clearFieldValidation(inputElem) {
    if (!inputElem) return;
    inputElem.classList.remove('is-invalid', 'is-valid');
}

function clearFormValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.querySelectorAll('.is-invalid, .is-valid').forEach(el => {
        el.classList.remove('is-invalid', 'is-valid');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Sincronización robusta de tabs y paneles exclusivos
    const allTabBtns = [
        document.getElementById('tab-guia-btn'),
        document.getElementById('tab-grafico-btn'),
        document.getElementById('tab-sonido-btn'),
        document.getElementById('tab-matematicas-btn'),
        document.getElementById('tab-marcadores-btn')
    ].filter(Boolean);

    const allTabPanes = [
        document.getElementById('tab-guia-pane'),
        document.getElementById('tab-grafico-pane'),
        document.getElementById('tab-sonido-pane'),
        document.getElementById('tab-matematicas-pane'),
        document.getElementById('tab-marcadores-pane')
    ].filter(Boolean);

    function activateTab(btn) {
        if (!btn) return;
        const targetSelector = btn.getAttribute('data-bs-target');
        const targetPane = document.querySelector(targetSelector);

        // Desactivar todos los botones
        allTabBtns.forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });

        // Ocultar todos los paneles
        allTabPanes.forEach(p => {
            p.classList.remove('show', 'active');
        });

        // Activar únicamente el botón y panel seleccionados
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        if (targetPane) {
            targetPane.classList.add('show', 'active');
        }
    }

    allTabBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            activateTab(this);
        });
    });

    // Limpiar estados de validación cuando el usuario escribe o cambia un valor
    ['formVisualConfig', 'formSonidoConfig', 'formSuavizadoConfig', 'formCuadratica', 'formLogaritmica', 'formPicos'].forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('input', function(e) {
                clearFieldValidation(e.target);
            });
            form.addEventListener('change', function(e) {
                clearFieldValidation(e.target);
            });
        }
    });
});
