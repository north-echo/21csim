// explore.js -- Explorer / Analytics for 21csim
// ES module -- loaded by explore.html

const VERDICT_COLORS = {
  'GOLDEN-AGE':          '#ffd700',
  'PROGRESS':            '#40c040',
  'MUDDLING-THROUGH':    '#c0c040',
  'DECLINE':             '#ff8040',
  'CATASTROPHE':         '#ff4040',
  'EXTINCTION':          '#ff0000',
  'TRANSCENDENCE':       '#c040ff',
  'RADICALLY-DIFFERENT': '#ff40ff',
};

const VERDICT_ORDER = [
  'TRANSCENDENCE', 'GOLDEN-AGE', 'PROGRESS', 'MUDDLING-THROUGH',
  'DECLINE', 'CATASTROPHE', 'EXTINCTION', 'RADICALLY-DIFFERENT',
];

// Dimensions for fan charts -- label, key, higher-is-good
const FAN_DIMENSIONS = [
  { key: 'climate_temp_anomaly',    label: 'Climate Temp Anomaly (C)',  goodDir: -1 },
  { key: 'us_polarization',         label: 'US Polarization',           goodDir: -1 },
  { key: 'nuclear_risk_level',      label: 'Nuclear Risk Level',        goodDir: -1 },
  { key: 'global_democracy_index',  label: 'Global Democracy Index',    goodDir:  1 },
  { key: 'renewable_energy_share',  label: 'Renewable Energy Share',    goodDir:  1 },
  { key: 'inequality_index',        label: 'Inequality Index',          goodDir: -1 },
];

// ── State ──
let indexData = [];         // run summaries from index.json
let allRuns = [];           // fully loaded run data
let allRunsLoaded = false;
let activeFilters = [];     // [{nodeId, branch}]

// ── Boot ──
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('/runs/index.json');
    indexData = await res.json();
  } catch (e) {
    console.error('Failed to load index.json', e);
    indexData = [];
  }
  renderOverview(indexData);
  renderSeedGrid(indexData);
  setupLoadButton();
});

