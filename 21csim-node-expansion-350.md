# 21csim — Node Expansion to 350+

## Addendum: ~115 New Nodes

Organized by gap category. All nodes follow the standard YAML schema. Dependencies reference existing nodes from the base spec and each other.

---

## CATEGORY A: 2000s Cultural & Disaster Texture (14 nodes)

These nodes add the connective tissue that makes the 2000s feel like a lived decade, not just a sequence of geopolitical decisions. Several have surprising downstream cascading effects.

```yaml
# A01: Columbia Shuttle Disaster (2003-02)
id: "2003_columbia"
year_month: "2003-02"
title: "Columbia Shuttle Disaster"
description: >
  Space Shuttle Columbia disintegrates on re-entry. Seven crew killed.
  Accelerates the end of the shuttle program and reshapes NASA's future
  direction — toward Constellation, then cancellation, then commercial crew.
options:
  historical_disaster: 0.45         # Shuttle destroyed; program eventually ends
  averted: 0.25                     # Foam strike detected; crew rescued via ISS
  worse_earlier: 0.10               # Earlier shuttle disaster in 2001 accelerates timeline
  program_cancelled_immediately: 0.20 # Congress kills shuttle program within a year
dependencies: []
key_effects: space_development_index
cascading:
  historical: {2032_moon_base.delayed_2040: "+0.05"}  # Delays NASA's next steps
  averted: {space_development_index: "+0.02", 2032_moon_base.us_only: "+0.05"}
  program_cancelled_immediately: {2032_moon_base.delayed_2040: "+0.08"}

# A02: Indian Ocean Tsunami (2004-12)
id: "2004_tsunami"
year_month: "2004-12"
title: "Indian Ocean Tsunami"
description: >
  9.1 earthquake triggers tsunami killing 230,000 across 14 countries.
  Creates the Indian Ocean early warning system. Reshapes international
  disaster response and aid architecture.
options:
  historical_catastrophe: 0.50      # 230K dead; no warning system existed
  warning_system_existed: 0.15      # Hypothetical early detection; deaths reduced to ~30K
  worse_timing: 0.10                # Hits during peak tourist season; 400K+ dead
  triggers_reform: 0.25             # Historical + leads to major international disaster preparedness
dependencies: []
key_effects: conflict_deaths, global_democracy_index
cascading:
  triggers_reform: {2005_katrina.adequate_response: "+0.05", 2020_covid_response.coordinated_early: "+0.03"}
  # Better disaster preparedness cascades forward

# A03: Hurricane Season 2004 (2004-08)
id: "2004_hurricane_season"
year_month: "2004-08"
title: "Record Hurricane Season"
description: >
  Four major hurricanes hit Florida in six weeks. Exposes FEMA weaknesses
  and sets the stage for the Katrina catastrophe a year later.
options:
  historical_four_storms: 0.50
  mild_season: 0.30                 # Fewer storms; FEMA not tested
  catastrophic_fifth: 0.10          # Category 5 hits Miami directly
  fema_reforms: 0.10                # 2004 storms trigger pre-Katrina reforms
dependencies: []
cascading:
  fema_reforms: {2005_katrina.adequate_response: "+0.15", 2005_katrina.exemplary_response: "+0.10"}
  mild_season: {2005_katrina.catastrophic_failure: "+0.05"} # FEMA untested, complacent

# A04: Beijing Olympics (2008-08)
id: "2008_beijing_olympics"
year_month: "2008-08"
title: "Beijing Olympics"
description: >
  China's global coming-out party. $44B investment. Showcases Chinese
  organizational capability and ambition. Shapes how China sees itself
  and how the world sees China for the next decade.
options:
  historical_success: 0.55          # Spectacular games; China arrives on world stage
  marred_by_protest: 0.15           # Tibet protests dominate coverage
  boycott: 0.10                     # Major Western boycott over human rights
  modest_games: 0.20                # Successful but not transformative
dependencies: [2001_china_wto]
key_effects: china_power_index, us_global_standing
cascading:
  historical_success: {2012_xi_consolidation.historical_consolidation: "+0.05"}
  boycott: {2012_xi_consolidation.reform_faction_wins: "+0.05", china_power_index: "-0.03"}

# A05: Obama Election (2008-11)
id: "2008_obama_election"
year_month: "2008-11"
title: "2008 US Presidential Election"
description: >
  In the base spec, this is implicit (the 2016 node references the prior cycle).
  Making it explicit allows the Obama/McCain choice to affect the 2009-2015
  period independently of the financial crisis.
options:
  obama_wins: 0.55                  # Historical
  mccain_wins: 0.35                 # Financial crisis blame falls on Democrats too
  third_party_factor: 0.05          # Ron Paul independent run
  contested: 0.05
dependencies: [2008_financial_crisis]
  # Worse crisis → Obama more likely
  great_depression_2: {obama_wins: "+0.10", mccain_wins: "-0.10"}
  mild_recession: {mccain_wins: "+0.10", obama_wins: "-0.05"}
key_effects: us_polarization, us_global_standing, racial_justice_index
cascading:
  obama_wins: {2010_arab_spring.broader_success: "+0.05", 2014_blm.historical_wave: "+0.03"}
  mccain_wins: {2015_iran_deal.no_deal: "+0.15", 2015_paris_climate.no_agreement: "+0.10"}

# A06: Haiti Earthquake (2010-01)
id: "2010_haiti"
year_month: "2010-01"
title: "Haiti Earthquake"
description: >
  7.0 earthquake kills 220,000-316,000 in the poorest country in the
  Western Hemisphere. International response is massive but widely
  criticized as ineffective. Shapes development aid debate.
options:
  historical_catastrophe: 0.50
  better_response: 0.20             # More effective aid coordination
  build_back_better: 0.10           # Haiti actually rebuilt with resilient infrastructure
  aid_scandal: 0.20                 # Red Cross/NGO failures dominate narrative
dependencies: [2004_tsunami]
  triggers_reform: {better_response: "+0.10"}
key_effects: latin_america_stability, us_institutional_trust

# A07: Deepwater Horizon (2010-04)
id: "2010_deepwater_horizon"
year_month: "2010-04"
title: "Deepwater Horizon Oil Spill"
description: >
  Largest marine oil spill in history. 11 workers killed, 4.9M barrels
  spilled into Gulf of Mexico. Reshapes drilling regulation and
  accelerates anti-fossil-fuel sentiment.
options:
  historical_spill: 0.45
  prevented_by_regulation: 0.20     # Stricter MMS oversight catches blowout preventer failure
  worse_uncontained: 0.10           # Takes 6+ months to cap; ecological catastrophe
  accelerates_transition: 0.25      # Spill triggers aggressive pivot to renewables
dependencies:
  - node: "2000_election"
    branch: "gore_wins"
    modifies: {prevented_by_regulation: "+0.10", historical_spill: "-0.08"}
key_effects: renewable_energy_share, us_institutional_trust, climate_temp_anomaly
cascading:
  accelerates_transition: {2027_energy_transition.rapid_transition: "+0.05"}
  worse_uncontained: {2015_paris_climate.binding_agreement: "+0.05"} # Galvanizes climate movement

# A08: Occupy Wall Street (2011-09)
id: "2011_occupy"
year_month: "2011-09"
title: "Occupy Wall Street"
description: >
  Protest movement against economic inequality. "We are the 99%."
  Failed to produce policy change but reshaped political vocabulary
  and set the stage for both Sanders and Trump populism.
options:
  historical_fizzle: 0.45           # Protests but no lasting institutional impact
  lasting_movement: 0.15            # Evolves into permanent political force
  policy_wins: 0.10                 # Achieves financial regulation or tax reform
  co_opted: 0.20                    # Energy absorbed into existing parties
  backlash: 0.10                    # Triggers anti-protest legislation
dependencies: [2008_financial_crisis, 2010_euro_crisis]
  great_depression_2: {lasting_movement: "+0.15", policy_wins: "+0.10"}
key_effects: inequality_index, us_polarization
cascading:
  lasting_movement: {2016_us_election.third_party_surge: "+0.05"}
  policy_wins: {inequality_index: "-0.03", 2012_zirp.fiscal_over_monetary: "+0.05"}

# A09: Sandy Hook / Gun Control Inflection (2012-12)
id: "2012_sandy_hook"
year_month: "2012-12"
title: "Sandy Hook / Gun Control"
description: >
  Mass shooting at elementary school kills 26 including 20 children.
  Fails to produce federal gun legislation despite overwhelming public support.
  Crystallizes the gun control gridlock.
options:
  historical_no_legislation: 0.45
  assault_weapons_ban: 0.15         # Manchin-Toomey passes; assault weapons restricted
  no_shooting: 0.15                 # Event doesn't occur (counterfactual)
  cultural_shift: 0.15              # March For Our Lives energy happens 6 years earlier
  backlash_more_guns: 0.10          # Defensive gun purchases spike; NRA strengthens
dependencies: [2008_obama_election]
  mccain_wins: {historical_no_legislation: "+0.10"}
key_effects: us_polarization, us_institutional_trust

# A10: Boston Marathon Bombing (2013-04)
id: "2013_boston_marathon"
year_month: "2013-04"
title: "Boston Marathon Bombing"
description: >
  Pressure cooker bombs at marathon finish line. 3 killed, 264 injured.
  Demonstrates domestic radicalization threat and the "lone wolf" problem.
options:
  historical_attack: 0.50
  plot_disrupted: 0.25              # FBI tips prevent attack
  larger_attack: 0.10               # More sophisticated device; more casualties
  no_attack: 0.15                   # Tsarnaev brothers don't radicalize
dependencies: [2001_911]
  plot_disrupted: {no_attack: "+0.10"} # Better intelligence post-9/11 prevention
key_effects: terrorism_threat_index, surveillance_state_index

# A11: Ebola Outbreak (2014-03)
id: "2014_ebola"
year_month: "2014-03"
title: "West Africa Ebola Outbreak"
description: >
  Largest Ebola outbreak in history. 28,600 cases, 11,325 deaths.
  Exposed weaknesses in global pandemic preparedness — lessons that
  were largely forgotten by the time COVID arrived.
options:
  historical_outbreak: 0.45
  contained_early: 0.25             # WHO responds faster; deaths under 1,000
  global_spread: 0.10               # Ebola reaches major cities outside Africa
  preparedness_legacy: 0.20         # Outbreak triggers lasting pandemic prep investment
dependencies: []
key_effects: global_pandemic_deaths, africa_development_index
cascading:
  preparedness_legacy: {2020_covid_response.coordinated_early: "+0.08"}
  global_spread: {2019_antivax.contained_niche: "+0.05"} # Fear actually drives vaccination

# A12: Malaysian Airlines MH370 (2014-03)
id: "2014_mh370"
year_month: "2014-03"
title: "MH370 Disappearance"
description: >
  Commercial aircraft vanishes without trace. Never found. Reshapes
  aviation tracking requirements worldwide.
options:
  historical_disappearance: 0.50
  found_quickly: 0.20               # Wreckage located within weeks
  pilot_theory_confirmed: 0.10      # Definitive evidence of deliberate action
  triggers_tracking_mandate: 0.20   # Immediate global real-time flight tracking mandate
dependencies: []
key_effects: surveillance_state_index
  # Minor node but adds cultural texture to 2014

# A13: Charlie Hebdo Attack (2015-01)
id: "2015_charlie_hebdo"
year_month: "2015-01"
title: "Charlie Hebdo Attack"
description: >
  Islamist gunmen attack satirical newspaper in Paris. 12 killed.
  Triggers "Je suis Charlie" movement and intensifies European debate
  about Islam, free speech, and multiculturalism.
options:
  historical_attack: 0.45
  attack_prevented: 0.25
  larger_attack: 0.10
  cultural_dialogue: 0.20           # Attack triggers genuine interfaith dialogue
dependencies: [2014_isis, 2003_iraq]
key_effects: eu_cohesion, terrorism_threat_index, misinformation_severity
cascading:
  historical_attack: {2015_paris_attacks.historical_paris: "+0.05"}
  attack_prevented: {2015_paris_attacks.no_major_western_attack: "+0.05"}

# A14: European Refugee Crisis (2015-09)
id: "2015_refugee_crisis"
year_month: "2015-09"
title: "European Refugee Crisis"
description: >
  Over 1 million asylum seekers enter Europe, primarily from Syria.
  Merkel's "Wir schaffen das" decision. Reshapes European politics,
  fuels right-wing populism, and directly contributes to Brexit.
options:
  historical_crisis: 0.40           # 1M+ refugees; Merkel opens borders
  managed_earlier: 0.15             # EU acts preemptively; orderly resettlement
  borders_closed_early: 0.20        # Hungary-style response dominates from start
  larger_crisis: 0.10               # 3M+; EU systems overwhelmed completely
  no_crisis: 0.15                   # Syria conflict resolved before mass displacement
dependencies: [2010_arab_spring, 2003_iraq, 2014_isis]
  diplomatic_resolution (iraq): {no_crisis: "+0.15"}
  broader_success (arab_spring): {no_crisis: "+0.10"}
key_effects: eu_cohesion, global_democracy_index
cascading:
  historical_crisis: {2016_brexit.leave_wins: "+0.08", 2022_european_right.historical_mainstreaming: "+0.08"}
  no_crisis: {2016_brexit.remain_wins: "+0.05", 2022_european_right.contained: "+0.08"}
  larger_crisis: {2016_brexit.leave_wins: "+0.12", 2045_eu_federation.dissolution_begins: "+0.05"}
```

