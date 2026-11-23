"""Reality Stream — automated news ingestion and world state updates.

Fetches real-world news via NewsAPI, uses an LLM to interpret geopolitical
significance, and updates the rolling reality YAML file.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from csim.llm.analyst import analyze_news, build_node_yaml
from csim.llm.base import LLMProvider

# ── News Fetching ──


def fetch_news_headlines(
    api_key: str,
    days_back: int = 7,
    categories: list[str] | None = None,
    page_size: int = 30,
) -> list[dict]:
    """Fetch top headlines from NewsAPI.

    Args:
        api_key: NewsAPI.org API key
        days_back: How many days back to search
        categories: NewsAPI categories (general, business, technology, science, health)
        page_size: Number of results per request (max 100)

    Returns:
        List of dicts with: title, description, source, published_at, url
    """
    if not api_key:
        raise ValueError("NEWSAPI_KEY not set. Get one at https://newsapi.org")

    from_date = (datetime.now(UTC) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    all_articles: list[dict] = []

    # Geopolitically-relevant search terms for broad coverage
    queries = [
        "war OR conflict OR military OR sanctions",
        "economy OR recession OR trade OR oil",
        "nuclear OR treaty OR alliance OR NATO",
        "climate OR disaster OR famine",
    ]

    if categories:
        # Use top-headlines endpoint with categories
        for cat in categories:
            url = (
                f"https://newsapi.org/v2/top-headlines?"
                f"category={cat}&language=en&pageSize={page_size}"
            )
            articles = _fetch_newsapi(url, api_key)
            all_articles.extend(articles)
    else:
        # Use everything endpoint with geopolitical queries
        for query in queries:
            url = (
                f"https://newsapi.org/v2/everything?"
                f"q={urllib.request.quote(query)}"
                f"&from={from_date}&language=en&sortBy=relevancy"
                f"&pageSize={min(page_size, 20)}"
            )
            articles = _fetch_newsapi(url, api_key)
            all_articles.extend(articles)

    # Deduplicate by title
    seen_titles: set[str] = set()
    unique: list[dict] = []
    for a in all_articles:
        title = a.get("title", "")
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique.append(a)

    return unique[:page_size]


def _fetch_newsapi(url: str, api_key: str) -> list[dict]:
    """Make a single NewsAPI request."""
    req = urllib.request.Request(
        url,
        headers={"X-Api-Key": api_key, "User-Agent": "21csim/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError):
        # Return empty on failure rather than crashing
        return []

    articles = []
    for article in data.get("articles", []):
        articles.append({
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "source": article.get("source", {}).get("name", ""),
            "published_at": article.get("publishedAt", ""),
            "url": article.get("url", ""),
        })
    return articles


# ── Reality Update ──

# Which simulation domain each dimension belongs to, for tagging the weekly
# pulse node. Valid domains match csim.llm.analyst._VALID_DOMAINS.
_DIMENSION_DOMAINS: dict[str, str] = {
    # Geopolitical
    "us_polarization": "geopolitical", "eu_cohesion": "geopolitical",
    "us_global_standing": "geopolitical", "china_power_index": "geopolitical",
    "russia_stability": "geopolitical", "middle_east_stability": "geopolitical",
    "india_power_index": "geopolitical", "latin_america_stability": "geopolitical",
    # Economic
    "global_gdp_growth_modifier": "economic", "inequality_index": "economic",
    "us_debt_gdp_ratio": "economic", "crypto_market_cap_trillion": "economic",
    "supply_chain_resilience": "economic",
    # Technology
    "ai_development_year_offset": "technology", "internet_freedom_index": "technology",
    "social_media_penetration": "technology", "human_augmentation_prevalence": "technology",
    "space_development_index": "technology",
    # Security
    "nuclear_risk_level": "security", "terrorism_threat_index": "security",
    "surveillance_state_index": "security", "global_cyber_damage_annual_b": "security",
    "drone_warfare_prevalence": "security",
    # Climate / Environment
    "climate_temp_anomaly": "climate", "renewable_energy_share": "climate",
    "sea_level_rise_meters": "climate", "biodiversity_index": "climate",
    "water_stress_index": "climate", "food_security_index": "climate",
    "arctic_ice_status": "climate",
    # Human / Social
    "global_pandemic_deaths": "social", "conflict_deaths": "social",
    "opioid_deaths_cumulative": "social", "global_democracy_index": "social",
    "us_institutional_trust": "social", "misinformation_severity": "social",
    "racial_justice_index": "social", "gender_equity_index": "social",
    "us_life_expectancy_delta": "social", "global_population_billions": "social",
    "median_age_global": "social", "automation_displacement": "social",
    # Governance / Structure (no dedicated domain → geopolitical)
    "governance_model": "geopolitical", "us_unity_index": "geopolitical",
    "europe_federation_index": "geopolitical", "china_regime_type": "geopolitical",
    "middle_east_post_oil": "geopolitical", "arctic_sovereignty_resolved": "geopolitical",
    "africa_development_index": "geopolitical",
    # Existential
    "existential_risk_cumulative": "shock",
}

# Tie-break order when a week touches several domains equally.
_DOMAIN_PRIORITY = ("shock", "security", "geopolitical", "economic", "climate", "technology", "social")

# Integer dimensions whose deltas are whole numbers (mirrors world_state._INT_DIMENSIONS).
_INT_DELTA_DIMS = {
    "global_pandemic_deaths", "conflict_deaths", "opioid_deaths_cumulative",
    "ai_development_year_offset",
}


def _fmt_delta(delta: float, dim: str) -> str:
    """Format a numeric delta as a signed effect string (e.g. '+0.01', '-3000')."""
    if dim in _INT_DELTA_DIMS:
        return f"{int(round(delta)):+d}"
    s = f"{delta:+.4f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return s


def _dominant_domain(dims: dict) -> str:
    """Pick the domain tag for a pulse node from the dimensions it touched."""
    counts: dict[str, int] = {}
    for dim in dims:
        domain = _DIMENSION_DOMAINS.get(dim)
        if domain:
            counts[domain] = counts.get(domain, 0) + 1
    if not counts:
        return "geopolitical"
    top = max(counts.values())
    winners = [d for d, c in counts.items() if c == top]
    for domain in _DOMAIN_PRIORITY:
        if domain in winners:
            return domain
    return winners[0]


def build_weekly_node(
    reality_before: dict,
    dimension_updates: dict[str, float],
    reasoning: str,
    now: datetime,
) -> dict | None:
    """Build a lightweight HISTORICAL "reality pulse" node for the week.

    The node records the week's dimension changes as delta effects and carries
    the analyst reasoning as its description, so each weekly update lands on the
    simulated timeline as a visible (locked, historical) event rather than only
    nudging the present-day baseline. Returns None when there is nothing to
    record (an empty-week update).
    """
    effects: dict[str, str] = {}
    for dim, new_val in dimension_updates.items():
        if dim == "year":
            continue
        old_val = reality_before.get(dim)
        if old_val is None:
            continue  # brand-new dimension: no delta to express
        try:
            delta = float(new_val) - float(old_val)
        except (TypeError, ValueError):
            continue
        if delta == 0:
            continue
        effects[dim] = _fmt_delta(delta, dim)

    if not effects:
        return None

    date_str = now.strftime("%Y-%m-%d")
    return {
        "id": f"{now.year}_reality_{now.strftime('%Y%m%d')}",
        "year_month": now.strftime("%Y-%m"),
        "title": f"Reality pulse: week of {date_str}",
        "description": (reasoning or "").strip() or f"Weekly reality-stream update ({date_str}).",
        "domain": _dominant_domain(effects),
        "world_state_effects": effects,
    }


def update_reality(
    data_dir: Path,
    dimension_updates: dict[str, float],
    new_nodes: list[dict],
    update_log: dict | None = None,
    emit_pulse: bool = True,
) -> Path:
    """Apply updates to the rolling reality YAML and write new node files.

    Args:
        data_dir: Path to csim data directory
        dimension_updates: Dict of dimension -> new absolute value
        new_nodes: List of node dicts to write as YAML files
        update_log: Optional metadata to append to the update log
        emit_pulse: When True, also write a lightweight weekly "reality pulse"
            node capturing this update's dimension deltas, so the week appears
            as an event on the simulated timeline (see build_weekly_node).

    Returns:
        Path to updated reality file
    """
    reality_path = data_dir / "reality_2026.yaml"

    # Load current reality
    with open(reality_path) as f:
        reality = yaml.safe_load(f)

    reality_before = dict(reality)  # snapshot for pulse-node deltas
    now = datetime.now(UTC)

    # Apply dimension updates
    for dim, value in dimension_updates.items():
        if dim == "year":
            continue
        reality[dim] = value

    # Write updated reality
    # Preserve comments by reading original and doing targeted replacements
    _write_reality_yaml(reality_path, reality)

    # Write new node YAML files
    nodes_dir = data_dir / "nodes"
    for node in new_nodes:
        node_id = node["id"]
        node_path = nodes_dir / f"{node_id}.yaml"
        if not node_path.exists():
            node_yaml = build_node_yaml(node)
            node_path.write_text(node_yaml)

    # Write the weekly reality-pulse node so the week lands on the timeline.
    pulse_id = None
    if emit_pulse:
        pulse_node = build_weekly_node(
            reality_before, dimension_updates, (update_log or {}).get("reasoning", ""), now
        )
        if pulse_node is not None:
            pulse_id = pulse_node["id"]
            pulse_path = nodes_dir / f"{pulse_id}.yaml"
            if not pulse_path.exists():
                pulse_path.write_text(build_node_yaml(pulse_node))

    # Append to update log
    log_path = data_dir / "reality_stream_log.json"
    log_entries = []
    if log_path.exists():
        try:
            log_entries = json.loads(log_path.read_text())
        except (json.JSONDecodeError, ValueError):
            log_entries = []

    log_entry = {
        "timestamp": now.isoformat(),
        "dimension_updates": dimension_updates,
        "new_nodes": [n["id"] for n in new_nodes],
        "pulse_node": pulse_id,
        "reasoning": (update_log or {}).get("reasoning", ""),
    }
    log_entries.append(log_entry)
    log_path.write_text(json.dumps(log_entries, indent=2))

    return reality_path


def _fmt_value(v) -> str:
    """Canonical number formatting so rewrites don't churn the git diff.

    Floats print with at most 4 decimals, trailing zeros trimmed, but always
    keep one decimal so YAML round-trips them as floats (1.0, not 1).
    """
    if isinstance(v, float):
        s = f"{v:.4f}".rstrip("0")
        if s.endswith("."):
            s += "0"
        return s
    return str(v)


def _write_reality_yaml(path: Path, data: dict) -> None:
    """Write reality YAML preserving structure."""
    # Write with comments for major sections
    lines = [
        "# Real-world values — auto-updated by reality stream",
        f"# Last update: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        f"year: {data.get('year', 2026)}",
        "",
    ]

    # Group dimensions by category (matching original file structure)
    categories = {
        "Geopolitical": [
            "us_polarization", "eu_cohesion", "us_global_standing", "china_power_index",
            "russia_stability", "middle_east_stability", "india_power_index", "latin_america_stability",
        ],
        "Economic": [
            "global_gdp_growth_modifier", "inequality_index", "us_debt_gdp_ratio",
            "crypto_market_cap_trillion", "supply_chain_resilience",
        ],
        "Technology": [
            "ai_development_year_offset", "internet_freedom_index", "social_media_penetration",
            "human_augmentation_prevalence", "space_development_index",
        ],
        "Security": [
            "nuclear_risk_level", "terrorism_threat_index", "surveillance_state_index",
            "global_cyber_damage_annual_b", "drone_warfare_prevalence",
        ],
        "Climate / Environment": [
            "climate_temp_anomaly", "renewable_energy_share", "sea_level_rise_meters",
            "biodiversity_index", "water_stress_index", "food_security_index", "arctic_ice_status",
        ],
        "Human / Social": [
            "global_pandemic_deaths", "conflict_deaths", "opioid_deaths_cumulative",
            "global_democracy_index", "us_institutional_trust", "misinformation_severity",
            "racial_justice_index", "gender_equity_index", "us_life_expectancy_delta",
            "global_population_billions", "median_age_global", "automation_displacement",
        ],
        "Governance / Structure": [
            "governance_model", "us_unity_index", "europe_federation_index",
            "china_regime_type", "middle_east_post_oil", "arctic_sovereignty_resolved",
            "africa_development_index",
        ],
        "Existential": [
            "existential_risk_cumulative",
        ],
    }

    for cat_name, dims in categories.items():
        lines.append(f"# ── {cat_name} ──")
        for dim in dims:
            if dim in data:
                lines.append(f"{dim}: {_fmt_value(data[dim])}")
        lines.append("")

    path.write_text("\n".join(lines))


def export_reality_snapshot(data_dir: Path, out_path: Path) -> Path:
    """Export reality state + recent stream log as static JSON.

    The production site is static files — serve.py's /api/reality endpoints
    only exist on the dev server, so the frontend reads this snapshot instead.
    """
    reality_path = data_dir / "reality_2026.yaml"
    with open(reality_path) as f:
        reality = yaml.safe_load(f)

    log_entries = []
    log_path = data_dir / "reality_stream_log.json"
    if log_path.exists():
        try:
            log_entries = json.loads(log_path.read_text())
        except (json.JSONDecodeError, ValueError):
            log_entries = []

    snapshot = {
        "generated": datetime.now(UTC).isoformat(),
        "reality": reality,
        "stream_log": log_entries[-5:],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2))
    return out_path


# ── High-level orchestration ──


async def run_reality_stream(
    data_dir: Path,
    provider: LLMProvider,
    newsapi_key: str,
    days_back: int = 7,
    dry_run: bool = False,
    emit_pulse: bool = True,
) -> dict:
    """Full reality stream cycle: fetch news → analyze → update.

    Args:
        data_dir: Path to csim data directory
        provider: LLM provider for analysis
        newsapi_key: NewsAPI.org API key
        days_back: How many days of news to fetch
        dry_run: If True, don't write files — just return proposed changes

    Returns:
        Dict with: dimension_updates, new_nodes, reasoning, news_count
    """
    # 1. Fetch news
    news_items = fetch_news_headlines(newsapi_key, days_back=days_back)
    if not news_items:
        return {
            "dimension_updates": {},
            "new_nodes": [],
            "reasoning": "No news fetched — check API key or connectivity.",
            "news_count": 0,
        }

    # 2. Load current state
    reality_path = data_dir / "reality_2026.yaml"
    with open(reality_path) as f:
        current_state = yaml.safe_load(f)

    # Check last update time from log
    log_path = data_dir / "reality_stream_log.json"
    last_update = None
    if log_path.exists():
        try:
            log = json.loads(log_path.read_text())
            if log:
                last_update = log[-1].get("timestamp")
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. LLM analysis
    result = await analyze_news(provider, news_items, current_state, last_update)

    # 4. Apply updates (unless dry run)
    if not dry_run:
        update_reality(
            data_dir,
            result.get("dimension_updates", {}),
            result.get("new_nodes", []),
            update_log={"reasoning": result.get("reasoning", "")},
            emit_pulse=emit_pulse,
        )

    return {
        "dimension_updates": result.get("dimension_updates", {}),
        "new_nodes": result.get("new_nodes", []),
        "reasoning": result.get("reasoning", ""),
        "news_count": len(news_items),
    }
