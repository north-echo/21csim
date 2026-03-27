"""Rich-based terminal output for cinema, sprint, and interactive modes."""

from __future__ import annotations

import sys
import time
from dataclasses import fields

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from csim.models import EventStatus, OutcomeClass, SimEvent, SimOutcome
from csim.world_state import WorldState, _HISTORICAL_BASELINES, compute_composite_score

console = Console()

# Status colors
STATUS_STYLES = {
    EventStatus.HISTORICAL: "dim",
    EventStatus.DIVERGENCE: "yellow",
    EventStatus.PREVENTED: "green",
    EventStatus.ACCELERATED: "cyan",
    EventStatus.DELAYED: "blue",
    EventStatus.ESCALATED: "red bold",
    EventStatus.DIMINISHED: "dim green",
}

STATUS_LABELS = {
    EventStatus.HISTORICAL: "─ historical ─",
    EventStatus.DIVERGENCE: "DIVERGENCE",
    EventStatus.PREVENTED: "PREVENTED",
    EventStatus.ACCELERATED: "ACCELERATED",
    EventStatus.DELAYED: "DELAYED",
    EventStatus.ESCALATED: "ESCALATED",
    EventStatus.DIMINISHED: "DIMINISHED",
}

# Verdict styles
VERDICT_STYLES = {
    OutcomeClass.GOLDEN_AGE: "bold green",
    OutcomeClass.PROGRESS: "green",
    OutcomeClass.MUDDLING_THROUGH: "yellow",
    OutcomeClass.DECLINE: "red",
    OutcomeClass.CATASTROPHE: "red bold",
    OutcomeClass.EXTINCTION: "red bold reverse",
    OutcomeClass.TRANSCENDENCE: "bold cyan",
    OutcomeClass.RADICALLY_DIFFERENT: "magenta",
}


def _era_for_year(year: int) -> tuple[str, str]:
    """Return era name and year range."""
    if year < 2030:
        return "THE RECKONING", "2000 – 2030"
    elif year < 2050:
        return "THE TRANSFORMATION", "2030 – 2050"
    elif year < 2070:
        return "THE FORK", "2050 – 2070"
    elif year < 2090:
        return "THE NEW WORLD", "2070 – 2090"
    else:
        return "END STATE", "2090 – 2100"


def _month_abbr(month: str) -> str:
    months = {
        "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR",
        "05": "MAY", "06": "JUN", "07": "JUL", "08": "AUG",
        "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC",
    }
    return months.get(month, "???")


def _compute_delay(current_ym: str, next_ym: str, speed: int) -> float:
    """Compute display delay between events based on real time gap."""
    try:
        cy, cm = current_ym.split("-")
        ny, nm = next_ym.split("-")
        gap_months = (int(ny) - int(cy)) * 12 + (int(nm) - int(cm))
        delay = (gap_months * 30 * 24 * 60) / speed
        return max(0.05, min(3.0, delay))
    except (ValueError, IndexError):
        return 0.2


def render_header(seed: int) -> None:
    """Render the simulation header."""
    console.print()
    console.print(
        Panel(
            f"[bold white]THE 21st CENTURY[/]  ·  SEED {seed}",
            style="bold white",
            expand=True,
            padding=(0, 2),
        )
    )
    console.print()


def render_era_transition(era_name: str, era_range: str) -> None:
    """Render an era transition banner."""
    console.print()
    console.print(
        Panel(
            f"[bold white]{era_name}[/]\n{era_range}",
            style="bold white",
            expand=False,
            padding=(0, 4),
        ),
        justify="center",
    )
    console.print()


def render_year_header(year: str) -> None:
    """Render a year header."""
    console.print(f"\n[bold white]                        ── {year} ──[/]\n")


