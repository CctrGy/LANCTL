from __future__ import annotations

import codecs
import io
import os
from collections.abc import Callable
from contextlib import contextmanager

from lanctl.shared.tui_keyboard import (
    CONFIGURABLE_TUI_KEYS as CONFIGURABLE_TUI_KEYS,
)
from lanctl.shared.tui_keyboard import (
    DEFAULT_TUI_KEY_BINDINGS as DEFAULT_TUI_KEY_BINDINGS,
)
from lanctl.shared.tui_keyboard import (
    DEFAULT_VISIBLE_FOOTER_ACTIONS as DEFAULT_VISIBLE_FOOTER_ACTIONS,
)
from lanctl.shared.tui_keyboard import (
    FOOTER_ACTIONS as FOOTER_ACTIONS,
)
from lanctl.shared.tui_keyboard import (
    normalize_footer_actions as normalize_footer_actions,
)
from lanctl.shared.tui_keyboard import (
    normalize_key_bindings as normalize_key_bindings,
)
from lanctl.shared.tui_keyboard import (
    validate_key_bindings as validate_key_bindings,
)

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
POSIX_ESCAPE_MAX_LENGTH = 64


def _read_posix_character(stream) -> str:
    """Read without TextIO read-ahead so select sees the remaining key bytes."""

    try:
        descriptor = stream.fileno()
    except (AttributeError, io.UnsupportedOperation):
        return stream.read(1)
    decoder = codecs.getincrementaldecoder(stream.encoding or "utf-8")(
        errors=stream.errors or "strict"
    )
    while True:
        chunk = os.read(descriptor, 1)
        value = decoder.decode(chunk, final=not chunk)
        if value or not chunk:
            return value


def posix_key_available(stream) -> bool:
    """Indica si existe entrada POSIX sin bloquear el ciclo de repintado."""

    import select

    return bool(select.select([stream], [], [], 0)[0])


def read_posix_key(stream, *, escape_timeout: float = POSIX_ESCAPE_TIMEOUT) -> str:
    """Normaliza caracteres y secuencias ANSI habituales de terminales POSIX."""

    import select
    import time

    first = _read_posix_character(stream)
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
        character = _read_posix_character(stream)
        if not character:
            break
        sequence += character
        if sequence in POSIX_ESCAPE_KEYS:
            break
        # Consume complete unsupported CSI/SS3 sequences (including mouse
        # reports) without turning them into the TUI's close command.
        if len(sequence) > 1 and sequence[0] in "[O" and "@" <= character <= "~":
            break
        if sequence[0] not in "[O":
            break
    return POSIX_ESCAPE_KEYS.get(sequence, "UNKNOWN" if sequence else "ESC")


@contextmanager
def posix_terminal_mode(stream):
    """Activa lectura inmediata y restaura siempre la configuración del TTY."""

    import termios
    import tty

    descriptor = stream.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setcbreak(descriptor)
        current = termios.tcgetattr(descriptor)
        # Ctrl+S/Ctrl+Q must reach the application, not stop/start TTY output.
        current[0] &= ~(termios.IXON | termios.IXOFF)
        termios.tcsetattr(descriptor, termios.TCSADRAIN, current)
        yield
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)
