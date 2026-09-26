"""Punto de entrada directo de LANIP."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    from lanctl.apps.ip.interfaces.cli.main import main as ip_main

    arguments = list(sys.argv[1:] if argv is None else argv)
    return ip_main(arguments, program_name="LANIP")


__all__ = ["main"]
