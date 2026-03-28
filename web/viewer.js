// viewer.js -- Cinematic event playback engine

export class Viewer {
  constructor({ timelineEl, dashboard, sound, onProgress, onComplete, onEraChange }) {
    this.timelineEl = timelineEl;
    this.dashboard = dashboard;
    this.sound = sound;
    this.onProgress = onProgress;
    this.onComplete = onComplete;
    this.onEraChange = onEraChange;

    this.run = null;
    this.events = [];
    this.currentIndex = -1;
    this.playing = false;
    this.speed = 1;
    this.timer = null;
    this.typewriterTimers = [];
    this.lastDecade = null;
    this.lastYearMonth = null;
    this.currentEraName = null;

    this.worldState = {};
  }

  static INITIAL_STATE = {
    us_polarization: 0.35, eu_cohesion: 0.75, us_global_standing: 0.85,
    china_power_index: 0.30, russia_stability: 0.45, middle_east_stability: 0.40,
    india_power_index: 0.15, latin_america_stability: 0.50,
    global_gdp_growth_modifier: 1.0, inequality_index: 0.50, us_debt_gdp_ratio: 0.55,
    crypto_market_cap_trillion: 0.0, supply_chain_resilience: 0.70,
    ai_development_year_offset: 0, internet_freedom_index: 0.80,
    social_media_penetration: 0.05, human_augmentation_prevalence: 0.0,
    space_development_index: 0.0, nuclear_risk_level: 0.15, terrorism_threat_index: 0.30,
    surveillance_state_index: 0.20, global_cyber_damage_annual_b: 1.0,
    drone_warfare_prevalence: 0.0, climate_temp_anomaly: 0.6, renewable_energy_share: 0.06,
    sea_level_rise_meters: 0.0, biodiversity_index: 0.80, water_stress_index: 0.25,
    food_security_index: 0.85, arctic_ice_status: 0.90, global_pandemic_deaths: 0,
    conflict_deaths: 0, opioid_deaths_cumulative: 0, global_democracy_index: 0.62,
    us_institutional_trust: 0.55, misinformation_severity: 0.15,
    racial_justice_index: 0.40, gender_equity_index: 0.45, us_life_expectancy_delta: 0.0,
    global_population_billions: 6.1, median_age_global: 26.0, automation_displacement: 0.0,
    governance_model: 0.50, us_unity_index: 0.70, europe_federation_index: 0.20,
    china_regime_type: 0.15, middle_east_post_oil: 0.05, arctic_sovereignty_resolved: 0.05,
    africa_development_index: 0.25, existential_risk_cumulative: 0.0,
  };

  static ERA_NAMES = {
    2000: 'THE RECKONING',
    2010: 'THE RECKONING',
    2020: 'THE RECKONING',
    2030: 'THE TRANSFORMATION',
    2040: 'THE TRANSFORMATION',
    2050: 'THE FORK',
    2060: 'THE FORK',
    2070: 'THE NEW WORLD',
    2080: 'THE NEW WORLD',
    2090: 'END STATE',
  };

  loadRun(runData) {
    this.stop();
    this.run = runData;
    this.events = runData.events || [];
    this.currentIndex = -1;
    this.lastDecade = null;
    this.lastYearMonth = null;
    this.currentEraName = null;
    this.worldState = { ...Viewer.INITIAL_STATE };
    this.timelineEl.innerHTML = '';
    this.dashboard.reset();
    this.dashboard.update(this.worldState, null);
    this._clearTypewriters();
    if (this.onProgress) this.onProgress(0, this.events.length);
  }

  play() {
    if (!this.run || this.playing) return;
    if (this.currentIndex >= this.events.length - 1) {
      this.currentIndex = -1;
      this.worldState = { ...Viewer.INITIAL_STATE };
      this.timelineEl.innerHTML = '';
      this.dashboard.reset();
      this.dashboard.update(this.worldState, null);
      this.lastDecade = null;
      this.lastYearMonth = null;
      this.currentEraName = null;
    }
    this.playing = true;
    // Init sound on first play (requires user gesture)
    if (this.sound && !this.sound.ctx) this.sound.init();
    this._scheduleNext();
  }

