"""Simulation engine — DAG traversal, sampling, and batch execution."""

from __future__ import annotations

import copy
import os
from multiprocessing import Pool
from pathlib import Path
from typing import Optional

import networkx as nx
import numpy as np

from csim.graph import build_graph, get_modified_distribution, is_reachable
from csim.models import BatchResult, EventStatus, SimEvent, SimOutcome
from csim.world_state import (
    WorldState,
    apply_effects,
    classify_outcome,
    compute_composite_score,
    compute_world_state_delta,
    generate_headline,
)


def sample(distribution: dict[str, float], rng: np.random.Generator) -> str:
    """Sample from a categorical distribution."""
    if not distribution:
        raise ValueError("Empty distribution")
    branches = list(distribution.keys())
    probs = [distribution[b] for b in branches]
    return branches[rng.choice(len(branches), p=probs)]


def simulate(
    graph: nx.DiGraph,
    seed: int,
    initial_state: Optional[WorldState] = None,
    locked_results: Optional[dict[str, str]] = None,
) -> SimOutcome:
    """Core simulation loop for a single run.

    1. Initialize WorldState to year-2000 baselines (or *initial_state*)
    2. Initialize numpy RNG with seed
    3. For each node in chronological/topological order:
       a. Check reachability
       b. Compute modified probability distribution
       c. Sample from distribution (or use *locked_results* if provided)
       d. Apply world_state_effects
       e. Record SimEvent
       f. Check for early termination (extinction)
    4. Compute composite score, classify, generate headline
    5. Return SimOutcome

    Args:
        graph: The simulation DAG.
        seed: RNG seed for reproducibility.
        initial_state: If provided, use instead of default year-2000 WorldState.
        locked_results: If provided, a dict of node_id -> branch that should be
            used instead of sampling.  World-state effects from locked nodes
            are still applied.
    """
    rng = np.random.default_rng(seed)
    state = copy.copy(initial_state) if initial_state is not None else WorldState()
    events: list[SimEvent] = []
    results: dict[str, str] = {}  # node_id -> branch_taken
    cascading_effects: dict[str, dict] = {}  # accumulated cascading modifiers
    extinct = False

    traversal = graph.graph.get("traversal_order", list(nx.topological_sort(graph)))

    for node_id in traversal:
        if node_id not in graph.nodes:
            continue

        data = graph.nodes[node_id]

        # Check reachability
        if not is_reachable(node_id, results, graph, state, extinct):
            continue

        # Get modified distribution
        probs = get_modified_distribution(node_id, results, graph, cascading_effects)
        if not probs:
            continue

        # Sample (or use locked result for historical nodes)
        if locked_results and node_id in locked_results:
            branch = locked_results[node_id]
            # Validate that the locked branch exists in the distribution
            if branch not in probs:
                # Fall back to sampling if locked branch is invalid
                branch = sample(probs, rng)
        else:
            branch = sample(probs, rng)
        results[node_id] = branch

        # Get outcome data
        outcomes = data.get("outcomes", {})
        outcome_data = outcomes.get(branch, {}) if isinstance(outcomes, dict) else {}

        # Determine status
        if isinstance(outcome_data, dict):
            status_str = outcome_data.get("status", "HISTORICAL")
        else:
            status_str = "HISTORICAL"

        try:
            status = EventStatus(status_str)
        except ValueError:
            status = EventStatus.HISTORICAL

        # Apply world state effects
        effects = {}
        if isinstance(outcome_data, dict):
            effects = outcome_data.get("world_state_effects", {}) or {}

        old_state = copy.copy(state)
        if effects:
            state = apply_effects(state, effects)

        # Track divergences
        if status != EventStatus.HISTORICAL:
            state.total_divergences += 1
            if state.first_divergence_year is None:
                state.first_divergence_year = data.get("year_month", "")

        # Compute delta for display
        ws_delta = compute_world_state_delta(old_state, state)
        is_high_impact = sum(abs(v) for v in ws_delta.values()) > 0.10

        # Record event
        # Skip silent outcomes (non-events like "no assassination happened")
        is_silent = isinstance(outcome_data, dict) and outcome_data.get("silent", False)
        if not is_silent:
            event = SimEvent(
                year_month=data.get("year_month", ""),
                node_id=node_id,
                title=data.get("title", node_id),
                description=outcome_data.get("description", "") if isinstance(outcome_data, dict) else str(outcome_data),
                status=status,
                branch_taken=branch,
                domain=data.get("domain", ""),
                probability_of_branch=probs.get(branch, 0.0),
                explanation=outcome_data.get("explanation") if isinstance(outcome_data, dict) else None,
                world_state_delta=ws_delta,
                is_high_impact=is_high_impact,
                confidence=data.get("confidence", "HIGH"),
            )
            events.append(event)

        # Accumulate cascading modifiers for downstream nodes
        if isinstance(outcome_data, dict):
            for target, shift in (outcome_data.get("cascading_modifiers") or {}).items():
                cascading_effects[target] = shift

        # Track largest divergence
        if ws_delta and status != EventStatus.HISTORICAL:
            delta_magnitude = sum(abs(v) for v in ws_delta.values())
            current_largest_mag = 0.0
            if state.largest_divergence:
                # Compare with stored largest
                for e in events[:-1]:
                    if e.node_id == state.largest_divergence:
                        current_largest_mag = sum(abs(v) for v in e.world_state_delta.values())
                        break
            if delta_magnitude > current_largest_mag:
                state.largest_divergence = node_id

        # Check for early termination
        if state.existential_risk_cumulative > 0.9:
            extinct = True

    # Final scoring
    composite = compute_composite_score(state)
    outcome_class = classify_outcome(state, events)
    headline = generate_headline(state, events)

    return SimOutcome(
        seed=seed,
        events=events,
        final_state=state,
        outcome_class=outcome_class,
        headline=headline,
        composite_score=composite,
        total_divergences=state.total_divergences,
        first_divergence_year=state.first_divergence_year,
        largest_divergence_node=state.largest_divergence,
    )


