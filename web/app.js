// app.js -- Main application logic

import { Dashboard } from './dashboard.js';
import { Viewer } from './viewer.js';
import { Controls } from './controls.js';
import { Selector } from './selector.js';
import { SoundEngine } from './sound.js';
import { initNav } from './nav.js';

const VERDICT_COLORS = {
  'GOLDEN-AGE': '#ffd700',
  'PROGRESS': '#40c040',
  'MUDDLING-THROUGH': '#c0c040',
  'DECLINE': '#ff8040',
  'CATASTROPHE': '#ff4040',
  'EXTINCTION': '#ff0000',
  'TRANSCENDENCE': '#c040ff',
  'RADICALLY-DIFFERENT': '#ff40ff',
};

class App {
  constructor() {
    this.currentRun = null;

    // Sound engine
    this.sound = new SoundEngine();

    // Dashboard
    this.dashboard = new Dashboard(document.getElementById('dashboard-panel'));

    // Viewer
    this.viewer = new Viewer({
      timelineEl: document.getElementById('timeline-panel'),
      dashboard: this.dashboard,
      sound: this.sound,
      onProgress: (cur, total) => this.controls.updateProgress(cur, total),
      onComplete: (run) => this._onRunComplete(run),
      onEraChange: (decade) => {},
    });

    // Controls
    this.controls = new Controls({
      containerEl: document.getElementById('controls-bar'),
      viewer: this.viewer,
    });

    // Sound toggle button
    this._addSoundToggle();

    // Selector
    this.selector = new Selector({
      overlayEl: document.getElementById('selector-overlay'),
      onSelect: (data) => this._loadRun(data),
    });

    // Top bar buttons
    document.getElementById('btn-select-run').addEventListener('click', () => {
      this.selector.open();
    });

    document.querySelector('.logo').addEventListener('click', () => {
      this.selector.open();
    });

    // Summary close
    document.getElementById('summary-overlay').addEventListener('click', (e) => {
      if (e.target.id === 'summary-overlay' || e.target.id === 'btn-close-summary') {
        document.getElementById('summary-overlay').classList.remove('open');
      }
    });

    // Load run index
    this._init();
  }

  async _init() {
    const runs = await this.selector.loadIndex('/runs/index.json');

    // Check for /century/{seed} path or ?seed=XXXX query param
    const pathMatch = window.location.pathname.match(/\/century\/(\d+)/);
    const params = new URLSearchParams(window.location.search);
    const seedParam = pathMatch ? pathMatch[1] : params.get('seed');
    if (seedParam && runs.length > 0) {
      const target = runs.find(r => String(r.seed) === seedParam);
      if (target) {
        // Load the run directly
        try {
          const resp = await fetch(target.file);
          if (resp.ok) {
            const data = await resp.json();
            this._loadRun(data);
            return;
          }
        } catch (e) {
          console.warn('Failed to auto-load seed', seedParam, e);
        }
      }
    }

    // Auto-open selector if no run loaded
    if (runs.length > 0) {
      this.selector.open();
    }
  }

  _loadRun(data) {
    this.currentRun = data;
    this.viewer.loadRun(data);

    // Update top bar
    const runInfo = document.getElementById('run-info');
    const color = VERDICT_COLORS[data.outcome_class] || '#888';
    runInfo.innerHTML = `
      <span class="seed">Seed #${data.seed}</span>
      <span class="verdict-badge" style="background: ${color}22; color: ${color}; border: 1px solid ${color}44;">
        ${data.outcome_class}
      </span>
      <span class="headline">${this._esc(data.headline)}</span>
    `;

    // Hide empty state
    const empty = document.getElementById('empty-state');
    if (empty) empty.style.display = 'none';

    // Auto-play
    setTimeout(() => {
      this.viewer.play();
      this.controls.setPlayState(true);
    }, 300);
  }

  _addSoundToggle() {
    const btn = document.createElement('button');
    btn.className = 'ctrl-btn sound-toggle';
    btn.textContent = '🔇';
    btn.title = 'Toggle sound';
    btn.addEventListener('click', () => {
      const on = this.sound.toggle();
      btn.textContent = on ? '🔊' : '🔇';
    });
    const topBar = document.querySelector('.top-bar');
    if (topBar) topBar.appendChild(btn);
  }

  _onRunComplete(run) {
    // Play verdict sound
    if (this.sound && this.sound.enabled) {
      this.sound.stopDrone();
      const oc = run.outcome_class;
      if (oc === 'EXTINCTION' || oc === 'CATASTROPHE') {
        if (oc === 'EXTINCTION') this.sound.extinction();
        else this.sound.verdictBad();
      } else if (oc === 'TRANSCENDENCE') {
        this.sound.transcendence();
      } else if (oc === 'GOLDEN-AGE' || oc === 'PROGRESS') {
        this.sound.verdictGood();
      } else {
        this.sound.verdictNeutral();
      }
    }
    // Show summary after a moment
    setTimeout(() => this._showSummary(run), 2000);
  }

  _showSummary(run) {
    this.controls.setPlayState(false);
    const overlay = document.getElementById('summary-overlay');
    const modal = document.getElementById('summary-modal');
    const color = VERDICT_COLORS[run.outcome_class] || '#888';
    const fs = run.final_state || {};

    const stats = [
      { label: 'Composite Score', value: (run.composite_score >= 0 ? '+' : '') + run.composite_score.toFixed(4) },
      { label: 'Total Divergences', value: run.total_divergences },
      { label: 'Events', value: run.events.length },
      { label: 'Percentile', value: (run.percentile || 50).toFixed(1) + '%' },
      { label: 'Democracy Index', value: (fs.global_democracy_index || 0).toFixed(3) },
      { label: 'Temp Anomaly', value: (fs.climate_temp_anomaly || 0).toFixed(2) + '\u00B0C' },
      { label: 'Nuclear Risk', value: (fs.nuclear_risk_level || 0).toFixed(3) },
      { label: 'Renewable Share', value: ((fs.renewable_energy_share || 0) * 100).toFixed(1) + '%' },
    ];

    modal.innerHTML = `
      <div class="verdict-large" style="color: ${color};">${run.outcome_class}</div>
      <div class="headline-large">${this._esc(run.headline)}</div>
      <div class="summary-stats">
        ${stats.map(s => `
          <div class="summary-stat">
            <div class="label">${s.label}</div>
            <div class="value">${s.value}</div>
          </div>
        `).join('')}
      </div>
      <button class="ctrl-btn" id="btn-close-summary" style="margin: 0 auto; padding: 8px 24px;">Close</button>
    `;

    modal.querySelector('#btn-close-summary').addEventListener('click', () => {
      overlay.classList.remove('open');
    });

    overlay.classList.add('open');
  }

  _esc(s) {
    if (!s) return '';
    const d = document.createElement('span');
    d.textContent = s;
    return d.innerHTML;
  }
}

// Boot
document.addEventListener('DOMContentLoaded', () => {
  initNav('viewer');
  window.app = new App();
});
