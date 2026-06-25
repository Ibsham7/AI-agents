import os
from pathlib import Path

# Safety: agents can only read from these directories
ALLOWED_READ_DIRS = [
    Path("test_targets").resolve(),
    Path("datasets").resolve(),
    Path("outputs").resolve(),
]

def _is_allowed_path(path: Path) -> bool:
    path = path.resolve()
    return any(
        str(path).startswith(str(allowed))
        for allowed in ALLOWED_READ_DIRS
    )

def read_file(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        return f"Error: file '{filepath}' does not exist."
    if not _is_allowed_path(path):
        return f"Error: reading outside allowed directories is not permitted."
    if path.stat().st_size > 100_000:  # 100KB cap
        return f"Error: file too large ({path.stat().st_size} bytes). Read in chunks."
    return path.read_text(encoding="utf-8")

def list_directory(dirpath: str) -> str:
    path = Path(dirpath)
    if not path.is_dir():
        return f"Error: '{dirpath}' is not a directory."
    entries = []
    for item in sorted(path.iterdir()):
        kind = "DIR" if item.is_dir() else "FILE"
        size = "" if item.is_dir() else f"({item.stat().st_size} bytes)"
        entries.append(f"  {kind}  {item.name} {size}")
    return f"Contents of {dirpath}:\n" + "\n".join(entries)

def write_file(filepath: str, content: str) -> str:
    """Only writes to outputs/ directory."""
    path = Path(filepath)
    if not str(path.resolve()).startswith(str(Path("outputs").resolve())):
        return "Error: can only write to the outputs/ directory."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Written {len(content)} characters to {filepath}"