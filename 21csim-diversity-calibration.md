# 21csim — Outcome Diversity Calibration

## Addendum to Complete Spec v2.0

---

## Problem Statement

In batch runs of 10,000 iterations, outcomes should span the full possibility space — every verdict category should appear, and runs within the same category should feel distinct from each other. The current node graph produces outcomes that cluster too tightly around a few dominant paths.

This document contains five calibration patches that, applied together, should produce meaningfully diverse outcomes.

---

## Patch 1: Break the Gore Cascade Monopoly

### Problem

The 2000 election → Iraq chain is so heavily weighted that it dominates total outcome variance. Gore winning shifts Iraq probability by -0.40, which is enormous — it makes "no invasion" the overwhelming favorite when Gore wins. This means ~45% of all runs follow the "Gore → No Iraq → Better World" path and look very similar to each other.

### Fix: Add Noise and Counter-Pressures

The real world is messier than "Gore wins → no Iraq." Even under Gore, there were hawks in the Democratic Party. The intelligence failures were bipartisan. 9/11 (in timelines where it still happens partially) would have created enormous pressure for action even under Gore.

```yaml
# MODIFIED: 2003_iraq node

# Old dependencies (too deterministic):
#   2000_election.gore_wins → full_invasion: -0.40
#   2001_911.plot_disrupted → full_invasion: -0.35

# New dependencies (more nuance):
dependencies:
  - node: "2000_election"
    branch: "gore_wins"
    modifies:
      full_invasion: "-0.25"          # Was -0.40 — still strong but not overwhelming
      limited_strikes: "+0.10"        # Gore might still strike; hawks in Dem party
      diplomatic_resolution: "+0.12"
      delayed_invasion: "+0.03"       # Coalition-building takes time
  
  - node: "2001_911"
    branch: "plot_disrupted"
    modifies:
      full_invasion: "-0.20"          # Was -0.35 — less war pressure but not zero
      diplomatic_resolution: "+0.15"
      limited_strikes: "+0.05"
  
  - node: "2001_911"
    branch: "partial_success"
    modifies:
      full_invasion: "+0.08"          # NEW — even partial 9/11 increases war pressure
      limited_strikes: "+0.05"
  
  - node: "2001_911"
    branch: "worse_outcome"
    modifies:
      full_invasion: "+0.20"          # Was +0.30 — still high but leaves room for variation
  
  # NEW DEPENDENCY: China WTO creates economic entanglement that
  # makes unilateral action costlier
  - node: "2001_china_wto"
    branch: "conditional_accession"
    modifies:
      diplomatic_resolution: "+0.05"  # Multilateral norm-building transfers

# Effect: Gore winning now makes Iraq less likely but not impossible.
# In ~25% of Gore timelines, limited strikes or delayed invasion still happen.
# This creates meaningful variation within the "Gore world" cluster.
```

### Add Counter-Cascades

Even in "no Iraq" timelines, other things go wrong. Without Iraq draining attention, what does the US do? Possibly overreach elsewhere.

```yaml
# NEW NODE: Post-9/11 Security Overreach (2002-06)
id: "2002_security_overreach"
year_month: "2002-06"
title: "Post-9/11 Security Architecture"
description: >
  Even without a full Iraq invasion, 9/11 (or its partial equivalent)
  triggers a massive security state expansion. Patriot Act, DHS creation,
  TSA, warrantless wiretapping. The question is how far it goes.
domain: "security"
variable: "security_expansion"
distribution:
  type: "categorical"
  options:
    historical_expansion: 0.40      # Full Patriot Act, DHS, surveillance
    moderate_expansion: 0.30        # Some measures but with sunset clauses
    aggressive_overreach: 0.10      # Worse than historical — internment discussions
    restrained_response: 0.20       # Civil liberties prioritized
dependencies:
  - node: "2001_911"
    branch: "historical_full"
    modifies:
      historical_expansion: "+0.15"
      aggressive_overreach: "+0.10"
      restrained_response: "-0.15"
  - node: "2001_911"
    branch: "plot_disrupted"
    modifies:
      restrained_response: "+0.20"
      historical_expansion: "-0.15"
  - node: "2000_election"
    branch: "gore_wins"
    modifies:
      moderate_expansion: "+0.10"
      aggressive_overreach: "-0.08"
outcomes:
  historical_expansion:
    status: "HISTORICAL"
    world_state_effects:
      surveillance_state_index: "+0.15"
      us_polarization: "+0.03"
      internet_freedom_index: "-0.08"
  moderate_expansion:
    status: "DIVERGENCE"
    world_state_effects:
      surveillance_state_index: "+0.08"
  aggressive_overreach:
    status: "ESCALATED"
    world_state_effects:
      surveillance_state_index: "+0.25"
      us_polarization: "+0.08"
      global_democracy_index: "-0.03"
      us_institutional_trust: "-0.05"
    cascading_modifiers:
      2013_snowden.historical_leak: "+0.10"  # More to leak
      2016_us_election.anti_establishment: "+0.05"
  restrained_response:
    status: "DIVERGENCE"
    world_state_effects:
      surveillance_state_index: "+0.03"
      internet_freedom_index: "-0.02"
      us_institutional_trust: "+0.03"
```

