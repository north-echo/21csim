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

    # ── Determine locked results for pre-2026 nodes ──
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

        # Only lock nodes before 2026-01
        if year_month >= "2026-01":
            continue

        node_id = node_data["id"]
        outcomes = node_data.get("outcomes", {})
        if not isinstance(outcomes, dict) or not outcomes:
            continue

        # Pick the HISTORICAL branch if one exists
        historical_branch = _find_historical_branch(outcomes)
        if historical_branch is not None:
            locked_results[node_id] = historical_branch

    return state, locked_results


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
