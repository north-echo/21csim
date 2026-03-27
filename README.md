# 21csim

Monte Carlo counterfactual simulator for 21st century world history (2000–2100).

A command-line tool and web viewer that models the major inflection points of the 21st century as a directed acyclic graph with probabilistic branching, runs Monte Carlo simulations sampling from historically-informed probability distributions, and renders alternate histories as narrative output.

Each run produces a plausible alternate 21st century. Batch runs reveal which decisions had the most leverage over how the century turned out.

## Quick Start

```bash
pip install .
21csim run --seed 42                    # Watch seed 42 unfold
21csim run --seed 42 --mode cinema      # Cinematic mode (default)
21csim run --seed 42 --mode interactive # Step through with keyboard
21csim run --seed 42 --mode sprint      # One-line-per-decade summary
21csim run --seed 42 --format json      # JSON output
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

Browse 300 pre-generated runs with cinematic playback, narration, world-state dashboard, and sound.

## Architecture

- **303 event nodes** spanning 2000–2100 as YAML files
- **32 world-state dimensions** (climate, politics, technology, security, demographics)
- **Cascading dependencies** — upstream outcomes shift downstream probability distributions
- **Conditional gating** — future nodes only fire if world-state conditions are met
- **LLM narration** — pre-generated Claude narrations for curated seeds, local Ollama for custom seeds
- **8 verdict categories** — Golden Age, Progress, Muddling Through, Decline, Catastrophe, Extinction, Transcendence, Radically Different

## Project Structure

```
src/csim/
  cli.py          — Typer CLI
  engine.py       — Simulation engine (DAG traversal + sampling)
  graph.py        — DAG construction, dependency resolution
  models.py       — Data models (SimEvent, SimOutcome, BatchResult)
  world_state.py  — 32-dimension world state + composite scoring + verdict classification
  renderer.py     — Rich terminal output (cinema, sprint, interactive modes)
  sound.py        — Runtime audio synthesis (numpy + afplay)
  analysis.py     — Batch statistics, sensitivity analysis, what-if
  exporter.py     — JSON export for web viewer
  llm/            — LLM narration (Claude, Ollama, caching)
  data/nodes/     — 303 YAML event definitions
  data/curated/   — 300 pre-generated seeds with narrations

web/
  index.html      — Cinematic viewer SPA
  explore.html    — Corpus analytics / Explorer
  serve.py        — Development server

tests/            — pytest suite (80 tests)
```

## Requirements

- Python 3.11+
- Dependencies: typer, numpy, networkx, rich, pyyaml

## License

MIT