---

## CATEGORY B: 2010s Platform Dynamics (10 nodes)

```yaml
# B01: Twitter as Political Infrastructure (2009-06)
id: "2009_twitter_politics"
year_month: "2009-06"
title: "Twitter Becomes Political Infrastructure"
description: >
  Twitter's role in the Iranian Green Movement (2009) establishes
  social media as political infrastructure. By 2016, it's the primary
  channel for political communication, radicalization, and manipulation.
options:
  historical_political_capture: 0.45 # Twitter becomes the political town square
  remains_niche: 0.20               # Twitter stays a tech/media platform
  moderated_early: 0.15             # Aggressive content moderation from 2012
  decentralized_alternative: 0.10   # Open protocol wins; no single company controls
  government_regulated: 0.10        # FCC-style regulation of political speech on platforms
dependencies: [2004_social_media, 2007_iphone]
key_effects: misinformation_severity, us_polarization
cascading:
  historical_political_capture: {2016_us_election.social_media_influence: "+0.08",
    2016_misinformation.historical_escalation: "+0.08", 2010_arab_spring.social_media_factor: "+0.05"}
  moderated_early: {2016_misinformation.platform_intervention: "+0.10"}

# B02: YouTube Radicalization Pipeline (2012-06)
id: "2012_youtube_radicalization"
year_month: "2012-06"
title: "YouTube Recommendation Radicalization"
description: >
  YouTube's recommendation algorithm begins systematically pushing users
  toward increasingly extreme content. The "rabbit hole" effect radicalizes
  millions over the next decade, from alt-right to QAnon to anti-vax.
options:
  historical_radicalization: 0.45   # Algorithm optimizes for engagement → extremism
  algorithm_fixed: 0.15             # YouTube identifies and fixes the pipeline by 2015
  worse_pipeline: 0.10              # Radicalization accelerates into real-world violence earlier
  competitor_breaks_model: 0.15     # TikTok-style competitor without the same problem
  regulated: 0.15                   # FTC investigation forces algorithmic changes
dependencies: [2004_social_media, 2006_cloud]
key_effects: misinformation_severity, us_polarization, terrorism_threat_index
cascading:
  historical_radicalization: {2016_misinformation.historical_escalation: "+0.08",
    2021_jan6.worse_violence: "+0.03", 2019_antivax.historical_growing: "+0.05"}
  algorithm_fixed: {2016_misinformation.historical_escalation: "-0.05"}

# B03: Death of Local News (2010-01)
id: "2010_local_news_death"
year_month: "2010-01"
title: "Collapse of Local Journalism"
description: >
  Craigslist kills classified ad revenue. Google/Facebook capture digital
  ad spending. Local newspapers close at the rate of 2 per week.
  "News deserts" cover 1/3 of US counties by 2020. Arguably the single
  largest structural driver of polarization — without local accountability
  journalism, national outrage media fills the void.
options:
  historical_collapse: 0.50         # 2,500+ newspapers close 2005-2030
  public_funding_saves: 0.10        # BBC-model public funding for local news
  platform_revenue_sharing: 0.15    # Google/Facebook forced to share revenue with publishers
  nonprofit_model_wins: 0.15        # ProPublica-style nonprofit journalism scales
  slow_decline: 0.10                # Decline is gradual; some local news survives
dependencies: [2004_social_media, 2006_cloud]
key_effects: misinformation_severity (+0.08), us_polarization (+0.06), us_institutional_trust (-0.05)
cascading:
  historical_collapse: {2016_misinformation.historical_escalation: "+0.08",
    2016_us_election.anti_establishment: "+0.03", 2018_populism.historical_global_wave: "+0.03"}
  public_funding_saves: {misinformation_severity: "-0.05", us_institutional_trust: "+0.03"}

# B04: Streaming Wars / Media Fragmentation (2013-02)
id: "2013_streaming"
year_month: "2013-02"
title: "Streaming and Media Fragmentation"
description: >
  Netflix original content (House of Cards, 2013) marks the end of
  shared media experiences. The monoculture fractures into niches.
  People stop watching the same news, same shows, same reality.
options:
  historical_fragmentation: 0.50
  shared_experiences_persist: 0.15  # Broadcast TV remains dominant longer
  hyper_fragmentation: 0.15         # Algorithmic personalization creates individual realities
  public_media_strengthened: 0.10   # PBS/BBC model scales; shared reference points maintained
  creator_economy: 0.10             # Individual creators replace institutions entirely
dependencies: [2006_cloud, 2007_iphone]
key_effects: misinformation_severity, us_polarization
cascading:
  hyper_fragmentation: {2016_misinformation.epistemic_collapse: "+0.05"}
  public_media_strengthened: {misinformation_severity: "-0.03"}

# B05: Instagram and Body Image Crisis (2012-04)
id: "2012_instagram"
year_month: "2012-04"
title: "Instagram / Visual Social Media"
description: >
  Facebook acquires Instagram. Visual social media creates unprecedented
  body image pressure, particularly for teen girls. Internal Facebook
  research (later leaked) shows Instagram is "toxic" for teen mental health.
options:
  historical_toxicity: 0.45
  stays_independent: 0.15           # Instagram not acquired; develops differently
  age_restrictions_enforced: 0.15   # Under-16 ban actually enforced
  design_for_wellbeing: 0.15        # Platform redesigned to reduce comparison
  backlash_kills_growth: 0.10       # Youth reject visual social media
dependencies: [2004_social_media, 2007_iphone]
key_effects: us_life_expectancy_delta, gender_equity_index
cascading:
  historical_toxicity: {2020_mental_health.historical_crisis: "+0.05"}
  age_restrictions_enforced: {2020_mental_health.resilience: "+0.05"}

# B06: Podcast Revolution (2014-10)
id: "2014_podcasts"
year_month: "2014-10"
title: "Podcast Revolution (Serial)"
description: >
  Serial podcast marks the mainstream arrival of podcasting. By 2020,
  podcasts are a major political influence channel — Joe Rogan, Ben Shapiro,
  NPR Politics. Long-form audio becomes an alternative to algorithmic feeds.
options:
  historical_growth: 0.50
  niche_medium: 0.25                # Podcasts stay niche; talk radio remains dominant
  regulated_as_media: 0.10          # Podcasts subject to same rules as broadcast
  democratizing_force: 0.15         # Podcasts genuinely diversify media landscape
dependencies: [2007_iphone]
key_effects: misinformation_severity, us_polarization
  # Complex: podcasts both increase AND decrease misinformation depending on which ones

# B07: Gamergate / Online Harassment as Political Tool (2014-08)
id: "2014_gamergate"
year_month: "2014-08"
title: "Gamergate / Online Harassment Weaponization"
description: >
  Gamergate controversy establishes the playbook for coordinated online
  harassment campaigns as political tools. The tactics pioneered here —
  doxxing, brigading, manufactured outrage — become standard in 2016
  election interference and beyond.
options:
  historical_weaponization: 0.45
  contained_to_gaming: 0.20         # Harassment stays in gaming communities
  platform_crackdown: 0.15          # Reddit/Twitter crack down; tactics don't spread
  early_antidote: 0.10              # Counter-harassment tools developed early
  worse_radicalization: 0.10        # Pipeline to political violence established earlier
dependencies: [2004_social_media, 2012_youtube_radicalization]
key_effects: gender_equity_index, misinformation_severity
cascading:
  historical_weaponization: {2016_us_election.social_media_influence: "+0.03",
    2017_metoo.backlash_dominant: "+0.03"}

# B08: WhatsApp / Encrypted Messaging Politics (2016-01)
id: "2016_whatsapp_politics"
year_month: "2016-01"
title: "WhatsApp as Political Misinformation Vector"
description: >
  In India, Brazil, and developing world, WhatsApp groups become
  the primary vector for political misinformation. End-to-end encryption
  makes moderation impossible. Lynchings in India directly linked to
  WhatsApp rumors.
options:
  historical_misinformation_vector: 0.45
  moderation_tools_added: 0.15      # WhatsApp adds forwarding limits, fact-check labels
  decentralized_moderation: 0.15    # Community-based fact-checking at scale
  unencrypted_alternative_wins: 0.10 # Telegram-style platform without E2E dominates
  regulation_forces_transparency: 0.15
dependencies: [2004_social_media, 2007_iphone]
key_effects: misinformation_severity, global_democracy_index, india_power_index

# B09: Fake News Industry / Macedonian Troll Farms (2016-06)
id: "2016_fake_news_industry"
year_month: "2016-06"
title: "Fake News as Industry"
description: >
  Teenagers in Veles, Macedonia discover that pro-Trump fake news
  generates massive ad revenue. The fake news industry scales globally.
  Russia's IRA runs thousands of fake American social media accounts.
options:
  historical_industry: 0.40
  detected_and_shut_down: 0.15      # Platforms detect and remove before election
  larger_operation: 0.10            # Chinese/Iranian operations join Russian
  no_profitable_model: 0.20         # Platform changes make fake news unprofitable
  counter_information_wins: 0.15    # Fact-checking scales faster than misinformation
dependencies: [2004_social_media, 2009_twitter_politics, 2012_youtube_radicalization]
key_effects: misinformation_severity, global_democracy_index
cascading:
  historical_industry: {2016_us_election.trump_wins: "+0.03",
    2016_brexit.leave_wins: "+0.03", 2020_us_election.close_contested: "+0.03"}
  detected_and_shut_down: {2016_us_election.clinton_wins: "+0.03"}

# B10: Algorithmic Content Moderation Debate (2019-03)
id: "2019_content_moderation"
year_month: "2019-03"
title: "Content Moderation at Scale"
description: >
  Christchurch mosque shooting livestreamed on Facebook. 1.5M copies
  uploaded in 24 hours. Forces the question: can platforms moderate
  content at the scale of billions of posts per day?
options:
  historical_struggling: 0.45       # Platforms try and mostly fail
  ai_moderation_works: 0.15         # AI-based moderation achieves 95%+ accuracy
  government_mandates: 0.15         # Christchurch Call leads to binding regulation
  decentralization_wins: 0.10       # Moderation impossible; decentralized platforms grow
  overmoderation: 0.15              # Aggressive moderation suppresses legitimate speech
dependencies: [2004_social_media, 2012_youtube_radicalization, 2018_facebook_cambridge]
key_effects: internet_freedom_index, misinformation_severity
```

