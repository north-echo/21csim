// sound.js -- Tone.js generative music engine for 21csim
// Reactive ambient score that responds to simulation world state

export class SoundEngine {
  constructor() {
    this.initialized = false;
    this.enabled = false;
    this.currentMood = 'neutral';
    this.targetMood = 'neutral';
    this.moodTransitioning = false;
    this.volume = 0.3; // default 30%

    // Tone.js nodes (created on init)
    this.masterVol = null;
    this.reverb = null;
    this.compressor = null;
    this.padSynth = null;
    this.arpSynth = null;
    this.bassSynth = null;
    this.arpLoop = null;
    this.padLoop = null;
    this.chordIndex = 0;
    this.arpNoteIndex = 0;
    this._scheduledIds = [];
  }

  // ── Chord & arpeggio definitions per mood ──

  static CHORDS = {
    hopeful: [
      ['C4', 'E4', 'G4', 'B4'],       // Cmaj7
      ['A3', 'C4', 'E4', 'G4'],       // Am7
      ['F3', 'A3', 'C4', 'E4'],       // Fmaj7
      ['G3', 'B3', 'D4', 'F4'],       // G7
    ],
    neutral: [
      ['C4', 'D4', 'G4'],             // Csus2
      ['F3', 'G3', 'C4'],             // Fsus2
      ['G3', 'C4', 'D4'],             // Gsus4
    ],
    tense: [
      ['C4', 'Eb4', 'G4'],            // Cm
      ['Ab3', 'C4', 'Eb4'],           // Ab
      ['Eb3', 'G3', 'Bb3'],           // Eb
      ['Bb3', 'D4', 'F4'],            // Bb/D
    ],
    dark: [
      ['C3', 'G3'],                    // C5
      ['Db3', 'Ab3'],                  // Db5
    ],
    transcendent: [
      ['C4', 'E4', 'G4', 'B4', 'D5'], // Cmaj9
      ['E4', 'G#4', 'B4', 'D#5'],     // Emaj7
      ['Ab3', 'C4', 'Eb4', 'G4'],     // Abmaj7
      ['Db4', 'F4', 'Ab4', 'C5', 'Eb5'], // Dbmaj9
    ],
  };

  static ARP_PATTERNS = {
    hopeful:      { subdivision: '16n', direction: 'up' },
    neutral:      { subdivision: '4n', direction: 'upDown' },
    tense:        { subdivision: '8n', direction: 'random' },
    dark:         { subdivision: '2n', direction: 'random' },
    transcendent: { subdivision: '32n', direction: 'up' },
  };

  static MOOD_SETTINGS = {
    hopeful:      { filterFreq: 2000, padAttack: 2, padRelease: 4, arpVol: -18, padVol: -14, bassVol: -24, bpm: 72 },
    neutral:      { filterFreq: 1200, padAttack: 3, padRelease: 5, arpVol: -22, padVol: -16, bassVol: -26, bpm: 60 },
    tense:        { filterFreq: 800,  padAttack: 1.5, padRelease: 3, arpVol: -16, padVol: -12, bassVol: -20, bpm: 90 },
    dark:         { filterFreq: 400,  padAttack: 4, padRelease: 6, arpVol: -28, padVol: -18, bassVol: -18, bpm: 48 },
    transcendent: { filterFreq: 4000, padAttack: 1, padRelease: 3, arpVol: -14, padVol: -12, bassVol: -26, bpm: 100 },
  };

  // Bars per chord cycle
  static MOOD_BARS = {
    hopeful: 16, neutral: 12, tense: 8, dark: 24, transcendent: 12,
  };

  // ── Public API ──

