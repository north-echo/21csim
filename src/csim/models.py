"""Core data models for the 21st Century Counterfactual Simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from csim.world_state import WorldState


class EventStatus(Enum):
    HISTORICAL = "HISTORICAL"
    DIVERGENCE = "DIVERGENCE"
    PREVENTED = "PREVENTED"
    ACCELERATED = "ACCELERATED"
    DELAYED = "DELAYED"
    ESCALATED = "ESCALATED"
    DIMINISHED = "DIMINISHED"


class OutcomeClass(Enum):
    GOLDEN_AGE = "GOLDEN-AGE"
    PROGRESS = "PROGRESS"
    MUDDLING_THROUGH = "MUDDLING-THROUGH"
    DECLINE = "DECLINE"
    CATASTROPHE = "CATASTROPHE"
    EXTINCTION = "EXTINCTION"
    TRANSCENDENCE = "TRANSCENDENCE"
    RADICALLY_DIFFERENT = "RADICALLY-DIFFERENT"


@dataclass
class SimEvent:
    year_month: str
    node_id: str
    title: str
    description: str
    status: EventStatus
    branch_taken: str
    domain: str
    probability_of_branch: float
    explanation: str | None = None
    delta: str | None = None
    world_state_delta: dict = field(default_factory=dict)
    is_high_impact: bool = False
    confidence: str = "HIGH"
    narration: str | None = None
    narration_source: str | None = None


@dataclass
class SimOutcome:
    seed: int
    events: list[SimEvent] = field(default_factory=list)
    final_state: WorldState | None = None
    outcome_class: OutcomeClass = OutcomeClass.MUDDLING_THROUGH
    headline: str = ""
    composite_score: float = 0.0
    percentile: float = 50.0
    total_divergences: int = 0
    first_divergence_year: str | None = None
    largest_divergence_node: str | None = None
    causal_chains: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass
class BatchResult:
    iterations: int
    outcomes: list[SimOutcome] = field(default_factory=list)
    dimension_stats: dict = field(default_factory=dict)
    outcome_distribution: dict[OutcomeClass, float] = field(default_factory=dict)
    highest_leverage_nodes: list[tuple[str, float]] = field(default_factory=list)
    common_paths: dict[OutcomeClass, list[list[str]]] = field(default_factory=dict)
