/**
 * tab_marcadores.js - Gestión de tabla de puntos y marcadores en tiempo real
 */

document.addEventListener('DOMContentLoaded', function() {
    const markersTable = document.getElementById('markersTable');
    const markersTableBody = document.getElementById('markersTableBody');
    const noMarkersMsg = document.getElementById('noMarkersMsg');
    const btnClearAllMarkers = document.getElementById('btnClearAllMarkers');
    const btnExportMarkersCsv = document.getElementById('btnExportMarkersCsv');

    function renderMarkersTable(markers) {
        if (!markersTableBody || !noMarkersMsg || !markersTable) return;
        
        if (!markers || !Array.isArray(markers)) {
            if (window.sonoUno1D && typeof window.sonoUno1D.getMarkers === 'function') {
                markers = window.sonoUno1D.getMarkers();
            } else {
                const stored = localStorage.getItem('markers');
                markers = stored ? JSON.parse(stored) : [];
            }
        }
        
        if (!markers || markers.length === 0) {
            markersTable.classList.add('d-none');
            noMarkersMsg.classList.remove('d-none');
            markersTableBody.innerHTML = '';
            const badge = document.getElementById('tabMarkerBadge');
            if (badge) badge.textContent = '0 puntos';
            return;
        }

        noMarkersMsg.classList.add('d-none');
        markersTable.classList.remove('d-none');
        markersTableBody.innerHTML = '';

        const badge = document.getElementById('tabMarkerBadge');
        if (badge) badge.textContent = `${markers.length} punto(s)`;

        markers.forEach((m, idx) => {
            const tr = document.createElement('tr');
            const xFormatted = typeof m.x === 'number' ? m.x.toFixed(3) : m.x;
            const yFormatted = typeof m.y === 'number' ? m.y.toFixed(3) : m.y;

            tr.innerHTML = `
                <td class="fw-bold">${idx + 1}</td>
                <td>${xFormatted}</td>
                <td>${yFormatted}</td>
                <td class="text-end">
                    <button class="btn btn-outline-danger btn-xs py-0 px-1 btn-delete-single-marker" data-index="${idx}" title="Eliminar este marcador">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
            `;
            markersTableBody.appendChild(tr);
        });

        // Eventos para eliminar marcador individual
        document.querySelectorAll('.btn-delete-single-marker').forEach(btn => {
            btn.addEventListener('click', function() {
                const markerIndex = parseInt(this.getAttribute('data-index'), 10);
                if (window.sonoUno1D) {
                    const currentMarkers = window.sonoUno1D.getMarkers();
                    currentMarkers.splice(markerIndex, 1);
                    window.sonoUno1D.setMarkers(currentMarkers);
                } else {
                    const stored = localStorage.getItem('markers');
                    const currentMarkers = stored ? JSON.parse(stored) : [];
                    currentMarkers.splice(markerIndex, 1);
                    localStorage.setItem('markers', JSON.stringify(currentMarkers));
                    renderMarkersTable(currentMarkers);
                }
            });
        });
    }

    // Escuchar eventos globales de cambio de marcadores
    window.addEventListener('sonouno:markers-changed', function(e) {
        if (e.detail && e.detail.markers) {
            renderMarkersTable(e.detail.markers);
        }
    });

    // Actualizar la tabla cada vez que el usuario abra la pestaña de Marcadores
    const tabMarcadoresBtn = document.getElementById('tab-marcadores-btn');
    if (tabMarcadoresBtn) {
        tabMarcadoresBtn.addEventListener('shown.bs.tab', function() {
            renderMarkersTable();
        });
    }

    // Callback directo si sonoUno1D ya está presente
    if (window.sonoUno1D) {
        window.sonoUno1D.onMarkersChanged = function(markers) {
            renderMarkersTable(markers);
        };
    }

    // Renderizado inicial al cargar la página
    renderMarkersTable();

    if (btnClearAllMarkers) {
        btnClearAllMarkers.addEventListener('click', function() {
            if (window.sonoUno1D) {
                const currentMarkers = window.sonoUno1D.getMarkers();
                if (currentMarkers.length === 0) {
                    alert('No hay marcadores para eliminar.');
                    return;
                }
                if (confirm('¿Eliminar todos los marcadores guardados?')) {
                    window.sonoUno1D.setMarkers([]);
                }
            } else {
                localStorage.setItem('markers', JSON.stringify([]));
                renderMarkersTable([]);
            }
        });
    }

    if (btnExportMarkersCsv) {
        btnExportMarkersCsv.addEventListener('click', function() {
            const downloadBtn = document.getElementById('downloadMarkers');
            if (downloadBtn) {
                downloadBtn.click();
            }
        });
    }
});
