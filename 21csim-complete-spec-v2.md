# 21csim — The 21st Century Counterfactual Simulator

## Complete Implementation Specification v2.0

---

## Table of Contents

1. Project Overview
2. Architecture and Data Models
3. World State System
4. Scenario Graph Engine
5. Node Definitions: Historical Era (2000–2030) — 102 Nodes
6. Node Definitions: Future Era (2030–2100) — 127 Nodes
7. CLI Experience Design
8. Sound Engine (WP7)
9. Web Viewer and Public Launch
10. Implementation Phasing
11. Testing and Calibration

---

## 1. Project Overview

### What Is This?

A command-line tool (and companion web viewer) that models the major inflection points of the 21st century (2000–2100) as a directed acyclic graph with probabilistic branching, runs Monte Carlo simulations sampling from historically-informed probability distributions, and renders alternate histories as narrative output.

Each run produces a plausible alternate 21st century. Batch runs reveal which decisions had the most leverage over how the century turned out.

### Why?

The casual question "what if Gore had won?" or "what if 9/11 hadn't happened?" is actually a question about causal structure — which events are path-dependent, which are inevitable, and which variables have the most leverage. This tool turns that casual wondering into a rigorous Monte Carlo analysis.

### Key Properties

- **229 decision nodes** spanning 2000–2100
- **32 world-state dimensions** tracking climate, politics, technology, security, demographics, and more
- **Cascading dependencies** — upstream outcomes shift downstream probability distributions
- **Conditional gating** — future nodes only fire if world-state conditions are met
- **Deterministic seeding** — every run is reproducible
- **YAML-driven** — all scenario data lives in YAML, not code. Swappable scenarios.
- **Sound design** — runtime-synthesized audio cues for era transitions, nuclear events, extinction, transcendence
- **Web viewer** — React-based interactive viewer with pre-generated runs, shareable permalinks

### Tech Stack

```
Language:         Python 3.11+
CLI Framework:    typer
Key Dependencies: numpy, networkx, rich, pyyaml
Web Viewer:       React + TypeScript + Tailwind + Web Audio API
Hosting:          Static site (Netlify/Cloudflare Pages)
Package Manager:  uv or pip
```

---

## 2. Architecture and Data Models

### Directory Structure

```
21csim/
├── pyproject.toml
├── README.md
├── METHODOLOGY.md
├── CONTRIBUTING.md
├── LICENSE                          # MIT
├── src/
│   └── csim/
│       ├── __init__.py
│       ├── cli.py                   # Typer CLI entrypoint
│       ├── engine.py                # Simulation engine (DAG traversal + sampling)
│       ├── models.py                # Data models (events, outcomes, timelines)
│       ├── graph.py                 # DAG construction, dependency resolution
│       ├── renderer.py              # Rich-based terminal output
│       ├── world_state.py           # World state tracker + composite scoring
│       ├── analysis.py              # Batch statistics and sensitivity
│       ├── sound.py                 # Runtime audio synthesis
│       ├── exporter.py              # JSON export for web viewer
│       └── data/
│           ├── scenario.yaml        # Master scenario definition
│           ├── world_state_schema.yaml
│           └── nodes/               # Individual node YAML files (229 files)
│               ├── 2000_election.yaml
│               ├── 2001_911.yaml
│               ├── ...
│               └── 2099_verdict.yaml
├── web/                             # React web viewer (separate build)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── audio/
│   │   └── data/
│   ├── public/
│   │   ├── runs/                    # Pre-generated JSON run files
│   │   └── batch/
│   └── package.json
├── blog/                            # Launch blog post
│   └── 21csim-launch.md
└── tests/
    ├── test_engine.py
    ├── test_graph.py
    ├── test_world_state.py
    ├── test_sound.py
    └── test_models.py
```

### pyproject.toml

```toml
[project]
name = "21csim"
version = "0.1.0"
description = "Monte Carlo counterfactual simulator for 21st century world history (2000-2100)"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "numpy>=1.26",
    "networkx>=3.2",
    "rich>=13.7",
    "pyyaml>=6.0",
]

[project.scripts]
21csim = "csim.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Core Data Models (`models.py`)

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class EventStatus(Enum):
    HISTORICAL = "HISTORICAL"
    DIVERGENCE = "DIVERGENCE"
    PREVENTED = "PREVENTED"
    ACCELERATED = "ACCELERATED"
    DELAYED = "DELAYED"
    ESCALATED = "ESCALATED"
    DIMINISHED = "DIMINISHED"

class OutcomeClass(Enum):
    GOLDEN_AGE = "GOLDEN-AGE"                  # Composite > 0.7
    PROGRESS = "PROGRESS"                      # 0.3 < composite <= 0.7
    MUDDLING_THROUGH = "MUDDLING-THROUGH"      # -0.1 < composite <= 0.3
    DECLINE = "DECLINE"                        # -0.5 < composite <= -0.1
    CATASTROPHE = "CATASTROPHE"                # -0.8 < composite <= -0.5
    EXTINCTION = "EXTINCTION"                  # Composite <= -0.8
    TRANSCENDENCE = "TRANSCENDENCE"            # Post-human markers triggered
    RADICALLY_DIFFERENT = "RADICALLY-DIFFERENT" # 15+ divergences, hard to classify

@dataclass
class SimEvent:
    year_month: str                 # "YYYY-MM"
    node_id: str
    title: str
    description: str
    status: EventStatus
    branch_taken: str
    domain: str
    probability_of_branch: float
    explanation: Optional[str] = None
    delta: Optional[str] = None
    world_state_delta: dict = field(default_factory=dict)
    is_high_impact: bool = False    # Sum of absolute deltas > 0.10
    confidence: str = "HIGH"        # HIGH for historical era, MEDIUM/LOW for future

@dataclass
class SimOutcome:
    seed: int
    events: list[SimEvent] = field(default_factory=list)
    final_state: "WorldState" = None
    outcome_class: OutcomeClass = OutcomeClass.MUDDLING_THROUGH
    headline: str = ""
    composite_score: float = 0.0
    percentile: float = 50.0
    total_divergences: int = 0
    first_divergence_year: Optional[str] = None
    largest_divergence_node: Optional[str] = None
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
```

---

## 3. World State System

### WorldState Dataclass (`world_state.py`)

32 dimensions tracking the state of the world. Initialized to year-2000 baselines. Updated by each node's outcome effects as the simulation traverses the DAG.

```python
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
```

### Effect Application

```python
def apply_effects(state: WorldState, effects: dict) -> WorldState:
    """
    Apply a node's outcome effects to the world state.

    Effect types:
    - Absolute:    {"us_polarization": 0.65}
    - Delta:       {"us_polarization": "+0.12"}
    - Multiplier:  {"global_gdp_growth_modifier": "*0.95"}
    - Conditional: {"if": "us_polarization > 0.6", "then": {"nuclear_risk_level": "+0.05"}}

    All values are clamped to their valid ranges after application.
    """
```

### Composite Scoring

```python
def compute_composite_score(state: WorldState) -> float:
    """
    Weighted composite of all dimensions, normalized to [-1, 1].
    Positive = better than historical, negative = worse.

    Weight categories (descending priority):
    - Existential (nuclear use, extinction risk): extreme weight
    - Human death toll (conflict, pandemic, opioid): high weight
    - Climate (temp anomaly, food security, water): high weight
    - Freedom (democracy, internet, surveillance): moderate weight
    - Prosperity (GDP, inequality): moderate weight
    - Stability (polarization, cohesion): moderate weight
    - Progress (AI, space, technology): low weight

    The weighting reflects a humanist value system:
    avoiding death > avoiding suffering > preserving freedom > prosperity > progress.
    """

def classify_outcome(state: WorldState, events: list) -> OutcomeClass:
    """
    Classify the simulation outcome.

    EXTINCTION:              existential_risk > 0.9 OR nuclear exchange + climate > 4°C
    CATASTROPHE:             composite <= -0.5
    TRANSCENDENCE:           human_augmentation > 0.6 AND space_dev > 0.5 AND composite > 0.5
    GOLDEN_AGE:              composite > 0.7 AND no major conflicts
    PROGRESS:                0.3 < composite <= 0.7
    MUDDLING_THROUGH:        -0.1 < composite <= 0.3
    DECLINE:                 -0.5 < composite <= -0.1
    RADICALLY_DIFFERENT:     total_divergences > 150 AND |composite| < 0.3
    """

def generate_headline(state: WorldState, events: list) -> str:
    """
    Generate a one-line alternate history headline based on the most
    significant divergence chain. Format: "The [Adjective] Century: [Description]"

    Examples:
    - "The Near-Miss Century: Climate Crisis Barely Averted"
    - "The Gore Presidency: No Iraq War, Slower Polarization"
    - "The Long Collapse: Cascading Failures from 2008 Onward"
    - "The Ascent: Humanity Transcends Through AI Partnership"
    - "The Quiet Century: Nothing Dramatic, Steady Progress"
    """
```

---

## 4. Scenario Graph Engine

### Node YAML Schema

Every node follows this schema. Each node is a standalone YAML file in `data/nodes/`.

```yaml
id: "unique_node_id"                # e.g., "2003_iraq"
year_month: "YYYY-MM"               # When this event occurs
title: "Short Title"                 # e.g., "Iraq War Decision"
description: >                       # Historical context (multiline)
  What happened and why it matters.
domain: "geopolitical"               # geopolitical|economic|technology|security|climate|social|demographics|space
confidence: "HIGH"                   # HIGH (historical)|MEDIUM (near-future)|LOW (speculative)

# ── Sampling ──
variable: "variable_name"            # What's being decided
distribution:
  type: "categorical"                # categorical|bernoulli|normal
  options:                           # For categorical:
    branch_a: 0.50                   #   branch_name: probability
    branch_b: 0.30                   #   Must sum to 1.0
    branch_c: 0.20

# ── Dependencies ──
dependencies:                        # How upstream nodes modify this node
  - node: "upstream_node_id"
    branch: "specific_branch"        # Which upstream outcome triggers modification
    modifies:
      branch_a: "+0.10"             # Shift probability mass
      branch_b: "-0.10"

# ── Conditional Gating ──
conditional: null                    # null = always fires
# OR: "climate_temp_anomaly > 1.5 AND existential_risk_cumulative < 0.3"

# ── Outcome Branches ──
outcomes:
  branch_a:
    status: "HISTORICAL"             # EventStatus enum value
    description: "What happens"
    explanation: "Why (for narration)"
    world_state_effects:
      dimension_name: "+0.XX"        # Delta
      other_dimension: "*0.95"       # Multiplier
      absolute_dim: 0.65             # Absolute set
    cascading_modifiers:             # How this affects downstream nodes
      downstream_node.branch_x: "+0.10"
      other_node.distribution.mean: "-5"
  branch_b:
    # ...
```

### Graph Construction (`graph.py`)

```python
def build_graph(scenario_dir: Path) -> nx.DiGraph:
    """
    Parse all node YAML files into a networkx DiGraph.

    - Nodes are keyed by id
    - Nodes store their full YAML data as attributes
    - Edges encode dependencies (upstream → downstream)
    - Edge attributes store modification rules
    - Validates: no cycles, all referenced nodes exist, probabilities sum to 1.0
    - Returns topologically sorted traversal order (chronological primary, topological secondary)
    """

def get_modified_distribution(node_id: str, results: dict, graph: nx.DiGraph) -> dict:
    """
    Given upstream results, compute the adjusted probability distribution for a node.

    For categorical distributions:
    1. Start with base probabilities
    2. Apply all upstream modifications (additive shifts to probability mass)
    3. Clamp all branches to [0, 1]
    4. Renormalize to sum to 1.0

    For normal distributions:
    - Modify mean (additive) and std (multiplicative)
    - Apply clip bounds after modification
    """

def is_reachable(node_id: str, results: dict, graph: nx.DiGraph) -> bool:
    """
    Check if a node should fire given upstream results.

    A node fires if:
    1. It appears in at least one upstream outcome's `next` list (or has no upstream constraints)
    2. Its `conditional` expression evaluates to True against current world state
    3. The simulation hasn't terminated early (extinction)
    """
```

