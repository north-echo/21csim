"""Prompt templates for LLM narration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from csim.models import SimEvent


LOCAL_NARRATOR_SYSTEM = (
    "You write alternate history narration. Voice: a calm historian in 2150 "
    "looking back. 2-3 sentences only. No exclamation points. Specific "
    "concrete details. Treat the alternate timeline as real history that happened."
)

CLAUDE_NARRATOR_SYSTEM = (
    "You are the narrator for a counterfactual history simulation spanning "
    "2000-2100. Voice: a calm, erudite historian writing in 2150, looking back "
    "at a century that diverged from our timeline. Write 2-4 sentences. "
    "Be specific and concrete. Reference people, places, dates. No exclamation "
    "points. Treat this alternate timeline as real history. When an event "
    "matches our timeline, note it calmly. When it diverges, convey the weight "
    "of the change without melodrama."
)

EXAMPLE_NARRATION = (
    '"The recount took eleven days longer than anyone expected. When the final '
    'tally arrived, the margin was 2,211 votes. Not comfortable, but clear."'
)


def build_local_prompt(event: SimEvent, preceding_events: list[SimEvent]) -> str:
    """Build a tight prompt for local 8B models."""
    recent = preceding_events[-3:]
    recent_text = "\n".join(
        f"  {e.year_month}: {e.description}" for e in recent
    )

    return f"""{LOCAL_NARRATOR_SYSTEM}

Recent timeline:
{recent_text}

Event to narrate:
  Date: {event.year_month}
  What happened: {event.description}
  Status: {event.status.value}
  {f"Why it diverged: {event.explanation}" if event.explanation else ""}

Example (for tone only — do NOT copy):
{EXAMPLE_NARRATION}

Write 2-3 sentences for the event above:"""


def build_claude_prompt(
    event: SimEvent,
    all_events: list[SimEvent],
    event_index: int,
) -> str:
    """Build a richer prompt for Claude with full timeline context."""
    preceding = all_events[:event_index]
    preceding_text = "\n".join(
        f"  {e.year_month} [{e.status.value}]: {e.description}"
        for e in preceding[-10:]
    )

    return f"""{CLAUDE_NARRATOR_SYSTEM}

Timeline so far (last 10 events):
{preceding_text}

Event to narrate:
  Date: {event.year_month}
  Title: {event.title}
  What happened: {event.description}
  Status: {event.status.value}
  Branch: {event.branch_taken}
  {f"Explanation: {event.explanation}" if event.explanation else ""}

Write 2-4 sentences:"""


def build_headline_prompt(events: list[SimEvent], outcome_class: str, composite_score: float) -> str:
    """Generate a headline for an entire simulation run."""
    divergences = [e for e in events if e.status.value != "HISTORICAL"]
    div_summary = "\n".join(
        f"  {e.year_month}: {e.description}" for e in divergences[:15]
    )

    return f"""You name alternate history timelines. Write a short, evocative title (5-10 words) for this century.

Outcome: {outcome_class} (score: {composite_score:.2f})

Key divergences:
{div_summary}

Write ONLY the title, no quotes, no explanation:"""