// ════════════════════════════════════════════════════════════════
// Section 1 -- Corpus Overview
// ════════════════════════════════════════════════════════════════
function renderOverview(data) {
  if (data.length === 0) {
    document.getElementById('overview-stats').innerHTML =
      '<div class="section-placeholder">No runs found. Generate runs first.</div>';
    return;
  }

  const scores = data.map(d => d.composite_score).sort((a, b) => a - b);
  const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
  const median = scores[Math.floor(scores.length / 2)];

  // Outcome counts
  const counts = {};
  for (const d of data) {
    counts[d.outcome_class] = (counts[d.outcome_class] || 0) + 1;
  }
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const mostCommon = sorted[0];
  const rarest = sorted[sorted.length - 1];

  // Stats cards
  document.getElementById('overview-stats').innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Total Runs</div>
      <div class="stat-value">${data.length}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Mean Score</div>
      <div class="stat-value">${mean >= 0 ? '+' : ''}${mean.toFixed(4)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Median Score</div>
      <div class="stat-value">${median >= 0 ? '+' : ''}${median.toFixed(4)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Most Common</div>
      <div class="stat-value" style="font-size:14px; color:${VERDICT_COLORS[mostCommon[0]] || '#888'}">${mostCommon[0]}</div>
      <div class="stat-sub">${mostCommon[1]} runs (${(mostCommon[1] / data.length * 100).toFixed(1)}%)</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Rarest</div>
      <div class="stat-value" style="font-size:14px; color:${VERDICT_COLORS[rarest[0]] || '#888'}">${rarest[0]}</div>
      <div class="stat-sub">${rarest[1]} runs (${(rarest[1] / data.length * 100).toFixed(1)}%)</div>
    </div>
  `;

  // Outcome distribution bar
  renderOutcomeBar(data, counts);

  // Histogram
  renderHistogram(scores);
}

function renderOutcomeBar(data, counts) {
  const area = document.getElementById('outcome-bar-area');
  const total = data.length;

  let barHtml = '<div class="outcome-bar">';
  let legendHtml = '<div class="outcome-legend">';

  for (const oc of VERDICT_ORDER) {
    const n = counts[oc] || 0;
    if (n === 0) continue;
    const pct = (n / total * 100);
    const color = VERDICT_COLORS[oc] || '#888';
    barHtml += `<div class="segment" style="width:${pct}%; background:${color};" title="${oc}: ${n} (${pct.toFixed(1)}%)">${pct >= 5 ? n : ''}</div>`;
    legendHtml += `<div class="legend-item"><div class="legend-swatch" style="background:${color};"></div>${oc} (${n})</div>`;
  }

  barHtml += '</div>';
  legendHtml += '</div>';
  area.innerHTML = barHtml + legendHtml;
}

function renderHistogram(scores) {
  const canvas = document.getElementById('histogram-canvas');
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 160 * dpr;
  ctx.scale(dpr, dpr);
  const W = rect.width;
  const H = 160;

  if (scores.length === 0) return;

  const min = scores[0];
  const max = scores[scores.length - 1];
  const range = max - min || 1;
  const bins = 30;
  const binW = range / bins;
  const buckets = new Array(bins).fill(0);

  for (const s of scores) {
    let idx = Math.floor((s - min) / binW);
    if (idx >= bins) idx = bins - 1;
    buckets[idx]++;
  }

  const maxCount = Math.max(...buckets);
  const pad = { top: 10, bottom: 30, left: 10, right: 10 };
  const chartW = W - pad.left - pad.right;
  const chartH = H - pad.top - pad.bottom;
  const barWidth = chartW / bins;

  ctx.clearRect(0, 0, W, H);

  // Bars
  for (let i = 0; i < bins; i++) {
    const x = pad.left + i * barWidth;
    const h = maxCount > 0 ? (buckets[i] / maxCount) * chartH : 0;
    const y = pad.top + chartH - h;

    // Color by score value
    const scoreVal = min + (i + 0.5) * binW;
    const t = (scoreVal - min) / range;
    const color = scoreVal >= 0
      ? lerpColor('#c0c040', '#40c040', Math.min(t * 2, 1))
      : lerpColor('#ff4040', '#c0c040', Math.max(0, 1 + scoreVal / Math.abs(min)));

    ctx.fillStyle = color;
    ctx.fillRect(x + 1, y, barWidth - 2, h);
  }

  // X-axis labels
  ctx.fillStyle = '#808090';
  ctx.font = '10px -apple-system, sans-serif';
  ctx.textAlign = 'center';
  for (let i = 0; i <= 5; i++) {
    const val = min + (range * i / 5);
    const x = pad.left + (chartW * i / 5);
    ctx.fillText(val.toFixed(2), x, H - 8);
  }

  // Zero line
  if (min < 0 && max > 0) {
    const zeroX = pad.left + (-min / range) * chartW;
    ctx.strokeStyle = '#555570';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(zeroX, pad.top);
    ctx.lineTo(zeroX, pad.top + chartH);
    ctx.stroke();
    ctx.setLineDash([]);
  }
}

function lerpColor(a, b, t) {
  const parse = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const [r1, g1, b1] = parse(a);
  const [r2, g2, b2] = parse(b);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const bl = Math.round(b1 + (b2 - b1) * t);
  return `rgb(${r},${g},${bl})`;
}

// ════════════════════════════════════════════════════════════════
// Section 2 -- Seed Grid
// ════════════════════════════════════════════════════════════════
let currentSort = 'seed';
let currentSearch = '';
let enabledOutcomes = new Set(VERDICT_ORDER);

function renderSeedGrid(data) {
  renderFilterBar(data);
  renderCards(data);
}

function renderFilterBar(data) {
  const bar = document.getElementById('filter-bar');

  // Outcome checkboxes
  const outcomes = [...new Set(data.map(d => d.outcome_class))];
  let html = '<span style="font-size:11px;color:var(--text-dim);margin-right:4px;">Filter:</span>';

  for (const oc of VERDICT_ORDER) {
    if (!outcomes.includes(oc)) continue;
    const color = VERDICT_COLORS[oc] || '#888';
    html += `<label><input type="checkbox" data-oc="${oc}" checked> <span style="color:${color}">${oc}</span></label>`;
  }

  html += `
    <span style="margin-left:auto;"></span>
    <input type="text" id="search-input" placeholder="Search headlines..." style="width:180px;">
    <select id="sort-select">
      <option value="seed">Sort: Seed</option>
      <option value="score">Sort: Score</option>
      <option value="divergences">Sort: Divergences</option>
    </select>
  `;
  bar.innerHTML = html;

  // Events
  bar.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      const oc = cb.dataset.oc;
      if (cb.checked) enabledOutcomes.add(oc);
      else enabledOutcomes.delete(oc);
      renderCards(indexData);
    });
  });

  document.getElementById('search-input').addEventListener('input', (e) => {
    currentSearch = e.target.value.toLowerCase();
    renderCards(indexData);
  });

  document.getElementById('sort-select').addEventListener('change', (e) => {
    currentSort = e.target.value;
    renderCards(indexData);
  });
}

function renderCards(data) {
  const grid = document.getElementById('seed-grid');
  let filtered = data.filter(d =>
    enabledOutcomes.has(d.outcome_class) &&
    (currentSearch === '' || d.headline.toLowerCase().includes(currentSearch))
  );

  if (currentSort === 'seed') filtered.sort((a, b) => a.seed - b.seed);
  else if (currentSort === 'score') filtered.sort((a, b) => b.composite_score - a.composite_score);
  else if (currentSort === 'divergences') filtered.sort((a, b) => b.total_divergences - a.total_divergences);

  grid.innerHTML = filtered.map(d => {
    const color = VERDICT_COLORS[d.outcome_class] || '#888';
    return `
      <a class="seed-card" href="index.html?seed=${d.seed}">
        <div class="card-top">
          <span class="seed-num">#${d.seed}</span>
          <span class="mini-badge" style="background:${color}22;color:${color};border:1px solid ${color}44;">${d.outcome_class}</span>
        </div>
        <div class="card-headline">${escHtml(d.headline)}</div>
        <div class="card-bottom">
          <span>Score: ${d.composite_score >= 0 ? '+' : ''}${d.composite_score.toFixed(4)}</span>
          <span>${d.total_divergences} div</span>
        </div>
      </a>
    `;
  }).join('');
}

function escHtml(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ════════════════════════════════════════════════════════════════
// Data Loading
// ════════════════════════════════════════════════════════════════
function setupLoadButton() {
  const btn = document.getElementById('btn-load-all');
  btn.addEventListener('click', () => loadAllRuns());
}

async function loadAllRuns() {
  if (allRunsLoaded) return;
  const btn = document.getElementById('btn-load-all');
  const track = document.getElementById('load-progress-track');
  const fill = document.getElementById('load-progress-fill');
  const text = document.getElementById('load-progress-text');

  btn.disabled = true;
  btn.textContent = 'Loading...';
  track.style.display = 'block';

  const total = indexData.length;
  allRuns = [];
  let loaded = 0;
  let failed = 0;

  // Load in batches of 10 for parallelism
  const BATCH = 10;
  for (let i = 0; i < total; i += BATCH) {
    const batch = indexData.slice(i, i + BATCH);
    const results = await Promise.allSettled(
      batch.map(entry =>
        fetch(entry.file).then(r => {
          if (!r.ok) throw new Error(r.status);
          return r.json();
        })
      )
    );
    for (const r of results) {
      loaded++;
      if (r.status === 'fulfilled') {
        allRuns.push(r.value);
      } else {
        failed++;
      }
    }
    const pct = (loaded / total * 100).toFixed(0);
    fill.style.width = pct + '%';
    text.textContent = `${loaded}/${total} loaded${failed > 0 ? ` (${failed} failed)` : ''}`;
  }

  allRunsLoaded = true;
  btn.textContent = 'Loaded';
  text.textContent = `${allRuns.length} runs loaded`;

  // Render deep analytics
  renderHeatmap();
  renderFanCharts();
  renderLeverage();
  renderWhatIf();
}

// ════════════════════════════════════════════════════════════════
// Section 3 -- Branch Frequency Heatmap
// ════════════════════════════════════════════════════════════════
function computeBranchFreqs(runs) {
  // nodeId -> { branches: { branchName: count }, year: string, title: string, totalRuns: count }
  const nodes = {};
  for (const run of runs) {
    for (const evt of run.events) {
      if (!evt.node_id) continue;
      if (!nodes[evt.node_id]) {
        nodes[evt.node_id] = {
          title: evt.title || evt.node_id,
          year: evt.year_month || '',
          branches: {},
          total: 0,
        };
      }
      const n = nodes[evt.node_id];
      const br = evt.branch_taken || 'default';
      n.branches[br] = (n.branches[br] || 0) + 1;
      n.total++;
    }
  }
  return nodes;
}

function renderHeatmap(runs) {
  runs = runs || getFilteredRuns();
  if (runs.length === 0) return;

  const nodes = computeBranchFreqs(runs);
  const area = document.getElementById('heatmap-area');

  // Sort nodes by year
  const sorted = Object.entries(nodes).sort((a, b) => a[1].year.localeCompare(b[1].year));

  // Collect all unique branches
  const allBranches = new Set();
  for (const [, n] of sorted) {
    for (const br of Object.keys(n.branches)) allBranches.add(br);
  }
  const branchList = [...allBranches].sort();

  // Compute variance: entropy-like measure; high variance = no single branch dominates
  function nodeVariance(n) {
    const total = n.total;
    if (total === 0) return 0;
    const probs = Object.values(n.branches).map(c => c / total);
    // Normalized entropy
    const k = probs.length;
    if (k <= 1) return 0;
    const entropy = -probs.reduce((s, p) => s + (p > 0 ? p * Math.log2(p) : 0), 0);
    return entropy / Math.log2(k);
  }

  // Limit to nodes that appear in at least 10% of runs, max 50 nodes
  const minAppearance = Math.max(1, runs.length * 0.1);
  const filtered = sorted.filter(([, n]) => n.total >= minAppearance);
  const displayed = filtered.slice(0, 60);

  let html = '<div class="heatmap-container"><table class="heatmap-table"><thead><tr>';
  html += '<th class="node-col">Node</th><th>Year</th>';
  // Only show branches that appear in displayed nodes
  const usedBranches = new Set();
  for (const [, n] of displayed) {
    for (const br of Object.keys(n.branches)) usedBranches.add(br);
  }
  const displayBranches = [...usedBranches].sort();
  for (const br of displayBranches) {
    html += `<th>${escHtml(br.replace(/_/g, ' '))}</th>`;
  }
  html += '</tr></thead><tbody>';

  for (const [nodeId, n] of displayed) {
    const hv = nodeVariance(n) > 0.7;
    html += `<tr class="${hv ? 'high-variance-row' : ''}">`;
    html += `<td class="node-name" title="${escHtml(nodeId)}">${escHtml(n.title)}</td>`;
    html += `<td style="color:var(--text-dim)">${n.year.slice(0, 4)}</td>`;
    for (const br of displayBranches) {
      const count = n.branches[br] || 0;
      const pct = n.total > 0 ? count / n.total : 0;
      const alpha = pct;
      const bgColor = hv ? `rgba(240,192,64,${alpha * 0.8})` : `rgba(96,128,255,${alpha * 0.8})`;
      html += `<td class="heat-cell" style="background:${bgColor}" title="${count}/${n.total} (${(pct * 100).toFixed(1)}%)">${count > 0 ? (pct * 100).toFixed(0) + '%' : ''}</td>`;
    }
    html += '</tr>';
  }

  html += '</tbody></table></div>';
  area.innerHTML = html;
}

// ════════════════════════════════════════════════════════════════
// Section 4 -- Fan Charts
// ════════════════════════════════════════════════════════════════
function extractTrajectories(runs) {
  // For each run, build time series of world state dimensions
  // We accumulate deltas from events by year
  const runTrajectories = [];

  for (const run of runs) {
    const traj = {};
    const state = {};
    for (const dim of FAN_DIMENSIONS) state[dim.key] = 0;

    for (const evt of run.events) {
      const year = parseInt((evt.year_month || '2000').slice(0, 4));
      if (evt.world_state_delta) {
        for (const dim of FAN_DIMENSIONS) {
          if (evt.world_state_delta[dim.key] !== undefined) {
            state[dim.key] += evt.world_state_delta[dim.key];
          }
        }
      }
      // Snapshot every year (overwrites within same year, keeping last)
      for (const dim of FAN_DIMENSIONS) {
        if (!traj[dim.key]) traj[dim.key] = {};
        traj[dim.key][year] = state[dim.key];
      }
    }

    // Also capture final_state if present
    if (run.final_state) {
      for (const dim of FAN_DIMENSIONS) {
        if (run.final_state[dim.key] !== undefined) {
          if (!traj[dim.key]) traj[dim.key] = {};
          traj[dim.key][2100] = run.final_state[dim.key];
        }
      }
    }

    runTrajectories.push(traj);
  }

  return runTrajectories;
}

function computePercentiles(values, percentiles) {
  if (values.length === 0) return percentiles.map(() => 0);
  const sorted = [...values].sort((a, b) => a - b);
  return percentiles.map(p => {
    const idx = (p / 100) * (sorted.length - 1);
    const lo = Math.floor(idx);
    const hi = Math.ceil(idx);
    if (lo === hi) return sorted[lo];
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
  });
}

function renderFanCharts(runs) {
  runs = runs || getFilteredRuns();
  if (runs.length === 0) return;

  const area = document.getElementById('fancharts-area');
  const trajectories = extractTrajectories(runs);

  // Collect all years present
  const allYears = new Set();
  for (const t of trajectories) {
    for (const dim of FAN_DIMENSIONS) {
      if (t[dim.key]) {
        for (const y of Object.keys(t[dim.key])) allYears.add(parseInt(y));
      }
    }
  }
  const years = [...allYears].sort((a, b) => a - b);
  if (years.length === 0) {
    area.innerHTML = '<div class="section-placeholder">No trajectory data found in run events.</div>';
    return;
  }

  let html = '<div class="fan-charts-grid">';
  for (const dim of FAN_DIMENSIONS) {
    html += `<div class="fan-chart-box"><h4>${dim.label}</h4><canvas id="fan-${dim.key}" height="200"></canvas></div>`;
  }
  html += '</div>';
  area.innerHTML = html;

  // Draw each
  requestAnimationFrame(() => {
    for (const dim of FAN_DIMENSIONS) {
      drawFanChart(dim, trajectories, years);
    }
  });
}

function drawFanChart(dim, trajectories, years) {
  const canvas = document.getElementById(`fan-${dim.key}`);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 200 * dpr;
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = 200;
  const pad = { top: 10, bottom: 25, left: 45, right: 10 };
  const cW = W - pad.left - pad.right;
  const cH = H - pad.top - pad.bottom;

  // Compute percentile bands for each year
  const pctLevels = [10, 25, 50, 75, 90];
  const bands = {}; // year -> [p10, p25, p50, p75, p90]

  let globalMin = Infinity, globalMax = -Infinity;

  for (const y of years) {
    const vals = [];
    for (const t of trajectories) {
      if (t[dim.key] && t[dim.key][y] !== undefined) {
        vals.push(t[dim.key][y]);
      }
    }
    if (vals.length > 0) {
      bands[y] = computePercentiles(vals, pctLevels);
      for (const v of vals) {
        if (v < globalMin) globalMin = v;
        if (v > globalMax) globalMax = v;
      }
    }
  }

  const validYears = years.filter(y => bands[y]);
  if (validYears.length === 0) return;

  if (globalMin === globalMax) {
    globalMax = globalMin + 1;
  }

  const yRange = globalMax - globalMin;
  const toX = y => pad.left + ((y - validYears[0]) / (validYears[validYears.length - 1] - validYears[0] || 1)) * cW;
  const toY = v => pad.top + cH - ((v - globalMin) / yRange) * cH;

  ctx.clearRect(0, 0, W, H);

  // Band colors: good direction -> green gradient, bad -> red
  const goodDir = dim.goodDir;
  // p10-p90 band, p25-p75 band, p50 line
  const bandPairs = [[0, 4], [1, 3]]; // p10-p90, p25-p75
  const alphas = [0.15, 0.25];

  for (let bi = 0; bi < bandPairs.length; bi++) {
    const [lo, hi] = bandPairs[bi];
    ctx.beginPath();
    // Forward for upper
    for (let i = 0; i < validYears.length; i++) {
      const x = toX(validYears[i]);
      const y = toY(bands[validYears[i]][hi]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    // Backward for lower
    for (let i = validYears.length - 1; i >= 0; i--) {
      const x = toX(validYears[i]);
      const y = toY(bands[validYears[i]][lo]);
      ctx.lineTo(x, y);
    }
    ctx.closePath();

    // Green if good direction means higher values and median is rising, else contextual
    const medianEnd = bands[validYears[validYears.length - 1]][2];
    const medianStart = bands[validYears[0]][2];
    const improving = (medianEnd - medianStart) * goodDir > 0;
    ctx.fillStyle = improving
      ? `rgba(64, 192, 64, ${alphas[bi]})`
      : `rgba(255, 64, 64, ${alphas[bi]})`;
    ctx.fill();
  }

  // Median line
  ctx.beginPath();
  ctx.strokeStyle = '#d0d0d8';
  ctx.lineWidth = 2;
  for (let i = 0; i < validYears.length; i++) {
    const x = toX(validYears[i]);
    const y = toY(bands[validYears[i]][2]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Axes
  ctx.fillStyle = '#808090';
  ctx.font = '10px -apple-system, sans-serif';
  ctx.textAlign = 'center';

  // X axis
  const yearStep = Math.max(1, Math.floor(validYears.length / 6));
  for (let i = 0; i < validYears.length; i += yearStep) {
    const x = toX(validYears[i]);
    ctx.fillText(validYears[i], x, H - 6);
  }
  // Always show last year
  ctx.fillText(validYears[validYears.length - 1], toX(validYears[validYears.length - 1]), H - 6);

  // Y axis
  ctx.textAlign = 'right';
  const nTicks = 5;
  for (let i = 0; i <= nTicks; i++) {
    const v = globalMin + (yRange * i / nTicks);
    const y = toY(v);
    ctx.fillText(v.toFixed(2), pad.left - 4, y + 3);

    ctx.strokeStyle = '#2a2a3a';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(pad.left + cW, y);
    ctx.stroke();
  }
}

// ════════════════════════════════════════════════════════════════
// Section 5 -- Leverage Ranking
// ════════════════════════════════════════════════════════════════
function renderLeverage(runs) {
  runs = runs || getFilteredRuns();
  if (runs.length === 0) return;

  const area = document.getElementById('leverage-area');

  // For each node/branch combo, compute correlation with final composite_score
  // Group runs by node_id -> branch_taken -> list of composite_scores
  const nodeData = {};

  for (const run of runs) {
    for (const evt of run.events) {
      if (!evt.node_id || !evt.branch_taken) continue;
      if (!nodeData[evt.node_id]) {
        nodeData[evt.node_id] = {
          title: evt.title || evt.node_id,
          year: evt.year_month || '',
          branches: {},
        };
      }
      const br = evt.branch_taken;
      if (!nodeData[evt.node_id].branches[br]) {
        nodeData[evt.node_id].branches[br] = [];
      }
      nodeData[evt.node_id].branches[br].push(run.composite_score);
    }
  }

  // Compute influence: variance of branch means (how much the branch choice affects the score)
  const ranked = [];
  for (const [nodeId, nd] of Object.entries(nodeData)) {
    const branches = Object.entries(nd.branches);
    if (branches.length < 2) continue;

    const branchMeans = branches.map(([, scores]) =>
      scores.reduce((a, b) => a + b, 0) / scores.length
    );
    // Variance of branch means
    const grandMean = branchMeans.reduce((a, b) => a + b, 0) / branchMeans.length;
    const variance = branchMeans.reduce((s, m) => s + (m - grandMean) ** 2, 0) / branchMeans.length;

    ranked.push({
      nodeId,
      title: nd.title,
      year: nd.year,
      branches,
      variance,
      totalRuns: branches.reduce((s, [, sc]) => s + sc.length, 0),
    });
  }

  ranked.sort((a, b) => b.variance - a.variance);
  const top20 = ranked.slice(0, 20);

  if (top20.length === 0) {
    area.innerHTML = '<div class="section-placeholder">Not enough branch variation data for leverage analysis.</div>';
    return;
  }

  let html = '<div class="leverage-list">';

  for (let i = 0; i < top20.length; i++) {
    const item = top20[i];
    const totalCount = item.branches.reduce((s, [, sc]) => s + sc.length, 0);
    const branchColors = ['#6080ff', '#40c0ff', '#ffd700', '#ff8040', '#c040ff', '#ff40ff', '#40c040', '#ff4040'];

    html += `<div class="leverage-item">`;
    html += `<div class="leverage-rank">${i + 1}</div>`;
    html += `<div><div class="leverage-node-name">${escHtml(item.title)}</div><div class="leverage-node-year">${item.year.slice(0, 7)} &middot; ${item.nodeId}</div></div>`;

    // Branch distribution bars
    html += `<div class="leverage-branches">`;
    for (let j = 0; j < item.branches.length; j++) {
      const [brName, scores] = item.branches[j];
      const pct = (scores.length / totalCount * 100).toFixed(0);
      const color = branchColors[j % branchColors.length];
      const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
      html += `<div class="leverage-branch-row">
        <span class="leverage-branch-label" title="${escHtml(brName)}">${escHtml(brName.replace(/_/g, ' '))}</span>
        <div class="leverage-branch-bar" style="width:${pct}%;background:${color};min-width:4px;"></div>
        <span style="color:var(--text-dim);font-size:10px;">${pct}%</span>
      </div>`;
    }
    html += `</div>`;

    // Score distribution per branch (mini bar showing mean)
    html += `<div class="leverage-branches">`;
    for (let j = 0; j < item.branches.length; j++) {
      const [brName, scores] = item.branches[j];
      const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
      const color = branchColors[j % branchColors.length];
      const meanColor = mean >= 0 ? '#40c040' : '#ff4040';
      html += `<div class="leverage-branch-row">
        <span style="color:${meanColor};font-size:10px;font-weight:700;min-width:55px;text-align:right;">${mean >= 0 ? '+' : ''}${mean.toFixed(3)}</span>
        <span style="color:var(--text-dim);font-size:9px;">(n=${scores.length})</span>
      </div>`;
    }
    html += `</div>`;

    html += `</div>`;
  }

  html += '</div>';
  area.innerHTML = html;
}

// ════════════════════════════════════════════════════════════════
// Section 6 -- What-If Filter
// ════════════════════════════════════════════════════════════════
function renderWhatIf() {
  if (!allRunsLoaded || allRuns.length === 0) return;

  const area = document.getElementById('whatif-area');

  // Build node->branches map
  const nodeMap = {};
  for (const run of allRuns) {
    for (const evt of run.events) {
      if (!evt.node_id || !evt.branch_taken) continue;
      if (!nodeMap[evt.node_id]) {
        nodeMap[evt.node_id] = { title: evt.title || evt.node_id, year: evt.year_month || '', branches: new Set() };
      }
      nodeMap[evt.node_id].branches.add(evt.branch_taken);
    }
  }

  // Sort nodes by year
  const sortedNodes = Object.entries(nodeMap).sort((a, b) => a[1].year.localeCompare(b[1].year));

  let html = '<div class="whatif-controls">';
  html += '<span style="color:var(--text);font-size:12px;">If</span>';
  html += '<select id="whatif-node"><option value="">-- select node --</option>';
  for (const [nodeId, nd] of sortedNodes) {
    html += `<option value="${escHtml(nodeId)}">[${nd.year.slice(0, 4)}] ${escHtml(nd.title)}</option>`;
  }
  html += '</select>';
  html += '<span style="color:var(--text);font-size:12px;">takes branch</span>';
  html += '<select id="whatif-branch" disabled><option value="">-- select branch --</option></select>';
  html += '<button class="load-btn" id="btn-add-filter" disabled style="padding:4px 12px;font-size:12px;">Add Filter</button>';
  html += '<button class="ctrl-btn" id="btn-clear-filters" style="font-size:11px;">Clear All</button>';
  html += '</div>';
  html += '<div id="whatif-tags" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;"></div>';
  html += '<div id="whatif-match" class="whatif-match-count"></div>';
  html += '<div id="whatif-results" class="whatif-results"></div>';

  area.innerHTML = html;

  // Wire up
  const nodeSelect = document.getElementById('whatif-node');
  const branchSelect = document.getElementById('whatif-branch');
  const addBtn = document.getElementById('btn-add-filter');
  const clearBtn = document.getElementById('btn-clear-filters');

  nodeSelect.addEventListener('change', () => {
    const nodeId = nodeSelect.value;
    branchSelect.innerHTML = '<option value="">-- select branch --</option>';
    if (nodeId && nodeMap[nodeId]) {
      for (const br of [...nodeMap[nodeId].branches].sort()) {
        branchSelect.innerHTML += `<option value="${escHtml(br)}">${escHtml(br.replace(/_/g, ' '))}</option>`;
      }
      branchSelect.disabled = false;
    } else {
      branchSelect.disabled = true;
    }
    addBtn.disabled = true;
  });

  branchSelect.addEventListener('change', () => {
    addBtn.disabled = !branchSelect.value;
  });

  addBtn.addEventListener('click', () => {
    const nodeId = nodeSelect.value;
    const branch = branchSelect.value;
    if (!nodeId || !branch) return;
    // Avoid duplicate
    if (activeFilters.some(f => f.nodeId === nodeId && f.branch === branch)) return;
    activeFilters.push({ nodeId, branch, title: nodeMap[nodeId]?.title || nodeId });
    applyWhatIfFilters();
  });

  clearBtn.addEventListener('click', () => {
    activeFilters = [];
    applyWhatIfFilters();
  });
}

function applyWhatIfFilters() {
  // Render tags
  const tagsEl = document.getElementById('whatif-tags');
  tagsEl.innerHTML = activeFilters.map((f, i) =>
    `<span class="whatif-tag">${escHtml(f.title)}: ${escHtml(f.branch.replace(/_/g, ' '))} <span class="remove-filter" data-idx="${i}">x</span></span>`
  ).join('');

  tagsEl.querySelectorAll('.remove-filter').forEach(el => {
    el.addEventListener('click', () => {
      activeFilters.splice(parseInt(el.dataset.idx), 1);
      applyWhatIfFilters();
    });
  });

  const filtered = getFilteredRuns();
  const matchEl = document.getElementById('whatif-match');
  if (activeFilters.length > 0) {
    matchEl.textContent = `${filtered.length} of ${allRuns.length} runs match`;
  } else {
    matchEl.textContent = `Showing all ${allRuns.length} runs (no filters active)`;
  }

  // Update deep analytics with filtered data
  renderWhatIfMiniOverview(filtered);
  renderHeatmap(filtered);
  renderFanCharts(filtered);
  renderLeverage(filtered);
}

function renderWhatIfMiniOverview(runs) {
  const area = document.getElementById('whatif-results');
  if (runs.length === 0) {
    area.innerHTML = '<div class="section-placeholder">No runs match these filters.</div>';
    return;
  }

  const scores = runs.map(r => r.composite_score).sort((a, b) => a - b);
  const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
  const median = scores[Math.floor(scores.length / 2)];

  const counts = {};
  for (const r of runs) {
    counts[r.outcome_class] = (counts[r.outcome_class] || 0) + 1;
  }

  let html = '<div class="stats-row" style="margin-top:12px;">';
  html += `<div class="stat-card"><div class="stat-label">Matching Runs</div><div class="stat-value">${runs.length}</div></div>`;
  html += `<div class="stat-card"><div class="stat-label">Mean Score</div><div class="stat-value">${mean >= 0 ? '+' : ''}${mean.toFixed(4)}</div></div>`;
  html += `<div class="stat-card"><div class="stat-label">Median Score</div><div class="stat-value">${median >= 0 ? '+' : ''}${median.toFixed(4)}</div></div>`;
  html += '</div>';

  // Mini outcome bar
  html += '<div class="outcome-bar" style="margin-bottom:8px;">';
  for (const oc of VERDICT_ORDER) {
    const n = counts[oc] || 0;
    if (n === 0) continue;
    const pct = (n / runs.length * 100);
    const color = VERDICT_COLORS[oc] || '#888';
    html += `<div class="segment" style="width:${pct}%; background:${color};" title="${oc}: ${n}">${pct >= 5 ? n : ''}</div>`;
  }
  html += '</div>';

  area.innerHTML = html;
}

function getFilteredRuns() {
  if (!allRunsLoaded) return [];
  if (activeFilters.length === 0) return allRuns;

  return allRuns.filter(run => {
    // Build a map of node_id -> branch_taken for this run
    const runBranches = {};
    for (const evt of run.events) {
      if (evt.node_id && evt.branch_taken) {
        runBranches[evt.node_id] = evt.branch_taken;
      }
    }
    // All filters must match
    return activeFilters.every(f => runBranches[f.nodeId] === f.branch);
  });
}

// ════════════════════════════════════════════════════════════════
// Window resize handler for canvases
// ════════════════════════════════════════════════════════════════
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (indexData.length > 0) {
      const scores = indexData.map(d => d.composite_score).sort((a, b) => a - b);
      renderHistogram(scores);
    }
    if (allRunsLoaded) {
      renderFanCharts();
    }
  }, 200);
});