This means even "Gore + no Iraq" timelines can still produce high surveillance, polarization from security overreach, and Snowden-like blowback. The "better world" path requires multiple things going right, not just one election.

---

## Patch 2: Strengthen Cross-Domain Cascades

### Problem

Most cascading modifiers stay within domain (geopolitical → geopolitical). The real world has more surprising cross-domain effects.

### Fix: Add 30+ New Cross-Domain Modifiers

```yaml
# ── Technology → Climate ──

# Fukushima → Climate trajectory (already exists but strengthen)
2011_fukushima.no_tsunami_hit:
  2025_climate_tipping.accelerated_action: "+0.08"    # Nuclear stays; lower emissions
  2027_energy_transition.nuclear_renaissance: "+0.15"  # Strengthen existing

# AI acceleration → Climate (faster AI enables better climate modeling/solutions)
2023_ai_acceleration.historical_rapid:
  2025_climate_tipping.technological_breakthrough: "+0.05"
  2035_carbon_capture.breakthrough_cheap: "+0.08"

2023_ai_acceleration.ai_winter:
  2035_carbon_capture.too_expensive: "+0.10"          # No AI to optimize capture
  2025_climate_tipping.accelerated_action: "-0.05"

# ── Economic → Social ──

# Financial crisis severity → Opioid epidemic (economic despair)
2008_financial_crisis.great_depression_2:
  2003_opioid_crisis.historical_epidemic: "+0.05"     # Despair accelerates addiction
  2014_deaths_of_despair.continues_worsening: "+0.10"

2008_financial_crisis.mild_recession:
  2014_deaths_of_despair.reversal_by_2025: "+0.10"

# ZIRP → Tech culture → Social media toxicity
2012_zirp.historical_extended_zirp:
  2018_facebook_cambridge.nothing_changes: "+0.05"    # No financial pressure for reform
  2019_unicorn_bubble.bubble_continues: "+0.05"

# ── Security → Technology ──

# Cyber attacks → AI regulation (security incidents drive AI governance)
2017_wannacry.major_infrastructure_attack:
  2025_ai_regulation.heavy_regulation: "+0.10"
  2032_ai_governance.international_treaty: "+0.08"

# Drone proliferation → Autonomous weapons trajectory
2004_drone_warfare.proliferation:
  2038_autonomous_weapons.proliferation: "+0.15"
  2038_autonomous_weapons.comprehensive_ban: "-0.08"

# ── Climate → Geopolitical ──

# Climate migration → European politics (already exists but add more paths)
2031_climate_migration.catastrophic:
  2035_europe_demographics.fortress_europe: "+0.15"
  2045_eu_federation.dissolution_begins: "+0.08"
  2030_us_realignment.continued_polarization: "+0.05"

# Food shock → Everything (food insecurity is the great destabilizer)
2034_food_shock.global_food_emergency:
  2036_water_conflict.multiple_conflicts: "+0.15"
  2033_post_oil.regional_conflict: "+0.10"
  2035_china_post_xi.instability: "+0.08"
  2034_israel_palestine.escalation: "+0.10"

# ── Social → Geopolitical ──

# Misinformation → Everything political (strengthen existing)
2016_misinformation.epistemic_collapse:
  2020_us_election.close_contested: "+0.10"
  2021_jan6.worse_violence: "+0.10"
  2024_us_election.contested: "+0.08"
  2030_us_realignment.continued_polarization: "+0.15"
  2033_us_fracture.formal_secession: "+0.08"
  2020_covid_response.catastrophic_failure: "+0.10"   # Can't coordinate if no shared reality

# BLM outcomes → Political trajectory
2014_blm.backlash_dominant:
  2016_us_election.trump_wins: "+0.05"
  2024_us_election.trump_wins: "+0.03"
  2030_us_realignment.continued_polarization: "+0.05"

2014_blm.sustained_reform:
  2030_us_realignment.class_based: "+0.05"            # Race resolved → class becomes axis

# ── Space → Everything ──

# Mars mission success → Existential risk awareness → Climate action
2040_mars_mission.successful_landing:
  2045_geoengineering.deployed_internationally: "+0.05"  # "We can do hard things"
  2042_superintelligence.contained_superintelligence: "+0.03"

# Kessler syndrome → Supply chain, GPS, military
2034_kessler_risk.full_kessler:
  2038_autonomous_weapons.arms_race: "-0.10"          # Can't do space-based weapons
  2026_taiwan_strait.tension_no_conflict: "+0.05"     # Everyone loses satellite capability
  2045_space_economy.collapsed: "+0.20"

# ── Demographics → Economics ──

# China demographic cliff → Taiwan risk (adventurism)
2032_china_demographics.military_adventurism:
  2026_taiwan_strait.full_invasion: "+0.10"
  2026_taiwan_strait.blockade: "+0.08"

# European demographics → EU federation pressure
2035_europe_demographics.pension_collapse:
  2045_eu_federation.dissolution_begins: "+0.10"
  2022_european_right.governing_majority: "+0.05"

2035_europe_demographics.managed_immigration:
  2045_eu_federation.enhanced_cooperation: "+0.08"
```

