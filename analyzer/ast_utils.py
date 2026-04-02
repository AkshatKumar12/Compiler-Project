from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, Optional

from pycparser import c_ast


LoopNode = c_ast.For | c_ast.While | c_ast.DoWhile


def is_loop(node: c_ast.Node) -> bool:
    """Return True if the node represents any loop construct."""
    return isinstance(node, (c_ast.For, c_ast.While, c_ast.DoWhile))


def is_conditional(node: c_ast.Node) -> bool:
    """Return True if the node represents a conditional (if-statement)."""
    return isinstance(node, c_ast.If)


def is_function_def(node: c_ast.Node) -> bool:
    """Return True if the node is a function definition."""
    return isinstance(node, c_ast.FuncDef)


def is_variable_decl(node: c_ast.Node) -> bool:
    """
    Return True if the node is a variable declaration (not a function).

    pycparser represents declarations using `Decl` nodes. Function
    declarations/definitions use a `FuncDecl` type, so we exclude those
    to count only variables.
    """
    if not isinstance(node, c_ast.Decl):
        return False

    # Function declarations use FuncDecl as their type.
    return not isinstance(node.type, c_ast.FuncDecl)


def iter_children(node: c_ast.Node) -> Iterator[c_ast.Node]:
    """
    Yield all direct child nodes of the given AST node.

    This uses pycparser's `children()` API which returns (name, child) pairs.
    """
    for _, child in node.children():
        yield child


def walk_ast(node: c_ast.Node) -> Iterator[c_ast.Node]:
    """
    Recursively traverse the AST yielding all nodes in depth-first order.
    """
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        # Extend stack with children in reverse order to maintain intuitive
        # left-to-right depth-first traversal.
        children = list(iter_children(current))
        stack.extend(reversed(children))


@dataclass
class LoopStatistics:
    """Basic statistics about loop usage in an AST."""

    total_loops: int = 0
    nested_loops: int = 0
    max_nesting_depth: int = 0


def compute_loop_statistics(root: c_ast.Node) -> LoopStatistics:
    """
    Compute loop-related statistics, including nested loops.

    Nested loops are counted as the number of loops that appear inside
    another loop (i.e. loops at depth > 1).
    """
    stats = LoopStatistics()

    def _traverse(node: c_ast.Node, loop_depth: int) -> None:
        if is_loop(node):
            stats.total_loops += 1
            if loop_depth >= 1:
                # Any loop found while already inside another loop is nested.
                stats.nested_loops += 1
            loop_depth += 1
            stats.max_nesting_depth = max(stats.max_nesting_depth, loop_depth)

        for child in iter_children(node):
            _traverse(child, loop_depth)

    _traverse(root, loop_depth=0)
    return stats


def count_nodes(root: c_ast.Node, predicate: Callable[[c_ast.Node], bool]) -> int:
    """
    Count nodes in the AST that satisfy the given predicate.
    """
    return sum(1 for node in walk_ast(root) if predicate(node))

