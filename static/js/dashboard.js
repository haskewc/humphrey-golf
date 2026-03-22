/**
 * Dashboard JavaScript - Chart.js visualizations for Humphrey Golf
 */

// Chart colors matching site aesthetic
const CHART_COLORS = {
    folio1: '#1a4a3a',      // Deep green
    folio2: '#2d5a47',      // Forest green
    folio3: '#4a7c59',      // Sage
    folio4: '#6b9b7a',      // Light green
    gold: '#c9a227',        // Gold accents
    burgundy: '#722f37',    // Burgundy
    primary: '#8B2635',     // Primary site color
    cream: '#F5F0E8',
    border: '#D4CFC0'
};

const FOLIO_COLORS = [CHART_COLORS.folio1, CHART_COLORS.folio2, CHART_COLORS.folio3, CHART_COLORS.folio4];

// Global chart instances
let charts = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

/**
 * Fetch dashboard data from API
 */
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data');
        }
        const data = await response.json();
        
        updateHeroStats(data);
        initFolioChart(data);
        initTimelineChart(data);
        initCountryChart(data);
        initPatternChart(data);
        initValueChart(data);
        populateManufacturersTable(data);
        startFactRotation(data);
    } catch (error) {
        console.error('Dashboard error:', error);
        showError('Failed to load dashboard data. Please try again later.');
    }
}

/**
 * Update hero stats cards
 */
function updateHeroStats(data) {
    // Total balls
    const totalBalls = data.by_folio?.reduce((sum, f) => sum + (f.count || 0), 0) || 0;
    animateNumber('total-balls', totalBalls);
    
    // Total manufacturers
    const totalManufacturers = data.top_manufacturers?.length || 0;
    animateNumber('total-manufacturers', totalManufacturers);
    
    // Total countries
    const totalCountries = data.by_country?.length || 0;
    animateNumber('total-countries', totalCountries);
    
    // Most valuable
    const mostValuable = data.top_valuable?.[0];
    const mostValuableText = mostValuable ? 
        `${mostValuable.currency}${Math.round(mostValuable.value_mid).toLocaleString()}` : 
        '-';
    document.getElementById('most-valuable').textContent = mostValuableText;
}

/**
 * Animate number counting up
 */
function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const duration = 1000;
    const startTime = performance.now();
    const startValue = 0;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.round(startValue + (targetValue - startValue) * easeOut);
        
        element.textContent = currentValue.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * Initialize Folio Distribution Donut Chart
 */
function initFolioChart(data) {
    const ctx = document.getElementById('folioChart');
    if (!ctx) return;
    
    const folioData = data.by_folio || [];
    const labels = folioData.map(f => `Folio ${f.folio}`);
    const counts = folioData.map(f => f.count);
    const avgValues = folioData.map(f => Math.round(f.avg_value || 0));
    
    charts.folio = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: FOLIO_COLORS.slice(0, folioData.length),
                borderColor: CHART_COLORS.cream,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        font: { family: "'Source Sans Pro', sans-serif", size: 12 },
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value} balls (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Populate folio table
    const tableHtml = `
        <table>
            <thead>
                <tr>
                    <th>Folio</th>
                    <th>Count</th>
                    <th>Avg Value</th>
                    <th>Currency</th>
                </tr>
            </thead>
            <tbody>
                ${folioData.map(f => `
                    <tr>
                        <td>Folio ${f.folio}</td>
                        <td>${f.count.toLocaleString()}</td>
                        <td>${f.currency}${Math.round(f.avg_value || 0).toLocaleString()}</td>
                        <td>${f.currency}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    document.getElementById('folio-table').innerHTML = tableHtml;
}

/**
 * Initialize Timeline Line Chart
 */