def render_event(event: SimEvent, detail: str = "standard", width: int = 100) -> None:
    """Render a single event in cinema mode."""
    year_month = event.year_month
    month = _month_abbr(year_month.split("-")[1]) if "-" in year_month else "???"

    status_style = STATUS_STYLES.get(event.status, "dim")
    status_label = STATUS_LABELS.get(event.status, str(event.status.value))

    # Event line
    title_text = Text()
    title_text.append(f" {month}  ", style="bold white")
    title_text.append(event.title, style="bold white")

    # Status tag right-aligned
    status_text = Text(status_label, style=status_style)

    if width >= 100:
        # Full layout
        padding = max(1, width - len(f" {month}  {event.title}") - len(status_label) - 8)
        console.print(f" [bold white]{month}[/]  [bold white]{event.title}[/]{' ' * padding}[{status_style}]{status_label}[/]")
    else:
        console.print(f" [bold white]{month}[/]  [bold white]{event.title}[/]  [{status_style}]{status_label}[/]")

    # Description (for divergences)
    if detail in ("standard", "full", "research"):
        desc = event.description
        if len(desc) > 70:
            desc = desc[:67] + "..."
        console.print(f"      {desc}")

    # Explanation (for divergences)
    if event.explanation and event.status != EventStatus.HISTORICAL:
        if detail in ("standard", "full", "research"):
            console.print(f"      [dim italic]↳ {event.explanation}[/]")

    # World state deltas (full detail)
    if detail in ("full", "research") and event.world_state_delta:
        delta_parts = []
        for dim, val in sorted(event.world_state_delta.items()):
            if abs(val) > 0.001:
                sign = "+" if val > 0 else ""
                delta_parts.append(f"{dim}: {sign}{val:.3f}")
        if delta_parts:
            console.print(f"      [dim]Δ {', '.join(delta_parts[:5])}[/]")

    console.print()


def render_nuclear_event(event: SimEvent) -> None:
    """Render special nuclear event display."""
    console.print()
    console.print(Panel(
        "[red bold]☢  NUCLEAR WEAPONS USED IN CONFLICT  ☢[/]\n"
        f"[red]{event.description}[/]",
        style="red bold",
        title="██ NUCLEAR ██",
        expand=False,
        padding=(1, 4),
    ), justify="center")
    console.print()


def render_extinction(year: str, state: WorldState) -> None:
    """Render extinction event."""
    console.print()
    console.print(Panel(
        f"[red bold]CIVILIZATION COLLAPSE[/]\n"
        f"Year: {year}\n"
        f"Population: ~{state.global_population_billions:.1f}B\n"
        f"Recovery probability: LOW\n"
        f"Verdict: CATASTROPHE",
        style="red bold",
        expand=False,
        padding=(1, 4),
    ), justify="center")
    console.print()


def render_transcendence(year: str) -> None:
    """Render transcendence event."""
    console.print()
    console.print(Panel(
        "[bold cyan]T R A N S C E N D E N C E[/]\n"
        "Humanity has merged with its AI creations\n"
        f"Year: {year} | Status: Post-human",
        style="bold cyan",
        expand=False,
        padding=(1, 4),
    ), justify="center")
    console.print()


def render_world_state_snapshot(state: WorldState, year: str) -> None:
    """Render a world state snapshot at era boundaries."""
    composite = compute_composite_score(state)

    key_dims = [
        ("Climate", f"+{state.climate_temp_anomaly:.1f}°C", "climate_temp_anomaly", True),
        ("US Polarization", f"{state.us_polarization:.2f}", "us_polarization", True),
        ("Conflict Deaths", f"{state.conflict_deaths:,}", "conflict_deaths", True),
        ("Nuclear Risk", f"{state.nuclear_risk_level:.2f}", "nuclear_risk_level", True),
        ("Democracy Index", f"{state.global_democracy_index:.2f}", "global_democracy_index", False),
        ("Renewable Energy", f"{state.renewable_energy_share:.0%}", "renewable_energy_share", False),
    ]

    lines = []
    for label, value, dim, higher_is_worse in key_dims:
        baseline = _HISTORICAL_BASELINES.get(dim, getattr(state, dim))
        current = getattr(state, dim)
        if isinstance(baseline, (int, float)) and isinstance(current, (int, float)):
            if higher_is_worse:
                better = current < baseline
            else:
                better = current > baseline
            indicator = "[green]▲ better[/]" if better else "[red]▼ worse[/]"
            if abs(current - baseline) < 0.01:
                indicator = "[dim]─ same[/]"
        else:
            indicator = ""
        lines.append(f"  {label:<20s} {value:<15s} {indicator}")

    # Score bar
    bar_len = 30
    filled = int((composite + 1) / 2 * bar_len)
    bar = "█" * max(0, filled) + "░" * max(0, bar_len - filled)
    lines.append(f"  Running score: {composite:+.2f}  {bar}")

    console.print(Panel(
        "\n".join(lines),
        title=f"World State at {year}",
        expand=False,
        padding=(0, 2),
    ), justify="center")