---

## Patch 3: Flatten Peaked Distributions

### Problem

Too many nodes have one branch at 0.45-0.55. In batch runs, this means the "most likely" branch fires ~50% of the time, creating large clusters of similar outcomes.

### Fix: Redistribute to Flatter Distributions

Rule: No single branch should exceed 0.40 on a node with 4+ branches, and no branch should exceed 0.45 on a node with 3 branches. This ensures that even without any upstream modifiers, every branch has a meaningful chance of firing.

```yaml
# Nodes that need flattening (original → new):

2001_911:
  # Old: historical_full: 0.35, partial: 0.30, single: 0.15, disrupted: 0.12, worse: 0.08
  # New:
  historical_full: 0.28
  partial_success: 0.27
  single_attack: 0.18
  plot_disrupted: 0.17
  worse_outcome: 0.10

2003_iraq:
  # Old: full: 0.55, limited: 0.20, diplomatic: 0.15, delayed: 0.10
  # New:
  full_invasion: 0.38
  limited_strikes: 0.22
  diplomatic_resolution: 0.22
  delayed_invasion: 0.18

2008_financial_crisis:
  # Old: severe: 0.45, contained: 0.20, depression: 0.15, mild: 0.20
  # New:
  historical_severe: 0.32
  contained_early: 0.25
  great_depression_2: 0.18
  mild_recession: 0.25

2016_us_election:
  # Old: trump: 0.48, clinton: 0.42, third: 0.05, contested: 0.05
  # New:
  trump_wins: 0.38
  clinton_wins: 0.38
  third_party_surge: 0.12
  contested_result: 0.12

2022_russia_ukraine:
  # Old: stalemate: 0.35, no_invasion: 0.20, quick_russian: 0.10,
  #      nato: 0.05, quick_ukrainian: 0.10, nuclear: 0.03, frozen: 0.17
  # New:
  historical_invasion_stalemate: 0.25
  no_invasion: 0.22
  quick_russian_victory: 0.10
  nato_direct_involvement: 0.05
  quick_ukrainian_victory: 0.12
  nuclear_use: 0.06         # Doubled — was too low for diversity
  frozen_conflict: 0.20

2023_ai_acceleration:
  # Old: rapid: 0.40, slower: 0.20, faster: 0.10, open: 0.15, winter: 0.05, china: 0.10
  # New:
  historical_rapid: 0.28
  slower_progress: 0.22
  faster_agi: 0.12
  open_source_dominant: 0.18
  ai_winter: 0.08
  china_leads: 0.12
```

