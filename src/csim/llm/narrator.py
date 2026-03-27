"""High-level narration interface — resolves curated/cached/live narration."""

from __future__ import annotations

from csim.llm.base import LLMProvider
from csim.llm.cache import cache_narration, load_cached_narration, load_curated_narration
from csim.llm.prompts import build_local_prompt, build_claude_prompt
from csim.models import SimEvent


async def get_narration(
    seed: int,
    event: SimEvent,
    all_events: list[SimEvent],
    event_index: int,
    provider: LLMProvider | None = None,
) -> str | None:
    """
    Narration resolution order:
    1. Check curated library (pre-generated JSON)
    2. Check local cache (~/.21csim/cache/)
    3. Generate via provider (Ollama or Claude)
    4. Return None (no narration for this event)
    """
    # 1. Pre-generated?
    curated = load_curated_narration(seed, event.node_id)
    if curated:
        return curated

    # 2. Cached from previous run?
    cached = load_cached_narration(seed, event.node_id)
    if cached:
        return cached

    # 3. Provider available?
    if provider and provider.is_available():
        preceding = all_events[:event_index]
        model = provider.model_name()

        if model.startswith("claude/"):
            prompt = build_claude_prompt(event, all_events, event_index)
        else:
            prompt = build_local_prompt(event, preceding)

        try:
            narration = await provider.generate(prompt)
            if narration:
                cache_narration(seed, event.node_id, narration, source=model)
                return narration
        except Exception:
            pass

    # 4. Nothing available
    return None


def should_narrate(event: SimEvent) -> bool:
    """Decide if an event warrants narration."""
    if event.status.value in ("DIVERGENCE", "ESCALATED", "PREVENTED"):
        return True
    if event.is_high_impact:
        return True
    return False


def select_narration_candidates(events: list[SimEvent], max_narrations: int = 25) -> list[int]:
    """Select the top-N most impactful events to narrate from a run.

    Returns list of event indices.
    """
    scored: list[tuple[int, float]] = []
    for i, event in enumerate(events):
        if not should_narrate(event):
            continue
        # Score by impact magnitude + status weight
        impact = sum(abs(v) for v in event.world_state_delta.values()) if event.world_state_delta else 0.0
        weight = {
            "ESCALATED": 3.0,
            "PREVENTED": 2.5,
            "DIVERGENCE": 1.5,
        }.get(event.status.value, 1.0)
        if event.is_high_impact:
            weight *= 1.5
        scored.append((i, impact * weight))

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x[1], reverse=True)
    # Return indices in chronological order
    selected = sorted([idx for idx, _ in scored[:max_narrations]])
    return selected
