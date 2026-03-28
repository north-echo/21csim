# 21csim — Future Improvements & Feature Roadmap

---

## Phase 6: Post-Launch Enhancements (Months 3-6)

### 6.1 Community Node Contributions

Open the node graph to community contributions. Anyone can propose a new node or calibrate existing probabilities via GitHub PR.

**Node submission template:**
```yaml
# .github/ISSUE_TEMPLATE/new-node.yaml
name: Propose New Node
body:
  - id: node_yaml
    label: "Node YAML (follow schema in CONTRIBUTING.md)"
  - id: sources
    label: "Sources for probability estimates"
  - id: dependencies
    label: "Which existing nodes does this connect to?"
  - id: rationale
    label: "Why should this node exist? What outcome diversity does it add?"
```

**Calibration debates:** Open GitHub Discussions threads for contested probability weights. "Should the Iraq invasion probability under Gore really be 0.13, or is 0.20 more realistic?" Domain experts (historians, political scientists, climate researchers) can weigh in with sourced arguments. Changes merged via PR with community review.

**Node attribution:** Each node YAML file includes an `author` field. Contributors get credited in the node catalog on the website and in the CLI's `--credits` output.

---

### 6.2 Custom Scenario Files

The engine already reads YAML. Expose this as a user-facing feature — anyone can create an entirely different scenario file and run it.

**Built-in scenarios shipped with the tool:**
- `21st-century.yaml` — the default (2000-2100, 350+ nodes)
- `cold-war.yaml` — 1945-1991 counterfactual
- `wwii.yaml` — 1933-1945 with branching decisions
- `personal.yaml` — template for life-decision simulation (career, relationships, health)

**Community scenarios:**
- `roman-empire.yaml` — What if Rome never fell?
- `industrial-revolution.yaml` — 1750-1900 technology and empire
- `us-civil-war.yaml` — 1860-1877 reconstruction paths
- `climate-only.yaml` — Deep simulation of climate decisions only, 2000-2200

```bash
$ 21csim run --scenario cold-war.yaml --seed 42
$ 21csim run --scenario community/roman-empire.yaml --seed 7714
```

**Scenario marketplace:** A page on 21csim.com where community-created scenarios can be browsed, rated, and downloaded.

---

### 6.3 Multiplayer / Collaborative Mode

Multiple people watch the same seed unfold simultaneously, each making predictions about what comes next before each node resolves. Track who predicted most accurately.

```bash
$ 21csim host --seed 42 --port 8080
# Opens a local web server; others connect via browser

$ 21csim join http://192.168.1.10:8080
```

**Web version:** A "Watch Party" mode on 21csim.com where a shareable link lets multiple people watch the same run with a synchronized playback and a chat sidebar.

**Prediction scoring:** Before each node resolves, participants predict which branch will fire. Points awarded for correct predictions, weighted by branch improbability (predicting the 8% outcome is worth more than predicting the 50% outcome).

---

### 6.4 "What If I Were President?" Mode

A special interactive mode where the user makes the decisions at each geopolitical node (Iraq, Afghanistan, COVID response, etc.) while the simulation handles everything else probabilistically. Shows how your decisions cascade through the century.

```bash
$ 21csim play --role us_president --seed 42

2003-03: Iraq War Decision
  Intelligence suggests WMDs in Iraq. Congress is pressuring for action.
  Your approval rating is 68% after 9/11. Allies are divided.
  
  What do you do?
  [1] Full invasion with coalition of the willing
  [2] Limited air strikes on suspected WMD sites
  [3] Continue UN inspections; no military action
  [4] Delayed invasion with broader coalition
  
  > 3

  You chose: Diplomatic resolution
  [simulation continues with your choice locked in, everything else sampled]
```

**Web version:** The viewer pauses at decision nodes, presenting the player with the same options and context. Narration adjusts to address the player directly.

---

### 6.5 Advanced Analytics Dashboard

Expand the `/findings` page into a full interactive analytics suite:

- **Scatter plots:** Any two world-state dimensions plotted against each other across 10K runs
- **Parallel coordinates:** Trace how all dimensions evolve simultaneously across a run
- **Cluster analysis:** K-means clustering of final world states; identify the 5-7 "archetypal centuries"
- **Node influence heatmap:** Which nodes most affect which dimensions (full correlation matrix)
- **Path explorer:** Click through the most common branch sequences leading to each verdict
- **Decade snapshots:** Compare world state distributions at 2030, 2050, 2070, 2100

---

## Phase 7: Platform Features (Months 6-12)