def render_final_summary(outcome: SimOutcome) -> None:
    """Render the final century summary screen."""
    state = outcome.final_state
    if not state:
        return

    composite = outcome.composite_score
    verdict_style = VERDICT_STYLES.get(outcome.outcome_class, "white")
    verdict_name = outcome.outcome_class.value.replace("-", " ")

    console.print()
    console.rule("[bold white]FINAL WORLD STATE: 2100[/]", style="bold white")
    console.print()

    # Dimension table
    table = Table(show_header=True, header_style="bold white", expand=False, show_lines=False)
    table.add_column("Dimension", style="white", width=22)
    table.add_column("This Run", style="bold white", width=15)
    table.add_column("Historical", style="dim", width=15)
    table.add_column("Delta", width=15)

    dims = [
        ("Climate", f"+{state.climate_temp_anomaly:.1f}°C", "+2.5°C", state.climate_temp_anomaly < 2.5),
        ("Population", f"{state.global_population_billions:.1f}B", "~8.5B", None),
        ("Conflict Deaths", f"{state.conflict_deaths:,}", "~2,000,000", state.conflict_deaths < 2_000_000),
        ("Nuclear Risk", f"{state.nuclear_risk_level:.2f}", "0.35", state.nuclear_risk_level < 0.35),
        ("Democracy Index", f"{state.global_democracy_index:.2f}", "0.55", state.global_democracy_index > 0.55),
        ("Inequality", f"{state.inequality_index:.2f}", "0.60", state.inequality_index < 0.60),
        ("Renewable Energy", f"{state.renewable_energy_share:.0%}", "40%", state.renewable_energy_share > 0.40),
        ("AI Progress", f"{state.ai_development_year_offset:+d} yrs", "0", None),
        ("Space Dev", f"{state.space_development_index:.2f}", "0.10", state.space_development_index > 0.10),
    ]

    for label, this_run, historical, is_better in dims:
        if is_better is True:
            delta = "[green]▲ better[/]"
        elif is_better is False:
            delta = "[red]▼ worse[/]"
        else:
            delta = "[dim]─[/]"
        table.add_row(label, this_run, historical, delta)

    console.print(table, justify="center")
    console.print()

    # Verdict
    console.print(f"  Century Verdict:     [{verdict_style}]{verdict_name}[/]")

    # Score bar
    bar_len = 30
    filled = int((composite + 1) / 2 * bar_len)
    bar = "█" * max(0, filled) + "░" * max(0, bar_len - filled)
    console.print(f"  Composite Score:     {composite:+.2f} {bar}")
    console.print(f"  Percentile:          {outcome.percentile:.0f}th")
    console.print(f"  Divergences:         {outcome.total_divergences} of {len(outcome.events)}")
    if outcome.first_divergence_year:
        console.print(f"  First Divergence:    {outcome.first_divergence_year}")
    if outcome.largest_divergence_node:
        console.print(f"  Largest Divergence:  {outcome.largest_divergence_node}")
    console.print()

    # Headline
    if outcome.headline:
        console.print(f'  [bold italic]"{outcome.headline}"[/]')
    console.print()
    console.rule(style="bold white")


