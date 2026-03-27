"""JSON export for web viewer and --format json."""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from csim.models import BatchResult, OutcomeClass, SimEvent, SimOutcome
from csim.world_state import WorldState


def _serialize_event(event: SimEvent) -> dict:
    return {
        "year_month": event.year_month,
        "node_id": event.node_id,
        "title": event.title,
        "description": event.description,
        "status": event.status.value,
        "branch_taken": event.branch_taken,
        "domain": event.domain,
        "probability_of_branch": round(event.probability_of_branch, 4),
        "explanation": event.explanation,
        "world_state_delta": {k: round(v, 4) for k, v in event.world_state_delta.items()},
        "is_high_impact": event.is_high_impact,
        "confidence": event.confidence,
        "narration": event.narration,
        "narration_source": event.narration_source,
    }


def _serialize_world_state(state: WorldState) -> dict:
    result = {}
    for f in fields(state):
        val = getattr(state, f.name)
        if isinstance(val, float):
            result[f.name] = round(val, 4)
        else:
            result[f.name] = val
    return result


def serialize_outcome(outcome: SimOutcome) -> dict:
    """Serialize a SimOutcome to a JSON-compatible dict."""
    return {
        "seed": outcome.seed,
        "headline": outcome.headline,
        "outcome_class": outcome.outcome_class.value,
        "composite_score": round(outcome.composite_score, 4),
        "percentile": round(outcome.percentile, 1),
        "total_divergences": outcome.total_divergences,
        "first_divergence_year": outcome.first_divergence_year,
        "largest_divergence_node": outcome.largest_divergence_node,
        "tags": outcome.tags,
        "events": [_serialize_event(e) for e in outcome.events],
        "final_state": _serialize_world_state(outcome.final_state) if outcome.final_state else None,
    }


def serialize_batch(result: BatchResult) -> dict:
    """Serialize a BatchResult to a JSON-compatible dict."""
    return {
        "iterations": result.iterations,
        "outcome_distribution": {k.value: round(v, 4) for k, v in result.outcome_distribution.items()},
        "highest_leverage_nodes": [
            {"node_id": n, "r_squared": round(r, 4)} for n, r in result.highest_leverage_nodes
        ],
        "dimension_stats": {
            dim: {k: round(float(v), 4) for k, v in stats.items()}
            for dim, stats in result.dimension_stats.items()
        },
    }


def export_outcome_json(outcome: SimOutcome, path: Path) -> None:
    """Export a single outcome to JSON file."""
    data = serialize_outcome(outcome)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def export_batch_json(result: BatchResult, path: Path) -> None:
    """Export batch results to JSON file."""
    data = serialize_batch(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def export_outcome_to_string(outcome: SimOutcome) -> str:
    """Serialize outcome to JSON string."""
    return json.dumps(serialize_outcome(outcome), indent=2)
