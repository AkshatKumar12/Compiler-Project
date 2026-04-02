AI-Based Code Optimizer (Static Analysis Foundation)
====================================================

This project provides the static analysis foundation for an AI-based C code
optimizer. It parses C code, verifies compilation, builds an AST, and computes
basic structural metrics that can later be used as features for machine
learning models.

Current features


- Load C source files safely.
- Verify compilation using `gcc -fsyntax-only`.
- Parse C code into an AST using `pycparser`.
- Traverse the AST to identify functions, loops, conditionals, and variables.
- Compute metrics such as:
  - Number of functions
  - Number of loops
  - Number of nested loops
  - Number of conditionals
  - Number of variable declarations
  - Approximate lines of code

Project structure
-----------------

- `analyzer/`
  - `ast_parser.py` - wraps `pycparser` to build an AST.
  - `ast_utils.py` - AST traversal helpers and loop statistics.
  - `code_metrics.py` - high-level metric computation helpers.
- `compiler/`
  - `compile_checker.py` - compilation checking using GCC.
- `utils/`
  - `file_loader.py` - safe file loading utilities.
- `examples/`
  - `sample.c` - example C program for testing.
- `data/features/`
  - (reserved for future ML feature exports)
- `main.py`
  - Command-line entry point and analysis pipeline orchestration.

Installation
------------

Create a virtual environment (recommended) and install dependencies:

```bash
pip install -r requirements.txt
```

Usage
-----

Run the analyzer on the example C file:

```bash
python main.py examples/sample.c
```

Example output:

```text
Compilation: SUCCESS

Code Metrics:
Functions: 2
Loops: 2
Nested Loops: 0
Conditionals: 1
Variables: 7
Lines: 30

JSON Metrics:
{
  "functions": 2,
  "loops": 2,
  "nested_loops": 0,
  "conditionals": 1,
  "variables": 7,
  "lines_of_code": 30
}
```

Note: Metrics are approximate and derived from `pycparser`'s AST; they are
intended for research and feature engineering rather than strict static
analysis guarantees.