def render_cinema(outcome: SimOutcome, speed: int = 600, detail: str = "standard",
                  divergences_only: bool = False, domain_filter: str | None = None,
                  sound_engine=None, no_pause: bool = False) -> None:
    """Render a full simulation in cinema mode."""
    width = console.width

    render_header(outcome.seed)

    current_year = ""
    current_era = ""
    last_ym = None

    for i, event in enumerate(outcome.events):
        # Filter
        if divergences_only and event.status == EventStatus.HISTORICAL:
            continue
        if domain_filter and event.domain != domain_filter:
            continue

        year = event.year_month.split("-")[0] if "-" in event.year_month else "????"
        era_name, era_range = _era_for_year(int(year) if year.isdigit() else 2000)

        # Era transition
        if era_name != current_era:
            if current_era and not no_pause:
                time.sleep(2.0)
            if sound_engine:
                sound_engine.play("era_transition")
            render_era_transition(era_name, era_range)
            if outcome.final_state and current_era:
                render_world_state_snapshot(outcome.final_state, year)
            current_era = era_name

        # Year header
        if year != current_year:
            render_year_header(year)
            current_year = year

        # Delay between events
        if last_ym and not no_pause:
            delay = _compute_delay(last_ym, event.year_month, speed)
            time.sleep(delay)

        # Special event rendering
        if event.is_high_impact and "nuclear" in event.description.lower():
            render_nuclear_event(event)
            if sound_engine:
                sound_engine.play("nuclear")
        else:
            render_event(event, detail=detail, width=width)

        # Sound for major divergences
        if sound_engine and event.is_high_impact and event.status != EventStatus.HISTORICAL:
            sound_engine.play("divergence_major")

        last_ym = event.year_month

    # Final summary
    if not no_pause:
        time.sleep(1.0)

    # Verdict sound
    if sound_engine and outcome.final_state:
        if outcome.outcome_class in (OutcomeClass.EXTINCTION, OutcomeClass.CATASTROPHE):
            sound_engine.play("extinction" if outcome.outcome_class == OutcomeClass.EXTINCTION else "verdict_bad")
        elif outcome.outcome_class == OutcomeClass.TRANSCENDENCE:
            sound_engine.play("transcendence")
        elif outcome.composite_score > 0.3:
            sound_engine.play("verdict_good")
        elif outcome.composite_score < -0.3:
            sound_engine.play("verdict_bad")
        else:
            sound_engine.play("verdict_neutral")

    # Special endings
    if outcome.outcome_class == OutcomeClass.EXTINCTION:
        render_extinction(current_year, outcome.final_state)
    elif outcome.outcome_class == OutcomeClass.TRANSCENDENCE:
        render_transcendence(current_year)

    render_final_summary(outcome)


def render_sprint(outcome: SimOutcome) -> None:
    """Render a full simulation in sprint mode (one line per decade)."""
    verdict_style = VERDICT_STYLES.get(outcome.outcome_class, "white")
    verdict_name = outcome.outcome_class.value.replace("-", " ")

    console.print(f'\n[bold white]SEED {outcome.seed}[/] · [italic]"{outcome.headline}"[/]')

    # Group events by decade
    decades: dict[str, list[SimEvent]] = {}
    for event in outcome.events:
        if event.status == EventStatus.HISTORICAL:
            continue
        year = event.year_month.split("-")[0] if "-" in event.year_month else "2000"
        decade = year[:3] + "0s"
        decades.setdefault(decade, []).append(event)

    for decade in sorted(decades.keys()):
        events = decades[decade]
        summaries = [e.title.split("(")[0].strip()[:30] for e in events[:4]]
        line = " ∙ ".join(summaries)
        if len(events) > 4:
            line += f" (+{len(events) - 4} more)"
        console.print(f"[bold white]{decade}[/]  {line}")

    console.print(
        f"[{verdict_style}]VERDICT: {verdict_name}[/] ({outcome.composite_score:+.2f}) ∙ "
        f"{outcome.total_divergences} divergences ∙ "
        f"{outcome.percentile:.0f}th percentile\n"
    )


