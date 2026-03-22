/* ============================================
   Modern Analytics Dashboard
   ============================================ */

// Color palette
const COLORS = {
  green: { bg: 'rgba(45, 148, 97, 0.15)', border: '#2d9461', solid: '#1f6042' },
  gold: { bg: 'rgba(200, 169, 81, 0.15)', border: '#c8a951', solid: '#9a7b2d' },
  blue: { bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6', solid: '#2563eb' },
  purple: { bg: 'rgba(139, 92, 246, 0.15)', border: '#8b5cf6', solid: '#7c3aed' },
  rose: { bg: 'rgba(244, 63, 94, 0.15)', border: '#f43f5e', solid: '#e11d48' },
  amber: { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', solid: '#d97706' },
  teal: { bg: 'rgba(20, 184, 166, 0.15)', border: '#14b8a6', solid: '#0d9488' },
  slate: { bg: 'rgba(100, 116, 139, 0.15)', border: '#94a3b8', solid: '#64748b' }
};

const PALETTE = [
  COLORS.green, COLORS.gold, COLORS.blue, COLORS.purple,
  COLORS.rose, COLORS.amber, COLORS.teal, COLORS.slate
];

const FOLIO_COLORS = [
  { bg: '#1f6042', border: '#1a4a35', label: 'Folio I — Gutta-Percha' },
  { bg: '#c8a951', border: '#9a7b2d', label: 'Folio II — Rubber-Core' },
  { bg: '#3b82f6', border: '#2563eb', label: 'Folio III — Wound' },
  { bg: '#8b5cf6', border: '#7c3aed', label: 'Folio IV — Post-War' }
];

// Chart.js defaults
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748b';
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyle = 'circle';
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.plugins.tooltip.backgroundColor = '#1e293b';
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.titleFont = { weight: '600' };

let dashboardData = null;
let insightIndex = 0;

// --- Init ---
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const [statsResp, extraResp] = await Promise.all([
      fetch('/api/dashboard/stats'),
      fetch('/api/analytics/extra')
    ]);
    dashboardData = await statsResp.json();
    const extraData = await extraResp.json();
    Object.assign(dashboardData, extraData);

    renderKPIs();
    renderFolioComparison();
    renderInsights();
    renderTimelineChart();
    renderCountryChart();
    renderPatternChart();
    renderValueChart();
    renderRarityChart();
    renderScatterChart();
    renderFolioDonutChart();
    renderManufacturerTable();
    renderTopValuable();
    renderCountryValueChart();
    renderPatternFolioChart();
  } catch (err) {
    console.error('Dashboard load error:', err);
  }
});

// --- KPIs ---
function renderKPIs() {
  const d = dashboardData;
  animateCount('kpiTotal', d.total_balls);
  animateCount('kpiManufacturers', d.total_manufacturers);
  animateCount('kpiCountries', d.total_countries);

  const mv = d.most_valuable;
  const sym = mv.currency === 'GBP' ? '£' : '$';
  document.getElementById('kpiMostValuable').textContent = `${sym}${Math.round(mv.value).toLocaleString()}`;
  document.getElementById('kpiMostValuableName').textContent = mv.ball_name;
}

function animateCount(id, target) {
  const el = document.getElementById(id);
  const duration = 1200;
  const start = performance.now();

  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(eased * target).toLocaleString();
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// --- Folio Comparison Cards ---
function renderFolioComparison() {
  const container = document.getElementById('folioComparison');
  const folios = dashboardData.by_folio;
  const maxCount = Math.max(...folios.map(f => f.count));
  const colors = ['green', 'gold', 'blue', 'purple'];

  container.innerHTML = folios.map((f, i) => {
    const sym = f.currency === 'GBP' ? '£' : '$';
    const pct = Math.round((f.count / maxCount) * 100);
    return `
      <div class="comparison-card">
        <h4>${FOLIO_COLORS[i]?.label || 'Folio ' + f.folio}</h4>
        <div class="comp-value">${f.count.toLocaleString()}</div>
        <div class="comp-sub">balls &middot; avg ${sym}${Math.round(f.avg_value).toLocaleString()} &middot; max ${sym}${Math.round(f.max_value).toLocaleString()}</div>
        <div class="comp-bar"><div class="comp-bar-fill ${colors[i]}" style="width:${pct}%"></div></div>
      </div>`;
  }).join('');
}

// --- Insights Rotation ---
function renderInsights() {
  const facts = dashboardData.interesting_facts || [];
  if (facts.length === 0) return;
  const el = document.getElementById('insightText');
  el.textContent = facts[0];
  setInterval(() => {
    insightIndex = (insightIndex + 1) % facts.length;
    el.style.opacity = 0;
    setTimeout(() => {
      el.textContent = facts[insightIndex];
      el.style.opacity = 1;
    }, 300);
  }, 6000);
  el.style.transition = 'opacity 0.3s ease';
}

// --- Timeline Chart ---
function renderTimelineChart() {
  const timeline = dashboardData.timeline;
  if (!timeline || timeline.length === 0) return;

  const labels = timeline.map(t => t.year);
  const datasets = FOLIO_COLORS.map((fc, i) => ({
    label: fc.label,
    data: timeline.map(t => t[`folio_${i + 1}`] || 0),
    borderColor: fc.bg,
    backgroundColor: fc.bg + '33',
    fill: true,
    tension: 0.35,
    pointRadius: 0,
    pointHoverRadius: 5,
    borderWidth: 2
  }));

  new Chart(document.getElementById('timelineChart'), {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            title: (items) => `Year: ${items[0].label}`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { maxTicksLimit: 15 }
        },
        y: {
          beginAtZero: true,
          grid: { color: '#f1f5f9' },
          ticks: { precision: 0 }
        }
      }
    }
  });
}

