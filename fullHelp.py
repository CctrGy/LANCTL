"""Genera la referencia completa y alfabética de comandos de LANCTL.

La información se obtiene directamente del parser de la aplicación para que
la ayuda no tenga que mantenerse manualmente cada vez que cambia un comando.
"""

from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Iterable
from pathlib import Path

from app import __version__
from app.cli import build_parser


TREE_BRANCH = "├── "
TREE_LAST = "└── "
TREE_PIPE = "│   "
TREE_SPACE = "    "


def _clean(value: object) -> str:
    return " ".join(str(value).replace("==SUPPRESS==", "").split())


def _metavar(action: argparse.Action) -> str:
    value = action.metavar or action.dest.upper()
    if isinstance(value, tuple):
        return " ".join(str(item) for item in value)
    return str(value)


def _cardinality(action: argparse.Action) -> str:
    values = {
        None: "uno",
        "?": "cero o uno",
        "*": "cero o más",
        "+": "uno o más",
    }
    if action.nargs in values:
        return values[action.nargs]
    return str(action.nargs)


def _default(action: argparse.Action) -> str | None:
    if action.default in (None, argparse.SUPPRESS, False):
        return None
    if action.default is True:
        return "activado"
    return _clean(action.default)


def _choice_text(action: argparse.Action) -> str | None:
    if action.choices is None:
        return None
    return " | ".join(sorted((_clean(choice) for choice in action.choices), key=str.casefold))


def _action_detail(action: argparse.Action) -> list[str]:
    details = [_clean(action.help or "Sin descripción.")]
    choices = _choice_text(action)
    if choices:
        details.append(f"Valores: {choices}")
    if action.nargs not in (None, 0):
        details.append(f"Cantidad: {_cardinality(action)}")
    if action.required:
        details.append("Obligatorio: sí")
    default = _default(action)
    if default is not None:
        details.append(f"Predeterminado: {default}")
    return details


def _option_label(action: argparse.Action) -> str:
    names = ", ".join(action.option_strings)
    if action.nargs != 0:
        names += f" <{_metavar(action)}>"
    return names


def _subparser_groups(
    action: argparse._SubParsersAction,
) -> list[tuple[str, tuple[str, ...], argparse.ArgumentParser]]:
    by_parser: dict[int, tuple[list[str], argparse.ArgumentParser]] = {}
    for name, parser in action.choices.items():
        names, _ = by_parser.setdefault(id(parser), ([], parser))
        names.append(name)

    groups = []
    for names, parser in by_parser.values():
        canonical = names[0]
        aliases = tuple(sorted(names[1:], key=str.casefold))
        groups.append((canonical, aliases, parser))
    return sorted(groups, key=lambda item: item[0].casefold())


def _subparser_action(parser: argparse.ArgumentParser):
    return next(
        (
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ),
        None,
    )


def _usage(parser: argparse.ArgumentParser) -> str:
    buffer = io.StringIO()
    parser.print_usage(buffer)
    value = buffer.getvalue().strip()
    for prefix in ("usage:", "Uso:"):
        if value.startswith(prefix):
            value = value[len(prefix):].strip()
            break
    return _clean(value)


def _exclusive_groups(parser: argparse.ArgumentParser) -> list[str]:
    results = []
    for group in parser._mutually_exclusive_groups:
        members = []
        for action in group._group_actions:
            members.append(
                "/".join(action.option_strings) if action.option_strings else action.dest
            )
        if len(members) > 1:
            requirement = "exactamente una" if group.required else "como máximo una"
            results.append(f"{requirement}: {' | '.join(members)}")
    return results


def _leaf_variants(parser: argparse.ArgumentParser) -> list[str]:
    """Expande las elecciones posicionales sin crear potencias de opciones."""
    variants = [""]
    for action in parser._actions:
        if action.option_strings or isinstance(action, argparse._SubParsersAction):
            continue
        choices = list(action.choices or [_metavar(action)])
        variants = [
            f"{prefix} {choice}".strip()
            for prefix in variants
            for choice in choices
        ]
    return variants or [""]


