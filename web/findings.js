// findings.js -- 21csim Findings page: displays pre-computed batch statistics

const VERDICT_ORDER = [
  'GOLDEN-AGE',
  'TRANSCENDENCE',
  'PROGRESS',
  'MUDDLING-THROUGH',
  'RADICALLY-DIFFERENT',
  'DECLINE',
  'CATASTROPHE',
  'EXTINCTION',
];

const VERDICT_COLORS = {
  'GOLDEN-AGE':          getComputedStyle(document.documentElement).getPropertyValue('--verdict-golden-age').trim()          || '#ffd700',
  'TRANSCENDENCE':       getComputedStyle(document.documentElement).getPropertyValue('--verdict-transcendence').trim()       || '#c040ff',
  'PROGRESS':            getComputedStyle(document.documentElement).getPropertyValue('--verdict-progress').trim()            || '#40c040',
  'MUDDLING-THROUGH':    getComputedStyle(document.documentElement).getPropertyValue('--verdict-muddling-through').trim()    || '#c0c040',
  'RADICALLY-DIFFERENT': getComputedStyle(document.documentElement).getPropertyValue('--verdict-radically-different').trim() || '#ff40ff',
  'DECLINE':             getComputedStyle(document.documentElement).getPropertyValue('--verdict-decline').trim()             || '#ff8040',
  'CATASTROPHE':         getComputedStyle(document.documentElement).getPropertyValue('--verdict-catastrophe').trim()         || '#ff4040',
  'EXTINCTION':          getComputedStyle(document.documentElement).getPropertyValue('--verdict-extinction').trim()          || '#ff0000',
};

const VERDICT_LABELS = {
  'GOLDEN-AGE':          'Golden Age',
  'TRANSCENDENCE':       'Transcendence',
  'PROGRESS':            'Progress',
  'MUDDLING-THROUGH':    'Muddling Through',
  'RADICALLY-DIFFERENT': 'Radically Different',
  'DECLINE':             'Decline',
  'CATASTROPHE':         'Catastrophe',
  'EXTINCTION':          'Extinction',
};

// Dimensions where higher values are generally "good"
const GOOD_HIGH = new Set([
  'eu_cohesion', 'us_global_standing', 'global_gdp_growth_modifier',
  'supply_chain_resilience', 'internet_freedom_index', 'renewable_energy_share',
  'biodiversity_index', 'food_security_index', 'arctic_ice_status',
  'global_democracy_index', 'us_institutional_trust', 'racial_justice_index',
  'gender_equity_index', 'space_development_index', 'human_augmentation_prevalence',
  'us_life_expectancy_delta', 'india_power_index', 'latin_america_stability',
  'middle_east_stability',
]);

// Dimensions where higher values are generally "bad"
const BAD_HIGH = new Set([
  'us_polarization', 'inequality_index', 'us_debt_gdp_ratio',
  'nuclear_risk_level', 'terrorism_threat_index', 'surveillance_state_index',
  'global_cyber_damage_annual_b', 'drone_warfare_prevalence',
  'climate_temp_anomaly', 'sea_level_rise_meters', 'water_stress_index',
  'misinformation_severity', 'global_pandemic_deaths', 'conflict_deaths',
  'opioid_deaths_cumulative',
]);

