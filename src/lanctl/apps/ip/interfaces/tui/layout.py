from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TuiLayout:
    compact: bool
    modal_margin: int
    modal_width: int
    modal_height: int
    body_rows: int


def adaptive_layout(width: int, height: int, *, settings: bool = False) -> TuiLayout:
    """Calcula una geometría segura para consola local, SSH y ventanas estrechas."""

    width = max(20, width)
    height = max(8, height)
    compact = width < 70 or height < 20
    margin = 2 if compact else 6
    width_limit = 130 if settings else 100
    height_limit = 36 if settings else 30
    modal_width = max(10, min(max(10, width - margin), width_limit))
    modal_height = max(6, min(max(6, height - margin), height_limit))
    return TuiLayout(
        compact=compact,
        modal_margin=margin,
        modal_width=modal_width,
        modal_height=modal_height,
        body_rows=max(1, modal_height - 7),
    )