def _node_lines(parser: argparse.ArgumentParser) -> list[tuple[str, list[str]]]:
    nodes: list[tuple[str, list[str]]] = []
    description = _clean(parser.description or "")
    if description:
        nodes.append(("Descripción", [description]))
    nodes.append(("Sintaxis", [_usage(parser)]))

    positionals = [
        action for action in parser._actions
        if not action.option_strings
        and not isinstance(action, argparse._SubParsersAction)
    ]
    for action in sorted(positionals, key=lambda item: item.dest.casefold()):
        nodes.append((f"Argumento: {_metavar(action)}", _action_detail(action)))

    options = [
        action for action in parser._actions
        if action.option_strings and action.help is not argparse.SUPPRESS
    ]
    for action in sorted(options, key=lambda item: item.option_strings[0].lstrip("-/").casefold()):
        nodes.append((f"Opción: {_option_label(action)}", _action_detail(action)))

    exclusions = _exclusive_groups(parser)
    if exclusions:
        nodes.append(("Combinaciones excluyentes", exclusions))
    variants = _leaf_variants(parser)
    if variants != [""] and len(variants) > 1:
        nodes.append(("Variantes posicionales", variants))
    return nodes


def _emit_details(
    lines: list[str], prefix: str, nodes: list[tuple[str, list[str]]],
    *, has_following: bool = False,
) -> None:
    for index, (label, details) in enumerate(nodes):
        last = index == len(nodes) - 1 and not has_following
        lines.append(prefix + (TREE_LAST if last else TREE_BRANCH) + label)
        child_prefix = prefix + (TREE_SPACE if last else TREE_PIPE)
        for detail_index, detail in enumerate(details):
            detail_last = detail_index == len(details) - 1
            lines.append(child_prefix + (TREE_LAST if detail_last else TREE_BRANCH) + detail)


def _emit_parser(
    lines: list[str],
    parser: argparse.ArgumentParser,
    prefix: str,
) -> None:
    details = _node_lines(parser)
    subparsers = _subparser_action(parser)
    children = _subparser_groups(subparsers) if subparsers else []
    if not children:
        _emit_details(lines, prefix, details)
        return

    _emit_details(lines, prefix, details, has_following=True)
    lines.append(prefix + TREE_LAST + "Subcomandos")
    command_prefix = prefix + TREE_SPACE
    for index, (name, aliases, child) in enumerate(children):
        last = index == len(children) - 1
        alias_text = f" (alias: {', '.join(aliases)})" if aliases else ""
        lines.append(command_prefix + (TREE_LAST if last else TREE_BRANCH) + name + alias_text)
        _emit_parser(
            lines,
            child,
            command_prefix + (TREE_SPACE if last else TREE_PIPE),
        )


def build_full_help() -> str:
    parser = build_parser()
    lines = [
        f"LANCTL {__version__} — referencia completa de comandos",
        "",
        "Los comandos y subcomandos aparecen en orden alfabético.",
        "Las opciones separadas por comas son formas equivalentes del mismo argumento.",
        "",
        "LANCTL",
    ]
    _emit_parser(lines, parser, "")
    return "\n".join(lines) + "\n"


def _arguments(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera la ayuda completa de LANCTL.")
    parser.add_argument(
        "-o", "--output", metavar="ARCHIVO",
        help="Guarda la referencia en UTF-8 además de mostrarla.",
    )
    parser.add_argument(
        "--no-print", action="store_true",
        help="No muestra la referencia; requiere --output.",
    )
    args = parser.parse_args(argv)
    if args.no_print and not args.output:
        parser.error("--no-print requiere --output")
    return args


def main(argv: Iterable[str] | None = None) -> int:
    args = _arguments(argv)
    content = build_full_help()
    if args.output:
        destination = Path(args.output).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="")
    if not args.no_print:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, io.UnsupportedOperation):
            pass
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