// Human-readable dimension labels
const DIM_LABELS = {
  us_polarization: 'US Polarization',
  eu_cohesion: 'EU Cohesion',
  us_global_standing: 'US Global Standing',
  china_power_index: 'China Power Index',
  russia_stability: 'Russia Stability',
  middle_east_stability: 'Middle East Stability',
  india_power_index: 'India Power Index',
  latin_america_stability: 'Latin America Stability',
  global_gdp_growth_modifier: 'Global GDP Growth Modifier',
  inequality_index: 'Inequality Index',
  us_debt_gdp_ratio: 'US Debt/GDP Ratio',
  crypto_market_cap_trillion: 'Crypto Market Cap ($T)',
  supply_chain_resilience: 'Supply Chain Resilience',
  ai_development_year_offset: 'AI Development Year Offset',
  internet_freedom_index: 'Internet Freedom Index',
  social_media_penetration: 'Social Media Penetration',
  human_augmentation_prevalence: 'Human Augmentation Prevalence',
  space_development_index: 'Space Development Index',
  nuclear_risk_level: 'Nuclear Risk Level',
  terrorism_threat_index: 'Terrorism Threat Index',
  surveillance_state_index: 'Surveillance State Index',
  global_cyber_damage_annual_b: 'Global Cyber Damage ($B/yr)',
  drone_warfare_prevalence: 'Drone Warfare Prevalence',
  climate_temp_anomaly: 'Climate Temp Anomaly (C)',
  renewable_energy_share: 'Renewable Energy Share',
  sea_level_rise_meters: 'Sea Level Rise (m)',
  biodiversity_index: 'Biodiversity Index',
  water_stress_index: 'Water Stress Index',
  food_security_index: 'Food Security Index',
  arctic_ice_status: 'Arctic Ice Status',
  global_pandemic_deaths: 'Global Pandemic Deaths',
  conflict_deaths: 'Conflict Deaths',
  opioid_deaths_cumulative: 'Opioid Deaths (Cumulative)',
  global_democracy_index: 'Global Democracy Index',
  us_institutional_trust: 'US Institutional Trust',
  misinformation_severity: 'Misinformation Severity',
  racial_justice_index: 'Racial Justice Index',
  gender_equity_index: 'Gender Equity Index',
  us_life_expectancy_delta: 'US Life Expectancy Delta',
};

