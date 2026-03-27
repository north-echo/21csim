// about.js -- Interactive node catalog for the About page

let allNodes = [];
let filteredNodes = [];

const STATUS_COLORS = {
  HISTORICAL:  'var(--status-historical)',
  DIVERGENCE:  'var(--status-divergence)',
  ESCALATED:   'var(--status-escalated)',
  PREVENTED:   'var(--status-prevented)',
  ACCELERATED: 'var(--status-accelerated)',
  DELAYED:     'var(--status-delayed)',
  DIMINISHED:  'var(--status-diminished)',
};

// ── Load catalog ──────────────────────────────────────────────

async function loadCatalog() {
  try {
    const resp = await fetch('nodes-catalog.json');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    allNodes = await resp.json();
    initFilters();
    applyFilters();
  } catch (err) {
    document.getElementById('node-list').innerHTML =
      `<div style="color:var(--status-escalated); text-align:center; padding:40px; font-family:var(--font-ui);">
        Failed to load node catalog: ${err.message}<br>
        <span style="color:var(--text-dim); font-size:12px;">Run the catalog generation script first.</span>
      </div>`;
  }
}

// ── Build filter dropdowns ────────────────────────────────────

function initFilters() {
  const domains = [...new Set(allNodes.map(n => n.domain).filter(Boolean))].sort();
  const decades = [...new Set(allNodes.map(n => {
    const y = extractYear(n.year_month);
    return y ? `${Math.floor(y / 10) * 10}s` : null;
  }).filter(Boolean))].sort();
  const confidences = [...new Set(allNodes.map(n => n.confidence).filter(Boolean))].sort();

  const domSel = document.getElementById('filter-domain');
  domains.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = d;
    domSel.appendChild(opt);
  });

  const decSel = document.getElementById('filter-decade');
  decades.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = d;
    decSel.appendChild(opt);
  });

  const confSel = document.getElementById('filter-confidence');
  confidences.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c;
    confSel.appendChild(opt);
  });

  // Bind events
  document.getElementById('catalog-search').addEventListener('input', applyFilters);
  domSel.addEventListener('change', applyFilters);
  decSel.addEventListener('change', applyFilters);
  confSel.addEventListener('change', applyFilters);
}

function extractYear(ym) {
  if (!ym) return null;
  const str = String(ym);
  const m = str.match(/^(\d{4})/);
  return m ? parseInt(m[1], 10) : null;
}

// ── Filter logic ──────────────────────────────────────────────

function applyFilters() {
  const query = (document.getElementById('catalog-search').value || '').toLowerCase().trim();
  const domain = document.getElementById('filter-domain').value;
  const decade = document.getElementById('filter-decade').value;
  const confidence = document.getElementById('filter-confidence').value;

  filteredNodes = allNodes.filter(node => {
    if (domain && node.domain !== domain) return false;
    if (confidence && node.confidence !== confidence) return false;
    if (decade) {
      const y = extractYear(node.year_month);
      const nodeDec = y ? `${Math.floor(y / 10) * 10}s` : '';
      if (nodeDec !== decade) return false;
    }
    if (query) {
      const haystack = `${node.id} ${node.title} ${node.description}`.toLowerCase();
      if (!haystack.includes(query)) return false;
    }
    return true;
  });

  renderNodeList();
}

// ── Render ────────────────────────────────────────────────────

function renderNodeList() {
  const container = document.getElementById('node-list');
  const countEl = document.getElementById('catalog-count');
  countEl.textContent = `${filteredNodes.length} / ${allNodes.length} nodes`;

  if (filteredNodes.length === 0) {
    container.innerHTML =
      `<div style="color:var(--text-dim); text-align:center; padding:40px; font-family:var(--font-ui);">
        No nodes match the current filters.
      </div>`;
    return;
  }

  container.innerHTML = filteredNodes.map(node => {
    const year = extractYear(node.year_month) || '????';
    return `
      <div class="node-item" data-id="${node.id}">
        <div class="node-header" onclick="window.__toggleNode('${node.id}')">
          <span class="node-year">${year}</span>
          <span class="node-title">${esc(node.title || node.id)}</span>
          <span class="node-domain-tag">${esc(node.domain || '')}</span>
          <span class="node-confidence-tag">${esc(node.confidence || '')}</span>
          <span class="node-expand-icon">&#9654;</span>
        </div>
        <div class="node-detail">
          ${renderNodeDetail(node)}
        </div>
      </div>`;
  }).join('');
}