  init() {
    if (this.initialized) return;
    const Tone = window.Tone;
    if (!Tone) { console.warn('Tone.js not loaded'); return; }

    // Start audio context (requires user gesture)
    Tone.start();

    // Master chain: compressor -> volume -> destination
    this.compressor = new Tone.Compressor({ threshold: -20, ratio: 4, attack: 0.1, release: 0.25 }).toDestination();
    this.masterVol = new Tone.Volume(this._dbFromLinear(this.volume)).connect(this.compressor);
    this.reverb = new Tone.Freeverb({ roomSize: 0.75, dampening: 3000, wet: 0.4 }).connect(this.masterVol);

    // Low-pass filter for mood control
    this.filter = new Tone.Filter({ frequency: 1200, type: 'lowpass', rolloff: -24 }).connect(this.reverb);

    // Pad synth — 4 voice polyphony, warm
    this.padSynth = new Tone.PolySynth(Tone.Synth, {
      maxPolyphony: 6,
      voice: Tone.Synth,
      options: {
        oscillator: { type: 'sine' },
        envelope: { attack: 3, decay: 1, sustain: 0.8, release: 5 },
        volume: -16,
      },
    }).connect(this.filter);

    // Arpeggio synth — mono, bright
    this.arpSynth = new Tone.MonoSynth({
      oscillator: { type: 'triangle' },
      envelope: { attack: 0.01, decay: 0.3, sustain: 0.1, release: 0.5 },
      filterEnvelope: { attack: 0.01, decay: 0.2, sustain: 0.3, release: 0.5, baseFrequency: 300, octaves: 2 },
      volume: -22,
    }).connect(this.filter);

    // Chorus for divergence shimmer effect
    this.chorus = new Tone.Chorus({ frequency: 4, delayTime: 3.5, depth: 0.7, wet: 0.5 }).connect(this.reverb);

    // Sub-bass drone — sine, very low
    this.bassSynth = new Tone.Synth({
      oscillator: { type: 'sine' },
      envelope: { attack: 4, decay: 2, sustain: 0.9, release: 6 },
      volume: -26,
    }).connect(this.masterVol); // bass direct to master, skip reverb

    // Event cue synths
    this.tickNoise = new Tone.NoiseSynth({
      noise: { type: 'white' },
      envelope: { attack: 0.001, decay: 0.01, sustain: 0, release: 0.01 },
      volume: -36,
    }).connect(this.masterVol);

    this.bellSynth = new Tone.MetalSynth({
      frequency: 200, envelope: { attack: 0.01, decay: 2, release: 1 },
      harmonicity: 5.1, modulationIndex: 16, resonance: 4000, octaves: 1.5,
      volume: -20,
    }).connect(this.reverb);

    this.fmSynth = new Tone.FMSynth({
      harmonicity: 1.5, modulationIndex: 8,
      oscillator: { type: 'sawtooth' },
      envelope: { attack: 0.02, decay: 0.3, sustain: 0, release: 0.2 },
      modulation: { type: 'square' },
      modulationEnvelope: { attack: 0.01, decay: 0.2, sustain: 0, release: 0.1 },
      volume: -14,
    }).connect(this.filter);

    // Distortion for nuclear event
    this.distortion = new Tone.Distortion({ distortion: 0.8, wet: 0.6 }).connect(this.masterVol);
    this.nuclearSynth = new Tone.Synth({
      oscillator: { type: 'sine' },
      envelope: { attack: 0.5, decay: 1, sustain: 0.6, release: 2 },
      volume: -10,
    }).connect(this.distortion);

    this.initialized = true;
    this.enabled = true;

    // Start ambient score
    this._startAmbient();
  }

  toggle() {
    if (!this.initialized) this.init();
    this.enabled = !this.enabled;
    if (this.enabled) {
      this.masterVol.volume.rampTo(this._dbFromLinear(this.volume), 0.3);
      if (window.Tone && window.Tone.getTransport().state !== 'started') {
        this._startAmbient();
      }
    } else {
      this.masterVol.volume.rampTo(-Infinity, 0.3);
    }
    return this.enabled;
  }

  setVolume(v) {
    this.volume = Math.max(0, Math.min(1, v));
    if (this.masterVol) {
      this.masterVol.volume.rampTo(this._dbFromLinear(this.volume), 0.1);
    }
  }

