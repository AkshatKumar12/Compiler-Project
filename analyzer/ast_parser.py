from typing import Any

from pycparser import CParser, c_ast
from pycparser.plyparser import ParseError


class ASTParsingError(Exception):
    """Raised when C code cannot be parsed into an AST."""


_PARSER = CParser()


def _strip_preprocessor_directives(code: str) -> str:
    """
    Remove simple preprocessor directives from the source.

    pycparser expects code that has already been preprocessed, and it does
    not support directives such as ``#include``. For this research tool we
    apply a light-weight preprocessing step that drops lines starting with
    ``#`` so that small examples using standard headers can still be parsed.
    """
    filtered_lines = []
    for line in code.splitlines():
        if line.lstrip().startswith("#"):
            # Drop preprocessor line.
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines)


def parse_c_code(code: str) -> c_ast.FileAST:
    """
    Parse C source code into a pycparser AST.

    Parameters
    ----------
    code:
        The C source code as a string. Preprocessor directives are
        stripped before parsing to keep the parser input compatible
        with pycparser's expectations.

    Returns
    -------
    c_ast.FileAST
        The root of the parsed C abstract syntax tree.

    Raises
    ------
    ASTParsingError
        If the C code cannot be parsed.
    """
    preprocessed = _strip_preprocessor_directives(code)

    try:
        # pycparser expects a complete translation unit.
        ast: Any = _PARSER.parse(preprocessed, filename="<input>")
    except ParseError as exc:
        raise ASTParsingError(f"Failed to parse C code: {exc}") from exc

    if not isinstance(ast, c_ast.FileAST):
        raise ASTParsingError("Parsed AST root is not a FileAST node.")

    return ast

