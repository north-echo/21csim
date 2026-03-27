// sound.js -- Web Audio API sound engine for 21csim
// Runtime-synthesized tones — no audio files needed

export class SoundEngine {
  constructor() {
    this.ctx = null;
    this.enabled = false;
    this.masterGain = null;
  }

  init() {
    if (this.ctx) return;
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.value = 0.3;
    this.masterGain.connect(this.ctx.destination);
    this.enabled = true;
  }

  toggle() {
    if (!this.ctx) this.init();
    this.enabled = !this.enabled;
    return this.enabled;
  }

  // ── Cues ──

  tick() {
    // Subtle click for each event
    if (!this.enabled) return;
    this._tone(800, 0.02, { type: 'sine', gain: 0.05, decay: 0.02 });
  }

  divergence() {
    // Warm ping for divergences
    if (!this.enabled) return;
    this._tone(440, 0.15, { type: 'sine', gain: 0.12, attack: 0.005, decay: 0.14 });
    this._tone(660, 0.12, { type: 'sine', gain: 0.06, attack: 0.01, decay: 0.11, delay: 0.03 });
  }

  escalation() {
    // Ominous low tone for escalated events
    if (!this.enabled) return;
    this._tone(110, 0.4, { type: 'sawtooth', gain: 0.08, attack: 0.05, decay: 0.35 });
    this._tone(117, 0.4, { type: 'sawtooth', gain: 0.06, attack: 0.05, decay: 0.35 });
  }

  eraTransition() {
    // Open fifth bell — A2 + E3
    if (!this.enabled) return;
    this._tone(110, 1.5, { type: 'sine', gain: 0.15, attack: 0.01, decay: 1.4 });
    this._tone(165, 1.5, { type: 'sine', gain: 0.12, attack: 0.01, decay: 1.4 });
    this._tone(220, 1.2, { type: 'sine', gain: 0.06, attack: 0.02, decay: 1.1, delay: 0.1 });
  }

  nuclear() {
    // Subsonic throb with dissonance
    if (!this.enabled) return;
    this._tone(55, 2.0, { type: 'sine', gain: 0.2, attack: 0.5, decay: 1.5 });
    this._tone(58, 2.0, { type: 'sine', gain: 0.15, attack: 0.5, decay: 1.5 });
    this._tone(110, 1.5, { type: 'sawtooth', gain: 0.05, attack: 0.8, decay: 0.7, delay: 0.3 });
  }

  extinction() {
    // A minor chord slowly fading
    if (!this.enabled) return;
    this._tone(220, 4.0, { type: 'sine', gain: 0.15, attack: 0.2, decay: 3.8 });
    this._tone(262, 4.0, { type: 'sine', gain: 0.12, attack: 0.3, decay: 3.7 });
    this._tone(330, 3.5, { type: 'sine', gain: 0.10, attack: 0.4, decay: 3.1 });
    // Low rumble
    this._tone(55, 5.0, { type: 'sine', gain: 0.08, attack: 1.0, decay: 4.0 });
  }

  transcendence() {
    // Rising harmonic series
    if (!this.enabled) return;
    const freqs = [220, 330, 440, 550, 660, 880, 1100];
    freqs.forEach((f, i) => {
      this._tone(f, 2.5 - i * 0.2, {
        type: 'sine',
        gain: 0.10 - i * 0.01,
        attack: 0.1 + i * 0.15,
        decay: 2.0 - i * 0.2,
        delay: i * 0.25,
      });
    });
  }

  verdictGood() {
    // C major arpeggio
    if (!this.enabled) return;
    this._tone(262, 1.2, { type: 'sine', gain: 0.12, attack: 0.02, decay: 1.1 });
    this._tone(330, 1.0, { type: 'sine', gain: 0.10, attack: 0.02, decay: 0.9, delay: 0.15 });
    this._tone(392, 0.8, { type: 'sine', gain: 0.10, attack: 0.02, decay: 0.7, delay: 0.30 });
    this._tone(523, 1.5, { type: 'sine', gain: 0.08, attack: 0.02, decay: 1.4, delay: 0.45 });
  }

  verdictBad() {
    // Bb minor descending
    if (!this.enabled) return;
    this._tone(466, 1.2, { type: 'sine', gain: 0.12, attack: 0.02, decay: 1.1 });
    this._tone(349, 1.0, { type: 'sine', gain: 0.10, attack: 0.02, decay: 0.9, delay: 0.2 });
    this._tone(277, 1.5, { type: 'sine', gain: 0.10, attack: 0.02, decay: 1.4, delay: 0.4 });
  }

  verdictNeutral() {
    // Suspended — unresolved
    if (!this.enabled) return;
    this._tone(262, 1.5, { type: 'sine', gain: 0.10, attack: 0.05, decay: 1.4 });
    this._tone(349, 1.5, { type: 'sine', gain: 0.08, attack: 0.05, decay: 1.4 });
  }

  // Ambient drone for background mood
  startDrone(mood = 'neutral') {
    if (!this.enabled) return;
    this.stopDrone();

    const freqs = {
      neutral: [65, 98],      // C2 + G2
      tense: [65, 69],        // C2 + Db2 (dissonant)
      hopeful: [65, 82],      // C2 + E2
      dark: [55, 58],         // A1 + Bb1
    };
    const f = freqs[mood] || freqs.neutral;

    this._droneOscs = f.map(freq => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = freq;
      gain.gain.value = 0;
      gain.gain.linearRampToValueAtTime(0.03, this.ctx.currentTime + 3);
      osc.connect(gain);
      gain.connect(this.masterGain);
      osc.start();
      return { osc, gain };
    });
  }

  stopDrone() {
    if (this._droneOscs) {
      const now = this.ctx.currentTime;
      this._droneOscs.forEach(({ osc, gain }) => {
        gain.gain.linearRampToValueAtTime(0, now + 1);
        osc.stop(now + 1.1);
      });
      this._droneOscs = null;
    }
  }

  // ── Internals ──

  _tone(freq, duration, opts = {}) {
    if (!this.ctx || !this.enabled) return;
    const {
      type = 'sine',
      gain: gainVal = 0.1,
      attack = 0.01,
      decay = duration * 0.8,
      delay = 0,
    } = opts;

    const now = this.ctx.currentTime + delay;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc.type = type;
    osc.frequency.value = freq;

    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(gainVal, now + attack);
    gain.gain.linearRampToValueAtTime(0, now + attack + decay);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(now);
    osc.stop(now + duration + 0.1);
  }
}
