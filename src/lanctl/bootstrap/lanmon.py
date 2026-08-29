"""Punto de entrada dedicado a monitorización LANCTL."""

from __future__ import annotations

import sys

from lanctl import __version__
from lanctl.apps.ip.interfaces.cli.main import main as lanctl_main


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--version"]:
        print(f"LANMON {__version__}")
        return 0
    return lanctl_main(["monitor", *(arguments or ["status"])])


__all__ = ["main"]
