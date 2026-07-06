# 21csim

[![CI](https://github.com/north-echo/21csim/actions/workflows/ci.yml/badge.svg)](https://github.com/north-echo/21csim/actions/workflows/ci.yml)
[![Code: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE-MIT)
[![Data: CC BY-NC-SA 4.0](https://img.shields.io/badge/data-CC%20BY--NC--SA%204.0-blue.svg)](LICENSE-DATA)

Monte Carlo counterfactual simulator for 21st century world history (2000–2100). Live at **[21csim.com](https://21csim.com)**.

A command-line tool and web viewer that models the major inflection points of the 21st century as a directed acyclic graph with probabilistic branching, runs Monte Carlo simulations sampling from historically-informed probability distributions, and renders alternate histories as narrative output.

Each run produces a plausible alternate 21st century. Batch runs reveal which decisions had the most leverage over how the century turned out.

Credit to https://github.com/mraml for the simulator inspiration.

## Quick Start

```bash
pip install .
21csim run --seed 42                    # Watch seed 42 unfold
21csim run --seed 42 --mode cinema      # Cinematic mode (default)
21csim run --seed 42 --mode interactive # Step through with keyboard
21csim run --seed 42 --mode sprint      # One-line-per-decade summary
21csim run --seed 42 --format json      # JSON output
21csim run --from-reality               # Start from the real 2026 world state
21csim batch --iterations 1000          # Run 1000 simulations
21csim diff 42 7714                     # Compare two seeds
21csim sensitivity --node 2003_iraq     # Sensitivity analysis
21csim what-if --set 2000_election=gore_wins --set 2001_911=plot_disrupted
```

## Web Viewer

```bash
cd web && python3 serve.py
# Open http://localhost:8080
```

Browse 497 pre-generated runs with cinematic playback, AI narration, world-state
dashboard, and a generative Tone.js score. Every curated run has a shareable
`/century/<seed>` page with its own social card.

**Forge mode** ("Forge Your Own" on the landing page) runs the full simulation
engine in the browser (`web/sim.js`, a verified port of the Python engine —
exact output parity on locked runs, verdict distribution within ~2pp of the
Python 10k batch). Playback pauses at eleven high-leverage decision nodes —
the 2000 election, 9/11, Iraq, the 2008 crisis, COVID response, the AMOC
collapse, the AI existential moment, and more — and your choice re-simulates
the rest of the century instantly. Finished centuries get a shareable
`?forge=` link that replays your world and lets the recipient re-decide.

**Life thread** — a quiet strand under the world events follows one person
through each run (birth year and hometown vary per seed; milestones are
chosen from the run's actual world state). Toggle with the "Life" button.

## Reality Stream

The simulator carries a rolling snapshot of the *actual* world
(`data/reality_2026.yaml`) so runs can start from today instead of 2000:

```bash
21csim update-reality --dry-run           # NewsAPI + LLM analyst propose updates
21csim apply-reality-updates updates.json # Apply a pre-computed analysis (no API calls)
```

Both paths validate and clamp every value against the engine's legal ranges
before anything touches disk. A scheduled Claude Code routine runs the
analysis weekly from web research and opens a `reality-update/YYYY-MM-DD`
pull request for review (see `.claude/skills/update-reality/`).

## Architecture

- **303 event nodes** spanning 2000–2100 as YAML files
- **50 world-state dimensions** (climate, politics, technology, security, demographics)
- **Cascading dependencies** — upstream outcomes shift downstream probability distributions
- **Conditional gating** — future nodes only fire if world-state conditions are met
- **LLM narration** — pre-generated Claude narrations for curated seeds, local Ollama for custom seeds
- **8 verdict categories** — Golden Age, Progress, Muddling Through, Decline, Catastrophe, Extinction, Transcendence, Radically Different

## Project Structure

```
src/csim/
  cli.py            — Typer CLI
  engine.py         — Simulation engine (DAG traversal + sampling)
  graph.py          — DAG construction, dependency resolution
  models.py         — Data models (SimEvent, SimOutcome, BatchResult)
  world_state.py    — World state + composite scoring + verdict classification
  renderer.py       — Rich terminal output (cinema, sprint, interactive modes)
  sound.py          — Runtime audio synthesis (numpy + afplay)
  analysis.py       — Batch statistics, sensitivity analysis, what-if
  exporter.py       — JSON export for web viewer
  reality_stream.py — News ingestion -> world state updates
  llm/              — LLM providers, narration, news analyst
  data/nodes/       — 303 YAML event definitions
  data/curated/     — 497 pre-generated seeds with narrations

web/
  index.html        — Cinematic viewer SPA
  explore.html      — Corpus analytics / Explorer
  sim.js            — In-browser simulation engine (port of engine.py)
  forge.js          — Interactive decision mode
  persona.js        — Life-thread generator
  serve.py          — Development server

scripts/
  export_sim_nodes.py       — Node data export for the browser engine
  validate_sim_parity.py    — Python/JS engine parity fixtures
  generate_century_pages.py — Per-seed share pages + sitemap

tests/              — pytest suite (100 tests, run in CI with ruff)
```

## Development

```bash
pip install -e ".[dev]"
ruff check src tests && pytest          # what CI runs
python scripts/export_sim_nodes.py     # after editing node YAMLs
python scripts/generate_century_pages.py  # after regenerating the run library
```

## Requirements

- Python 3.11+
- Dependencies: typer, numpy, networkx, rich, pyyaml

## License

Split license:

- **Code** (engine, CLI, web viewer, scripts) — [MIT](LICENSE-MIT). Use it for anything.
- **Simulation data & creative assets** (the node library, curated runs,
  narrations, audio, social cards) — [CC BY-NC-SA 4.0](LICENSE-DATA).
  Share and adapt with attribution for noncommercial purposes; commercial
  use of the data requires permission.

The node library is the research product of this project — hundreds of
hand-calibrated probability distributions and cascade structures. The split
keeps the engine open while protecting that work from commercial reuse.