def render_batch_summary(result) -> None:
    """Render batch mode summary."""
    from csim.models import BatchResult

    console.print("\n[bold white]Century Verdicts:[/]")

    # Sort by expected order
    order = [
        OutcomeClass.GOLDEN_AGE, OutcomeClass.PROGRESS,
        OutcomeClass.MUDDLING_THROUGH, OutcomeClass.DECLINE,
        OutcomeClass.CATASTROPHE, OutcomeClass.EXTINCTION,
        OutcomeClass.TRANSCENDENCE, OutcomeClass.RADICALLY_DIFFERENT,
    ]

    max_pct = max(result.outcome_distribution.values()) if result.outcome_distribution else 1.0

    for oc in order:
        pct = result.outcome_distribution.get(oc, 0.0) * 100
        bar_len = int(pct / max(max_pct * 100, 1) * 30)
        bar_len = min(bar_len, 30)
        bar = "█" * bar_len if bar_len > 0 else "▏" if pct > 0 else ""
        style = VERDICT_STYLES.get(oc, "white")
        name = oc.value.replace("-", " ")
        console.print(f"  [{style}]{name:<22s}[/] {pct:5.1f}%  {bar}")

    # Leverage nodes
    if result.highest_leverage_nodes:
        console.print("\n[bold white]Highest-leverage nodes:[/]")
        for i, (node_id, r2) in enumerate(result.highest_leverage_nodes[:10], 1):
            console.print(f"  {i:2d}. {node_id:<35s} r² = {r2:.2f}")

    console.print()


def _getch() -> str:
    """Read a single character from stdin without waiting for Enter."""
    import tty
    import termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def _render_interactive_help():
    console.print(
        "[dim]────────────────────────────────────────────────────────────────[/]"
    )
    console.print(
        "[dim]  ENTER/→ next  ·  ←/b back  ·  w world state  ·  "
        "d detail  ·  s skip to year  ·  q quit[/]"
    )


