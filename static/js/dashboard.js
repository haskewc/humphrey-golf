// Dashboard JavaScript
// Fetches stats from /api/dashboard/stats and renders charts

// Chart colors
const folioColors = {
    1: '#1a4a3a',
    2: '#2d5a47',
    3: '#4a7c59',
    4: '#6b9b7a'
};

const goldColor = '#c9a227';
const burgundyColor = '#722f37';

// Interesting facts that rotate
const facts = [
    "The oldest ball in the collection dates back to 1845 — over 180 years old!",
    "Gutta-percha balls were made from the sap of Malaysian trees.",
    "The Haskell ball (1898) revolutionized golf with its rubber core.",
    "Some rare balls can fetch over £10,000 at auction.",
    "The collection spans from the feather ball era to post-war rubber cores.",
    "Many manufacturers from the 1800s no longer exist today.",
    "Condition grading ranges from A1 (mint) to A5 (poor).",
    "The collection represents over 4,400 unique golf ball specimens."
];

let currentFactIndex = 0;

// Format currency
function formatCurrency(value, currency = 'GBP') {
    if (!value) return '£0';
    const symbol = currency === 'USD' ? '$' : '£';
    return symbol + Math.round(value).toLocaleString();
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    startFactRotation();
});

// Load dashboard data from API
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) throw new Error('Failed to load dashboard data');
        
        const data = await response.json();
        updateHeroStats(data);
        renderCharts(data);
        renderManufacturersTable(data.top_manufacturers);
    } catch (error) {
        console.error('Dashboard error:', error);
        showError('Failed to load dashboard data. Please try again later.');
    }
}

// Update hero stats
function updateHeroStats(data) {
    document.getElementById('total-balls').textContent = data.total_balls.toLocaleString();
    document.getElementById('total-manufacturers').textContent = data.total_manufacturers.toLocaleString();
    document.getElementById('total-countries').textContent = data.total_countries.toLocaleString();
    document.getElementById('most-valuable').textContent = formatCurrency(data.most_valuable.value, data.most_valuable.currency);
}

// Render all charts
function renderCharts(data) {
    renderFolioChart(data.by_folio);
    renderTimelineChart(data.timeline);
    renderCountriesChart(data.by_country);
    renderPatternsChart(data.by_pattern);
    renderValueChart(data.by_value_range);
}

// Folio Distribution (Donut Chart)
function renderFolioChart(folioData) {
    const ctx = document.getElementById('folioChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: folioData.map(f => `Folio ${f.folio} - ${f.name}`),
            datasets: [{
                data: folioData.map(f => f.count),
                backgroundColor: folioData.map(f => folioColors[f.folio] || '#999'),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.label}: ${context.raw.toLocaleString()} balls (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// Timeline (Line Chart)
function renderTimelineChart(timelineData) {
    const ctx = document.getElementById('timelineChart').getContext('2d');
    
    // Prepare datasets for each folio
    const folios = [1, 2, 3, 4];
    const datasets = folios.map(folio => ({
        label: `Folio ${folio}`,
        data: timelineData.map(t => t[`folio_${folio}`] || 0),
        borderColor: folioColors[folio],
        backgroundColor: folioColors[folio] + '20',
        fill: false,
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6
    }));
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: timelineData.map(t => t.year),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 10
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Countries (Bar Chart)
function renderCountriesChart(countriesData) {
    const ctx = document.getElementById('countriesChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: countriesData.map(c => `${c.flag} ${c.country}`),
            datasets: [{
                label: 'Balls',
                data: countriesData.map(c => c.count),
                backgroundColor: folioColors[1],
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Patterns (Horizontal Bar Chart)
function renderPatternsChart(patternsData) {
    const ctx = document.getElementById('patternsChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: patternsData.map(p => p.pattern),
            datasets: [{
                label: 'Balls',
                data: patternsData.map(p => p.count),
                backgroundColor: folioColors[3],
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Value Ranges (Histogram)
function renderValueChart(valueData) {
    const ctx = document.getElementById('valueChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: valueData.map(v => v.range),
            datasets: [{
                label: 'Number of Balls',
                data: valueData.map(v => v.count),
                backgroundColor: valueData.map((v, i) => {
                    // Gradient from light to dark
                    const opacity = 0.3 + (i / valueData.length) * 0.7;
                    return `rgba(201, 162, 39, ${opacity})`;
                }),
                borderColor: goldColor,
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.raw.toLocaleString()} balls`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Render manufacturers table
function renderManufacturersTable(manufacturers) {
    const tbody = document.getElementById('manufacturers-tbody');
    tbody.innerHTML = '';
    
    if (!manufacturers || manufacturers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No data available</td></tr>';
        return;
    }
    
    manufacturers.forEach((m, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${escapeHtml(m.name)}</td>
            <td>${m.count.toLocaleString()}</td>
            <td>${formatCurrency(m.avg_value || m.avgValue)}</td>
            <td>${escapeHtml(m.top_ball || m.topBall || 'N/A')}</td>
        `;
        tbody.appendChild(row);
    });
}

// Rotate facts
function startFactRotation() {
    const factElement = document.getElementById('rotating-fact');
    if (!factElement) return;
    
    // Show first fact
    factElement.textContent = facts[0];
    
    // Rotate every 8 seconds
    setInterval(() => {
        currentFactIndex = (currentFactIndex + 1) % facts.length;
        factElement.style.opacity = '0';
        
        setTimeout(() => {
            factElement.textContent = facts[currentFactIndex];
            factElement.style.opacity = '1';
        }, 300);
    }, 8000);
}

// Utility: Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility: Show error
function showError(message) {
    const container = document.querySelector('.dashboard-container');
    if (container) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = 'background: #f8d7da; color: #721c24; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;';
        errorDiv.textContent = message;
        container.insertBefore(errorDiv, container.firstChild);
    }
}
