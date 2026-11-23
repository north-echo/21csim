"""Load real-world 2026 state and determine historical node outcomes."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import yaml

from csim.world_state import WorldState


def load_reality(data_dir: Path) -> tuple[WorldState, dict[str, str]]:
    """Load real-world state and determine historical node outcomes.

    Args:
        data_dir: Path to the csim data directory (containing reality_2026.yaml
                  and nodes/).

    Returns:
        state: WorldState initialized to real 2026 values.
        locked_results: dict mapping node_id -> historical branch for all
                        pre-2026 nodes.
    """
    # ── Load reality YAML ──
    reality_path = data_dir / "reality_2026.yaml"
    if not reality_path.exists():
        raise FileNotFoundError(f"Reality data not found: {reality_path}")

    with open(reality_path) as f:
        reality_data = yaml.safe_load(f)

    # ── Build WorldState from reality data ──
    state = WorldState()
    ws_field_names = {f.name for f in fields(WorldState)}
    for key, value in reality_data.items():
        if key == "year":
            continue
        if key in ws_field_names:
            setattr(state, key, value)

    # The reality snapshot represents the world as of the present day. Anything
    # dated in or before the reality year has already happened; later nodes are
    # the future being simulated.
    reality_year = int(reality_data.get("year", 2026))
    future_cutoff = f"{reality_year + 1}-01"  # first year_month that is "future"

    # ── Determine locked results for settled (historical) nodes ──
    locked_results: dict[str, str] = {}
    nodes_dir = data_dir / "nodes"

    if not nodes_dir.exists():
        return state, locked_results

    for yaml_file in sorted(nodes_dir.glob("*.yaml")):
        with open(yaml_file) as f:
            node_data = yaml.safe_load(f)

        if not node_data or "id" not in node_data:
            continue

        year_month = node_data.get("year_month", "")
        if not year_month:
            continue

        # Future nodes (after the reality year) stay probabilistic.
        if year_month >= future_cutoff:
            continue

        node_id = node_data["id"]
        outcomes = node_data.get("outcomes", {})
        if not isinstance(outcomes, dict) or not outcomes:
            continue

        if year_month < f"{reality_year}-01":
            # Strictly pre-reality-year: lock to the historical outcome, falling
            # back to the most-likely branch (preserves long-standing behaviour).
            branch = _find_historical_branch(outcomes)
        else:
            # Within the reality year itself, lock ONLY nodes that carry an
            # explicit HISTORICAL branch (settled reality-stream events such as
            # 2026_hormuz_crisis and the weekly reality-pulse nodes). Genuine
            # present-year forecasts with no historical outcome (e.g. the Taiwan
            # or Artemis nodes) are left to be sampled, not pinned to a guess.
            branch = _find_explicit_historical_branch(outcomes)

        if branch is not None:
            locked_results[node_id] = branch

    return state, locked_results


def _find_explicit_historical_branch(outcomes: dict) -> str | None:
    """Return the branch explicitly marked ``status: HISTORICAL``, else None.

    Unlike :func:`_find_historical_branch`, this does NOT fall back to the
    highest-probability branch — absence of a HISTORICAL branch means the event
    is an unresolved forecast that should keep being sampled.
    """
    for branch_name, branch_data in outcomes.items():
        if isinstance(branch_data, dict) and branch_data.get("status", "") == "HISTORICAL":
            return branch_name
    return None


def _find_historical_branch(outcomes: dict) -> str | None:
    """Find the branch marked HISTORICAL, or fall back to highest probability.

    For pre-2026 nodes we want to select the branch that actually happened
    in reality.  If a branch has ``status: HISTORICAL``, use that.  Otherwise,
    fall back to the branch with the highest base probability (a reasonable
    heuristic — the most likely outcome is what usually happened).
    """
    # First pass: look for an explicit HISTORICAL status
    for branch_name, branch_data in outcomes.items():
        if isinstance(branch_data, dict):
            status = branch_data.get("status", "")
            if status == "HISTORICAL":
                return branch_name

    # Second pass: no HISTORICAL branch found — shouldn't normally happen for
    # pre-2026 nodes, but fall back to first branch (which is typically the
    # historical one by convention in the YAML ordering).
    if outcomes:
        return next(iter(outcomes))

    return None