def _render_interactive_world_state(state: WorldState, year: str):
    """Show full world state in interactive mode."""
    composite = compute_composite_score(state)
    table = Table(title=f"World State — {year}", show_edge=False, pad_edge=False)
    table.add_column("Dimension", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Bar", min_width=20)

    dims = [
        ("Climate Anomaly", f"+{state.climate_temp_anomaly:.2f}°C", state.climate_temp_anomaly / 5.0, True),
        ("US Polarization", f"{state.us_polarization:.2f}", state.us_polarization, True),
        ("Nuclear Risk", f"{state.nuclear_risk_level:.2f}", state.nuclear_risk_level, True),
        ("Democracy Index", f"{state.global_democracy_index:.2f}", state.global_democracy_index, False),
        ("Inequality", f"{state.inequality_index:.2f}", state.inequality_index, True),
        ("US Standing", f"{state.us_global_standing:.2f}", state.us_global_standing, False),
        ("Renewables", f"{state.renewable_energy_share:.0%}", state.renewable_energy_share, False),
        ("Space Dev", f"{state.space_development_index:.2f}", state.space_development_index, False),
        ("Conflict Deaths", f"{state.conflict_deaths:,}", min(state.conflict_deaths / 1_000_000, 1.0), True),
        ("Existential Risk", f"{state.existential_risk_cumulative:.2f}", state.existential_risk_cumulative, True),
        ("Surveillance", f"{state.surveillance_state_index:.2f}", state.surveillance_state_index, True),
        ("Internet Freedom", f"{state.internet_freedom_index:.2f}", state.internet_freedom_index, False),
        ("AI Development", f"{state.ai_development_year_offset:+.0f}y", (state.ai_development_year_offset + 5) / 15, False),
        ("Pandemic Deaths", f"{state.global_pandemic_deaths:,}", min(state.global_pandemic_deaths / 10_000_000, 1.0), True),
    ]

    for label, value_str, ratio, bad_when_high in dims:
        ratio = max(0.0, min(1.0, ratio))
        filled = int(ratio * 20)
        if bad_when_high:
            color = "green" if ratio < 0.3 else "yellow" if ratio < 0.6 else "red"
        else:
            color = "red" if ratio < 0.3 else "yellow" if ratio < 0.6 else "green"
        bar = f"[{color}]{'█' * filled}[/][dim]{'░' * (20 - filled)}[/]"
        table.add_row(label, value_str, bar)

    console.print()
    console.print(table)
    console.print(f"\n  [bold]Composite Score:[/] {composite:+.3f}")
    console.print()


def render_interactive(outcome: SimOutcome, detail: str = "standard",
                       divergences_only: bool = False, domain_filter: str | None = None,
                       sound_engine=None) -> None:
    """Render simulation in interactive step-through mode."""
    width = console.width

    # Filter events
    events = outcome.events
    if divergences_only:
        events = [e for e in events if e.status != EventStatus.HISTORICAL]
    if domain_filter:
        events = [e for e in events if e.domain == domain_filter]

    if not events:
        console.print("[red]No events to display.[/]")
        return

    render_header(outcome.seed)
    console.print(f"  [dim]{len(events)} events · Interactive mode[/]\n")

    idx = 0
    current_era = ""
    current_detail = detail

    while 0 <= idx < len(events):
        event = events[idx]
        year = event.year_month.split("-")[0] if "-" in event.year_month else "2000"
        era_name, era_range = _era_for_year(int(year) if year.isdigit() else 2000)

        # Era transition
        if era_name != current_era:
            if sound_engine and current_era:
                sound_engine.play("era_transition")
            render_era_transition(era_name, era_range)
            current_era = era_name

        # Event counter
        console.print(f"[dim]  [{idx + 1}/{len(events)}][/]")

        # Render event
        render_event(event, detail=current_detail, width=width)

        # Sound
        if sound_engine and event.is_high_impact and event.status != EventStatus.HISTORICAL:
            sound_engine.play("divergence_major")

        # Prompt
        _render_interactive_help()

        # Read input
        while True:
            ch = _getch()
            if ch in ('\r', '\n', ' ', '\x1b'):
                # Enter, space, or start of arrow key
                if ch == '\x1b':
                    # Arrow key sequence
                    ch2 = _getch()
                    if ch2 == '[':
                        ch3 = _getch()
                        if ch3 == 'C':  # Right arrow
                            idx += 1
                            break
                        elif ch3 == 'D':  # Left arrow
                            idx = max(0, idx - 1)
                            break
                        else:
                            continue
                    else:
                        continue
                else:
                    idx += 1
                    break
            elif ch in ('b', 'B'):
                idx = max(0, idx - 1)
                break
            elif ch in ('w', 'W'):
                if outcome.final_state:
                    _render_interactive_world_state(outcome.final_state, year)
                else:
                    console.print("[dim]  World state not available[/]")
                continue
            elif ch in ('d', 'D'):
                levels = ["minimal", "standard", "full", "research"]
                ci = levels.index(current_detail) if current_detail in levels else 1
                current_detail = levels[(ci + 1) % len(levels)]
                console.print(f"[dim]  Detail: {current_detail}[/]")
                continue
            elif ch in ('s', 'S'):
                console.print("[bold]  Skip to year: [/]", end="")
                # Read year with echoing
                import termios, tty
                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                try:
                    target = input()
                except EOFError:
                    continue
                found = False
                for j, e in enumerate(events):
                    if e.year_month.startswith(target):
                        idx = j
                        found = True
                        break
                if not found:
                    console.print(f"[red]  Year {target} not found[/]")
                    continue
                break
            elif ch in ('q', 'Q'):
                console.print("\n[dim]  Exiting...[/]\n")
                return

    # Final summary
    if outcome.outcome_class == OutcomeClass.EXTINCTION:
        render_extinction(year, outcome.final_state)
    elif outcome.outcome_class == OutcomeClass.TRANSCENDENCE:
        render_transcendence(year)

    render_final_summary(outcome)
