"""LLM-powered news analyst — translates world events into world state updates."""

from __future__ import annotations

import json
import re

from csim.llm.base import LLMProvider
from csim.world_state import _CLAMP_RANGES, _INT_DIMENSIONS, _clamp

# All updatable dimension names with brief descriptions for the LLM
DIMENSION_DESCRIPTIONS = {
    # Geopolitical
    "us_polarization": "US political polarization (0=united, 1=civil war level)",
    "eu_cohesion": "European Union cohesion/unity (0=dissolved, 1=federation)",
    "us_global_standing": "US global influence and soft power (0=pariah, 1=hegemon)",
    "china_power_index": "China's relative global power (0=collapse, 1=dominant superpower)",
    "russia_stability": "Russian state stability (0=failed state, 1=stable)",
    "middle_east_stability": "Middle East regional stability (0=total war, 1=lasting peace)",
    "india_power_index": "India's relative global power (0=failed, 1=superpower)",
    "latin_america_stability": "Latin America stability (0=collapse, 1=thriving)",
    # Economic
    "global_gdp_growth_modifier": "Global GDP growth multiplier (1.0=trend, <1=contraction, >1=boom)",
    "inequality_index": "Global wealth inequality (0=equal, 1=extreme)",
    "us_debt_gdp_ratio": "US federal debt to GDP ratio",
    "crypto_market_cap_trillion": "Total crypto market cap in trillions USD",
    "supply_chain_resilience": "Global supply chain reliability (0=broken, 1=robust)",
    # Technology
    "ai_development_year_offset": "Years AI progress is ahead(+)/behind(-) our timeline (integer)",
    "internet_freedom_index": "Global internet openness (0=fully censored, 1=fully open)",
    "social_media_penetration": "Share of humanity on social media (0-1)",
    "human_augmentation_prevalence": "Human augmentation adoption (0=none, 1=ubiquitous)",
    "space_development_index": "Space industry/settlement progress (0=none, 1=interplanetary)",
    # Security
    "nuclear_risk_level": "Risk of nuclear weapon use (0=zero, 1=imminent)",
    "terrorism_threat_index": "Global terrorism threat (0=none, 1=extreme)",
    "surveillance_state_index": "Global surveillance prevalence (0=none, 1=total)",
    "global_cyber_damage_annual_b": "Annual global cyberattack damage in billions USD",
    "drone_warfare_prevalence": "Drone/autonomous warfare adoption (0=none, 1=dominant)",
    # Climate / Environment
    "climate_temp_anomaly": "Global temp anomaly above pre-industrial (degrees C)",
    "renewable_energy_share": "Renewables as share of total energy (0-1)",
    "sea_level_rise_meters": "Sea level rise since 2000 (meters)",
    "biodiversity_index": "Global biodiversity health (0=collapse, 1=pristine)",
    "water_stress_index": "Global water stress (0=none, 1=crisis)",
    "food_security_index": "Global food security (0=famine, 1=abundance)",
    "arctic_ice_status": "Arctic ice extent (0=gone, 1=year-2000 levels)",
    # Human / Social
    "global_pandemic_deaths": "Cumulative pandemic deaths since 2000 (integer)",
    "conflict_deaths": "Cumulative conflict deaths since 2000 (integer)",
    "opioid_deaths_cumulative": "Cumulative US opioid deaths (integer)",
    "global_democracy_index": "Global democracy level (0=authoritarian, 1=full democracy)",
    "us_institutional_trust": "US public trust in institutions (0=none, 1=full)",
    "misinformation_severity": "Misinformation prevalence/impact (0=none, 1=total epistemic collapse)",
    "racial_justice_index": "Global racial justice progress (0=apartheid, 1=full equity)",
    "gender_equity_index": "Global gender equity (0=none, 1=full parity)",
    "us_life_expectancy_delta": "US life expectancy change vs 2000 baseline (years, +/-)",
    "global_population_billions": "Global population in billions",
    "median_age_global": "Global median age (years)",
    "automation_displacement": "Workforce share displaced by automation (0-1)",
    # Governance / Structure
    "governance_model": "Dominant global governance (0=authoritarian, 0.5=status quo, 1=liberal democratic)",
    "us_unity_index": "US national unity/territorial integrity (0=dissolved, 1=united)",
    "europe_federation_index": "European political integration (0=fragmented, 1=federal state)",
    "china_regime_type": "China regime openness (0=hardline, 1=liberal democracy)",
    "middle_east_post_oil": "Middle East economic diversification beyond oil (0=fully dependent, 1=diversified)",
    "arctic_sovereignty_resolved": "Arctic territorial disputes resolved (0=contested, 1=settled)",
    "africa_development_index": "African development level (0=crisis, 1=fully developed)",
    # Existential
    "existential_risk_cumulative": "Cumulative existential risk (0=safe, >0.9=extinction)",
}


