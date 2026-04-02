from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List


def compile_c_file(source_path: str) -> Dict[str, object]:
    """
    Attempt to compile a C source file using GCC.

    The compilation is performed with the `-fsyntax-only` flag so that GCC
    checks syntax and semantics without producing an output binary.

    Parameters
    ----------
    source_path:
        Path to the C source file to compile.

    Returns
    -------
    dict
        A dictionary with keys:

        - ``compiled`` (bool): True if compilation succeeded.
        - ``errors`` (list[str]): Compilation error messages, if any.
    """
    path = Path(source_path)

    cmd = ["gcc", "-fsyntax-only", str(path)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        # GCC is not available on the system.
        return {
            "compiled": False,
            "errors": ["gcc not found on system PATH. Please install GCC to use compilation checking."],
        }

    compiled_ok = result.returncode == 0
    errors: List[str] = []

    if not compiled_ok:
        stderr = result.stderr.strip()
        if stderr:
            errors.extend(stderr.splitlines())

    return {
        "compiled": compiled_ok,
        "errors": errors,
    }

