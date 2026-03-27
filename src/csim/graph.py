"""DAG construction and dependency resolution from YAML node files."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import yaml

from csim.world_state import WorldState, _evaluate_condition


def build_graph(scenario_dir: Path) -> nx.DiGraph:
    """Parse all node YAML files into a networkx DiGraph.

    - Nodes keyed by id
    - Nodes store their full YAML data as attributes
    - Edges encode dependencies (upstream -> downstream)
    - Validates: no cycles, all referenced nodes exist, probabilities sum to ~1.0
    - Returns graph with topological traversal order stored as attribute
    """
    G = nx.DiGraph()
    nodes_dir = scenario_dir / "nodes"

    if not nodes_dir.exists():
        raise FileNotFoundError(f"Nodes directory not found: {nodes_dir}")

    # Load all node YAML files
    node_data: dict[str, dict] = {}
    for yaml_file in sorted(nodes_dir.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if data and "id" in data:
            node_data[data["id"]] = data

    # Add nodes to graph
    for node_id, data in node_data.items():
        G.add_node(node_id, **data)

    # Add dependency edges
    for node_id, data in node_data.items():
        for dep in data.get("dependencies", []) or []:
            if isinstance(dep, dict):
                upstream = dep["node"]
            else:
                upstream = dep
            if upstream in node_data:
                G.add_edge(upstream, node_id, dep_data=dep if isinstance(dep, dict) else {"node": upstream})

        # Also parse cascading_modifiers in outcomes to build edges
        for branch_name, outcome in (data.get("outcomes") or {}).items():
            if not isinstance(outcome, dict):
                continue
            for target_spec in (outcome.get("cascading_modifiers") or {}).keys():
                # Format: "downstream_node.branch" or "downstream_node.distribution.param"
                target_node = target_spec.split(".")[0]
                if target_node in node_data and target_node != node_id:
                    if not G.has_edge(node_id, target_node):
                        G.add_edge(node_id, target_node, dep_data={"node": node_id})

    # Validate no cycles
    if not nx.is_directed_acyclic_graph(G):
        cycles = list(nx.simple_cycles(G))
        raise ValueError(f"Graph contains cycles: {cycles[:3]}")

    # Compute traversal order: chronological primary, topological secondary
    traversal = _compute_traversal_order(G, node_data)
    G.graph["traversal_order"] = traversal

    return G


def _compute_traversal_order(G: nx.DiGraph, node_data: dict) -> list[str]:
    """Sort nodes chronologically, breaking ties with topological order."""
    topo_order = {n: i for i, n in enumerate(nx.topological_sort(G))}

    def sort_key(node_id):
        data = node_data.get(node_id, {})
        year_month = data.get("year_month", "9999-12")
        topo_idx = topo_order.get(node_id, 9999)
        return (year_month, topo_idx)

    return sorted(node_data.keys(), key=sort_key)


def validate_probabilities(G: nx.DiGraph) -> list[str]:
    """Validate that all categorical distributions sum to ~1.0."""
    errors = []
    for node_id in G.nodes:
        data = G.nodes[node_id]
        dist = data.get("distribution", {})
        if not dist:
            # Try options shorthand
            options = data.get("options", {})
            if options:
                total = sum(options.values())
                if abs(total - 1.0) > 0.01:
                    errors.append(f"{node_id}: options sum to {total:.3f}")
            continue
        if dist.get("type") == "categorical":
            options = dist.get("options", {})
            total = sum(options.values())
            if abs(total - 1.0) > 0.01:
                errors.append(f"{node_id}: distribution options sum to {total:.3f}")
    return errors


def get_modified_distribution(
    node_id: str,
    results: dict[str, str],
    graph: nx.DiGraph,
    cascading_effects: dict[str, dict] | None = None,
) -> dict[str, float]:
    """Compute adjusted probability distribution for a node given upstream results.

    1. Start with base probabilities
    2. Apply dependency modifications
    3. Apply cascading_modifiers from upstream outcomes
    4. Clamp all branches to [0, 1]
    5. Renormalize to sum to 1.0
    """
    data = graph.nodes[node_id]

    # Get base distribution
    dist = data.get("distribution", {})
    if dist and dist.get("type") == "categorical":
        probs = dict(dist.get("options", {}))
    elif "options" in data:
        # Abbreviated format
        probs = dict(data["options"])
    else:
        return {}

    if not probs:
        return {}

    # Apply dependency modifications
    for dep in data.get("dependencies", []) or []:
        if isinstance(dep, dict):
            upstream_node = dep["node"]
            dep_branch = dep.get("branch")
            modifies = dep.get("modifies", {})

            upstream_result = results.get(upstream_node)
            if upstream_result is None:
                continue

            # Apply if the upstream took the specified branch (or any branch if not specified)
            if dep_branch is None or upstream_result == dep_branch:
                for branch, shift in modifies.items():
                    if branch in probs:
                        probs[branch] = probs[branch] + float(str(shift).lstrip("+"))

    # Apply cascading modifiers from upstream outcomes
    if cascading_effects:
        for target_spec, shift_value in cascading_effects.items():
            parts = target_spec.split(".")
            if parts[0] == node_id and len(parts) >= 2:
                branch = parts[1]
                if branch in probs:
                    probs[branch] = probs[branch] + float(str(shift_value).lstrip("+"))

    # Clamp to [0, 1] and renormalize
    probs = {k: max(0.0, v) for k, v in probs.items()}
    total = sum(probs.values())

    if total == 0:
        # Uniform fallback
        n = len(probs)
        probs = {k: 1.0 / n for k in probs}
    else:
        probs = {k: v / total for k, v in probs.items()}

    return probs


def is_reachable(
    node_id: str,
    results: dict[str, str],
    graph: nx.DiGraph,
    world_state: WorldState,
    extinct: bool = False,
) -> bool:
    """Check if a node should fire given upstream results and world state.

    A node fires if:
    1. The simulation hasn't terminated early (extinction)
    2. Its conditional expression evaluates to True against current world state
    3. It has no unmet upstream constraints
    """
    if extinct:
        return False

    data = graph.nodes[node_id]

    # Check conditional gating
    conditional = data.get("conditional")
    if conditional:
        # Handle "node_id != branch" style conditions
        if "!=" in conditional and not any(op in conditional for op in [">", "<", ">="]):
            parts = conditional.split("!=")
            ref_node = parts[0].strip()
            ref_branch = parts[1].strip()
            if ref_node in results and results[ref_node] == ref_branch:
                return False
        elif "==" in conditional and not any(op in conditional for op in [">", "<", ">="]):
            parts = conditional.split("==")
            ref_node = parts[0].strip()
            ref_branch = parts[1].strip()
            if ref_node in results and results[ref_node] != ref_branch:
                return False
        else:
            # World state condition
            if not _evaluate_condition(world_state, conditional):
                return False

    return True
