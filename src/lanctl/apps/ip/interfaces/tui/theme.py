from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TuiTheme:
    accent: str = "bright_cyan"
    muted: str = "bright_black"
    selected: str = "bold black on bright_cyan"
    keycap: str = "bold black on bright_white"
    success: str = "bold green"
    warning: str = "bold yellow"
    error: str = "bold red"


DEFAULT_THEME = TuiTheme()
