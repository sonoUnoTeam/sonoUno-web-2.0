/**
 * ImageSonif Utils - Utilidades específicas para la aplicación de sonificación de imágenes
 * Basado en el patrón de LHC Utils
 */

const ImagesonifUtils = {
    // Configuración
    config: {
        maxFileSize: 50 * 1024 * 1024, // 50MB
        allowedTypes: ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/tiff', 'image/webp'],
        progressUpdateInterval: 500
    },

    // Estado global
    state: {
        isProcessing: false,
        currentFiles: {
            video: null,
            audio: null
        }
    },

    /**
     * Mostrar mensaje de éxito
     */
    showSuccess: function(message) {
        this.showMessage(message, 'success');
    },

    /**
     * Mostrar mensaje de error
     */
    showError: function(message) {
        this.showMessage(message, 'error');
    },

    /**
     * Mostrar mensaje de información
     */
    showInfo: function(message) {
        this.showMessage(message, 'info');
    },

    /**
     * Mostrar mensaje de advertencia
     */
    showWarning: function(message) {
        this.showMessage(message, 'warning');
    },

    /**
     * Mostrar mensaje genérico
     */
    showMessage: function(message, type = 'info') {
        // Crear el elemento de mensaje
        const alertClass = this.getBootstrapClass(type);
        const iconClass = this.getIconClass(type);
        
        const messageHtml = `
            <div class="container mt-3">
                <div class="alert alert-${alertClass} alert-dismissible fade show imagesonif-fade-in" role="alert">
                    <i class="${iconClass} me-2"></i>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            </div>
        `;

        // Insertar el mensaje en el navbar (después del navbar)
        const navbar = document.querySelector('nav.navbar');
        if (navbar) {
            navbar.insertAdjacentHTML('afterend', messageHtml);
        } else {
            // Fallback: insertar al inicio del contenido
            const content = document.querySelector('.imagesonif-container');
            if (content) {
                content.insertAdjacentHTML('afterbegin', messageHtml);
            }
        }

        // Auto-ocultar después de 5 segundos para mensajes de éxito e info
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                const alerts = document.querySelectorAll('.alert:not(.alert-danger):not(.alert-warning)');
                alerts.forEach(alert => {
                    if (alert.style.display !== 'none') {
                        const bsAlert = new bootstrap.Alert(alert);
                        bsAlert.close();
                    }
                });
            }, 5000);
        }
    },

    /**
     * Limpiar todos los mensajes
     */
    clearMessages: function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                alert.remove();
            }
        });
    },

    /**
     * Mostrar indicador de carga
     */
    showLoading: function(message = 'Procesando...') {
        this.state.isProcessing = true;
        
        // Deshabilitar controles
        this.disableControls();
        
        // Mostrar panel de progreso
        let progressContainer = document.getElementById('progressContainer');
        if (!progressContainer) {
            const progressHtml = `
                <div id="progressContainer" class="imagesonif-progress-container imagesonif-fade-in">
                    <div class="text-center mb-3">
                        <div class="imagesonif-loading">
                            <div class="imagesonif-spinner"></div>
                        </div>
                    </div>
                    <div class="progress">
                        <div id="progressBar" class="imagesonif-progress-bar" style="width: 0%"></div>
                    </div>
                    <div id="progressText" class="imagesonif-progress-text">${message}</div>
                </div>
            `;
            
            const resultsPanel = document.getElementById('resultsPanel');
            if (resultsPanel) {
                resultsPanel.insertAdjacentHTML('beforebegin', progressHtml);
            }
        }
        
        progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            progressContainer.style.display = 'block';
        }
    },

    /**
     * Actualizar progreso
     */
    updateProgress: function(percentage, message = '') {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar) {
            progressBar.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
        }
        
        if (progressText && message) {
            progressText.textContent = message;
        }
    },

    /**
     * Ocultar indicador de carga
     */
    hideLoading: function() {
        this.state.isProcessing = false;
        
        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        
        // Rehabilitar controles
        this.enableControls();
    },

    /**
     * Deshabilitar controles durante el procesamiento
     */
    disableControls: function() {
        const processBtn = document.getElementById('processBtn');
        const fileInput = document.getElementById('imageFile');
        const form = document.getElementById('sonificationForm');
        
        if (processBtn) {
            processBtn.disabled = true;
            processBtn.innerHTML = '<div class="imagesonif-spinner" style="width: 20px; height: 20px;"></div> Procesando...';
        }
        
        if (fileInput) fileInput.disabled = true;
        if (form) {
            const inputs = form.querySelectorAll('input, select, button');
            inputs.forEach(input => input.disabled = true);
        }
    },

    /**
     * Rehabilitar controles
     */
    enableControls: function() {
        const processBtn = document.getElementById('processBtn');
        const fileInput = document.getElementById('imageFile');
        const form = document.getElementById('sonificationForm');
        
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.innerHTML = '<i class="bi bi-play me-2"></i>Generar Sonificación';
        }
        
        if (fileInput) fileInput.disabled = false;
        if (form) {
            const inputs = form.querySelectorAll('input, select, button');
            inputs.forEach(input => input.disabled = false);
        }
    },

    /**
     * Validar archivo de imagen
     */
    validateImageFile: function(file) {
        const errors = [];
        
        if (!file) {
            errors.push('No se ha seleccionado ningún archivo');
            return errors;
        }
        
        // Validar tipo
        if (!this.config.allowedTypes.includes(file.type)) {
            errors.push(`Tipo de archivo no soportado: ${file.type}. Use JPG, PNG, BMP, GIF, TIFF o WebP.`);
        }
        
        // Validar tamaño
        if (file.size > this.config.maxFileSize) {
            const maxMB = this.config.maxFileSize / (1024 * 1024);
            errors.push(`Archivo demasiado grande: ${this.formatFileSize(file.size)}. Máximo permitido: ${maxMB}MB.`);
        }
        
        return errors;
    },

    /**
     * Formatear tamaño de archivo
     */
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Crear blob de descarga
     */
    createDownloadBlob: function(base64Data, mimeType) {
        try {
            const byteCharacters = atob(base64Data);
            const byteNumbers = new Array(byteCharacters.length);
            
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            
            const byteArray = new Uint8Array(byteNumbers);
            return new Blob([byteArray], { type: mimeType });
        } catch (error) {
            console.error('Error creando blob:', error);
            return null;
        }
    },

    /**
     * Descargar archivo
     */
    downloadFile: function(blob, filename) {
        if (!blob) {
            this.showError('Error preparando el archivo para descarga');
            return;
        }
        
        try {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            window.URL.revokeObjectURL(url);
            
            this.showSuccess(`Descarga iniciada: ${filename}`);
        } catch (error) {
            console.error('Error en descarga:', error);
            this.showError('Error iniciando la descarga');
        }
    },

    /**
     * Generar nombre de archivo único
     */
    generateFilename: function(extension, prefix = 'sonificacion') {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        return `${prefix}_${timestamp}.${extension}`;
    },

    /**
     * Obtener clase de Bootstrap para tipo de mensaje
     */
    getBootstrapClass: function(type) {
        const classMap = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return classMap[type] || 'info';
    },

    /**
     * Obtener clase de icono para tipo de mensaje
     */
    getIconClass: function(type) {
        const iconMap = {
            'success': 'bi bi-check-circle',
            'error': 'bi bi-exclamation-triangle',
            'warning': 'bi bi-exclamation-circle',
            'info': 'bi bi-info-circle'
        };
        return iconMap[type] || 'bi bi-info-circle';
    },

    /**
     * Manejar errores de red/AJAX
     */
    handleNetworkError: function(error, customMessage = null) {
        console.error('Error de red:', error);
        
        let message = customMessage || 'Error de conexión con el servidor. Inténtalo de nuevo.';
        
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            message = 'No se pudo conectar al servidor. Verifica tu conexión a internet.';
        } else if (error.status) {
            switch (error.status) {
                case 413:
                    message = 'El archivo es demasiado grande para el servidor.';
                    break;
                case 500:
                    message = 'Error interno del servidor. Inténtalo más tarde.';
                    break;
                case 503:
                    message = 'Servidor temporalmente no disponible. Inténtalo más tarde.';
                    break;
                default:
                    message = `Error del servidor (${error.status}). Inténtalo de nuevo.`;
            }
        }
        
        this.showError(message);
    },

    /**
     * Inicializar utilidades
     */
    init: function() {
        console.log('ImageSonif Utils inicializado');
        
        // Limpiar mensajes al hacer clic en enlaces
        document.addEventListener('click', (e) => {
            if (e.target.tagName === 'A' && !e.target.classList.contains('dropdown-item')) {
                this.clearMessages();
            }
        });
        
        // Manejar errores globales de JavaScript
        window.addEventListener('error', (e) => {
            console.error('Error global:', e.error);
        });
        
        // Manejar promesas rechazadas
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Promesa rechazada:', e.reason);
        });
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    ImagesonifUtils.init();
});

// Exportar para uso global
window.ImagesonifUtils = ImagesonifUtils;
