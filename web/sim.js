// sim.js -- In-browser port of the Python simulation engine (src/csim).
// Faithful to engine.py / graph.py / world_state.py semantics so interactive
// runs behave like the canonical simulator. RNG differs (mulberry32 vs numpy),
// so free-running timelines are new worlds — but any fully-locked run
// reproduces the Python engine's output exactly (verified in CI-adjacent
// parity tests; see scripts/validate_sim_parity.py).

// ── World state ──

export const INITIAL_STATE = {
  us_polarization: 0.35, eu_cohesion: 0.75, us_global_standing: 0.85,
  china_power_index: 0.30, russia_stability: 0.45, middle_east_stability: 0.40,
  india_power_index: 0.15, latin_america_stability: 0.50,
  global_gdp_growth_modifier: 1.0, inequality_index: 0.50, us_debt_gdp_ratio: 0.55,
  crypto_market_cap_trillion: 0.0, supply_chain_resilience: 0.70,
  ai_development_year_offset: 0, internet_freedom_index: 0.80,
  social_media_penetration: 0.05, human_augmentation_prevalence: 0.0,
  space_development_index: 0.0, nuclear_risk_level: 0.15, terrorism_threat_index: 0.30,
  surveillance_state_index: 0.20, global_cyber_damage_annual_b: 1.0,
  drone_warfare_prevalence: 0.0, climate_temp_anomaly: 0.6, renewable_energy_share: 0.06,
  sea_level_rise_meters: 0.0, biodiversity_index: 0.80, water_stress_index: 0.25,
  food_security_index: 0.85, arctic_ice_status: 0.90, global_pandemic_deaths: 0,
  conflict_deaths: 0, opioid_deaths_cumulative: 0, global_democracy_index: 0.62,
  us_institutional_trust: 0.55, misinformation_severity: 0.15,
  racial_justice_index: 0.40, gender_equity_index: 0.45, us_life_expectancy_delta: 0.0,
  global_population_billions: 6.1, median_age_global: 26.0, automation_displacement: 0.0,
  governance_model: 0.50, us_unity_index: 0.70, europe_federation_index: 0.20,
  china_regime_type: 0.15, middle_east_post_oil: 0.05, arctic_sovereignty_resolved: 0.05,
  africa_development_index: 0.25, existential_risk_cumulative: 0.0,
};

const CLAMP_RANGES = {
  us_polarization: [0, 1], eu_cohesion: [0, 1], us_global_standing: [0, 1],
  china_power_index: [0, 1], russia_stability: [0, 1], middle_east_stability: [0, 1],
  india_power_index: [0, 1], latin_america_stability: [0, 1],
  global_gdp_growth_modifier: [0.1, 3.0], inequality_index: [0, 1],
  us_debt_gdp_ratio: [0, 5.0], crypto_market_cap_trillion: [0, 100.0],
  supply_chain_resilience: [0, 1], internet_freedom_index: [0, 1],
  social_media_penetration: [0, 1], human_augmentation_prevalence: [0, 1],
  space_development_index: [0, 1], nuclear_risk_level: [0, 1],
  terrorism_threat_index: [0, 1], surveillance_state_index: [0, 1],
  global_cyber_damage_annual_b: [0, 10000.0], drone_warfare_prevalence: [0, 1],
  climate_temp_anomaly: [0, 10.0], renewable_energy_share: [0, 1],
  sea_level_rise_meters: [0, 20.0], biodiversity_index: [0, 1],
  water_stress_index: [0, 1], food_security_index: [0, 1], arctic_ice_status: [0, 1],
  global_democracy_index: [0, 1], us_institutional_trust: [0, 1],
  misinformation_severity: [0, 1], racial_justice_index: [0, 1],
  gender_equity_index: [0, 1], us_life_expectancy_delta: [-20.0, 20.0],
  global_population_billions: [0, 15.0], median_age_global: [15.0, 60.0],
  automation_displacement: [0, 1], governance_model: [0, 1], us_unity_index: [0, 1],
  europe_federation_index: [0, 1], china_regime_type: [0, 1],
  middle_east_post_oil: [0, 1], arctic_sovereignty_resolved: [0, 1],
  africa_development_index: [0, 1], existential_risk_cumulative: [0, 1],
};