---

## CATEGORY C: Space Timeline (12 nodes)

```yaml
# C01: SpaceX Falcon 9 / Reusable Rockets (2010-06)
id: "2010_spacex_falcon9"
year_month: "2010-06"
title: "SpaceX and Reusable Rocketry"
description: >
  Falcon 9 first flight. First successful landing 2015. Reduces launch
  costs by 10x. Without reusable rockets, nothing else in the space
  timeline happens.
options:
  historical_success: 0.50          # SpaceX succeeds; costs plummet
  delayed_5_years: 0.15             # Technical challenges delay to ~2015
  spacex_fails: 0.10                # Company fails; ULA/Arianespace continue at high cost
  multiple_competitors: 0.15        # Blue Origin, Rocket Lab achieve parity
  government_only: 0.10             # Private space doesn't take off; NASA/ESA dominate
key_effects: space_development_index
cascading:
  historical_success: {2032_moon_base.us_only: "+0.05", 2040_mars_mission.successful_landing: "+0.08"}
  spacex_fails: {2032_moon_base.delayed_2040: "+0.15", 2040_mars_mission.delayed_2050: "+0.15"}
  # This is a keystone node — everything downstream depends on it

# C02: ISS End of Life Decision (2024-01)
id: "2024_iss_deorbit"
year_month: "2024-01"
title: "ISS Transition"
description: >
  ISS approaching end of life. Transition to commercial stations
  (Axiom, Orbital Reef) or gap in human spaceflight capability.
options:
  smooth_transition: 0.30           # Commercial stations ready; seamless handoff
  capability_gap: 0.35              # 3-5 year gap with no space station
  extended_iss: 0.15                # ISS life extended to 2035
  china_station_dominant: 0.15      # Tiangong becomes the only operational station
  no_replacement: 0.05              # No commercial station materializes
dependencies: [2010_spacex_falcon9]
key_effects: space_development_index, us_global_standing, china_power_index

# C03: Starship Orbital (2025-06)
id: "2025_starship"
year_month: "2025-06"
title: "Starship Reaches Orbit"
description: >
  SpaceX Starship achieves full orbital flight and landing. If successful,
  it's the largest and cheapest rocket ever built — enabling Moon bases,
  Mars missions, and orbital manufacturing.
options:
  on_schedule: 0.30                 # Full orbital success by 2025
  delayed_2028: 0.30                # Technical challenges delay 3 years
  partial_success: 0.15             # Orbital but landing fails; iterates
  program_cancelled: 0.05           # Catastrophic failure ends program
  competitor_beats: 0.10            # Blue Origin or Chinese equivalent succeeds first
  revolutionary_success: 0.10       # Exceeds expectations; rapid iteration
dependencies: [2010_spacex_falcon9]
key_effects: space_development_index
cascading:
  on_schedule: {2032_moon_base.us_china_bases: "+0.10", 2040_mars_mission.successful_landing: "+0.10"}
  program_cancelled: {2032_moon_base.delayed_2040: "+0.20", 2040_mars_mission.cancelled: "+0.10"}

# C04: Artemis Program (2026-01)
id: "2026_artemis"
year_month: "2026-01"
title: "Artemis Lunar Landing"
description: >
  NASA's return to the Moon. First woman and first person of color
  on the lunar surface. Whether it leads to sustained presence
  depends on funding and political will.
options:
  successful_landing: 0.30
  delayed_2030: 0.30
  cancelled: 0.10
  international_mission: 0.15       # Becomes joint US/ESA/JAXA mission
  china_beats_artemis: 0.15         # China lands first; Artemis responds
dependencies: [2025_starship, 2024_us_election]
key_effects: space_development_index, us_global_standing
cascading:
  china_beats_artemis: {2032_moon_base.china_only: "+0.10", us_global_standing: "-0.03"}

# C05-C08: Additional Space Nodes
# C05: Lunar Economy Begins (2034) — water mining, He-3, tourism
# C06: Space Tourism Mainstream (2030) — Blue Origin, Virgin, SpaceX civilian flights
# C07: Space Debris Cleanup Industry (2031) — response to growing Kessler risk
# C08: Cislunar Economy (2038) — Earth-Moon economic zone
# Each follows standard schema with 4-5 branches and cross-dependencies

# C09-C12: Future Space (already in base spec, but adding detail)
# C09: Mars Communication Infrastructure (2042) — delay-tolerant networking
# C10: In-Space Manufacturing (2045) — zero-G manufacturing advantages
# C11: Space Solar Power (2050) — beamed energy from orbit
# C12: Asteroid Redirect Mission (2048) — moving asteroids for mining
```