// --- Country Chart ---
function renderCountryChart() {
  const countries = dashboardData.by_country;
  if (!countries) return;

  new Chart(document.getElementById('countryChart'), {
    type: 'bar',
    data: {
      labels: countries.map(c => `${c.flag} ${c.country}`),
      datasets: [{
        label: 'Ball Count',
        data: countries.map(c => c.count),
        backgroundColor: PALETTE.map(p => p.bg),
        borderColor: PALETTE.map(p => p.border),
        borderWidth: 1.5,
        borderRadius: 6,
        barPercentage: 0.7
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, grid: { color: '#f1f5f9' } },
        y: { grid: { display: false } }
      }
    }
  });
}

// --- Pattern Chart ---
function renderPatternChart() {
  const patterns = dashboardData.by_pattern;
  if (!patterns) return;

  new Chart(document.getElementById('patternChart'), {
    type: 'bar',
    data: {
      labels: patterns.map(p => p.pattern),
      datasets: [{
        label: 'Count',
        data: patterns.map(p => p.count),
        backgroundColor: COLORS.green.bg,
        borderColor: COLORS.green.border,
        borderWidth: 1.5,
        borderRadius: 6,
        barPercentage: 0.7
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, grid: { color: '#f1f5f9' } },
        y: { grid: { display: false }, ticks: { font: { size: 11 } } }
      }
    }
  });
}