### 7.1 User Accounts and Saved Runs

Optional (never required) user accounts for:
- Saving favorite runs with personal notes
- Building playlists of curated seeds ("The Five Best Catastrophe Runs")
- Tracking prediction accuracy across multiplayer sessions
- Contributing nodes under a persistent identity

**Implementation:** Cloudflare D1 (serverless SQLite) + Cloudflare Workers for auth. No external auth provider — email magic links or GitHub OAuth.

---

### 7.2 AI Narrator v2: Voice Synthesis

Generate spoken narration using text-to-speech. The narrator reads the prose aloud during cinema mode — like listening to an audiobook of alternate history.

**Local (free):** Use Piper TTS (open source, runs locally) with a male British narrator voice. Narration audio generated alongside text during `export-library`.

**Premium:** ElevenLabs or Coqui for higher-quality voices. Optional, user brings their own API key.

**Web viewer:** `<audio>` elements synced to the typewriter text reveal. The voice reads each narration passage as it types onto screen.

```bash
$ 21csim run --seed 42 --narrate --voice

# Narration appears on screen AND is read aloud
```

---

### 7.3 VR / Spatial Mode

A WebXR version of the viewer for VR headsets. The timeline becomes a spatial experience — you stand inside a dark room as events materialize around you as floating text and glowing nodes. Era transitions are full environmental shifts (lighting, ambient sound, spatial audio cues).

**MVP:** Use A-Frame or Three.js with WebXR. The branch timeline becomes a 3D path you walk along. Nodes are glowing spheres you can inspect by looking at them. World state is a surrounding dashboard of floating panels.

**This is the long-shot feature** but it would be genuinely unprecedented — standing inside an alternate century as it unfolds around you in VR.

---

### 7.4 Educational Mode

A structured learning experience for classrooms:

- **Guided scenarios:** Pre-built lesson plans ("The Iraq War: Counterfactual Analysis")
- **Quiz mode:** Students predict outcomes before each node resolves
- **Essay prompts:** After a run completes, generate essay questions about the causal chains
- **Comparison assignments:** "Run seeds 42 and 7714. Write 500 words on why the Iraq decision produces such different outcomes."
- **Teacher dashboard:** Track student engagement and prediction accuracy

**Partnership opportunity:** Work with history departments at universities to create course-integrated scenarios.

---

### 7.5 Podcast / Content Series

Each week, pick a curated seed and produce a 15-minute narrative podcast episode:

- AI-generated narration (from the narrator system) as the backbone
- Human host provides context, analysis, and commentary
- "This week on 21csim: Seed 4891 — What if the 2008 financial crisis had been worse?"
- Publish on Spotify, Apple Podcasts, YouTube

**Automate production:** The narration text is already generated. Use TTS for a rough cut, have a human host record intros/outros and commentary. Editing is minimal because the structure is consistent.

---

## Phase 8: Technical Deepening (Months 12-18)

### 8.1 Bayesian Network Upgrade

Replace the current DAG with a proper Bayesian network that can:
- **Infer backwards:** Given a final world state, what sequence of events most likely produced it?
- **Update probabilities dynamically:** As evidence accumulates during a run, update all downstream distributions using Bayes' theorem (not just additive modifiers)
- **Handle continuous variables natively:** Instead of discretizing everything into categorical branches, model some variables (climate temp, GDP growth) as continuous distributions that interact

**Library:** Use `pgmpy` or `pyro` for the Bayesian network backend.

---

### 8.2 Agent-Based Sub-Simulations

For high-resolution nodes (like the 9/11 attack or a military conflict), embed agent-based sub-simulations within the DAG node:

- **9/11 node:** Instead of a categorical distribution, run a mini-simulation of the four flights with agents (hijackers, crew, passengers, FAA, NORAD) making probabilistic decisions in sequence. The sub-simulation produces an outcome that feeds back into the main DAG.
- **Battle of Ukraine:** Model individual army groups, supply lines, and morale as agents. The sub-simulation runs thousands of micro-iterations to determine the war's outcome.

This gives much richer outcome distributions for high-stakes nodes while keeping the main DAG tractable.

---

### 8.3 Machine Learning Calibration

Use the historical record to calibrate probability distributions more rigorously:

- **Prediction market data:** Use historical prediction market prices (Metaculus, Polymarket, PredictIt) as priors for node probabilities. The 2016 election node's probability distribution should reflect what the best forecasters actually thought, not what we assign in hindsight.
- **Superforecaster surveys:** Commission surveys from the superforecasting community to calibrate contested probabilities.
- **Backtesting:** Run the simulation with 2000-2020 nodes only, see if the distribution of 2020 world states matches reality. Iteratively adjust weights until the model is well-calibrated.
- **Sensitivity-aware calibration:** Automatically identify which probability weights have the most leverage on outcome diversity and focus calibration effort there.

---

### 8.4 Real-Time World State Tracking

Connect the simulation to real-world data feeds to maintain a continuously-updated "current world state" that serves as the jumping-off point for future projections:

- **Climate:** Global temperature anomaly from NASA GISTEMP
- **Economics:** GDP growth, unemployment, inequality from World Bank API
- **Security:** ACLED conflict data, nuclear risk indices
- **Democracy:** V-Dem democracy indices, Freedom House scores
- **Technology:** AI benchmark performance, renewable energy share from IEA

The simulation uses these real values as the starting point for the 2026+ nodes, making future projections grounded in current reality rather than accumulated simulation drift.

```bash
$ 21csim run --from-reality --seed 42
# Uses live data for 2000-2026, simulates 2026-2100
```

---

### 8.5 Fine-Tuned Narrator Model

Train a custom LoRA adapter on the ~3,600 Claude-generated narrations from the curated library:

1. Extract all narrations as training examples (input: event context, output: narration prose)
2. Fine-tune Llama 3.1 8B or Mistral 7B using QLoRA (~4 hours on one A100)
3. Ship the adapter (~100MB) in the repo or as a separate download
4. Local narration quality approaches Claude for this specific task
5. Cost: $0 ongoing after initial training

```bash
$ ollama create 21csim-narrator -f Modelfile
$ 21csim run --seed 42 --narrator-model 21csim-narrator
```

---

## Phase 9: Expansion (Months 18+)

### 9.1 Multi-Century Mode

Extend the simulation beyond 2100 — model 2100-2500 as a deep-future speculative era:

- **Post-scarcity economics:** What happens when material abundance is achieved?
- **Interstellar civilization:** Colony ships, light-speed communication delays, political fragmentation
- **Post-biological humanity:** Digital consciousness, substrate independence, new forms of identity
- **Existential risk resolution:** Does humanity permanently solve existential risk, or does it remain indefinitely?
- **Alien contact:** Low-probability node (~1% per century) for first contact with extraterrestrial intelligence

---

### 9.2 Parallel Universe Browser

Run 100 seeds simultaneously and visualize them as parallel timelines branching from shared decision points:

- **3D visualization:** Timelines as branching paths in 3D space, color-coded by verdict
- **Convergence detection:** Find moments where very different timelines converge to similar world states
- **Divergence mapping:** Identify the exact nodes where two similar timelines split dramatically
- **"Multiverse statistics":** What fraction of possible universes have humans on Mars by 2060? What fraction experience nuclear war?

---

### 9.3 Geographic Resolution

Add sub-national geographic detail:

- **US states:** Model individual state trajectories (California tech boom, Rust Belt decline, Texas energy transition)
- **Chinese provinces:** Coastal vs. interior development, Xinjiang, Hong Kong, Taiwan
- **European countries:** Each EU member's trajectory within the federation/dissolution spectrum
- **African nations:** Individual development paths for Nigeria, Kenya, Ethiopia, South Africa
- **City-level:** Model megacities (Lagos, Mumbai, Jakarta, São Paulo) as individual nodes

This transforms the simulation from a global overview into a detailed geographic model where you can zoom into any region and see its specific alternate history.

---

### 9.4 Personal Life Simulator

Apply the same engine to personal decision-making:

```bash
$ 21csim run --scenario personal.yaml --seed 42

──── AGE 18 ────
  College Choice
  State university (affordable, close to home)                 HISTORICAL
  
──── AGE 22 ────
  First Job Decision
  Startup in San Francisco                                     DIVERGENCE
  ↳ Declined the safe corporate offer; took the risk
  
──── AGE 25 ────
  Relationship
  Married college girlfriend                                   HISTORICAL

...

──── AGE 65 ────
  LIFE OUTCOME: FULFILLING
  Career satisfaction: 0.72
  Financial security: 0.85  
  Relationships: 0.68
  Health: 0.61
  Regrets: 2 (didn't travel in 20s, worked too hard in 40s)
```

Same engine, same Monte Carlo analysis, same sensitivity testing — applied to the decisions of an individual life. "Which single decision had the most leverage on my life satisfaction?" is a question the engine can answer.

---

