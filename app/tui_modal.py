from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SettingField:
    key: str
    label: str
    option: str
    value: str
    original: str
    hint: str = ""
    section: str = "GENERAL"
    description: str = "Sin descripción disponible."
    choices: tuple[str, ...] = ()


@dataclass(slots=True)
class ModalState:
    """Estado de una superposición que toma el foco completo del TUI."""

    kind: str
    title: str
    tabs: list[str]
    pages: list[list[str]]
    tab_index: int = 0
    scroll: int = 0
    selected: int = 0
    items: list[Any] = field(default_factory=list)
    footer: str = "←/→ sección  ↑/↓ desplazar  Esc cerrar"
    background: list[str] = field(default_factory=list)
    editor_fresh: bool = True
    editing: bool = False
    edit_snapshot: str = ""
    tab_selections: dict[int, int] = field(default_factory=dict)

    @property
    def page(self) -> list[str]:
        if not self.pages:
            return []
        return self.pages[min(self.tab_index, len(self.pages) - 1)]

    def change_tab(self, delta: int) -> None:
        if self.tabs:
            self.tab_index = (self.tab_index + delta) % len(self.tabs)
            self.scroll = 0
