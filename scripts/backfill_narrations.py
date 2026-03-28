#!/usr/bin/env python3
"""Backfill narrations for seeds that have 0 narrations."""

import asyncio
import json
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from csim.llm.claude import ClaudeProvider
from csim.llm.narrator import get_narration, select_narration_candidates
from csim.models import SimEvent, EventStatus


def load_events(data):
    """Convert JSON events back to SimEvent objects."""
    events = []
    for e in data.get("events", []):
        events.append(SimEvent(
            year_month=e["year_month"],
            node_id=e["node_id"],
            title=e["title"],
            description=e["description"],
            status=EventStatus(e["status"]),
            branch_taken=e["branch_taken"],
            domain=e["domain"],
            probability_of_branch=e.get("probability_of_branch", 0),
            explanation=e.get("explanation"),
            world_state_delta=e.get("world_state_delta", {}),
            is_high_impact=e.get("is_high_impact", False),
            confidence=e.get("confidence", "HIGH"),
        ))
    return events


async def narrate_seed(filepath, llm):
    """Narrate a single seed file."""
    data = json.loads(Path(filepath).read_text())
    seed = data.get("seed", 0)
    events = load_events(data)

    candidates = select_narration_candidates(events, max_narrations=25)

    count = 0
    for batch_start in range(0, len(candidates), 5):
        batch = candidates[batch_start:batch_start + 5]
        tasks = [
            get_narration(seed, events[idx], events, idx, llm)
            for idx in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for j, r in enumerate(results):
            if r and not isinstance(r, Exception):
                event_idx = batch[j]
                data["events"][event_idx]["narration"] = r
                data["events"][event_idx]["narration_source"] = llm.model_name()
                count += 1

    # Write back
    Path(filepath).write_text(json.dumps(data, indent=2))
    return count


async def main():
    llm = ClaudeProvider(model="claude-sonnet-4-20250514")
    if not llm.is_available():
        print("Error: Claude API not available")
        sys.exit(1)

    files = sorted(glob.glob("src/csim/data/curated/runs/seed_*.json"))
    to_narrate = []
    for f in files:
        d = json.load(open(f))
        n = sum(1 for e in d["events"] if e.get("narration"))
        if n == 0:
            to_narrate.append(f)

    print(f"Backfilling {len(to_narrate)} seeds with narrations...")
    print(f"Narrator: {llm.model_name()}")

    for i, filepath in enumerate(to_narrate, 1):
        seed = json.loads(Path(filepath).read_text()).get("seed", "?")
        count = await narrate_seed(filepath, llm)
        print(f"  Seed {seed}: {count} narrations [{i}/{len(to_narrate)}]")

    print(f"\nDone. Backfilled {len(to_narrate)} seeds.")


if __name__ == "__main__":
    asyncio.run(main())