const INT_DIMENSIONS = new Set([
  'global_pandemic_deaths', 'conflict_deaths', 'opioid_deaths_cumulative',
  'ai_development_year_offset',
]);

function clamp(value, dim) {
  const r = CLAMP_RANGES[dim];
  return r ? Math.max(r[0], Math.min(r[1], value)) : value;
}

// Python int() truncates toward zero
function toInt(x) { return Math.trunc(x); }

function applySingleEffect(current, effectValue, dim) {
  let result;
  if (typeof effectValue === 'string') {
    const v = effectValue.trim();
    if (v.startsWith('*')) {
      result = current * parseFloat(v.slice(1));
    } else if (v.startsWith('+') || v.startsWith('-')) {
      result = current + parseFloat(v);
    } else {
      const abs = Number(v);
      if (Number.isNaN(abs)) return current; // non-numeric categorical label
      result = abs;
    }
  } else if (typeof effectValue === 'number') {
    result = effectValue;
  } else {
    return current;
  }
  if (INT_DIMENSIONS.has(dim)) return toInt(result);
  return clamp(result, dim);
}

export function evaluateCondition(state, condition) {
  if (!condition) return false;
  if (condition.includes(' AND ')) {
    return condition.split(' AND ').every(p => evaluateCondition(state, p.trim()));
  }
  if (condition.includes(' OR ')) {
    return condition.split(' OR ').some(p => evaluateCondition(state, p.trim()));
  }
  const m = condition.trim().match(/^(\w+)\s*(>=|<=|>|<|==|!=)\s*(.+)$/);
  if (!m) return false;
  const [, dim, op, valStr] = m;
  if (!(dim in state)) return false;
  const current = state[dim];
  let target = parseFloat(valStr);
  if (Number.isNaN(target)) {
    // Non-numeric target: string comparison (rare; all dims are numeric today)
    const t = valStr.trim().replace(/^['"]|['"]$/g, '');
    switch (op) {
      case '==': return String(current) === t;
      case '!=': return String(current) !== t;
      default: return false;
    }
  }
  if (INT_DIMENSIONS.has(dim)) target = toInt(target);
  switch (op) {
    case '>': return current > target;
    case '<': return current < target;
    case '>=': return current >= target;
    case '<=': return current <= target;
    case '==': return current === target;
    case '!=': return current !== target;
    default: return false;
  }
}

// effects may contain {"if": cond, "then": {...}} — the condition is
// evaluated against the state as it was BEFORE this effects block
// (matching apply_effects in world_state.py)
function applyEffects(state, effects) {
  const newState = { ...state };
  for (const [key, value] of Object.entries(effects)) {
    if (key === 'if') continue;
    if (key === 'then') {
      if (evaluateCondition(state, effects['if'] || '')) {
        Object.assign(newState, applyEffects(newState, value));
      }
      continue;
    }
    if (!(key in newState)) continue;
    newState[key] = applySingleEffect(newState[key], value, key);
  }
  return newState;
}

// ── Distribution / reachability (graph.py) ──

export function getModifiedDistribution(nodeId, results, nodes, cascadingEffects) {
  const data = nodes[nodeId];
  const probs = { ...(data.distribution || {}) };
  if (Object.keys(probs).length === 0) return {};

  for (const dep of data.dependencies || []) {
    const upstreamResult = results[dep.node];
    if (upstreamResult === undefined) continue;
    if (dep.branch == null || upstreamResult === dep.branch) {
      for (const [branch, shift] of Object.entries(dep.modifies || {})) {
        if (branch in probs) probs[branch] += parseFloat(String(shift));
      }
    }
  }

  for (const [targetSpec, shift] of Object.entries(cascadingEffects || {})) {
    const parts = targetSpec.split('.');
    if (parts[0] === nodeId && parts.length >= 2) {
      const branch = parts[1];
      if (branch in probs) probs[branch] += parseFloat(String(shift));
    }
  }

  let total = 0;
  for (const k of Object.keys(probs)) {
    probs[k] = Math.max(0, probs[k]);
    total += probs[k];
  }
  const keys = Object.keys(probs);
  if (total === 0) {
    for (const k of keys) probs[k] = 1 / keys.length;
  } else {
    for (const k of keys) probs[k] /= total;
  }
  return probs;
}

export function isReachable(nodeId, results, nodes, state, extinct) {
  if (extinct) return false;
  const conditional = nodes[nodeId].conditional;
  if (!conditional) return true;

  const hasIneq = ['>', '<', '>='].some(op => conditional.includes(op));
  if (conditional.includes('!=') && !hasIneq) {
    const [refNode, refBranch] = conditional.split('!=').map(s => s.trim());
    if (refNode in results && results[refNode] === refBranch) return false;
  } else if (conditional.includes('==') && !hasIneq) {
    const [refNode, refBranch] = conditional.split('==').map(s => s.trim());
    if (refNode in results && results[refNode] !== refBranch) return false;
  } else {
    if (!evaluateCondition(state, conditional)) return false;
  }
  return true;
}

// ── RNG + sampling ──

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function sample(distribution, rng) {
  const branches = Object.keys(distribution);
  const r = rng();
  let cum = 0;
  for (const b of branches) {
    cum += distribution[b];
    if (r < cum) return b;
  }
  return branches[branches.length - 1];
}

// ── Scoring (world_state.py) ──

const COMPOSITE_WEIGHTS = [
  ['existential_risk_cumulative', -5.0], ['nuclear_risk_level', -3.0],
  ['conflict_deaths', -2.0], ['global_pandemic_deaths', -2.0],
  ['opioid_deaths_cumulative', -1.0],
  ['climate_temp_anomaly', -2.5], ['food_security_index', 2.0],
  ['water_stress_index', -1.5], ['biodiversity_index', 1.5],
  ['sea_level_rise_meters', -1.5],
  ['global_democracy_index', 1.5], ['internet_freedom_index', 1.0],
  ['surveillance_state_index', -1.0],
  ['global_gdp_growth_modifier', 1.0], ['inequality_index', -1.0],
  ['us_polarization', -1.0], ['eu_cohesion', 0.8],
  ['middle_east_stability', 0.5], ['us_institutional_trust', 0.8],
  ['space_development_index', 0.3], ['human_augmentation_prevalence', 0.2],
  ['renewable_energy_share', 0.5],
];

const HISTORICAL_BASELINES = {
  existential_risk_cumulative: 0.15, nuclear_risk_level: 0.35,
  conflict_deaths: 2000000, global_pandemic_deaths: 7000000,
  opioid_deaths_cumulative: 700000, climate_temp_anomaly: 2.5,
  food_security_index: 0.65, water_stress_index: 0.45, biodiversity_index: 0.50,
  sea_level_rise_meters: 0.3, global_democracy_index: 0.55,
  internet_freedom_index: 0.60, surveillance_state_index: 0.50,
  global_gdp_growth_modifier: 1.0, inequality_index: 0.60,
  us_polarization: 0.78, eu_cohesion: 0.55, middle_east_stability: 0.30,
  us_institutional_trust: 0.30, space_development_index: 0.10,
  human_augmentation_prevalence: 0.05, renewable_energy_share: 0.40,
};

export function computeCompositeScore(state) {
  let score = 0, maxPossible = 0;
  for (const [dim, weight] of COMPOSITE_WEIGHTS) {
    if (!(dim in state)) continue;
    const current = state[dim];
    const baseline = dim in HISTORICAL_BASELINES ? HISTORICAL_BASELINES[dim] : current;
    let diff;
    if (baseline === 0) {
      diff = current === 0 ? 0 : (current * weight > 0 ? 1 : -1);
    } else {
      diff = (current - baseline) / Math.max(Math.abs(baseline), 1.0);
    }
    score += weight * diff;
    maxPossible += Math.abs(weight);
  }
  if (maxPossible === 0) return 0;
  return Math.max(-1, Math.min(1, score / maxPossible));
}

export function classifyOutcome(state, totalDivergences, eventCount) {
  const composite = computeCompositeScore(state);
  if (state.existential_risk_cumulative > 0.9) return 'EXTINCTION';
  if (state.nuclear_risk_level > 0.8 && state.climate_temp_anomaly > 4.0) return 'EXTINCTION';
  if (state.human_augmentation_prevalence > 0.4 && state.space_development_index > 0.3
      && composite > 0.12) return 'TRANSCENDENCE';
  const divergenceRatio = totalDivergences / Math.max(eventCount, 1);
  if (divergenceRatio > 0.78 && Math.abs(composite) < 0.03) return 'RADICALLY-DIFFERENT';
  if (composite > 0.20) return 'GOLDEN-AGE';
  if (composite > 0.08) return 'PROGRESS';
  if (composite > -0.04) return 'MUDDLING-THROUGH';
  if (composite > -0.15) return 'DECLINE';
  if (composite > -0.40) return 'CATASTROPHE';
  return 'EXTINCTION';
}

export function generateHeadline(state, events) {
  const composite = computeCompositeScore(state);
  const divergences = events.filter(e => e.status !== 'HISTORICAL');
  if (divergences.length === 0) return 'The Historical Century: Everything Happened As It Did';
  let adj;
  if (composite > 0.7) adj = 'Golden';
  else if (composite > 0.4) adj = 'Hopeful';
  else if (composite > 0.2) adj = 'Near-Miss';
  else if (composite > 0.0) adj = 'Quiet';
  else if (composite > -0.2) adj = 'Troubled';
  else if (composite > -0.5) adj = 'Long Collapse';
  else if (composite > -0.8) adj = 'Dark';
  else adj = 'Final';
  const first = divergences[0];
  const desc = first.description.length < 50 ? first.description : first.title;
  return `The ${adj} Century: ${desc}`;
}

function computeDelta(oldState, newState) {
  const delta = {};
  for (const key of Object.keys(INITIAL_STATE)) {
    if (oldState[key] !== newState[key]) delta[key] = newState[key] - oldState[key];
  }
  return delta;
}

const round4 = (x) => Math.round(x * 10000) / 10000;

const VALID_STATUSES = new Set([
  'HISTORICAL', 'DIVERGENCE', 'PREVENTED', 'ACCELERATED',
  'DELAYED', 'ESCALATED', 'DIMINISHED',
]);

// ── Main loop (engine.py::simulate) ──

export function simulate(nodesData, seed, lockedResults) {
  const { traversal_order: traversal, nodes } = nodesData;
  const rng = mulberry32(seed);
  let state = { ...INITIAL_STATE };
  const events = [];
  const results = {};
  const dists = {};
  const cascadingEffects = {};
  let extinct = false;
  let totalDivergences = 0;
  let firstDivergenceYear = null;
  let largestDivergence = null;

  for (const nodeId of traversal) {
    const data = nodes[nodeId];
    if (!data) continue;

    if (!isReachable(nodeId, results, nodes, state, extinct)) continue;

    const probs = getModifiedDistribution(nodeId, results, nodes, cascadingEffects);
    if (Object.keys(probs).length === 0) continue;
    dists[nodeId] = probs;

    let branch;
    if (lockedResults && nodeId in lockedResults && lockedResults[nodeId] in probs) {
      branch = lockedResults[nodeId];
      // Burn one draw so the RNG stream stays aligned with the unlocked run:
      // locking a node to the branch it already took reproduces the exact
      // same future, and a different choice only changes what it causes.
      rng();
    } else {
      branch = sample(probs, rng);
    }
    results[nodeId] = branch;

    const outcomeData = (data.outcomes || {})[branch] || {};
    // Unknown statuses coerce to HISTORICAL, matching EventStatus() in engine.py
    let status = outcomeData.status || 'HISTORICAL';
    if (!VALID_STATUSES.has(status)) status = 'HISTORICAL';
    const effects = outcomeData.world_state_effects || {};

    const oldState = state;
    if (Object.keys(effects).length > 0) state = applyEffects(state, effects);

    if (status !== 'HISTORICAL') {
      totalDivergences += 1;
      if (firstDivergenceYear === null) firstDivergenceYear = data.year_month || '';
    }

    const wsDelta = computeDelta(oldState, state);
    const deltaMagnitude = Object.values(wsDelta).reduce((t, v) => t + Math.abs(v), 0);
    const isHighImpact = deltaMagnitude > 0.10;

    if (!outcomeData.silent) {
      const displayDelta = {};
      for (const [k, v] of Object.entries(wsDelta)) displayDelta[k] = round4(v);
      events.push({
        year_month: data.year_month || '',
        node_id: nodeId,
        title: data.title || nodeId,
        description: outcomeData.description || '',
        status,
        branch_taken: branch,
        domain: data.domain || '',
        probability_of_branch: round4(probs[branch] ?? 0),
        explanation: outcomeData.explanation ?? null,
        world_state_delta: displayDelta,
        is_high_impact: isHighImpact,
        confidence: data.confidence || 'HIGH',
        narration: null,
        narration_source: null,
      });
    }

    for (const [target, shift] of Object.entries(outcomeData.cascading_modifiers || {})) {
      cascadingEffects[target] = shift;
    }

    if (Object.keys(wsDelta).length > 0 && status !== 'HISTORICAL') {
      let currentLargestMag = 0;
      if (largestDivergence) {
        for (let i = 0; i < events.length - 1; i++) {
          if (events[i].node_id === largestDivergence) {
            currentLargestMag = Object.values(events[i].world_state_delta)
              .reduce((t, v) => t + Math.abs(v), 0);
            break;
          }
        }
      }
      if (deltaMagnitude > currentLargestMag) largestDivergence = nodeId;
    }

    if (state.existential_risk_cumulative > 0.9) extinct = true;
  }

  const composite = computeCompositeScore(state);
  const outcomeClass = classifyOutcome(state, totalDivergences, events.length);
  const headline = generateHeadline(state, events);

  const finalState = {};
  for (const [k, v] of Object.entries(state)) {
    finalState[k] = Number.isInteger(v) ? v : round4(v);
  }
  finalState.total_divergences = totalDivergences;
  finalState.first_divergence_year = firstDivergenceYear;
  finalState.largest_divergence = largestDivergence;

  return {
    seed,
    headline,
    outcome_class: outcomeClass,
    composite_score: round4(composite),
    percentile: 50.0,
    total_divergences: totalDivergences,
    first_divergence_year: firstDivergenceYear,
    largest_divergence_node: largestDivergence,
    tags: [],
    events,
    final_state: finalState,
    _results: results,
    _dists: dists,
  };
}

// ── Node data loading (cached) ──

let _nodesData = null;
let _nodesPromise = null;

export function loadSimNodes() {
  if (_nodesData) return Promise.resolve(_nodesData);
  if (_nodesPromise) return _nodesPromise;
  _nodesPromise = fetch('/nodes-sim.json')
    .then(r => { if (!r.ok) throw new Error(`nodes-sim.json: HTTP ${r.status}`); return r.json(); })
    .then(data => { _nodesData = data; return data; });
  return _nodesPromise;
}