  pause() {
    this.playing = false;
    clearTimeout(this.timer);
    this.timer = null;
  }

  stop() {
    this.pause();
    this._clearTypewriters();
    // Stop any playing narration audio
    if (this._currentAudio) {
      this._currentAudio.pause();
      this._currentAudio = null;
    }
    if (this.sound) {
      this.sound.stopDrone();
      this.sound.stopAll();
      this.sound.currentMood = 'neutral';
    }
  }

  togglePlay() {
    if (this.playing) this.pause();
    else this.play();
    return this.playing;
  }

  setSpeed(s) {
    this.speed = s;
    if (this.playing) {
      clearTimeout(this.timer);
      this._scheduleNext();
    }
  }

  skipForward() {
    if (!this.run) return;
    this.pause();
    this._showNextEvent();
  }

  skipBackward() {
    if (!this.run || this.currentIndex <= 0) return;
    this.pause();
    const targetIdx = this.currentIndex - 1;
    this.currentIndex = -1;
    this.worldState = { ...Viewer.INITIAL_STATE };
    this.timelineEl.innerHTML = '';
    this.dashboard.reset();
    this.lastDecade = null;
    this.lastYearMonth = null;
    this.currentEraName = null;
    this._clearTypewriters();
    for (let i = 0; i <= targetIdx; i++) {
      this._showEvent(i, false);
    }
    this.currentIndex = targetIdx;
    this.dashboard.update(this.worldState, null);
    if (this.onProgress) this.onProgress(this.currentIndex + 1, this.events.length);
  }

  seekTo(fraction) {
    if (!this.run) return;
    const wasPlaying = this.playing;
    this.pause();
    const targetIdx = Math.min(Math.floor(fraction * this.events.length), this.events.length - 1);
    this.currentIndex = -1;
    this.worldState = { ...Viewer.INITIAL_STATE };
    this.timelineEl.innerHTML = '';
    this.dashboard.reset();
    this.lastDecade = null;
    this.lastYearMonth = null;
    this.currentEraName = null;
    this._clearTypewriters();
    for (let i = 0; i <= targetIdx; i++) {
      this._showEvent(i, false);
    }
    this.currentIndex = targetIdx;
    this.dashboard.update(this.worldState, null);
    if (this.onProgress) this.onProgress(this.currentIndex + 1, this.events.length);
    if (wasPlaying) this.play();
  }

  get isPlaying() { return this.playing; }
  get eventCount() { return this.events.length; }
  get currentEventIndex() { return this.currentIndex; }

  // ── Private ──

  _computeDelay(prevYM, nextYM) {
    // Cinematic pacing: delay proportional to time gap between events
    if (!prevYM || !nextYM) return 1500;
    try {
      const [py, pm] = prevYM.split('-').map(Number);
      const [ny, nm] = nextYM.split('-').map(Number);
      const gapMonths = (ny - py) * 12 + (nm - pm);

      // Base delays (at 1x speed):
      // Same month: 800ms (quick succession)
      // 1-6 months: 1200ms
      // 6-24 months: 2000ms
      // 2-5 years: 3000ms
      // 5+ years: 4000ms (dramatic pause)
      let delay;
      if (gapMonths <= 0) delay = 800;
      else if (gapMonths <= 6) delay = 1200;
      else if (gapMonths <= 24) delay = 2000;
      else if (gapMonths <= 60) delay = 3000;
      else delay = 4000;

      return delay / this.speed;
    } catch {
      return 1500 / this.speed;
    }
  }

