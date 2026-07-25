from __future__ import annotations

import sys

from colorama import Fore, Style, just_fix_windows_console

from app.core.logger import write_log
from app.core.layout import terminal_columns, wrapped_lines

# Activa ANSI en consolas antiguas de Windows sin envolver stdout/stderr.
just_fix_windows_console()

COLORS = {"ok": Fore.GREEN, "pending": Fore.YELLOW, "error": Fore.RED}


def status(label: str, message: str, kind: str = "ok") -> None:
    """Imprime estados consistentes; usa color solo en terminales compatibles."""
    write_log(f"[{label}] {message}")
    stream = sys.stderr
    plain_prefix = f"[{label}]"
    if stream.isatty():
        prefix = f"{COLORS[kind]}{plain_prefix}{Style.RESET_ALL}"
    else:
        prefix = plain_prefix

    prefix_width = max(14, len(plain_prefix))
    padding = " " * (prefix_width + 1)
    width = terminal_columns(stream)
    lines: list[str] = []
    for source_line in message.splitlines() or [""]:
        lines.extend(wrapped_lines(source_line, max(1, width - len(padding))) if width else [source_line])
    print(f"{prefix}{' ' * (prefix_width - len(plain_prefix))} {lines[0]}", file=stream)
    for line in lines[1:]:
        print(f"{padding}{line}", file=stream)
    stream.flush()


def ok(label: str, message: str) -> None:
    status(label, message, "ok")


def pending(message: str) -> None:
    print(file=sys.stderr)
    status("PENDIENTE", message, "pending")


def error(message: str) -> None:
    status("ERROR", message, "error")