---

## CATEGORY D: Biotech & Health (12 nodes)

```yaml
# D01: Human Genome Project Aftermath (2003-04)
id: "2003_genome_aftermath"
year_month: "2003-04"
title: "Post-Genome Era"
description: >
  Human Genome Project completed. The $1000 genome is a decade away.
  Personal genomics, pharmacogenomics, and genetic privacy debates begin.
options:
  historical_slow_translation: 0.45 # Genomics advances but clinical translation is slow
  rapid_personalized_medicine: 0.15 # Personalized medicine arrives by 2015
  genetic_privacy_crisis: 0.15      # Genetic discrimination becomes major issue
  open_science_model: 0.15          # Open access to genetic data accelerates research
  overhyped_stalls: 0.10            # Funding dries up when miracle cures don't materialize
key_effects: us_life_expectancy_delta, inequality_index

# D02: Antibiotic Resistance Crisis (2015-05)
id: "2015_antibiotic_resistance"
year_month: "2015-05"
title: "Antibiotic Resistance Escalation"
description: >
  WHO declares antimicrobial resistance a global health emergency.
  Without new antibiotics, routine surgeries become life-threatening.
  By 2050, AMR could kill 10M/year — more than cancer.
options:
  historical_slow_crisis: 0.40      # Resistance grows; new drugs trickle
  manhattan_project_for_antibiotics: 0.10 # Global crash program; new drug classes discovered
  phage_therapy_scales: 0.15        # Bacteriophage therapy becomes viable alternative
  superbug_pandemic: 0.10           # Pan-resistant pathogen causes major outbreak
  market_incentives_work: 0.15      # Pull incentives create sustainable antibiotic pipeline
  no_progress: 0.10                 # No new antibiotics; surgery becomes dangerous
key_effects: global_pandemic_deaths, us_life_expectancy_delta
cascading:
  superbug_pandemic: {global_pandemic_deaths: "+1000000"}
  manhattan_project: {us_life_expectancy_delta: "+0.5"}

# D03: mRNA Platform Discovery (2020-01)
id: "2020_mrna_platform"
year_month: "2020-01"
title: "mRNA Vaccine Platform"
description: >
  COVID forces mRNA technology from lab curiosity to mass deployment
  in record time. But the platform's potential extends far beyond COVID —
  cancer vaccines, malaria, HIV, genetic diseases.
options:
  historical_covid_only: 0.35       # mRNA used for COVID; other applications slow
  platform_revolution: 0.25         # mRNA becomes universal vaccine platform by 2030
  safety_concerns_slow: 0.15        # Long-term concerns reduce adoption
  cancer_vaccine_breakthrough: 0.15 # mRNA cancer vaccines work; transformative
  developing_world_access: 0.10     # IP waivers enable global mRNA manufacturing
dependencies: [2019_covid_emergence, 2020_covid_response]
conditional: "2019_covid_emergence != no_pandemic"
key_effects: us_life_expectancy_delta, global_pandemic_deaths, inequality_index
cascading:
  cancer_vaccine_breakthrough: {2058_life_extension.significant_extension: "+0.10"}
  platform_revolution: {2029_pandemic_2.contained_quickly: "+0.10"}

# D04-D12: Additional Biotech Nodes
# D04: Gain-of-Function Research Debate (2014) — lab leak risk, dual-use research
# D05: CRISPR Baby Scandal (2018) — He Jiankui; ethics of germline editing
# D06: Synthetic Biology Regulation (2022) — DNA synthesis screening, biosecurity
# D07: Longevity Research Boom (2025) — senolytics, rapamycin, caloric restriction mimetics
# D08: Brain-Computer Interface Trials (2025) — Neuralink, Synchron, clinical applications
# D09: Pandemic Preparedness Treaty (2024) — WHO pandemic accord negotiations
# D10: Alzheimer's Treatment Breakthrough (2027) — disease-modifying treatments
# D11: Artificial Wombs (2035) — ectogenesis research; reproductive technology
# D12: Human Genetic Enhancement Debate (2038) — polygenic screening, embryo selection at scale
```

