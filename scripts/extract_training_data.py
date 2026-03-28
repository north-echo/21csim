#!/usr/bin/env python3
"""Extract narration training data from curated 21csim seed runs.

Reads all curated seed JSON files and extracts events that have narrations,
building training examples in the same prompt format used by the narrator.

Outputs:
  - narrations.jsonl         : Chat fine-tuning format (messages array)
  - narrations_completion.jsonl : Simple prompt/completion format
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURATED_RUNS = PROJECT_ROOT / "src" / "csim" / "data" / "curated" / "runs"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"

# ---------------------------------------------------------------------------
# Prompt templates (mirroring src/csim/llm/prompts.py)
# ---------------------------------------------------------------------------

CLAUDE_NARRATOR_SYSTEM = (
    "You are the narrator for a counterfactual history simulation spanning "
    "2000-2100. Voice: a calm, erudite historian writing in 2150, looking back "
    "at a century that diverged from our timeline. Write 2-4 sentences. "
    "Be specific and concrete. Reference people, places, dates. No exclamation "
    "points. Treat this alternate timeline as real history. When an event "
    "matches our timeline, note it calmly. When it diverges, convey the weight "
    "of the change without melodrama."
)

LOCAL_NARRATOR_SYSTEM = (
    "You write alternate history narration. Voice: a calm historian in 2150 "
    "looking back. 2-3 sentences only. No exclamation points. Specific "
    "concrete details. Treat the alternate timeline as real history that happened."
)


def build_claude_prompt(event: dict, all_events: list[dict], event_index: int) -> str:
    """Reproduce the prompt format from build_claude_prompt in prompts.py."""
    preceding = all_events[:event_index][-10:]
    preceding_text = "\n".join(
        f"  {e['year_month']} [{e['status']}]: {e['description']}"
        for e in preceding
    )

    explanation_line = (
        f"  Explanation: {event['explanation']}" if event.get("explanation") else ""
    )

    return f"""{CLAUDE_NARRATOR_SYSTEM}

Timeline so far (last 10 events):
{preceding_text}

Event to narrate:
  Date: {event['year_month']}
  Title: {event['title']}
  What happened: {event['description']}
  Status: {event['status']}
  Branch: {event['branch_taken']}
  {explanation_line}

Write 2-4 sentences:"""


def build_local_prompt(event: dict, all_events: list[dict], event_index: int) -> str:
    """Build the shorter local-model prompt (used for completion format)."""
    preceding = all_events[max(0, event_index - 3):event_index]
    recent_text = "\n".join(
        f"  {e['year_month']}: {e['description']}" for e in preceding
    )

    explanation_line = (
        f"  Why it diverged: {event['explanation']}" if event.get("explanation") else ""
    )

    example = (
        '"The recount took eleven days longer than anyone expected. When the final '
        'tally arrived, the margin was 2,211 votes. Not comfortable, but clear."'
    )

    return f"""{LOCAL_NARRATOR_SYSTEM}

Recent timeline:
{recent_text}

Event to narrate:
  Date: {event['year_month']}
  What happened: {event['description']}
  Status: {event['status']}
  {explanation_line}

Example (for tone only -- do NOT copy):
{example}

Write 2-3 sentences for the event above:"""


def extract_examples() -> list[dict]:
    """Walk all seed files and extract narration training pairs."""
    examples = []
    seed_files = sorted(CURATED_RUNS.glob("seed_*.json"))

    if not seed_files:
        print(f"ERROR: No seed files found in {CURATED_RUNS}", file=sys.stderr)
        sys.exit(1)

    for path in seed_files:
        with open(path) as f:
            run = json.load(f)

        events = run.get("events", [])
        for idx, event in enumerate(events):
            narration = event.get("narration")
            if not narration:
                continue

            # Chat format (Claude-style prompt)
            user_prompt = build_claude_prompt(event, events, idx)
            chat_example = {
                "messages": [
                    {"role": "system", "content": CLAUDE_NARRATOR_SYSTEM},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": narration},
                ]
            }

            # Completion format (local-model prompt)
            local_prompt = build_local_prompt(event, events, idx)
            completion_example = {
                "prompt": local_prompt,
                "completion": narration,
            }

            examples.append({
                "chat": chat_example,
                "completion": completion_example,
                "seed": run.get("seed"),
                "node_id": event.get("node_id"),
                "source": event.get("narration_source"),
            })

    return examples


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    print(f"Reading seed files from: {CURATED_RUNS}")
    examples = extract_examples()

    if not examples:
        print("No narrated events found. Nothing to write.")
        sys.exit(0)

    # Write chat format
    chat_path = OUTPUT_DIR / "narrations.jsonl"
    write_jsonl(chat_path, [ex["chat"] for ex in examples])
    print(f"Wrote {len(examples)} chat examples to {chat_path}")

    # Write completion format
    completion_path = OUTPUT_DIR / "narrations_completion.jsonl"
    write_jsonl(completion_path, [ex["completion"] for ex in examples])
    print(f"Wrote {len(examples)} completion examples to {completion_path}")

    # ---------------------------------------------------------------------------
    # Stats
    # ---------------------------------------------------------------------------
    input_lengths = [
        len(ex["chat"]["messages"][1]["content"]) for ex in examples
    ]
    output_lengths = [
        len(ex["chat"]["messages"][2]["content"]) for ex in examples
    ]

    sources = {}
    for ex in examples:
        src = ex.get("source") or "unknown"
        sources[src] = sources.get(src, 0) + 1

    seeds_with_narrations = len({ex["seed"] for ex in examples})

    print("\n--- Training Data Stats ---")
    print(f"  Total examples:            {len(examples)}")
    print(f"  Seeds with narrations:     {seeds_with_narrations} / 300")
    print(f"  Avg input length (chars):  {statistics.mean(input_lengths):.0f}")
    print(f"  Avg output length (chars): {statistics.mean(output_lengths):.0f}")
    print(f"  Min output length (chars): {min(output_lengths)}")
    print(f"  Max output length (chars): {max(output_lengths)}")
    print(f"  Narration sources:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count}")


if __name__ == "__main__":
    main()