  // ── Event Cues ──

  tick() {
    if (!this.enabled || !this.initialized) return;
    this.tickNoise.triggerAttackRelease('32n');
  }

  divergence() {
    if (!this.enabled || !this.initialized) return;
    // Play the next note in the current arpeggio louder, through chorus
    const chords = SoundEngine.CHORDS[this.currentMood] || SoundEngine.CHORDS.neutral;
    const chord = chords[this.chordIndex % chords.length];
    const note = chord[this.arpNoteIndex % chord.length];
    const shimmerSynth = new window.Tone.Synth({
      oscillator: { type: 'sine' },
      envelope: { attack: 0.01, decay: 0.6, sustain: 0.2, release: 1.0 },
      volume: -10,
    }).connect(this.chorus);
    shimmerSynth.triggerAttackRelease(note, '4n');
    // Cleanup after sound finishes
    setTimeout(() => shimmerSynth.dispose(), 3000);
  }

  escalation() {
    if (!this.enabled || !this.initialized) return;
    // Low brass-like stab, minor 2nd interval
    this.fmSynth.triggerAttackRelease('C2', '8n');
    setTimeout(() => {
      if (this.enabled) this.fmSynth.triggerAttackRelease('Db2', '8n');
    }, 80);
  }

  eraTransition() {
    if (!this.enabled || !this.initialized) return;
    // Sustained bell chord with reverb swell
    this.bellSynth.triggerAttackRelease('16n');

    // Layer with pad chord
    const chords = SoundEngine.CHORDS[this.currentMood] || SoundEngine.CHORDS.neutral;
    const chord = chords[0];
    this.padSynth.triggerAttackRelease(chord, '2n');

    // Trigger mood reassessment on next updateMood call
  }

  nuclear() {
    if (!this.enabled || !this.initialized) return;
    const Tone = window.Tone;

    // Cut everything to silence for 0.5s
    this.masterVol.volume.rampTo(-Infinity, 0.05);

    setTimeout(() => {
      if (!this.enabled) return;
      // Restore volume
      this.masterVol.volume.rampTo(this._dbFromLinear(this.volume), 0.1);
      // Deep subharmonic rumble at 30Hz with distortion, builds over 3s
      this.nuclearSynth.triggerAttackRelease('C1', 3);
    }, 500);
  }

  extinction() {
    if (!this.enabled || !this.initialized) return;
    const Tone = window.Tone;

    // Score deconstructs: slow down, detune, sparse out, fade
    const transport = Tone.getTransport();
    const originalBpm = transport.bpm.value;

    // Slow tempo over 4 seconds
    transport.bpm.rampTo(30, 4);

    // Detune pad
    if (this.padSynth) {
      this.padSynth.set({ detune: 0 });
      // Ramp detune (manual steps since detune ramp isn't directly supported on PolySynth)
      let detune = 0;
      const detuneInterval = setInterval(() => {
        detune -= 15;
        if (detune < -200) { clearInterval(detuneInterval); return; }
        try { this.padSynth.set({ detune }); } catch(e) {}
      }, 300);
    }

    // Fade to silence over 6 seconds
    this.masterVol.volume.rampTo(-Infinity, 6);

    // Restore after 8 seconds
    setTimeout(() => {
      if (this.padSynth) {
        try { this.padSynth.set({ detune: 0 }); } catch(e) {}
      }
      transport.bpm.value = originalBpm;
      if (this.enabled) {
        this.masterVol.volume.rampTo(this._dbFromLinear(this.volume), 2);
      }
    }, 8000);
  }

