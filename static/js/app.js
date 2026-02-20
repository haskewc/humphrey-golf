document.addEventListener('DOMContentLoaded', function() {
    // Initial load
    searchBalls();
    
    // Enter key on search
    document.getElementById('search-query').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') searchBalls();
    });
});

let currentPage = 1;
let currentFilters = {};

function searchBalls(page = 1) {
    currentPage = page;
    
    const query = document.getElementById('search-query').value;
    const era = document.getElementById('filter-era').value;
    const pattern = document.getElementById('filter-pattern').value;
    const country = document.getElementById('filter-country').value;
    const minValue = document.getElementById('min-value').value;
    const maxValue = document.getElementById('max-value').value;
    
    currentFilters = { query, era, pattern, country, minValue, maxValue };
    
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (era) params.append('era', era);
    if (pattern) params.append('pattern', pattern);
    if (country) params.append('country', country);
    if (minValue) params.append('min_value', minValue);
    if (maxValue) params.append('max_value', maxValue);
    params.append('page', page);
    params.append('per_page', '20');
    
    // Show loading
    document.getElementById('results-container').innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading results...</p>
        </div>
    `;
    
    fetch(`/api/search?${params}`)
        .then(response => response.json())
        .then(data => {
            displayResults(data);
            updatePagination(data);
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('results-container').innerHTML = `
                <div class="loading">
                    <p>Error loading results. Please try again.</p>
                </div>
            `;
        });
}

function displayResults(data) {
    const container = document.getElementById('results-container');
    const countLabel = document.getElementById('results-count');
    
    countLabel.textContent = `${data.total} results`;
    
    if (data.results.length === 0) {
        container.innerHTML = `
            <div class="loading">
                <p>No results found. Try adjusting your filters.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = data.results.map(ball => `
        <div class="card" onclick="viewDetail(${ball.record_no})">
            <div class="card-header">
                <h4>${escapeHtml(ball.ball_name)}</h4>
                <span class="card-era">${ball.era || 'Unknown era'}</span>
            </div>
            <div class="card-body">
                <div class="card-row">
                    <span class="card-label">Pattern</span>
                    <span class="card-value">${ball.cover_pattern || 'N/A'}</span>
                </div>
                <div class="card-row">
                    <span class="card-label">Manufacturer</span>
                    <span class="card-value">${formatManufacturer(ball.manufacturer)}</span>
                </div>
                <div class="card-row">
                    <span class="card-label">Country</span>
                    <span class="card-value">${ball.country || 'Unknown'}</span>
                </div>
                <div class="card-row">
                    <span class="card-label">Estimated Value</span>
                    <span class="card-value price">$${ball.value_mid ? ball.value_mid.toLocaleString() : 'N/A'}</span>
                </div>
            </div>
            <div class="card-footer">
                <span class="rarity-badge ${getRarityClass(ball.rarity_score)}">
                    ${getRarityLabel(ball.rarity_score)}
                </span>
            </div>
        </div>
    `).join('');
}

function updatePagination(data) {
    const container = document.getElementById('pagination');
    const totalPages = data.pages;
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous
    html += `<button onclick="searchBalls(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>`;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<button onclick="searchBalls(1)">1</button>`;
        if (startPage > 2) html += `<span>...</span>`;
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button onclick="searchBalls(${i})" class="${i === currentPage ? 'active' : ''}">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span>...</span>`;
        html += `<button onclick="searchBalls(${totalPages})">${totalPages}</button>`;
    }
    
    // Next
    html += `<button onclick="searchBalls(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>`;
    
    container.innerHTML = html;
}

function resetFilters() {
    document.getElementById('search-query').value = '';
    document.getElementById('filter-era').value = '';
    document.getElementById('filter-pattern').value = '';
    document.getElementById('filter-country').value = '';
    document.getElementById('min-value').value = '';
    document.getElementById('max-value').value = '';
    searchBalls(1);
}

function viewDetail(recordNo) {
    window.location.href = `/ball/${recordNo}`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatManufacturer(manufacturer) {
    if (!manufacturer) return 'Unknown';
    if (manufacturer.length > 40) {
        return manufacturer.substring(0, 40) + '...';
    }
    return manufacturer;
}

function getRarityClass(score) {
    if (score >= 6) return 'rarity-legendary';
    if (score >= 5) return 'rarity-epic';
    if (score >= 4) return 'rarity-rare';
    if (score >= 3) return 'rarity-uncommon';
    return 'rarity-common';
}

function getRarityLabel(score) {
    if (score >= 6) return 'Legendary';
    if (score >= 5) return 'Epic';
    if (score >= 4) return 'Rare';
    if (score >= 3) return 'Uncommon';
    return 'Common';
}
