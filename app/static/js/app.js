// Car Buddies GaragePro - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initApp();
});

function initApp() {
    // Initialize all components
    initServiceToggles();
    initQuickActions();
    initSearch();
    initForms();
    initPrintButtons();
    initAutoRefresh();
    
    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
        registerServiceWorker();
    }
}

// Service Worker Registration
async function registerServiceWorker() {
    try {
        const registration = await navigator.serviceWorker.register('/static/sw.js');
        console.log('ServiceWorker registered successfully');
    } catch (error) {
        console.log('ServiceWorker registration failed:', error);
    }
}

// Service Item Toggle Functionality
function initServiceToggles() {
    const toggleSwitches = document.querySelectorAll('.service-toggle input[type="checkbox"]');
    
    toggleSwitches.forEach(switchElement => {
        switchElement.addEventListener('change', function() {
            const serviceId = this.dataset.serviceId;
            const isFixed = this.checked;
            
            toggleServiceStatus(serviceId, isFixed);
        });
    });
}

async function toggleServiceStatus(serviceId, isFixed) {
    try {
        const response = await fetch(`/jobs/service/${serviceId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_fixed: isFixed })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update service status');
        }
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('Service status updated successfully!', 'success');
            // Update the UI accordingly
            updateServiceUI(serviceId, isFixed);
        } else {
            throw new Error(result.message || 'Update failed');
        }
    } catch (error) {
        console.error('Error updating service status:', error);
        showAlert('Failed to update service status', 'error');
        // Revert the toggle
        const toggle = document.querySelector(`[data-service-id="${serviceId}"]`);
        if (toggle) {
            toggle.checked = !isFixed;
        }
    }
}

function updateServiceUI(serviceId, isFixed) {
    const serviceElement = document.querySelector(`[data-service="${serviceId}"]`);
    if (serviceElement) {
        if (isFixed) {
            serviceElement.classList.add('fixed');
            serviceElement.classList.remove('pending');
        } else {
            serviceElement.classList.add('pending');
            serviceElement.classList.remove('fixed');
        }
    }
    
    // Update totals if they exist on the page
    updateJobTotals();
}

function updateJobTotals() {
    // This would recalculate and update the displayed totals
    // Implementation depends on specific page structure
}

// Quick Actions
function initQuickActions() {
    const quickActionButtons = document.querySelectorAll('[data-quick-action]');
    
    quickActionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.dataset.quickAction;
            executeQuickAction(action);
        });
    });
}

function executeQuickAction(action) {
    switch(action) {
        case 'new-job':
            window.location.href = '/jobs/add';
            break;
        case 'new-owner':
            window.location.href = '/car_owners/add';
            break;
        case 'new-car':
            window.location.href = '/cars/add';
            break;
        case 'record-payment':
            window.location.href = '/payments';
            break;
        case 'generate-quote':
            // Implementation for quick quote generation
            break;
        default:
            console.log('Unknown quick action:', action);
    }
}

// Search Functionality
function initSearch() {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    
    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });
        
        // Real-time search as user types (with debounce)
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performSearch, 500);
        });
    }
}

function performSearch() {
    const searchInput = document.getElementById('search-input');
    const searchType = document.getElementById('search-type');
    const resultsContainer = document.getElementById('search-results');
    
    if (!searchInput || !resultsContainer) return;
    
    const query = searchInput.value.trim();
    const type = searchType ? searchType.value : 'all';
    
    if (query.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }
    
    // Show loading state
    resultsContainer.innerHTML = '<div class="text-center">🔍 Searching...</div>';
    
    // Perform search via AJAX
    fetch(`/api/search?q=${encodeURIComponent(query)}&type=${type}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data, resultsContainer);
        })
        .catch(error => {
            console.error('Search error:', error);
            resultsContainer.innerHTML = '<div class="alert alert-error">Search failed</div>';
        });
}

function displaySearchResults(results, container) {
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="text-muted">No results found</div>';
        return;
    }
    
    let html = '';
    
    results.forEach(result => {
        if (result.type === 'car') {
            html += `
                <div class="search-result-item">
                    <div class="d-flex justify-between align-center">
                        <div>
                            <strong>🚗 ${result.license_plate}</strong>
                            <div>${result.make} ${result.model} • ${result.owner_name}</div>
                        </div>
                        <a href="/cars/${result.id}" class="btn btn-sm btn-primary">View</a>
                    </div>
                </div>
            `;
        } else if (result.type === 'owner') {
            html += `
                <div class="search-result-item">
                    <div class="d-flex justify-between align-center">
                        <div>
                            <strong>👤 ${result.name}</strong>
                            <div>${result.phone} • Balance: R ${result.balance}</div>
                        </div>
                        <a href="/car_owners/${result.id}" class="btn btn-sm btn-primary">View</a>
                    </div>
                </div>
            `;
        }
    });
    
    container.innerHTML = html;
}