  _scheduleNext() {
    if (!this.playing) return;
    const nextIdx = this.currentIndex + 1;
    if (nextIdx >= this.events.length) {
      this.pause();
      if (this.onComplete) this.onComplete(this.run);
      return;
    }

    const nextEvent = this.events[nextIdx];
    const prevYM = this.lastYearMonth;
    const nextYM = nextEvent.year_month;

    // Check for era transition — add extra pause
    const nextYear = parseInt(nextYM.split('-')[0], 10);
    const nextDecade = Math.floor(nextYear / 10) * 10;
    const nextEra = Viewer.ERA_NAMES[nextDecade] || 'END STATE';
    const eraChanging = this.currentEraName && nextEra !== this.currentEraName;

    let delay = this._computeDelay(prevYM, nextYM);

    // Extra pause for era transitions
    if (eraChanging) {
      delay += 2500 / this.speed;
    }

    // Extra pause for high-impact events (let them breathe)
    if (nextEvent.is_high_impact) {
      delay += 500 / this.speed;
    }

    this.timer = setTimeout(() => {
      try {
        this._showNextEvent();
      } catch (e) {
        console.warn('[21csim] Error showing event:', e.message);
      }
      if (this.playing) this._scheduleNext();
    }, delay);
  }

  _showNextEvent() {
    const nextIdx = this.currentIndex + 1;
    if (nextIdx >= this.events.length) {
      this.pause();
      if (this.onComplete) this.onComplete(this.run);
      return;
    }
    this._showEvent(nextIdx, true);
    this.currentIndex = nextIdx;
    this.lastYearMonth = this.events[nextIdx].year_month;
    if (this.onProgress) this.onProgress(this.currentIndex + 1, this.events.length);
  }

