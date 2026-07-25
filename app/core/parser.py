from __future__ import annotations

import argparse
import os
import re
import sys

from colorama import Fore, Style

from app.core.console import error as print_error


def _color_enabled(stream) -> bool:
    return stream.isatty() and "NO_COLOR" not in os.environ


def colorize_help(text: str, stream=None) -> str:
    """Aplica la paleta común a ayudas argparse e interactivas."""
    stream = stream or sys.stdout
    if not _color_enabled(stream):
        return text

    colored: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if line.startswith("Uso:"):
            line = f"{Style.BRIGHT}{Fore.CYAN}{line}{Style.RESET_ALL}"
        elif stripped.endswith(":") and not line.startswith(" "):
            line = f"{Style.BRIGHT}{Fore.YELLOW}{line}{Style.RESET_ALL}"
        else:
            match = re.match(r"^(\s{2,})(\S+(?:,\s+\S+)*)(\s{2,}.*)$", line)
            if match:
                line = (
                    f"{match.group(1)}{Fore.CYAN}{match.group(2)}"
                    f"{Style.RESET_ALL}{match.group(3)}"
                )
        colored.append(line)
    return "\n".join(colored) + ("\n" if text.endswith("\n") else "")


class LANCTLHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Formato estable para toda la ayuda, incluidas descripciones multilínea."""

    def __init__(self, prog: str):
        super().__init__(
            prog,
            indent_increment=2,
            max_help_position=30,
            width=88,
        )


class LANCTLArgumentParser(argparse.ArgumentParser):
    """ArgumentParser común de LANCTL con ayuda /? y colores."""

    def __init__(self, *args, **kwargs):
        kwargs["add_help"] = False
        kwargs["prefix_chars"] = "-/"
        kwargs.setdefault("formatter_class", LANCTLHelpFormatter)
        super().__init__(*args, **kwargs)
        self.add_argument(
            "-h",
            "--help",
            "/?",
            action="help",
            help="Muestra esta ayuda y termina.",
        )

    def format_help(self) -> str:
        text = super().format_help()
        replacements = {
            "usage:": "Uso:",
            "positional arguments:": "Argumentos:",
            "options:": "Opciones:",
            "optional arguments:": "Opciones:",
        }
        lines = text.splitlines()
        normalized: list[str] = []
        for line in lines:
            stripped = line.strip()
            replacement = replacements.get(stripped)
            if replacement:
                line = replacement
            elif line.startswith("usage:"):
                line = "Uso:" + line[len("usage:"):]
            normalized.append(line)
        text = "\n".join(normalized) + "\n"
        return colorize_help(text, sys.stdout)

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print_error(message)
        self.exit(2)


# Compatibilidad con extensiones que todavía importen el nombre anterior.
ALSArgumentParser = LANCTLArgumentParser
