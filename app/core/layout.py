from __future__ import annotations

import shutil
import sys
import textwrap
from typing import Iterable


def terminal_columns(stream=None, fallback: int = 120) -> int | None:
    """Devuelve el ancho utilizable solo cuando la salida es una terminal real."""
    stream = stream or sys.stdout
    if not getattr(stream, "isatty", lambda: False)():
        return None
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