  _showEvent(idx, animate) {
    const event = this.events[idx];
    const year = parseInt(event.year_month.split('-')[0], 10);
    const decade = Math.floor(year / 10) * 10;
    const eraName = Viewer.ERA_NAMES[decade] || 'END STATE';

    // Era transition
    if (eraName !== this.currentEraName) {
      if (this.currentEraName !== null) {
        this._showEraBanner(eraName, decade, animate);
        if (animate && this.sound) {
          this.sound.eraTransition();
          // Update drone mood based on world state
          this._updateDroneMood();
        }
      }
      this.currentEraName = eraName;
    }

    // Year header when year changes
    const prevEvent = idx > 0 ? this.events[idx - 1] : null;
    const prevYear = prevEvent ? parseInt(prevEvent.year_month.split('-')[0], 10) : null;
    if (prevYear === null || year !== prevYear) {
      this._showYearHeader(year, animate);
    }
    this.lastDecade = decade;

    // Apply world state delta
    const delta = event.world_state_delta || {};
    for (const [key, val] of Object.entries(delta)) {
      if (this.worldState[key] !== undefined) {
        this.worldState[key] += val;
        if (typeof this.worldState[key] === 'number' && key !== 'conflict_deaths' &&
            key !== 'global_pandemic_deaths' && key !== 'opioid_deaths_cumulative' &&
            key !== 'climate_temp_anomaly' && key !== 'sea_level_rise_meters' &&
            key !== 'global_gdp_growth_modifier' && key !== 'us_debt_gdp_ratio' &&
            key !== 'global_cyber_damage_annual_b' && key !== 'crypto_market_cap_trillion' &&
            key !== 'ai_development_year_offset' && key !== 'us_life_expectancy_delta' &&
            key !== 'global_population_billions' && key !== 'median_age_global') {
          this.worldState[key] = Math.max(0, Math.min(1, this.worldState[key]));
        }
      }
    }

    if (animate) {
      this.dashboard.update(this.worldState, delta);
      // Update generative music mood based on new world state
      if (this.sound && this.sound.updateMood) {
        try { this.sound.updateMood(this.worldState); } catch (e) { /* ignore */ }
      }
    }

    // Sound cues (wrapped in try/catch to prevent audio errors from killing playback)
    if (animate && this.sound) {
      try {
        const desc = (event.description || '').toLowerCase();
        if (event.status === 'ESCALATED' && desc.includes('nuclear')) {
          this.sound.nuclear();
        } else if (event.status === 'ESCALATED') {
          this.sound.escalation();
        } else if (event.status === 'DIVERGENCE') {
          this.sound.divergence();
        } else if (event.status === 'HISTORICAL') {
          this.sound.tick();
        }
      } catch (e) {
        console.warn('[21csim] Sound cue error:', e.message);
      }
    }

    // Create event card
    const card = document.createElement('div');
    card.className = 'event-card';
    if (event.is_high_impact) card.classList.add('high-impact');
    if (event.status === 'HISTORICAL') card.classList.add('historical');
    if (!animate) card.style.animation = 'none';

    const statusClass = 'status-' + event.status;
    const month = this._monthAbbr(event.year_month);

    // Build explanation line
    let explanationHtml = '';
    if (event.explanation && event.status !== 'HISTORICAL') {
      explanationHtml = `<div class="event-explanation">↳ ${this._esc(event.explanation)}</div>`;
    }

    // Build narration line with optional voice playback
    let narrationHtml = '';
    if (event.narration) {
      const audioSrc = `/audio/${this.run.seed}/${idx}.mp3`;
      narrationHtml = `<div class="event-narration" data-narration="${this._escAttr(event.narration)}" data-audio="${audioSrc}">` +
        `<button class="narration-play-btn" title="Listen to narration" aria-label="Play narration audio">&#x1F50A;</button>` +
        `</div>`;
    }

    card.innerHTML = `
      <div class="event-header">
        <span class="year-badge">${month}</span>
        <span class="event-title">${this._esc(event.title)}</span>
        <span class="status-badge ${statusClass}">${event.status}</span>
      </div>
      <div class="event-description">${this._esc(event.description)}</div>
      ${explanationHtml}
      ${narrationHtml}`;

    this.timelineEl.appendChild(card);

    // Typewriter for narration (use a text span to avoid destroying the play button)
    if (animate && event.narration) {
      const narEl = card.querySelector('.event-narration');
      if (narEl) {
        const textSpan = document.createElement('span');
        textSpan.className = 'narration-text';
        narEl.insertBefore(textSpan, narEl.firstChild);
        this._typewrite(textSpan, event.narration);
      }
    } else if (event.narration) {
      const narEl = card.querySelector('.event-narration');
      if (narEl) {
        const textSpan = document.createElement('span');
        textSpan.className = 'narration-text';
        textSpan.textContent = event.narration;
        narEl.insertBefore(textSpan, narEl.firstChild);
      }
    }

    // Voice playback button
    const playBtn = card.querySelector('.narration-play-btn');
    if (playBtn) {
      playBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this._playNarrationAudio(playBtn);
      });
    }

    // Auto-scroll only if user is near the bottom (not scrolled up reading)
    if (animate) {
      const el = this.timelineEl;
      const nearBottom = (el.scrollHeight - el.scrollTop - el.clientHeight) < 200;
      if (nearBottom) {
        card.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    }
  }

  _showEraBanner(eraName, decade, animate) {
    const banner = document.createElement('div');
    banner.className = 'era-banner';
    if (!animate) banner.style.animation = 'none';

    const yearRange = {
      'THE RECKONING': '2000 — 2030',
      'THE TRANSFORMATION': '2030 — 2050',
      'THE FORK': '2050 — 2070',
      'THE NEW WORLD': '2070 — 2090',
      'END STATE': '2090 — 2100',
    };

    banner.innerHTML = `
      <div class="era-name">${eraName}</div>
      <div class="era-range">${yearRange[eraName] || ''}</div>`;
    this.timelineEl.appendChild(banner);
    if (this.onEraChange) this.onEraChange(decade);
  }

  _showYearHeader(year, animate) {
    const header = document.createElement('div');
    header.className = 'year-header';
    if (!animate) header.style.animation = 'none';
    header.textContent = `── ${year} ──`;
    this.timelineEl.appendChild(header);
  }

  _updateDroneMood() {
    if (!this.sound) return;
    const ws = this.worldState;
    // Determine mood from world state
    if (ws.existential_risk_cumulative > 0.3 || ws.nuclear_risk_level > 0.4) {
      this.sound.startDrone('dark');
    } else if (ws.us_polarization > 0.6 || ws.conflict_deaths > 200000) {
      this.sound.startDrone('tense');
    } else if (ws.global_democracy_index > 0.65 && ws.renewable_energy_share > 0.3) {
      this.sound.startDrone('hopeful');
    } else {
      this.sound.startDrone('neutral');
    }
  }

  _typewrite(el, text) {
    el.textContent = '';
    el.classList.add('cursor-blink');
    let i = 0;
    const baseInterval = 25;
    const interval = baseInterval / Math.max(this.speed, 0.5);
    const tid = setInterval(() => {
      if (i < text.length) {
        el.textContent += text[i];
        i++;
      } else {
        clearInterval(tid);
        el.classList.remove('cursor-blink');
      }
    }, interval);
    this.typewriterTimers.push(tid);
  }

  _clearTypewriters() {
    for (const t of this.typewriterTimers) clearInterval(t);
    this.typewriterTimers = [];
  }

  _monthAbbr(ym) {
    const months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    const parts = (ym || '').split('-');
    if (parts.length < 2) return '???';
    const m = parseInt(parts[1], 10);
    return months[m - 1] || '???';
  }

  _esc(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  _escAttr(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  _playNarrationAudio(btn) {
    const narEl = btn.closest('.event-narration');
    const audioSrc = narEl?.dataset.audio;
    if (!audioSrc) return;

    // Check if clicking the same button that was playing (before we clear state)
    const wasPlaying = btn.classList.contains('playing');

    // Stop any currently playing narration
    if (this._currentAudio) {
      this._currentAudio.pause();
      this._currentAudio = null;
      // Reset all play buttons
      this.timelineEl.querySelectorAll('.narration-play-btn.playing').forEach(b => {
        b.classList.remove('playing');
        b.innerHTML = '&#x1F50A;';
      });
      // Restore ambient music volume
      if (this.sound && this.sound.masterVol) {
        try {
          const vol = this.sound._dbFromLinear ? this.sound._dbFromLinear(this.sound.volume) : -10;
          this.sound.masterVol.volume.rampTo(vol, 0.5);
        } catch (e) { /* ignore */ }
      }
    }

    // If clicking the same button that was playing, just stop
    if (wasPlaying) {
      return;
    }

    // Dim the ambient music while voice plays
    if (this.sound && this.sound.masterVol) {
      try { this.sound.masterVol.volume.rampTo(-40, 0.5); } catch (e) { /* ignore */ }
    }

    btn.classList.add('playing');
    btn.innerHTML = '&#x23F8;'; // pause icon

    const audio = new Audio(audioSrc);
    this._currentAudio = audio;

    audio.addEventListener('ended', () => {
      btn.classList.remove('playing');
      btn.innerHTML = '&#x1F50A;';
      this._currentAudio = null;
      // Restore ambient music volume
      if (this.sound && this.sound.masterVol) {
        try {
          const vol = this.sound._dbFromLinear ? this.sound._dbFromLinear(this.sound.volume) : -10;
          this.sound.masterVol.volume.rampTo(vol, 0.5);
        } catch (e) { /* ignore */ }
      }
    });

    audio.addEventListener('error', () => {
      btn.classList.remove('playing');
      btn.innerHTML = '&#x1F50A;';
      btn.title = 'Audio not available';
      this._currentAudio = null;
      // Restore ambient music
      if (this.sound && this.sound.masterVol) {
        try {
          const vol = this.sound._dbFromLinear ? this.sound._dbFromLinear(this.sound.volume) : -10;
          this.sound.masterVol.volume.rampTo(vol, 0.5);
        } catch (e) { /* ignore */ }
      }
    });

    audio.play().catch(() => {
      btn.classList.remove('playing');
      btn.innerHTML = '&#x1F50A;';
    });
  }
}
