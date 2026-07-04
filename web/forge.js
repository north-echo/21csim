// forge.js -- Interactive mode: the viewer becomes the fork.
// Playback pauses at high-leverage decision nodes; the user picks a branch,
// the century re-simulates in-browser (sim.js) with that choice locked, and
// playback continues into the altered future. Confirming the branch fate
// already took changes nothing (RNG stream stays aligned — see sim.js).

import { simulate, loadSimNodes } from './sim.js';

// The century's steering wheel: famous early hinges + the nodes the 10k-run
// batch analysis found highest-leverage on the final verdict.
const DECISION_NODES = [
  '2000_election', '2001_911', '2003_iraq', '2008_financial_crisis',
  '2016_us_election', '2020_covid_response', '2029_pandemic_2',
  '2031_climate_migration', '2042_amoc', '2053_ai_existential',
  '2078_last_great_war',
];
const DECISION_SET = new Set(DECISION_NODES);

const STATUS_LABELS = { HISTORICAL: 'OUR TIMELINE' };

export class Forge {
  constructor({ viewer, controls, onRunReplaced }) {
    this.viewer = viewer;
    this.controls = controls;
    this.onRunReplaced = onRunReplaced;
    this.active = false;
    this.overlay = null;
  }

  async start(seed, presetLocks) {
    this.nodes = await loadSimNodes();
    this.seed = seed ?? Math.floor(Math.random() * 1000000);
    this.locks = { ...(presetLocks || {}) };
    this.decided = new Set(Object.keys(this.locks));
    this.decisionsMade = Object.keys(this.locks).length;
    this.run = simulate(this.nodes, this.seed, this.locks);
    this.active = true;
    this.viewer.interceptor = (idx) => this._maybeIntercept(idx);
    return this.run;
  }

  stop() {
    this.active = false;
    this.viewer.interceptor = null;
    this._hideOverlay();
  }

  shareUrl() {
    const d = Object.entries(this.locks).map(([n, b]) => `${n}.${b}`).join('~');
    return `https://21csim.com/?forge=${this.seed}${d ? `&d=${encodeURIComponent(d)}` : ''}`;
  }

  static parseShareParams(params) {
    const seedStr = params.get('forge');
    if (seedStr === null || !/^\d+$/.test(seedStr)) return null;
    const locks = {};
    const d = params.get('d');
    if (d) {
      for (const pair of d.split('~')) {
        const dot = pair.lastIndexOf('.');
        if (dot > 0) locks[pair.slice(0, dot)] = pair.slice(dot + 1);
      }
    }
    return { seed: parseInt(seedStr, 10), locks };
  }

  // ── Interception ──

  _maybeIntercept(idx) {
    if (!this.active) return false;
    const ev = this.viewer.events[idx];
    if (!ev || !DECISION_SET.has(ev.node_id) || this.decided.has(ev.node_id)) return false;
    this.controls.setPlayState(false);
    this._showChoice(idx, ev);
    return true;
  }

  _showChoice(idx, ev) {
    const node = this.nodes.nodes[ev.node_id];
    const dist = this.run._dists[ev.node_id] || {};
    const branches = Object.entries(dist).sort((a, b) => b[1] - a[1]);

    const overlay = this._ensureOverlay();
    const esc = this._esc;
    const [year, month] = ev.year_month.split('-');
    const MON = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

    overlay.innerHTML = `
      <div class="forge-modal" role="document">
        <div class="forge-kicker">Decision ${this.decisionsMade + 1} &middot; ${MON[parseInt(month, 10) - 1] || ''} ${esc(year)}</div>
        <h2 class="forge-title">${esc(node.title)}</h2>
        <p class="forge-desc">${esc(node.description || '')}</p>
        <div class="forge-options">
          ${branches.map(([branch, p]) => {
            const o = (node.outcomes || {})[branch] || {};
            const tag = STATUS_LABELS[o.status]
              ? `<span class="forge-tag">${STATUS_LABELS[o.status]}</span>` : '';
            return `<button class="forge-option" data-branch="${esc(branch)}">
              <span class="forge-prob">${(p * 100).toFixed(0)}%</span>
              <span class="forge-option-text">${esc(o.description || branch)}${tag}</span>
            </button>`;
          }).join('')}
        </div>
        <button class="forge-fate" data-fate="1">&#127922; Leave it to the dice</button>
      </div>`;

    overlay.querySelectorAll('.forge-option').forEach(btn => {
      btn.addEventListener('click', () => this._choose(idx, ev.node_id, btn.dataset.branch));
    });
    overlay.querySelector('.forge-fate').addEventListener('click', () => this._choose(idx, ev.node_id, null));
    overlay.classList.add('open');
    const firstBtn = overlay.querySelector('.forge-option');
    if (firstBtn) firstBtn.focus();
  }

  _choose(idx, nodeId, branch) {
    this.decided.add(nodeId);
    this.decisionsMade += 1;
    this._hideOverlay();

    // Fate = accept the branch the simulation already sampled; nothing changes.
    if (branch) {
      const current = this.run.events[idx];
      if (!current || current.branch_taken !== branch) {
        this.locks[nodeId] = branch;
        this.run = simulate(this.nodes, this.seed, this.locks);
        // Events before idx are identical (aligned RNG + same locks); swap the
        // future in place without resetting the timeline.
        this.viewer.refreshRun(this.run);
        if (this.onRunReplaced) this.onRunReplaced(this.run);
      }
    }

    this.viewer.play();
    this.controls.setPlayState(true);
  }

  // ── Overlay plumbing ──

  _ensureOverlay() {
    if (this.overlay) return this.overlay;
    const el = document.createElement('div');
    el.id = 'forge-overlay';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-label', 'Decision point');
    document.body.appendChild(el);
    this.overlay = el;
    return el;
  }

  _hideOverlay() {
    if (this.overlay) this.overlay.classList.remove('open');
  }

  _esc(s) {
    return String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }
}