// Node descriptions (brief) keyed by node_id pattern
const NODE_DESCRIPTIONS = {
  '2000_election':           'The 2000 US presidential election and its contested outcome',
  '2001_dotcom_aftermath':   'Aftermath of the dot-com bubble burst',
  '2001_china_wto':          'China joining the World Trade Organization',
  '2003_opioid_crisis':      'The US opioid epidemic escalation',
  '2003_brics_rise':         'Rise of BRICS emerging economies',
  '2004_social_media':       'Dawn of the social media era',
  '2005_katrina':            'Hurricane Katrina and US infrastructure',
  '2005_katrina_racial':     'Racial dimensions of Katrina response',
  '2006_cloud':              'Cloud computing revolution',
  '2006_north_korea':        'North Korea nuclear program',
  '2007_iphone':             'The iPhone and mobile revolution',
  '2010_arab_spring':        'Arab Spring uprisings',
  '2010_euro_crisis':        'European sovereign debt crisis',
  '2010_stuxnet':            'Stuxnet and state-sponsored cyber warfare',
  '2010_wikileaks':          'WikiLeaks and radical transparency',
  '2011_debt_ceiling':       'US debt ceiling crisis',
  '2011_libya':              'Libya intervention and aftermath',
  '2012_deep_learning':      'Deep learning breakthrough',
  '2012_xi_consolidation':   'Xi Jinping consolidation of power',
  '2013_snowden':            'Snowden revelations on mass surveillance',
  '2013_crypto':             'Cryptocurrency emergence',
  '2013_syria_redline':      'Syria chemical weapons red line',
  '2014_crimea':             'Russian annexation of Crimea',
  '2014_gig_economy':        'Rise of the gig economy',
  '2014_isis':               'Rise of ISIS',
  '2014_deaths_of_despair':  'Deaths of despair in the US',
  '2014_india_modi':         'Modi era begins in India',
  '2014_venezuela':          'Venezuelan crisis deepens',
  '2015_paris_attacks':      'Paris terrorist attacks',
  '2015_iran_deal':          'Iran nuclear deal (JCPOA)',
  '2015_paris_climate':      'Paris Climate Agreement',
  '2015_crispr':             'CRISPR gene editing arrives',
  '2015_marriage_equality':  'US marriage equality ruling',
  '2015_africa_development': 'African development trajectories',
  '2016_brexit':             'UK votes to leave the EU',
  '2016_self_driving':       'Self-driving vehicle development',
  '2017_metoo':              '#MeToo movement',
  '2017_saudi_transformation': 'Saudi Arabia transformation agenda',
  '2018_trade_war':          'US-China trade war escalation',
  '2018_facebook_cambridge': 'Facebook/Cambridge Analytica scandal',
  '2018_populism':           'Global populism wave',
  '2019_covid_emergence':    'COVID-19 emergence',
  '2019_unicorn_bubble':     'Tech unicorn bubble',
  '2019_antivax':            'Anti-vaccination movement growth',
  '2019_global_protests':    'Global protest movements',
  '2019_quantum':            'Quantum computing milestones',
  '2020_covid_response':     'COVID-19 pandemic response',
  '2020_us_election':        '2020 US presidential election',
  '2020_solarwinds':         'SolarWinds cyber attack',
  '2020_remote_work':        'Remote work revolution',
  '2020_mental_health':      'Global mental health crisis',
  '2020_education':          'Education system disruption',
  '2020_tiktok':             'TikTok and short-form media',
  '2021_jan6':               'January 6th Capitol breach',
  '2021_supply_chain':       'Global supply chain crisis',
  '2021_hypersonics':        'Hypersonic weapons race',
  '2021_myanmar':            'Myanmar military coup',
  '2022_inflation_crisis':   'Global inflation crisis',
  '2022_wagner':             'Wagner Group and Russia fractures',
  '2022_european_right':     'European far-right surge',
  '2023_brics_expansion':    'BRICS expansion and de-dollarization',
  '2023_open_source_ai':     'Open source AI proliferation',
  '2024_us_election':        '2024 US presidential election',
  '2025_ai_regulation':      'AI regulation inflection point',
  '2025_climate_tipping':    'Climate tipping points approach',
  '2026_taiwan_strait':      'Taiwan Strait crisis',
  '2027_energy_transition':  'Global energy transition',
  '2028_agi_threshold':      'AGI threshold -- the most consequential technology question',
  '2029_pandemic_2':         'Second major pandemic',
  '2030_japan_population':   'Japan population crisis',
  '2031_ai_displacement':    'AI-driven mass displacement of workers',
  '2032_ai_governance':      'AI governance frameworks',
  '2032_moon_base':          'Permanent lunar base',
  '2033_ai_science':         'AI-accelerated scientific discovery',
  '2033_arctic_ice_free':    'Arctic ice-free summers',
  '2033_urbanization':       'Megacity urbanization',
  '2035_carbon_capture':     'Carbon capture at scale',
  '2035_neural_interface':   'Neural interface technology',
  '2036_water_conflict':     'Water scarcity conflicts',
  '2037_ai_consciousness':   'AI consciousness debate',
  '2038_autonomous_weapons':  'Autonomous weapons proliferation',
  '2040_us_infrastructure':  'US infrastructure renewal',
  '2042_amoc':               'Atlantic ocean circulation collapse risk',
  '2042_superintelligence':  'Superintelligence emergence',
  '2043_ubi':                'Universal basic income adoption',
  '2044_climate_refugee':    'Climate refugee crisis',
  '2044_us_constitutional':  'US constitutional crisis',
  '2045_geoengineering':     'Solar geoengineering deployment',
  '2045_cognitive_enhancement': 'Cognitive enhancement technology',
  '2045_space_economy':      'Space-based economy',
  '2047_amazon_tipping':     'Amazon rainforest tipping point',
  '2048_digital_immortality': 'Digital immortality technology',
  '2048_mars_settlement':    'Mars settlement',
  '2049_hybrid_governance':  'Human-AI hybrid governance',
  '2065_climate_verdict':    'Climate verdict for the century',
  '2065_post_human':         'Post-human divergence',
  '2065_multiplanetary':     'Multiplanetary civilization',
  '2065_population_decline': 'Global population decline',
  '2068_ocean_ecosystem':    'Ocean ecosystem status',
  '2068_interstellar_probe': 'Interstellar probe launch',
};


async function init() {
  const loadingEl = document.getElementById('loading');
  const errorEl = document.getElementById('error');

  let data;
  try {
    const resp = await fetch('batch-10k.json');
    if (!resp.ok) throw new Error(`Failed to load batch-10k.json (${resp.status})`);
    data = await resp.json();
  } catch (err) {
    loadingEl.style.display = 'none';
    errorEl.style.display = 'block';
    errorEl.textContent = `Error: ${err.message}. Run the batch generation script first.`;
    return;
  }

  loadingEl.style.display = 'none';

  renderInsights(data);
  renderVerdictChart(data);
  renderLeverageRanking(data);
  renderDimensionStats(data);
  renderMethodology(data);

  // Show all sections
  document.querySelectorAll('.findings-section').forEach(s => s.style.display = '');
}