### Simulation Engine (`engine.py`)

```python
def simulate(scenario: Scenario, seed: int) -> SimOutcome:
    """
    Core simulation loop for a single run.

    1. Initialize WorldState to year-2000 baselines
    2. Initialize numpy RNG with seed
    3. For each node in chronological/topological order:
       a. Check reachability (conditional gating + upstream constraints)
       b. Skip if not reachable
       c. Compute modified probability distribution from upstream results
       d. Sample from distribution
       e. Determine outcome branch
       f. Apply world_state_effects to WorldState
       g. Record SimEvent
       h. Check for early termination (extinction)
    4. Compute composite score
    5. Classify outcome
    6. Generate headline
    7. Build causal chains for key dimensions
    8. Return SimOutcome
    """

def sample(distribution: dict, rng: np.random.Generator) -> str:
    """
    Sample from a distribution.

    categorical: weighted random choice among branches
    bernoulli: rng.random() < p
    normal: rng.normal(mean, std), clipped to range
    """

def simulate_batch(scenario: Scenario, iterations: int, seeds: list[int] = None) -> BatchResult:
    """
    Run N simulations. Optionally parallelize with multiprocessing.
    Compute aggregate statistics, leverage rankings, and common paths.
    """
```

### Performance Requirements

- Single run: < 50ms (229 nodes, all numpy operations)
- 10,000 runs: < 60 seconds (parallelized)
- 100,000 runs (for seed curation): < 10 minutes
## 5. Node Definitions: Historical Era (2000–2030)

### Node Map

102 nodes across 7 domains. Listed chronologically within each domain. Full YAML for marquee nodes; abbreviated format for supporting nodes.

**Reading the abbreviated format:**
```yaml
id: "node_id"
variable: "variable_name"
options:
  branch_a: 0.XX    # Short description
  branch_b: 0.XX    # Short description
dependencies: [upstream_node_ids]
key_effects: dimension1, dimension2
cascading: brief description of downstream impact
```

All abbreviated nodes follow the full YAML schema — the abbreviated format here is for spec readability. Claude Code should expand each to full YAML during implementation.

---

### GEOPOLITICAL — 12 Nodes

#### GP01: 2000 US Presidential Election (2000-11) ★ MARQUEE

```yaml
id: "2000_election"
year_month: "2000-11"
title: "2000 US Presidential Election"
description: >
  The closest presidential election in modern US history. Bush v. Gore
  decided by 537 votes in Florida after a Supreme Court decision halting
  the recount. Shaped foreign policy, climate policy, judicial appointments,
  and the trajectory of American polarization for decades.
domain: "geopolitical"
confidence: "HIGH"
variable: "election_winner"
distribution:
  type: "categorical"
  options:
    bush_wins: 0.52
    gore_wins: 0.45
    contested_months: 0.03
dependencies: []
outcomes:
  bush_wins:
    status: "HISTORICAL"
    description: "George W. Bush wins after Supreme Court halts Florida recount"
    world_state_effects:
      us_polarization: "+0.05"
    cascading_modifiers:
      2003_iraq.full_invasion: "+0.25"
      2005_katrina.catastrophic_failure: "+0.10"
      2015_paris_climate.agreement_ambition: "-0.05"
  gore_wins:
    status: "DIVERGENCE"
    description: "Al Gore wins after full Florida recount"
    explanation: "Butterfly ballot confusion resolved, Gore carries Florida by ~2,000 votes"
    world_state_effects:
      us_polarization: "+0.03"
      renewable_energy_share: "+0.02"
    cascading_modifiers:
      2003_iraq.full_invasion: "-0.40"
      2005_katrina.adequate_response: "+0.20"
      2008_financial_crisis.mild_recession: "+0.0"
      2015_paris_climate.binding_agreement: "+0.10"
      2016_us_election.polarization_factor: "-0.08"
  contested_months:
    status: "DIVERGENCE"
    description: "Constitutional crisis — no clear president until February 2001"
    explanation: "Supreme Court ruling ignored, dueling electors, House decides"
    world_state_effects:
      us_polarization: "+0.15"
      us_global_standing: "-0.08"
      global_democracy_index: "-0.02"
    cascading_modifiers:
      2001_911.faa_response_readiness: "-0.05"
      2003_iraq.full_invasion: "-0.15"
```

#### GP02: September 11 Attacks (2001-09) ★ MARQUEE

```yaml
id: "2001_911"
year_month: "2001-09"
title: "September 11 Attacks"
description: >
  Coordinated al-Qaeda hijackings of four commercial aircraft. Two struck
  the World Trade Center, one hit the Pentagon, one crashed in Pennsylvania.
  2,977 killed. The defining event shaping US foreign policy, civil liberties,
  and global security architecture for the entire century.
domain: "security"
confidence: "HIGH"
variable: "attack_outcome"
distribution:
  type: "categorical"
  options:
    historical_full: 0.35
    partial_success: 0.30
    single_attack: 0.15
    plot_disrupted: 0.12
    worse_outcome: 0.08
dependencies:
  - node: "2000_election"
    branch: "contested_months"
    modifies:
      historical_full: "+0.05"
      plot_disrupted: "-0.05"
outcomes:
  historical_full:
    status: "HISTORICAL"
    description: "All four hijackings succeed; WTC, Pentagon struck; UA93 crashes in PA"
    world_state_effects:
      us_polarization: "+0.08"
      us_global_standing: "+0.10"
      terrorism_threat_index: "+0.35"
      surveillance_state_index: "+0.20"
      middle_east_stability: "-0.10"
      conflict_deaths: "+3000"
      internet_freedom_index: "-0.05"
    cascading_modifiers:
      2003_iraq.full_invasion: "+0.20"
      2013_snowden.surveillance_scale: "+0.30"
  partial_success:
    status: "DIVERGENCE"
    description: "1-2 flights hit targets; others intercepted or failed"
    explanation: "Earlier FAA response or passenger awareness prevents full attack"
    world_state_effects:
      us_polarization: "+0.05"
      terrorism_threat_index: "+0.20"
      surveillance_state_index: "+0.12"
      conflict_deaths: "+800"
    cascading_modifiers:
      2003_iraq.full_invasion: "+0.05"
      2013_snowden.surveillance_scale: "+0.15"
  single_attack:
    status: "DIVERGENCE"
    description: "Only WTC North Tower struck; other plots foiled in execution"
    explanation: "Rapid military response after first impact; heightened cabin awareness"
    world_state_effects:
      terrorism_threat_index: "+0.12"
      surveillance_state_index: "+0.08"
      conflict_deaths: "+1600"
    cascading_modifiers:
      2003_iraq.full_invasion: "-0.10"
  plot_disrupted:
    status: "DIVERGENCE"
    description: "9/11 plot disrupted before execution"
    explanation: "FBI/CIA intelligence sharing catches plotters; Phoenix/Minneapolis memos acted on"
    world_state_effects:
      terrorism_threat_index: "+0.05"
      surveillance_state_index: "+0.03"
      us_global_standing: "+0.02"
    cascading_modifiers:
      2003_iraq.full_invasion: "-0.35"
      2013_snowden.surveillance_scale: "-0.10"
      2021_afghanistan.withdrawal_pressure: "-0.15"
  worse_outcome:
    status: "ESCALATED"
    description: "All four flights hit targets including US Capitol"
    explanation: "UA93 passenger revolt fails; Capitol struck during session"
    world_state_effects:
      us_polarization: "+0.12"
      terrorism_threat_index: "+0.45"
      surveillance_state_index: "+0.30"
      conflict_deaths: "+3500"
      nuclear_risk_level: "+0.05"
      global_democracy_index: "-0.03"
    cascading_modifiers:
      2003_iraq.full_invasion: "+0.30"
      2013_snowden.surveillance_scale: "+0.40"
```

#### GP03: Iraq War Decision (2003-03) ★ MARQUEE

```yaml
id: "2003_iraq"
year_month: "2003-03"
title: "Iraq War Decision"
description: >
  Decision to invade Iraq based on WMD claims and terrorism links.
  No WMDs found. Prolonged occupation, ~200,000+ Iraqi civilian deaths,
  ISIS emergence, massive erosion of US credibility. Arguably the single
  highest-leverage policy decision of the century.
domain: "geopolitical"
confidence: "HIGH"
variable: "iraq_decision"
distribution:
  type: "categorical"
  options:
    full_invasion: 0.55
    limited_strikes: 0.20
    diplomatic_resolution: 0.15
    delayed_invasion: 0.10
dependencies:
  - node: "2001_911"
    branch: "plot_disrupted"
    modifies:
      full_invasion: "-0.35"
      diplomatic_resolution: "+0.25"
      limited_strikes: "+0.10"
  - node: "2000_election"
    branch: "gore_wins"
    modifies:
      full_invasion: "-0.40"
      diplomatic_resolution: "+0.30"
      limited_strikes: "+0.10"
outcomes:
  full_invasion:
    status: "HISTORICAL"
    description: "US-led coalition invades Iraq; Saddam toppled"
    world_state_effects:
      us_global_standing: "-0.20"
      middle_east_stability: "-0.25"
      us_polarization: "+0.10"
      conflict_deaths: "+200000"
      us_debt_gdp_ratio: "+0.15"
      terrorism_threat_index: "+0.10"
      global_democracy_index: "-0.02"
    cascading_modifiers:
      2010_arab_spring.regional_instability: "+0.15"
      2014_crimea.us_credibility_deterrent: "-0.10"
      2016_brexit.anti_establishment: "+0.08"
      2016_us_election.anti_establishment: "+0.10"
      2022_russia_ukraine.us_deterrence: "-0.05"
  limited_strikes:
    status: "DIVERGENCE"
    description: "US conducts air strikes against suspected WMD sites only"
    explanation: "Congress refuses ground invasion authorization"
    world_state_effects:
      us_global_standing: "-0.05"
      conflict_deaths: "+5000"
      us_debt_gdp_ratio: "+0.02"
  diplomatic_resolution:
    status: "DIVERGENCE"
    description: "UN inspections continue; no military action taken"
    explanation: "Inspectors given more time; WMD claims debunked before invasion"
    world_state_effects:
      us_global_standing: "+0.05"
      middle_east_stability: "+0.05"
      global_democracy_index: "+0.01"
    cascading_modifiers:
      2010_arab_spring.regional_instability: "-0.10"
      2014_crimea.us_credibility_deterrent: "+0.05"
      2016_brexit.anti_establishment: "-0.05"
      2016_us_election.anti_establishment: "-0.08"
      2022_russia_ukraine.us_deterrence: "+0.05"
  delayed_invasion:
    status: "DIVERGENCE"
    description: "Invasion delayed to 2004-2005 with broader coalition"
    world_state_effects:
      us_global_standing: "-0.08"
      middle_east_stability: "-0.15"
      conflict_deaths: "+120000"
      eu_cohesion: "+0.05"
```

#### GP04–GP12: Remaining Geopolitical Nodes

