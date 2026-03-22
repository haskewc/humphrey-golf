/* ============================================
   Modern Collection - Interactive Browse
   ============================================ */

const RARITY_LABELS = {
  1: 'Common', 2: 'Uncommon', 3: 'Rare',
  4: 'Very Rare', 5: 'Epic', 6: 'Legendary'
};

const FOLIO_LABELS = {
  1: 'I — Gutta-Percha',
  2: 'II — Rubber-Core',
  3: 'III — Wound',
  4: 'IV — Post-War'
};

let currentPage = 1;
let currentView = 'grid';
let totalResults = 0;
let totalPages = 0;

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
  initFolioTabs();
  initSearchDebounce();
  applyFilters();
});

// --- Folio Tab Clicks ---
function initFolioTabs() {
  document.querySelectorAll('.folio-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.folio-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentPage = 1;
      applyFilters();
    });
  });
}

// --- Search Debounce ---
function initSearchDebounce() {
  let timeout;
  document.getElementById('searchInput').addEventListener('input', () => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      currentPage = 1;
      applyFilters();
    }, 350);
  });
}

// --- Build Query Params ---
function getFilterParams() {
  const sortVal = document.getElementById('sortSelect').value.split('-');
  const activeFolio = document.querySelector('.folio-tab.active');

  return {
    q: document.getElementById('searchInput').value.trim(),
    folio: activeFolio ? activeFolio.dataset.folio : '',
    era: document.getElementById('eraSelect').value,
    pattern: document.getElementById('patternSelect').value,
    country: document.getElementById('countrySelect').value,
    min_value: document.getElementById('minValue').value,
    max_value: document.getElementById('maxValue').value,
    rarity: document.getElementById('raritySelect').value,
    sort: sortVal[0],
    order: sortVal[1] || 'DESC',
    page: currentPage,
    per_page: 24
  };
}

// --- Apply Filters ---
async function applyFilters() {
  const params = getFilterParams();
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v) qs.set(k, v); });

  renderActiveChips(params);
  showLoading();

  try {
    const resp = await fetch('/api/search?' + qs.toString());
    const data = await resp.json();
    totalResults = data.total;
    totalPages = data.pages;
    currentPage = data.page;
    renderResults(data.results, data.total);
    renderPagination();
  } catch (err) {
    document.getElementById('ballsGrid').innerHTML =
      '<div class="empty-state"><h3>Error loading results</h3><p>Please try again.</p></div>';
  }
}

// --- Loading State ---
function showLoading() {
  document.getElementById('ballsGrid').innerHTML =
    '<div class="loading-overlay"><div class="spinner"></div> Searching...</div>';
}

