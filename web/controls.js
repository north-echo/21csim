// controls.js -- Playback controls

export class Controls {
  constructor({ containerEl, viewer, onSelectRun }) {
    this.container = containerEl;
    this.viewer = viewer;
    this.onSelectRun = onSelectRun;
    this._build();
    this._bindKeys();
  }

  _build() {
    this.container.innerHTML = `
      <button class="ctrl-btn" id="btn-prev" title="Previous (Left)" aria-label="Previous event">\u25C0</button>
      <button class="ctrl-btn" id="btn-play" title="Play/Pause (Space)" aria-label="Play" aria-pressed="false">\u25B6</button>
      <button class="ctrl-btn" id="btn-next" title="Next (Right)" aria-label="Next event">\u25B6\u25B6</button>
      <div class="speed-group" role="group" aria-label="Playback speed">
        <button class="speed-btn" data-speed="0.1" aria-label="Speed 0.1x" aria-pressed="false">0.1x</button>
        <button class="speed-btn" data-speed="0.25" aria-label="Speed 0.25x" aria-pressed="false">0.25x</button>
        <button class="speed-btn" data-speed="0.5" aria-label="Speed 0.5x" aria-pressed="false">0.5x</button>
        <button class="speed-btn active" data-speed="1" aria-label="Speed 1x" aria-pressed="true">1x</button>
        <button class="speed-btn" data-speed="2" aria-label="Speed 2x" aria-pressed="false">2x</button>
        <button class="speed-btn" data-speed="4" aria-label="Speed 4x" aria-pressed="false">4x</button>
      </div>
      <div id="progress-container">
        <div id="progress-track" role="slider" aria-label="Playback progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" tabindex="0"><div id="progress-fill"></div></div>
        <span id="progress-text" aria-live="off">--</span>
      </div>
      <span id="event-counter" aria-live="polite" aria-atomic="true">0 / 0</span>
    `;

    this.btnPlay = this.container.querySelector('#btn-play');
    this.btnPrev = this.container.querySelector('#btn-prev');
    this.btnNext = this.container.querySelector('#btn-next');
    this.progressFill = this.container.querySelector('#progress-fill');
    this.progressTrack = this.container.querySelector('#progress-track');
    this.progressText = this.container.querySelector('#progress-text');
    this.eventCounter = this.container.querySelector('#event-counter');
    this.speedBtns = this.container.querySelectorAll('.speed-btn');

    this.btnPlay.addEventListener('click', () => this._togglePlay());
    this.btnPrev.addEventListener('click', () => this.viewer.skipBackward());
    this.btnNext.addEventListener('click', () => this.viewer.skipForward());

    for (const btn of this.speedBtns) {
      btn.addEventListener('click', () => {
        const speed = parseFloat(btn.dataset.speed);
        this.viewer.setSpeed(speed);
        for (const b of this.speedBtns) {
          b.classList.remove('active');
          b.setAttribute('aria-pressed', 'false');
        }
        btn.classList.add('active');
        btn.setAttribute('aria-pressed', 'true');
      });
    }

    this.progressTrack.addEventListener('click', (e) => {
      const rect = this.progressTrack.getBoundingClientRect();
      const frac = (e.clientX - rect.left) / rect.width;
      this.viewer.seekTo(Math.max(0, Math.min(1, frac)));
    });
  }

  _togglePlay() {
    const playing = this.viewer.togglePlay();
    this.btnPlay.textContent = playing ? '\u23F8' : '\u25B6';
    this.btnPlay.classList.toggle('active', playing);
    this.btnPlay.setAttribute('aria-label', playing ? 'Pause' : 'Play');
    this.btnPlay.setAttribute('aria-pressed', String(playing));
  }

  _bindKeys() {
    document.addEventListener('keydown', (e) => {
      // Don't capture if typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      switch (e.code) {
        case 'Space':
          e.preventDefault();
          this._togglePlay();
          break;
        case 'ArrowRight':
          e.preventDefault();
          this.viewer.skipForward();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          this.viewer.skipBackward();
          break;
        case 'ArrowUp':
          e.preventDefault();
          this._cycleSpeed(1);
          break;
        case 'ArrowDown':
          e.preventDefault();
          this._cycleSpeed(-1);
          break;
      }
    });
  }

  _cycleSpeed(dir) {
    const speeds = [0.1, 0.25, 0.5, 1, 2, 4];
    const current = this.viewer.speed;
    let idx = speeds.indexOf(current);
    if (idx === -1) idx = 1;
    idx = Math.max(0, Math.min(speeds.length - 1, idx + dir));
    this.viewer.setSpeed(speeds[idx]);
    for (const b of this.speedBtns) {
      const isActive = parseFloat(b.dataset.speed) === speeds[idx];
      b.classList.toggle('active', isActive);
      b.setAttribute('aria-pressed', String(isActive));
    }
  }

  updateProgress(current, total) {
    if (total === 0) return;
    const pct = (current / total) * 100;
    this.progressFill.style.width = pct + '%';
    this.progressTrack.setAttribute('aria-valuenow', Math.round(pct));
    this.eventCounter.textContent = `${current} / ${total}`;

    // Show year range
    if (this.viewer.events.length > 0) {
      const firstYear = this.viewer.events[0]?.year_month || '';
      const currentEvent = this.viewer.events[Math.min(current - 1, this.viewer.events.length - 1)];
      const lastEvent = this.viewer.events[this.viewer.events.length - 1];
      const curYear = currentEvent?.year_month || firstYear;
      const endYear = lastEvent?.year_month || '';
      this.progressText.textContent = `${curYear} \u2192 ${endYear}`;
    }
  }

  setPlayState(playing) {
    this.btnPlay.textContent = playing ? '\u23F8' : '\u25B6';
    this.btnPlay.classList.toggle('active', playing);
    this.btnPlay.setAttribute('aria-label', playing ? 'Pause' : 'Play');
    this.btnPlay.setAttribute('aria-pressed', String(playing));
  }
}