---

## CATEGORY E: Energy Detail (10 nodes)

```yaml
# E01: Fracking Revolution (2008-01)
id: "2008_fracking"
year_month: "2008-01"
title: "US Shale / Fracking Revolution"
description: >
  Hydraulic fracturing transforms US from energy importer to the world's
  largest oil and gas producer. Geopolitical implications are enormous —
  reduces Middle East leverage, delays renewable transition, but also
  enables coal-to-gas switching that reduces emissions.
options:
  historical_boom: 0.50             # US becomes energy independent by 2019
  regulated_heavily: 0.15           # Environmental concerns limit fracking
  technology_fails: 0.10            # Shale wells deplete faster than expected
  earlier_boom: 0.10                # Fracking scales 3 years earlier
  environmental_catastrophe: 0.15   # Major groundwater contamination event
dependencies: [2000_election]
  gore_wins: {regulated_heavily: "+0.15", historical_boom: "-0.10"}
key_effects: renewable_energy_share, climate_temp_anomaly, us_global_standing, middle_east_stability
cascading:
  historical_boom: {2022_russia_ukraine.eu_energy_dependence: "-0.05",
    2027_energy_transition.fossil_resurgence: "+0.05"}
  regulated_heavily: {renewable_energy_share: "+0.02", climate_temp_anomaly: "-0.02"}

# E02: Solyndra / Solar Cost Curve (2011-09)
id: "2011_solar_revolution"
year_month: "2011-09"
title: "Solar Cost Revolution"
description: >
  Solyndra bankruptcy embarrasses US solar policy, but Chinese manufacturing
  drives solar costs down 90% over the decade — the fastest cost decline
  of any energy technology in history.
options:
  historical_cost_collapse: 0.50    # Solar drops below coal by 2020
  slower_decline: 0.20              # Cost parity delayed to 2028
  manufacturing_distributed: 0.10   # Non-Chinese manufacturing develops; slower but resilient
  accelerated_by_policy: 0.15       # Carbon pricing accelerates adoption
  trade_wars_slow: 0.05             # Tariffs on Chinese panels slow deployment
dependencies: [2001_china_wto]
key_effects: renewable_energy_share, climate_temp_anomaly
cascading:
  historical_cost_collapse: {2027_energy_transition.rapid_transition: "+0.05",
    2025_climate_tipping.accelerated_action: "+0.03"}

# E03: Battery Storage Breakthrough (2017-07)
id: "2017_battery_storage"
year_month: "2017-07"
title: "Battery Storage Revolution"
description: >
  Tesla Powerwall and grid-scale battery storage enable intermittent
  renewables to provide baseload power. The missing piece for 100%
  renewable grids.
options:
  historical_progress: 0.45         # Steady cost decline; grid-scale by 2025
  breakthrough_chemistry: 0.15      # Solid-state or sodium-ion dramatically cheaper
  slower_than_hoped: 0.20           # Lithium supply constraints limit scaling
  alternative_storage: 0.10         # Hydrogen, compressed air, or gravity storage wins
  china_dominance: 0.10             # China controls 90% of battery supply chain
dependencies: [2011_solar_revolution, 2001_china_wto]
key_effects: renewable_energy_share, supply_chain_resilience
cascading:
  breakthrough_chemistry: {2027_energy_transition.rapid_transition: "+0.08"}
  china_dominance: {supply_chain_resilience: "-0.05", 2018_trade_war.full_decoupling: "+0.03"}

# E04: Fukushima's Energy Legacy (already exists — adding downstream detail)
# E05: Paris Agreement Implementation (2016-2020) — NDC submissions, ratchet mechanism
# E06: US Rejoins/Leaves Paris (2017/2021) — Trump withdrawal, Biden return
# E07: European Green Deal (2019-12) — EU net-zero by 2050 commitment
# E08: Grid Modernization Crisis (2025) — aging infrastructure meets renewable integration
# E09: Fusion Ignition (2022-12) — NIF achievement; timeline to commercial fusion
# E10: Hydrogen Economy Viability (2028) — green hydrogen cost curve; infrastructure buildout

# E09 deserves full treatment:
id: "2022_fusion_ignition"
year_month: "2022-12"
title: "Fusion Ignition Achievement"
description: >
  National Ignition Facility achieves fusion ignition — more energy out
  than laser energy in. But commercial fusion is decades away. Or is it?
options:
  historical_milestone: 0.40        # Scientific success; commercial fusion 2050+
  accelerated_timeline: 0.15        # Private fusion companies (Commonwealth, TAE) achieve breakeven by 2035
  dead_end: 0.15                    # Ignition was a one-off; can't be economically scaled
  manhattan_project_2: 0.10         # Government crash program like Apollo
  private_sector_wins: 0.20         # Startup-driven; first commercial reactor 2040
dependencies: [2012_deep_learning]
  # AI accelerates plasma simulation and reactor design
  historical_gpu_revolution: {accelerated_timeline: "+0.05"}
key_effects: renewable_energy_share, climate_temp_anomaly
cascading:
  accelerated_timeline: {2027_energy_transition.nuclear_renaissance: "+0.10",
    2025_climate_tipping.technological_breakthrough: "+0.08"}
  manhattan_project_2: {climate_temp_anomaly: "-0.05", global_gdp_growth_modifier: "*1.01"}
```