// --- Value Distribution Chart ---
function renderValueChart() {
  const ranges = dashboardData.by_value_range;
  if (!ranges) return;

  new Chart(document.getElementById('valueChart'), {
    type: 'bar',
    data: {
      labels: ranges.map(r => r.range),
      datasets: [{
        label: 'Ball Count',
        data: ranges.map(r => r.count),
        backgroundColor: [
          COLORS.green.bg, COLORS.teal.bg, COLORS.blue.bg,
          COLORS.gold.bg, COLORS.amber.bg
        ],
        borderColor: [
          COLORS.green.border, COLORS.teal.border, COLORS.blue.border,
          COLORS.gold.border, COLORS.amber.border
        ],
        borderWidth: 1.5,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
        x: { grid: { display: false } }
      }
    }
  });
}

// --- Rarity Chart ---
function renderRarityChart() {
  const rarity = dashboardData.by_rarity;
  if (!rarity) return;

  const labels = ['Common', 'Uncommon', 'Rare', 'Very Rare', 'Epic', 'Legendary'];
  const rarityColors = ['#10b981', '#22c55e', '#eab308', '#f59e0b', '#ec4899', '#8b5cf6'];

  new Chart(document.getElementById('rarityChart'), {
    type: 'doughnut',
    data: {
      labels: rarity.map((r, i) => labels[i] || `Score ${r.rarity_score}`),
      datasets: [{
        data: rarity.map(r => r.count),
        backgroundColor: rarityColors.slice(0, rarity.length).map(c => c + '22'),
        borderColor: rarityColors.slice(0, rarity.length),
        borderWidth: 2,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '55%',
      plugins: {
        legend: { position: 'right' }
      }
    }
  });
}

// --- Scatter: Value vs Era ---
function renderScatterChart() {
  const scatter = dashboardData.scatter_data;
  if (!scatter) return;

  const dataByFolio = {};
  scatter.forEach(pt => {
    const key = pt.folio;
    if (!dataByFolio[key]) dataByFolio[key] = [];
    dataByFolio[key].push({ x: pt.era_start, y: pt.value_mid });
  });

  const datasets = Object.keys(dataByFolio).map(folio => {
    const fi = parseInt(folio) - 1;
    return {
      label: FOLIO_COLORS[fi]?.label || `Folio ${folio}`,
      data: dataByFolio[folio],
      backgroundColor: (FOLIO_COLORS[fi]?.bg || '#999') + '88',
      borderColor: FOLIO_COLORS[fi]?.bg || '#999',
      pointRadius: 3,
      pointHoverRadius: 6
    };
  });

  new Chart(document.getElementById('scatterChart'), {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        x: {
          title: { display: true, text: 'Year' },
          grid: { color: '#f1f5f9' }
        },
        y: {
          title: { display: true, text: 'Value' },
          beginAtZero: true,
          grid: { color: '#f1f5f9' },
          ticks: {
            callback: v => v >= 1000 ? (v / 1000) + 'k' : v
          }
        }
      }
    }
  });
}

// --- Folio Donut ---
function renderFolioDonutChart() {
  const folios = dashboardData.by_folio;
  if (!folios) return;

  new Chart(document.getElementById('folioDonutChart'), {
    type: 'doughnut',
    data: {
      labels: folios.map((f, i) => FOLIO_COLORS[i]?.label || `Folio ${f.folio}`),
      datasets: [{
        data: folios.map(f => f.count),
        backgroundColor: FOLIO_COLORS.map(c => c.bg + 'cc'),
        borderColor: FOLIO_COLORS.map(c => c.border),
        borderWidth: 2,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '60%',
      plugins: {
        legend: { position: 'right' },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = ((ctx.raw / total) * 100).toFixed(1);
              return ` ${ctx.raw.toLocaleString()} balls (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

// --- Manufacturer Table ---
function renderManufacturerTable() {
  const mfrs = dashboardData.top_manufacturers;
  if (!mfrs) return;

  const tbody = document.querySelector('#manufacturerTable tbody');
  tbody.innerHTML = mfrs.map((m, i) => `
    <tr>
      <td class="rank-cell">${i + 1}</td>
      <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeAttr(m.name)}">${escapeHtml(m.name)}</td>
      <td class="fw-600">${m.count}</td>
      <td>${escapeHtml(m.country)}</td>
    </tr>
  `).join('');
}

// --- Top Valuable ---
function renderTopValuable() {
  const top = dashboardData.top_valuable;
  if (!top) return;

  const container = document.getElementById('topValuableList');
  container.innerHTML = top.map((ball, i) => {
    const sym = ball.currency === 'GBP' ? '£' : '$';
    return `
      <div class="top-list-item">
        <div class="rank">${i + 1}</div>
        <div class="item-info">
          <div class="item-name">${escapeHtml(ball.ball_name)}</div>
          <div class="item-meta">${escapeHtml(ball.era || '')} &middot; Folio ${ball.folio}</div>
        </div>
        <div class="item-value">${sym}${Math.round(ball.value_mid).toLocaleString()}</div>
      </div>`;
  }).join('');
}

// --- Country Value Chart ---
function renderCountryValueChart() {
  const data = dashboardData.country_avg_value;
  if (!data) return;

  new Chart(document.getElementById('countryValueChart'), {
    type: 'bar',
    data: {
      labels: data.map(d => d.country),
      datasets: [{
        label: 'Average Value',
        data: data.map(d => Math.round(d.avg_value)),
        backgroundColor: COLORS.gold.bg,
        borderColor: COLORS.gold.border,
        borderWidth: 1.5,
        borderRadius: 6,
        barPercentage: 0.65
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: '#f1f5f9' },
          ticks: { callback: v => v >= 1000 ? (v / 1000) + 'k' : v }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

// --- Pattern by Folio Stacked Bar ---
function renderPatternFolioChart() {
  const data = dashboardData.pattern_by_folio;
  if (!data) return;

  const patterns = [...new Set(data.map(d => d.pattern))];
  const folioNums = [1, 2, 3, 4];

  const datasets = folioNums.map((f, i) => ({
    label: FOLIO_COLORS[i]?.label || `Folio ${f}`,
    data: patterns.map(p => {
      const entry = data.find(d => d.pattern === p && d.folio === f);
      return entry ? entry.count : 0;
    }),
    backgroundColor: FOLIO_COLORS[i]?.bg + 'aa',
    borderColor: FOLIO_COLORS[i]?.border,
    borderWidth: 1
  }));

  new Chart(document.getElementById('patternFolioChart'), {
    type: 'bar',
    data: { labels: patterns, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        x: { stacked: true, grid: { display: false }, ticks: { font: { size: 10 }, maxRotation: 45 } },
        y: { stacked: true, beginAtZero: true, grid: { color: '#f1f5f9' } }
      }
    }
  });
}

// --- Helpers ---
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function escapeAttr(text) {
  if (!text) return '';
  return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