```yaml
# GP04: Hurricane Katrina Response (2005-08)
id: "2005_katrina"
options:
  catastrophic_failure: 0.50   # Historical — FEMA fails
  adequate_response: 0.30      # FEMA acts within 24hrs; ~400 deaths
  exemplary_response: 0.10     # Pre-positioned assets; <100 deaths
  worse_failure: 0.10          # Even slower; 3,000+ die
dependencies: [2000_election]
key_effects: us_polarization, inequality_index, us_institutional_trust
cascading: affects 2020_covid_response (institutional trust)

# GP05: Arab Spring (2010-12)
id: "2010_arab_spring"
options:
  historical_mixed: 0.45       # Tunisia succeeds; Egypt coup; Libya/Syria civil war
  broader_success: 0.15        # Multiple successful democratic transitions
  no_uprising: 0.15            # Protests fizzle
  regional_war: 0.10           # Cascading multi-state conflict
  delayed_5_years: 0.15        # Same pressures erupt ~2015
dependencies: [2003_iraq, 2008_financial_crisis, 2007_iphone]
key_effects: middle_east_stability, conflict_deaths (+500K historical), global_democracy_index
cascading: affects 2014_crimea, 2015_paris_attacks, 2022_russia_ukraine

# GP06: Bin Laden Operation (2011-05)
id: "2011_bin_laden"
options:
  successful_raid: 0.55        # Historical
  raid_fails: 0.20             # Mission aborts; bin Laden escapes
  diplomatic_capture: 0.10     # Pakistan cooperates; arrest
  not_found: 0.15              # Intelligence never locates compound
dependencies: [2001_911]
key_effects: terrorism_threat_index, us_global_standing

# GP07: Crimea Annexation (2014-03)
id: "2014_crimea"
options:
  historical_annexation: 0.50  # Russia annexes Crimea
  failed_operation: 0.15       # Ukrainian military resists
  negotiated_autonomy: 0.20    # Crimea gets autonomy within Ukraine
  full_eastern_invasion: 0.15  # Russia takes Crimea + Donbas in 2014
dependencies: [2003_iraq, 2010_arab_spring, 2013_syria_redline]
key_effects: russia_stability, nuclear_risk_level, eu_cohesion
cascading: heavily affects 2022_russia_ukraine

# GP08: Brexit Referendum (2016-06)
id: "2016_brexit"
options:
  leave_wins: 0.48             # Historical
  remain_wins: 0.40            # Remain wins 52-48
  no_referendum: 0.07          # Cameron doesn't call it
  leave_then_reverse: 0.05     # Leave wins but second referendum reverses
dependencies: [2003_iraq, 2008_financial_crisis, 2010_arab_spring, 2010_euro_crisis]
key_effects: eu_cohesion, global_democracy_index

# GP09: 2016 US Presidential Election (2016-11)
id: "2016_us_election"
options:
  trump_wins: 0.48             # Historical
  clinton_wins: 0.42
  third_party_surge: 0.05
  contested_result: 0.05
dependencies: [2003_iraq, 2008_financial_crisis, 2007_iphone, 2004_social_media]
key_effects: us_polarization, us_global_standing, climate_temp_anomaly
cascading: affects 2018_trade_war, 2020_us_election, 2022_russia_ukraine

# GP10: 2020 US Presidential Election (2020-11)
id: "2020_us_election"
options:
  biden_wins: 0.50             # Historical
  trump_wins: 0.30
  close_contested: 0.15
  landslide_either: 0.05
dependencies: [2016_us_election, 2020_covid_response]
key_effects: us_polarization, climate_temp_anomaly

# GP11: January 6 Capitol Breach (2021-01)
id: "2021_jan6"
conditional: "2020_us_election != trump_wins"
options:
  historical_breach: 0.40      # Historical
  peaceful_protest: 0.25
  worse_violence: 0.10         # Organized armed assault; legislators harmed
  no_protest: 0.25             # Trump concedes
dependencies: [2020_us_election, 2016_us_election, 2016_misinformation]
key_effects: us_polarization, global_democracy_index

# GP12: 2024 US Presidential Election (2024-11)
id: "2024_us_election"
options:
  trump_wins: 0.48             # Historical
  harris_wins: 0.40
  contested: 0.07
  third_party: 0.05
dependencies: [2020_us_election, 2022_inflation_crisis, 2021_jan6]
key_effects: us_polarization, us_global_standing, climate_temp_anomaly
```

---

### ECONOMIC — 18 Nodes

```yaml
# EC01: Dot-Com Crash Aftermath (2001-03)
id: "2001_dotcom_aftermath"
options:
  historical_slow_rates_cut: 0.50  # Greenspan cuts to 1%; seeds housing bubble
  faster_recovery: 0.20
  deeper_recession: 0.15
  structural_reform: 0.15
cascading: affects 2008_financial_crisis severity

# EC02: China Joins WTO (2001-12)
id: "2001_china_wto"
options:
  historical_full_accession: 0.60  # Historical — minimal enforcement
  conditional_accession: 0.20      # Stricter IP/currency conditions
  delayed_5_years: 0.10
  no_accession: 0.10
key_effects: china_power_index, inequality_index, supply_chain_resilience
cascading: affects 2018_trade_war, 2016_us_election, 2026_taiwan_strait

# EC03: BRICS / Emerging Market Boom (2003-06)
id: "2003_brics_rise"
options:
  historical_boom_then_bust: 0.50
  sustained_growth: 0.20
  china_only: 0.15
  no_boom: 0.15
dependencies: [2001_china_wto]
key_effects: inequality_index, africa_development_index, india_power_index

# EC04: 2008 Financial Crisis (2008-09) ★ MARQUEE
id: "2008_financial_crisis"
options:
  historical_severe: 0.45          # Lehman collapse; deep recession
  contained_early: 0.20            # Bear Stearns triggers earlier intervention
  great_depression_2: 0.15         # No TARP; cascading failures
  mild_recession: 0.20             # Better regulation prevented worst
dependencies: [2001_dotcom_aftermath, 2003_iraq]
key_effects: global_gdp, inequality_index, us_polarization, us_debt_gdp
cascading: affects 2010_arab_spring, 2016_brexit, 2016_us_election, 2022_inflation

# EC05: Euro Sovereign Debt Crisis (2010-05)
id: "2010_euro_crisis"
options:
  historical_austerity: 0.45       # Troika austerity; slow recovery
  fiscal_union: 0.15               # Eurobonds; faster recovery
  grexit: 0.15                     # Greece exits; contagion
  no_crisis: 0.15                  # Better fiscal discipline
  full_breakup: 0.10               # Euro collapses
dependencies: [2008_financial_crisis]
key_effects: eu_cohesion, inequality_index, global_democracy_index

# EC06: US Debt Ceiling Crises (2011-08)
id: "2011_debt_ceiling"
options:
  historical_recurring_crises: 0.50
  abolished_early: 0.15
  actual_default: 0.10
  grand_bargain: 0.25
dependencies: [2008_financial_crisis]
key_effects: us_institutional_trust, us_global_standing

# EC07: ZIRP Era / QE (2012-09)
id: "2012_zirp"
options:
  historical_extended_zirp: 0.50   # Near-zero rates for 12+ years
  early_normalization: 0.25        # Rate hikes begin 2014
  negative_rates_us: 0.10
  fiscal_over_monetary: 0.15
dependencies: [2008_financial_crisis]
key_effects: inequality_index, us_debt_gdp, global_gdp
cascading: affects 2022_inflation, 2013_crypto, 2023_ai_acceleration (VC funding)

# EC08: Bitcoin / Cryptocurrency (2013-11)
id: "2013_crypto"
options:
  historical_speculative: 0.45     # $2T+ speculative asset
  becomes_real_currency: 0.10
  regulated_early: 0.20
  banned_globally: 0.10
  stablecoin_dominance: 0.15
dependencies: [2008_financial_crisis]
key_effects: crypto_market_cap, inequality_index, global_cyber_damage

# EC09: Gig Economy / Labor Transformation (2014-06)
id: "2014_gig_economy"
options:
  historical_unregulated: 0.45
  regulated_as_employees: 0.20
  platform_cooperatives: 0.10
  automation_replaces: 0.25
dependencies: [2007_iphone, 2012_zirp]
key_effects: inequality_index, us_life_expectancy_delta

# EC10: US-China Trade War (2018-03)
id: "2018_trade_war"
options:
  historical_escalation: 0.45
  diplomatic_resolution: 0.20
  full_decoupling: 0.15
  no_trade_war: 0.20
dependencies: [2016_us_election, 2001_china_wto]
key_effects: china_power_index, global_gdp, supply_chain_resilience
cascading: affects 2023_ai_acceleration (chip controls), 2026_taiwan_strait

# EC11: WeWork / Unicorn Bubble (2019-09)
id: "2019_unicorn_bubble"
options:
  historical_slow_deflate: 0.50
  sharp_correction_2019: 0.20
  bubble_continues: 0.15
  healthy_ecosystem: 0.15
dependencies: [2012_zirp]

# EC12: COVID-19 Emergence (2019-12) ★ MARQUEE
id: "2019_covid_emergence"
options:
  historical_wuhan: 0.50
  contained_locally: 0.15
  earlier_emergence: 0.10
  delayed_2021: 0.15
  no_pandemic: 0.10
dependencies: []
key_effects: gates 2020_covid_response and related nodes

# EC13: COVID-19 Global Response (2020-03) ★ MARQUEE
id: "2020_covid_response"
conditional: "2019_covid_emergence != no_pandemic"
options:
  historical_fragmented: 0.40
  coordinated_early: 0.15
  faster_vaccines: 0.15
  catastrophic_failure: 0.10
  china_transparent: 0.20
dependencies: [2019_covid_emergence, 2016_us_election, 2005_katrina]
key_effects:
  historical: {global_pandemic_deaths: "+7000000", us_polarization: "+0.12", global_gdp: "*0.94"}
  coordinated: {global_pandemic_deaths: "+2000000", us_polarization: "+0.04"}
  catastrophic: {global_pandemic_deaths: "+25000000", global_gdp: "*0.85"}

# EC14: Global Supply Chain Crisis (2021-03)
id: "2021_supply_chain"
options:
  historical_prolonged: 0.45
  quick_recovery: 0.20
  permanent_reshoring: 0.15
  worse_collapse: 0.10
  china_decoupling: 0.10
dependencies: [2019_covid_emergence, 2001_china_wto]
key_effects: supply_chain_resilience, global_gdp
cascading: affects 2022_inflation_crisis

# EC15: Afghanistan Withdrawal (2021-08)
id: "2021_afghanistan"
options:
  historical_chaotic: 0.45
  orderly_withdrawal: 0.25
  no_withdrawal: 0.10
  negotiated_coalition: 0.20
dependencies: [2001_911, 2011_bin_laden, 2020_us_election]
key_effects: us_global_standing, terrorism_threat_index
cascading: affects 2022_russia_ukraine (perceived US weakness)

# EC16: Russia-Ukraine War (2022-02) ★ MARQUEE
id: "2022_russia_ukraine"
options:
  historical_invasion_stalemate: 0.35
  no_invasion: 0.20
  quick_russian_victory: 0.10
  nato_direct_involvement: 0.05
  quick_ukrainian_victory: 0.10
  nuclear_use: 0.03
  frozen_conflict: 0.17
dependencies: [2014_crimea, 2003_iraq, 2016_brexit, 2021_afghanistan, 2011_fukushima]
key_effects:
  historical: {conflict_deaths: "+300000", nuclear_risk_level: "+0.12", eu_cohesion: "+0.08"}
  nuclear_use: {nuclear_risk_level: "+0.40", conflict_deaths: "+500000", global_gdp: "*0.90"}
cascading: affects 2026_taiwan_strait, 2024_us_election

# EC17: Inflation Crisis (2022-06)
id: "2022_inflation_crisis"
options:
  historical_high_then_controlled: 0.45
  stagflation: 0.15
  hyperinflation_emerging: 0.10
  soft_landing: 0.30
dependencies: [2020_covid_response, 2022_russia_ukraine, 2012_zirp]

# EC18: BRICS Expansion (2023-08)
id: "2023_brics_expansion"
options:
  historical_expansion: 0.45
  effective_alternative: 0.15
  fractures: 0.20
  geopolitical_bloc: 0.10
  paper_tiger: 0.10
dependencies: [2022_russia_ukraine, 2018_trade_war]
key_effects: us_global_standing, china_power_index
```

