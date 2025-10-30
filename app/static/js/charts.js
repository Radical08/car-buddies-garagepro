// Chart.js implementations for dashboard
class GarageCharts {
    static initRevenueChart() {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Monthly Revenue (R)',
                    data: [12000, 19000, 15000, 25000, 22000, 30000],
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8f9fa'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#f8f9fa',
                            callback: function(value) {
                                return 'R ' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#f8f9fa'
                        }
                    }
                }
            }
        });
    }
    
    static initServiceDistributionChart() {
        const ctx = document.getElementById('serviceDistributionChart');
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Suspension', 'Engine', 'Brakes', 'Diagnosis', 'Other'],
                datasets: [{
                    data: [30, 25, 20, 15, 10],
                    backgroundColor: [
                        '#00d4ff',
                        '#ff6b35',
                        '#28a745',
                        '#ffc107',
                        '#6c757d'
                    ],
                    borderWidth: 2,
                    borderColor: '#1a1a1a'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f8f9fa',
                            padding: 20
                        }
                    }
                }
            }
        });
    }
    
    static initJobStatusChart() {
        const ctx = document.getElementById('jobStatusChart');
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['In Progress', 'Completed', 'Quoted'],
                datasets: [{
                    label: 'Jobs',
                    data: [8, 15, 5],
                    backgroundColor: [
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(23, 162, 184, 0.8)'
                    ],
                    borderColor: [
                        '#ffc107',
                        '#28a745',
                        '#17a2b8'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#f8f9fa'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#f8f9fa'
                        }
                    }
                }
            }
        });
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    GarageCharts.initRevenueChart();
    GarageCharts.initServiceDistributionChart();
    GarageCharts.initJobStatusChart();
});