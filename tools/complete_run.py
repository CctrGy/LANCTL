"""Candidatos de completado Bash desde los parsers, sin ejecutar comandos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def candidates(words: list[str]) -> list[str]:
    from lanctl.bootstrap.lanctl import build_parser

    parser = build_parser()
    aliases = {
        "lanip": "ip",
        "ip": "ip",
        "lanwire": "wire",
        "wire": "wire",
        "lanrack": "rack",
        "rack": "rack",
        "lanaccess": "access",
        "access": "access",
        "lanmon": "monitor",
        "monitor": "monitor",
    }
    current = words[-1] if words else ""
    previous = words[:-1]
    if previous and previous[0] == "--foreground":
        previous = previous[1:]
    if previous and previous[0] in aliases:
        app = aliases[previous.pop(0)]
        if app == "ip":
            from lanctl.apps.ip.interfaces.cli.main import build_parser
        elif app == "wire":
            from lanctl.apps.wire.cli.main import build_parser
        elif app == "rack":
            from lanctl.apps.rack.cli import build_parser
        elif app == "access":
            from lanctl.apps.access.manager_cli import build_parser
        else:
            from lanctl.bootstrap.lanmon import build_parser
        parser = build_parser()
    elif previous and previous[0] in {"plugin", "settings", "language", "backend"}:
        # Suite routes these shared commands through their dedicated parsers.
        if previous[0] == "backend":
            from lanctl.core.coordination_cli import build_parser

            previous.pop(0)
        else:
            from lanctl.apps.ip.interfaces.cli.main import build_parser
        parser = build_parser()

    pending = None
    positional = 0
    for word in previous:
        if pending is not None:
            if pending.nargs != "?" or not word.startswith("-"):
                pending = None
                continue
            pending = None
        action = parser._option_string_actions.get(word)
        if action:
            if action.nargs != 0:
                pending = action
            continue
        if word.startswith("-"):
            continue
        subparsers = next(
            (a for a in parser._actions if isinstance(a, argparse._SubParsersAction)), None
        )
        if subparsers and word in subparsers.choices:
            parser = subparsers.choices[word]
            positional = 0
        else:
            positional += 1
    if pending is not None and not (pending.nargs == "?" and current.startswith("-")):
        return [str(c) for c in (pending.choices or []) if str(c).startswith(current)]
    result = set(parser._option_string_actions)
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            result.update(action.choices)
    positionals = [
        a
        for a in parser._actions
        if not a.option_strings and not isinstance(a, argparse._SubParsersAction)
    ]
    if positional < len(positionals):
        result.update(str(c) for c in (positionals[positional].choices or []))
    if parser.prog == "LANCTL":
        result.update({"--foreground", "-help", "-version", "/?"})
    return sorted(value for value in result if value.startswith(current))


if __name__ == "__main__":
    print("\n".join(candidates(sys.argv[1:])))
