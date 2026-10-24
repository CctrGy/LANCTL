"""Punto de entrada directo de LANIP."""

from __future__ import annotations

import os
import sys


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments[:2] == ["access", "serve"] and os.environ.get("LANCTL_ACCESS_START_TOKEN"):
        # An owned listener must not initialize/migrate program preferences while
        # its parent holds their transaction open awaiting readiness.
        from lanctl.apps.access.processes import _run_service_child

        return _run_service_child(arguments)
    from lanctl.apps.ip.interfaces.cli.main import main as ip_main

    return ip_main(arguments, program_name="LANIP")


__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