---

## CATEGORY F: Cyber & Digital (12 nodes)

```yaml
# F01: Stuxnet (already exists) — but adding detail
# F02: Sony Hack / North Korea (2014-11)
id: "2014_sony_hack"
year_month: "2014-11"
title: "Sony Pictures Hack"
description: >
  North Korea hacks Sony Pictures over "The Interview." First major
  nation-state hack of a corporation for political purposes. Sets
  precedent for state-sponsored corporate cyber warfare.
options:
  historical_hack: 0.50
  deterred: 0.20                    # US cyber deterrence prevents attack
  larger_attack: 0.10               # Attack destroys data; Sony permanently damaged
  diplomatic_resolution: 0.15       # Back-channel prevents hack
  triggers_cyber_norms: 0.05        # Attack triggers international cyber norms agreement
dependencies: [2010_stuxnet]
key_effects: global_cyber_damage_annual_b

# F03: Ransomware Economy (2016-01)
id: "2016_ransomware"
year_month: "2016-01"
title: "Ransomware as Business Model"
description: >
  CryptoLocker and its successors create a billion-dollar criminal
  economy. Hospitals, cities, pipelines held hostage. Cryptocurrency
  enables untraceable payments.
options:
  historical_epidemic: 0.45         # Ransomware grows to $20B+/year industry
  contained_by_2020: 0.15           # Law enforcement disrupts major groups
  critical_infrastructure_attack: 0.15 # Hospital attack kills patients; triggers crackdown
  crypto_regulation_stops_it: 0.10  # Can't pay ransoms without anonymous crypto
  ransomware_insurance_normalizes: 0.15 # Insurance makes it a routine business cost
dependencies: [2013_crypto, 2010_stuxnet]
key_effects: global_cyber_damage_annual_b, us_institutional_trust
cascading:
  critical_infrastructure_attack: {2017_wannacry.major_infrastructure_attack: "+0.10"}
  crypto_regulation_stops_it: {global_cyber_damage_annual_b: "-5.0"}

# F04: Colonial Pipeline (2021-05)
id: "2021_colonial_pipeline"
year_month: "2021-05"
title: "Colonial Pipeline Ransomware"
description: >
  Ransomware shuts down the largest US fuel pipeline. Panic buying,
  gas shortages on East Coast. Demonstrates cyber-physical vulnerability.
options:
  historical_shutdown: 0.45
  prevented: 0.20
  worse_cascading: 0.10             # Multiple pipelines hit simultaneously
  triggers_mandate: 0.25            # Federal cybersecurity mandate for critical infrastructure
dependencies: [2016_ransomware, 2020_solarwinds]
key_effects: supply_chain_resilience, global_cyber_damage_annual_b

# F05: Deepfakes (2018-12)
id: "2018_deepfakes"
year_month: "2018-12"
title: "Deepfake Technology Proliferation"
description: >
  AI-generated fake video becomes convincing enough to fool humans.
  Implications for elections, evidence, trust, and the very concept
  of visual truth.
options:
  historical_growing_threat: 0.40
  detection_keeps_pace: 0.20        # AI detection tools stay ahead of generation
  election_deepfake_crisis: 0.10    # Deepfake of candidate influences major election
  authentication_standard: 0.15     # C2PA/content authenticity standards adopted widely
  deepfake_normalized: 0.15         # Society adapts; video evidence loses legal weight
dependencies: [2012_deep_learning, 2016_misinformation]
key_effects: misinformation_severity, global_democracy_index
cascading:
  election_deepfake_crisis: {2020_us_election.close_contested: "+0.05",
    global_democracy_index: "-0.03"}

# F06: Digital Identity Systems (2020-01)
id: "2020_digital_identity"
year_month: "2020-01"
title: "Digital Identity Infrastructure"
description: >
  India's Aadhaar, EU's eIDAS, various national digital ID systems.
  Enables financial inclusion and government services but also
  enables surveillance and exclusion.
options:
  fragmented_national: 0.40         # Each country builds its own system
  interoperable_global: 0.10        # International digital ID standard
  privacy_preserving: 0.15          # Zero-knowledge proofs enable ID without surveillance
  surveillance_tool: 0.20           # Digital ID becomes primary surveillance mechanism
  rejected: 0.15                    # Privacy backlash prevents adoption
dependencies: [2013_snowden, 2019_quantum]
key_effects: surveillance_state_index, internet_freedom_index, inequality_index
cascading:
  surveillance_tool: {surveillance_state_index: "+0.08"}
  privacy_preserving: {internet_freedom_index: "+0.03"}

# F07-F12: Additional Cyber/Digital Nodes
# F07: Zero-Day Market (2015) — government stockpiling vs disclosure debate
# F08: NotPetya (2017) — most destructive cyber attack in history, $10B damage
# F09: SolarWinds (already exists — adding detail)
# F10: Log4j / Supply Chain Vulnerability (2021-12) — open source security crisis
# F11: AI-Powered Cyber Attacks (2024) — LLMs used for phishing, code exploitation
# F12: Post-Quantum Cryptography Transition (2026) — migrating before quantum breaks RSA
```

