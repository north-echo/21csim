#!/usr/bin/env python3
"""Export full node data for the in-browser simulation engine (web/sim.js).

nodes-catalog.json only carries display data (no effects/cascades/modifies);
the browser engine needs everything the Python engine reads. Re-run after
editing node YAMLs:  python scripts/export_sim_nodes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from csim.graph import build_graph  # noqa: E402

WEB = Path(__file__).parent.parent / "web"
DATA = Path(__file__).parent.parent / "src" / "csim" / "data"


def main() -> None:
    graph = build_graph(DATA)
    nodes = {}
    for node_id in graph.nodes:
        d = graph.nodes[node_id]

        dist = d.get("distribution") or {}
        if dist.get("type") == "categorical":
            options = dict(dist.get("options", {}))
        else:
            options = dict(d.get("options", {}))

        # Only dict-form dependencies (with branch/modifies) affect sampling
        deps = []
        for dep in d.get("dependencies") or []:
            if isinstance(dep, dict):
                deps.append({
                    "node": dep["node"],
                    "branch": dep.get("branch"),
                    "modifies": dep.get("modifies", {}) or {},
                })

        outcomes = {}
        for branch, o in (d.get("outcomes") or {}).items():
            if not isinstance(o, dict):
                outcomes[branch] = {"status": "HISTORICAL", "description": str(o)}
                continue
            entry = {
                "status": o.get("status", "HISTORICAL"),
                "description": o.get("description", ""),
            }
            if o.get("explanation"):
                entry["explanation"] = o["explanation"]
            if o.get("silent"):
                entry["silent"] = True
            if o.get("world_state_effects"):
                entry["world_state_effects"] = o["world_state_effects"]
            if o.get("cascading_modifiers"):
                entry["cascading_modifiers"] = o["cascading_modifiers"]
            outcomes[branch] = entry

        nodes[node_id] = {
            "year_month": d.get("year_month", ""),
            "title": d.get("title", node_id),
            "description": (d.get("description") or "").strip(),
            "domain": d.get("domain", ""),
            "confidence": d.get("confidence", "HIGH"),
            "conditional": d.get("conditional"),
            "distribution": options,
            "dependencies": deps,
            "outcomes": outcomes,
        }

    out = {
        "traversal_order": graph.graph["traversal_order"],
        "nodes": nodes,
    }
    path = WEB / "nodes-sim.json"
    path.write_text(json.dumps(out, separators=(",", ":")))
    print(f"wrote {path} ({path.stat().st_size // 1024} KB, {len(nodes)} nodes)")


if __name__ == "__main__":
    main()
