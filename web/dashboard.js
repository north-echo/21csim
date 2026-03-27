// dashboard.js -- World state dashboard with animated bars

// Dimension definitions: { key, label, section, range, goodHigh }
const DIMENSIONS = [
  // Geopolitical
  { key: 'us_polarization', label: 'US Polarization', section: 'Geopolitical', range: [0, 1], goodHigh: false },
  { key: 'us_global_standing', label: 'US Global Standing', section: 'Geopolitical', range: [0, 1], goodHigh: true },
  { key: 'eu_cohesion', label: 'EU Cohesion', section: 'Geopolitical', range: [0, 1], goodHigh: true },
  { key: 'china_power_index', label: 'China Power', section: 'Geopolitical', range: [0, 1], goodHigh: null },
  { key: 'russia_stability', label: 'Russia Stability', section: 'Geopolitical', range: [0, 1], goodHigh: null },
  { key: 'middle_east_stability', label: 'Middle East Stability', section: 'Geopolitical', range: [0, 1], goodHigh: true },

  // Security
  { key: 'nuclear_risk_level', label: 'Nuclear Risk', section: 'Security', range: [0, 1], goodHigh: false },
  { key: 'terrorism_threat_index', label: 'Terrorism Threat', section: 'Security', range: [0, 1], goodHigh: false },
  { key: 'surveillance_state_index', label: 'Surveillance State', section: 'Security', range: [0, 1], goodHigh: false },
  { key: 'existential_risk_cumulative', label: 'Existential Risk', section: 'Security', range: [0, 1], goodHigh: false },

  // Climate
  { key: 'climate_temp_anomaly', label: 'Temp Anomaly', section: 'Climate', range: [0, 6], goodHigh: false, unit: '\u00B0C' },
  { key: 'renewable_energy_share', label: 'Renewable Energy', section: 'Climate', range: [0, 1], goodHigh: true },
  { key: 'biodiversity_index', label: 'Biodiversity', section: 'Climate', range: [0, 1], goodHigh: true },
  { key: 'sea_level_rise_meters', label: 'Sea Level Rise', section: 'Climate', range: [0, 2], goodHigh: false, unit: 'm' },

  // Economic
  { key: 'inequality_index', label: 'Inequality', section: 'Economic', range: [0, 1], goodHigh: false },
  { key: 'global_gdp_growth_modifier', label: 'GDP Growth Mod', section: 'Economic', range: [0.1, 3], goodHigh: true },
  { key: 'supply_chain_resilience', label: 'Supply Chain', section: 'Economic', range: [0, 1], goodHigh: true },

  // Technology
  { key: 'space_development_index', label: 'Space Development', section: 'Technology', range: [0, 1], goodHigh: true },
  { key: 'internet_freedom_index', label: 'Internet Freedom', section: 'Technology', range: [0, 1], goodHigh: true },
  { key: 'social_media_penetration', label: 'Social Media', section: 'Technology', range: [0, 1], goodHigh: null },

  // Human / Social
  { key: 'global_democracy_index', label: 'Democracy Index', section: 'Human', range: [0, 1], goodHigh: true },
  { key: 'us_institutional_trust', label: 'US Trust', section: 'Human', range: [0, 1], goodHigh: true },
  { key: 'conflict_deaths', label: 'Conflict Deaths', section: 'Human', range: [0, 5000000], goodHigh: false, format: 'int' },
  { key: 'global_pandemic_deaths', label: 'Pandemic Deaths', section: 'Human', range: [0, 50000000], goodHigh: false, format: 'int' },
];

export class Dashboard {
  constructor(containerEl) {
    this.container = containerEl;
    this.currentState = {};
    this.dimElements = {};
    this._build();
  }