---

### TECHNOLOGY — 15 Nodes

```yaml
# T01: Social Media Emergence (2004-02) ★ MARQUEE
id: "2004_social_media"
options:
  historical_ad_driven: 0.50       # Ad-funded, engagement-maximizing
  subscription_model: 0.15
  decentralized: 0.10
  regulated_early: 0.15
  slower_adoption: 0.10
key_effects: social_media_penetration (+0.55 historical), us_polarization (+0.10),
  misinformation_severity (+0.25), us_institutional_trust (-0.08)
cascading: affects 2010_arab_spring, 2016_us_election, 2017_metoo, all political nodes

# T02: Cloud Computing / AWS (2006-08)
id: "2006_cloud"
options:
  historical_hyperscaler: 0.55
  distributed_model: 0.15
  delayed_5_years: 0.10
  government_cloud: 0.10
  open_source_cloud: 0.10
cascading: affects 2023_ai_acceleration (compute), 2020_covid_response (remote work)

# T03: Smartphone Revolution (2007-06)
id: "2007_iphone"
options:
  historical_apple_led: 0.60
  open_platform_wins: 0.25
  delayed_3_years: 0.10
  fragmented_market: 0.05
cascading: affects 2010_arab_spring, 2016_us_election, 2017_metoo

# T04: WikiLeaks / Information Warfare (2010-07)
id: "2010_wikileaks"
options:
  historical_leaks: 0.50
  no_manning_leak: 0.25
  more_damaging: 0.10
  whistleblower_protection: 0.15
key_effects: internet_freedom_index, us_global_standing

# T05: Fukushima Nuclear Disaster (2011-03)
id: "2011_fukushima"
options:
  historical_meltdown: 0.40        # Three meltdowns; global nuclear retreat
  contained_quickly: 0.30
  worse_chernobyl_scale: 0.10
  no_tsunami_hit: 0.20
key_effects: renewable_energy_share, climate_temp_anomaly
cascading: affects 2022_russia_ukraine (EU energy dependence on Russian gas),
  2027_energy_transition (nuclear capacity)

# T06: Deep Learning / AlexNet (2012-10)
id: "2012_deep_learning"
options:
  historical_gpu_revolution: 0.50
  slower_progress: 0.20
  alternative_paradigm: 0.10
  earlier_breakthrough: 0.10
  compute_bottleneck: 0.10
dependencies: [2006_cloud]
cascading: affects 2023_ai_acceleration

# T07: Snowden Revelations (2013-06)
id: "2013_snowden"
options:
  historical_leak: 0.50
  no_leak: 0.25
  earlier_leak_2010: 0.10
  limited_leak: 0.15
dependencies: [2001_911]
key_effects: surveillance_state_index, internet_freedom_index

# T08: CRISPR Gene Editing (2015-12)
id: "2015_crispr"
options:
  historical_cautious: 0.50
  designer_babies_race: 0.10
  strict_global_ban: 0.15
  therapeutic_breakthrough: 0.25
key_effects: inequality_index, us_life_expectancy_delta

# T09: Self-Driving Cars (2016-03)
id: "2016_self_driving"
options:
  historical_delayed: 0.50
  achieved_2020: 0.10
  fatal_setback: 0.15
  gradual_2028: 0.25

# T10: Cybersecurity Inflection / WannaCry (2017-05)
id: "2017_wannacry"
options:
  historical_escalation: 0.50      # WannaCry, NotPetya, SolarWinds cascade
  cyber_geneva_convention: 0.10
  major_infrastructure_attack: 0.15
  defense_improves: 0.25
dependencies: [2010_stuxnet]
key_effects: global_cyber_damage, nuclear_risk_level

# T11: Cambridge Analytica / Platform Accountability (2018-03)
id: "2018_facebook_cambridge"
options:
  historical_minimal_reform: 0.50
  strong_regulation: 0.15
  platform_breakup: 0.10
  self_regulation_works: 0.15
  nothing_changes: 0.10
dependencies: [2004_social_media]
key_effects: misinformation_severity, internet_freedom_index

# T12: Quantum Computing (2019-10)
id: "2019_quantum"
options:
  historical_slow_progress: 0.45
  breakthrough_2025: 0.15
  quantum_winter: 0.20
  encryption_broken: 0.05
  hybrid_useful: 0.15

# T13: TikTok / Algorithmic Media (2020-06)
id: "2020_tiktok"
options:
  historical_dominance: 0.45
  banned_in_west: 0.20
  domestic_alternative: 0.15
  regulated_algorithm: 0.10
  youth_backlash: 0.10
dependencies: [2018_trade_war]
key_effects: misinformation_severity, china_power_index

# T14: AI Acceleration (2023-01) ★ MARQUEE
id: "2023_ai_acceleration"
options:
  historical_rapid: 0.40
  slower_progress: 0.20
  faster_agi: 0.10
  open_source_dominant: 0.15
  ai_winter: 0.05
  china_leads: 0.10
dependencies: [2012_deep_learning, 2006_cloud, 2018_trade_war, 2012_zirp]
key_effects: ai_development_year_offset, inequality_index, global_gdp
cascading: affects 2025_ai_regulation, 2028_agi_threshold, 2031_ai_displacement

# T15: Open Source AI / Llama 2 (2023-07)
id: "2023_open_source_ai"
options:
  historical_mixed: 0.45
  open_wins: 0.20
  closed_dominates: 0.20
  open_source_incident: 0.10
  fragmented: 0.05
dependencies: [2023_ai_acceleration]
key_effects: internet_freedom_index, inequality_index
```

---

### SECURITY — 15 Nodes

```yaml
# S01: Drone Warfare Program (2004-06)
id: "2004_drone_warfare"
options:
  historical_expansion: 0.50
  limited_use: 0.25
  banned_early: 0.05
  proliferation: 0.15
  autonomous_early: 0.05
dependencies: [2001_911, 2003_iraq]
key_effects: drone_warfare_prevalence, conflict_deaths, us_global_standing

# S02: North Korea Nuclear (2006-10)
id: "2006_north_korea"
options:
  historical_nuclear_state: 0.50
  denuclearization_deal: 0.10
  regime_collapse: 0.10
  frozen_program: 0.15
  preemptive_strike: 0.05
  nuclear_sale: 0.10
key_effects: nuclear_risk_level, china_power_index

# S03: Stuxnet / Cyber Warfare (2010-06)
id: "2010_stuxnet"
options:
  historical_escalation: 0.50
  contained_secret: 0.15
  cyber_arms_race: 0.15
  deterrence_established: 0.10
  iran_retaliates: 0.10
dependencies: [2003_iraq]
key_effects: global_cyber_damage, nuclear_risk_level

# S04: Libya Intervention (2011-03)
id: "2011_libya"
options:
  historical_intervention_chaos: 0.45
  no_intervention: 0.25
  full_commitment: 0.15
  arab_league_led: 0.15
key_effects: middle_east_stability, conflict_deaths
cascading: affects 2015_paris_attacks (Libya as ISIS staging ground)

# S05: Syria Red Line (2013-08)
id: "2013_syria_redline"
options:
  historical_no_strike: 0.45
  limited_strike: 0.25
  full_intervention: 0.10
  diplomatic_only: 0.20
key_effects: us_global_standing, middle_east_stability
cascading: affects 2014_crimea (Putin reads US resolve)

# S06: ISIS Rise (2014-06)
id: "2014_isis"
options:
  historical_caliphate: 0.45
  contained_early: 0.20
  worse_expansion: 0.10
  no_isis: 0.25
dependencies: [2003_iraq, 2010_arab_spring]
key_effects: terrorism_threat_index, middle_east_stability, conflict_deaths

# S07: Paris Attacks / ISIS Terror (2015-11)
id: "2015_paris_attacks"
options:
  historical_paris: 0.45
  no_major_western_attack: 0.25
  worse_multi_city: 0.10
  earlier_defeat: 0.20
dependencies: [2010_arab_spring, 2003_iraq, 2014_isis]
key_effects: terrorism_threat_index, eu_cohesion, surveillance_state_index

# S08: Iran Nuclear Deal / JCPOA (2015-07)
id: "2015_iran_deal"
options:
  historical_deal_then_withdrawal: 0.45
  deal_holds: 0.25
  no_deal: 0.15
  iran_nuclear_weapon: 0.05
  broader_peace: 0.10
dependencies: [2003_iraq, 2016_us_election]
key_effects: nuclear_risk_level, middle_east_stability

# S09: Paris Climate Agreement (2015-12)
id: "2015_paris_climate"
options:
  historical_agreement: 0.50       # Signed, weak enforcement
  binding_agreement: 0.15
  no_agreement: 0.20
  delayed_agreement: 0.15
dependencies: [2000_election, 2008_financial_crisis]
key_effects: climate_temp_anomaly, renewable_energy_share
cascading: affects 2025_climate_tipping, 2027_energy_transition

# S10: SolarWinds Cyber Espionage (2020-12)
id: "2020_solarwinds"
options:
  historical_discovered: 0.45
  never_discovered: 0.20
  retaliation: 0.10
  defensive_reform: 0.25
key_effects: global_cyber_damage, us_institutional_trust

# S11: Hypersonic Weapons Race (2021-10)
id: "2021_hypersonics"
options:
  historical_arms_race: 0.45
  arms_control: 0.10
  chinese_superiority: 0.15
  defense_breakthrough: 0.15
  non_event: 0.15
key_effects: nuclear_risk_level, china_power_index

# S12: Wagner Mutiny (2022-06)
id: "2022_wagner"
options:
  historical_mutiny: 0.45
  wagner_succeeds: 0.10
  private_military_norm: 0.25
  state_reasserts: 0.20
dependencies: [2022_russia_ukraine]
key_effects: russia_stability, global_democracy_index

# S13: AI Regulation (2025-06)
id: "2025_ai_regulation"
options:
  fragmented_national: 0.40
  coordinated_global: 0.15
  minimal_regulation: 0.25
  heavy_regulation: 0.20
dependencies: [2023_ai_acceleration, 2024_us_election, 2013_snowden]

# S14: Climate Tipping Points (2025-12)
id: "2025_climate_tipping"
options:
  on_track_2_5c: 0.40
  tipping_point_crossed: 0.15
  accelerated_action: 0.20
  technological_breakthrough: 0.15
  climate_conflict: 0.10
dependencies: [2015_paris_climate, 2011_fukushima, 2024_us_election]
key_effects: climate_temp_anomaly, conflict_deaths

# S15: AGI Threshold (2028-06)
id: "2028_agi_threshold"
options:
  no_agi_yet: 0.40
  proto_agi: 0.25
  full_agi: 0.08
  agi_accident: 0.02
  slow_takeoff: 0.25
dependencies: [2023_ai_acceleration, 2025_ai_regulation]
key_effects: ai_development_year_offset, existential_risk_cumulative
```

---

### SOCIAL / CULTURAL — 14 Nodes

