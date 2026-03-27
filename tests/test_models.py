"""Tests for data models."""

from csim.models import EventStatus, OutcomeClass, SimEvent, SimOutcome, BatchResult


class TestEnums:
    def test_event_status_values(self):
        assert EventStatus.HISTORICAL.value == "HISTORICAL"
        assert EventStatus.DIVERGENCE.value == "DIVERGENCE"
        assert EventStatus.ESCALATED.value == "ESCALATED"

    def test_outcome_class_values(self):
        assert OutcomeClass.GOLDEN_AGE.value == "GOLDEN-AGE"
        assert OutcomeClass.EXTINCTION.value == "EXTINCTION"
        assert OutcomeClass.TRANSCENDENCE.value == "TRANSCENDENCE"


class TestSimEvent:
    def test_creation(self):
        event = SimEvent(
            year_month="2000-11",
            node_id="2000_election",
            title="2000 US Presidential Election",
            description="Gore wins",
            status=EventStatus.DIVERGENCE,
            branch_taken="gore_wins",
            domain="geopolitical",
            probability_of_branch=0.45,
        )
        assert event.node_id == "2000_election"
        assert event.is_high_impact is False
        assert event.confidence == "HIGH"

    def test_defaults(self):
        event = SimEvent(
            year_month="2000-11",
            node_id="test",
            title="Test",
            description="Test",
            status=EventStatus.HISTORICAL,
            branch_taken="a",
            domain="test",
            probability_of_branch=1.0,
        )
        assert event.explanation is None
        assert event.world_state_delta == {}


class TestSimOutcome:
    def test_creation(self):
        outcome = SimOutcome(seed=42)
        assert outcome.seed == 42
        assert outcome.events == []
        assert outcome.outcome_class == OutcomeClass.MUDDLING_THROUGH
        assert outcome.composite_score == 0.0

class TestBatchResult:
    def test_creation(self):
        result = BatchResult(iterations=100)
        assert result.iterations == 100
        assert result.outcomes == []