  transcendence() {
    if (!this.enabled || !this.initialized) return;
    const Tone = window.Tone;
    const transport = Tone.getTransport();

    // Score transforms: tempo accelerates, filter opens, harmonics stack
    transport.bpm.rampTo(140, 4);

    // Open filter completely
    this.filter.frequency.rampTo(8000, 3);

    // Stack ascending harmonics
    const harmonicNotes = ['C5', 'E5', 'G5', 'B5', 'D6', 'F#6', 'A6'];
    harmonicNotes.forEach((note, i) => {
      setTimeout(() => {
        if (!this.enabled) return;
        const s = new window.Tone.Synth({
          oscillator: { type: 'sine' },
          envelope: { attack: 0.1, decay: 0.5, sustain: 0.4, release: 2 },
          volume: -16 - i * 2,
        }).connect(this.reverb);
        s.triggerAttackRelease(note, '2n');
        setTimeout(() => s.dispose(), 5000);
      }, i * 350);
    });

    // Restore after 6 seconds
    setTimeout(() => {
      const settings = SoundEngine.MOOD_SETTINGS[this.currentMood] || SoundEngine.MOOD_SETTINGS.neutral;
      transport.bpm.rampTo(settings.bpm, 2);
      this.filter.frequency.rampTo(settings.filterFreq, 2);
    }, 6000);
  }

  verdictGood() {
    if (!this.enabled || !this.initialized) return;
    // Warm major chord, gentle arpeggio flourish, fade
    const notes = ['C4', 'E4', 'G4', 'C5'];
    notes.forEach((note, i) => {
      setTimeout(() => {
        if (!this.enabled) return;
        this.arpSynth.triggerAttackRelease(note, '4n');
      }, i * 200);
    });
    // Sustained warm chord
    setTimeout(() => {
      if (!this.enabled) return;
      this.padSynth.triggerAttackRelease(['C4', 'E4', 'G4', 'B4'], '1m');
    }, 800);
  }

  verdictBad() {
    if (!this.enabled || !this.initialized) return;
    // Dissonant cluster, slow fade
    this.padSynth.triggerAttackRelease(['C4', 'Db4', 'Fb4', 'Gb4'], '2m');
    this.masterVol.volume.rampTo(this._dbFromLinear(this.volume) - 10, 4);
    setTimeout(() => {
      if (this.enabled) this.masterVol.volume.rampTo(this._dbFromLinear(this.volume), 2);
    }, 5000);
  }

  verdictNeutral() {
    if (!this.enabled || !this.initialized) return;
    // Unresolved sus chord, held, slow fade
    this.padSynth.triggerAttackRelease(['C4', 'F4', 'G4'], '2m');
    this.masterVol.volume.rampTo(this._dbFromLinear(this.volume) - 6, 5);
    setTimeout(() => {
      if (this.enabled) this.masterVol.volume.rampTo(this._dbFromLinear(this.volume), 2);
    }, 6000);
  }

  startDrone(mood = 'neutral') {
    if (!this.enabled || !this.initialized) return;
    this.updateMood({ _forceMood: mood });
  }

  stopDrone() {
    if (!this.initialized) return;
    this._stopAmbient();
  }

  // ── Mood system ──

  updateMood(worldState) {
    if (!this.initialized) return;

    let newMood;
    if (worldState && worldState._forceMood) {
      newMood = worldState._forceMood;
    } else {
      newMood = this._calculateMood(worldState);
    }

    if (newMood === this.currentMood) return;

    this.targetMood = newMood;
    this._crossfadeToMood(newMood);
  }

  // ── Private: Mood calculation ──

  _calculateMood(ws) {
    if (!ws) return 'neutral';

    const existentialRisk = ws.existential_risk_cumulative || 0;
    const nuclearRisk = ws.nuclear_risk_level || 0;
    const polarization = ws.us_polarization || 0;
    const democracy = ws.global_democracy_index || 0;
    const renewable = ws.renewable_energy_share || 0;
    const spaceDev = ws.space_development_index || 0;
    const augmentation = ws.human_augmentation_prevalence || 0;
    const conflictDeaths = ws.conflict_deaths || 0;
    const biodiversity = ws.biodiversity_index || 0;

    // Dark: existential risk high or extinction-track
    if (existentialRisk > 0.3 || (nuclearRisk > 0.5 && biodiversity < 0.3)) {
      return 'dark';
    }

    // Transcendent: high tech + positive trajectory
    if (spaceDev > 0.4 && augmentation > 0.3 && democracy > 0.5 && existentialRisk < 0.15) {
      return 'transcendent';
    }

    // Tense: high polarization, conflict, or nuclear risk
    if (polarization > 0.6 || nuclearRisk > 0.35 || conflictDeaths > 200000) {
      return 'tense';
    }

    // Hopeful: democracy, renewables, low risk
    if (democracy > 0.65 && renewable > 0.3 && nuclearRisk < 0.25) {
      return 'hopeful';
    }

    return 'neutral';
  }