```yaml
# SC01: Opioid Crisis (2003-01)
id: "2003_opioid_crisis"
options:
  historical_epidemic: 0.50        # 700K+ dead by 2030
  regulated_early: 0.15            # FDA restricts by 2005
  purdue_prosecuted: 0.15
  fentanyl_prevented: 0.10
  treatment_focused: 0.10
key_effects:
  historical: {opioid_deaths: "+700000", us_life_expectancy_delta: "-2.5", us_institutional_trust: "-0.05"}
  regulated_early: {opioid_deaths: "+150000", us_life_expectancy_delta: "-0.5"}

# SC02: Katrina Racial Reckoning (2005-09)
id: "2005_katrina_racial"
options:
  historical_slow_build: 0.50
  immediate_reform: 0.10
  no_reckoning: 0.20
  earlier_blm: 0.20
dependencies: [2005_katrina]
cascading: affects 2014_blm

# SC03: #MeToo Movement (2017-10)
id: "2017_metoo"
options:
  historical_viral: 0.50
  limited_hollywood: 0.25
  earlier_2013: 0.10
  backlash_dominant: 0.15
dependencies: [2007_iphone, 2004_social_media]
key_effects: gender_equity_index, global_democracy_index

# SC04: BLM / Ferguson (2014-08)
id: "2014_blm"
options:
  historical_wave: 0.45            # 2014 spark, 2020 explosion
  sustained_reform: 0.15
  backlash_dominant: 0.15
  no_movement: 0.10
  earlier_victory: 0.15
dependencies: [2004_social_media, 2005_katrina_racial]
key_effects: racial_justice_index, us_polarization

# SC05: Deaths of Despair / Life Expectancy (2014-01)
id: "2014_deaths_of_despair"
options:
  historical_decline: 0.50
  public_health_response: 0.20
  continues_worsening: 0.15
  reversal_by_2025: 0.15
dependencies: [2003_opioid_crisis, 2008_financial_crisis]
key_effects: us_life_expectancy_delta, inequality_index

# SC06: Marriage Equality / Gender Politics (2015-06)
id: "2015_marriage_equality"
options:
  historical_backlash_cycle: 0.45
  steady_progress: 0.20
  reversal: 0.10
  global_progress: 0.15
  culture_war_intensifies: 0.10
dependencies: [2016_us_election]
key_effects: gender_equity_index, us_polarization

# SC07: Misinformation Epidemic (2016-10) ★ MARQUEE
id: "2016_misinformation"
options:
  historical_escalation: 0.45      # Worsens through COVID, elections
  platform_intervention: 0.15
  media_literacy: 0.15
  epistemic_collapse: 0.10
  decentralized_trust: 0.15
dependencies: [2004_social_media, 2018_facebook_cambridge]
key_effects:
  historical: {misinformation_severity: "+0.15", us_polarization: "+0.08",
               us_institutional_trust: "-0.10", global_democracy_index: "-0.03"}
cascading: affects 2020_covid_response (vaccine hesitancy), 2021_jan6

# SC08: Populism / Democratic Backsliding (2018-01)
id: "2018_populism"
options:
  historical_global_wave: 0.50
  liberal_resilience: 0.15
  authoritarian_consolidation: 0.15
  new_alignment: 0.20
dependencies: [2008_financial_crisis, 2016_us_election, 2016_brexit, 2010_euro_crisis]
key_effects: global_democracy_index, us_polarization, eu_cohesion

# SC09: Anti-Vaccine Movement (2019-01)
id: "2019_antivax"
options:
  historical_growing: 0.50
  contained_niche: 0.20
  pandemic_wake_up: 0.15
  mandatory_vaccination: 0.10
  measles_outbreak: 0.05
dependencies: [2016_misinformation, 2004_social_media]
key_effects: misinformation_severity, global_pandemic_deaths

# SC10: Global Protest Wave (2019-06)
id: "2019_global_protests"
options:
  historical_widespread: 0.50
  successful_reforms: 0.15
  crushed_globally: 0.15
  no_wave: 0.20
key_effects: global_democracy_index, china_power_index

# SC11: Remote Work Revolution (2020-03)
id: "2020_remote_work"
options:
  historical_hybrid: 0.45
  full_remote_wins: 0.15
  return_to_office: 0.25
  geographic_revolution: 0.15
dependencies: [2019_covid_emergence, 2006_cloud]

# SC12: COVID Mental Health Crisis (2020-06)
id: "2020_mental_health"
options:
  historical_crisis: 0.50
  resilience: 0.15
  permanent_damage: 0.15
  treatment_revolution: 0.20
dependencies: [2019_covid_emergence, 2020_tiktok]

# SC13: Education Disruption (2020-09)
id: "2020_education"
options:
  historical_learning_loss: 0.45
  rapid_adaptation: 0.20
  permanent_transformation: 0.15
  generation_lost: 0.20
dependencies: [2019_covid_emergence]

# SC14: Second Pandemic (2029-03)
id: "2029_pandemic_2"
options:
  no_pandemic: 0.55
  contained_quickly: 0.20
  moderate_pandemic: 0.15
  severe_pandemic: 0.10
dependencies: [2020_covid_response]
```

---

### REGIONAL — 8 Nodes

```yaml
# R01: China — Xi Consolidation (2012-11)
id: "2012_xi_consolidation"
options:
  historical_consolidation: 0.50   # Xi abolishes term limits
  reform_faction_wins: 0.15
  economic_liberalization: 0.10
  instability: 0.10
  aggressive_expansion: 0.15
key_effects: china_power_index, china_regime_type, internet_freedom_index
cascading: affects 2018_trade_war, 2026_taiwan_strait

# R02: India — Modi Era (2014-05)
id: "2014_india_modi"
options:
  historical_rise: 0.50
  democratic_deepening: 0.15
  hindu_nationalism_dominant: 0.15
  economic_stall: 0.10
  india_china_conflict: 0.10
key_effects: india_power_index, global_democracy_index

# R03: Venezuela Collapse (2014-01)
id: "2014_venezuela"
options:
  historical_collapse: 0.50
  maduro_falls: 0.15
  muddling_through: 0.20
  us_intervention: 0.05
  regional_contagion: 0.10
key_effects: latin_america_stability

# R04: Africa Development (2015-01)
id: "2015_africa_development"
options:
  historical_mixed: 0.45
  african_century: 0.15
  resource_curse: 0.15
  climate_devastation: 0.15
  china_debt_trap: 0.10
key_effects: africa_development_index, global_democracy_index

# R05: Saudi Transformation (2017-06)
id: "2017_saudi_transformation"
options:
  historical_mbs: 0.45
  democratic_opening: 0.10
  succession_crisis: 0.15
  iran_war: 0.10
  oil_transition: 0.20
key_effects: middle_east_stability, renewable_energy_share

# R06: Myanmar Crisis (2021-02)
id: "2021_myanmar"
options:
  historical_coup: 0.50
  democracy_holds: 0.20
  rapid_restoration: 0.15
  full_civil_war: 0.15

# R07: European Right Wing Rise (2022-09)
id: "2022_european_right"
options:
  historical_mainstreaming: 0.45
  contained: 0.20
  governing_majority: 0.15
  eu_reform_response: 0.20
dependencies: [2010_euro_crisis, 2016_brexit, 2022_russia_ukraine]
key_effects: eu_cohesion, global_democracy_index

# R08: Taiwan Strait Crisis (2026-06) ★ MARQUEE
id: "2026_taiwan_strait"
options:
  tension_no_conflict: 0.45
  blockade: 0.20
  full_invasion: 0.08
  diplomatic_resolution: 0.15
  us_china_war: 0.02
  peaceful_unification: 0.10
dependencies: [2018_trade_war, 2022_russia_ukraine, 2024_us_election, 2012_xi_consolidation]
key_effects:
  us_china_war: {nuclear_risk_level: "+0.35", conflict_deaths: "+500000", global_gdp: "*0.80"}
  blockade: {china_power_index: "+0.05", global_gdp: "*0.95"}
```

---

### ENERGY / CLIMATE (Remaining) — 2 Nodes

```yaml
# EN01: Energy Transition (2027-06)
id: "2027_energy_transition"
options:
  gradual_transition: 0.40
  rapid_transition: 0.20
  fossil_resurgence: 0.15
  nuclear_renaissance: 0.15
  energy_crisis: 0.10
dependencies: [2011_fukushima, 2025_climate_tipping, 2022_russia_ukraine]
key_effects: renewable_energy_share, climate_temp_anomaly

# EN02: (2015_paris_climate already in Security section)
```

---

### Historical Era Total: 102 Nodes

| Domain | Count |
|--------|-------|
| Geopolitical | 12 |
| Economic | 18 |
| Technology | 15 |
| Security | 15 |
| Social/Cultural | 14 |
| Regional | 8 |
| Energy/Climate | 2 |
| **TOTAL** | **102** (some nodes cross domains) |
## 6. Node Definitions: Future Era (2030–2100)

### Design Principles for Future Nodes

1. **Increasing uncertainty**: Probability distributions become wider over time. 2035 nodes have 4-5 branches; 2085 nodes have 5-6 with more even distribution.
2. **Path dependency dominance**: By 2050, world state is mostly determined by 2000–2040 choices.
3. **Conditional gating**: Many future nodes only fire if world-state thresholds are met.
4. **Confidence tags**: All future nodes marked MEDIUM (2030s-2040s) or LOW (2050s+).
5. **Era markers**: Simulation uses structural checkpoints at 2030, 2050, 2070, 2100.

### Era Structure

- **2030s: "The Reckoning"** — Consequences of early-century decisions become undeniable
- **2040s: "The Transformation"** — World becomes unrecognizable from 2000
- **2050s: "The Fork"** — Civilization either stabilizes or enters decline
- **2060s–2080s: "The New World"** — Whatever emerges is radically different
- **2090s: "End State"** — Final world state assessment

---

### 2030s — 39 Nodes

#### Climate (5)
```yaml
# C31: First Major Climate Migration (2031-06)
id: "2031_climate_migration"
conditional: "climate_temp_anomaly > 1.5"
options:
  moderate_managed: 0.30      # 20-50M displaced; framework manages
  large_unmanaged: 0.35       # 50-100M; overwhelms systems
  catastrophic: 0.15          # 100M+; destabilizes receiving countries
  minimal: 0.20               # Adaptation prevents mass displacement
dependencies: [2025_climate_tipping]
key_effects: conflict_deaths, eu_cohesion, food_security_index

# C32: Arctic Ice-Free Summer (2033-09)
id: "2033_arctic_ice_free"
options:
  historical_2033: 0.35       # Ice-free ~2033-2035
  delayed_2045: 0.20
  abrupt_2028: 0.15
  seasonal_only: 0.20
  permanent_loss: 0.10
key_effects: arctic_ice_status, climate_temp_anomaly (albedo feedback)
cascading: gates Arctic governance/shipping nodes

# C33: Simultaneous Breadbasket Failure (2034-08)
id: "2034_food_shock"
conditional: "climate_temp_anomaly > 1.3"
options:
  managed_crisis: 0.30
  regional_famines: 0.30
  global_food_emergency: 0.15
  averted_by_tech: 0.15
  no_simultaneous_failure: 0.10
key_effects: food_security_index, conflict_deaths, global_gdp

# C34: Carbon Capture at Scale (2035-06)
id: "2035_carbon_capture"
options:
  works_at_scale: 0.20
  too_expensive: 0.35
  breakthrough_cheap: 0.10
  energy_penalty: 0.20
  abandoned: 0.15
key_effects: climate_temp_anomaly, renewable_energy_share

# C35: Water Conflict (2036-04)
id: "2036_water_conflict"
conditional: "water_stress_index > 0.40"
options:
  nile_basin_war: 0.20
  indus_crisis: 0.20
  diplomatic_resolution: 0.25
  desalination_prevents: 0.15
  multiple_conflicts: 0.10
  internal_only: 0.10
key_effects: water_stress_index, conflict_deaths, nuclear_risk_level
```

