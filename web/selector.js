// selector.js -- Run selector modal

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

export class Selector {
  constructor({ overlayEl, onSelect }) {
    this.overlay = overlayEl;
    this.onSelect = onSelect;
    this.runs = [];
    this._build();
  }

  _build() {
    this.overlay.innerHTML = `
      <div id="selector-modal" role="document">
        <div id="selector-header">
          <h2 id="selector-title">Select a Simulation Run</h2>
          <div id="selector-actions">
            <button class="ctrl-btn" id="btn-random" aria-label="Load a random run">Random</button>
            <button class="ctrl-btn" id="btn-close-selector" aria-label="Close run selector">\u2715</button>
          </div>
        </div>
        <div id="selector-list" role="listbox" aria-labelledby="selector-title"></div>
      </div>
    `;
    this.overlay.setAttribute('aria-labelledby', 'selector-title');

    this.listEl = this.overlay.querySelector('#selector-list');
    this.overlay.querySelector('#btn-close-selector').addEventListener('click', () => this.close());
    this.overlay.querySelector('#btn-random').addEventListener('click', () => this._pickRandom());
    // Close on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.overlay.classList.contains('open')) this.close();
    });
  }

  async loadIndex(url) {
    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      this.runs = await resp.json();
      this._renderList();
      return this.runs;
    } catch (err) {
      console.warn('Could not load run index:', err);
      this.runs = [];
      this.listEl.innerHTML = `
        <div style="padding: 40px; text-align: center; color: var(--text-dim);">
          <p>No runs found.</p>
          <p style="font-size: 11px; margin-top: 8px;">
            Start the server with <code>python serve.py</code> and generate some runs first.
          </p>
        </div>`;
      return [];
    }
  }

  _renderList() {
    this.listEl.innerHTML = '';
    if (this.runs.length === 0) {
      this.listEl.innerHTML = `
        <div style="padding: 40px; text-align: center; color: var(--text-dim);">
          No runs available.
        </div>`;
      return;
    }

    for (const run of this.runs) {
      const item = document.createElement('div');
      item.className = 'run-item';
      item.setAttribute('role', 'option');
      item.setAttribute('tabindex', '0');
      item.setAttribute('aria-label', `Seed ${run.seed}, ${run.outcome_class}, ${run.headline}`);
      const color = VERDICT_COLORS[run.outcome_class] || '#888';
      item.innerHTML = `
        <span class="seed">#${run.seed}</span>
        <span class="verdict-badge" style="background: ${color}22; color: ${color}; border: 1px solid ${color}44;">
          ${run.outcome_class}
        </span>
        <span class="headline">${this._esc(run.headline)}</span>
        <span class="score">${(run.composite_score >= 0 ? '+' : '') + run.composite_score.toFixed(3)}</span>
      `;
      item.addEventListener('click', () => this._selectRun(run));
      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this._selectRun(run);
        }
      });
      this.listEl.appendChild(item);
    }
  }

  async _selectRun(runMeta) {
    try {
      const resp = await fetch(runMeta.file);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      this.close();
      if (this.onSelect) this.onSelect(data);
    } catch (err) {
      console.warn('Failed to load run:', err);
      alert('Failed to load run file: ' + err.message);
    }
  }

  _pickRandom() {
    if (this.runs.length === 0) return;
    const idx = Math.floor(Math.random() * this.runs.length);
    this._selectRun(this.runs[idx]);
  }

  open() {
    this.overlay.classList.add('open');
    // Focus first focusable element in modal
    const firstBtn = this.overlay.querySelector('#btn-random');
    if (firstBtn) setTimeout(() => firstBtn.focus(), 50);
  }
  close() {
    this.overlay.classList.remove('open');
    // Return focus to the trigger button
    const trigger = document.getElementById('btn-select-run');
    if (trigger) trigger.focus();
  }
  toggle() {
    if (this.overlay.classList.contains('open')) {
      this.close();
    } else {
      this.open();
    }
  }

  _esc(s) {
    if (!s) return '';
    const d = document.createElement('span');
    d.textContent = s;
    return d.innerHTML;
  }
}