  // ── Private: Ambient score ──

  _startAmbient() {
    const Tone = window.Tone;
    if (!Tone) return;

    const transport = Tone.getTransport();
    const settings = SoundEngine.MOOD_SETTINGS[this.currentMood];
    transport.bpm.value = settings.bpm;

    // Pad loop: play chord every N measures depending on mood
    this.chordIndex = 0;
    const barsPerChord = this._barsPerChord();
    this.padLoop = new Tone.Loop((time) => {
      const chords = SoundEngine.CHORDS[this.currentMood] || SoundEngine.CHORDS.neutral;
      const chord = chords[this.chordIndex % chords.length];
      this.padSynth.triggerAttackRelease(chord, `${barsPerChord}m`, time);

      // Sub bass on root
      const root = chord[0];
      const bassNote = this._transposeDown(root, 1);
      this.bassSynth.triggerAttackRelease(bassNote, `${barsPerChord}m`, time);

      this.chordIndex++;
    }, `${barsPerChord}m`);

    // Arp loop
    this.arpNoteIndex = 0;
    const arpConfig = SoundEngine.ARP_PATTERNS[this.currentMood] || SoundEngine.ARP_PATTERNS.neutral;
    this.arpLoop = new Tone.Loop((time) => {
      const chords = SoundEngine.CHORDS[this.currentMood] || SoundEngine.CHORDS.neutral;
      const chord = chords[this.chordIndex % chords.length];
      if (!chord || chord.length === 0) return;

      let noteIdx;
      if (arpConfig.direction === 'up') {
        noteIdx = this.arpNoteIndex % chord.length;
      } else if (arpConfig.direction === 'upDown') {
        const cycle = chord.length * 2 - 2;
        const pos = this.arpNoteIndex % (cycle || 1);
        noteIdx = pos < chord.length ? pos : cycle - pos;
      } else {
        // random
        noteIdx = Math.floor(Math.random() * chord.length);
      }

      const note = chord[Math.min(noteIdx, chord.length - 1)];
      this.arpSynth.triggerAttackRelease(note, arpConfig.subdivision, time);
      this.arpNoteIndex++;
    }, arpConfig.subdivision);

    this.padLoop.start(0);
    this.arpLoop.start(0);

    // Apply mood volumes
    this.padSynth.volume.value = settings.padVol;
    this.arpSynth.volume.value = settings.arpVol;
    this.bassSynth.volume.value = settings.bassVol;
    this.filter.frequency.value = settings.filterFreq;

    if (transport.state !== 'started') {
      transport.start();
    }
  }

  _stopAmbient() {
    if (this.padLoop) { this.padLoop.stop(); this.padLoop.dispose(); this.padLoop = null; }
    if (this.arpLoop) { this.arpLoop.stop(); this.arpLoop.dispose(); this.arpLoop = null; }
  }

