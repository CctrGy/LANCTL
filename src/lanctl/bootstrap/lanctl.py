"""Orquestador principal de las aplicaciones de la suite."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0].casefold() in {"ip", "lanip"}:
        from lanctl.apps.ip.interfaces.cli.main import main as ip_main

        return ip_main(arguments[1:])
    if arguments and arguments[0].casefold() in {"wire", "lanwire"}:
        from lanctl.apps.wire.cli.main import main as wire_main

        return wire_main(arguments[1:])

    # Compatibilidad: los comandos históricos pertenecen ahora a LANIP.
    from lanctl.apps.ip.interfaces.cli.main import main as ip_main

    return ip_main(arguments)
