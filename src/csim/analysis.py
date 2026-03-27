"""Batch statistics, sensitivity analysis, and what-if analysis."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from csim.engine import simulate, simulate_batch
from csim.models import BatchResult, OutcomeClass, SimOutcome


def sensitivity_analysis(
    graph,
    node_id: str,
    metric: str = "composite_score",
    iterations: int = 1000,
) -> dict:
    """Analyze how a specific node's branches affect a metric.

    Returns per-branch statistics for the specified metric.
    """
    seeds = list(range(iterations))
    outcomes = [simulate(graph, s) for s in seeds]

    # Group by branch taken at the specified node
    branch_groups: dict[str, list[float]] = {}
    for outcome in outcomes:
        branch = None
        for event in outcome.events:
            if event.node_id == node_id:
                branch = event.branch_taken
                break
        if branch is None:
            branch = "__skipped__"

        if metric == "composite_score":
            value = outcome.composite_score
        elif hasattr(outcome.final_state, metric):
            value = float(getattr(outcome.final_state, metric))
        else:
            continue

        branch_groups.setdefault(branch, []).append(value)

    result = {}
    for branch, values in sorted(branch_groups.items()):
        result[branch] = {
            "count": len(values),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "p5": float(np.percentile(values, 5)),
            "p95": float(np.percentile(values, 95)),
        }

    return result


def what_if_analysis(
    graph,
    overrides: dict[str, str],
    iterations: int = 1000,
) -> tuple[BatchResult, BatchResult]:
    """Run simulations with forced branch selections vs. baseline.

    Returns (baseline_result, overridden_result).
    """
    import copy
    import networkx as nx

    seeds = list(range(iterations))

    # Baseline
    baseline = simulate_batch(graph, iterations, seeds)

    # Override: modify graph to force specific branches
    override_graph = copy.deepcopy(graph)
    for node_id, forced_branch in overrides.items():
        if node_id in override_graph.nodes:
            data = override_graph.nodes[node_id]
            dist = data.get("distribution", {})
            if dist and dist.get("type") == "categorical":
                options = dist.get("options", {})
                # Set forced branch to 1.0, others to 0.0
                for b in options:
                    options[b] = 1.0 if b == forced_branch else 0.0
            elif "options" in data:
                options = data["options"]
                for b in list(options.keys()):
                    options[b] = 1.0 if b == forced_branch else 0.0

    overridden = simulate_batch(override_graph, iterations, seeds)

    return baseline, overridden


def diff_runs(outcome_a: SimOutcome, outcome_b: SimOutcome) -> dict:
    """Compare two simulation runs."""
    events_a = {e.node_id: e for e in outcome_a.events}
    events_b = {e.node_id: e for e in outcome_b.events}

    differences = []
    all_nodes = sorted(set(events_a.keys()) | set(events_b.keys()))

    for node_id in all_nodes:
        ea = events_a.get(node_id)
        eb = events_b.get(node_id)
        if ea and eb and ea.branch_taken != eb.branch_taken:
            differences.append({
                "node_id": node_id,
                "year_month": ea.year_month,
                "title": ea.title,
                "seed_a_branch": ea.branch_taken,
                "seed_b_branch": eb.branch_taken,
            })
        elif ea and not eb:
            differences.append({
                "node_id": node_id,
                "year_month": ea.year_month,
                "title": ea.title,
                "seed_a_branch": ea.branch_taken,
                "seed_b_branch": "__skipped__",
            })
        elif eb and not ea:
            differences.append({
                "node_id": node_id,
                "year_month": eb.year_month,
                "title": eb.title,
                "seed_a_branch": "__skipped__",
                "seed_b_branch": eb.branch_taken,
            })

    return {
        "seed_a": outcome_a.seed,
        "seed_b": outcome_b.seed,
        "score_a": outcome_a.composite_score,
        "score_b": outcome_b.composite_score,
        "verdict_a": outcome_a.outcome_class.value,
        "verdict_b": outcome_b.outcome_class.value,
        "differences": differences,
        "total_differences": len(differences),
    }