  _crossfadeToMood(newMood) {
    if (this.moodTransitioning) {
      // If already transitioning, just update target
      this.currentMood = newMood;
      return;
    }
    this.moodTransitioning = true;

    const Tone = window.Tone;
    const settings = SoundEngine.MOOD_SETTINGS[newMood] || SoundEngine.MOOD_SETTINGS.neutral;
    const transitionTime = 4; // seconds

    // Crossfade settings smoothly
    Tone.getTransport().bpm.rampTo(settings.bpm, transitionTime);
    this.filter.frequency.rampTo(settings.filterFreq, transitionTime);
    this.padSynth.volume.rampTo(settings.padVol, transitionTime);
    this.arpSynth.volume.rampTo(settings.arpVol, transitionTime);
    this.bassSynth.volume.rampTo(settings.bassVol, transitionTime);

    // Update pad envelope
    try {
      this.padSynth.set({
        envelope: { attack: settings.padAttack, release: settings.padRelease },
      });
    } catch(e) { /* PolySynth may not support live envelope changes on all voices */ }

    // Rebuild arp loop with new subdivision
    const arpConfig = SoundEngine.ARP_PATTERNS[newMood] || SoundEngine.ARP_PATTERNS.neutral;
    if (this.arpLoop) {
      this.arpLoop.stop();
      this.arpLoop.dispose();
    }
    this.arpNoteIndex = 0;
    this.arpLoop = new Tone.Loop((time) => {
      const chords = SoundEngine.CHORDS[this.currentMood] || SoundEngine.CHORDS.neutral;
      const chord = chords[this.chordIndex % chords.length];
      if (!chord || chord.length === 0) return;

      let noteIdx;
      if (arpConfig.direction === 'up') {
        noteIdx = this.arpNoteIndex % chord.length;
      } else if (arpConfig.direction === 'upDown') {
        const cycle = chord.length * 2 - 2;
        const pos = this.arpNoteIndex % (cycle || 1);
        noteIdx = pos < chord.length ? pos : cycle - pos;
      } else {
        noteIdx = Math.floor(Math.random() * chord.length);
      }

      const note = chord[Math.min(noteIdx, chord.length - 1)];
      this.arpSynth.triggerAttackRelease(note, arpConfig.subdivision, time);
      this.arpNoteIndex++;
    }, arpConfig.subdivision);
    this.arpLoop.start(0);

    // Rebuild pad loop with new bar length
    const barsPerChord = this._barsPerChordForMood(newMood);
    if (this.padLoop) {
      this.padLoop.stop();
      this.padLoop.dispose();
    }
    this.chordIndex = 0;
    this.padLoop = new Tone.Loop((time) => {
      const chords = SoundEngine.CHORDS[this.currentMood] || SoundEngine.CHORDS.neutral;
      const chord = chords[this.chordIndex % chords.length];
      this.padSynth.triggerAttackRelease(chord, `${barsPerChord}m`, time);
      const root = chord[0];
      const bassNote = this._transposeDown(root, 1);
      this.bassSynth.triggerAttackRelease(bassNote, `${barsPerChord}m`, time);
      this.chordIndex++;
    }, `${barsPerChord}m`);
    this.padLoop.start(0);

    // Mark mood as current
    this.currentMood = newMood;

    setTimeout(() => {
      this.moodTransitioning = false;
    }, transitionTime * 1000);
  }

  _barsPerChord() {
    return this._barsPerChordForMood(this.currentMood);
  }

  _barsPerChordForMood(mood) {
    const totalBars = SoundEngine.MOOD_BARS[mood] || 12;
    const numChords = (SoundEngine.CHORDS[mood] || SoundEngine.CHORDS.neutral).length;
    return Math.max(1, Math.floor(totalBars / numChords));
  }

  _transposeDown(note, octaves) {
    // Simple transpose: extract note name and octave, subtract octaves
    const match = note.match(/^([A-G][#b]?)(\d+)$/);
    if (!match) return note;
    const newOctave = Math.max(1, parseInt(match[2], 10) - octaves);
    return match[1] + newOctave;
  }

  _dbFromLinear(v) {
    // Convert 0-1 linear to dB, with floor at -60dB
    if (v <= 0) return -Infinity;
    return 20 * Math.log10(v);
  }

  // Keep ctx getter for compatibility with viewer.js play() check
  get ctx() {
    return this.initialized ? true : null;
  }
}
