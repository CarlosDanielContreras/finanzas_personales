/**
 * JavaScript Principal
 * Finanzas Personales
 */

// Esperar a que el DOM esté completamente cargado
$(document).ready(function() {
    
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-cerrar alertas después de 5 segundos
    setTimeout(function() {
        $('.alert').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
    
    // Formatear números como moneda en inputs
    $('.currency-input').on('input', function() {
        let value = $(this).val().replace(/[^0-9.]/g, '');
        if (value) {
            $(this).val(formatCurrency(parseFloat(value)));
        }
    });
    
    // Confirmación antes de eliminar
    $('.btn-delete').on('click', function(e) {
        if (!confirm('¿Estás seguro de que deseas eliminar este elemento?')) {
            e.preventDefault();
        }
    });
    
    // Animación de fade-in para elementos
    $('.fade-in').each(function(index) {
        $(this).delay(100 * index).animate({
            opacity: 1
        }, 300);
    });
});

/**
 * Formatear número como moneda
 */
function formatCurrency(amount) {
    return '$' + amount.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

/**
 * Formatear fecha
 */
function formatDate(date) {
    const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
    return new Date(date).toLocaleDateString('es-CO', options);
}

/**
 * Mostrar spinner de carga
 */
function showLoader() {
    const loaderHtml = `
        <div class="spinner-overlay">
            <div class="spinner-border text-light" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
    `;
    $('body').append(loaderHtml);
}

/**
 * Ocultar spinner de carga
 */
function hideLoader() {
    $('.spinner-overlay').remove();
}

/**
 * Mostrar notificación toast
 */
function showToast(message, type = 'info') {
    const iconMap = {
        'success': 'check-circle',
        'danger': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${iconMap[type]} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    $('body').append(toastHtml);
    const toastElement = $('.toast').last()[0];
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    // Eliminar el toast del DOM después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        $(this).remove();
    });
}

/**
 * Validar formularios
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return false;
    }
    return true;
}

/**
 * Debounce para búsquedas
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copiar texto al portapapeles
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copiado al portapapeles', 'success');
    }, function(err) {
        showToast('Error al copiar', 'danger');
    });
}

/**
 * Descargar archivo
 */
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Petición AJAX genérica
 */
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    showLoader();
    
    $.ajax({
        url: url,
        method: method,
        data: JSON.stringify(data),
        contentType: 'application/json',
        success: function(response) {
            hideLoader();
            if (successCallback) successCallback(response);
        },
        error: function(xhr, status, error) {
            hideLoader();
            if (errorCallback) {
                errorCallback(xhr, status, error);
            } else {
                showToast('Ocurrió un error. Por favor intenta de nuevo.', 'danger');
            }
        }
    });
}

/**
 * Actualizar estadísticas en tiempo real (WebSocket o polling)
 */
function updateDashboardStats() {
    // Implementar según necesidad
    // Puede usar polling o WebSocket para actualizaciones en tiempo real
}

/**
 * Exportar tabla a CSV
 */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            row.push(cols[j].innerText);
        }
        
        csv.push(row.join(','));
    }
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    downloadFile(url, filename + '.csv');
}

/**
 * Imprimir elemento
 */
function printElement(elementId) {
    const printContents = document.getElementById(elementId).innerHTML;
    const originalContents = document.body.innerHTML;
    
    document.body.innerHTML = printContents;
    window.print();
    document.body.innerHTML = originalContents;
    location.reload();
}

// Configuración global de AJAX para CSRF
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            const csrfToken = $('meta[name="csrf-token"]').attr('content');
            if (csrfToken) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            }
        }
    }
});