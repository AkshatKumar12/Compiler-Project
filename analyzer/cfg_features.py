from __future__ import annotations

from typing import Dict

import networkx as nx


def _average_branching_factor(graph: nx.DiGraph) -> float:
    """
    Compute the average branching factor of the CFG.

    This is defined as the mean out-degree over all nodes that have at
    least one outgoing edge.
    """
    out_degrees = [deg for _, deg in graph.out_degree() if deg > 0]
    if not out_degrees:
        return 0.0
    return float(sum(out_degrees)) / float(len(out_degrees))


def _max_path_length(graph: nx.DiGraph) -> int:
    """
    Estimate the maximum path length in the CFG.

    Exact longest simple path computation is exponential in general graphs.
    Here we approximate it by computing the maximum shortest-path distance
    between any pair of nodes in the same weakly connected component.
    """
    if graph.number_of_nodes() == 0:
        return 0

    max_len = 0
    # Work on each weakly connected component separately for efficiency.
    for component_nodes in nx.weakly_connected_components(graph):
        sub = graph.subgraph(component_nodes)
        for source in sub.nodes():
            lengths = nx.single_source_shortest_path_length(sub, source)
            if lengths:
                local_max = max(lengths.values())
                if local_max > max_len:
                    max_len = local_max
    return int(max_len)


def _loop_count(graph: nx.DiGraph) -> int:
    """
    Estimate number of loops in the CFG.

    For this research prototype we approximate loop count as the number of
    loop-related nodes present in the graph.
    """
    loop_types = {"for", "while", "do_while"}
    count = 0
    for _, data in graph.nodes(data=True):
        if data.get("type") in loop_types:
            count += 1
    return count


def cyclomatic_complexity(graph: nx.DiGraph) -> int:
    """
    Compute cyclomatic complexity of the CFG.

    Uses the classic McCabe formula:

    M = E - N + 2P

    where:
      - E: number of edges
      - N: number of nodes
      - P: number of connected components (we use weakly-connected here)
    """
    E = graph.number_of_edges()
    N = graph.number_of_nodes()
    P = nx.number_weakly_connected_components(graph) if N > 0 else 0
    return int(E - N + 2 * P)


def extract_cfg_features(graph: nx.DiGraph) -> Dict[str, float]:
    """
    Extract structural features from a control-flow graph.

    Returns
    -------
    dict
        Dictionary with keys such as:

        - ``nodes``: number of CFG nodes
        - ``edges``: number of CFG edges
        - ``branching_factor``: average out-degree
        - ``loops``: approximate loop count
        - ``max_path_length``: estimated maximal path length
        - ``cyclomatic_complexity``: McCabe complexity
    """
    nodes = graph.number_of_nodes()
    edges = graph.number_of_edges()

    features: Dict[str, float] = {
        "nodes": float(nodes),
        "edges": float(edges),
        "branching_factor": _average_branching_factor(graph),
        "loops": float(_loop_count(graph)),
        "max_path_length": float(_max_path_length(graph)),
        "cyclomatic_complexity": float(cyclomatic_complexity(graph)),
    }
    return features

