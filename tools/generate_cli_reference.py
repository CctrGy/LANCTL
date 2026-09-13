from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lanctl.apps.access.manager_cli import build_parser as access_parser  # noqa: E402
from lanctl.apps.ip.interfaces.cli.main import build_parser as ip_parser  # noqa: E402
from lanctl.apps.rack.cli import build_parser as rack_parser  # noqa: E402
from lanctl.apps.wire.cli.main import build_parser as wire_parser  # noqa: E402
from lanctl.bootstrap.lanctl import build_parser as suite_parser  # noqa: E402
from lanctl.bootstrap.lanmon import build_parser as monitor_parser  # noqa: E402

OUTPUT = ROOT / "docs" / "CLI-REFERENCE.md"


def parser_tree(parser: argparse.ArgumentParser, path: tuple[str, ...] = ("LANCTL",)):
    yield path, parser
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        seen: set[int] = set()
        for name, child in action.choices.items():
            if id(child) in seen:
                continue
            seen.add(id(child))
            yield from parser_tree(child, (*path, name))


def generate() -> str:
    # La referencia es un artefacto multiplataforma: usa la sintaxis común
    # POSIX/Windows y documenta /? por separado, evitando diffs según el runner.
    os.environ["LANCTL_CANONICAL_HELP"] = "1"
    sections = [
        "# Referencia completa del CLI LANCTL",
        "",
        "Documento generado automáticamente desde los parsers de la aplicación.",
        "No lo edites manualmente; ejecuta `python tools/generate_cli_reference.py`.",
    ]
    roots = (
        (("LANCTL",), suite_parser(), False),
        (("LANIP",), ip_parser(program_name="LANIP"), True),
        (("LANWIRE",), wire_parser(), True),
        (("LANRACK",), rack_parser(), True),
        (("LANACCESS",), access_parser(), True),
        (("LANMON",), monitor_parser(), True),
    )
    for path, root, recursive in roots:
        parsers = parser_tree(root, path) if recursive else ((path, root),)
        for parser_path, parser in parsers:
            title = " ".join(parser_path)
            sections.extend(
                ["", f"## `{title}`", "", "```text", parser.format_help().rstrip(), "```"]
            )
    return "\n".join(sections) + "\n"


def main() -> int:
    content = generate()
    if "--check" in sys.argv:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
            print(f"CLI reference is stale: {OUTPUT}", file=sys.stderr)
            return 1
        print(f"CLI reference verified: {OUTPUT}")
        return 0
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"CLI reference generated: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
