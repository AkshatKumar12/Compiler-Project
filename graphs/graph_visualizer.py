from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
from graphviz import Digraph


def visualize_cfg(graph: nx.DiGraph, output_file: str) -> str:
    """
    Render a control-flow graph using Graphviz.

    Parameters
    ----------
    graph:
        The CFG as a `networkx.DiGraph`.
    output_file:
        Desired output file path, e.g. ``"cfg_output.png"``.

    Returns
    -------
    str
        The path to the generated file.
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine Graphviz output format from the file suffix.
    suffix = output_path.suffix.lstrip(".") or "png"

    dot = Digraph(format=suffix)
    dot.attr(rankdir="TB", fontsize="10")

    # Add nodes with informative labels.
    for node_id, data in graph.nodes(data=True):
        node_type = data.get("type", "node")
        line = data.get("line")
        func = data.get("func")

        label_parts = [f"{node_id}", node_type]
        if func:
            label_parts.append(f"func={func}")
        if line is not None:
            label_parts.append(f"L{line}")

        label = "\\n".join(label_parts)
        dot.node(str(node_id), label=label, shape="box")

    # Add edges.
    for u, v in graph.edges():
        dot.edge(str(u), str(v))

    # Graphviz expects a filename without extension; it appends the format.
    rendered_path = dot.render(filename=output_path.stem, directory=str(output_path.parent), cleanup=True)
    return str(rendered_path)