---

## CATEGORY G: Additional Cross-Domain Nodes (15 nodes)

These fill remaining gaps and add cross-domain connections.

```yaml
# G01: Pope Francis Election (2013-03) — first Latin American pope; climate encyclical
# G02: Flint Water Crisis (2014-04) — infrastructure decay, environmental racism
# G03: Panama Papers (2016-04) — global tax evasion exposed; wealth inequality
# G04: Puerto Rico Hurricane Maria (2017-09) — colonial infrastructure failure
# G05: Jamal Khashoggi Murder (2018-10) — Saudi relations, press freedom
# G06: Australian Bushfires (2019-12) — climate change visual; "new normal"
# G07: George Floyd / 2020 Racial Reckoning (2020-05) — separate from BLM node; global impact
# G08: Suez Canal Blockage (2021-03) — supply chain fragility visualized
# G09: James Webb Space Telescope (2022-07) — scientific inspiration; cosmic perspective
# G10: SVB / Banking Wobble (2023-03) — ZIRP hangover; regional bank fragility
# G11: Lahaina / Climate Disasters New Normal (2023-08) — developed-world climate impacts
# G12: Gaza Conflict Escalation (2023-10) — reshapes Middle East trajectory, campus protests
# G13: Mpox / Disease X Preparedness Test (2024-08) — tests post-COVID preparedness
# G14: US TikTok Ban Saga (2024-01) — tech sovereignty, free speech, US-China
# G15: OpenAI Board Crisis (2023-11) — AI governance in microcosm; safety vs deployment debate
```

