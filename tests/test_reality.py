"""Tests for load_reality locking and --from-reality effect handling (fix B)."""

from __future__ import annotations

import textwrap

import pytest

from csim.engine import simulate
from csim.graph import build_graph
from csim.reality import load_reality

# Reality baseline the synthetic scenario starts from.
_REALITY_YAML = textwrap.dedent(
    """\
    year: 2026
    middle_east_stability: 0.40
    nuclear_risk_level: 0.30
    supply_chain_resilience: 0.50
    food_security_index: 0.70
    """
)

# A pre-reality-year historical event (effects baked into the baseline).
_NODE_PRE = textwrap.dedent(
    """\
    id: "2010_quake"
    year_month: "2010-01"
    title: "Historical Quake"
    description: "d"
    domain: "climate"
    distribution:
      type: "categorical"
      options:
        happened: 1.0
    outcomes:
      happened:
        status: "HISTORICAL"
        description: "d"
        world_state_effects:
          middle_east_stability: "-0.10"
    """
)

# A settled present-year reality-stream event (explicit HISTORICAL branch).
_NODE_SETTLED = textwrap.dedent(
    """\
    id: "2026_war"
    year_month: "2026-07"
    title: "Settled War"
    description: "d"
    domain: "geopolitical"
    distribution:
      type: "categorical"
      options:
        war: 1.0
    outcomes:
      war:
        status: "HISTORICAL"
        description: "d"
        world_state_effects:
          nuclear_risk_level: "+0.10"
    """
)

# A genuine present-year forecast (no HISTORICAL branch -> must stay sampled).
_NODE_FORECAST = textwrap.dedent(
    """\
    id: "2026_forecast"
    year_month: "2026-06"
    title: "Open Forecast"
    description: "d"
    domain: "economic"
    distribution:
      type: "categorical"
      options:
        up: 1.0
    outcomes:
      up:
        description: "d"
        world_state_effects:
          supply_chain_resilience: "+0.05"
    """
)

# A future event (after the reality year) -> sampled, effects applied.
_NODE_FUTURE = textwrap.dedent(
    """\
    id: "2027_future"
    year_month: "2027-03"
    title: "Future Shock"
    description: "d"
    domain: "shock"
    distribution:
      type: "categorical"
      options:
        hit: 1.0
    outcomes:
      hit:
        status: "DIVERGENCE"
        description: "d"
        world_state_effects:
          food_security_index: "-0.10"
    """
)


@pytest.fixture
def scenario(tmp_path):
    (tmp_path / "reality_2026.yaml").write_text(_REALITY_YAML)
    nodes = tmp_path / "nodes"
    nodes.mkdir()
    (nodes / "2010_quake.yaml").write_text(_NODE_PRE)
    (nodes / "2026_war.yaml").write_text(_NODE_SETTLED)
    (nodes / "2026_forecast.yaml").write_text(_NODE_FORECAST)
    (nodes / "2027_future.yaml").write_text(_NODE_FUTURE)
    return tmp_path


def test_initial_state_reflects_reality(scenario):
    state, _ = load_reality(scenario)
    assert state.middle_east_stability == 0.40
    assert state.nuclear_risk_level == 0.30


def test_locks_pre_year_and_settled_present_events(scenario):
    _, locked = load_reality(scenario)
    assert locked["2010_quake"] == "happened"   # pre-reality-year historical
    assert locked["2026_war"] == "war"           # present-year settled (explicit HISTORICAL)


def test_does_not_lock_forecasts_or_future(scenario):
    _, locked = load_reality(scenario)
    # Present-year forecast with no HISTORICAL branch stays sampled...
    assert "2026_forecast" not in locked
    # ...and anything after the reality year is future, never locked.
    assert "2027_future" not in locked


def test_from_reality_skips_locked_effects(scenario):
    """With apply_locked_effects=False the baseline is authoritative: locked
    historical effects are NOT re-applied, but unlocked (forecast/future)
    effects still are."""
    graph = build_graph(scenario)
    state, locked = load_reality(scenario)

    out = simulate(graph, seed=1, initial_state=state,
                   locked_results=locked, apply_locked_effects=False)
    final = out.final_state

    # Locked historical effects skipped -> dimensions stay at the reality baseline.
    assert final.nuclear_risk_level == 0.30        # 2026_war "+0.10" skipped
    assert final.middle_east_stability == 0.40     # 2010_quake "-0.10" skipped
    # Unlocked forecast/future effects still apply.
    assert final.supply_chain_resilience == pytest.approx(0.55)  # forecast "+0.05"
    assert final.food_security_index == pytest.approx(0.60)      # 2027 future "-0.10"


def test_default_replay_applies_locked_effects(scenario):
    """Default (apply_locked_effects=True) preserves the original replay
    behaviour: locked historical effects ARE applied on top of the state."""
    graph = build_graph(scenario)
    state, locked = load_reality(scenario)

    out = simulate(graph, seed=1, initial_state=state,
                   locked_results=locked, apply_locked_effects=True)
    final = out.final_state

    assert final.nuclear_risk_level == pytest.approx(0.40)      # +0.10 applied
    assert final.middle_east_stability == pytest.approx(0.30)   # -0.10 applied


def test_locked_events_still_appear_on_timeline(scenario):
    """Skipping effects must not drop the events themselves from the timeline."""
    graph = build_graph(scenario)
    state, locked = load_reality(scenario)
    out = simulate(graph, seed=1, initial_state=state,
                   locked_results=locked, apply_locked_effects=False)
    node_ids = {e.node_id for e in out.events}
    assert {"2010_quake", "2026_war", "2026_forecast", "2027_future"} <= node_ids
