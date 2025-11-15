/**
 * /**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    initializeForm();
    initializeRangeControls();
    initializeAccordionSteps();
    initializeVideoControls();
});

/**
 * Inicializar control de pasos del accordion
 */
function initializeAccordionSteps() {
    // Inicializar estados
    updateStepStatus(1, 'active', 'Selecciona una imagen');
    updateStepStatus(2, 'disabled', 'Bloqueado');
    updateStepStatus(3, 'disabled', 'Bloqueado');
    
    // Prevenir que se abran pasos bloqueados
    const accordionButtons = document.querySelectorAll('.accordion-button');
    accordionButtons.forEach((button, index) => {
        button.addEventListener('click', function(e) {
            const stepNumber = index + 1;
            const status = getStepStatus(stepNumber);
            
            if (status === 'disabled') {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        });
    });
}

/**
 * Actualizar estado de un paso
 */
function updateStepStatus(stepNumber, status, message) {
    const statusBadge = document.getElementById(`step${stepNumber}Status`);
    const accordionItem = document.querySelector(`#collapseStep${stepNumber}`).closest('.accordion-item');
    
    if (!statusBadge || !accordionItem) return;
    
    // Limpiar clases previas
    accordionItem.classList.remove('step-completed', 'step-active', 'step-disabled');
    statusBadge.classList.remove('bg-success', 'bg-warning', 'bg-secondary');
    
    // Aplicar nuevo estado
    switch(status) {
        case 'completed':
            accordionItem.classList.add('step-completed');
            statusBadge.classList.add('bg-success');
            statusBadge.textContent = '✓ Completado';
            break;
        case 'active':
            accordionItem.classList.add('step-active');
            statusBadge.classList.add('bg-warning');
            statusBadge.textContent = message || 'Activo';
            break;
        case 'disabled':
        default:
            accordionItem.classList.add('step-disabled');
            statusBadge.classList.add('bg-secondary');
            statusBadge.textContent = message || 'Bloqueado';
            break;
    }
}

/**
 * Obtener estado actual de un paso
 */
function getStepStatus(stepNumber) {
    const accordionItem = document.querySelector(`#collapseStep${stepNumber}`).closest('.accordion-item');
    
    if (accordionItem.classList.contains('step-completed')) return 'completed';
    if (accordionItem.classList.contains('step-active')) return 'active';
    return 'disabled';
}

/**
 * Avanzar al siguiente paso del accordion
 */
function goToNextStep(currentStep) {
    const nextStep = currentStep + 1;
    
    // Marcar paso actual como completado
    updateStepStatus(currentStep, 'completed');
    
    // Activar siguiente paso
    if (nextStep <= 3) {
        // Texto específico para cada paso
        const stepTexts = {
            2: 'En progreso',
            3: 'Completado' // Cambiado de "En progreso" a "Completado"
        };
        
        const statusText = stepTexts[nextStep] || 'En progreso';
        updateStepStatus(nextStep, 'active', statusText);
        
        // Cerrar paso actual primero
        const currentCollapse = new bootstrap.Collapse(document.getElementById(`collapseStep${currentStep}`), {
            hide: true
        });
        
        // Esperar un poco y luego abrir el siguiente paso
        setTimeout(() => {
            const nextCollapse = new bootstrap.Collapse(document.getElementById(`collapseStep${nextStep}`), {
                show: true
            });
        }, 300); // Pequeña pausa para mejor transición
    }
}

// === FUNCIONALIDAD PRINCIPAL ===

// Variables globales
let currentVideoData = null;
let currentAudioData = null;

/**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeUploadArea();
    initializeForm();
    initializeRangeControls();
});

/**
 * Inicializar área de subida con drag & drop
 */
function initializeUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('imageFile');
    
    if (!uploadArea || !fileInput) return;
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });
    
    // Click en área de subida
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Cambio de archivo
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFileSelect(this.files[0]);
        }
    });
}

/**
 * Inicializar formulario
 */
function initializeForm() {
    const form = document.getElementById('sonificationForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        processSonification();
    });
    
    // También añadir listener directo al botón (por si acaso)
    const processBtn = document.getElementById('processBtn');
    if (processBtn) {
        processBtn.addEventListener('click', function(e) {
            e.preventDefault();
            processSonification();
        });
    }
}

/**
 * Inicializar controles de rango
 */
