"""Typer CLI entrypoint for 21csim."""

from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path

import typer

app = typer.Typer(
    name="21csim",
    help="Monte Carlo counterfactual simulator for 21st century world history (2000-2100)",
    no_args_is_help=True,
)


class DisplayMode(str, Enum):
    cinema = "cinema"
    sprint = "sprint"
    interactive = "interactive"


class SpeedPreset(str, Enum):
    ultra = "ultra"
    fast = "fast"
    normal = "normal"
    slow = "slow"


class DetailLevel(str, Enum):
    minimal = "minimal"
    standard = "standard"
    full = "full"
    research = "research"


class OutputFormat(str, Enum):
    terminal = "terminal"
    json = "json"


SPEED_MAP = {
    "ultra": 1200,
    "fast": 600,
    "normal": 300,
    "slow": 120,
}


def _get_data_dir() -> Path:
    """Find the data directory."""
    # Check relative to this file (installed package)
    pkg_data = Path(__file__).parent / "data"
    if pkg_data.exists():
        return pkg_data
    # Check CWD
    cwd_data = Path.cwd() / "src" / "csim" / "data"
    if cwd_data.exists():
        return cwd_data
    raise typer.BadParameter(
        f"Cannot find data directory. Looked in {pkg_data} and {cwd_data}"
    )


