from pathlib import Path
from typing import Optional


class FileLoadingError(Exception):
    """Raised when a C source file cannot be loaded."""


def load_c_file(path: str, encoding: str = "utf-8") -> str:
    """
    Load a C source file from disk.

    Parameters
    ----------
    path:
        Path to the C source file.
    encoding:
        Text encoding to use when reading the file.

    Returns
    -------
    str
        Contents of the file as a string.

    Raises
    ------
    FileLoadingError
        If the file does not exist or cannot be read.
    """
    file_path = Path(path)

    if not file_path.is_file():
        raise FileLoadingError(f"C source file not found: {file_path}")

    try:
        return file_path.read_text(encoding=encoding, errors="replace")
    except OSError as exc:
        raise FileLoadingError(f"Failed to read file '{file_path}': {exc}") from exc

