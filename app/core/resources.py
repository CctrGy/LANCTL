from __future__ import annotations

from pathlib import Path
import sys


def bundled_path(value: str | Path) -> Path:
    """Resolve a read-only resource in source and PyInstaller one-file builds."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return (base / value).resolve()
