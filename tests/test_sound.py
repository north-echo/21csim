"""Tests for sound engine."""

from csim.sound import SoundEngine


class TestSoundEngine:
    def test_disabled_is_noop(self):
        engine = SoundEngine(enabled=False)
        assert not engine.enabled
        engine.play("era_transition")  # Should not raise
        engine.shutdown()  # Should not raise

    def test_enabled_generates_cues(self):
        engine = SoundEngine(enabled=True)
        if engine.enabled:  # May be disabled if no player found
            assert len(engine._cues) == 8
            for name, path in engine._cues.items():
                assert path.exists()
                assert path.stat().st_size > 0
            engine.shutdown()

    def test_play_unknown_cue(self):
        engine = SoundEngine(enabled=True)
        engine.play("nonexistent")  # Should not raise
        engine.shutdown()

    def test_shutdown_cleans_up(self):
        engine = SoundEngine(enabled=True)
        if engine.enabled:
            temp_dir = engine._temp_dir
            assert temp_dir.exists()
            engine.shutdown()
            assert not temp_dir.exists()