function renderNodeDetail(node) {
  let html = '';

  // Description
  if (node.description) {
    html += `<div class="node-description">${esc(node.description)}</div>`;
  }

  // Meta row
  html += `<div class="node-meta-row">`;
  html += `<span>ID: <code style="font-size:11px; color:var(--accent)">${esc(node.id)}</code></span>`;
  if (node.year_month) html += `<span>Date: ${esc(String(node.year_month))}</span>`;
  if (node.domain) html += `<span>Domain: ${esc(node.domain)}</span>`;
  if (node.confidence) html += `<span>Confidence: ${esc(node.confidence)}</span>`;
  html += `</div>`;

  // Branches
  if (node.branches && node.branches.length > 0) {
    html += `<div class="branches-label">Branches</div>`;
    html += `<div class="branch-list">`;
    node.branches.forEach(b => {
      const statusColor = STATUS_COLORS[b.status] || 'var(--text-dim)';
      const probPct = typeof b.probability === 'number' ? (b.probability * 100).toFixed(1) + '%' : '?';
      html += `
        <div class="branch-row" data-status="${esc(b.status || '')}">
          <span class="branch-name">${esc(b.name)}</span>
          <span class="branch-prob">${probPct}</span>
          <span class="branch-status" style="color:${statusColor}">${esc(b.status || '')}</span>
          <span class="branch-desc">${esc(b.description || '')}</span>
        </div>`;
    });
    html += `</div>`;
  }

  // Dependencies mini-graph
  if (node.dependencies && node.dependencies.length > 0) {
    html += `<div class="deps-section">`;
    html += `<div class="deps-label">Dependencies</div>`;
    html += `<div class="deps-graph">`;
    node.dependencies.forEach(dep => {
      html += `<span class="dep-node" onclick="window.__scrollToNode('${esc(dep)}')" title="Click to find ${esc(dep)}">${esc(dep)}</span>`;
      html += `<span class="dep-arrow">&rarr;</span>`;
    });
    html += `<span class="dep-target">${esc(node.id)}</span>`;
    html += `</div></div>`;
  }

  // Conditional
  if (node.conditional) {
    const cond = node.conditional;
    let condText = '';
    if (typeof cond === 'string') {
      condText = cond;
    } else if (typeof cond === 'object') {
      condText = `Requires ${cond.node || '?'} = ${cond.branch || cond.outcome || '?'}`;
    }
    if (condText) {
      html += `<div class="conditional-note">Conditional: ${esc(condText)}</div>`;
    }
  }

  return html;
}

// ── Interaction ───────────────────────────────────────────────

window.__toggleNode = function(id) {
  const el = document.querySelector(`.node-item[data-id="${id}"]`);
  if (el) el.classList.toggle('expanded');
};

window.__scrollToNode = function(id) {
  // Clear filters to ensure the node is visible
  document.getElementById('catalog-search').value = id;
  document.getElementById('filter-domain').value = '';
  document.getElementById('filter-decade').value = '';
  document.getElementById('filter-confidence').value = '';
  applyFilters();

  // Expand and scroll
  requestAnimationFrame(() => {
    const el = document.querySelector(`.node-item[data-id="${id}"]`);
    if (el) {
      el.classList.add('expanded');
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
};

// ── Utility ───────────────────────────────────────────────────

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ── Init ──────────────────────────────────────────────────────

loadCatalog();