@app.command()
def run(
    seed: int = typer.Option(42, help="RNG seed for reproducible simulation"),
    mode: DisplayMode = typer.Option(DisplayMode.cinema, help="Display mode"),
    speed: SpeedPreset = typer.Option(SpeedPreset.fast, help="Playback speed"),
    detail: DetailLevel = typer.Option(DetailLevel.standard, help="Detail level"),
    divergences_only: bool = typer.Option(False, "--divergences-only", help="Only show divergences"),
    domain: str | None = typer.Option(None, help="Filter by domain"),
    no_pause: bool = typer.Option(False, "--no-pause", help="Skip timing delays"),
    sound: bool = typer.Option(False, "--sound", help="Enable audio cues"),
    format: OutputFormat = typer.Option(OutputFormat.terminal, "--format", help="Output format"),
    narrate: bool = typer.Option(True, "--narrate/--no-narrate", help="Enable/disable AI narration"),
    provider: str | None = typer.Option(None, "--provider", help="Force provider: ollama|claude|none"),
    model: str | None = typer.Option(None, "--model", help="Override model name"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI narration (alias for --provider none)"),
    from_reality: bool = typer.Option(False, "--from-reality", help="Start from real 2026 world state"),
) -> None:
    """Run a single simulation of the 21st century."""
    from csim.engine import simulate
    from csim.graph import build_graph

    data_dir = _get_data_dir()
    graph = build_graph(data_dir)

    initial_state = None
    locked_results = None
    if from_reality:
        from csim.reality import load_reality
        initial_state, locked_results = load_reality(data_dir)
        typer.echo(f"Starting from reality: {len(locked_results)} nodes locked to historical outcomes")

    outcome = simulate(graph, seed, initial_state=initial_state, locked_results=locked_results)

    # Resolve narration provider
    llm_provider = None
    if narrate and not no_ai:
        from csim.llm import resolve_provider
        effective_provider = "none" if not narrate else provider
        llm_provider = resolve_provider(effective_provider)
        if llm_provider.model_name() != "none":
            typer.echo(f"Narrator: {llm_provider.model_name()}")
        elif provider and provider != "none":
            typer.echo(f"Narrator: not available ({provider} not found)")


    if format == OutputFormat.json:
        from csim.exporter import export_outcome_to_string
        typer.echo(export_outcome_to_string(outcome))
        return

    # Terminal output
    sound_engine = None
    if sound:
        from csim.sound import SoundEngine
        sound_engine = SoundEngine(enabled=True)

    if mode == DisplayMode.cinema:
        from csim.renderer import render_cinema
        render_cinema(
            outcome,
            speed=SPEED_MAP[speed.value],
            detail=detail.value,
            divergences_only=divergences_only,
            domain_filter=domain,
            sound_engine=sound_engine,
            no_pause=no_pause,
        )
    elif mode == DisplayMode.sprint:
        from csim.renderer import render_sprint
        render_sprint(outcome)
    elif mode == DisplayMode.interactive:
        from csim.renderer import render_interactive
        render_interactive(
            outcome,
            detail=detail.value,
            divergences_only=divergences_only,
            domain_filter=domain,
            sound_engine=sound_engine,
        )

    if sound_engine:
        sound_engine.shutdown()


@app.command()
def batch(
    iterations: int = typer.Option(1000, help="Number of simulations"),
    output: Path | None = typer.Option(None, help="Output JSON file path"),
    parallel: int = typer.Option(1, help="Number of parallel workers"),
    format: OutputFormat = typer.Option(OutputFormat.terminal, "--format", help="Output format"),
    from_reality: bool = typer.Option(False, "--from-reality", help="Start from real 2026 world state"),
) -> None:
    """Run batch simulations and analyze results."""
    from csim.engine import simulate_batch
    from csim.graph import build_graph

    data_dir = _get_data_dir()
    graph = build_graph(data_dir)

    initial_state = None
    locked_results = None
    if from_reality:
        from csim.reality import load_reality
        initial_state, locked_results = load_reality(data_dir)
        typer.echo(f"Starting from reality: {len(locked_results)} nodes locked to historical outcomes")

    typer.echo(f"Running {iterations} simulations...")
    result = simulate_batch(graph, iterations, parallel=parallel,
                            initial_state=initial_state, locked_results=locked_results)

    if format == OutputFormat.json or output:
        from csim.exporter import export_batch_json, serialize_batch
        if output:
            export_batch_json(result, output)
            typer.echo(f"Results exported to {output}")
        else:
            typer.echo(json.dumps(serialize_batch(result), indent=2))
        return

    from csim.renderer import render_batch_summary
    render_batch_summary(result)


@app.command()
def diff(
    seed_a: int = typer.Argument(..., help="First seed"),
    seed_b: int = typer.Argument(..., help="Second seed"),
) -> None:
    """Compare two simulation runs."""
    from rich.console import Console

    from csim.analysis import diff_runs
    from csim.engine import simulate
    from csim.graph import build_graph

    data_dir = _get_data_dir()
    graph = build_graph(data_dir)

    outcome_a = simulate(graph, seed_a)
    outcome_b = simulate(graph, seed_b)
    result = diff_runs(outcome_a, outcome_b)

    console = Console()
    console.print(f"\n[bold]Seed {seed_a}[/]: {outcome_a.headline} ({outcome_a.outcome_class.value}, {outcome_a.composite_score:+.2f})")
    console.print(f"[bold]Seed {seed_b}[/]: {outcome_b.headline} ({outcome_b.outcome_class.value}, {outcome_b.composite_score:+.2f})")
    console.print(f"\n[bold]{result['total_differences']} differences:[/]")

    for d in result["differences"]:
        console.print(
            f"  {d['year_month']} {d['title']}: "
            f"[yellow]{d['seed_a_branch']}[/] vs [cyan]{d['seed_b_branch']}[/]"
        )
    console.print()


@app.command()
def sensitivity(
    node: str = typer.Option(..., help="Node ID to analyze"),
    metric: str = typer.Option("composite_score", help="Metric to measure"),
    iterations: int = typer.Option(1000, help="Number of simulations"),
) -> None:
    """Analyze sensitivity of outcomes to a specific node."""
    from rich.console import Console
    from rich.table import Table

    from csim.analysis import sensitivity_analysis
    from csim.graph import build_graph

    data_dir = _get_data_dir()
    graph = build_graph(data_dir)

    typer.echo(f"Running sensitivity analysis for {node} ({iterations} iterations)...")
    result = sensitivity_analysis(graph, node, metric, iterations)

    console = Console()
    table = Table(title=f"Sensitivity: {node} → {metric}")
    table.add_column("Branch", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Mean", justify="right")
    table.add_column("Std", justify="right")
    table.add_column("Range", justify="right")

    for branch, stats in result.items():
        table.add_row(
            branch,
            str(stats["count"]),
            f"{stats['mean']:+.3f}",
            f"{stats['std']:.3f}",
            f"[{stats['p5']:+.3f}, {stats['p95']:+.3f}]",
        )

    console.print(table)


@app.command(name="what-if")
def what_if(
    set_branches: list[str] = typer.Option(
        ..., "--set", help="NODE=BRANCH pairs to force (repeatable)"
    ),
    iterations: int = typer.Option(1000, help="Number of simulations"),
) -> None:
    """Run what-if analysis with forced branch selections."""
    from rich.console import Console

    from csim.analysis import what_if_analysis
    from csim.graph import build_graph
    from csim.renderer import render_batch_summary

    data_dir = _get_data_dir()
    graph = build_graph(data_dir)

    overrides = {}
    for pair in set_branches:
        if "=" not in pair:
            typer.echo(f"Invalid format: {pair}. Use NODE=BRANCH", err=True)
            raise typer.Exit(1)
        node, branch = pair.split("=", 1)
        overrides[node] = branch

    typer.echo(f"Running what-if analysis ({iterations} iterations)...")
    typer.echo(f"Overrides: {overrides}")

    baseline, overridden = what_if_analysis(graph, overrides, iterations)

    console = Console()
    console.print("\n[bold]Baseline:[/]")
    render_batch_summary(baseline)
    console.print("[bold]With overrides:[/]")
    render_batch_summary(overridden)


@app.command(name="export-library")
def export_library(
    count: int = typer.Option(200, help="Number of curated seeds"),
    candidates: int = typer.Option(100_000, help="Candidate pool size"),
    narrate: bool = typer.Option(False, "--narrate", help="Generate AI narrations"),
    narrator_provider: str | None = typer.Option(None, "--narrator-provider", help="Provider: claude|ollama"),
    narrator_model: str | None = typer.Option(None, "--narrator-model", help="Model override"),
    output: Path = typer.Option(Path("src/csim/data/curated"), help="Output directory"),
) -> None:
    """Generate curated seed library with optional narration."""
    import asyncio

    from csim.engine import simulate, simulate_batch
    from csim.exporter import export_outcome_json
    from csim.graph import build_graph

    data_dir = _get_data_dir()
    graph = build_graph(data_dir)

    typer.echo(f"Selecting {count} curated seeds from {candidates} candidates...")
    batch = simulate_batch(graph, candidates)

    # Select diverse seeds across outcome classes
    from csim.models import OutcomeClass
    selected_outcomes = []
    by_class: dict[OutcomeClass, list] = {}
    for o in batch.outcomes:
        cls = o.outcome_class
        by_class.setdefault(cls, []).append(o)

    quotas = {
        OutcomeClass.GOLDEN_AGE: 15,
        OutcomeClass.PROGRESS: 40,
        OutcomeClass.MUDDLING_THROUGH: 30,
        OutcomeClass.DECLINE: 35,
        OutcomeClass.CATASTROPHE: 30,
        OutcomeClass.EXTINCTION: 10,
        OutcomeClass.TRANSCENDENCE: 15,
        OutcomeClass.RADICALLY_DIFFERENT: 25,
    }

    for cls, quota in quotas.items():
        available = by_class.get(cls, [])
        # Sort by diversity (spread of composite scores)
        available.sort(key=lambda o: abs(o.composite_score))
        selected_outcomes.extend(available[:quota])

    # Fill remaining slots proportionally to natural distribution
    remaining = count - len(selected_outcomes)
    selected_seeds = {o.seed for o in selected_outcomes}
    if remaining > 0:
        # Group unselected by class, fill proportionally
        unselected_by_class: dict[OutcomeClass, list] = {}
        for o in batch.outcomes:
            if o.seed not in selected_seeds:
                unselected_by_class.setdefault(o.outcome_class, []).append(o)

        # Calculate proportional fill per class
        total_unselected = sum(len(v) for v in unselected_by_class.values())
        if total_unselected > 0:
            for pool in unselected_by_class.values():
                share = max(1, int(remaining * len(pool) / total_unselected))
                # Sort by score diversity within class
                pool.sort(key=lambda o: abs(o.composite_score))
                selected_outcomes.extend(pool[:share])
                for o in pool[:share]:
                    selected_seeds.add(o.seed)

    selected_outcomes = selected_outcomes[:count]
    typer.echo(f"Selected {len(selected_outcomes)} seeds")

    # Generate narrations if requested
    llm = None
    if narrate:
        from csim.llm import resolve_provider
        llm = resolve_provider(narrator_provider)
        if narrator_model and hasattr(llm, 'model'):
            llm.model = narrator_model
        if not llm.is_available():
            typer.echo("Error: narrator provider not available", err=True)
            raise typer.Exit(1)
        typer.echo(f"Narrator: {llm.model_name()}")

    # Export
    output.mkdir(parents=True, exist_ok=True)
    runs_dir = output / "runs"
    runs_dir.mkdir(exist_ok=True)

    for i, outcome in enumerate(selected_outcomes, 1):
        # Re-simulate to get fresh outcome (batch outcomes are minimal)
        outcome = simulate(graph, outcome.seed)

        if narrate and llm:
            from csim.llm.narrator import get_narration, select_narration_candidates
            candidates = select_narration_candidates(outcome.events, max_narrations=25)

            async def narrate_batch():
                import asyncio as aio
                count = 0
                for batch_start in range(0, len(candidates), 5):
                    batch = candidates[batch_start:batch_start + 5]
                    tasks = [
                        get_narration(outcome.seed, outcome.events[idx], outcome.events, idx, llm)
                        for idx in batch
                    ]
                    results = await aio.gather(*tasks, return_exceptions=True)
                    for j, r in enumerate(results):
                        if r and not isinstance(r, Exception):
                            event_idx = batch[j]
                            outcome.events[event_idx].narration = r
                            outcome.events[event_idx].narration_source = llm.model_name()
                            count += 1
                return count

            narrated_count = asyncio.run(narrate_batch())
            typer.echo(f"  Seed {outcome.seed}: {narrated_count} narrations [{i}/{len(selected_outcomes)}]")
        else:
            typer.echo(f"  Seed {outcome.seed} [{i}/{len(selected_outcomes)}]")

        out_path = runs_dir / f"seed_{outcome.seed}.json"
        export_outcome_json(outcome, out_path)

    typer.echo(f"\nExported {len(selected_outcomes)} runs to {runs_dir}")


@app.command(name="update-reality")
def update_reality(
    days_back: int = typer.Option(7, help="Days of news to fetch"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without applying"),
    provider: str | None = typer.Option(None, "--provider", help="LLM provider: claude|ollama"),
    model: str | None = typer.Option(None, "--model", help="Override model name"),
    newsapi_key: str | None = typer.Option(None, "--newsapi-key", envvar="NEWSAPI_KEY", help="NewsAPI.org key"),
) -> None:
    """Fetch world news and update reality state via LLM analysis."""
    import asyncio

    from rich.console import Console
    from rich.table import Table

    from csim.llm import resolve_provider
    from csim.reality_stream import export_reality_snapshot, run_reality_stream

    console = Console()
    data_dir = _get_data_dir()

    # Resolve API key
    api_key = newsapi_key or os.environ.get("NEWSAPI_KEY", "")
    if not api_key:
        # Try .env file
        from pathlib import Path
        for candidate in [Path.cwd() / ".env", Path(__file__).parent.parent.parent / ".env"]:
            if candidate.exists():
                for line in candidate.read_text().splitlines():
                    if line.strip().startswith("NEWSAPI_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip("\"'")
                        break
            if api_key:
                break

    if not api_key:
        console.print("[red]Error:[/] NEWSAPI_KEY not set. Get one at https://newsapi.org")
        raise typer.Exit(1)

    # Resolve LLM provider
    llm = resolve_provider(provider)
    if model and hasattr(llm, 'model'):
        llm.model = model
    if not llm.is_available():
        console.print("[red]Error:[/] LLM provider not available. Set ANTHROPIC_API_KEY or use --provider ollama")
        raise typer.Exit(1)

    console.print(f"[bold]Reality Stream[/] — fetching {days_back} days of news...")
    console.print(f"Analyst: {llm.model_name()}")

    if dry_run:
        console.print("[yellow]DRY RUN[/] — no files will be modified\n")

    # Run the stream
    result = asyncio.run(run_reality_stream(
        data_dir=data_dir,
        provider=llm,
        newsapi_key=api_key,
        days_back=days_back,
        dry_run=dry_run,
    ))

    # Display results
    console.print(f"\nProcessed [bold]{result['news_count']}[/] news articles")
    console.print(f"[dim]{result['reasoning']}[/]\n")

    if result["dimension_updates"]:
        table = Table(title="World State Updates")
        table.add_column("Dimension", style="bold")
        table.add_column("New Value", justify="right")
        for dim, val in sorted(result["dimension_updates"].items()):
            table.add_row(dim, f"{val}")
        console.print(table)
    else:
        console.print("[dim]No dimension changes.[/]")

    if result["new_nodes"]:
        console.print(f"\n[bold]{len(result['new_nodes'])} new event nodes:[/]")
        for node in result["new_nodes"]:
            console.print(f"  • {node.get('year_month', '?')} — {node.get('title', node.get('id', '?'))}")
    else:
        console.print("\n[dim]No new event nodes.[/]")

    if dry_run:
        console.print("\n[yellow]No files modified (dry run).[/]")
    else:
        console.print("\n[green]✓ reality_2026.yaml updated[/]")
        # Export static snapshot for the production site (static host, no /api)
        web_dir = Path(__file__).parent.parent.parent / "web"
        if web_dir.is_dir():
            snapshot = export_reality_snapshot(data_dir, web_dir / "reality.json")
            console.print(f"[green]✓ exported[/] {snapshot}")


@app.command(name="apply-reality-updates")
def apply_reality_updates(
    updates_file: Path = typer.Argument(..., help="JSON file with dimension_updates, new_nodes, reasoning"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and show changes without writing"),
) -> None:
    """Apply a pre-computed reality update authored outside the API path.

    Same validation and file writes as update-reality, but the analysis JSON
    is supplied directly — e.g. authored by Claude Code from web research —
    so no NewsAPI or Anthropic API calls are made.
    """
    from rich.console import Console
    from rich.table import Table

    from csim.llm.analyst import validate_dimension_updates, validate_new_nodes
    from csim.reality_stream import export_reality_snapshot, update_reality

    console = Console()
    data_dir = _get_data_dir()

    raw = json.loads(updates_file.read_text())
    proposed_dims = raw.get("dimension_updates", {}) or {}
    proposed_nodes = raw.get("new_nodes", []) or []
    reasoning = raw.get("reasoning", "")

    dims = validate_dimension_updates(proposed_dims)
    nodes = validate_new_nodes(proposed_nodes)

    rejected_dims = sorted(set(proposed_dims) - set(dims))
    rejected_nodes = [n.get("id", "?") for n in proposed_nodes if isinstance(n, dict)]
    rejected_nodes = sorted(set(rejected_nodes) - {n["id"] for n in nodes})
    if rejected_dims:
        console.print(f"[yellow]Rejected dimensions:[/] {', '.join(rejected_dims)}")
    if rejected_nodes:
        console.print(f"[yellow]Rejected nodes:[/] {', '.join(rejected_nodes)}")

    if dims:
        table = Table(title="World State Updates")
        table.add_column("Dimension", style="bold")
        table.add_column("Proposed", justify="right")
        table.add_column("Applied (clamped)", justify="right")
        for dim, val in sorted(dims.items()):
            table.add_row(dim, f"{proposed_dims.get(dim)}", f"{val}")
        console.print(table)
    else:
        console.print("[dim]No dimension changes.[/]")

    if nodes:
        console.print(f"\n[bold]{len(nodes)} new event nodes:[/]")
        for node in nodes:
            console.print(f"  • {node['year_month']} — {node['title']}")

    if dry_run:
        console.print("\n[yellow]No files modified (dry run).[/]")
        return

    update_reality(data_dir, dims, nodes, update_log={"reasoning": reasoning})
    console.print("\n[green]✓ reality_2026.yaml updated[/]")
    web_dir = Path(__file__).parent.parent.parent / "web"
    if web_dir.is_dir():
        snapshot = export_reality_snapshot(data_dir, web_dir / "reality.json")
        console.print(f"[green]✓ exported[/] {snapshot}")


if __name__ == "__main__":
    app()