**Impact:** With flatter distributions, the "most common" path becomes less common. Instead of one dominant cluster, you get a more even spread across outcome classes.

---

## Patch 4: Add "Good World" Future Nodes

### Problem

Many future nodes only fire when things go badly (conditional on high temperature, high risk, etc.). "Good" timelines have sparse future eras because there's nothing to happen. The optimistic future needs its own interesting events.

### Fix: Add Conditional Nodes for Positive Trajectories

```yaml
# NEW: Fires when climate action succeeds early
id: "2033_green_economy_boom"
year_month: "2033-06"
title: "Green Industrial Revolution"
conditional: "renewable_energy_share > 0.25 AND climate_temp_anomaly < 1.5"
description: >
  When clean energy wins early, the economic transformation creates a
  boom — new industries, new jobs, new geopolitical winners and losers.
  But even good transitions create losers.
options:
  broad_prosperity: 0.30            # Green growth lifts all boats
  petro_state_collapse: 0.25        # Oil states crash; regional instability
  green_inequality: 0.25            # Clean energy billionaires; new oligarchy
  nationalist_backlash: 0.20        # Transition too fast; populist revolt
key_effects: inequality_index, middle_east_post_oil, global_gdp

# NEW: Fires when AI governance works
id: "2036_ai_abundance"
year_month: "2036-06"
title: "AI-Driven Abundance"
conditional: "ai_development_year_offset > 0 AND governance_model > 0.4"
description: >
  When AI develops fast AND governance works, abundance follows —
  but abundance creates its own problems.
options:
  meaning_crisis: 0.30              # Material abundance, spiritual emptiness
  creative_renaissance: 0.25        # Free from toil, humans create
  concentration_of_power: 0.25      # AI owners become de facto rulers
  equitable_distribution: 0.20      # Benefits broadly shared
key_effects: inequality_index, automation_displacement, global_democracy_index

# NEW: Fires when US avoids fracture
id: "2035_us_renewal"
year_month: "2035-01"
title: "American Renewal"
conditional: "us_polarization < 0.50 AND us_unity_index > 0.55"
description: >
  In timelines where the US avoids the worst polarization, a national
  renewal is possible — but what form does it take?
options:
  infrastructure_renaissance: 0.30  # Massive rebuilding, national purpose
  tech_leader_consolidation: 0.25   # US cements AI/space dominance
  social_compact_2: 0.20            # New social contract, reduced inequality
  complacency: 0.25                 # Avoided the worst, but drifts
key_effects: us_unity_index, us_global_standing, inequality_index

# NEW: Fires when no major wars happen
id: "2040_peace_dividend"
year_month: "2040-01"
title: "The Peace Dividend"
conditional: "conflict_deaths < 100000 AND nuclear_risk_level < 0.10"
description: >
  A world without Iraq, without Ukraine, without major conflict
  has trillions of dollars and millions of lives to spend on
  something else. But peace is also boring, and bored great
  powers find new competitions.
options:
  space_race_2: 0.25                # Competition redirected to space
  development_boom: 0.25            # Investment in Global South
  technology_race: 0.20             # AI/biotech/quantum competition
  complacent_decline: 0.15          # No external threat, internal rot
  new_cold_war: 0.15                # Economic competition escalates
key_effects: space_development_index, global_gdp, africa_development_index

# NEW: Fires when democracy strengthens
id: "2038_democratic_renaissance"
year_month: "2038-06"
title: "Democratic Innovation"
conditional: "global_democracy_index > 0.65 AND misinformation_severity < 0.15"
description: >
  When misinformation is contained and institutional trust holds,
  democratic innovation becomes possible.
options:
  deliberative_democracy: 0.30      # Citizens' assemblies, liquid democracy
  digital_democracy: 0.25           # Blockchain voting, direct participation
  technocratic_hybrid: 0.20         # Expert panels + democratic oversight
  participatory_stagnation: 0.25    # More participation, slower decisions
key_effects: global_democracy_index, governance_model

# NEW: Fires in catastrophic timelines — resistance and recovery
id: "2055_resilience"
year_month: "2055-01"
title: "The Rebuilding"
conditional: "existential_risk_cumulative > 0.3 AND existential_risk_cumulative < 0.8"
description: >
  Even in the worst timelines short of extinction, humans rebuild.
  The question is what they build.
options:
  authoritarian_order: 0.25         # Strongmen restore stability
  cooperative_rebuilding: 0.25      # Crisis forces cooperation
  fragmented_survival: 0.25         # Local communities, no global order
  technological_rescue: 0.15        # AI/tech used to repair damage
  dark_age: 0.10                    # Genuine civilizational regression
key_effects: global_democracy_index, governance_model, global_gdp
```

