import os
GRAPHVIZ_BIN = r"C:\Program Files\Graphviz\bin"

if GRAPHVIZ_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = GRAPHVIZ_BIN + os.pathsep + os.environ.get("PATH", "")

from utils.file_loader import load_c_file
from analyzer.ast_parser import parse_c_code
from analyzer.cfg_builder import build_cfg
from graphs.graph_visualizer import visualize_cfg
from graphs.ast_visualizer import visualize_ast


def main() -> None:
    # 1. Load the example C program
    source_path = "examples/sample.c"
    code = load_c_file(source_path)

    # 2. Parse into AST
    ast = parse_c_code(code)

    # 3. Build CFG from AST
    cfg = build_cfg(ast)

    # 4. Visualize CFG
    cfg_output = "outputs/cfg_sample.png"
    cfg_path = visualize_cfg(cfg, cfg_output)
    print(f"CFG image saved to: {cfg_path}")

    # 5. Visualize AST
    ast_output = "outputs/ast_sample.png"
    ast_path = visualize_ast(ast, ast_output)
    print(f"AST image saved to: {ast_path}")


if __name__ == "__main__":
    main()