// --- Render Results ---
function renderResults(results, total) {
  const grid = document.getElementById('ballsGrid');
  const countEl = document.getElementById('resultsCount');

  countEl.innerHTML = `Showing <strong>${results.length}</strong> of <strong>${total.toLocaleString()}</strong> balls`;

  if (results.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
        </svg>
        <h3>No balls found</h3>
        <p>Try adjusting your filters or search terms.</p>
      </div>`;
    return;
  }

  grid.className = currentView === 'list' ? 'balls-grid list-view' : 'balls-grid';

  grid.innerHTML = results.map(ball => {
    const value = ball.value_mid
      ? `${ball.currency === 'GBP' ? '£' : '$'}${ball.value_mid.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}`
      : null;
    const rarityLabel = RARITY_LABELS[ball.rarity_score] || '';
    const folioLabel = FOLIO_LABELS[ball.folio] || `Folio ${ball.folio}`;

    return `
      <a class="ball-card" href="/ball/${ball.record_no}">
        <div class="ball-card-header folio-${ball.folio}">
          <div class="ball-folio">${folioLabel}</div>
          <div class="ball-name">${escapeHtml(ball.ball_name || 'Unknown')}</div>
        </div>
        <div class="ball-card-body">
          <div class="ball-card-row">
            <span class="row-label">Era</span>
            <span class="row-value">${escapeHtml(ball.era || '—')}</span>
          </div>
          <div class="ball-card-row">
            <span class="row-label">Pattern</span>
            <span class="row-value">${escapeHtml(ball.cover_pattern || '—')}</span>
          </div>
          <div class="ball-card-row">
            <span class="row-label">Country</span>
            <span class="row-value">${escapeHtml(ball.country || '—')}</span>
          </div>
        </div>
        <div class="ball-card-footer">
          <span class="ball-value ${value ? '' : 'no-value'}">${value || 'No valuation'}</span>
          ${rarityLabel ? `<span class="rarity-badge rarity-${ball.rarity_score}">${rarityLabel}</span>` : ''}
        </div>
      </a>`;
  }).join('');
}

// --- Render Active Filter Chips ---
function renderActiveChips(params) {
  const container = document.getElementById('activeFilters');
  const chips = [];

  if (params.q) chips.push({ label: `Search: "${params.q}"`, clear: () => { document.getElementById('searchInput').value = ''; }});
  if (params.era) chips.push({ label: `Era: ${params.era}`, clear: () => { document.getElementById('eraSelect').value = ''; }});
  if (params.pattern) chips.push({ label: `Pattern: ${params.pattern}`, clear: () => { document.getElementById('patternSelect').value = ''; }});
  if (params.country) chips.push({ label: `Country: ${params.country}`, clear: () => { document.getElementById('countrySelect').value = ''; }});
  if (params.rarity) chips.push({ label: `Rarity: ${RARITY_LABELS[params.rarity]}`, clear: () => { document.getElementById('raritySelect').value = ''; }});
  if (params.min_value) chips.push({ label: `Min: ${params.min_value}`, clear: () => { document.getElementById('minValue').value = ''; }});
  if (params.max_value) chips.push({ label: `Max: ${params.max_value}`, clear: () => { document.getElementById('maxValue').value = ''; }});

  container.innerHTML = chips.map((chip, i) =>
    `<span class="filter-chip">${escapeHtml(chip.label)}<button data-idx="${i}">&times;</button></span>`
  ).join('');

  container.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.dataset.idx);
      chips[idx].clear();
      currentPage = 1;
      applyFilters();
    });
  });
}

// --- Pagination ---
function renderPagination() {
  const container = document.getElementById('pagination');
  if (totalPages <= 1) { container.innerHTML = ''; return; }

  let html = '';
  html += `<button ${currentPage <= 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">&lsaquo;</button>`;

  const range = getPageRange(currentPage, totalPages);
  for (const p of range) {
    if (p === '...') {
      html += '<span class="page-ellipsis">...</span>';
    } else {
      html += `<button class="${p === currentPage ? 'active' : ''}" onclick="goToPage(${p})">${p}</button>`;
    }
  }

  html += `<button ${currentPage >= totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">&rsaquo;</button>`;
  container.innerHTML = html;
}

function getPageRange(current, total) {
  if (total <= 7) return Array.from({length: total}, (_, i) => i + 1);
  const pages = [];
  if (current <= 3) {
    pages.push(1, 2, 3, 4, '...', total);
  } else if (current >= total - 2) {
    pages.push(1, '...', total - 3, total - 2, total - 1, total);
  } else {
    pages.push(1, '...', current - 1, current, current + 1, '...', total);
  }
  return pages;
}

function goToPage(page) {
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  applyFilters();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// --- View Toggle ---
function setView(view) {
  currentView = view;
  document.getElementById('gridViewBtn').classList.toggle('active', view === 'grid');
  document.getElementById('listViewBtn').classList.toggle('active', view === 'list');
  const grid = document.getElementById('ballsGrid');
  grid.className = view === 'list' ? 'balls-grid list-view' : 'balls-grid';
}

// --- Reset Filters ---
function resetFilters() {
  document.getElementById('searchInput').value = '';
  document.getElementById('eraSelect').value = '';
  document.getElementById('patternSelect').value = '';
  document.getElementById('countrySelect').value = '';
  document.getElementById('raritySelect').value = '';
  document.getElementById('minValue').value = '';
  document.getElementById('maxValue').value = '';
  document.getElementById('sortSelect').value = 'value_mid-DESC';
  document.querySelectorAll('.folio-tab').forEach(t => t.classList.remove('active'));
  document.querySelector('.folio-tab[data-folio=""]').classList.add('active');
  currentPage = 1;
  applyFilters();
}

// --- Escape HTML ---
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