def _simulate_worker(
    graph_data: dict,
    seed: int,
    initial_state: Optional[WorldState] = None,
    locked_results: Optional[dict[str, str]] = None,
) -> SimOutcome:
    """Worker function for parallel batch simulation.

    Accepts serialised graph data (via ``nx.node_link_data``) and a seed.
    Each worker reconstructs the DiGraph from the serialised form so that the
    graph never needs to be pickled directly.
    """
    graph = nx.node_link_graph(graph_data)
    return simulate(graph, seed, initial_state=initial_state, locked_results=locked_results)


def simulate_batch(
    graph: nx.DiGraph,
    iterations: int,
    seeds: Optional[list[int]] = None,
    parallel: int = 1,
    initial_state: Optional[WorldState] = None,
    locked_results: Optional[dict[str, str]] = None,
) -> BatchResult:
    """Run N simulations, optionally parallelized."""
    if seeds is None:
        seeds = list(range(iterations))

    if parallel > 1:
        # Cap workers at CPU count to avoid oversubscription
        workers = min(parallel, os.cpu_count() or 1)
        graph_data = nx.node_link_data(graph)
        with Pool(workers) as pool:
            outcomes = pool.starmap(
                _simulate_worker,
                [(graph_data, s, initial_state, locked_results) for s in seeds],
            )
    else:
        outcomes = [
            simulate(graph, s, initial_state=initial_state, locked_results=locked_results)
            for s in seeds
        ]

    # Compute statistics
    result = BatchResult(iterations=len(outcomes), outcomes=outcomes)
    _compute_batch_stats(result)
    return result


def _compute_batch_stats(result: BatchResult) -> None:
    """Compute aggregate statistics for a batch."""
    from csim.models import OutcomeClass

    # Outcome distribution
    counts: dict[OutcomeClass, int] = {}
    for o in result.outcomes:
        counts[o.outcome_class] = counts.get(o.outcome_class, 0) + 1
    total = len(result.outcomes)
    result.outcome_distribution = {k: v / total for k, v in counts.items()}

    # Composite score percentiles
    scores = sorted(o.composite_score for o in result.outcomes)
    for o in result.outcomes:
        rank = sum(1 for s in scores if s <= o.composite_score)
        o.percentile = (rank / total) * 100

    # Dimension statistics
    if result.outcomes and result.outcomes[0].final_state:
        from dataclasses import fields as dc_fields
        for f in dc_fields(WorldState):
            if f.name.startswith("_"):
                continue
            vals = []
            for o in result.outcomes:
                if o.final_state:
                    v = getattr(o.final_state, f.name)
                    if isinstance(v, (int, float)):
                        vals.append(float(v))
            if vals:
                result.dimension_stats[f.name] = {
                    "mean": np.mean(vals),
                    "std": np.std(vals),
                    "min": np.min(vals),
                    "max": np.max(vals),
                    "p5": np.percentile(vals, 5),
                    "p95": np.percentile(vals, 95),
                }

    # Highest leverage nodes (variance of composite score explained by each node)
    _compute_leverage(result)


def _compute_leverage(result: BatchResult) -> None:
    """Compute which nodes have highest leverage on composite score."""
    if len(result.outcomes) < 10:
        return

    # Collect all node_ids and their branch choices
    node_branches: dict[str, dict[str, list[float]]] = {}
    for outcome in result.outcomes:
        for event in outcome.events:
            if event.node_id not in node_branches:
                node_branches[event.node_id] = {}
            branch = event.branch_taken
            if branch not in node_branches[event.node_id]:
                node_branches[event.node_id][branch] = []
            node_branches[event.node_id][branch].append(outcome.composite_score)

    # For each node, compute r² (fraction of variance explained)
    overall_var = np.var([o.composite_score for o in result.outcomes])
    if overall_var == 0:
        return

    leverage: list[tuple[str, float]] = []
    for node_id, branches in node_branches.items():
        if len(branches) < 2:
            continue
        # Between-group variance
        group_means = []
        group_sizes = []
        for scores in branches.values():
            if scores:
                group_means.append(np.mean(scores))
                group_sizes.append(len(scores))
        if len(group_means) < 2:
            continue
        overall_mean = np.mean([o.composite_score for o in result.outcomes])
        between_var = sum(
            n * (m - overall_mean) ** 2 for m, n in zip(group_means, group_sizes)
        ) / sum(group_sizes)
        r_squared = min(between_var / overall_var, 1.0)
        leverage.append((node_id, r_squared))

    result.highest_leverage_nodes = sorted(leverage, key=lambda x: x[1], reverse=True)[:20]
