/**
 * LHC Download Functions - Funciones para descargar imagen y audio
 * Separado del template para mejorar la mantenibilidad
 */

// Variables globales para los datos de descarga
let downloadData = {
    image: {
        base64: null,
        fileName: "LHC_Evento_X.png"
    },
    audio: {
        base64: null,
        fileName: "LHC_Evento_X.wav"
    }
};

/**
 * Configura los datos de descarga desde el template
 */
function setDownloadData(imageBase64, audioBase64, eventNumber, fileName) {
    downloadData.image.base64 = imageBase64;
    downloadData.image.fileName = `LHC_Evento_${eventNumber}_${fileName}.png`;
    downloadData.audio.base64 = audioBase64;
    downloadData.audio.fileName = `LHC_Evento_${eventNumber}_${fileName}.wav`;
}

/**
 * Descarga la imagen del evento
 */
function downloadImage() {
    if (downloadData.image.base64) {
        // Crear un enlace temporal para descargar
        const link = document.createElement('a');
        link.href = 'data:image/png;base64,' + downloadData.image.base64;
        link.download = downloadData.image.fileName;
        link.style.display = 'none';
        
        // Añadir al DOM, hacer click y remover
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Mostrar mensaje de confirmación
        showDownloadMessage('Imagen descargada exitosamente: ' + downloadData.image.fileName);
    } else {
        showDownloadMessage('No hay imagen disponible para descargar. Genere el video primero.', 'warning');
    }
}

/**
 * Descarga el audio del evento
 */
function downloadAudio() {
    if (downloadData.audio.base64) {
        // Crear un enlace temporal para descargar
        const link = document.createElement('a');
        link.href = 'data:audio/wav;base64,' + downloadData.audio.base64;
        link.download = downloadData.audio.fileName;
        link.style.display = 'none';
        
        // Añadir al DOM, hacer click y remover
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Mostrar mensaje de confirmación
        showDownloadMessage('Audio descargado exitosamente: ' + downloadData.audio.fileName);
    } else {
        showDownloadMessage('No hay audio disponible para descargar. Genere el video primero.', 'warning');
    }
}

/**
 * Muestra un mensaje de confirmación de descarga
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

/**
 * Inicializa los event listeners para los botones de descarga
 */
function initializeDownloadButtons() {
    const downloadImageBtn = document.getElementById('downloadEventImage');
    const downloadAudioBtn = document.getElementById('downloadEventAudio');
    
    if (downloadImageBtn) {
        downloadImageBtn.addEventListener('click', function(e) {
            e.preventDefault();
            downloadImage();
        });
    }
    
    if (downloadAudioBtn) {
        downloadAudioBtn.addEventListener('click', function(e) {
            e.preventDefault();
            downloadAudio();
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeDownloadButtons();
});
