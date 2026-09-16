from __future__ import annotations

import os
from collections.abc import Callable
from contextlib import contextmanager

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

DEFAULT_TUI_KEY_BINDINGS = {
    "help": "F1",
    "info": "F2",
    "ping": "F3",
    "refresh": "F5",
    "plugins": "F7",
    "projects": "F9",
    "settings": "F12",
    "history": "CTRL_H",
    "search": "CTRL_F",
    "reload": "CTRL_R",
    "edit": "CTRL_E",
    "groups": "CTRL_G",
    "ports": "CTRL_P",
    "open": "CTRL_O",
    "save": "CTRL_S",
    "differences": "CTRL_D",
    "copyLine": "CTRL_X",
    "copyJson": "CTRL_J",
    "console": "CTRL_L",
    "quit": "CTRL_Q",
    "deviceHistory": None,
    "scanSelected": None,
    "filterActive": None,
    "filterDisconnected": None,
    "filterAll": None,
    "ssh": None,
    "terminal": None,
    "credentials": None,
    "wakeOnLan": None,
    "copyIp": None,
    "copyMac": None,
    "projectStatus": None,
}

CONFIGURABLE_TUI_KEYS = (
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "CTRL_H",
    "CTRL_J",
    "CTRL_D",
    "CTRL_E",
    "CTRL_F",
    "CTRL_G",
    "CTRL_L",
    "CTRL_O",
    "CTRL_P",
    "CTRL_Q",
    "CTRL_R",
    "CTRL_S",
    "CTRL_X",
)

DEFAULT_VISIBLE_FOOTER_ACTIONS = (
    "help",
    "info",
    "ping",
    "refresh",
    "plugins",
    "projects",
    "settings",
    "select",
)

FOOTER_ACTIONS = (
    *DEFAULT_TUI_KEY_BINDINGS,
    "select",
    "execute",
    "exit",
)


def normalize_key_bindings(value: object) -> dict[str, str | None]:
    configured = value if isinstance(value, dict) else {}
    result = dict(DEFAULT_TUI_KEY_BINDINGS)
    for action in result:
        raw = configured.get(action, result[action])
        if raw is None or str(raw).strip().casefold() in {"none", "null", "off", "-"}:
            result[action] = None
            continue
        key = str(raw).strip().upper().replace("+", "_")
        if key in CONFIGURABLE_TUI_KEYS:
            result[action] = key
    return result


def validate_key_bindings(value: dict[str, str | None]) -> dict[str, str | None]:
    result = normalize_key_bindings(value)
    assigned = [key for key in result.values() if key]
    duplicates = {key for key in assigned if assigned.count(key) > 1}
    if duplicates:
        shown = ", ".join(sorted(key.replace("_", "+") for key in duplicates))
        raise ValueError(f"cada acción TUI debe usar una tecla distinta; duplicadas: {shown}")
    return result


def normalize_footer_actions(value: object) -> list[str]:
    if isinstance(value, str):
        values = [part.strip() for part in value.split(",")]
    elif isinstance(value, (list, tuple)):
        values = [str(part).strip() for part in value]
    else:
        values = list(DEFAULT_VISIBLE_FOOTER_ACTIONS)
    if any(item.casefold() == "all" for item in values):
        return list(FOOTER_ACTIONS)
    aliases = {item.casefold(): item for item in FOOTER_ACTIONS}
    result = []
    for item in values:
        action = aliases.get(item.casefold())
        if action and action not in result:
            result.append(action)
    return result


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
    ">": "F4",
    "?": "F5",
    "@": "F6",
    "A": "F7",
    "B": "F8",
    "C": "F9",
    "D": "F10",
    "\x85": "F11",
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
        "\x18": "CTRL_X",
        "\x04": "CTRL_D",
        "\x05": "CTRL_E",
        "\x06": "CTRL_F",
        "\x07": "CTRL_G",
        "\x0a": "CTRL_J",
        "\x0c": "CTRL_L",
        "\x0e": "CTRL_N",
        "\x0f": "CTRL_O",
        "\x10": "CTRL_P",
        "\x11": "CTRL_Q",
        "\t": "TAB",
        "\r": "ENTER",
        "\x1b": "ESC",
        "\x03": "ESC",
    }.get(first, first)


POSIX_ESCAPE_KEYS = {
    "[A": "UP",
    "[B": "DOWN",
    "[C": "RIGHT",
    "[D": "LEFT",
    "OA": "UP",
    "OB": "DOWN",
    "OC": "RIGHT",
    "OD": "LEFT",
    "[H": "HOME",
    "[F": "END",
    "OH": "HOME",
    "OF": "END",
    "[3~": "DELETE",
    "[5~": "PGUP",
    "[6~": "PGDN",
    "[Z": "SHIFT_TAB",
    "OP": "F1",
    "OQ": "F2",
    "OR": "F3",
    "OS": "F4",
    "[11~": "F1",
    "[12~": "F2",
    "[13~": "F3",
    "[14~": "F4",
    "[15~": "F5",
    "[17~": "F6",
    "[18~": "F7",
    "[19~": "F8",
    "[20~": "F9",
    "[21~": "F10",
    "[23~": "F11",
    "[24~": "F12",
}

POSIX_ESCAPE_TIMEOUT = 0.15
POSIX_ESCAPE_MAX_LENGTH = max(map(len, POSIX_ESCAPE_KEYS))


def posix_key_available(stream) -> bool:
    """Indica si existe entrada POSIX sin bloquear el ciclo de repintado."""

    import select

    return bool(select.select([stream], [], [], 0)[0])


def read_posix_key(stream, *, escape_timeout: float = POSIX_ESCAPE_TIMEOUT) -> str:
    """Normaliza caracteres y secuencias ANSI habituales de terminales POSIX."""

    import select
    import time

    first = stream.read(1)
    if first != "\x1b":
        return {
            "\x7f": "BACKSPACE",
            "\x08": "CTRL_H",
            "\x12": "CTRL_R",
            "\x13": "CTRL_S",
            "\x18": "CTRL_X",
            "\x04": "CTRL_D",
            "\x05": "CTRL_E",
            "\x06": "CTRL_F",
            "\x07": "CTRL_G",
            "\x0a": "ENTER",
            "\x0c": "CTRL_L",
            "\x0e": "CTRL_N",
            "\x0f": "CTRL_O",
            "\x10": "CTRL_P",
            "\x11": "CTRL_Q",
            "\t": "TAB",
            "\r": "ENTER",
            "\x03": "ESC",
        }.get(first, first)
    sequence = ""
    deadline = time.monotonic() + max(0.0, escape_timeout)
    while len(sequence) < POSIX_ESCAPE_MAX_LENGTH:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([stream], [], [], remaining)[0]:
            break
        sequence += stream.read(1)
        if sequence in POSIX_ESCAPE_KEYS or sequence.endswith("~"):
            break
    return POSIX_ESCAPE_KEYS.get(sequence, "ESC")


@contextmanager
def posix_terminal_mode(stream):
    """Activa lectura inmediata y restaura siempre la configuración del TTY."""

    import termios
    import tty

    descriptor = stream.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setcbreak(descriptor)
        yield
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)