// Form Enhancements
function initForms() {
    // Auto-format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"][data-currency]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            formatCurrencyInput(this);
        });
        
        input.addEventListener('focus', function() {
            unformatCurrencyInput(this);
        });
    });
    
    // Auto-calculate totals
    const costInputs = document.querySelectorAll('input[name="cost"]');
    costInputs.forEach(input => {
        input.addEventListener('input', calculateServiceTotal);
    });
    
    // Enhanced select elements
    const enhancedSelects = document.querySelectorAll('select[data-enhanced]');
    enhancedSelects.forEach(select => {
        // Add search functionality to large select boxes
        if (select.options.length > 10) {
            enhanceSelectWithSearch(select);
        }
    });
}

function formatCurrencyInput(input) {
    let value = parseFloat(input.value);
    if (!isNaN(value)) {
        input.value = 'R ' + value.toLocaleString('en-ZA', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
}

function unformatCurrencyInput(input) {
    let value = input.value.replace(/[^0-9.]/g, '');
    input.value = value;
}

function calculateServiceTotal() {
    const costInputs = document.querySelectorAll('input[name="cost"]');
    let total = 0;
    
    costInputs.forEach(input => {
        let value = parseFloat(input.value) || 0;
        total += value;
    });
    
    const totalElement = document.getElementById('service-total');
    if (totalElement) {
        totalElement.textContent = 'R ' + total.toLocaleString('en-ZA', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
}

function enhanceSelectWithSearch(select) {
    // Create search input
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Type to search...';
    searchInput.className = 'form-control mb-2';
    searchInput.style.marginBottom = '0.5rem';
    
    // Insert search input before select
    select.parentNode.insertBefore(searchInput, select);
    
    // Filter options based on search
    searchInput.addEventListener('input', function() {
        const filter = this.value.toLowerCase();
        const options = select.options;
        
        for (let i = 0; i < options.length; i++) {
            const text = options[i].text.toLowerCase();
            options[i].style.display = text.includes(filter) ? '' : 'none';
        }
    });
}

// Print Functionality
function initPrintButtons() {
    const printButtons = document.querySelectorAll('[data-print]');
    
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = this.dataset.print;
            printElement(target);
        });
    });
}

function printElement(elementSelector) {
    const element = document.querySelector(elementSelector);
    if (!element) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Print</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .receipt-container { max-width: 800px; margin: 0 auto; }
                    .text-center { text-align: center; }
                    .text-right { text-align: right; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 8px; border-bottom: 1px solid #ddd; }
                    th { background-color: #f8f9fa; }
                    .total-row { font-weight: bold; border-top: 2px solid #000; }
                </style>
            </head>
            <body>
                ${element.innerHTML}
            </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.focus();
    
    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 500);
}

// Auto-refresh dashboard data
function initAutoRefresh() {
    const dashboardElements = document.querySelectorAll('[data-auto-refresh]');
    
    if (dashboardElements.length > 0) {
        // Refresh every 30 seconds
        setInterval(refreshDashboardData, 30000);
    }
}

async function refreshDashboardData() {
    try {
        const response = await fetch('/api/dashboard_stats');
        const data = await response.json();
        
        // Update stats on the page
        updateDashboardStats(data);
    } catch (error) {
        console.error('Failed to refresh dashboard data:', error);
    }
}

function updateDashboardStats(data) {
    // Update various stat elements on the page
    const statElements = {
        'total-cars': data.total_cars,
        'active-jobs': data.active_jobs,
        'total-revenue': 'R ' + data.total_revenue.toLocaleString('en-ZA'),
        'total-outstanding': 'R ' + data.total_outstanding.toLocaleString('en-ZA')
    };
    
    Object.keys(statElements).forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            element.textContent = statElements[key];
        }
    });
}

// Alert System
function showAlert(message, type = 'info', duration = 5000) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.flash-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} flash-alert`;
    alert.innerHTML = `
        <div class="d-flex justify-between align-center">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer;">×</button>
        </div>
    `;
    
    // Add to page
    const container = document.querySelector('.alerts-container') || createAlertsContainer();
    container.appendChild(alert);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, duration);
    }
}

function createAlertsContainer() {
    const container = document.createElement('div');
    container.className = 'alerts-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '1000';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-ZA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatCurrency(amount) {
    return 'R ' + parseFloat(amount).toLocaleString('en-ZA', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Export functions for global access
window.showAlert = showAlert;
window.formatDate = formatDate;
window.formatCurrency = formatCurrency;