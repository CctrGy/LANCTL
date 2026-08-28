from __future__ import annotations

import os
from collections.abc import Callable

KEY_BINDINGS = {
    "F1": "Ayuda",
    "F2": "Información",
    "F3": "Ping",
    "F5": "Actualizar",
    "F7": "Plugins",
    "F9": "Proyectos",
    "F12": "Settings",
    "CTRL_H": "Historial",
}

WINDOWS_EXTENDED_KEYS = {
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
    "<": "F2",
    "=": "F3",
    "?": "F5",
    "A": "F7",
    "C": "F9",
    "\x86": "F12",
    "\x0f": "SHIFT_TAB",
}


def windows_control_pressed() -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.user32.GetKeyState(0x11) & 0x8000)
    except (AttributeError, OSError):
        return False


def read_windows_key(
    getwch: Callable[[], str], control_pressed: Callable[[], bool] | None = None
) -> str:
    """Normaliza la entrada de Windows a las teclas semánticas del TUI."""

    first = getwch()
    if first in ("\x00", "\xe0"):
        return WINDOWS_EXTENDED_KEYS.get(getwch(), "UNKNOWN")
    if first == "\x08":
        pressed = control_pressed or windows_control_pressed
        return "CTRL_H" if pressed() else "BACKSPACE"
    return {
        "\x12": "CTRL_R",
        "\x13": "CTRL_S",
        "\t": "TAB",
        "\r": "ENTER",
        "\n": "ENTER",
        "\x1b": "ESC",
        "\x03": "ESC",
    }.get(first, first)