function renderInsights(data) {
  const dist = data.outcome_distribution;
  const dimStats = data.dimension_stats;

  // Most common outcome
  let maxVerdict = '';
  let maxPct = 0;
  for (const [v, pct] of Object.entries(dist)) {
    if (pct > maxPct) { maxPct = pct; maxVerdict = v; }
  }

  // Extinction risk
  const extinctionPct = (dist['EXTINCTION'] || 0) * 100;

  // Mean composite score -- approximate from dimension stats
  // We can compute a rough score from the mean values, but the batch data
  // does not include composite_score stats directly. Use a sentinel if missing.
  let meanScore = '--';
  if (data.mean_composite_score !== undefined) {
    meanScore = data.mean_composite_score > 0
      ? `+${data.mean_composite_score.toFixed(3)}`
      : data.mean_composite_score.toFixed(3);
  } else {
    // Estimate from dimension means if available
    const dims = Object.values(dimStats);
    if (dims.length > 0) {
      const avg = dims.reduce((s, d) => s + (d.mean || 0), 0) / dims.length;
      meanScore = avg > 0 ? `+${avg.toFixed(3)}` : avg.toFixed(3);
    }
  }

  // Most volatile node -- find highest std across dimensions
  let mostVolatile = '';
  let maxStd = 0;
  for (const [dim, stats] of Object.entries(dimStats)) {
    if ((stats.std || 0) > maxStd) {
      maxStd = stats.std;
      mostVolatile = dim;
    }
  }

  const container = document.getElementById('insight-cards');
  container.innerHTML = `
    <div class="insight-card">
      <div class="insight-label">Most Common Outcome</div>
      <div class="insight-value" style="color: ${VERDICT_COLORS[maxVerdict] || 'var(--text-bright)'}">
        ${VERDICT_LABELS[maxVerdict] || maxVerdict}
      </div>
      <div class="insight-sub">${(maxPct * 100).toFixed(1)}% of all runs</div>
    </div>
    <div class="insight-card">
      <div class="insight-label">Extinction Risk</div>
      <div class="insight-value" style="color: ${VERDICT_COLORS['EXTINCTION']}">${extinctionPct.toFixed(1)}%</div>
      <div class="insight-sub">of 10,000 simulated centuries</div>
    </div>
    <div class="insight-card">
      <div class="insight-label">Mean Composite Score</div>
      <div class="insight-value">${meanScore}</div>
      <div class="insight-sub">averaged across all dimensions</div>
    </div>
    <div class="insight-card">
      <div class="insight-label">Most Volatile Dimension</div>
      <div class="insight-value" style="font-size: 16px;">${DIM_LABELS[mostVolatile] || mostVolatile}</div>
      <div class="insight-sub">std = ${maxStd.toFixed(4)}</div>
    </div>
  `;
}


function renderVerdictChart(data) {
  const dist = data.outcome_distribution;
  const container = document.getElementById('verdict-chart');

  // Sort by our defined order
  const sorted = VERDICT_ORDER.filter(v => dist[v] !== undefined);

  let html = '';
  for (const v of sorted) {
    const pct = (dist[v] || 0) * 100;
    const color = VERDICT_COLORS[v] || '#888';
    const label = VERDICT_LABELS[v] || v;
    const widthPct = Math.max(pct, 0.3); // min visual width

    html += `
      <div class="verdict-bar-row">
        <div class="verdict-bar-label" style="color: ${color}">${label}</div>
        <div class="verdict-bar-track">
          <div class="verdict-bar-fill" style="width: ${widthPct}%; background: ${color};">
            ${pct >= 5 ? `<span class="verdict-bar-pct">${pct.toFixed(1)}%</span>` : ''}
          </div>
        </div>
        ${pct < 5 ? `<span class="verdict-bar-pct-outside">${pct.toFixed(1)}%</span>` : ''}
      </div>
    `;
  }

  container.innerHTML = html;
}


