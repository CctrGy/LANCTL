from __future__ import annotations

import textwrap
from collections.abc import Callable

from rich.text import Text

from lanctl.apps.ip.interfaces.tui.modal import ModalState, SettingField
from lanctl.core.layout import fit_text

SETTINGS_FOOTER = "←/→ menú  ↑/↓ variable  Tab editar  Esc salir"


class SettingsEditor:
    """Controlador del editor; no conoce el bucle ni el renderizador del TUI."""

    @staticmethod
    def field_indices(modal: ModalState) -> list[int]:
        section = modal.tabs[modal.tab_index] if modal.tabs else "GENERAL"
        if section == "EXIT":
            return []
        indices = [
            index
            for index, field in enumerate(modal.items)
            if isinstance(field, SettingField) and field.section == section
        ]
        return indices or list(range(len(modal.items)))

    @classmethod
    def render_page(
        cls, modal: ModalState, *, description_width: int = 106, table_width: int = 118
    ) -> list[str]:
        keyboard = bool(modal.tabs) and modal.tabs[modal.tab_index] == "TECLADO"
        table_width = max(24, table_width)
        compact = table_width < 54
        if keyboard:
            visible_width = 7
            field_width = max(8, min(29, (table_width - visible_width - 7) // 2))
            value_width = max(8, table_width - field_width - visible_width - 7)
            rows = [
                f"  {'CAMPO':<{field_width}}  {'TECLA/VALOR':<{value_width}}  VISIBLE",
                f"  {'─' * field_width}  {'─' * value_width}  {'─' * visible_width}",
            ]
        else:
            field_width = max(8, min(25, table_width // 4))
            hint_width = max(8, min(31, table_width // 4))
            value_width = max(8, table_width - field_width - hint_width - 8)
            rows = [
                f"  {'CAMPO':<{field_width}}  {'VALOR':<{value_width}}  FORMATO",
                f"  {'─' * field_width}  {'─' * value_width}  {'─' * hint_width}",
            ]
        if compact:
            heading = "CAMPO / TECLA / VISIBLE" if keyboard else "CAMPO / VALOR / FORMATO"
            rows = [f"  {cls._pad(heading, table_width - 2)}", "  " + "─" * (table_width - 2)]
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
            if keyboard:
                changed = (
                    "*"
                    if field.value != field.original or field.visible != field.original_visible
                    else " "
                )
                if compact:
                    rows.extend(
                        (
                            f"{marker}{changed} {cls._pad(field.label, table_width - 4)}",
                            (
                                f"   {cls._pad(field.value or 'None', table_width - 12)}  "
                                f"[{field.visible or 'OFF'}]"
                            ),
                        )
                    )
                else:
                    rows.append(
                        f"{marker}{changed} {cls._pad(field.label, field_width)} "
                        f" {cls._pad(field.value or 'None', value_width)}  {field.visible or 'OFF'}"
                    )
            else:
                value = field.value or "(vacío)"
                chunks = (
                    textwrap.wrap(
                        value,
                        width=value_width,
                        break_long_words=True,
                        break_on_hyphens=False,
                    )
                    if field.key == "listColumns"
                    else [fit_text(value, value_width)]
                )
                if compact:
                    rows.extend(
                        (
                            f"{marker}{changed} {cls._pad(field.label, table_width - 4)}",
                            f"   {cls._pad(value, table_width - 4)}",
                            f"   Formato: {cls._pad(field.hint, table_width - 12)}",
                        )
                    )
                else:
                    rows.append(
                        f"{marker}{changed} {cls._pad(field.label, field_width)}  "
                        f"{cls._pad(chunks[0], value_width)}  {fit_text(field.hint, hint_width)}"
                    )
                    rows.extend(
                        f"   {' ' * field_width}  {cls._pad(chunk, value_width)}"
                        for chunk in chunks[1:]
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
                "* cambio pendiente · Esc abre el menú de salida y guardado",
            )
        )
        # Ninguna fila puede forzar autowrap: el redimensionado del terminal
        # debe cambiar la geometría, no desplazar el borde inferior del modal.
        return [cls._pad(row, table_width).rstrip() for row in rows]

    @staticmethod
    def _pad(value: object, width: int) -> str:
        fitted = Text(str(value))
        fitted.truncate(max(0, width), overflow="ellipsis")
        return fitted.plain + " " * max(0, width - fitted.cell_len)

    @classmethod
    def handle_key(
        cls,
        modal: ModalState,
        key: str,
        *,
        close: Callable[[], None],
        open_remote_users: Callable[[], None],
    ) -> None:
        if not modal.items:
            return
        field = modal.items[modal.selected]
        if field.key == "remoteAccessUsers" and key in ("ENTER", "TAB"):
            open_remote_users()
            return
        keyboard_field = field.section == "TECLADO" and field.visible is not None
        if keyboard_field and not modal.editing and key in ("ENTER", "SPACE"):
            field.visible = "OFF" if field.visible == "ON" else "ON"
            return
        if field.key.startswith("tuiFixed.") and key in ("TAB", "SHIFT_TAB"):
            field.visible = "OFF" if field.visible == "ON" else "ON"
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
            modal.selected = remembered if remembered in indices else (indices[0] if indices else 0)
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
