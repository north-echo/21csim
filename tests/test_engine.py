"""Tests for the simulation engine."""

import pytest
from pathlib import Path

from csim.graph import build_graph
from csim.engine import simulate, simulate_batch, sample
from csim.models import EventStatus, OutcomeClass

DATA_DIR = Path(__file__).parent.parent / "src" / "csim" / "data"


@pytest.fixture
def graph():
    return build_graph(DATA_DIR)


class TestDeterminism:
    """Same seed must produce identical output every time."""

    def test_same_seed_same_result(self, graph):
        a = simulate(graph, seed=42)
        b = simulate(graph, seed=42)
        assert a.composite_score == b.composite_score
        assert a.headline == b.headline
        assert a.outcome_class == b.outcome_class
        assert len(a.events) == len(b.events)
        for ea, eb in zip(a.events, b.events):
            assert ea.branch_taken == eb.branch_taken
            assert ea.node_id == eb.node_id

    def test_different_seeds_different_results(self, graph):
        a = simulate(graph, seed=1)
        b = simulate(graph, seed=999)
        # Not guaranteed to differ, but extremely likely with enough nodes
        branches_a = [e.branch_taken for e in a.events]
        branches_b = [e.branch_taken for e in b.events]
        assert branches_a != branches_b

    def test_determinism_across_many_seeds(self, graph):
        for seed in [0, 1, 100, 9999, 42424]:
            a = simulate(graph, seed=seed)
            b = simulate(graph, seed=seed)
            assert a.composite_score == b.composite_score


class TestSampling:
    def test_sample_categorical(self):
        import numpy as np
        rng = np.random.default_rng(42)
        dist = {"a": 0.5, "b": 0.3, "c": 0.2}
        result = sample(dist, rng)
        assert result in dist

    def test_sample_deterministic(self):
        import numpy as np
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        dist = {"a": 0.5, "b": 0.3, "c": 0.2}
        assert sample(dist, rng1) == sample(dist, rng2)

    def test_sample_degenerate(self):
        import numpy as np
        rng = np.random.default_rng(42)
        dist = {"only": 1.0}
        assert sample(dist, rng) == "only"

    def test_sample_empty_raises(self):
        import numpy as np
        rng = np.random.default_rng(42)
        with pytest.raises(ValueError):
            sample({}, rng)


class TestSimulation:
    def test_events_produced(self, graph):
        outcome = simulate(graph, seed=42)
        assert len(outcome.events) > 0

    def test_events_chronological(self, graph):
        outcome = simulate(graph, seed=42)
        year_months = [e.year_month for e in outcome.events]
        assert year_months == sorted(year_months)

    def test_outcome_has_required_fields(self, graph):
        outcome = simulate(graph, seed=42)
        assert outcome.seed == 42
        assert isinstance(outcome.composite_score, float)
        assert isinstance(outcome.outcome_class, OutcomeClass)
        assert isinstance(outcome.headline, str)
        assert outcome.final_state is not None

    def test_divergence_count(self, graph):
        outcome = simulate(graph, seed=42)
        divergences = [e for e in outcome.events if e.status != EventStatus.HISTORICAL]
        assert outcome.total_divergences == len(divergences)

    def test_composite_score_bounded(self, graph):
        for seed in range(50):
            outcome = simulate(graph, seed=seed)
            assert -1.0 <= outcome.composite_score <= 1.0


class TestConditionalGating:
    def test_jan6_skipped_if_trump_wins_2020(self, graph):
        """Jan 6 should not fire if Trump wins 2020."""
        # Run many seeds and check
        for seed in range(100):
            outcome = simulate(graph, seed=seed)
            events_by_id = {e.node_id: e for e in outcome.events}
            if "2020_us_election" in events_by_id:
                if events_by_id["2020_us_election"].branch_taken == "trump_wins":
                    assert "2021_jan6" not in events_by_id

    def test_covid_response_skipped_if_no_pandemic(self, graph):
        """COVID response should not fire if no pandemic."""
        for seed in range(100):
            outcome = simulate(graph, seed=seed)
            events_by_id = {e.node_id: e for e in outcome.events}
            if "2019_covid_emergence" in events_by_id:
                if events_by_id["2019_covid_emergence"].branch_taken == "no_pandemic":
                    assert "2020_covid_response" not in events_by_id


class TestBatch:
    def test_batch_runs(self, graph):
        result = simulate_batch(graph, iterations=10)
        assert result.iterations == 10
        assert len(result.outcomes) == 10

    def test_batch_outcome_distribution(self, graph):
        result = simulate_batch(graph, iterations=100)
        assert len(result.outcome_distribution) > 0
        total = sum(result.outcome_distribution.values())
        assert abs(total - 1.0) < 0.01

    def test_batch_leverage(self, graph):
        result = simulate_batch(graph, iterations=100)
        assert len(result.highest_leverage_nodes) > 0
        for node_id, r2 in result.highest_leverage_nodes:
            assert 0 <= r2 <= 1.0