def build_analyst_prompt(
    news_items: list[dict],
    current_state: dict,
    last_update: str | None = None,
) -> str:
    """Build the prompt for the LLM analyst to interpret news as world state changes.

    Args:
        news_items: List of dicts with 'title', 'description', 'source', 'published_at'
        current_state: Current reality YAML values as dict
        last_update: ISO date of last update (for context)
    """
    # Format news
    news_block = "\n".join(
        f"- [{item.get('published_at', 'unknown')}] {item['title']}"
        + (f"\n  {item['description']}" if item.get('description') else "")
        for item in news_items[:30]  # Cap at 30 items
    )

    # Format current state (subset of most relevant dimensions)
    state_block = "\n".join(
        f"  {dim}: {current_state.get(dim, '?')}  # {desc}"
        for dim, desc in DIMENSION_DESCRIPTIONS.items()
        if dim in current_state
    )

    return f"""You are an expert geopolitical analyst for a Monte Carlo simulation of world history (2000-2100).

Your job: Given recent real-world news headlines, determine what adjustments (if any) should be made to the simulation's world state dimensions.

## Current World State
{state_block}

## Recent News Headlines
{news_block}

## Last Update
{last_update or "Never (first run)"}

## Instructions

Analyze the news and return a JSON object with two keys:

1. "dimension_updates": A dict of dimension_name -> new_absolute_value for any dimensions that should change based on these events. Only include dimensions where news warrants a meaningful shift. Use your judgment about magnitude — a regional skirmish might shift middle_east_stability by 0.02, while a full-scale war might shift it by 0.15-0.30.

2. "new_nodes": A list of significant new events that should be added as simulation nodes. Each node should have:
   - "id": snake_case identifier with year prefix (e.g. "2026_iran_war")
   - "year_month": "YYYY-MM" when the event started/occurred
   - "title": Short human-readable title
   - "description": 1-2 sentence description
   - "domain": one of: geopolitical, economic, technology, security, climate, shock
   - "world_state_effects": dict of dimension -> effect string (use "+0.05" for deltas)
   - "cascading_modifiers": dict of downstream_node_id.dimension -> modifier (optional)
   Only create nodes for genuinely significant events (wars, economic crises, major treaties, etc.) — not routine news.

3. "reasoning": A brief explanation of your analysis (2-3 sentences).

Return ONLY valid JSON. No markdown code fences.

Example response:
{{"dimension_updates": {{"middle_east_stability": 0.10, "global_gdp_growth_modifier": 0.98, "conflict_deaths": 1650000}}, "new_nodes": [{{"id": "2026_iran_war", "year_month": "2026-02", "title": "US-Israel-Iran War", "description": "Coalition military strikes against Iranian nuclear and military targets escalate into full regional conflict", "domain": "geopolitical", "world_state_effects": {{"middle_east_stability": "-0.20", "conflict_deaths": "+150000", "nuclear_risk_level": "+0.10", "global_gdp_growth_modifier": "*0.95"}}, "cascading_modifiers": {{}}}}], "reasoning": "The Iran conflict represents a major regional war with global economic implications via oil supply disruption."}}"""


