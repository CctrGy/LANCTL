"""Entrada de teclado nativa en Windows y alternativa ANSI básica."""

from __future__ import annotations

import os
import select
import sys
import time
from collections.abc import Callable

WINDOWS_SPECIAL_KEYS = {
    "H": "UP",
    "P": "DOWN",
    "K": "LEFT",
    "M": "RIGHT",
    "I": "PGUP",
    "Q": "PGDN",
    "G": "HOME",
    "O": "END",
    "S": "DELETE",
    ";": "F1",
    "=": "F3",
    "?": "F5",
    "A": "F7",
    "C": "F9",
    "\x86": "F12",
}


def decode_windows_key(getwch: Callable[[], str]) -> str:
    first = getwch()
    if first in ("\x00", "\xe0"):
        return WINDOWS_SPECIAL_KEYS.get(getwch(), "UNKNOWN")
    return {
        "\r": "ENTER",
        "\x1b": "ESC",
        "\x08": "BACKSPACE",
        "\t": "TAB",
        "\x13": "CTRL_S",
        "\x11": "CTRL_Q",
        "\x03": "CTRL_C",
        "\x0a": "CTRL_J",
    }.get(first, first)


def read_key(timeout: float = 0.1) -> str | None:
    """Lee una tecla sin bloquear el refresco periódico de la TUI."""
    if os.name == "nt":
        import msvcrt

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                return decode_windows_key(msvcrt.getwch)
            time.sleep(0.01)
        return None
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return None
    first = sys.stdin.read(1)
    if first == "\x1b":
        sequence = first
        while select.select([sys.stdin], [], [], 0.005)[0]:
            sequence += sys.stdin.read(1)
        return {
            "\x1b[A": "UP",
            "\x1b[B": "DOWN",
            "\x1b[C": "RIGHT",
            "\x1b[D": "LEFT",
            "\x1bOP": "F1",
            "\x1bOR": "F3",
            "\x1b[13~": "F3",
            "\x1b[18~": "F7",
            "\x1b[20~": "F9",
            "\x1b[24~": "F12",
            "\x1b[3~": "DELETE",
            "\x1b[5~": "PGUP",
            "\x1b[6~": "PGDN",
        }.get(sequence, "ESC")
    return {
        "\r": "ENTER",
        "\x7f": "BACKSPACE",
        "\x03": "CTRL_C",
        "\x08": "CTRL_H",
        "\t": "TAB",
        "\x13": "CTRL_S",
        "\x11": "CTRL_Q",
        "\x0a": "CTRL_J",
    }.get(first, first)
