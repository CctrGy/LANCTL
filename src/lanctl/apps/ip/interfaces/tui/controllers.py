from __future__ import annotations

import textwrap
from collections.abc import Callable

from lanctl.apps.ip.interfaces.tui.modal import ModalState, SettingField
from lanctl.core.layout import fit_text

SETTINGS_FOOTER = "←/→ menú  ↑/↓ variable  Tab editar  Ctrl+S guardar  Esc cerrar"


class SettingsEditor:
    """Controlador del editor; no conoce el bucle ni el renderizador del TUI."""

    @staticmethod
    def field_indices(modal: ModalState) -> list[int]:
        section = modal.tabs[modal.tab_index] if modal.tabs else "GENERAL"
        indices = [
            index
            for index, field in enumerate(modal.items)
            if isinstance(field, SettingField) and field.section == section
        ]
        return indices or list(range(len(modal.items)))

    @classmethod
    def render_page(cls, modal: ModalState, *, description_width: int = 106) -> list[str]:
        rows = [
            "  CAMPO                      VALOR                         FORMATO",
            "  ─────────────────────────  ─────────────────────────────  ─────────────────────────",
        ]
        visible = set(cls.field_indices(modal))
        for index, field in enumerate(modal.items):
            if index not in visible:
                continue
            marker = (
                "◆"
                if index == modal.selected and modal.editing
                else "▶"
                if index == modal.selected
                else " "
            )
            changed = "*" if field.value != field.original else " "
            rows.append(
                f"{marker}{changed} {field.label:<25} {fit_text(field.value or '(vacío)', 29):<29} {field.hint}"
            )
        selected = modal.items[modal.selected]
        rows.extend(("", "  DESCRIPCIÓN"))
        rows.extend(
            "  " + line
            for line in textwrap.wrap(
                selected.description,
                width=max(24, description_width),
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
        state = (
            "edición activa"
            if modal.editing
            else "modificado, pendiente de guardar"
            if selected.value != selected.original
            else "sin cambios"
        )
        rows.extend(
            (
                f"  Clave: {selected.key}  ·  Opción CLI: {selected.option}  ·  Estado: {state}",
                "",
                "* cambio pendiente · Ctrl+S valida y guarda todos los cambios",
            )
        )
        return rows

    @classmethod
    def handle_key(
        cls,
        modal: ModalState,
        key: str,
        *,
        close: Callable[[], None],
        save: Callable[[ModalState], None],
        open_remote_users: Callable[[], None],
    ) -> None:
        if not modal.items:
            return
        field = modal.items[modal.selected]
        if field.key == "remoteAccessUsers" and key in ("ENTER", "TAB"):
            open_remote_users()
            return
        if key in ("TAB", "SHIFT_TAB"):
            modal.editing = not modal.editing
            modal.editor_fresh = True
            if modal.editing:
                modal.edit_snapshot = field.value
                modal.footer = (
                    "←/→ cambiar valor  ↑/↓ cambiar valor  escribir reemplazar  Tab aceptar  Esc cancelar"
                    if field.choices
                    else "escribir reemplazar  Backspace/Delete editar  Tab aceptar  Esc cancelar"
                )
            else:
                modal.footer = SETTINGS_FOOTER
            return
        if key == "ESC":
            if modal.editing:
                field.value = modal.edit_snapshot
                modal.editing = False
                modal.editor_fresh = True
                modal.footer = SETTINGS_FOOTER
            else:
                close()
            return
        if key == "CTRL_S":
            modal.editing = False
            save(modal)
            return
        if modal.editing:
            if field.choices and key in ("LEFT", "UP", "RIGHT", "DOWN"):
                try:
                    current = field.choices.index(field.value)
                except ValueError:
                    current = -1 if key in ("RIGHT", "DOWN") else 0
                delta = -1 if key in ("LEFT", "UP") else 1
                field.value = field.choices[(current + delta) % len(field.choices)]
                modal.editor_fresh = False
            elif key == "BACKSPACE":
                field.value = field.value[:-1]
                modal.editor_fresh = False
            elif key == "DELETE":
                field.value = ""
                modal.editor_fresh = False
            elif len(key) == 1 and key.isprintable() and not field.choices:
                field.value = key if modal.editor_fresh else field.value + key
                modal.editor_fresh = False
            return
        if key in ("LEFT", "RIGHT"):
            modal.tab_selections[modal.tab_index] = modal.selected
            modal.change_tab(-1 if key == "LEFT" else 1)
            indices = cls.field_indices(modal)
            remembered = modal.tab_selections.get(modal.tab_index)
            modal.selected = remembered if remembered in indices else indices[0]
            modal.editor_fresh = True
            modal.scroll = 0
        elif key in ("UP", "DOWN"):
            indices = cls.field_indices(modal)
            current = indices.index(modal.selected) if modal.selected in indices else 0
            modal.selected = indices[(current + (-1 if key == "UP" else 1)) % len(indices)]
            modal.editor_fresh = True
            modal.scroll = max(0, indices.index(modal.selected) - 5)


class ManagerController:
    """Navegación común de Project Manager, Plugin Manager e historial."""

    @staticmethod
    def move(modal: ModalState, delta: int, update_detail: Callable[[ModalState], None]) -> None:
        if not modal.page:
            return
        modal.selected = max(0, min(len(modal.page) - 1, modal.selected + delta))
        update_detail(modal)
        modal.scroll = max(0, modal.selected - 4)