#### AI / Post-Human (6)
```yaml
# A31: Mass AI Job Displacement (2031-03)
id: "2031_ai_displacement"
options:
  managed_transition: 0.20
  social_crisis: 0.30
  new_jobs_emerge: 0.20
  slower_than_expected: 0.15
  bifurcated_economy: 0.15
dependencies: [2028_agi_threshold, 2025_ai_regulation]
key_effects: automation_displacement, inequality_index, us_polarization

# A32: Global AI Governance Framework (2032-06)
id: "2032_ai_governance"
options:
  fragmented_national: 0.30
  international_treaty: 0.15
  corporate_controlled: 0.20
  open_global_commons: 0.10
  authoritarian_advantage: 0.15
  governance_failure: 0.10
dependencies: [2025_ai_regulation, 2028_agi_threshold]
key_effects: ai_development_year_offset, surveillance_state_index, governance_model

# A33: AI Scientific Breakthrough (2033-09)
id: "2033_ai_science"
options:
  drug_discovery: 0.30
  materials_science: 0.25
  physics_breakthrough: 0.10
  incremental_only: 0.25
  fabricated_results: 0.10
key_effects: global_gdp, us_life_expectancy_delta

# A34: Consumer Neural Interface (2035-01)
id: "2035_neural_interface"
options:
  medical_only: 0.35
  elite_early_adopters: 0.25
  mass_market_2040: 0.10
  banned: 0.10
  cognitive_divide: 0.15
  rejected: 0.05
dependencies: [2028_agi_threshold]
key_effects: human_augmentation_prevalence, inequality_index

# A35: AI Consciousness Debate (2037-06)
id: "2037_ai_consciousness"
conditional: "ai_development_year_offset > -3"
options:
  dismissed: 0.30
  unresolved: 0.30
  rights_granted: 0.10
  consciousness_confirmed: 0.05
  moral_panic: 0.15
  irrelevant: 0.10
key_effects: governance_model, global_democracy_index

# A36: Autonomous Weapons Treaty (2038-01)
id: "2038_autonomous_weapons"
options:
  proliferation: 0.35
  partial_ban: 0.25
  comprehensive_ban: 0.10
  arms_race: 0.20
  non_state_actors: 0.10
dependencies: [2004_drone_warfare, 2032_ai_governance]
key_effects: nuclear_risk_level, drone_warfare_prevalence
```

#### Demographics (4)
```yaml
# D31: Japan Population Crisis (2030-01)
id: "2030_japan_population"
options:
  robot_care_economy: 0.30
  immigration_opening: 0.15
  managed_decline: 0.30
  crisis_unmanaged: 0.15
  pronatalist_success: 0.10

# D32: China Demographic Cliff (2032-06)
id: "2032_china_demographics"
options:
  economic_slowdown: 0.35
  automation_compensates: 0.20
  immigration_impossible: 0.15
  military_adventurism: 0.10
  reform_and_adapt: 0.20
dependencies: [2012_xi_consolidation]
key_effects: china_power_index, global_gdp, nuclear_risk_level

# D33: 70% Global Urbanization (2033-01)
id: "2033_urbanization"
options:
  smart_city_success: 0.20
  slum_expansion: 0.30
  urban_heat_crisis: 0.20
  remote_reversal: 0.15
  mega_city_governance: 0.15

# D34: European Demographic Emergency (2035-01)
id: "2035_europe_demographics"
options:
  managed_immigration: 0.25
  fortress_europe: 0.20
  pension_collapse: 0.15
  eu_pronatalist: 0.15
  automation_substitution: 0.25
dependencies: [2022_european_right, 2031_climate_migration]
key_effects: eu_cohesion, europe_federation_index, inequality_index
```

#### Space (3)
```yaml
# SP31: Permanent Lunar Base (2032-06)
id: "2032_moon_base"
options:
  us_china_bases: 0.25
  international_base: 0.15
  us_only: 0.15
  china_only: 0.10
  delayed_2040: 0.25
  abandoned: 0.10
key_effects: space_development_index, us_global_standing, china_power_index

# SP32: Orbital Debris / Kessler Risk (2034-03)
id: "2034_kessler_risk"
options:
  near_miss: 0.35
  partial_cascade: 0.25
  full_kessler: 0.05
  prevented_by_cleanup: 0.20
  no_incident: 0.15
key_effects: space_development_index, global_gdp, supply_chain_resilience

# SP33: Space Mining Economics (2038-01)
id: "2038_space_mining"
options:
  lunar_water_viable: 0.25
  asteroid_mining_works: 0.10
  too_expensive: 0.35
  government_subsidized: 0.20
  revolutionary_cheap: 0.10
key_effects: space_development_index, inequality_index
```

#### Regional (8)
```yaml
# R31: US Political Realignment (2030-11)
id: "2030_us_realignment"
options:
  class_based: 0.25
  urban_rural_permanent: 0.20
  multiparty_emergence: 0.15
  one_party_dominance: 0.10
  continued_polarization: 0.30
dependencies: [2024_us_election, 2031_ai_displacement]
key_effects: us_polarization, us_unity_index

# R32: US State Fracture Risk (2033-06)
id: "2033_us_fracture"
conditional: "us_polarization > 0.65"
options:
  rhetorical_only: 0.35
  selective_nullification: 0.25
  formal_secession: 0.15
  constitutional_convention: 0.15
  resolved_by_reform: 0.10
dependencies: [2030_us_realignment, 2021_jan6]
key_effects: us_unity_index, global_democracy_index

# R33: EU Defense Autonomy (2032-01)
id: "2032_eu_defense"
options:
  nato_strengthened: 0.30
  eu_army: 0.15
  fragmented: 0.20
  us_withdrawal_forces_unity: 0.15
  nuclear_sharing: 0.10
  demilitarized: 0.10
dependencies: [2022_russia_ukraine, 2024_us_election]
key_effects: eu_cohesion, europe_federation_index

# R34: China Post-Xi Transition (2035-01)
id: "2035_china_post_xi"
options:
  hardliner_successor: 0.30
  reform_faction: 0.15
  collective_leadership: 0.20
  instability: 0.15
  xi_continues: 0.10
  democratic_opening: 0.10
dependencies: [2012_xi_consolidation, 2032_china_demographics]
key_effects: china_power_index, china_regime_type

# R35: Middle East Post-Oil (2033-01)
id: "2033_post_oil"
options:
  saudi_succeeds: 0.20
  petrostate_collapse: 0.15
  gradual_managed: 0.30
  oil_renaissance: 0.10
  regional_conflict: 0.15
  green_hydrogen: 0.10
dependencies: [2027_energy_transition, 2017_saudi_transformation]
key_effects: middle_east_stability, middle_east_post_oil

# R36: Israel-Palestine (2034-06)
id: "2034_israel_palestine"
options:
  two_state: 0.10
  one_state_reality: 0.30
  confederation: 0.10
  escalation: 0.20
  status_quo: 0.25
  international_intervention: 0.05
key_effects: middle_east_stability, conflict_deaths

# R37: Arctic Governance (2035-06)
id: "2035_arctic_governance"
conditional: "arctic_ice_status < 0.50"
options:
  cooperative_framework: 0.25
  russian_dominance: 0.20
  resource_rush: 0.25
  militarized: 0.15
  environmental_protection: 0.15
dependencies: [2033_arctic_ice_free, 2022_russia_ukraine]
key_effects: arctic_sovereignty_resolved, nuclear_risk_level

# R38: Northern Sea Route (2036-06)
id: "2036_northern_sea_route"
options:
  russian_controlled: 0.30
  internationalized: 0.20
  too_dangerous: 0.20
  china_russia_corridor: 0.15
  environmental_restrictions: 0.15
dependencies: [2033_arctic_ice_free, 2035_arctic_governance]
key_effects: global_gdp, supply_chain_resilience
```

#### Additional 2030s (13 — cross-domain)
```yaml
# XD31-XD39: Not enumerated above but included in count
# These fill gaps: biotech regulation, space debris governance,
# autonomous vehicle rollout, digital currency adoption,
# global tax reform, antibiotic resistance crisis,
# African Union strengthening, ASEAN integration,
# Latin America pink tide 2.0, polar resource treaties,
# deep sea mining, fusion energy timeline, genetic privacy
# Each follows the standard YAML schema with 3-5 branches
```

**2030s Total: 39 nodes**

---

### 2040s — 28 Nodes

#### Climate (4)
```yaml
# C41: AMOC Collapse (2042-01)
id: "2042_amoc"
conditional: "climate_temp_anomaly > 1.8"
options:
  significant_weakening: 0.30     # 30-50% weaker; European cooling
  full_collapse: 0.10             # Complete shutdown
  stable: 0.30
  temporary_disruption: 0.20
  accelerated_by_greenland: 0.10
key_effects: climate_temp_anomaly, food_security, eu_cohesion

# C42: Climate Refugee Treaty (2044-06)
id: "2044_climate_refugee"
options:
  binding_treaty: 0.15
  regional_agreements: 0.25
  fortress_borders: 0.25
  managed_resettlement: 0.15
  failed_states_absorb: 0.20
dependencies: [2031_climate_migration]

# C43: Geoengineering Decision (2045-01)
id: "2045_geoengineering"
conditional: "climate_temp_anomaly > 2.0"
options:
  deployed_internationally: 0.15
  unilateral: 0.20
  banned: 0.15
  tested_not_deployed: 0.25
  emergency_deployment: 0.15
  governance_deadlock: 0.10
key_effects: climate_temp_anomaly (-0.3 to -0.8 if deployed)

# C44: Amazon Tipping Point (2047-01)
id: "2047_amazon_tipping"
conditional: "climate_temp_anomaly > 1.8"
options:
  partial_dieback: 0.30
  full_dieback: 0.10
  stabilized: 0.25
  managed_transition: 0.20
  accelerated_by_fires: 0.15
key_effects: climate_temp_anomaly (+0.3 if dieback), biodiversity_index
```

#### AI / Post-Human (5)
```yaml
# A41: Superintelligence (2042-01)
id: "2042_superintelligence"
conditional: "ai_development_year_offset > -2"
options:
  gradual_improvement: 0.35
  contained_superintelligence: 0.10
  uncontrolled: 0.05
  theoretical_limits: 0.30
  distributed_intelligence: 0.15
  simulated_only: 0.05
key_effects: existential_risk_cumulative, governance_model

# A42: UBI Global Adoption (2043-01)
id: "2043_ubi"
conditional: "automation_displacement > 0.20"
options:
  widespread: 0.20
  partial: 0.25
  failed: 0.15
  alternative_models: 0.20
  unnecessary: 0.10
  class_warfare: 0.10
key_effects: inequality_index, global_democracy_index

# A43: Cognitive Enhancement (2045-06)
id: "2045_cognitive_enhancement"
options:
  elite_only: 0.30
  democratized: 0.10
  banned: 0.15
  military_first: 0.20
  voluntary: 0.15
  biological_risks: 0.10
dependencies: [2035_neural_interface, 2015_crispr]
key_effects: human_augmentation_prevalence, inequality_index

# A44: Digital Immortality Attempt (2048-01)
id: "2048_digital_immortality"
options:
  technical_failure: 0.40
  philosophical_success: 0.15
  verified_consciousness: 0.05
  partial_upload: 0.20
  abandoned: 0.15
  cultural_phenomenon: 0.05

# A45: AI-Human Hybrid Governance (2049-06)
id: "2049_hybrid_governance"
options:
  advisory_only: 0.30
  algorithmic_policy: 0.20
  ai_decision_maker: 0.05
  rejected: 0.25
  hybrid_model: 0.15
  authoritarian_ai: 0.05
key_effects: governance_model, global_democracy_index
```