function initializeRangeControls() {
    // Función mantenida para compatibilidad, pero ya no hay controles de rango en el paso 2
    // El volumen se maneja automáticamente en el backend
    console.log('Controles de rango: No hay controles de volumen en la interfaz simplificada');
}

/**
 * Manejar selección de archivo
 */
function handleFileSelect(file) {
    // Validar archivo de forma directa (como LHC)
    const allowedTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/tiff', 'image/webp'];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    if (!allowedTypes.includes(file.type)) {
        showError('Tipo de archivo no soportado. Use JPG, PNG, BMP, GIF, TIFF o WebP.');
        return;
    }
    
    if (file.size > maxSize) {
        showError('El archivo es demasiado grande. Máximo 50MB.');
        return;
    }
    
    // Mostrar preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('imagePreview');
        const img = document.getElementById('previewImg');
        const info = document.getElementById('imageInfo');
        
        if (!preview || !img || !info) return;
        
        img.src = e.target.result;
        img.onload = function() {
            const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
            info.innerHTML = `
                <span class="badge bg-primary me-2">
                    <i class="bi bi-arrows-fullscreen me-1"></i>
                    ${this.naturalWidth} × ${this.naturalHeight} píxeles
                </span>
                <span class="badge bg-info">
                    <i class="bi bi-file-earmark me-1"></i>
                    ${fileSizeMB} MB
                </span>
            `;
        };
        
        preview.style.display = 'block';
        
        // Habilitar botón de procesamiento
        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.disabled = false;
        }
        
        // Avanzar al paso 2 automáticamente
        setTimeout(() => {
            goToNextStep(1);
        }, 500); // Pequeña pausa para que el usuario vea la imagen cargada
    };
    reader.readAsDataURL(file);
}

/**
 * Limpiar mensajes previos
 */
function clearMessages() {
    const alertContainer = document.getElementById('alertContainer');
    if (alertContainer) {
        // Cerrar todas las alertas existentes
        const alerts = alertContainer.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }
}

/**
 * Mostrar mensaje de error (estilo LHC)
 */