  _build() {
    this.container.innerHTML = '';
    const sections = {};
    for (const dim of DIMENSIONS) {
      if (!sections[dim.section]) sections[dim.section] = [];
      sections[dim.section].push(dim);
    }
    for (const [sectionName, dims] of Object.entries(sections)) {
      const sec = document.createElement('div');
      sec.className = 'dashboard-section';
      sec.innerHTML = `<h3>${sectionName}</h3>`;
      for (const dim of dims) {
        const row = document.createElement('div');
        row.className = 'dim-row';
        row.innerHTML = `
          <div class="dim-label">
            <span class="dim-name">${dim.label}</span>
            <span class="dim-value" data-dim="${dim.key}">--</span>
          </div>
          <div class="dim-bar-track">
            <div class="dim-bar-fill" data-dim="${dim.key}"></div>
            <span class="dim-bar-delta" data-dim="${dim.key}"></span>
          </div>`;
        sec.appendChild(row);
        this.dimElements[dim.key] = {
          value: row.querySelector('.dim-value'),
          fill: row.querySelector('.dim-bar-fill'),
          delta: row.querySelector('.dim-bar-delta'),
        };
      }
      this.container.appendChild(sec);
    }
  }

  update(worldState, delta) {
    this.currentState = { ...this.currentState, ...worldState };
    for (const dim of DIMENSIONS) {
      const val = this.currentState[dim.key];
      if (val === undefined) continue;
      const els = this.dimElements[dim.key];
      if (!els) continue;

      // Format value
      let displayVal;
      if (dim.format === 'int') {
        displayVal = Number(val).toLocaleString();
      } else if (dim.unit) {
        displayVal = val.toFixed(2) + dim.unit;
      } else {
        displayVal = (typeof val === 'number') ? val.toFixed(3) : String(val);
      }
      els.value.textContent = displayVal;

      // Bar width
      const [lo, hi] = dim.range;
      const pct = Math.max(0, Math.min(100, ((val - lo) / (hi - lo)) * 100));
      els.fill.style.width = pct + '%';

      // Bar color
      els.fill.style.backgroundColor = this._barColor(pct / 100, dim.goodHigh);

      // Delta indicator
      if (delta && delta[dim.key] !== undefined) {
        const d = delta[dim.key];
        els.delta.textContent = (d >= 0 ? '+' : '') + d.toFixed(3);
        els.delta.className = 'dim-bar-delta show ' + (d >= 0 ? 'positive' : 'negative');
        // If "bad when high" and going up, flip colors
        if (dim.goodHigh === false) {
          els.delta.className = 'dim-bar-delta show ' + (d >= 0 ? 'negative' : 'positive');
        }
        setTimeout(() => { els.delta.classList.remove('show'); }, 2000);
      }
    }
  }

  _barColor(fraction, goodHigh) {
    // fraction is 0-1 of the bar fill
    if (goodHigh === null) return '#6080a0'; // neutral
    const t = goodHigh ? fraction : (1 - fraction);
    // t=1 is good (green), t=0 is bad (red)
    if (t > 0.6) return this._lerp('#c0c040', '#40c040', (t - 0.6) / 0.4);
    if (t > 0.3) return this._lerp('#ff8040', '#c0c040', (t - 0.3) / 0.3);
    return this._lerp('#ff4040', '#ff8040', t / 0.3);
  }

  _lerp(colorA, colorB, t) {
    const a = this._hex(colorA), b = this._hex(colorB);
    const r = Math.round(a[0] + (b[0] - a[0]) * t);
    const g = Math.round(a[1] + (b[1] - a[1]) * t);
    const bl = Math.round(a[2] + (b[2] - a[2]) * t);
    return `rgb(${r},${g},${bl})`;
  }

  _hex(h) {
    const m = h.match(/^#(..)(..)(..)$/);
    return m ? [parseInt(m[1],16), parseInt(m[2],16), parseInt(m[3],16)] : [128,128,128];
  }

  reset() {
    this.currentState = {};
    for (const dim of DIMENSIONS) {
      const els = this.dimElements[dim.key];
      if (!els) continue;
      els.value.textContent = '--';
      els.fill.style.width = '0%';
      els.delta.className = 'dim-bar-delta';
      els.delta.textContent = '';
    }
  }
}
