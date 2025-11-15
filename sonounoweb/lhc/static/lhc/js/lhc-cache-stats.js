/**
 * LHC Cache Stats - Funciones para la página de estadísticas de caché
 * Separado del template para mejorar la mantenibilidad
 */

// Variables para el auto-refresh
let refreshTimer;

/**
 * Función para confirmar limpieza de caché
 */
function confirmClearCache() {
    return confirm('¿Está seguro de que desea limpiar todo el caché?\n\nEsta acción eliminará todos los videos almacenados y no se puede deshacer.');
}

/**
 * Inicia el auto-refresh de la página
 */
function startAutoRefresh() {
    refreshTimer = setTimeout(function() {
        if (!document.hidden) {
            location.reload();
        } else {
            // Si la página está oculta, intentar de nuevo en 5 segundos
            setTimeout(startAutoRefresh, 5000);
        }
    }, 30000); // 30 segundos
}

/**
 * Configura el auto-refresh basado en si hay archivos en caché
 */
function setupAutoRefresh(hasFiles) {
    if (!hasFiles) return;
    
    // Pausar auto-refresh cuando la página está oculta
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            clearTimeout(refreshTimer);
        } else {
            startAutoRefresh();
        }
    });
    
    // Iniciar auto-refresh
    startAutoRefresh();
}

/**
 * Inicializa la funcionalidad de la página de estadísticas
 */
function initializeCacheStats() {
    console.log('Cache stats page initialized');
    
    // Determinar si hay archivos en caché basándose en el contenido de la página
    const filesElement = document.querySelector('[data-cache-files]');
    const hasFiles = filesElement ? parseInt(filesElement.getAttribute('data-cache-files')) > 0 : false;
    
    // Configurar auto-refresh si hay archivos en caché
    if (hasFiles) {
        console.log('Archivos en caché detectados, configurando auto-refresh');
        setupAutoRefresh(true);
    } else {
        console.log('No hay archivos en caché, auto-refresh deshabilitado');
        setupAutoRefresh(false);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeCacheStats();
});
