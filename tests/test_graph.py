"""Tests for graph construction and dependency resolution."""

import pytest
from pathlib import Path

from csim.graph import build_graph, get_modified_distribution, is_reachable, validate_probabilities
from csim.world_state import WorldState

DATA_DIR = Path(__file__).parent.parent / "src" / "csim" / "data"


@pytest.fixture
def graph():
    return build_graph(DATA_DIR)


class TestGraphConstruction:
    def test_graph_loads(self, graph):
        assert len(graph.nodes) > 0

    def test_no_cycles(self, graph):
        import networkx as nx
        assert nx.is_directed_acyclic_graph(graph)

    def test_traversal_order_exists(self, graph):
        assert "traversal_order" in graph.graph
        assert len(graph.graph["traversal_order"]) > 0

    def test_traversal_order_chronological(self, graph):
        order = graph.graph["traversal_order"]
        year_months = []
        for node_id in order:
            ym = graph.nodes[node_id].get("year_month", "9999-12")
            year_months.append(ym)
        assert year_months == sorted(year_months)

    def test_all_nodes_have_id(self, graph):
        for node_id in graph.nodes:
            assert "id" in graph.nodes[node_id]
            assert graph.nodes[node_id]["id"] == node_id

    def test_all_nodes_have_year_month(self, graph):
        for node_id in graph.nodes:
            assert "year_month" in graph.nodes[node_id]


class TestProbabilities:
    def test_all_probabilities_valid(self, graph):
        errors = validate_probabilities(graph)
        assert errors == [], f"Probability errors: {errors}"


class TestModifiedDistribution:
    def test_base_distribution(self, graph):
        # 2000_election has no dependencies, so distribution should be unmodified
        dist = get_modified_distribution("2000_election", {}, graph)
        assert abs(sum(dist.values()) - 1.0) < 0.01
        assert "bush_wins" in dist
        assert "gore_wins" in dist

    def test_dependency_modifies_distribution(self, graph):
        # Iraq war with plot_disrupted 9/11 should shift probabilities
        results = {"2001_911": "plot_disrupted", "2000_election": "gore_wins"}
        dist = get_modified_distribution("2003_iraq", results, graph)
        assert abs(sum(dist.values()) - 1.0) < 0.01
        # full_invasion should be much lower
        base = get_modified_distribution("2003_iraq", {}, graph)
        assert dist.get("full_invasion", 0) < base.get("full_invasion", 1)

    def test_renormalization(self, graph):
        # Even with extreme modifications, should still sum to 1
        for node_id in graph.nodes:
            dist = get_modified_distribution(node_id, {}, graph)
            if dist:
                assert abs(sum(dist.values()) - 1.0) < 0.01


class TestReachability:
    def test_unconditional_always_reachable(self, graph):
        state = WorldState()
        assert is_reachable("2000_election", {}, graph, state)

    def test_jan6_blocked_by_trump_2020(self, graph):
        state = WorldState()
        results = {"2020_us_election": "trump_wins"}
        assert not is_reachable("2021_jan6", results, graph, state)

    def test_jan6_allowed_by_biden_2020(self, graph):
        state = WorldState()
        results = {"2020_us_election": "biden_wins"}
        assert is_reachable("2021_jan6", results, graph, state)

    def test_covid_response_blocked_by_no_pandemic(self, graph):
        state = WorldState()
        results = {"2019_covid_emergence": "no_pandemic"}
        assert not is_reachable("2020_covid_response", results, graph, state)

    def test_extinction_blocks_all(self, graph):
        state = WorldState()
        assert not is_reachable("2000_election", {}, graph, state, extinct=True)