function initTimelineChart(data) {
    const ctx = document.getElementById('timelineChart');
    if (!ctx) return;
    
    const eraData = data.by_era || [];
    
    charts.timeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: eraData.map(e => e.era),
            datasets: [{
                label: 'Number of Balls',
                data: eraData.map(e => e.count),
                borderColor: CHART_COLORS.primary,
                backgroundColor: CHART_COLORS.primary + '20',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: CHART_COLORS.gold,
                pointBorderColor: CHART_COLORS.primary,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: { family: "'Source Sans Pro', sans-serif" }
                    },
                    grid: {
                        color: CHART_COLORS.border
                    }
                },
                x: {
                    ticks: {
                        font: { family: "'Source Sans Pro', sans-serif" },
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Initialize Country Bar Chart
 */
function initCountryChart(data) {
    const ctx = document.getElementById('countryChart');
    if (!ctx) return;
    
    // Take top 10 countries
    const countryData = (data.by_country || []).slice(0, 10);
    
    charts.country = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: countryData.map(c => c.country),
            datasets: [{
                label: 'Balls',
                data: countryData.map(c => c.count),
                backgroundColor: CHART_COLORS.folio2,
                borderColor: CHART_COLORS.folio1,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { font: { family: "'Source Sans Pro', sans-serif" } },
                    grid: { color: CHART_COLORS.border }
                },
                x: {
                    ticks: { 
                        font: { family: "'Source Sans Pro', sans-serif", size: 10 },
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Initialize Cover Patterns Horizontal Bar Chart
 */
function initPatternChart(data) {
    const ctx = document.getElementById('patternChart');
    if (!ctx) return;
    
    // Take top 8 patterns
    const patternData = (data.by_pattern || []).slice(0, 8);
    
    charts.pattern = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: patternData.map(p => p.cover_pattern),
            datasets: [{
                label: 'Balls',
                data: patternData.map(p => p.count),
                backgroundColor: CHART_COLORS.folio3,
                borderColor: CHART_COLORS.folio2,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { font: { family: "'Source Sans Pro', sans-serif" } },
                    grid: { color: CHART_COLORS.border }
                },
                y: {
                    ticks: { 
                        font: { family: "'Source Sans Pro', sans-serif", size: 11 }
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Initialize Value Distribution Histogram
 */
function initValueChart(data) {
    const ctx = document.getElementById('valueChart');
    if (!ctx) return;
    
    // Create value ranges from top_valuable data
    const valuableData = data.top_valuable || [];
    const ranges = {
        'Under £100': 0,
        '£100-£500': 0,
        '£500-£1000': 0,
        '£1000-£2000': 0,
        '£2000-£5000': 0,
        'Over £5000': 0
    };
    
    valuableData.forEach(ball => {
        const value = ball.value_mid || 0;
        if (value < 100) ranges['Under £100']++;
        else if (value < 500) ranges['£100-£500']++;
        else if (value < 1000) ranges['£500-£1000']++;
        else if (value < 2000) ranges['£1000-£2000']++;
        else if (value < 5000) ranges['£2000-£5000']++;
        else ranges['Over £5000']++;
    });
    
    const labels = Object.keys(ranges);
    const values = Object.values(ranges);
    
    charts.value = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Balls',
                data: values,
                backgroundColor: [
                    CHART_COLORS.folio4,
                    CHART_COLORS.folio3,
                    CHART_COLORS.folio2,
                    CHART_COLORS.folio1,
                    CHART_COLORS.burgundy,
                    CHART_COLORS.gold
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { font: { family: "'Source Sans Pro', sans-serif" } },
                    grid: { color: CHART_COLORS.border }
                },
                x: {
                    ticks: { 
                        font: { family: "'Source Sans Pro', sans-serif", size: 10 },
                        maxRotation: 45,
                        minRotation: 30
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * Populate manufacturers table
 */
function populateManufacturersTable(data) {
    const tbody = document.getElementById('manufacturers-tbody');
    if (!tbody) return;
    
    const manufacturers = data.top_manufacturers || [];
    const currency = data.by_folio?.[0]?.currency || '£';
    
    if (manufacturers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">No manufacturer data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = manufacturers.slice(0, 10).map(m => `
        <tr>
            <td>${m.manufacturer}</td>
            <td>${m.count}</td>
            <td>${currency}${Math.round(m.avg_value || 0).toLocaleString()}</td>
        </tr>
    `).join('');
}

/**
 * Start rotating interesting facts
 */
function startFactRotation(data) {
    const facts = generateFacts(data);
    const factElement = document.getElementById('rotating-fact');
    if (!factElement || facts.length === 0) return;
    
    let currentIndex = 0;
    factElement.textContent = facts[0];
    
    setInterval(() => {
        currentIndex = (currentIndex + 1) % facts.length;
        // Fade out
        factElement.style.opacity = '0';
        setTimeout(() => {
            factElement.textContent = facts[currentIndex];
            // Fade in
            factElement.style.opacity = '1';
        }, 300);
    }, 8000);
}

/**
 * Generate interesting facts from data
 */
function generateFacts(data) {
    const facts = [];
    const folioData = data.by_folio || [];
    const eraData = data.by_era || [];
    const countryData = data.by_country || [];
    const patternData = data.by_pattern || [];
    const valuableData = data.top_valuable || [];
    
    // Total balls fact
    const totalBalls = folioData.reduce((sum, f) => sum + (f.count || 0), 0);
    facts.push(`The collection contains ${totalBalls.toLocaleString()} antique golf balls across ${folioData.length} folios.`);
    
    // Most common era
    if (eraData.length > 0) {
        const topEra = eraData.reduce((max, e) => e.count > max.count ? e : max, eraData[0]);
        facts.push(`The ${topEra.era} era is the most represented with ${topEra.count} balls.`);
    }
    
    // Most common country
    if (countryData.length > 0) {
        const topCountry = countryData[0];
        facts.push(`${topCountry.country} leads with ${topCountry.count} balls in the collection.`);
    }
    
    // Most common pattern
    if (patternData.length > 0) {
        const topPattern = patternData[0];
        facts.push(`The ${topPattern.cover_pattern} pattern is the most common with ${topPattern.count} examples.`);
    }
    
    // Most valuable
    if (valuableData.length > 0) {
        const mostValuable = valuableData[0];
        const currency = mostValuable.currency || '£';
        facts.push(`The most valuable ball is "${mostValuable.ball_name}" valued at ${currency}${Math.round(mostValuable.value_mid).toLocaleString()}.`);
    }
    
    // Era span
    if (eraData.length > 1) {
        facts.push(`The collection spans from the ${eraData[0].era} to the ${eraData[eraData.length - 1].era}.`);
    }
    
    // Add some general facts
    facts.push('Gutta-percha balls were the standard from 1845 to 1903 before being replaced by rubber-core balls.');
    facts.push('The rarest balls often feature unique hand-hammered patterns or experimental designs.');
    
    return facts;
}

/**
 * Show error message
 */
function showError(message) {
    const container = document.querySelector('.dashboard-container');
    if (container) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = 'background: #f8d7da; color: #721c24; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #f5c6cb;';
        errorDiv.textContent = message;
        container.insertBefore(errorDiv, container.firstChild);
    }
}
