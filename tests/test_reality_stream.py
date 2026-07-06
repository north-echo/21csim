"""Tests for the reality stream: analyst validation, node YAML, file updates."""

from __future__ import annotations

import asyncio
import json

import pytest
import yaml

from csim.llm.analyst import (
    DIMENSION_DESCRIPTIONS,
    analyze_news,
    build_analyst_prompt,
    build_node_yaml,
    validate_dimension_updates,
)
from csim.llm.base import LLMProvider
from csim.reality_stream import (
    _write_reality_yaml,
    export_reality_snapshot,
    update_reality,
)
from csim.world_state import _META_FIELDS, WorldState


class FakeProvider(LLMProvider):
    """Returns a canned response for analyze_news tests."""

    def __init__(self, response: str):
        self.response = response

    async def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return self.response

    def is_available(self) -> bool:
        return True

    def model_name(self) -> str:
        return "fake"


NEWS = [{"title": "War breaks out", "description": "Bad news", "published_at": "2026-07-01"}]
STATE = {"middle_east_stability": 0.4, "conflict_deaths": 1_500_000}


# ── Dimension coverage ──


def test_descriptions_cover_all_world_state_dimensions():
    """Every simulation dimension should be describable/updatable by the analyst."""
    sim_dims = {f for f in WorldState.__dataclass_fields__ if f not in _META_FIELDS} - {
        "first_divergence_year",
        "largest_divergence",
    }
    missing = sim_dims - set(DIMENSION_DESCRIPTIONS)
    assert not missing, f"Dimensions unknown to the analyst: {sorted(missing)}"


def test_descriptions_contain_no_unknown_dimensions():
    unknown = set(DIMENSION_DESCRIPTIONS) - set(WorldState.__dataclass_fields__)
    assert not unknown, f"Analyst describes nonexistent dimensions: {sorted(unknown)}"


# ── validate_dimension_updates ──


def test_validate_filters_unknown_dimensions():
    out = validate_dimension_updates({"middle_east_stability": 0.5, "not_a_dim": 1.0})
    assert out == {"middle_east_stability": 0.5}


def test_validate_clamps_out_of_range_values():
    out = validate_dimension_updates(
        {"global_democracy_index": 47.0, "nuclear_risk_level": -3, "climate_temp_anomaly": 2.1}
    )
    assert out["global_democracy_index"] == 1.0
    assert out["nuclear_risk_level"] == 0.0
    assert out["climate_temp_anomaly"] == 2.1


def test_validate_coerces_and_rejects_non_numeric():
    out = validate_dimension_updates(
        {"eu_cohesion": "0.8", "us_polarization": "very high", "russia_stability": None}
    )
    assert out == {"eu_cohesion": 0.8}


def test_validate_int_dimensions():
    out = validate_dimension_updates(
        {"conflict_deaths": 1_650_000.7, "ai_development_year_offset": -2.0}
    )
    assert out["conflict_deaths"] == 1_650_000
    assert out["ai_development_year_offset"] == -2


def test_validate_death_counts_not_negative():
    out = validate_dimension_updates({"conflict_deaths": -5})
    assert out["conflict_deaths"] == 0


# ── analyze_news ──


def _analyze(response: str) -> dict:
    provider = FakeProvider(response)
    return asyncio.run(analyze_news(provider, NEWS, STATE))


def test_analyze_news_parses_plain_json():
    result = _analyze(
        json.dumps(
            {
                "dimension_updates": {"middle_east_stability": 0.3},
                "new_nodes": [],
                "reasoning": "test",
            }
        )
    )
    assert result["dimension_updates"] == {"middle_east_stability": 0.3}
    assert result["reasoning"] == "test"


def test_analyze_news_strips_markdown_fences():
    payload = json.dumps({"dimension_updates": {"eu_cohesion": 0.7}, "new_nodes": []})
    result = _analyze(f"```json\n{payload}\n```")
    assert result["dimension_updates"] == {"eu_cohesion": 0.7}


def test_analyze_news_raises_on_invalid_json():
    with pytest.raises(ValueError, match="invalid JSON"):
        _analyze("The situation is concerning.")


def test_analyze_news_clamps_hallucinated_values():
    result = _analyze(
        json.dumps(
            {
                "dimension_updates": {"global_democracy_index": 47, "fake_dim": 1},
                "new_nodes": [],
            }
        )
    )
    assert result["dimension_updates"] == {"global_democracy_index": 1.0}


def test_prompt_includes_state_and_news():
    prompt = build_analyst_prompt(NEWS, STATE, last_update="2026-06-01")
    assert "War breaks out" in prompt
    assert "middle_east_stability: 0.4" in prompt
    assert "2026-06-01" in prompt


# ── build_node_yaml ──


def test_build_node_yaml_roundtrip():
    node = {
        "id": "2026_test_event",
        "year_month": "2026-06",
        "title": "Test Event",
        "description": "Something happened.",
        "domain": "geopolitical",
        "world_state_effects": {"middle_east_stability": "-0.10"},
        "cascading_modifiers": {"2030_oil_shock.middle_east_stability": "*0.9"},
    }
    parsed = yaml.safe_load(build_node_yaml(node))
    assert parsed["id"] == "2026_test_event"
    assert parsed["confidence"] == "HIGH"
    # Locked distribution: single branch with probability 1.0
    assert parsed["distribution"]["options"] == {"test_event": 1.0}
    outcome = parsed["outcomes"]["test_event"]
    assert outcome["status"] == "HISTORICAL"
    assert outcome["world_state_effects"] == {"middle_east_stability": "-0.10"}
    assert outcome["cascading_modifiers"] == {"2030_oil_shock.middle_east_stability": "*0.9"}


