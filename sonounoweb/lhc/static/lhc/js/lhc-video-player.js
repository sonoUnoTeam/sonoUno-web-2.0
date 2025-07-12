/**
 * LHC Video Player - Controles para reproducción de videos LHC
 * Separado del template para mejorar la mantenibilidad
 */

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
 * Inicializa los controles del video
 */
function initializeVideo() {
    if (videoInitialized) return;
    videoInitialized = true;
    
    console.log('Inicializando controles de video...');
    
    const loader = document.getElementById('videoLoader');
    const video = document.getElementById('lhcVideo');
    const controls = document.getElementById('videoControls');
    const totalTimeSpan = document.getElementById('totalTime');
    const totalTimeLabel = document.getElementById('totalTimeLabel');
    const progressBar = document.getElementById('progressBar');
    
    if (loader) loader.style.display = 'none';
    if (video) video.style.display = 'block';
    if (controls) controls.style.display = 'block';
    
    // Configurar duración si está disponible
    if (video && video.duration && !isNaN(video.duration) && isFinite(video.duration)) {
        const formattedDuration = formatTime(video.duration);
        if (totalTimeSpan) {
            totalTimeSpan.textContent = formattedDuration;
        }
        if (totalTimeLabel) {
            totalTimeLabel.textContent = formattedDuration;
        }
        if (progressBar) {
            progressBar.max = video.duration;
        }
    }
    
    // Inicializar volumen
    if (video) {
        video.volume = 1.0;
        updateVolumeDisplay(1.0);
        updateMuteIcon(1.0);
    }
}

/**
 * Verifica si el video está listo para reproducir
 */
function checkVideoReady() {
    const video = document.getElementById('lhcVideo');
    if (video && video.readyState >= 1) { // HAVE_METADATA
        initializeVideo();
    } else {
        // Intentar de nuevo en un momento
        setTimeout(checkVideoReady, 100);
    }
}

/**
 * Controles de reproducción
 */
function playVideo() {
    const video = document.getElementById('lhcVideo');
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

function pauseVideo() {
    const video = document.getElementById('lhcVideo');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    
    if (video) {
        video.pause();
        console.log('Video pausado');
        if (pauseBtn) pauseBtn.style.display = 'none';
        if (playBtn) playBtn.style.display = 'inline-block';
    }
}

function stopVideo() {
    const video = document.getElementById('lhcVideo');
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

function rewindVideo() {
    const video = document.getElementById('lhcVideo');
    if (video) {
        video.currentTime = Math.max(0, video.currentTime - 5);
        console.log('Video rebobinado 5 segundos');
    }
}

function forwardVideo() {
    const video = document.getElementById('lhcVideo');
    if (video) {
        video.currentTime = Math.min(video.duration, video.currentTime + 5);
        console.log('Video adelantado 5 segundos');
    }
}

function resetVideo() {
    const video = document.getElementById('lhcVideo');
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
    const video = document.getElementById('lhcVideo');
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
    const video = document.getElementById('lhcVideo');
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
    const video = document.getElementById('lhcVideo');
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
    const video = document.getElementById('lhcVideo');
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
 * Control de progreso
 */
function seekVideo(event) {
    const video = document.getElementById('lhcVideo');
    const progressBar = event.target;
    
    if (video && progressBar) {
        const clickX = event.offsetX;
        const progressBarWidth = progressBar.offsetWidth;
        const newTime = (clickX / progressBarWidth) * video.duration;
        
        if (!isNaN(newTime) && isFinite(newTime)) {
            video.currentTime = newTime;
            console.log('Video saltó a:', formatTime(newTime));
        }
    }
}

/**
 * Actualización del progreso del video
 */
function updateProgress() {
    const video = document.getElementById('lhcVideo');
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
 * Inicialización del reproductor
 */
function initializeVideoPlayer() {
    const video = document.getElementById('lhcVideo');
    const loader = document.getElementById('videoLoader');
    
    if (!video) {
        console.log('No hay elemento video en esta página');
        return;
    }
    
    console.log('Inicializando reproductor de video LHC...');
    
    // Mostrar loader inicial
    if (loader) loader.style.display = 'block';
    
    // Múltiples eventos para asegurar que se inicialice
    video.addEventListener('loadeddata', initializeVideo);
    video.addEventListener('loadedmetadata', initializeVideo);
    video.addEventListener('canplay', initializeVideo);
    
    // Evento para actualizar el progreso
    video.addEventListener('timeupdate', updateProgress);
    
    // Evento cuando el video termina
    video.addEventListener('ended', function() {
        const playBtn = document.getElementById('playBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        
        if (pauseBtn) pauseBtn.style.display = 'none';
        if (playBtn) playBtn.style.display = 'inline-block';
        
        console.log('Video terminado');
    });
    
    // Configurar el slider de progreso para que sea clickeable
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.addEventListener('click', seekVideo);
        progressBar.addEventListener('input', function(e) {
            const video = document.getElementById('lhcVideo');
            if (video && !isNaN(e.target.value) && isFinite(e.target.value)) {
                video.currentTime = e.target.value;
                console.log('Progreso cambiado a:', formatTime(e.target.value));
            }
        });
    }
    
    // Configurar el slider de volumen
    const volumeSlider = document.getElementById('volumeSlider');
    if (volumeSlider) {
        volumeSlider.addEventListener('input', function(e) {
            changeVolume(e.target.value);
        });
        
        // Inicializar volumen al 100%
        volumeSlider.value = 100;
    }
    
    // Inicializar display de volumen
    updateVolumeDisplay(1.0);
    updateMuteIcon(1.0);
    
    // Verificar si el video ya está listo
    checkVideoReady();
    
    console.log('Event listeners configurados correctamente');
}

/**
 * Mostrar loader cuando se navega a nuevo evento
 */
function setupNavigationLoaders() {
    document.addEventListener('click', function(e) {
        if (e.target.matches('a[href*="?event="]')) {
            const loader = document.getElementById('videoLoader');
            if (loader) {
                loader.style.display = 'block';
            }
        }
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeVideoPlayer();
    setupNavigationLoaders();
});