def build_node_yaml(node: dict) -> str:
    """Convert an LLM-generated node dict into YAML format matching existing nodes."""
    import yaml

    # Build the node structure matching existing format
    node_data = {
        "id": node["id"],
        "year_month": node["year_month"],
        "title": node["title"],
        "description": node["description"],
        "domain": node.get("domain", "geopolitical"),
        "confidence": "HIGH",  # It happened in reality
        "distribution": {
            "type": "categorical",
            "options": {_branch_name(node): 1.0},  # Lock to what actually happened
        },
        "outcomes": {
            _branch_name(node): {
                "status": "HISTORICAL",
                "description": node["description"],
                "world_state_effects": node.get("world_state_effects", {}),
            }
        },
    }

    if node.get("cascading_modifiers"):
        node_data["outcomes"][_branch_name(node)]["cascading_modifiers"] = node["cascading_modifiers"]

    return yaml.dump(node_data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _branch_name(node: dict) -> str:
    """Generate a branch name from a node dict."""
    # Use the id without the year prefix as the branch name
    parts = node["id"].split("_", 1)
    return parts[1] if len(parts) > 1 else node["id"]


async def analyze_news(
    provider: LLMProvider,
    news_items: list[dict],
    current_state: dict,
    last_update: str | None = None,
) -> dict:
    """Send news to LLM and get structured world state updates.

    Returns dict with keys: dimension_updates, new_nodes, reasoning
    """
    prompt = build_analyst_prompt(news_items, current_state, last_update)
    response = await provider.generate(prompt, max_tokens=2000)

    # Parse JSON response (strip any accidental markdown fencing)
    text = response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nResponse: {text[:500]}") from e

    result["dimension_updates"] = validate_dimension_updates(result.get("dimension_updates", {}))
    result["new_nodes"] = validate_new_nodes(result.get("new_nodes", []))

    return result


def validate_dimension_updates(updates: dict) -> dict:
    """Filter to known dimensions, coerce to numbers, and clamp to legal ranges.

    LLMs occasionally hallucinate dimension names or out-of-range magnitudes;
    everything written to reality_2026.yaml must survive the same clamps the
    engine applies (_CLAMP_RANGES / _INT_DIMENSIONS).
    """
    valid: dict[str, float | int] = {}
    for dim, value in updates.items():
        if dim not in DIMENSION_DESCRIPTIONS:
            continue
        try:
            num = float(value)
        except (TypeError, ValueError):
            continue
        if dim in _INT_DIMENSIONS:
            # Death counts can't go negative; ai_development_year_offset can
            valid[dim] = int(num) if dim == "ai_development_year_offset" else max(0, int(num))
        elif dim in _CLAMP_RANGES:
            valid[dim] = _clamp(num, dim)
        else:
            valid[dim] = num
    return valid


_NODE_ID_RE = re.compile(r"^20\d{2}_[a-z0-9_]+$")
_YEAR_MONTH_RE = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])$")
_VALID_DOMAINS = {"geopolitical", "economic", "technology", "security", "climate", "social", "shock"}


def validate_new_nodes(nodes: list) -> list[dict]:
    """Drop malformed nodes and unknown-dimension effects before they hit disk."""
    valid = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if not _NODE_ID_RE.match(str(node.get("id", ""))):
            continue
        if not _YEAR_MONTH_RE.match(str(node.get("year_month", ""))):
            continue
        if not node.get("title") or not node.get("description"):
            continue
        if node.get("domain") not in _VALID_DOMAINS:
            node["domain"] = "geopolitical"
        effects = node.get("world_state_effects") or {}
        node["world_state_effects"] = {
            dim: val for dim, val in effects.items() if dim in DIMENSION_DESCRIPTIONS
        }
        valid.append(node)
    return valid
