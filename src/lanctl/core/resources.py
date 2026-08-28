from __future__ import annotations

import sys
from pathlib import Path


def bundled_path(value: str | Path) -> Path:
    """Resolve a read-only resource in source and PyInstaller one-file builds."""
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        source = Path(__file__).resolve()
        base = next(
            (parent for parent in source.parents if (parent / "pyproject.toml").is_file()),
            source.parents[3],
        )
    return (base / value).resolve()
