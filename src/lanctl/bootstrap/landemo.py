"""Punto de entrada dedicado al recorrido reproducible LANCTL."""

from __future__ import annotations

import sys

from lanctl import __version__
from lanctl.apps.ip.interfaces.cli.main import main as lanctl_main


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--version"]:
        print(f"LANDEMO {__version__}")
        return 0
    return lanctl_main(["demo", *arguments])


__all__ = ["main"]
