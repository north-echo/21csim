"""Runtime audio synthesis using numpy. Zero overhead when disabled."""

from __future__ import annotations

import atexit
import os
import platform
import shutil
import struct
import subprocess
import tempfile
import threading
from pathlib import Path

import numpy as np


def _detect_player() -> str | None:
    """Detect system audio player."""
    if platform.system() == "Darwin":
        if shutil.which("afplay"):
            return "afplay"
    elif platform.system() == "Linux":
        for player in ("paplay", "aplay"):
            if shutil.which(player):
                return player
    return None


def _make_wav(samples: np.ndarray, sample_rate: int = 44100) -> bytes:
    """Convert float samples to WAV bytes."""
    # Clip and convert to 16-bit PCM
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype(np.int16)
    data = pcm.tobytes()

    # WAV header
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(data),
        b"WAVE",
        b"fmt ",
        16,  # chunk size
        1,   # PCM
        1,   # mono
        sample_rate,
        sample_rate * 2,  # byte rate
        2,   # block align
        16,  # bits per sample
        b"data",
        len(data),
    )
    return header + data


def _sine(freq: float, duration: float, sample_rate: int = 44100) -> np.ndarray:
    """Generate sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _envelope(samples: np.ndarray, attack: float = 0.01, decay: float = 0.5,
              sustain_level: float = 0.0, release: float = 0.5,
              sample_rate: int = 44100) -> np.ndarray:
    """Apply ADSR envelope."""
    n = len(samples)
    env = np.zeros(n)

    a_samples = int(attack * sample_rate)
    d_samples = int(decay * sample_rate)
    r_samples = int(release * sample_rate)
    s_samples = max(0, n - a_samples - d_samples - r_samples)

    idx = 0
    # Attack
    end = min(idx + a_samples, n)
    env[idx:end] = np.linspace(0, 1, end - idx)
    idx = end
    # Decay
    end = min(idx + d_samples, n)
    env[idx:end] = np.linspace(1, sustain_level, end - idx)
    idx = end
    # Sustain
    end = min(idx + s_samples, n)
    env[idx:end] = sustain_level
    idx = end
    # Release
    end = min(idx + r_samples, n)
    env[idx:end] = np.linspace(sustain_level, 0, end - idx)

    return samples * env


class SoundEngine:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._player = None
        self._temp_dir = None
        self._cues: dict[str, Path] = {}

        if not enabled:
            return

        self._player = _detect_player()
        if not self._player:
            self.enabled = False
            return

        self._temp_dir = Path(tempfile.mkdtemp(prefix="21csim_sound_"))
        atexit.register(self.shutdown)
        self._generate_all_cues()

    def _generate_all_cues(self) -> None:
        """Pre-generate all tone cues as WAV files."""
        sr = 44100

        # Era transition: open fifth (A2+E3), hollow bell
        samples = 0.5 * _sine(110, 1.2, sr) + 0.5 * _sine(165, 1.2, sr)
        samples = _envelope(samples, attack=0.01, decay=0.3, sustain_level=0.3, release=0.6, sample_rate=sr)
        self._save_cue("era_transition", samples * 0.4)

        # Nuclear: subsonic throb (55+58 Hz, 3 Hz beat)
        samples = 0.5 * _sine(55, 1.5, sr) + 0.5 * _sine(58, 1.5, sr)
        samples = _envelope(samples, attack=0.5, decay=0.2, sustain_level=0.6, release=0.3, sample_rate=sr)
        self._save_cue("nuclear", samples * 0.5)

        # Extinction: A minor chord fading
        samples = 0.4 * _sine(220, 2.5, sr) + 0.3 * _sine(277, 2.5, sr) + 0.3 * _sine(330, 2.5, sr)
        samples = _envelope(samples, attack=0.1, decay=0.5, sustain_level=0.5, release=1.4, sample_rate=sr)
        self._save_cue("extinction", samples * 0.4)

        # Transcendence: rising harmonic stack
        t = np.linspace(0, 2.0, int(sr * 2.0), endpoint=False)
        freq_sweep = np.linspace(220, 660, len(t))
        samples = np.sin(2 * np.pi * freq_sweep * t / sr * sr)
        # Add harmonics
        samples = samples * 0.5 + 0.3 * np.sin(2 * np.pi * freq_sweep * 2 * t / sr * sr) + 0.2 * np.sin(2 * np.pi * freq_sweep * 3 * t / sr * sr)
        samples = _envelope(samples, attack=0.3, decay=0.2, sustain_level=0.7, release=0.8, sample_rate=sr)
        self._save_cue("transcendence", samples * 0.3)

        # Verdict good: C major
        samples = 0.4 * _sine(262, 1.0, sr) + 0.3 * _sine(330, 1.0, sr) + 0.3 * _sine(392, 1.0, sr)
        samples = _envelope(samples, attack=0.05, decay=0.2, sustain_level=0.4, release=0.5, sample_rate=sr)
        self._save_cue("verdict_good", samples * 0.35)

        # Verdict bad: Bb minor
        samples = 0.4 * _sine(233, 1.0, sr) + 0.3 * _sine(277, 1.0, sr) + 0.3 * _sine(349, 1.0, sr)
        samples = _envelope(samples, attack=0.05, decay=0.2, sustain_level=0.4, release=0.5, sample_rate=sr)
        self._save_cue("verdict_bad", samples * 0.35)

        # Verdict neutral: sus4
        samples = 0.5 * _sine(262, 1.0, sr) + 0.5 * _sine(349, 1.0, sr)
        samples = _envelope(samples, attack=0.05, decay=0.2, sustain_level=0.4, release=0.5, sample_rate=sr)
        self._save_cue("verdict_neutral", samples * 0.35)

        # Divergence major: sonar ping
        samples = _sine(440, 0.15, sr)
        samples = _envelope(samples, attack=0.001, decay=0.05, sustain_level=0.0, release=0.1, sample_rate=sr)
        self._save_cue("divergence_major", samples * 0.3)

    def _save_cue(self, name: str, samples: np.ndarray) -> None:
        """Save generated samples as WAV file."""
        wav_data = _make_wav(samples)
        path = self._temp_dir / f"{name}.wav"
        path.write_bytes(wav_data)
        self._cues[name] = path

    def play(self, cue_name: str) -> None:
        """Fire-and-forget playback in daemon thread."""
        if not self.enabled or cue_name not in self._cues:
            return

        path = self._cues[cue_name]

        def _play():
            try:
                subprocess.run(
                    [self._player, str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except Exception:
                pass

        t = threading.Thread(target=_play, daemon=True)
        t.start()

    def shutdown(self) -> None:
        """Clean up temp WAV files."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
