/**
 * Muongrafía: controles del reproductor y aviso mientras se genera un ejemplo.
 */
(function () {
    'use strict';

    function formatTime(seconds) {
        if (!Number.isFinite(seconds) || seconds < 0) {
            seconds = 0;
        }
        const minutes = Math.floor(seconds / 60);
        const rest = Math.floor(seconds % 60);
        return minutes + ':' + String(rest).padStart(2, '0');
    }

    function setupPlayer() {
        const video = document.getElementById('videoPlayer');
        if (!video) {
            return;
        }

        const playPauseButton = document.getElementById('playPauseButton');
        const playPauseIcon = playPauseButton.querySelector('.bi');
        const playPauseText = playPauseButton.querySelector('.muon-button-text');
        const stopButton = document.getElementById('stopButton');
        const progressBar = document.getElementById('progressBar');
        const currentTimeLabel = document.getElementById('currentTime');
        const durationLabel = document.getElementById('duration');
        const volumeControl = document.getElementById('volumeControl');
        const muteButton = document.getElementById('muteButton');
        const muteIcon = muteButton.querySelector('.bi');

        function setPlayingState(playing) {
            playPauseIcon.classList.toggle('bi-play-fill', !playing);
            playPauseIcon.classList.toggle('bi-pause-fill', playing);
            playPauseText.textContent = playing ? 'Pausar' : 'Reproducir';
        }

        function updateProgress() {
            const current = video.currentTime;
            const duration = video.duration;
            progressBar.value = current;
            currentTimeLabel.textContent = formatTime(current);
            progressBar.setAttribute('aria-valuetext', formatTime(current) + ' de ' + formatTime(duration));
        }

        function updateVolumeState() {
            const silent = video.muted || video.volume === 0;
            muteIcon.classList.toggle('bi-volume-up-fill', !silent);
            muteIcon.classList.toggle('bi-volume-mute-fill', silent);
            muteButton.setAttribute('aria-pressed', String(video.muted));
            muteButton.setAttribute('aria-label', video.muted ? 'Activar sonido' : 'Silenciar');
            volumeControl.setAttribute('aria-valuetext', Math.round(video.volume * 100) + ' %');
        }

        video.addEventListener('loadedmetadata', function () {
            progressBar.max = video.duration;
            durationLabel.textContent = formatTime(video.duration);
            updateProgress();
        });
        video.addEventListener('timeupdate', updateProgress);
        video.addEventListener('play', function () { setPlayingState(true); });
        video.addEventListener('pause', function () { setPlayingState(false); });
        video.addEventListener('ended', function () { setPlayingState(false); });
        video.addEventListener('volumechange', updateVolumeState);

        playPauseButton.addEventListener('click', function () {
            if (video.paused || video.ended) {
                video.play().catch(function () {
                    setPlayingState(false);
                });
            } else {
                video.pause();
            }
        });

        stopButton.addEventListener('click', function () {
            video.pause();
            video.currentTime = 0;
        });

        progressBar.addEventListener('input', function () {
            video.currentTime = Number(progressBar.value);
            updateProgress();
        });

        volumeControl.addEventListener('input', function () {
            video.volume = Number(volumeControl.value);
            if (video.volume > 0 && video.muted) {
                video.muted = false;
            }
        });

        muteButton.addEventListener('click', function () {
            video.muted = !video.muted;
        });

        // Si el video ya cargó antes de registrar los listeners
        if (video.readyState >= 1) {
            progressBar.max = video.duration;
            durationLabel.textContent = formatTime(video.duration);
            updateProgress();
        }
        updateVolumeState();
    }

    function setupLoadingStatus() {
        const status = document.getElementById('muonStatus');
        if (!status) {
            return;
        }

        document.querySelectorAll('a[href*="/muongraphy/grafico/"]').forEach(function (link) {
            link.addEventListener('click', function (event) {
                // Abrir en otra pestaña no recarga esta página
                if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) {
                    return;
                }
                const spinner = document.createElement('span');
                spinner.className = 'spinner-border spinner-border-sm';
                spinner.setAttribute('aria-hidden', 'true');
                const text = document.createElement('span');
                text.textContent = 'Generando el video de ' + link.textContent.trim() + '. Puede tardar unos segundos…';
                status.replaceChildren(spinner, text);
            });
        });

        // Al volver con el botón Atrás la página puede restaurarse con el aviso visible
        window.addEventListener('pageshow', function () {
            status.replaceChildren();
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        setupPlayer();
        setupLoadingStatus();
    });
})();
