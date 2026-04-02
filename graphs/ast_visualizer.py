from __future__ import annotations

from pathlib import Path
from typing import Any

from graphviz import Digraph
from pycparser import c_ast


def _node_label(node: c_ast.Node) -> str:
    """
    Build a compact, informative label for an AST node.
    """
    node_type = type(node).__name__
    parts = [node_type]

    # Attach common attributes (e.g. identifier names) when present.
    for attr in ("name", "op", "value"):
        if hasattr(node, attr):
            val = getattr(node, attr)
            if isinstance(val, str):
                parts.append(f"{attr}={val}")

    # Add source location if available.
    coord = getattr(node, "coord", None)
    if coord is not None and getattr(coord, "line", None):
        parts.append(f"L{coord.line}")

    return "\\n".join(parts)


def visualize_ast(ast: c_ast.Node, output_file: str) -> str:
    """
    Render a pycparser AST as a Graphviz diagram.

    Parameters
    ----------
    ast:
        Root of the AST (typically ``c_ast.FileAST``).
    output_file:
        Target output file, e.g. ``\"ast_sample.png\"``.

    Returns
    -------
    str
        Path to the generated file.
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = output_path.suffix.lstrip(".") or "png"

    dot = Digraph(format=suffix)
    dot.attr(rankdir="TB", fontsize="10")

    # We assign deterministic IDs based on object identity.
    id_map: dict[int, str] = {}

    def get_id(node: c_ast.Node) -> str:
        obj_id = id(node)
        if obj_id not in id_map:
            id_map[obj_id] = str(len(id_map))
        return id_map[obj_id]

    def visit(node: c_ast.Node) -> None:
        node_id = get_id(node)
        dot.node(node_id, label=_node_label(node), shape="box")

        for _, child in node.children():
            child_id = get_id(child)
            dot.edge(node_id, child_id)
            visit(child)

    visit(ast)

    rendered_path = dot.render(
        filename=output_path.stem,
        directory=str(output_path.parent),
        cleanup=True,
    )
    return str(rendered_path)