function showError(message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertContainer = document.getElementById('alertContainer') || 
                          document.querySelector('.container-fluid') ||
                          document.body;
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = alertHtml;
    const alertElement = tempDiv.firstElementChild;
    alertContainer.insertBefore(alertElement, alertContainer.firstChild);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        if (alertElement && alertElement.parentNode) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Mostrar mensaje de éxito
 */
function showSuccess(message) {
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="fas fa-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertContainer = document.getElementById('alertContainer') || 
                          document.querySelector('.container-fluid') ||
                          document.body;
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = alertHtml;
    const alertElement = tempDiv.firstElementChild;
    alertContainer.insertBefore(alertElement, alertContainer.firstChild);
    
    // Auto-eliminar después de 4 segundos
    setTimeout(() => {
        if (alertElement && alertElement.parentNode) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 4000);
}

/**
 * Mostrar mensaje de descarga (estilo LHC)
 */
function showDownloadMessage(filename, type) {
    const message = `¡${type} "${filename}" descargado exitosamente!`;
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="fas fa-download me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertContainer = document.getElementById('alertContainer') || 
                          document.querySelector('.container-fluid') ||
                          document.body;
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = alertHtml;
    alertContainer.insertBefore(tempDiv.firstElementChild, alertContainer.firstChild);
    
    // Auto-eliminar después de 3 segundos
    setTimeout(() => {
        const alert = alertContainer.querySelector('.alert-success');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 3000);
}

/**
 * Procesar sonificación
 */
function processSonification() {
    console.log('=== INICIO PROCESAMIENTO ===');
    
    // Limpiar mensajes previos
    clearMessages();
    
    const fileInput = document.getElementById('imageFile');
    console.log('File input encontrado:', !!fileInput);
    console.log('Archivos en input:', fileInput?.files?.length || 0);
    
    if (!fileInput || !fileInput.files.length) {
        console.log('ERROR: No hay archivo seleccionado');
        showError('Por favor selecciona una imagen primero.');
        return;
    }
    
    console.log('Archivo seleccionado:', fileInput.files[0].name);
    
    // Preparar FormData
    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    
    // Añadir CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    console.log('CSRF token encontrado:', !!csrfToken);
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken.value);
    }
    
    // Añadir otros campos del formulario
    const formElements = document.getElementById('sonificationForm').elements;
    console.log('Elementos del formulario:', formElements.length);
    for (let element of formElements) {
        if (element.name && element.type !== 'file' && element.name !== 'csrfmiddlewaretoken') {
            console.log('Añadiendo campo:', element.name, '=', element.value);
            formData.append(element.name, element.value);
        }
    }
    
    // Mostrar progreso de forma directa (como LHC)
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.querySelector('#progressContainer .progress-bar');
    const progressText = document.getElementById('progressText');
    
    console.log('Elementos de progreso encontrados:', {
        container: !!progressContainer,
        bar: !!progressBar,
        text: !!progressText
    });
    
    if (progressContainer) {
        progressContainer.style.display = 'block';
        if (progressBar) progressBar.style.width = '0%';
        if (progressText) progressText.textContent = 'Procesando imagen...';
    }
    
    // Simular progreso
    const progressInterval = simulateProgress();
    
    console.log('Enviando petición a:', getProcessUrl());
    
    // Realizar petición
    fetch(getProcessUrl(), {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Respuesta recibida:', response.status, response.statusText);
        return response.json();
    })
    .then(data => {
        console.log('Datos procesados:', data);
        clearInterval(progressInterval);
        
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        
        if (data.success) {
            console.log('Procesamiento exitoso, mostrando resultados');
            showResults(data);
        } else {
            console.log('Error en el procesamiento:', data.error);
            showError(data.error || 'Error procesando la imagen');
        }
    })
    .catch(error => {
        console.error('Error en la petición:', error);
        clearInterval(progressInterval);
        
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        
        showError(`Error de red: ${error.message}`);
    });
}

/**
 * Simular progreso durante el procesamiento (estilo LHC)
 */
function simulateProgress() {
    let progress = 0;
    const progressBar = document.querySelector('#progressContainer .progress-bar');
    const progressText = document.getElementById('progressText');
    
    return setInterval(() => {
        progress += Math.random() * 10;
        if (progress > 90) progress = 90;
        
        let text = 'Procesando imagen...';
        if (progress > 30) text = 'Generando sonido...';
        if (progress > 60) text = 'Creando video...';
        if (progress > 80) text = 'Finalizando...';
        
        if (progressBar) {
            progressBar.style.width = progress + '%';
        }
        
        if (progressText) {
            progressText.textContent = text;
        }
    }, 500);
}

/**
 * Obtener URL de procesamiento (placeholder para template tag)
 */
function getProcessUrl() {
    // Esta función será reemplazada en el template con la URL real
    return window.imagesonifProcessUrl || '/imagesonif/process/';
}

/**
 * Mostrar resultados de la sonificación
 */
function showResults(data) {
    currentVideoData = data.video_base64;
    currentAudioData = data.audio_base64;
    
    // Configurar video
    setupVideo(data.video_base64);
    
    // Mostrar controles de video
    const videoControls = document.getElementById('videoControls');
    if (videoControls) {
        videoControls.style.display = 'block';
    }
    
    // Mostrar información
    displaySonificationInfo(data);
    
    // Avanzar al paso 3 automáticamente
    goToNextStep(2);
    
    // Después de un pequeño delay, marcar como completado exitosamente
    setTimeout(() => {
        updateStepStatus(3, 'completed', 'Finalizado');
    }, 100);
    
    // Scroll hacia el paso 3
    setTimeout(() => {
        const step3 = document.getElementById('collapseStep3');
        if (step3) {
            step3.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 500);
}

/**
 * Configurar video con audio
 */
function setupVideo(videoBase64) {
    const video = document.getElementById('sonificationVideo');
    if (!video || !videoBase64) return;
    
    video.src = `data:video/mp4;base64,${videoBase64}`;
    video.style.display = 'block';
    
    // Inicializar controles del video
    initializeVideoControls();
    
    // Event listeners para diagnóstico de audio
    video.addEventListener('loadedmetadata', function() {
        console.log('Video metadata cargada:');
        console.log('- Duración:', video.duration);
        console.log('- ¿Tiene audio?:', video.audioTracks ? video.audioTracks.length > 0 : 'No determinado');
        console.log('- Volume:', video.volume);
        console.log('- Muted:', video.muted);
    });
    
    video.addEventListener('loadeddata', function() {
        console.log('Video data cargada');
        // Asegurar que el volumen esté activado
        video.muted = false;
        video.volume = 1.0;
    });
}

/**
 * Mostrar información de la sonificación
 */
function displaySonificationInfo(data) {
    if (!data.sonification_info) return;
    
    const info = data.sonification_info;
    const settings = info.settings || {};
    
    const elements = {
        'infoDimensions': `${info.image_dimensions[0]} × ${info.image_dimensions[1]}`,
        'infoColumns': info.total_columns,
        'infoDuration': `${info.duration_seconds.toFixed(1)} segundos`,
        'infoProcessTime': `${data.processing_time} segundos`
    };
    
    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    const infoPanel = document.getElementById('sonificationInfo');
    if (infoPanel) {
        infoPanel.style.display = 'block';
    }
}

// === CONTROLES DE VIDEO (ESTILO LHC) ===

// Variables globales del reproductor
let previousVolume = 1.0;
let videoInitialized = false;

/**
 * Formatea el tiempo en formato MM:SS
 */
function formatTime(seconds) {
    if (!seconds || isNaN(seconds) || !isFinite(seconds)) {
        return '00:00';
    }
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    const formattedMinutes = minutes.toString().padStart(2, '0');
    const formattedSeconds = remainingSeconds.toString().padStart(2, '0');
    
    return `${formattedMinutes}:${formattedSeconds}`;
}

/**
 * Reproducir video
 */
function playVideo() {
    const video = document.getElementById('sonificationVideo');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    
    if (video) {
        video.play().then(() => {
            console.log('Video reproduciendo');
            if (playBtn) playBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'inline-block';
        }).catch(error => {
            console.error('Error al reproducir video:', error);
        });
    }
}

/**
 * Pausar video
 */
function pauseVideo() {
    const video = document.getElementById('sonificationVideo');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    
    if (video) {
        video.pause();
        console.log('Video pausado');
        if (pauseBtn) pauseBtn.style.display = 'none';
        if (playBtn) playBtn.style.display = 'inline-block';
    }
}

/**
 * Detener video
 */
function stopVideo() {
    const video = document.getElementById('sonificationVideo');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const progressBar = document.getElementById('progressBar');
    const currentTimeSpan = document.getElementById('currentTime');
    
    if (video) {
        video.pause();
        video.currentTime = 0;
        console.log('Video detenido');
        
        if (pauseBtn) pauseBtn.style.display = 'none';
        if (playBtn) playBtn.style.display = 'inline-block';
        if (progressBar) progressBar.value = 0;
        if (currentTimeSpan) currentTimeSpan.textContent = '00:00';
    }
}

/**
 * Reiniciar video
 */
function resetVideo() {
    const video = document.getElementById('sonificationVideo');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const progressBar = document.getElementById('progressBar');
    const currentTimeSpan = document.getElementById('currentTime');
    const volumeSlider = document.getElementById('volumeSlider');
    
    if (video) {
        video.pause();
        video.currentTime = 0;
        video.volume = 1.0;
        video.muted = false;
        previousVolume = 1.0;
        
        console.log('Video reseteado completamente');
        
        // Actualizar controles visuales
        if (pauseBtn) pauseBtn.style.display = 'none';
        if (playBtn) playBtn.style.display = 'inline-block';
        if (progressBar) progressBar.value = 0;
        if (currentTimeSpan) currentTimeSpan.textContent = '00:00';
        if (volumeSlider) volumeSlider.value = 100;
        
        // Actualizar displays de volumen
        updateVolumeDisplay(1.0);
        updateMuteIcon(1.0);
    }
}

/**
 * Control de volumen
 */
function changeVolume(value) {
    const video = document.getElementById('sonificationVideo');
    if (video) {
        const volume = value / 100;
        video.volume = volume;
        video.muted = volume === 0;
        updateVolumeDisplay(volume);
        updateMuteIcon(volume);
        
        if (volume > 0) {
            previousVolume = volume;
        }
    }
}

function increaseVolume() {
    const video = document.getElementById('sonificationVideo');
    const volumeSlider = document.getElementById('volumeSlider');
    
    if (video && volumeSlider) {
        const currentVolume = video.volume;
        const newVolume = Math.min(1.0, currentVolume + 0.1);
        video.volume = newVolume;
        video.muted = false;
        volumeSlider.value = newVolume * 100;
        updateVolumeDisplay(newVolume);
        updateMuteIcon(newVolume);
        
        if (newVolume > 0) {
            previousVolume = newVolume;
        }
        
        console.log('Volumen aumentado a:', Math.round(newVolume * 100) + '%');
    }
}

function decreaseVolume() {
    const video = document.getElementById('sonificationVideo');
    const volumeSlider = document.getElementById('volumeSlider');
    
    if (video && volumeSlider) {
        const currentVolume = video.volume;
        const newVolume = Math.max(0.0, currentVolume - 0.1);
        video.volume = newVolume;
        volumeSlider.value = newVolume * 100;
        updateVolumeDisplay(newVolume);
        updateMuteIcon(newVolume);
        
        if (newVolume === 0) {
            video.muted = true;
        } else {
            previousVolume = newVolume;
            video.muted = false;
        }
        
        console.log('Volumen disminuido a:', Math.round(newVolume * 100) + '%');
    }
}

function toggleMute() {
    const video = document.getElementById('sonificationVideo');
    const volumeSlider = document.getElementById('volumeSlider');
    
    if (video && volumeSlider) {
        if (video.muted) {
            // Desactivar mute
            video.muted = false;
            video.volume = previousVolume;
            volumeSlider.value = previousVolume * 100;
            updateVolumeDisplay(previousVolume);
            updateMuteIcon(previousVolume);
        } else {
            // Activar mute
            previousVolume = video.volume;
            video.muted = true;
            volumeSlider.value = 0;
            updateVolumeDisplay(0);
            updateMuteIcon(0);
        }
    }
}

function updateVolumeDisplay(volume) {
    const volumeDisplay = document.getElementById('volumeDisplay');
    if (volumeDisplay) {
        volumeDisplay.textContent = Math.round(volume * 100) + '%';
    }
}

function updateMuteIcon(volume) {
    const muteIcon = document.getElementById('muteIcon');
    if (muteIcon) {
        if (volume === 0) {
            muteIcon.className = 'bi bi-volume-mute';
        } else if (volume < 0.5) {
            muteIcon.className = 'bi bi-volume-down';
        } else {
            muteIcon.className = 'bi bi-volume-up';
        }
    }
}

/**
 * Actualización del progreso del video
 */
function updateProgress() {
    const video = document.getElementById('sonificationVideo');
    const progressBar = document.getElementById('progressBar');
    const currentTimeSpan = document.getElementById('currentTime');
    
    if (video && progressBar && currentTimeSpan) {
        if (!isNaN(video.currentTime) && isFinite(video.currentTime)) {
            progressBar.value = video.currentTime;
            currentTimeSpan.textContent = formatTime(video.currentTime);
        }
    }
}

/**
 * Cambiar velocidad de reproducción (mantenido)
 */
function changePlaybackSpeed() {
    const video = document.getElementById('sonificationVideo');
    const speedSelect = document.getElementById('playbackSpeed');
    
    if (video && speedSelect) {
        video.playbackRate = parseFloat(speedSelect.value);
    }
}

/**
 * Empezar de nuevo - Reset completo de la página
 */
function processNewImage() {
    // Mostrar confirmación antes del reset
    const confirmReset = confirm('¿Estás seguro de que quieres empezar de nuevo? Se perderán todos los datos actuales.');
    
    if (confirmReset) {
        // Recargar la página completamente para empezar desde el inicio
        window.location.reload();
    }
}

// === FUNCIONES DE DESCARGA ===

/**
 * Descargar video (patrón LHC)
 */
function downloadVideo() {
    if (!currentVideoData) {
        showDownloadMessage('No hay video disponible para descargar. Genere la sonificación primero.', 'warning');
        return;
    }
    
    // Crear enlace temporal para descargar
    const link = document.createElement('a');
    link.href = `data:video/mp4;base64,${currentVideoData}`;
    link.download = `imagesonif_video_${Date.now()}.mp4`;
    link.style.display = 'none';
    
    // Añadir al DOM, hacer click y remover
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Mostrar mensaje de confirmación
    showDownloadMessage('Video descargado exitosamente: ' + link.download);
}

/**
 * Descargar audio (patrón LHC)
 */
function downloadAudio() {
    if (!currentAudioData) {
        showDownloadMessage('No hay audio disponible para descargar. Genere la sonificación primero.', 'warning');
        return;
    }
    
    // Crear enlace temporal para descargar
    const link = document.createElement('a');
    link.href = `data:audio/wav;base64,${currentAudioData}`;
    link.download = `imagesonif_audio_${Date.now()}.wav`;
    link.style.display = 'none';
    
    // Añadir al DOM, hacer click y remover
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Mostrar mensaje de confirmación
    showDownloadMessage('Audio descargado exitosamente: ' + link.download);
}

/**
 * Mostrar mensaje de descarga (como en LHC)
 */
function showDownloadMessage(message, type = 'success') {
    // Crear o actualizar el mensaje de descarga
    let messageDiv = document.getElementById('downloadMessage');
    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.id = 'downloadMessage';
        messageDiv.style.position = 'fixed';
        messageDiv.style.top = '20px';
        messageDiv.style.right = '20px';
        messageDiv.style.zIndex = '9999';
        messageDiv.style.padding = '15px 20px';
        messageDiv.style.borderRadius = '5px';
        messageDiv.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        messageDiv.style.maxWidth = '400px';
        messageDiv.style.fontSize = '14px';
        messageDiv.style.fontWeight = 'bold';
        document.body.appendChild(messageDiv);
    }
    
    // Configurar estilos según el tipo
    if (type === 'success') {
        messageDiv.style.backgroundColor = '#d4edda';
        messageDiv.style.color = '#155724';
        messageDiv.style.border = '1px solid #c3e6cb';
        messageDiv.innerHTML = '<i class="bi bi-check-circle-fill"></i> ' + message;
    } else if (type === 'warning') {
        messageDiv.style.backgroundColor = '#fff3cd';
        messageDiv.style.color = '#856404';
        messageDiv.style.border = '1px solid #ffeaa7';
        messageDiv.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> ' + message;
    }
    
    // Mostrar el mensaje
    messageDiv.style.display = 'block';
    
    // Ocultar después de 5 segundos
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// === UTILIDADES ===

/**
 * Función de inicialización del video
 */
function initializeVideoControls() {
    const video = document.getElementById('sonificationVideo');
    const progressBar = document.getElementById('progressBar');
    const totalTimeSpan = document.getElementById('totalTime');
    const currentTimeSpan = document.getElementById('currentTime');
    const volumeSlider = document.getElementById('volumeSlider');
    
    // Añadir event listeners a botones de control con prevención de propagación
    const addButtonListener = (id, callback) => {
        const button = document.getElementById(id);
        if (button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                callback();
            });
        }
    };
    
    // Event listeners para controles de video
    addButtonListener('playBtn', playVideo);
    addButtonListener('pauseBtn', pauseVideo);
    addButtonListener('stopBtn', stopVideo);
    addButtonListener('resetBtn', resetVideo);
    addButtonListener('volumeUpBtn', increaseVolume);
    addButtonListener('volumeDownBtn', decreaseVolume);
    addButtonListener('muteBtn', toggleMute);
    addButtonListener('downloadVideoBtn', downloadVideo);
    addButtonListener('downloadAudioBtn', downloadAudio);
    addButtonListener('processNewImageBtn', processNewImage);
    
    // Event listener para selector de velocidad
    const speedSelect = document.getElementById('playbackSpeed');
    if (speedSelect) {
        speedSelect.addEventListener('change', function(e) {
            e.stopPropagation();
            changePlaybackSpeed();
        });
    }
    
    if (!video) return;
    
    // Event listeners del video
    video.addEventListener('loadedmetadata', function() {
        if (progressBar) {
            progressBar.max = video.duration;
        }
        if (totalTimeSpan) {
            totalTimeSpan.textContent = formatTime(video.duration);
        }
        console.log('Video metadata cargada, duración:', formatTime(video.duration));
    });
    
    video.addEventListener('timeupdate', updateProgress);
    
    video.addEventListener('ended', function() {
        const playBtn = document.getElementById('playBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        
        if (pauseBtn) pauseBtn.style.display = 'none';
        if (playBtn) playBtn.style.display = 'inline-block';
        console.log('Video terminado');
    });
    
    // Event listener para la barra de progreso
    if (progressBar) {
        progressBar.addEventListener('input', function(e) {
            e.stopPropagation();
            if (video) {
                video.currentTime = progressBar.value;
            }
        });
    }
    
    // Event listener para el slider de volumen
    if (volumeSlider) {
        volumeSlider.addEventListener('input', function(e) {
            e.stopPropagation();
            changeVolume(this.value);
        });
    }
    
    // Inicializar valores por defecto
    if (currentTimeSpan) currentTimeSpan.textContent = '00:00';
    updateVolumeDisplay(1.0);
    updateMuteIcon(1.0);
    
    videoInitialized = true;
    console.log('Controles de video inicializados con event listeners');
}

// Exportar solo las funciones que podrían necesitarse externamente
window.initializeVideoControls = initializeVideoControls;