---

## Updated Node Count

| Category | Existing | New | Total |
|----------|---------|-----|-------|
| Base historical | 102 | — | 102 |
| Future era | 127 | — | 127 |
| Diversity patch | — | 12 | 12 |
| A: 2000s texture | — | 14 | 14 |
| B: 2010s platforms | — | 10 | 10 |
| C: Space timeline | — | 12 | 12 |
| D: Biotech/health | — | 12 | 12 |
| E: Energy | — | 10 | 10 |
| F: Cyber/digital | — | 12 | 12 |
| G: Cross-domain | — | 15 | 15 |
| Shock events | — | 6 | 6 |
| **TOTAL** | **229** | **~103** | **~332** |

*Some abbreviated nodes (C05-C08, D04-D12, E04-E08, F07-F12, G01-G15) need full YAML expansion during implementation, which will bring the effective total to approximately 350-360 playable nodes.*

---

## New Dependency Connections (Key Additions)

These new nodes create ~150 additional edges in the dependency graph, primarily cross-domain:

```
2010_local_news_death → 2016_misinformation (major)
2012_youtube_radicalization → 2021_jan6 (radicalization pipeline)
2008_fracking → 2022_russia_ukraine (energy independence)
2010_spacex_falcon9 → 2032_moon_base, 2040_mars_mission (keystone)
2015_antibiotic_resistance → 2029_pandemic_2 (AMR + pandemic interaction)
2015_refugee_crisis → 2016_brexit, 2022_european_right (direct link)
2020_mrna_platform → 2029_pandemic_2, 2058_life_extension (platform effect)
2011_solar_revolution → 2027_energy_transition (cost curve)
2017_battery_storage → 2027_energy_transition (storage enables renewables)
2022_fusion_ignition → 2027_energy_transition (potential game-changer)
2016_ransomware → 2017_wannacry (enabling economy)
2018_deepfakes → 2020_us_election (trust erosion)
2014_gamergate → 2016_us_election, 2017_metoo (harassment playbook)
2008_obama_election → 2015_iran_deal, 2014_blm (policy + cultural)
2015_refugee_crisis → 2016_brexit (CRITICAL missing link now added)
```

The refugee crisis → Brexit connection is arguably the single most important missing edge in the original graph. Without it, Brexit's probability distribution doesn't respond to Middle East outcomes, which misses a major real-world causal chain.
