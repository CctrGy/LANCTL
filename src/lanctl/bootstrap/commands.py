"""Construcción de launchers internos desde fuentes y distribuciones congeladas."""

from __future__ import annotations

import sys
from pathlib import Path


def ip_command(*arguments: str) -> list[str]:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        name = executable.stem.casefold()
        if name in {"lanip", "als"}:
            return [str(executable), *arguments]
        for name in ("LANIP", "lanip"):
            sibling = executable.with_name(name + executable.suffix)
            if sibling.is_file():
                return [str(sibling), *arguments]
        # El launcher de la suite acepta la aplicación como primer argumento.
        if executable.stem.casefold() == "lanctl":
            return [str(executable), "lanip", *arguments]
        raise FileNotFoundError("no se encuentra el launcher LANIP junto al ejecutable")
    source = Path(__file__).resolve().parents[2]
    checkout = source.parent / "lanip.py"
    if checkout.is_file():
        return [sys.executable, str(checkout), *arguments]
    return [sys.executable, "-m", "lanctl.bootstrap.lanip", *arguments]
