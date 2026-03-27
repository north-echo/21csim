"""World state tracker with 32 dimensions, effect application, and composite scoring."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field, fields
from typing import Optional

from csim.models import EventStatus, OutcomeClass


@dataclass
class WorldState:
    # ── Geopolitical ──
    us_polarization: float = 0.35
    eu_cohesion: float = 0.75
    us_global_standing: float = 0.85
    china_power_index: float = 0.30
    russia_stability: float = 0.45
    middle_east_stability: float = 0.40
    india_power_index: float = 0.15
    latin_america_stability: float = 0.50

    # ── Economic ──
    global_gdp_growth_modifier: float = 1.0
    inequality_index: float = 0.50
    us_debt_gdp_ratio: float = 0.55
    crypto_market_cap_trillion: float = 0.0
    supply_chain_resilience: float = 0.70

    # ── Technology ──
    ai_development_year_offset: int = 0
    internet_freedom_index: float = 0.80
    social_media_penetration: float = 0.05
    human_augmentation_prevalence: float = 0.0
    space_development_index: float = 0.0

    # ── Security ──
    nuclear_risk_level: float = 0.15
    terrorism_threat_index: float = 0.30
    surveillance_state_index: float = 0.20
    global_cyber_damage_annual_b: float = 1.0
    drone_warfare_prevalence: float = 0.0

    # ── Climate / Environment ──
    climate_temp_anomaly: float = 0.6
    renewable_energy_share: float = 0.06
    sea_level_rise_meters: float = 0.0
    biodiversity_index: float = 0.80
    water_stress_index: float = 0.25
    food_security_index: float = 0.85
    arctic_ice_status: float = 0.90

    # ── Human / Social ──
    global_pandemic_deaths: int = 0
    conflict_deaths: int = 0
    opioid_deaths_cumulative: int = 0
    global_democracy_index: float = 0.62
    us_institutional_trust: float = 0.55
    misinformation_severity: float = 0.15
    racial_justice_index: float = 0.40
    gender_equity_index: float = 0.45
    us_life_expectancy_delta: float = 0.0
    global_population_billions: float = 6.1
    median_age_global: float = 26.0
    automation_displacement: float = 0.0

    # ── Governance / Structure ──
    governance_model: float = 0.50
    us_unity_index: float = 0.70
    europe_federation_index: float = 0.20
    china_regime_type: float = 0.15
    middle_east_post_oil: float = 0.05
    arctic_sovereignty_resolved: float = 0.05
    africa_development_index: float = 0.25

    # ── Existential ──
    existential_risk_cumulative: float = 0.0

    # ── Meta ──
    total_divergences: int = 0
    first_divergence_year: Optional[str] = None
    largest_divergence: Optional[str] = None


# Ranges for clamping float dimensions (dimension_name -> (min, max))
_CLAMP_RANGES: dict[str, tuple[float, float]] = {
    "us_polarization": (0.0, 1.0),
    "eu_cohesion": (0.0, 1.0),
    "us_global_standing": (0.0, 1.0),
    "china_power_index": (0.0, 1.0),
    "russia_stability": (0.0, 1.0),
    "middle_east_stability": (0.0, 1.0),
    "india_power_index": (0.0, 1.0),
    "latin_america_stability": (0.0, 1.0),
    "global_gdp_growth_modifier": (0.1, 3.0),
    "inequality_index": (0.0, 1.0),
    "us_debt_gdp_ratio": (0.0, 5.0),
    "crypto_market_cap_trillion": (0.0, 100.0),
    "supply_chain_resilience": (0.0, 1.0),
    "internet_freedom_index": (0.0, 1.0),
    "social_media_penetration": (0.0, 1.0),
    "human_augmentation_prevalence": (0.0, 1.0),
    "space_development_index": (0.0, 1.0),
    "nuclear_risk_level": (0.0, 1.0),
    "terrorism_threat_index": (0.0, 1.0),
    "surveillance_state_index": (0.0, 1.0),
    "global_cyber_damage_annual_b": (0.0, 10000.0),
    "drone_warfare_prevalence": (0.0, 1.0),
    "climate_temp_anomaly": (0.0, 10.0),
    "renewable_energy_share": (0.0, 1.0),
    "sea_level_rise_meters": (0.0, 20.0),
    "biodiversity_index": (0.0, 1.0),
    "water_stress_index": (0.0, 1.0),
    "food_security_index": (0.0, 1.0),
    "arctic_ice_status": (0.0, 1.0),
    "global_democracy_index": (0.0, 1.0),
    "us_institutional_trust": (0.0, 1.0),
    "misinformation_severity": (0.0, 1.0),
    "racial_justice_index": (0.0, 1.0),
    "gender_equity_index": (0.0, 1.0),
    "us_life_expectancy_delta": (-20.0, 20.0),
    "global_population_billions": (0.0, 15.0),
    "median_age_global": (15.0, 60.0),
    "automation_displacement": (0.0, 1.0),
    "governance_model": (0.0, 1.0),
    "us_unity_index": (0.0, 1.0),
    "europe_federation_index": (0.0, 1.0),
    "china_regime_type": (0.0, 1.0),
    "middle_east_post_oil": (0.0, 1.0),
    "arctic_sovereignty_resolved": (0.0, 1.0),
    "africa_development_index": (0.0, 1.0),
    "existential_risk_cumulative": (0.0, 1.0),
}

# Integer dimensions that don't get clamped to [0,1]
_INT_DIMENSIONS = {
    "global_pandemic_deaths",
    "conflict_deaths",
    "opioid_deaths_cumulative",
    "ai_development_year_offset",
    "total_divergences",
}

# Meta fields not subject to effects
_META_FIELDS = {"total_divergences", "first_divergence_year", "largest_divergence"}


def _clamp(value: float, dim: str) -> float:
    if dim in _CLAMP_RANGES:
        lo, hi = _CLAMP_RANGES[dim]
        return max(lo, min(hi, value))
    return value


def apply_effects(state: WorldState, effects: dict) -> WorldState:
    """Apply a node's outcome effects to the world state.

    Effect types:
    - Absolute:    {"us_polarization": 0.65}
    - Delta:       {"us_polarization": "+0.12"}
    - Multiplier:  {"global_gdp_growth_modifier": "*0.95"}
    - Conditional: {"if": "us_polarization > 0.6", "then": {"nuclear_risk_level": "+0.05"}}
    """
    new_state = copy.copy(state)

    for key, value in effects.items():
        if key == "if":
            # Conditional effect — handled as a pair with "then"
            continue
        if key == "then":
            # Evaluate the "if" condition
            condition = effects.get("if", "")
            if _evaluate_condition(state, condition):
                new_state = apply_effects(new_state, value)
            continue

        if key in _META_FIELDS:
            continue

        if not hasattr(new_state, key):
            continue

        current = getattr(new_state, key)
        new_value = _apply_single_effect(current, value, key)
        setattr(new_state, key, new_value)

    return new_state


def _apply_single_effect(current, effect_value, dim: str):
    """Apply a single effect value (absolute, delta, or multiplier)."""
    if isinstance(effect_value, str):
        effect_value = effect_value.strip()
        if effect_value.startswith("*"):
            multiplier = float(effect_value[1:])
            result = current * multiplier
        elif effect_value.startswith("+") or effect_value.startswith("-"):
            delta = float(effect_value)
            result = current + delta
        else:
            try:
                result = float(effect_value)
            except ValueError:
                return current  # skip non-numeric categorical labels
    elif isinstance(effect_value, (int, float)):
        # Check if it looks like a delta (spec sometimes uses bare numbers as absolute)
        result = effect_value
    else:
        return current

    if dim in _INT_DIMENSIONS:
        return int(result)
    return _clamp(float(result), dim)


def _evaluate_condition(state: WorldState, condition: str) -> bool:
    """Evaluate a simple condition string against world state."""
    if not condition:
        return False

    # Support AND/OR
    if " AND " in condition:
        parts = condition.split(" AND ")
        return all(_evaluate_condition(state, p.strip()) for p in parts)
    if " OR " in condition:
        parts = condition.split(" OR ")
        return any(_evaluate_condition(state, p.strip()) for p in parts)

    # Parse "dimension op value"
    match = re.match(r"(\w+)\s*(>=|<=|>|<|==|!=)\s*(.+)", condition.strip())
    if not match:
        return False

    dim, op, val_str = match.groups()
    if not hasattr(state, dim):
        return False

    current = getattr(state, dim)
    try:
        target = type(current)(float(val_str))
    except (ValueError, TypeError):
        target = val_str.strip().strip("'\"")

    ops = {
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    return ops[op](current, target)


# ── Composite Scoring ──

# Weights for composite score: (dimension, weight, invert)
# invert=True means higher values are worse
_COMPOSITE_WEIGHTS: list[tuple[str, float, bool]] = [
    # Existential (extreme weight)
    ("existential_risk_cumulative", -5.0, False),
    ("nuclear_risk_level", -3.0, False),
    # Human death toll (high weight, inverted — more deaths = worse)
    ("conflict_deaths", -2.0, False),
    ("global_pandemic_deaths", -2.0, False),
    ("opioid_deaths_cumulative", -1.0, False),
    # Climate (high weight)
    ("climate_temp_anomaly", -2.5, False),
    ("food_security_index", 2.0, False),
    ("water_stress_index", -1.5, False),
    ("biodiversity_index", 1.5, False),
    ("sea_level_rise_meters", -1.5, False),
    # Freedom (moderate weight)
    ("global_democracy_index", 1.5, False),
    ("internet_freedom_index", 1.0, False),
    ("surveillance_state_index", -1.0, False),
    # Prosperity (moderate weight)
    ("global_gdp_growth_modifier", 1.0, False),
    ("inequality_index", -1.0, False),
    # Stability (moderate weight)
    ("us_polarization", -1.0, False),
    ("eu_cohesion", 0.8, False),
    ("middle_east_stability", 0.5, False),
    ("us_institutional_trust", 0.8, False),
    # Progress (low weight)
    ("space_development_index", 0.3, False),
    ("human_augmentation_prevalence", 0.2, False),
    ("renewable_energy_share", 0.5, False),
]

# Baseline "historical" values for comparison (approximate 2100 values if all goes historical)
_HISTORICAL_BASELINES: dict[str, float] = {
    "existential_risk_cumulative": 0.15,
    "nuclear_risk_level": 0.35,
    "conflict_deaths": 2_000_000,
    "global_pandemic_deaths": 7_000_000,
    "opioid_deaths_cumulative": 700_000,
    "climate_temp_anomaly": 2.5,
    "food_security_index": 0.65,
    "water_stress_index": 0.45,
    "biodiversity_index": 0.50,
    "sea_level_rise_meters": 0.3,
    "global_democracy_index": 0.55,
    "internet_freedom_index": 0.60,
    "surveillance_state_index": 0.50,
    "global_gdp_growth_modifier": 1.0,
    "inequality_index": 0.60,
    "us_polarization": 0.78,
    "eu_cohesion": 0.55,
    "middle_east_stability": 0.30,
    "us_institutional_trust": 0.30,
    "space_development_index": 0.10,
    "human_augmentation_prevalence": 0.05,
    "renewable_energy_share": 0.40,
}


def compute_composite_score(state: WorldState) -> float:
    """Weighted composite of all dimensions, normalized to [-1, 1].
    Positive = better than historical, negative = worse."""
    score = 0.0
    max_possible = 0.0

    for dim, weight, _ in _COMPOSITE_WEIGHTS:
        if not hasattr(state, dim):
            continue
        current = float(getattr(state, dim))
        baseline = _HISTORICAL_BASELINES.get(dim, current)

        if baseline == 0:
            if current == 0:
                diff = 0.0
            else:
                diff = 1.0 if (current * weight > 0) else -1.0
        else:
            diff = (current - baseline) / max(abs(baseline), 1.0)

        # Weight already encodes direction (negative weight = higher is worse)
        score += weight * diff
        max_possible += abs(weight)

    if max_possible == 0:
        return 0.0

    normalized = score / max_possible
    return max(-1.0, min(1.0, normalized))


def classify_outcome(state: WorldState, events: list) -> OutcomeClass:
    """Classify the simulation outcome based on world state and events."""
    composite = compute_composite_score(state)

    # Check extinction
    if state.existential_risk_cumulative > 0.9:
        return OutcomeClass.EXTINCTION
    if state.nuclear_risk_level > 0.8 and state.climate_temp_anomaly > 4.0:
        return OutcomeClass.EXTINCTION

    # Check transcendence
    if (state.human_augmentation_prevalence > 0.4
            and state.space_development_index > 0.3
            and composite > 0.12):
        return OutcomeClass.TRANSCENDENCE

    # Check radically different — use divergence ratio so it scales with node count
    total_events = max(len(events), 1)
    divergence_ratio = state.total_divergences / total_events
    if divergence_ratio > 0.78 and abs(composite) < 0.03:
        return OutcomeClass.RADICALLY_DIFFERENT

    # Standard classification by composite score
    # Thresholds calibrated for ~300-node graph where scores cluster in [-0.7, +0.3]
    if composite > 0.20:
        return OutcomeClass.GOLDEN_AGE
    elif composite > 0.08:
        return OutcomeClass.PROGRESS
    elif composite > -0.04:
        return OutcomeClass.MUDDLING_THROUGH
    elif composite > -0.15:
        return OutcomeClass.DECLINE
    elif composite > -0.40:
        return OutcomeClass.CATASTROPHE
    else:
        return OutcomeClass.EXTINCTION


def generate_headline(state: WorldState, events: list) -> str:
    """Generate a one-line alternate history headline."""
    from csim.models import EventStatus

    composite = compute_composite_score(state)
    divergences = [e for e in events if e.status != EventStatus.HISTORICAL]

    if not divergences:
        return "The Historical Century: Everything Happened As It Did"

    # Find the largest-impact divergence
    largest = max(divergences, key=lambda e: abs(sum(
        float(str(v).lstrip("+*")) if isinstance(v, str) and v[0] in "+-*" else 0.0
        for v in e.world_state_delta.values()
    )) if e.world_state_delta else 0.0)

    # Determine adjective based on composite
    if composite > 0.7:
        adj = "Golden"
    elif composite > 0.4:
        adj = "Hopeful"
    elif composite > 0.2:
        adj = "Near-Miss"
    elif composite > 0.0:
        adj = "Quiet"
    elif composite > -0.2:
        adj = "Troubled"
    elif composite > -0.5:
        adj = "Long Collapse"
    elif composite > -0.8:
        adj = "Dark"
    else:
        adj = "Final"

    # Build description from earliest major divergence
    first = divergences[0]
    desc = first.description if len(first.description) < 50 else first.title

    return f"The {adj} Century: {desc}"


def compute_world_state_delta(old: WorldState, new: WorldState) -> dict[str, float]:
    """Compute the difference between two world states for display."""
    delta = {}
    for f in fields(WorldState):
        if f.name in _META_FIELDS:
            continue
        old_val = getattr(old, f.name)
        new_val = getattr(new, f.name)
        if isinstance(old_val, (int, float)) and old_val != new_val:
            delta[f.name] = new_val - old_val
    return delta