### 9.5 API / Embeddable Widget

Expose the simulation as an API and embeddable widget:

**API:**
```
GET  https://api.21csim.com/run?seed=42&format=json
GET  https://api.21csim.com/run?seed=42&nodes=2000_election,2003_iraq
POST https://api.21csim.com/what-if
     body: { "forced": {"2000_election": "gore_wins"}, "iterations": 1000 }
GET  https://api.21csim.com/batch?iterations=10000
```

**Embeddable widget:**
```html
<iframe src="https://21csim.com/embed/century/7714" width="800" height="600"></iframe>
```

Journalists, bloggers, and educators can embed a specific run or the full viewer in their own pages.

---

### 9.6 Documentary / Film Collaboration

The simulation produces complete alternate history narratives with AI narration. These are essentially documentary scripts.

**Short film series:** Each episode is one curated seed, narrated by a human voice actor, with simple animations illustrating the divergences. 10-15 minutes per episode. Publish on YouTube.

**Interactive documentary:** Partner with a documentary filmmaker to create an interactive film where the viewer makes decisions at key nodes and watches the consequences unfold. The simulation engine runs in real-time behind the documentary.

---

### 9.7 Academic Research Platform

Position 21csim as a tool for serious counterfactual analysis:

- **Peer-reviewed methodology paper:** Submit to a journal like *Journal of Artificial Societies and Social Simulation* or *Simulation & Gaming*
- **Conference presentations:** Present at simulation, history, or political science conferences
- **Research mode API:** Expose the engine for academic use with full probability distribution access, batch analysis, and sensitivity tools
- **Citation format:** Standard academic citation for researchers using the tool
- **Reproducibility:** Every run is deterministic and reproducible; results can be independently verified

---

### 9.8 Mobile App

Native iOS/Android app for watching centuries unfold on your phone:

- **Haptic feedback** synced to events (gentle tap for divergence, strong pulse for escalation, sustained vibration for nuclear event)
- **Lock screen widget:** Shows the current event from a run in progress
- **Daily seed:** Every day, a new curated seed is featured with push notification
- **Offline mode:** Pre-downloaded JSON runs work without network
- **Watch/AirPods integration:** Audio narration + haptics on wearables

---

### 9.9 Gamification Layer

Optional competitive layer for engaged users:

- **Prediction leagues:** Compete to predict outcomes before each node resolves
- **Scenario design contests:** Community votes on the best custom scenarios
- **Speedrun mode:** How fast can you identify which seed is running from the first 3 events?
- **Calibration score:** How well-calibrated are your probability estimates compared to the model's?
- **Achievement badges:** "Witnessed extinction," "Found the Golden Age," "Predicted 10 nodes correctly in a row"

---

## Feature Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|:------:|:------:|:--------:|
| Community node contributions | High | Low | P1 |
| Custom scenario files | High | Medium | P1 |
| Advanced analytics dashboard | High | Medium | P1 |
| Fine-tuned narrator model | Medium | Medium | P2 |
| Educational mode | High | High | P2 |
| "What If I Were President?" | High | Medium | P2 |
| Real-time world state tracking | Medium | Medium | P2 |
| Voice narration (TTS) | Medium | Medium | P2 |
| Multiplayer / watch party | Medium | High | P3 |
| Personal life simulator | High | High | P3 |
| API / embeddable widget | Medium | Medium | P3 |
| Mobile app | Medium | High | P3 |
| Bayesian network upgrade | Medium | Very High | P3 |
| Agent-based sub-simulations | Low | Very High | P4 |
| VR / spatial mode | Low | Very High | P4 |
| Multi-century mode | Low | High | P4 |
| Parallel universe browser | Low | High | P4 |
| Geographic resolution | Medium | Very High | P4 |
| Documentary collaboration | Medium | Variable | P4 |
| Gamification layer | Low | Medium | P4 |

---

## North Star Metrics

Track these to know if the project is succeeding:

| Metric | Launch Target | 6-Month Target | 18-Month Target |
|--------|:---:|:---:|:---:|
| GitHub stars | 100 | 1,000 | 5,000 |
| Weekly active viewers (web) | 500 | 5,000 | 25,000 |
| Curated seeds watched | 200 | 2,000 | 10,000 |
| Community-contributed nodes | 0 | 50 | 200 |
| Custom scenarios created | 0 | 10 | 50 |
| Blog post shares | 100 | 500 | 2,000 |
| Academic citations | 0 | 1 | 5 |
| CLI installs (PyPI) | 50 | 500 | 2,500 |
