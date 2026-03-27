"""Tests for LLM narration layer."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from csim.llm.base import LLMProvider
from csim.llm.null import NullProvider
from csim.llm.resolver import resolve_provider
from csim.llm.prompts import build_local_prompt, build_claude_prompt, build_headline_prompt
from csim.llm.cache import cache_narration, load_cached_narration, _CACHE_DIR
from csim.llm.narrator import get_narration, should_narrate
from csim.models import SimEvent, EventStatus


@pytest.fixture
def sample_event():
    return SimEvent(
        year_month="2003-03",
        node_id="2003_iraq",
        title="Iraq War Decision",
        description="UN inspections continue; no military action taken",
        status=EventStatus.DIVERGENCE,
        branch_taken="diplomatic_resolution",
        domain="geopolitical",
        probability_of_branch=0.22,
        explanation="Inspectors given more time; WMD claims debunked",
    )


@pytest.fixture
def sample_events(sample_event):
    preceding = SimEvent(
        year_month="2001-09",
        node_id="2001_911",
        title="September 11 Attacks",
        description="Plot disrupted by FBI",
        status=EventStatus.DIVERGENCE,
        branch_taken="plot_disrupted",
        domain="security",
        probability_of_branch=0.17,
    )
    return [preceding, sample_event]


class TestNullProvider:
    def test_generate(self):
        p = NullProvider()
        result = asyncio.run(p.generate("test"))
        assert result == ""

    def test_is_available(self):
        assert NullProvider().is_available()

    def test_model_name(self):
        assert NullProvider().model_name() == "none"


class TestResolver:
    def test_resolve_none(self):
        p = resolve_provider("none")
        assert isinstance(p, NullProvider)

    def test_resolve_default_no_ollama(self):
        # With no Ollama running, should fall back to NullProvider
        p = resolve_provider()
        assert isinstance(p, NullProvider)

    def test_resolve_claude_without_key(self):
        with patch.dict("os.environ", {}, clear=True), \
             patch("csim.llm.claude._load_dotenv_key", return_value=""):
            p = resolve_provider("claude")
            assert p.model_name().startswith("claude/")
            assert not p.is_available()


class TestPrompts:
    def test_local_prompt(self, sample_event, sample_events):
        prompt = build_local_prompt(sample_event, sample_events[:-1])
        assert "Iraq" in prompt or "inspections" in prompt
        assert "2-3 sentences" in prompt

    def test_claude_prompt(self, sample_event, sample_events):
        prompt = build_claude_prompt(sample_event, sample_events, 1)
        assert "2-4 sentences" in prompt
        assert "diplomatic_resolution" in prompt

    def test_headline_prompt(self, sample_events):
        prompt = build_headline_prompt(sample_events, "PROGRESS", 0.45)
        assert "PROGRESS" in prompt
        assert "5-10 words" in prompt


class TestCache:
    def test_cache_round_trip(self, tmp_path, monkeypatch):
        monkeypatch.setattr("csim.llm.cache._CACHE_DIR", tmp_path)
        cache_narration(42, "2003_iraq", "The inspections continued.", source="test")
        result = load_cached_narration(42, "2003_iraq")
        assert result == "The inspections continued."

    def test_cache_miss(self, tmp_path, monkeypatch):
        monkeypatch.setattr("csim.llm.cache._CACHE_DIR", tmp_path)
        result = load_cached_narration(99999, "nonexistent")
        assert result is None


class TestNarrator:
    def test_should_narrate_divergence(self, sample_event):
        assert should_narrate(sample_event) is True

    def test_should_narrate_historical(self):
        e = SimEvent(
            year_month="2001-12",
            node_id="2001_china_wto",
            title="China WTO",
            description="China joins WTO",
            status=EventStatus.HISTORICAL,
            branch_taken="historical",
            domain="economic",
            probability_of_branch=0.80,
        )
        assert should_narrate(e) is False

    def test_should_narrate_high_impact_historical(self):
        e = SimEvent(
            year_month="2001-09",
            node_id="2001_911",
            title="September 11",
            description="Full attack",
            status=EventStatus.HISTORICAL,
            branch_taken="historical_full",
            domain="security",
            probability_of_branch=0.28,
            is_high_impact=True,
        )
        assert should_narrate(e) is True

    def test_get_narration_null_provider(self, sample_event, sample_events):
        result = asyncio.run(
            get_narration(42, sample_event, sample_events, 1, NullProvider())
        )
        assert result is None  # NullProvider returns "", which is falsy

    def test_get_narration_no_provider(self, sample_event, sample_events):
        result = asyncio.run(
            get_narration(42, sample_event, sample_events, 1, None)
        )
        assert result is None