function renderLeverageRanking(data) {
  const nodes = data.highest_leverage_nodes || [];
  const top20 = nodes.slice(0, 20);
  const container = document.getElementById('leverage-list');

  if (top20.length === 0) {
    container.innerHTML = '<div style="color: var(--text-dim); padding: 20px; text-align: center;">No leverage data available.</div>';
    return;
  }

  const maxR2 = top20[0].r_squared || 0.01;

  let html = '';
  for (let i = 0; i < top20.length; i++) {
    const node = top20[i];
    const nodeId = node.node_id;
    const r2 = node.r_squared;
    const desc = NODE_DESCRIPTIONS[nodeId] || '';
    const barPct = (r2 / maxR2) * 100;

    html += `
      <div class="leverage-item">
        <div class="leverage-rank">${i + 1}</div>
        <div class="leverage-info">
          <div class="leverage-node-name">${nodeId}</div>
          ${desc ? `<div class="leverage-node-desc">${desc}</div>` : ''}
        </div>
        <div class="leverage-r2">r2 = ${r2.toFixed(4)}</div>
        <div class="leverage-bar-track">
          <div class="leverage-bar-fill" style="width: ${barPct}%;"></div>
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}


function renderDimensionStats(data) {
  const dimStats = data.dimension_stats || {};
  const container = document.getElementById('dim-stats');

  const dims = Object.keys(dimStats).sort();
  if (dims.length === 0) {
    container.innerHTML = '<div style="color: var(--text-dim); padding: 20px; text-align: center;">No dimension data available.</div>';
    return;
  }

  const statCols = ['mean', 'std', 'p5', 'p25', 'p50', 'p75', 'p95'];
  const colLabels = ['Mean', 'Std', 'P5', 'P25', 'Median', 'P75', 'P95'];

  let html = '<table class="dim-stats-table"><thead><tr>';
  html += '<th class="dim-col">Dimension</th>';
  for (let i = 0; i < statCols.length; i++) {
    html += `<th>${colLabels[i]}</th>`;
  }
  html += '</tr></thead><tbody>';

  for (const dim of dims) {
    const stats = dimStats[dim];
    html += '<tr>';
    html += `<td class="dim-name">${DIM_LABELS[dim] || dim}</td>`;

    for (const col of statCols) {
      const val = stats[col];
      const display = val !== undefined ? formatValue(val) : '--';

      // Color-code the mean column
      let cls = 'cell-neutral';
      if (col === 'mean') {
        cls = getCellClass(dim, val);
      }

      html += `<td class="${cls}">${display}</td>`;
    }
    html += '</tr>';
  }

  html += '</tbody></table>';
  container.innerHTML = html;
}


function getCellClass(dim, val) {
  // Color based on whether the value seems good or bad
  if (GOOD_HIGH.has(dim)) {
    return val > 0.6 ? 'cell-good' : val < 0.3 ? 'cell-bad' : 'cell-neutral';
  }
  if (BAD_HIGH.has(dim)) {
    return val > 0.6 ? 'cell-bad' : val < 0.3 ? 'cell-good' : 'cell-neutral';
  }
  return 'cell-neutral';
}


function formatValue(val) {
  if (Number.isInteger(val) && Math.abs(val) > 1000) {
    return val.toLocaleString();
  }
  if (Math.abs(val) >= 100) {
    return val.toFixed(1);
  }
  return val.toFixed(4);
}


function renderMethodology(data) {
  const n = data.iterations || 10000;
  const container = document.getElementById('methodology');

  container.innerHTML = `
    <p>
      These findings are generated via <strong>Monte Carlo simulation</strong>: ${n.toLocaleString()} independent
      runs of the 21st Century Simulation engine, each tracing a plausible history from the year 2000
      through ~2100. The simulation graph contains <strong>303 decision nodes</strong> spanning geopolitics,
      technology, climate, economics, security, and social dimensions. Each node has probabilistically
      weighted branches; at each node, the engine samples a branch according to its probability
      distribution (conditioned on current world state), applies the resulting state deltas across
      <strong>32 tracked dimensions</strong>, and proceeds to successor nodes. After all nodes are
      resolved, a composite score and outcome class (verdict) are computed from the final world state.
    </p>
    <p style="margin-top: 12px;">
      The <strong>leverage ranking</strong> uses r-squared values from a variance decomposition: for each node,
      we measure how much of the variance in composite scores across all ${n.toLocaleString()} runs can be
      attributed to which branch was taken at that node. Higher r-squared indicates that the node's
      outcome has an outsized effect on how the century turns out. The <strong>dimension statistics</strong>
      table shows percentile distributions of each world-state dimension at the end of the simulation,
      giving a sense of the range of futures for each tracked variable.
    </p>
  `;
}


// Boot
init();
