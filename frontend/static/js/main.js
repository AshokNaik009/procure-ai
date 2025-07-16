// Procurement Intelligence System - Main JavaScript

class ProcurementAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.requestId = null;
    }

    async analyzeMarket(query) {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.baseURL}/api/v1/procurement/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(query)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Market analysis failed:', error);
            throw error;
        } finally {
            this.hideLoading();
        }
    }

    async discoverSuppliers(params) {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.baseURL}/api/v1/suppliers/discover`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Supplier discovery failed:', error);
            throw error;
        } finally {
            this.hideLoading();
        }
    }

    async getMarketIntelligence(params) {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.baseURL}/api/v1/market/intelligence`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Market intelligence failed:', error);
            throw error;
        } finally {
            this.hideLoading();
        }
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }

    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('d-none');
            this.updateProgress(0);
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('d-none');
        }
    }

    updateProgress(percent) {
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
        }
    }
}

// Toast Notifications
class ToastManager {
    static showSuccess(message) {
        const toast = document.getElementById('successToast');
        const body = document.getElementById('successToastBody');
        
        if (toast && body) {
            body.textContent = message;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    }

    static showError(message) {
        const toast = document.getElementById('errorToast');
        const body = document.getElementById('errorToastBody');
        
        if (toast && body) {
            body.textContent = message;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    }
}

// Utility Functions
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatTime(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

function generateStars(rating) {
    if (!rating) return '<span class="text-muted">No rating</span>';
    
    const fullStars = Math.floor(rating);
    const halfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
    
    let stars = '';
    
    // Full stars
    for (let i = 0; i < fullStars; i++) {
        stars += '<i class="fas fa-star"></i>';
    }
    
    // Half star
    if (halfStar) {
        stars += '<i class="fas fa-star-half-alt"></i>';
    }
    
    // Empty stars
    for (let i = 0; i < emptyStars; i++) {
        stars += '<i class="far fa-star empty-star"></i>';
    }
    
    return `<span class="rating-stars">${stars}</span>`;
}

function getConfidenceClass(score) {
    if (score >= 0.8) return 'confidence-high';
    if (score >= 0.6) return 'confidence-medium';
    return 'confidence-low';
}

function getConfidenceText(score) {
    if (score >= 0.8) return 'High Confidence';
    if (score >= 0.6) return 'Medium Confidence';
    return 'Low Confidence';
}

// Search functionality
function scrollToSearch() {
    const searchSection = document.getElementById('searchSection');
    if (searchSection) {
        searchSection.scrollIntoView({ behavior: 'smooth' });
    }
}

function showDemo() {
    // Demo functionality
    const demoQuery = {
        query: 'industrial steel suppliers',
        category: 'materials',
        location: 'Texas',
        timeline: '30 days'
    };
    
    // Fill form with demo data
    document.getElementById('productQuery').value = demoQuery.query;
    document.getElementById('category').value = demoQuery.category;
    document.getElementById('location').value = demoQuery.location;
    document.getElementById('timeline').value = demoQuery.timeline;
    
    // Scroll to search section
    scrollToSearch();
    
    // Show demo notification
    ToastManager.showSuccess('Demo data loaded! Click "Analyze Market" to see results.');
}

// Export functionality
function exportResults(format) {
    const resultsData = {
        timestamp: new Date().toISOString(),
        query: document.getElementById('productQuery').value,
        format: format
    };
    
    // In a real implementation, this would generate and download the file
    console.log('Exporting results:', resultsData);
    ToastManager.showSuccess(`Export to ${format.toUpperCase()} initiated. Download will start shortly.`);
}

function shareResults() {
    const shareData = {
        title: 'Procurement Intelligence Results',
        text: 'Check out these procurement analysis results',
        url: window.location.href
    };
    
    if (navigator.share) {
        navigator.share(shareData);
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            ToastManager.showSuccess('Results URL copied to clipboard!');
        });
    }
}

// System status check
async function checkSystemStatus() {
    const api = new ProcurementAPI();
    const statusElement = document.getElementById('systemStatus');
    
    if (statusElement) {
        try {
            const isHealthy = await api.checkHealth();
            const statusText = isHealthy ? 'Online' : 'Offline';
            const statusClass = isHealthy ? 'text-success' : 'text-danger';
            
            statusElement.innerHTML = `System Status: <span class="${statusClass}">${statusText}</span>`;
        } catch (error) {
            statusElement.innerHTML = 'System Status: <span class="text-warning">Unknown</span>';
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check system status
    checkSystemStatus();
    
    // Setup periodic status checks
    setInterval(checkSystemStatus, 60000); // Every minute
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Setup form auto-save (if needed)
    setupFormAutoSave();
});

// Form auto-save functionality
function setupFormAutoSave() {
    const form = document.getElementById('procurementForm');
    if (!form) return;
    
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('input', debounce(() => {
            saveFormData();
        }, 1000));
    });
    
    // Load saved data on page load
    loadFormData();
}

function saveFormData() {
    const formData = {
        productQuery: document.getElementById('productQuery')?.value || '',
        location: document.getElementById('location')?.value || '',
        category: document.getElementById('category')?.value || '',
        timeline: document.getElementById('timeline')?.value || '',
        requirements: document.getElementById('requirements')?.value || ''
    };
    
    localStorage.setItem('procurementFormData', JSON.stringify(formData));
}

function loadFormData() {
    const savedData = localStorage.getItem('procurementFormData');
    if (!savedData) return;
    
    try {
        const formData = JSON.parse(savedData);
        
        Object.keys(formData).forEach(key => {
            const element = document.getElementById(key);
            if (element && formData[key]) {
                element.value = formData[key];
            }
        });
    } catch (error) {
        console.error('Error loading form data:', error);
    }
}

// Debounce utility
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

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    ToastManager.showError('An unexpected error occurred. Please try again.');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    ToastManager.showError('An unexpected error occurred. Please try again.');
});

// Export classes for use in other files
window.ProcurementAPI = ProcurementAPI;
window.ToastManager = ToastManager;