#!/usr/bin/env python3
"""Dump parity fixtures for the JS engine (web/sim.js).

For N seeds, runs the Python engine while recording every branch choice
(including silent outcomes, which never appear in the event list), then
writes {seed: {locks, expected}} JSON. The JS harness replays each run with
ALL branches locked — no RNG involved — so outputs must match exactly.

Usage: python scripts/validate_sim_parity.py <out.json> [n_seeds]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import csim.engine as engine  # noqa: E402
from csim.exporter import serialize_outcome  # noqa: E402
from csim.graph import build_graph, get_modified_distribution  # noqa: E402

DATA = Path(__file__).parent.parent / "src" / "csim" / "data"


def main() -> None:
    out_path = Path(sys.argv[1])
    n_seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    graph = build_graph(DATA)

    orig_sample = engine.sample
    fixtures = {}
    for seed in range(n_seeds):
        choices: dict[str, str] = {}
        current_node = [""]

        def recording_dist(node_id, results, g, cascading_effects=None,
                           _cur=current_node):
            _cur[0] = node_id
            return get_modified_distribution(node_id, results, g, cascading_effects)

        def recording_sample(distribution, rng, _choices=choices, _cur=current_node):
            branch = orig_sample(distribution, rng)
            _choices[_cur[0]] = branch
            return branch

        engine.get_modified_distribution = recording_dist
        engine.sample = recording_sample
        try:
            outcome = engine.simulate(graph, seed)
        finally:
            engine.sample = orig_sample
            engine.get_modified_distribution = get_modified_distribution

        fixtures[str(seed)] = {
            "locks": choices,
            "expected": serialize_outcome(outcome),
        }

    out_path.write_text(json.dumps(fixtures))
    print(f"wrote {out_path} ({len(fixtures)} seeds)")


if __name__ == "__main__":
    main()
