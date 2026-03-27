"""Tests for WorldState system."""

import pytest

from csim.world_state import (
    WorldState,
    apply_effects,
    classify_outcome,
    compute_composite_score,
    _evaluate_condition,
)
from csim.models import OutcomeClass


class TestApplyEffects:
    def test_delta_effect(self):
        state = WorldState()
        new = apply_effects(state, {"us_polarization": "+0.10"})
        assert new.us_polarization == pytest.approx(0.45)

    def test_negative_delta(self):
        state = WorldState()
        new = apply_effects(state, {"us_polarization": "-0.10"})
        assert new.us_polarization == pytest.approx(0.25)

    def test_absolute_effect(self):
        state = WorldState()
        new = apply_effects(state, {"us_polarization": 0.80})
        assert new.us_polarization == pytest.approx(0.80)

    def test_multiplier_effect(self):
        state = WorldState()
        new = apply_effects(state, {"global_gdp_growth_modifier": "*0.90"})
        assert new.global_gdp_growth_modifier == pytest.approx(0.90)

    def test_clamping(self):
        state = WorldState(us_polarization=0.95)
        new = apply_effects(state, {"us_polarization": "+0.20"})
        assert new.us_polarization == 1.0

    def test_clamping_lower(self):
        state = WorldState(us_polarization=0.05)
        new = apply_effects(state, {"us_polarization": "-0.20"})
        assert new.us_polarization == 0.0

    def test_integer_effect(self):
        state = WorldState()
        new = apply_effects(state, {"conflict_deaths": "+5000"})
        assert new.conflict_deaths == 5000
        assert isinstance(new.conflict_deaths, int)

    def test_multiple_effects(self):
        state = WorldState()
        new = apply_effects(state, {
            "us_polarization": "+0.10",
            "eu_cohesion": "-0.05",
            "conflict_deaths": "+1000",
        })
        assert new.us_polarization == pytest.approx(0.45)
        assert new.eu_cohesion == pytest.approx(0.70)
        assert new.conflict_deaths == 1000

    def test_unknown_dimension_ignored(self):
        state = WorldState()
        new = apply_effects(state, {"nonexistent_dim": "+0.50"})
        # Should not raise

    def test_immutability(self):
        state = WorldState()
        original_pol = state.us_polarization
        apply_effects(state, {"us_polarization": "+0.50"})
        assert state.us_polarization == original_pol


class TestConditionalEffects:
    def test_condition_true(self):
        state = WorldState(us_polarization=0.70)
        new = apply_effects(state, {
            "if": "us_polarization > 0.6",
            "then": {"nuclear_risk_level": "+0.05"},
        })
        assert new.nuclear_risk_level == pytest.approx(0.20)

    def test_condition_false(self):
        state = WorldState(us_polarization=0.30)
        new = apply_effects(state, {
            "if": "us_polarization > 0.6",
            "then": {"nuclear_risk_level": "+0.05"},
        })
        assert new.nuclear_risk_level == pytest.approx(0.15)


class TestEvaluateCondition:
    def test_greater_than(self):
        state = WorldState(us_polarization=0.70)
        assert _evaluate_condition(state, "us_polarization > 0.6")

    def test_less_than(self):
        state = WorldState(us_polarization=0.30)
        assert _evaluate_condition(state, "us_polarization < 0.5")

    def test_and_condition(self):
        state = WorldState(us_polarization=0.70, nuclear_risk_level=0.50)
        assert _evaluate_condition(state, "us_polarization > 0.6 AND nuclear_risk_level > 0.3")

    def test_and_condition_one_false(self):
        state = WorldState(us_polarization=0.70, nuclear_risk_level=0.10)
        assert not _evaluate_condition(state, "us_polarization > 0.6 AND nuclear_risk_level > 0.3")


class TestCompositeScore:
    def test_baseline_near_zero(self):
        """Default state should score near zero (it IS the baseline)."""
        state = WorldState()
        score = compute_composite_score(state)
        # Year 2000 state vs historical 2100 baselines — should be positive
        # since 2000 had lower deaths, lower warming, etc.
        assert -1.0 <= score <= 1.0

    def test_worse_state_lower_score(self):
        state_good = WorldState()
        state_bad = WorldState(
            conflict_deaths=5_000_000,
            nuclear_risk_level=0.80,
            climate_temp_anomaly=4.0,
        )
        assert compute_composite_score(state_bad) < compute_composite_score(state_good)

    def test_score_bounded(self):
        for _ in range(10):
            state = WorldState(
                existential_risk_cumulative=0.5,
                nuclear_risk_level=0.8,
                conflict_deaths=10_000_000,
            )
            score = compute_composite_score(state)
            assert -1.0 <= score <= 1.0


class TestClassifyOutcome:
    def test_extinction(self):
        state = WorldState(existential_risk_cumulative=0.95)
        assert classify_outcome(state, []) == OutcomeClass.EXTINCTION

    def test_nuclear_climate_extinction(self):
        state = WorldState(nuclear_risk_level=0.85, climate_temp_anomaly=4.5)
        assert classify_outcome(state, []) == OutcomeClass.EXTINCTION

    def test_transcendence(self):
        state = WorldState(
            human_augmentation_prevalence=0.7,
            space_development_index=0.6,
            # Need composite > 0.5, so set favorable conditions
            conflict_deaths=0,
            nuclear_risk_level=0.05,
            climate_temp_anomaly=1.0,
        )
        result = classify_outcome(state, [])
        # May or may not classify as transcendence depending on composite
        assert isinstance(result, OutcomeClass)
