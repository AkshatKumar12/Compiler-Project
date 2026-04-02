from __future__ import annotations

from typing import Dict

from pycparser import c_ast

from . import ast_utils


def count_functions(ast: c_ast.FileAST) -> int:
    """Count function definitions in the AST."""
    return ast_utils.count_nodes(ast, ast_utils.is_function_def)


def count_loops(ast: c_ast.FileAST) -> int:
    """Count all loop constructs (for, while, do-while) in the AST."""
    loop_stats = ast_utils.compute_loop_statistics(ast)
    return loop_stats.total_loops


def count_nested_loops(ast: c_ast.FileAST) -> int:
    """
    Count nested loops in the AST.

    A nested loop is any loop that appears lexically inside another loop.
    """
    loop_stats = ast_utils.compute_loop_statistics(ast)
    return loop_stats.nested_loops


def count_conditionals(ast: c_ast.FileAST) -> int:
    """Count conditional statements (if) in the AST."""
    return ast_utils.count_nodes(ast, ast_utils.is_conditional)


def count_variables(ast: c_ast.FileAST) -> int:
    """Count variable declarations in the AST."""
    return ast_utils.count_nodes(ast, ast_utils.is_variable_decl)


def count_lines(code: str) -> int:
    """
    Approximate the number of lines of code.

    This counts non-empty, non-comment (`//`) lines. Block comments are
    not treated specially and may still be counted.
    """
    count = 0
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("//"):
            continue
        count += 1
    return count


def compute_metrics(ast: c_ast.FileAST, code: str) -> Dict[str, int]:
    """
    Compute a collection of structural metrics for the C program.

    Returns
    -------
    dict
        Dictionary containing metrics such as number of functions, loops,
        nested loops, conditionals, variables, and lines of code.
    """
    metrics: Dict[str, int] = {
        "functions": count_functions(ast),
        "loops": count_loops(ast),
        "nested_loops": count_nested_loops(ast),
        "conditionals": count_conditionals(ast),
        "variables": count_variables(ast),
        "lines_of_code": count_lines(code),
    }
    return metrics