#### Space (3)
```yaml
# SP41: Mars Mission (2040-06)
id: "2040_mars_mission"
options:
  successful_landing: 0.20
  one_way_colony: 0.05
  mission_failure: 0.10
  delayed_2050: 0.30
  cancelled: 0.15
  robotic_only: 0.20
dependencies: [2032_moon_base]
key_effects: space_development_index

# SP42: Space Economy $1T (2045-01)
id: "2045_space_economy"
options:
  on_track: 0.25
  slower: 0.30
  explosive: 0.10
  collapsed: 0.15
  military_dominated: 0.20
dependencies: [2038_space_mining, 2034_kessler_risk]

# SP43: Mars Settlement (2048-01)
id: "2048_mars_settlement"
conditional: "space_development_index > 0.3"
options:
  small_outpost: 0.25
  growing_colony: 0.10
  abandoned: 0.15
  corporate_colony: 0.10
  not_yet: 0.30
  independent_governance: 0.10
dependencies: [2040_mars_mission]
```

#### Regional (6)
```yaml
# R41: US Infrastructure Reckoning (2040-01)
id: "2040_us_infrastructure"
options: [massive_rebuild: 0.20, continued_decay: 0.30, climate_adapted: 0.15,
          privatized: 0.15, regional_divergence: 0.20]

# R42: US Constitutional Amendment (2044-06)
id: "2044_us_constitutional"
options: [no_amendment: 0.40, electoral_reform: 0.15, ai_rights: 0.05,
          secession_addressed: 0.10, convention_chaos: 0.10, democratic_reform: 0.20]
dependencies: [2033_us_fracture]

# R43: China Political Trajectory (2042-01)
id: "2042_china_political"
options: [authoritarian_stable: 0.25, gradual_liberalization: 0.15, sudden_transition: 0.10,
          techno_authoritarianism: 0.25, fragmentation: 0.10, hybrid: 0.15]
dependencies: [2035_china_post_xi, 2032_china_demographics]

# R44: EU Federation Decision (2045-01)
id: "2045_eu_federation"
options: [full_federation: 0.10, enhanced_cooperation: 0.25, two_speed: 0.25,
          dissolution: 0.10, status_quo: 0.20, defense_federation: 0.10]
dependencies: [2032_eu_defense, 2035_europe_demographics]

# R45: Middle East New Economy (2045-01)
id: "2045_me_new_economy"
options: [hydrogen_economy: 0.15, tourism_tech: 0.20, collapse: 0.15,
          renewed_conflict: 0.15, diaspora_driven: 0.15, foreign_dependency: 0.20]
dependencies: [2033_post_oil]

# R46: Arctic Extraction (2045-01)
id: "2045_arctic_extraction"
options: [regulated: 0.25, unregulated_rush: 0.20, protected: 0.15,
          russian_monopoly: 0.15, tech_unnecessary: 0.15, indigenous_sovereignty: 0.10]
dependencies: [2035_arctic_governance]
```

#### Additional 2040s (10 — cross-domain)
```yaml
# Fills: ocean acidification verdict, antibiotic resistance crisis,
# global education transformation, synthetic biology regulation,
# space law framework, digital nation-states, currency evolution,
# great power arms control, African continental free trade results,
# Latin America integration
```

**2040s Total: 28 nodes**

---

### 2050s — 18 Nodes

```yaml
# 2°C Threshold (2050), Sea Level 0.5m (2052), Biodiversity (2055)
# Post-Scarcity Potential (2050), AI Existential Risk Event (2053)
# Human-AI Integration (2055), Mars Self-Sufficiency (2055)
# Asteroid Deflection (2052), Population Peak (2055)
# Life Extension (2058), Nuclear Status (2055)
# US Restructuring (2050), China Status (2050), Europe 2050
# Middle East 2050, Arctic Mature, India 2050, Africa 2050

# Each follows standard schema with 4-6 branches
# All marked confidence: LOW
# Heavy conditional gating based on accumulated world state
```

**2050s Total: 18 nodes**

---

### 2060s — 16 Nodes

```yaml
# Climate Verdict (2065), Ocean Ecosystem (2068)
# Post-Human Divergence (2065), Digital Civilization (2068)
# Multi-Planetary Status (2065), Interstellar Probe (2068)
# Population Decline (2065), New World Order (2060)
# Autonomous War (2062), Bioweapon Risk (2065)
# Global Culture (2065), US at 2065, China at 2065
# Europe at 2065, Middle East at 2065, Arctic at 2065
```

**2060s Total: 16 nodes**

---

### 2070s–2080s — 16 Nodes

```yaml
# Climate Equilibrium (2075), AI Maturity (2075)
# Solar System Civilization (2075), Population (2075)
# Global Governance (2075), US Status (2075)
# Last Great Power War? (2078), Arctic Settled (2075)
# Climate Recovery (2085), Human Identity (2085)
# Interstellar (2085), Demographics New Normal (2085)
# World System (2085), Existential Risk Assessment (2085)
# Economic Model (2085), Middle East (2085)
```

**2070s-2080s Total: 16 nodes**

---

### 2090s — 10 Nodes

```yaml
# Final Climate State (2095), AI-Human Relationship (2095)
# Space Status (2095), Population Final (2095)
# Governance Final (2095), US at 2100 (2095)
# China at 2100 (2095), Europe at 2100 (2095)
# Civilization Verdict (2095)

# 2099 Verdict — COMPUTED NODE (not sampled)
id: "2099_verdict"
computed_from: "all world state dimensions"
categories:
  GOLDEN_AGE: composite > 0.7
  PROGRESS: 0.3 < composite <= 0.7
  MUDDLING_THROUGH: -0.1 < composite <= 0.3
  DECLINE: -0.5 < composite <= -0.1
  CATASTROPHE: -0.8 < composite <= -0.5
  EXTINCTION: composite <= -0.8
  TRANSCENDENCE: post-human markers triggered
```

**2090s Total: 10 nodes**

---

### Future Era Total: 127 Nodes

| Decade | Nodes |
|--------|-------|
| 2030s | 39 |
| 2040s | 28 |
| 2050s | 18 |
| 2060s | 16 |
| 2070s-80s | 16 |
| 2090s | 10 |
| **TOTAL** | **127** |

### Grand Total: 229 Nodes
## 7. CLI Experience Design

### Display Modes

#### Cinema Mode (`--cinema`, default)

The flagship experience. Events appear with timing proportional to real time gaps, compressed by a speed multiplier.

**Pacing:**
```python
def compute_delay(current, next_event, speed):
    real_gap_months = months_between(current.year_month, next_event.year_month)
    display_gap = (real_gap_months * 30 * 24 * 60) / speed
    return clamp(display_gap, 0.05, 3.0)
```

**Speed presets:**
| Preset | Multiplier | Century Duration |
|--------|-----------|-----------------|
| `--speed ultra` | 1200 | ~75 seconds |
| `--speed fast` | 600 | ~2.5 minutes (default) |
| `--speed normal` | 300 | ~5 minutes |
| `--speed slow` | 120 | ~12 minutes |

**Visual layout:**

```
╔══════════════════════════════════════════════════════════════╗
║           THE 21st CENTURY  ·  SEED 7714                    ║
╚══════════════════════════════════════════════════════════════╝

                    ╔══ THE RECKONING ══╗
                    ║    2000 – 2030    ║
                    ╚═══════════════════╝

                        ── 2000 ──

 NOV  US Presidential Election
      Gore wins Florida by 2,211 votes                    DIVERGENCE
      ↳ Full recount completes; Gore wins by ~2,000 votes

                        ── 2001 ──

 SEP  September 11 Attacks
      Plot disrupted by FBI                               DIVERGENCE
      ↳ Phoenix memo acted on; two cells arrested in August

 DEC  China WTO Accession
      Full accession with minimal conditions              ─ historical ─
```

**Elements:** Year headers centered with em dashes. Month left-aligned in caps. Event title bold/bright. Status tag right-aligned (DIVERGENCE=yellow, HISTORICAL=dim, ESCALATED=red, PREVENTED=green). Narration line with `↳` in dim italic, only for divergences.

**Era transitions:** 2-second pause, banner animation, world state snapshot:

```
                    ╔══ THE TRANSFORMATION ══╗
                    ║      2030 – 2050       ║
                    ╚════════════════════════╝

    ┌─────────────── World State at 2030 ───────────────┐
    │  Climate          +1.2°C          ▲ better         │
    │  US Polarization  0.38   ░░▓░░░░  ▲ much better    │
    │  Conflict Deaths  45K             ▲ much better    │
    │  Nuclear Risk     0.08   ▓░░░░░░  ▲ much better    │
    │  Running score: +0.52  ████████████░░░░░░░░░░      │
    └────────────────────────────────────────────────────┘
```

#### Sprint Mode (`--sprint`)

Full century in ~10 seconds. One-line-per-decade summaries:

```
SEED 7714 · "The Near-Miss Century"
2000s  Gore wins ∙ 9/11 disrupted ∙ No Iraq ∙ FDA blocks opioids
2010s  Arab Spring succeeds ∙ No Crimea ∙ Remain wins ∙ Clinton wins
2020s  COVID contained ∙ No Ukraine war ∙ AI accelerates
2030s  80M climate displaced ∙ Mars mission ∙ AMOC weakening
...
VERDICT: PROGRESS (+0.45) ∙ 147 divergences ∙ 65th percentile
```

#### Decade Mode (`--interactive`)

Same as cinema but pauses at era boundaries with interactive prompt:

```
[Enter] Continue  [s] Full state  [w] Why?  [r] Replay decade  [q] Quit
```

**`[w] Why?`** traces causal chains:
```
Why is US Polarization so low (0.38)?
↳ Gore wins (2000) → No Iraq → Lower anti-establishment sentiment
  → Milder financial crisis backlash → Clinton wins 2016
    → No Jan 6 → Cumulative: 0.38 vs historical 0.78
```

#### Research Mode (`--research`)

Shows probability tables, modifications, random draws, and downstream effects for every node.

### Detail Levels (orthogonal to display mode)

```
--detail minimal     One line per node
--detail standard    Event + status + narration (default)
--detail full        + world state deltas
--detail research    + probability tables, modifications, draws
```

### Special Visual Moments

**Nuclear event:**
```
 FEB  Russia-Ukraine War
      Tactical nuclear weapon deployed                    ██ NUCLEAR ██
      ┌───────────────────────────────────────────────┐
      │  ☢  NUCLEAR WEAPONS USED IN CONFLICT  ☢      │
      │  First use since 1945.                        │
      │  Nuclear risk: 0.35 → 0.75                    │
      └───────────────────────────────────────────────┘
```

**Extinction (early termination):**
```
        ╔══════════════════════════════════════════════╗
        ║         CIVILIZATION COLLAPSE                ║
        ║   Year: 2067 | Population: ~800M            ║
        ║   Recovery probability: LOW                  ║
        ║   Verdict: CATASTROPHE                       ║
        ╚══════════════════════════════════════════════╝
```

**Transcendence:**
```
        ╔══════════════════════════════════════════════╗
        ║         T R A N S C E N D E N C E            ║
        ║   Humanity has merged with its AI creations  ║
        ║   Year: 2084 | Status: Post-human            ║
        ╚══════════════════════════════════════════════╝
```

### Final Summary Screen

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    FINAL WORLD STATE: 2100
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        This Run    Historical   Delta
  Climate              +2.4°C        +2.5°C       ▲ better
  Population           7.8B          ~8.5B        ↘ post-peak
  Conflict Deaths      1.2M          ~2M          ▲ less
  Nuclear Risk         0.05          0.35         ▲ much safer
  Democracy Index      0.68          0.55         ▲ better
  AI Status            Symbiotic     —            ● new
  Space                Multi-planet  —            ● new

  Century Verdict:     P R O G R E S S
  Composite Score:     +0.45 ████████████████░░░░░░░░░░░░░░
  Percentile:          65th
  Divergences:         147 of 229
  First Divergence:    2000-11 (US Election)
  Largest Divergence:  2003-03 (Iraq War)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Batch Mode