# ── update_reality / file IO ──


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "nodes").mkdir()
    (tmp_path / "reality_2026.yaml").write_text(
        "year: 2026\nmiddle_east_stability: 0.4\nconflict_deaths: 1500000\n"
    )
    return tmp_path


def test_update_reality_applies_updates_and_logs(data_dir):
    node = {
        "id": "2026_new_event",
        "year_month": "2026-06",
        "title": "New Event",
        "description": "d",
        "world_state_effects": {},
    }
    update_reality(
        data_dir,
        {"middle_east_stability": 0.3},
        [node],
        update_log={"reasoning": "escalation"},
    )

    reality = yaml.safe_load((data_dir / "reality_2026.yaml").read_text())
    assert reality["middle_east_stability"] == 0.3
    assert reality["year"] == 2026
    assert (data_dir / "nodes" / "2026_new_event.yaml").exists()

    log = json.loads((data_dir / "reality_stream_log.json").read_text())
    assert log[-1]["new_nodes"] == ["2026_new_event"]
    assert log[-1]["reasoning"] == "escalation"


def test_update_reality_never_overwrites_existing_node(data_dir):
    existing = data_dir / "nodes" / "2026_existing.yaml"
    existing.write_text("id: 2026_existing\n")
    node = {
        "id": "2026_existing",
        "year_month": "2026-01",
        "title": "x",
        "description": "d",
        "world_state_effects": {},
    }
    update_reality(data_dir, {}, [node])
    assert existing.read_text() == "id: 2026_existing\n"


def test_write_reality_yaml_preserves_all_dimensions(data_dir):
    """Rewriting the file must not silently drop any dimension."""
    data = {f: 0.5 for f in WorldState.__dataclass_fields__ if f not in _META_FIELDS}
    data.pop("first_divergence_year", None)
    data.pop("largest_divergence", None)
    data["year"] = 2026
    path = data_dir / "reality_2026.yaml"
    _write_reality_yaml(path, data)
    reread = yaml.safe_load(path.read_text())
    missing = set(data) - set(reread)
    assert not missing, f"Dimensions dropped on rewrite: {sorted(missing)}"


def test_export_reality_snapshot(data_dir, tmp_path):
    (data_dir / "reality_stream_log.json").write_text(
        json.dumps([{"timestamp": "2026-07-01T00:00:00Z", "dimension_updates": {}}])
    )
    out = export_reality_snapshot(data_dir, tmp_path / "web" / "reality.json")
    snapshot = json.loads(out.read_text())
    assert snapshot["reality"]["middle_east_stability"] == 0.4
    assert len(snapshot["stream_log"]) == 1
    assert "generated" in snapshot


# ── validate_new_nodes ──


def test_validate_new_nodes_accepts_well_formed():
    from csim.llm.analyst import validate_new_nodes

    nodes = validate_new_nodes([{
        "id": "2026_test_war",
        "year_month": "2026-06",
        "title": "Test War",
        "description": "d",
        "domain": "geopolitical",
        "world_state_effects": {"middle_east_stability": "-0.1", "bogus_dim": "+1"},
    }])
    assert len(nodes) == 1
    # Unknown-dimension effects are stripped
    assert nodes[0]["world_state_effects"] == {"middle_east_stability": "-0.1"}


def test_validate_new_nodes_rejects_malformed():
    from csim.llm.analyst import validate_new_nodes

    bad = [
        {"id": "no_year_prefix", "year_month": "2026-06", "title": "t", "description": "d"},
        {"id": "2026_ok", "year_month": "June 2026", "title": "t", "description": "d"},
        {"id": "2026_ok", "year_month": "2026-06", "title": "", "description": "d"},
        "not a dict",
    ]
    assert validate_new_nodes(bad) == []


def test_validate_new_nodes_defaults_unknown_domain():
    from csim.llm.analyst import validate_new_nodes

    nodes = validate_new_nodes([{
        "id": "2026_thing",
        "year_month": "2026-01",
        "title": "t",
        "description": "d",
        "domain": "vibes",
    }])
    assert nodes[0]["domain"] == "geopolitical"


# ── Format stability ──


def test_write_reality_yaml_is_idempotent(data_dir):
    """Rewriting an already-generated file must produce byte-identical output
    (modulo the timestamp header) so weekly PRs only diff real changes."""
    import re

    data = {"year": 2026, "us_polarization": 0.72, "global_gdp_growth_modifier": 1.0,
            "russia_stability": 0.29, "conflict_deaths": 1_503_000,
            "ai_development_year_offset": 5, "climate_temp_anomaly": 1.3}
    path = data_dir / "reality_2026.yaml"

    strip_ts = lambda s: re.sub(r"# Last update:.*", "", s)  # noqa: E731
    _write_reality_yaml(path, data)
    first = strip_ts(path.read_text())
    _write_reality_yaml(path, yaml.safe_load(path.read_text()))
    second = strip_ts(path.read_text())
    assert first == second


def test_fmt_value_canonical():
    from csim.reality_stream import _fmt_value

    assert _fmt_value(0.3) == "0.3"
    assert _fmt_value(0.32) == "0.32"
    assert _fmt_value(1.0) == "1.0"          # stays a YAML float
    assert _fmt_value(1_503_000) == "1503000"
    assert _fmt_value(5) == "5"
    assert _fmt_value(0.30000000000000004) == "0.3"  # float noise squashed
    # Round-trips as the same type and value
    assert yaml.safe_load(f"x: {_fmt_value(1.0)}")["x"] == 1.0
    assert isinstance(yaml.safe_load(f"x: {_fmt_value(1.0)}")["x"], float)