---

## Patch 5: Add Random Shock Events

### Problem

The DAG is fully deterministic given upstream results. Real history includes shocks that are genuinely independent of everything else — a volcanic eruption, an assassination, a scientific accident. These add irreducible randomness that prevents any path from feeling "inevitable."

### Fix: Add 6 Low-Probability Shock Nodes

These nodes have no dependencies and flat distributions. They fire (or don't) regardless of what else has happened, injecting genuine randomness into the timeline.

```yaml
# SHOCK: Major Volcanic Eruption (like Tambora)
id: "shock_supervolcano"
year_month: "2037-08"
title: "Major Volcanic Eruption"
description: >
  A VEI-7 eruption (like Tambora 1815) causes a "year without summer."
  Independent of all other events — geology doesn't care about politics.
variable: "eruption"
distribution:
  type: "bernoulli"
  p: 0.06                          # ~6% chance per century
outcomes:
  eruption:
    status: "ESCALATED"
    description: "VEI-7 eruption in Indonesia; global temperatures drop 1°C for 2 years"
    world_state_effects:
      climate_temp_anomaly: "-0.30"   # Temporary cooling (ironic)
      food_security_index: "-0.20"
      conflict_deaths: "+50000"
      global_gdp_growth_modifier: "*0.95"
  no_eruption:
    status: "HISTORICAL"
    world_state_effects: {}

# SHOCK: Charismatic Global Leader
id: "shock_global_leader"
year_month: "2034-01"
title: "Transformative Political Figure"
description: >
  A Mandela/Gandhi-level figure emerges and shifts global politics.
  Independent event — great individuals are not predictable.
variable: "leader_emerges"
distribution:
  type: "bernoulli"
  p: 0.12
outcomes:
  emerges:
    status: "DIVERGENCE"
    description: "Charismatic leader unifies global climate/peace movement"
    world_state_effects:
      global_democracy_index: "+0.05"
      climate_temp_anomaly: "-0.03"
      conflict_deaths: "-20000"
      us_polarization: "-0.03"
  no_leader:
    status: "HISTORICAL"
    world_state_effects: {}

# SHOCK: Novel Pandemic (Pre-COVID equivalent for 2030s+)
id: "shock_pandemic_2035"
year_month: "2035-06"
title: "Novel Pathogen Emergence"
description: >
  Zoonotic spillover is probabilistic, not deterministic.
variable: "pandemic_2035"
distribution:
  type: "bernoulli"
  p: 0.15
outcomes:
  pandemic:
    status: "ESCALATED"
    description: "Novel respiratory pathogen; 1-5M deaths depending on response"
    world_state_effects:
      global_pandemic_deaths: "+2000000"
      global_gdp_growth_modifier: "*0.97"
    cascading_modifiers:
      2038_autonomous_weapons.proliferation: "+0.03"   # Crisis accelerates militarization
  no_pandemic:
    status: "HISTORICAL"
    world_state_effects: {}

# SHOCK: Major Scientific Breakthrough (Unexpected)
id: "shock_breakthrough"
year_month: "2041-03"
title: "Unexpected Scientific Revolution"
description: >
  A genuine paradigm shift — room-temperature superconductors,
  breakthrough in consciousness, proof of multiverse. Can't be predicted.
variable: "breakthrough"
distribution:
  type: "bernoulli"
  p: 0.10
outcomes:
  breakthrough:
    status: "DIVERGENCE"
    description: "Room-temperature superconductor verified and reproducible"
    world_state_effects:
      global_gdp_growth_modifier: "*1.03"
      renewable_energy_share: "+0.08"
      climate_temp_anomaly: "-0.05"
      ai_development_year_offset: "+1"
  no_breakthrough:
    status: "HISTORICAL"
    world_state_effects: {}

# SHOCK: Assassination of Major Leader
id: "shock_assassination"
year_month: "2032-09"
title: "Assassination of Major World Leader"
description: >
  Political assassination with cascading consequences.
  Independent of other events.
variable: "assassination"
distribution:
  type: "bernoulli"
  p: 0.08
outcomes:
  assassination:
    status: "ESCALATED"
    description: "Major head of state assassinated; succession crisis"
    world_state_effects:
      nuclear_risk_level: "+0.05"
      global_democracy_index: "-0.02"
      conflict_deaths: "+5000"
  no_assassination:
    status: "HISTORICAL"
    world_state_effects: {}

# SHOCK: Carrington-Class Solar Storm
id: "shock_solar_storm"
year_month: "2044-07"
title: "Massive Solar Storm"
description: >
  Carrington-class coronal mass ejection hits Earth.
  Could destroy satellite infrastructure and power grids.
variable: "solar_storm"
distribution:
  type: "bernoulli"
  p: 0.08
outcomes:
  storm:
    status: "ESCALATED"
    description: "Solar storm destroys 30% of satellites; power grid damage in Northern Hemisphere"
    world_state_effects:
      supply_chain_resilience: "-0.15"
      global_gdp_growth_modifier: "*0.95"
      space_development_index: "-0.10"
      global_cyber_damage_annual_b: "+20"
  no_storm:
    status: "HISTORICAL"
    world_state_effects: {}
```

**Impact of shock events:** In any given run, 0-3 of these shocks fire. Most runs get zero or one. But when a supervolcano erupts in a timeline that was otherwise heading toward GOLDEN AGE, or when a scientific breakthrough rescues a timeline heading toward DECLINE, it creates genuinely surprising outcomes that prevent any path from feeling predetermined.

---

## Expected Batch Distribution After Patches

### Before Patches (Estimated)
```
GOLDEN AGE         0.4%
PROGRESS          35.0%    ← too dominant
MUDDLING THROUGH  30.0%    ← too dominant  
DECLINE           22.0%
CATASTROPHE        9.0%
EXTINCTION         0.3%
TRANSCENDENCE      1.3%
RADICALLY DIFF     2.0%
```

### After Patches (Target)
```
GOLDEN AGE         1.5%    ↑ Good futures have interesting events now
PROGRESS          25.0%    ↓ Spread more evenly
MUDDLING THROUGH  22.0%    ↓ 
DECLINE           20.0%    
CATASTROPHE       15.0%    ↑ Flatter distributions make bad outcomes more reachable
EXTINCTION         1.5%    ↑ Nuclear use probability doubled
TRANSCENDENCE      3.0%    ↑ AI paths more variable
RADICALLY DIFF    12.0%    ↑ Cross-domain shocks create weird timelines
```

### Diversity Metrics to Validate

After implementing these patches, run 10,000 iterations and check:

1. **All 8 verdict categories appear** (currently EXTINCTION and TRANSCENDENCE may be too rare to appear in 10K)
2. **No single node has r² > 0.30 with composite** (Iraq War should drop from ~0.28 to ~0.20)
3. **Top 5 leverage nodes collectively explain < 60% of variance** (currently ~70%)
4. **Within PROGRESS outcomes, standard deviation of composite scores > 0.15** (indicates diversity within the category, not clustering)
5. **At least 20% of runs have a shock event** (~50% of runs should have at least one of the 6 shocks fire, given their individual probabilities)
6. **"Good" and "bad" futures have similar node-firing rates** (currently good futures have sparse future eras)
7. **The most common specific path (exact sequence of branches) appears in < 0.5% of runs** (no single path should dominate)
