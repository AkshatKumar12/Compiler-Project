from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from analyzer.ast_parser import ASTParsingError, parse_c_code
from analyzer.cfg_builder import build_cfg
from analyzer.cfg_features import extract_cfg_features
from analyzer.code_metrics import compute_metrics
from compiler.compile_checker import compile_c_file
from utils.file_loader import FileLoadingError, load_c_file


def run_pipeline(source_path: str) -> int:
    """
    Execute the analysis pipeline on a C source file.

    Steps:
    1. Load code from disk.
    2. Check compilation using GCC.
    3. If compilation succeeds, parse AST and compute metrics.
    """
    try:
        code = load_c_file(source_path)
    except FileLoadingError as exc:
        print(f"Error loading file: {exc}", file=sys.stderr)
        return 1

    compile_result = compile_c_file(source_path)

    if compile_result["compiled"]:
        print("Compilation: SUCCESS")
    else:
        print("Compilation: FAILURE")
        errors = compile_result.get("errors") or []
        if errors:
            print("Compiler errors:")
            for line in errors:
                print(f"  {line}")
        # For this research tool we stop if compilation fails.
        return 1

    try:
        ast = parse_c_code(code)
    except ASTParsingError as exc:
        print(f"AST parsing failed: {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # AST-based code metrics
    # ------------------------------------------------------------------
    code_metrics: Dict[str, Any] = compute_metrics(ast, code)

    print("\nCode Metrics:")
    print(f"Functions: {code_metrics.get('functions', 0)}")
    print(f"Loops: {code_metrics.get('loops', 0)}")
    print(f"Nested Loops: {code_metrics.get('nested_loops', 0)}")
    print(f"Conditionals: {code_metrics.get('conditionals', 0)}")
    print(f"Variables: {code_metrics.get('variables', 0)}")
    print(f"Lines: {code_metrics.get('lines_of_code', 0)}")

    # ------------------------------------------------------------------
    # CFG construction & features
    # ------------------------------------------------------------------
    cfg = build_cfg(ast)
    cfg_metrics: Dict[str, Any] = extract_cfg_features(cfg)

    print("\nCFG Metrics:")
    print(f"Nodes: {int(cfg_metrics.get('nodes', 0))}")
    print(f"Edges: {int(cfg_metrics.get('edges', 0))}")
    print(f"Cyclomatic Complexity: {int(cfg_metrics.get('cyclomatic_complexity', 0))}")
    print(f"Branching Factor: {cfg_metrics.get('branching_factor', 0.0):.2f}")
    print(f"Max Path Length: {int(cfg_metrics.get('max_path_length', 0))}")

    # ------------------------------------------------------------------
    # Combined feature export for downstream ML
    # ------------------------------------------------------------------
    all_features: Dict[str, Any] = {}
    all_features.update(code_metrics)
    all_features.update(
        {
            "cfg_nodes": cfg_metrics.get("nodes", 0),
            "cfg_edges": cfg_metrics.get("edges", 0),
            "cfg_branching_factor": cfg_metrics.get("branching_factor", 0.0),
            "cfg_loops": cfg_metrics.get("loops", 0),
            "cfg_max_path_length": cfg_metrics.get("max_path_length", 0),
            "cyclomatic_complexity": cfg_metrics.get("cyclomatic_complexity", 0),
        }
    )

    features_dir = Path("data") / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    features_path = features_dir / "program_features.json"

    with features_path.open("w", encoding="utf-8") as f:
        json.dump(all_features, f, indent=2)

    # Also print a JSON representation for quick inspection.
    print("\nJSON Features:")
    print(json.dumps(all_features, indent=2))

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI-Based Code Optimizer - Static Analysis Foundation",
    )
    parser.add_argument(
        "source",
        help="Path to the C source file to analyze",
    )
    args = parser.parse_args(argv)

    return run_pipeline(args.source)


if __name__ == "__main__":
    raise SystemExit(main())

