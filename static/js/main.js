// Configuração global / global configuration
window.AutoU = {
    API_BASE: '/api/classifier/classifications/',
    ENDPOINTS: {
        classify: 'classify_no_db/',
        stats: 'stats/',
        test: 'test_ai/'
    }
};

// Utilitários globais / Global utilities
const Utils = {
    // Loading states
    showLoading: function(element) {
        element.classList.add('loading');
        element.disabled = true;
    },
    
    hideLoading: function(element) {
        element.classList.remove('loading');
        element.disabled = false;
    },
    
    // Notificações / Notifications
    showNotification: function(message, type = 'info') {
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show m-3" role="alert">
                <i class="fas fa-${this.getIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('.messages-container') || 
                         document.querySelector('main');
        container.insertAdjacentHTML('afterbegin', alertHTML);
    },
    
    getIcon: function(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-triangle', 
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
};

// Inicialização / Initialization
document.addEventListener('DOMContentLoaded', function() {
    // Navbar ativa
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Animações fade-in / Fade-in animations
    document.querySelectorAll('.fade-in').forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.5s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, 100);
    });
});