```
$ 21csim batch --iterations 10000

Century Verdicts:
  GOLDEN AGE        0.4%  ▏
  PROGRESS         31.2%  ██████████████
  MUDDLING THROUGH 28.1%  ████████████
  DECLINE          24.8%  ███████████
  CATASTROPHE      13.2%  █████
  EXTINCTION        0.5%  ▏
  TRANSCENDENCE     1.8%  ▏

Highest-leverage nodes:
  1. Iraq War Decision           r² = 0.28
  2. 2000 US Election            r² = 0.22
  3. COVID-19 Response           r² = 0.17
  4. AI Governance (2032)        r² = 0.14
  5. Russia-Ukraine              r² = 0.11
```

### Terminal Adaptation

- **≥100 cols:** Full layout with boxes
- **80-99 cols:** Compact (shorter descriptions, no box drawing)
- **<80 cols:** Minimal (one-line events)

### Color Scheme

| Element | Color |
|---------|-------|
| Year headers | bold white |
| Event title | bold white |
| HISTORICAL | dim |
| DIVERGENCE | yellow |
| ESCALATED | red |
| PREVENTED | green |
| Narration (↳) | dim italic |
| Better than historical | green |
| Worse than historical | red |

### CLI Command Reference

```
21csim run [OPTIONS]
  --seed INT              RNG seed
  --cinema/--sprint/--interactive  Display mode
  --speed PRESET          ultra|fast|normal|slow
  --detail LEVEL          minimal|standard|full|research
  --divergences-only      Only show divergences
  --domain DOMAIN         Filter by domain
  --era ERA               Filter by era
  --no-pause              Skip era pauses
  --sound on|off          Audio cues (default: off)
  --format FMT            terminal|json|md|csv

21csim batch --iterations INT --output PATH --parallel INT

21csim diff SEED_A SEED_B --highlight-critical

21csim sensitivity --node ID --metric METRIC --iterations INT

21csim explore --node ID | --chain NODE --branch B | --why DIM

21csim what-if --set NODE=BRANCH [repeatable] --iterations INT

21csim export-library --seeds curated --count 200 --output DIR
```

---

## 8. Sound Engine

### Architecture

Runtime-synthesized audio using numpy. No bundled files. Zero overhead when disabled. Plays asynchronously via system audio player (`afplay` macOS, `paplay`/`aplay` Linux).

### Tone Inventory (8 cues)

| Cue | Frequencies | Duration | Envelope | Character |
|-----|------------|----------|----------|-----------|
| `era_transition` | 110 + 165 Hz (open fifth A2+E3) | 1.2s | Quick attack, long decay | Hollow bell, like time passing |
| `nuclear` | 55 + 58 Hz (3 Hz beat) | 1.5s | Slow swell, abrupt cut | Subsonic throb you feel more than hear |
| `extinction` | 220 + 277 + 330 Hz (A minor) | 2.5s | Sustain then fade to silence | Lights going out |
| `transcendence` | 220→660 Hz (harmonic stack) | 2.0s | Sequential fade-in, rising | Chord building upward, ascent |
| `verdict_good` | 262 + 330 + 392 Hz (C major) | 1.0s | Gentle | Resolution, arriving somewhere good |
| `verdict_bad` | 233 + 277 + 349 Hz (Bb minor) | 1.0s | Gentle | Door closing, somber |
| `verdict_neutral` | 262 + 349 Hz (sus4) | 1.0s | Gentle | Unresolved, hanging in air |
| `divergence_major` | 440 Hz (A4) | 0.15s | Pluck (instant attack, fast decay) | Sonar ping, "something changed" |

### Implementation

```python
class SoundEngine:
    def __init__(self, enabled: bool = False):
        # Detect system player, generate all tones at startup (~50ms)
        # If no player found, silently disable

    def play(self, cue_name: str) -> None:
        # Fire-and-forget in daemon thread
        # Never blocks display, never crashes on failure

    def shutdown(self) -> None:
        # Clean up temp WAV files (also registered with atexit)
```

**Synthesis:** `numpy.sin()` → amplitude envelope → 16-bit PCM → WAV file → system player.

**`divergence_major` threshold:** Only fires when sum of absolute world state deltas > 0.10. Roughly 15-25 pings per century, not 150.

### Web Audio Port

Same tones implemented via Web Audio API `OscillatorNode` + `GainNode` for the web viewer. Better control (real-time synthesis, precise timing, no temp files).

---

## 9. Web Viewer and Public Launch

### Architecture

**Static site with pre-generated runs.** No server, no API.

Python CLI exports curated runs as JSON. React app loads and plays them back with animations, timeline, world-state dashboard, and Web Audio sound.

### Pre-Generation

```bash
21csim export-library --seeds curated --count 200 --output web/public/runs/
```

Curated seed selection: run 100K iterations, select 200 seeds representing all verdict categories, notable causal chains, extreme outliers, and diverse world states. Library is ~50MB of JSON.

### Web Viewer Components

- **CenturyViewer** — Main container; manages playback state
- **Timeline** — Horizontal scrubber with dots for events (yellow=divergence, dim=historical)
- **EventsPanel** — Scrolling event list with cinema mode rendering
- **WorldStatePanel** — Live-updating bars for key dimensions
- **EraTransition** — Full-screen overlay animation at era boundaries
- **SpecialMoments** — Nuclear flash, extinction fade, transcendence glow
- **RunSelector** — Browse/filter the 200 pre-generated runs
- **FinalSummary** — End-of-century summary with all dimensions
- **SpeedControl** — Play/pause/speed controls + keyboard shortcuts
- **SoundEngine** — Web Audio API tone synthesis

### Interactions

- **Timeline scrubber:** Click/drag to jump to any year
- **Speed controls:** ▶ ⏸ ⏩ | Space=pause, →=next, ←=prev, ↑↓=speed
- **Sound toggle:** 🔊/🔇
- **Event click:** Expand to show probability distribution and downstream effects
- **World state bars:** Animate smoothly; color-shift green→yellow→red

### Shareable URLs

Each run: `yoursite.com/21csim/century/7714`

Open Graph social card per seed:
```
THE 21st CENTURY · Seed 7714
"The Near-Miss Century: Climate Crisis Barely Averted"
Verdict: PROGRESS · 65th percentile
147 divergences. Watch it unfold →
```

### Site Structure

```
yoursite.com/21csim/              # Landing page / viewer
yoursite.com/21csim/century/SEED  # Specific run permalink
yoursite.com/21csim/explore       # Run browser
yoursite.com/21csim/findings      # Batch analysis dashboard
yoursite.com/blog/21csim-launch   # Launch blog post
```

### Tech Stack

```
Framework:  Astro or Next.js (static export)
Viewer:     React + TypeScript
Styling:    Tailwind CSS
Charts:     Recharts or D3
Sound:      Web Audio API
Hosting:    Netlify or Cloudflare Pages (free tier)
```

### Launch Blog Post

**Title:** "I Built a Monte Carlo Simulator for the 21st Century. Here's What 10,000 Alternate Histories Reveal."

**Sections:**
1. The Hook — describe watching a specific seed unfold
2. What Is This? — concept explanation
3. How It Works — walk through one node (Iraq War Decision)
4. What 10,000 Centuries Tell Us — batch findings, leverage rankings
5. The Most Interesting Seeds — 4-5 showcases with viewer screenshots
6. Methodology and Limitations — honest about what this is and isn't
7. Try It Yourself — links to viewer and GitHub

**Key finding to lead with:** The Iraq War Decision has r² = 0.28 with the entire century's composite score. No single decision matters more.

### Open Source (GitHub: north-echo/21csim)

- MIT license
- Node contribution model: anyone can propose nodes or calibrate probabilities via YAML PRs
- METHODOLOGY.md explaining calibration approach and sources
- CONTRIBUTING.md with node submission guidelines

---

## 10. Implementation Phasing

### Phase 1: CLI MVP (Weeks 1-3)

- Project scaffolding (pyproject.toml, directory structure)
- Data models and WorldState
- Graph construction from YAML
- Simulation engine (core loop, sampling, effect application)
- 32 base marquee nodes only
- Cinema mode renderer (Rich)
- Sprint mode
- Batch mode with basic statistics
- Sound engine
- `--format json` export
- Tests: determinism, boundary, conditional gating

### Phase 2: Full Node Library (Weeks 3-5)

- All 229 nodes in YAML
- Full conditional gating system
- Probability redistribution (renormalization)
- Sensitivity analysis
- What-if mode
- Explore / chain / why commands
- Headline generation
- Era transition rendering
- Special moments (nuclear, extinction, transcendence)
- Comprehensive testing and calibration

### Phase 3: Web Viewer (Weeks 5-8)

- React viewer with timeline, events panel, world state dashboard
- Web Audio sound engine
- Pre-generate 200 curated runs
- Run selector / browser
- Permalink system with social cards
- Mobile responsive
- Static site build + hosting setup

### Phase 4: Blog + Launch (Weeks 8-9)

- Write and publish launch blog post
- Generate batch analysis results and visualizations
- Social media assets and push
- Submit to Hacker News, Reddit, relevant communities

### Phase 5: Community (Ongoing)

- Node contribution pipeline
- Probability calibration discussions
- New scenario files (other historical periods, personal decision-making)
- Community features and enhancements

---

## 11. Testing and Calibration

### Test Categories

**Determinism:** Same seed → same full timeline, every time.

**Historical baseline:** All nodes forced to HISTORICAL branch → WorldState ≈ actual 2030 conditions. This is the most important calibration test.

**Conditional gating:** COVID response skipped when no pandemic. Jan 6 skipped when Trump wins 2020. Future nodes correctly gated by world state thresholds.

**Probability redistribution:** Extreme upstream modifiers don't create invalid distributions (p < 0 or p > 1). All branches always sum to 1.0.

**Boundary cases:** All-prevented run (everything goes right). All-escalated run (everything goes wrong). Single-divergence runs (one change, everything else historical).

**Performance:** Single run < 50ms. 10,000 runs < 60 seconds. 100,000 runs < 10 minutes.

**Sound:** Disabled engine is true no-op. Enabled engine detects player. Playback doesn't block. Temp files cleaned up.

### Calibration Paths

**Path 1 — "The Best Century":**
Gore → 9/11 prevented → No Iraq → Mild recession → Coordinated COVID → Climate treaty → AI governed → Mars colony → GOLDEN AGE (~0.1% of runs)

**Path 2 — "Our Century" (baseline):**
All historical → World state ≈ actual → MUDDLING THROUGH

**Path 3 — "The Worst Century":**
Contested 2000 → Worse 9/11 → Iraq + financial collapse → Fragmented COVID → Ukraine nuclear → Climate runaway → CATASTROPHE (~2-3%)

**Path 4 — "Extinction":**
Nuclear exchange + climate runaway + AI catastrophe → EXTINCTION (<0.1%)

**Path 5 — "Transcendence":**
AI breakthrough → Contained superintelligence → Human-AI merge → Multi-planetary → TRANSCENDENCE (<0.5%)

### Key Validation Metrics

- Iraq War Decision should show highest r² with composite (~0.25-0.30)
- 2000 Election should show second highest (~0.20-0.25)
- MUDDLING THROUGH should be most common outcome (~25-30%)
- EXTINCTION should be <1%
- GOLDEN AGE should be <2%
- Median composite should be slightly negative (reality has some structural risks)
