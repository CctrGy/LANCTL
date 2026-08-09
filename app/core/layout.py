from __future__ import annotations

import ctypes
import os
import shutil
import sys
import textwrap
from collections.abc import Iterable


def terminal_columns(stream=None, fallback: int = 120) -> int | None:
    """Devuelve el ancho utilizable solo cuando la salida es una terminal real."""
    stream = stream or sys.stdout
    if not getattr(stream, "isatty", lambda: False)():
        return None
    if os.name == "nt":
        # En Windows `shutil` puede devolver el ancho del búfer desplazable.
        # `srWindow` representa los caracteres que el usuario ve realmente.
        class _Coord(ctypes.Structure):
            _fields_ = (("x", ctypes.c_short), ("y", ctypes.c_short))

        class _SmallRect(ctypes.Structure):
            _fields_ = (
                ("left", ctypes.c_short),
                ("top", ctypes.c_short),
                ("right", ctypes.c_short),
                ("bottom", ctypes.c_short),
            )

        class _ConsoleInfo(ctypes.Structure):
            _fields_ = (
                ("size", _Coord),
                ("cursor", _Coord),
                ("attributes", ctypes.c_ushort),
                ("window", _SmallRect),
                ("maximum", _Coord),
            )

        try:
            handle_id = -12 if stream is sys.stderr else -11
            handle = ctypes.windll.kernel32.GetStdHandle(handle_id)
            info = _ConsoleInfo()
            if ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
                return max(20, info.window.right - info.window.left + 1)
        except (AttributeError, OSError, ValueError):
            pass
    return max(20, shutil.get_terminal_size(fallback=(fallback, 24)).columns)


def fit_text(value: object, width: int) -> str:
    text = str(value)
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return "…"
    return text[: width - 1] + "…"


def shrink_widths(
    widths: dict[str, int],
    minimums: dict[str, int],
    fields: Iterable[str],
    max_width: int | None,
    priority: Iterable[str],
    gap: int = 2,
) -> tuple[dict[str, int], bool]:
    """Reduce columnas flexibles y avisa si hace falta una vista vertical."""
    result = dict(widths)
    ordered = list(fields)
    if max_width is None:
        return result, False
    excess = sum(result[field] for field in ordered) + gap * max(0, len(ordered) - 1) - max_width
    for field in priority:
        if excess <= 0 or field not in result:
            continue
        reducible = max(0, result[field] - minimums.get(field, 3))
        reduction = min(excess, reducible)
        result[field] -= reduction
        excess -= reduction
    return result, excess > 0


def wrapped_lines(text: object, width: int) -> list[str]:
    return textwrap.wrap(
        str(text),
        width=max(1, width),
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
    ) or [""]
