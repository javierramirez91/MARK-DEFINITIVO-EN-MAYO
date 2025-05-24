/**
 * Funcionalidades comunes para el panel de administración del asistente Mark
 */

// Función para manejar la autenticación
function handleAuth() {
    const token = localStorage.getItem('access_token');
    
    // Si no hay token y no estamos en la página de login, redirigir al login
    if (!token && window.location.pathname !== '/') {
        window.location.href = '/';
        return;
    }
    
    // Añadir token a todas las peticiones fetch
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Si ya tiene Authorization header o es la petición de login, no modificar
        if (url === '/token' || (options.headers && options.headers.Authorization)) {
            return originalFetch(url, options);
        }
        
        // Añadir el token a los headers
        const newOptions = {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            }
        };
        
        return originalFetch(url, newOptions)
            .then(response => {
                // Si recibimos un 401 (Unauthorized), redirigir al login
                if (response.status === 401) {
                    localStorage.removeItem('access_token');
                    window.location.href = '/';
                    return Promise.reject('Sesión expirada');
                }
                return response;
            });
    };
}

// Función para cerrar sesión
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/';
}

// Función para formatear fechas
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Función para formatear números de teléfono
function formatPhone(phone) {
    if (!phone) return '';
    
    // Asegurarse de que tiene el prefijo internacional
    if (!phone.startsWith('+')) {
        phone = '+34' + phone;
    }
    
    // Eliminar espacios y guiones
    phone = phone.replace(/[\s-]/g, '');
    
    return phone;
}

// Función para mostrar notificaciones toast
function showToast(message, type = 'info') {
    // Crear el elemento toast si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Crear el toast
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Contenido del toast
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Añadir el toast al contenedor
    toastContainer.appendChild(toast);
    
    // Inicializar y mostrar el toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Eliminar el toast del DOM cuando se oculte
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Función para confirmar acciones peligrosas
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Función para validar formularios
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    // Añadir la clase 'was-validated' para mostrar los mensajes de validación
    form.classList.add('was-validated');
    
    // Comprobar si el formulario es válido
    return form.checkValidity();
}

// Función para cargar datos en una tabla
function loadTableData(tableId, data, columns, emptyMessage = 'No hay datos disponibles') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    // Limpiar la tabla
    tbody.innerHTML = '';
    
    // Si no hay datos, mostrar mensaje
    if (!data || data.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="${columns.length}" class="text-center">${emptyMessage}</td>`;
        tbody.appendChild(tr);
        return;
    }
    
    // Añadir filas con datos
    data.forEach(item => {
        const tr = document.createElement('tr');
        
        columns.forEach(column => {
            const td = document.createElement('td');
            
            if (typeof column.render === 'function') {
                td.innerHTML = column.render(item);
            } else {
                td.textContent = item[column.field] || '';
            }
            
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Manejar autenticación
    handleAuth();
    
    // Configurar eventos de logout
    const logoutLinks = document.querySelectorAll('#logout-link, #logout-dropdown');
    logoutLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    });
    
    // Formatear fechas en la página
    document.querySelectorAll('.format-date').forEach(element => {
        element.textContent = formatDate(element.textContent);
    });
    
    // Formatear teléfonos en la página
    document.querySelectorAll('.format-phone').forEach(element => {
        element.textContent = formatPhone(element.textContent);
    });
    
    // Inicializar tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 