"""TUI de pantalla completa de LANWIRE."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from contextlib import suppress
from copy import deepcopy
from pathlib import Path

from colorama import just_fix_windows_console
from rich.text import Text

from lanctl import __version__
from lanctl.apps.wire.cli.commands import CommandProcessor
from lanctl.apps.wire.graph import topology_text
from lanctl.apps.wire.idf.database import DEFAULT_DATABASE_PATH, IDFDatabaseManager
from lanctl.apps.wire.log import write_exception
from lanctl.apps.wire.topology import compatible_connection, groups_for
from lanctl.apps.wire.tui.detail import (
    cable_endpoints,
    cable_sides,
    combine_with_sidebar,
    element_detail,
    element_sidebar,
    rack_occupant,
    selectable_ports,
    wire_for_port,
)
from lanctl.apps.wire.tui.editor import (
    EditableField,
    actions_view,
    connection_browser_view,
    connector_actions,
    editable_fields,
    editor_view,
    element_options_view,
    field_options,
    options_view,
    set_field,
)
from lanctl.apps.wire.tui.help import COMMANDS, KEYS, help_view
from lanctl.apps.wire.tui.keyboard import read_key
from lanctl.apps.wire.tui.renderer import RichTuiRenderer, detail_modal_footer, footer_bar
from lanctl.apps.wire.tui.settings import load_settings, save_settings
from lanctl.core.layout import terminal_columns, terminal_rows

ENTER_SCREEN = "\x1b[?1049h\x1b[?7l\x1b[2J\x1b[H"
LEAVE_SCREEN = "\x1b[?25h\x1b[?7h\x1b[?1049l"


class LanwireTui:
    def __init__(self, database_path: str | Path = DEFAULT_DATABASE_PATH, stream=None) -> None:
        self.stream = stream or sys.stdout
        self.renderer = RichTuiRenderer(self.stream)
        self.database = IDFDatabaseManager(database_path)
        self.settings = load_settings()
        self.settings_draft: dict | None = None
        self.utility_modal: str | None = None
        self.delete_confirmation_id: str | None = None
        self.utility_selection = 0
        self.help_tab = 0
        self.help_scroll = 0
        self.clipboard_text = ""
        self.commands = CommandProcessor(self.database)
        self.all_records: list[dict] = []
        self.records: list[dict] = []
        self.list_prefix: str | None = None
        self.list_group: str | None = None
        self.list_kind = "elements"
        self.view_id: str | None = None
        self.modal_scroll = 0
        self.modal_selection = 0
        self.modal_endpoint = 0
        self._modal_size_key: tuple[str, int, int, str] | None = None
        self._modal_size_locked: tuple[int, int] | None = None
        self.modal_focus = "view"
        self.menu_selection = 0
        self.editor_scope = "general"
        self.editor_selection = 0
        self.editor_buffer: str | None = None
        self.editor_option_index: int | None = None
        self.action_selection = 0
        self.action_buffer: str | None = None
        self.action_option_index: int | None = None
        self.action_filter = ""
        self.navigation_stack: list[tuple[str, int, int]] = []
        self.selected_index = 0
        self.tree_scroll = 0
        self.messages = ["LANWIRE preparado. Escribe 'help' para ver los comandos."]
        self.cli_scroll = 0
        self.command = ""
        self.command_cursor = 0
        self._cli_prompt_line = 1
        self.running = True
        self._last_size = (0, 0)
        self.reload()

    def reload(self) -> None:
        selected = self.selected_id
        self.all_records = self.database.all()
        self.records = [
            record
            for record in self.all_records
            if self.list_kind == "all"
            or (((record.get("data") or {}).get("type") == "wire") == (self.list_kind == "wires"))
            if self.list_prefix is None or record["prefix"] == self.list_prefix
            if self.list_group is None or self.list_group in groups_for(record)
        ]
        if selected:
            self.selected_index = next(
                (i for i, record in enumerate(self.records) if record["id"] == selected),
                min(self.selected_index, max(0, len(self.records) - 1)),
            )
        else:
            self.selected_index = min(self.selected_index, max(0, len(self.records) - 1))

    @property
    def selected_id(self) -> str | None:
        return self.records[self.selected_index]["id"] if self.records else None

    def dimensions(self) -> tuple[int, int]:
        size = shutil.get_terminal_size(fallback=(120, 30))
        return (
            terminal_columns(self.stream) or max(20, size.columns),
            max(12, terminal_rows(self.stream) or size.lines),
        )

    @staticmethod
    def panel_heights(height: int) -> tuple[int, int]:
        usable = max(2, height - 1)
        lower = max(4, min(14, usable - 4, round(usable / 3) + 2))
        return usable - lower, lower

    def _panel_heights(self, height: int) -> tuple[int, int]:
        usable = max(2, height - 1)
        lower = max(4, min(min(18, usable - 4), int(self.settings["cliHeight"])))
        return usable - lower, lower

    def tree_view(self, content_height: int, width: int = 120) -> Text:
        """Tabla ASCII seleccionable de elementos; conserva el nombre histórico."""
        rows = max(1, content_height - 2)
        if self.selected_index < self.tree_scroll:
            self.tree_scroll = self.selected_index
        elif self.selected_index >= self.tree_scroll + rows:
            self.tree_scroll = self.selected_index - rows + 1
        margin = "  "
        table_width = max(20, width - len(margin))
        configured = self.settings["columnWidths"]
        idf_width = min(configured["idf"], max(6, table_width // 4))
        type_width = min(configured["type"], max(6, table_width // 4))
        name_width = min(configured["name"], max(6, table_width // 4))
        group_width = min(configured["group"], max(6, table_width // 5))
        show_groups = self.settings["showGroups"]
        group_space = group_width if show_groups else 0
        available_description = max(
            0,
            table_width
            - idf_width
            - type_width
            - name_width
            - group_space
            - (4 if show_groups else 3),
        )
        description_width = min(
            configured["description"] or available_description, available_description
        )

        visible_columns = (0, 1, 2, 3, 4) if show_groups else (0, 1, 2, 4)
        column_widths = [idf_width, type_width, name_width, group_width, description_width]
        overflow = (
            sum(column_widths[index] for index in visible_columns)
            + len(visible_columns)
            - 1
            - table_width
        )
        for index in (4, 3, 2, 1, 0):
            if index not in visible_columns or overflow <= 0:
                continue
            minimum = 0 if index == 4 else 6
            reduction = min(overflow, column_widths[index] - minimum)
            column_widths[index] -= reduction
            overflow -= reduction
        widths = tuple(column_widths)

        def append_row(
            values: tuple[str, ...], styles: tuple[str, ...], *, selected: bool = False
        ) -> None:
            for position, index in enumerate(visible_columns):
                if position:
                    text.append(" ")
                style = (
                    ("black" if index == 4 else styles[index]) + " on grey50"
                    if selected
                    else styles[index]
                )
                text.append(f"{values[index][: widths[index]]:<{widths[index]}}", style=style)

        text = Text(margin)
        append_row(
            ("IDF", "TYPE", "NAME", "GROUP", "DESCRIPTION"),
            ("bold bright_cyan",) * 5,
        )
        text.append("\n" + margin)
        append_row(tuple("─" * width for width in widths), ("dim cyan",) * 5)
        if not self.records:
            text.append("\n(sin registros para este filtro)", style="dim")
            return text
        visible = self.records[self.tree_scroll : self.tree_scroll + rows]
        for offset, record in enumerate(visible):
            index = self.tree_scroll + offset
            data = record.get("data") or {}
            definition = self.database.get_prefix(record["prefix"])
            element_type = data.get("subtype") or (
                definition["name"] if definition else data.get("type", "element")
            )
            name = data.get("name") or data.get("alias") or ""
            groups = "/".join(sorted(groups_for(record))) if show_groups else ""
            description = (
                data.get("description") or (definition.get("description", "") if definition else "")
                if self.settings["showDescriptions"]
                else ""
            )
            if self.settings["tableDensity"] == "compact":
                description = ""
            text.append("\n")
            text.append(
                "▶ " if index == self.selected_index else margin,
                style="bold bright_white" if index == self.selected_index else "",
            )
            if index == self.selected_index:
                append_row(
                    (record["id"], str(element_type), str(name), groups, str(description)),
                    ("bright_blue", "bright_yellow", "green", "yellow", "white"),
                    selected=True,
                )
            else:
                append_row(
                    (record["id"], str(element_type), str(name), groups, str(description)),
                    ("bright_blue", "bright_yellow", "green", "yellow", "white"),
                )
        return text

    def cli_view(self, content_height: int) -> Text:
        rows = max(0, content_height - 1)
        maximum_scroll = max(0, len(self.messages) - rows)
        self.cli_scroll = max(0, min(self.cli_scroll, maximum_scroll))
        start = max(0, len(self.messages) - rows - self.cli_scroll)
        text = Text()
        visible = self.messages[start : start + rows]
        for line in visible:
            text.append(line + "\n", style="white")
        for _ in range(rows - len(visible)):
            text.append("\n")
        self._cli_prompt_line = rows + 1
        text.append("lanwire> ", style="bold green")
        cursor = max(0, min(self.command_cursor, len(self.command)))
        text.append(self.command[:cursor], style="bright_white")
        text.append(self.command[cursor:], style="bright_white")
        return text

    def render(self) -> None:
        width, height = self.dimensions()
        upper_height, lower_height = self._panel_heights(height)
        detail_record = next(
            (record for record in self.all_records if record["id"] == self.view_id), None
        )
        upper = self.tree_view(upper_height - 1, width)
        modal = None
        modal_size = None
        if self.utility_modal:
            modal_title, modal = self._utility_modal_content()
            modal_size = (
                (max(28, width - 4), max(6, height - 4))
                if self.utility_modal == "help"
                else self.renderer.modal_size(modal, modal_title, width, height)
            )
        elif detail_record:
            modal_title = self._modal_title(detail_record)
            ports = selectable_ports(detail_record)
            selected_port = (
                ports[min(self.modal_selection, len(ports) - 1)]
                if ports and self.modal_selection >= 0
                else None
            )
            detail = element_detail(
                detail_record,
                self.all_records,
                max(20, width - 30),
                selected_port=selected_port,
                selected_endpoint=self.modal_endpoint,
            )
            fields = self._editing_fields(detail_record)
            self.editor_selection = min(self.editor_selection, max(0, len(fields) - 1))
            is_device = str((detail_record.get("data") or {}).get("type", "")).startswith("device.")
            is_wire = (detail_record.get("data") or {}).get("type") == "wire"
            connected_wire = (
                wire_for_port(detail_record, self.all_records, selected_port)
                if selected_port and is_device
                else None
            )
            if is_device:
                self.menu_selection = min(self.menu_selection, self._menu_count() - 1)
            if self.modal_focus == "editor":
                sidebar = (
                    editor_view(fields, self.editor_selection, self.editor_buffer)
                    if self.editor_option_index is None
                    else options_view(
                        fields[self.editor_selection],
                        self.editor_option_index,
                        self._editor_options(fields[self.editor_selection]),
                    )
                )
            elif self.modal_focus == "actions" and selected_port is not None and is_device:
                actions = connector_actions(connected_wire)
                self.action_selection = min(self.action_selection, len(actions) - 1)
                sidebar = (
                    connection_browser_view(
                        self._action_options(),
                        self.action_option_index or 0,
                        self.action_filter,
                        max_rows=max(3, height - 12),
                    )
                    if connected_wire is None
                    else actions_view(actions, self.action_selection, self.action_buffer)
                    if self.action_option_index is None
                    else options_view(
                        EditableField("cable", (), ""),
                        self.action_option_index,
                        self._action_options(),
                        filter_text=self.action_filter,
                    )
                )
            elif self.modal_focus == "actions" and is_wire:
                connected = cable_sides(detail_record)[min(self.modal_endpoint, 1)] is not None
                sidebar = (
                    options_view(
                        EditableField("elemento.puerto", (), ""),
                        self.action_option_index,
                        self._action_options(),
                        filter_text=self.action_filter,
                    )
                    if self.action_option_index is not None
                    else actions_view(
                        ["Desconectar"] if connected else ["Conectar"], 0, self.action_buffer
                    )
                )
            elif is_device:
                sidebar = element_options_view(
                    detail_record["id"],
                    selected_port,
                    connected_wire,
                    self.menu_selection,
                    self.modal_focus == "menu",
                )
            else:
                sidebar = element_sidebar(
                    detail_record,
                    self.all_records,
                    selected_port=selected_port,
                    selected_endpoint=self.modal_endpoint,
                    general_selected=self.modal_selection < 0,
                )
            combined = combine_with_sidebar(detail, sidebar, max(20, width - 10))
            detail_lines = list(combined.split("\n"))
            modal_size = self._fixed_modal_size(detail_record, width, height, modal_title)
            modal_rows = max(1, modal_size[1] - 4)
            highlighted = next(
                (span for span in combined.spans if str(span.style) == "bold black on bright_cyan"),
                None,
            )
            if highlighted is not None:
                selected_row = combined.plain[: highlighted.start].count("\n")
                if selected_row < self.modal_scroll:
                    self.modal_scroll = selected_row
                elif selected_row >= self.modal_scroll + modal_rows:
                    self.modal_scroll = selected_row - modal_rows + 1
            maximum_scroll = max(0, len(detail_lines) - modal_rows)
            self.modal_scroll = max(0, min(self.modal_scroll, maximum_scroll))
            modal = Text("\n").join(
                detail_lines[self.modal_scroll : self.modal_scroll + modal_rows]
            )
        lower = self.cli_view(lower_height - 1)
        prompt_row = upper_height + 1 + self._cli_prompt_line
        if self.settings["panelLayout"] == "cli.top":
            prompt_row = 1 + self._cli_prompt_line
        prompt_column = min(width, len("lanwire> ") + self.command_cursor + 1)
        modal_title = (
            self._utility_modal_content()[0]
            if self.utility_modal
            else self._modal_title(detail_record)
            if detail_record
            else "INFO"
        )
        self.renderer.render(
            upper,
            lower,
            footer_bar(width),
            width=width,
            height=height,
            upper_height=upper_height,
            lower_height=lower_height,
            cursor_row=prompt_row,
            cursor_column=prompt_column,
            modal=modal,
            modal_title=modal_title,
            modal_size=modal_size,
            modal_controls=detail_modal_footer(width)
            if detail_record and not self.utility_modal
            else None,
            upper_title=(
                f"LANWIRE TUI {__version__} ─ ListElement [{('WIRE' if self.list_kind == 'wires' else self.list_kind.upper())} · "
                f"{self.list_group or self.list_prefix or 'all'}] "
                f"{self.selected_index + 1 if self.records else 0}/{len(self.records)}"
            ),
            panel_layout=self.settings["panelLayout"],
        )
        self._last_size = (width, height)

    def _utility_modal_content(self) -> tuple[str, Text]:
        """Contenido de las ventanas globales, limitado al ámbito de LANWIRE."""
        modal = self.utility_modal
        if modal == "help":
            width, height = self.dimensions()
            return "HELP", help_view(
                max(20, width - 10),
                max(2, height - 8),
                self.help_tab,
                self.utility_selection,
                self.help_scroll,
            )
        if modal == "plugins":
            return "PLUGINS", Text(
                "  LANWIRE no carga plugins LCP.\n\n"
                "  El editor físico usa únicamente su base IDF local para que\n"
                "  la topología y sus conexiones sigan siendo deterministas."
            )
        if modal == "project":
            return "ESPACIO FÍSICO", Text(
                "  BASE IDF ACTIVA\n\n"
                f"  {self.database.path}\n\n"
                "  Los cambios de topología se guardan de forma atómica al\n"
                "  confirmar cada edición. LANWIRE no muestra proyectos, redes\n"
                "  ni preferencias de otros launchers en esta ventana."
            )
        if modal == "history":
            lines = self.messages[-12:] or ["(No hay comandos en esta sesión.)"]
            return "HISTORIAL", Text("\n".join(f"  {line}" for line in lines))
        if modal == "delete":
            identifier = self.delete_confirmation_id or "(sin selección)"
            return "ELIMINAR ELEMENTO", Text(
                f"  Vas a eliminar {identifier}.\n\n"
                "  Se desconectarán sus extremos de cable y se eliminarán\n"
                "  referencias de rack asociadas. Los cables permanecerán\n"
                "  como extremos libres.\n\n"
                "  Enter confirmar   Esc cancelar",
                style="bright_white",
            )
        if modal == "graph":
            return "TOPOLOGÍA", topology_text(self.all_records, self.selected_id)

        draft = self.settings_draft or self.settings
        rows = (
            ("Posición del CLI", draft["panelLayout"], "cli.top / cli.bottom"),
            ("Altura del panel CLI", f"{draft['cliHeight']} líneas", "8 a 18"),
            ("Densidad de tabla", draft["tableDensity"], "compact / comfortable"),
            ("Mostrar descripciones", "ON" if draft["showDescriptions"] else "OFF", "tabla"),
            ("Mostrar grupos", "ON" if draft["showGroups"] else "OFF", "tabla"),
            ("Confirmar salida", "ON" if draft["confirmExit"] else "OFF", "Ctrl+Q / Esc"),
            ("Columna IDF", f"{draft['columnWidths']['idf']} ch", "6 a 60"),
            ("Columna TYPE", f"{draft['columnWidths']['type']} ch", "6 a 60"),
            ("Columna NAME", f"{draft['columnWidths']['name']} ch", "6 a 60"),
            ("Columna GROUP", f"{draft['columnWidths']['group']} ch", "6 a 60"),
            (
                "Columna DESCRIPTION",
                f"{draft['columnWidths']['description'] or 'AUTO'}",
                "0=auto, 8 a 60",
            ),
        )
        self.utility_selection = min(self.utility_selection, len(rows) - 1)
        text = Text("  CONFIGURACIÓN EXCLUSIVA DE LANWIRE\n\n", style="bold bright_cyan")
        text.append("  CAMPO                         VALOR                 ÁMBITO\n", style="bold")
        for index, (label, value, scope) in enumerate(rows):
            style = "bold black on bright_cyan" if index == self.utility_selection else "white"
            text.append(f"  {label:<29} {value:<21} {scope}", style=style)
            if index < len(rows) - 1:
                text.append("\n")
        text.append(
            "\n\n  ↑/↓ seleccionar   ←/→ cambiar   Ctrl+S guardar   Esc cerrar", style="dim"
        )
        return "SETTINGS", text

    @staticmethod
    def _modal_title(record: dict) -> str:
        alias = (record.get("data") or {}).get("alias")
        return record["id"] + (f" · {alias}" if alias else "")

    def _fixed_modal_size(
        self, record: dict, width: int, height: int, title: str
    ) -> tuple[int, int]:
        """Estabiliza cada modo sin agrandar la vista por editores ocultos."""
        mode = self.modal_focus if self.modal_focus in {"editor", "actions"} else "view"
        key = (record["id"], width, height, mode)
        if self._modal_size_key == key and self._modal_size_locked is not None:
            return self._modal_size_locked

        ports = selectable_ports(record)
        states: list[tuple[str | None, int]]
        if ports:
            states = [(port, 0) for port in ports]
        elif (record.get("data") or {}).get("type") == "wire":
            states = [(None, endpoint) for endpoint in range(2)]
        else:
            states = [(None, 0)]

        sizes: list[tuple[int, int]] = []
        controls = detail_modal_footer(width)
        for selected_port, selected_endpoint in states:
            detail = element_detail(
                record,
                self.all_records,
                max(20, width - 30),
                selected_port=selected_port,
                selected_endpoint=selected_endpoint,
            )
            sidebar = element_sidebar(
                record,
                self.all_records,
                selected_port=selected_port,
                selected_endpoint=selected_endpoint,
            )
            content = combine_with_sidebar(detail, sidebar, max(20, width - 10))
            if mode == "view":
                sizes.append(
                    self.renderer.modal_size(content, title, width, height, controls=controls)
                )
                if str((record.get("data") or {}).get("type", "")).startswith("device."):
                    menu = element_options_view(record["id"], selected_port, None, 0, False)
                    sizes.append(
                        self.renderer.modal_size(
                            combine_with_sidebar(detail, menu, max(20, width - 10)),
                            title,
                            width,
                            height,
                            controls=controls,
                        )
                    )
            elif mode == "editor":
                edit = editor_view(editable_fields(record, selected_port, selected_endpoint), 0)
                edit_content = combine_with_sidebar(detail, edit, max(20, width - 10))
                sizes.append(
                    self.renderer.modal_size(edit_content, title, width, height, controls=controls)
                )
            elif selected_port is not None:
                browser = connection_browser_view(
                    self._available_cables(record, selected_port),
                    0,
                    "",
                    max_rows=max(3, height - 12),
                )
                sizes.append(
                    self.renderer.modal_size(
                        combine_with_sidebar(detail, browser, max(20, width - 10)),
                        title,
                        width,
                        height,
                        controls=controls,
                    )
                )
                for connected in (None, "XX-00"):
                    action_content = combine_with_sidebar(
                        detail, actions_view(connector_actions(connected), 0), max(20, width - 10)
                    )
                    sizes.append(
                        self.renderer.modal_size(
                            action_content, title, width, height, controls=controls
                        )
                    )
            else:
                sizes.append(
                    self.renderer.modal_size(content, title, width, height, controls=controls)
                )
                if (record.get("data") or {}).get("type") == "wire":
                    wire_actions = actions_view(["Conectar", "Desconectar"], 0)
                    sizes.append(
                        self.renderer.modal_size(
                            combine_with_sidebar(detail, wire_actions, max(20, width - 10)),
                            title,
                            width,
                            height,
                            controls=controls,
                        )
                    )
        self._modal_size_key = key
        self._modal_size_locked = (max(size[0] for size in sizes), max(size[1] for size in sizes))
        return self._modal_size_locked

    def execute(self) -> None:
        command = self.command.strip()
        self.command = ""
        self.command_cursor = 0
        if not command:
            return
        self.messages.append(f"lanwire> {command}")
        result = self.commands.execute(command, selected_id=self.selected_id)
        if command.casefold() == "clear":
            self.messages.clear()
        elif result.view_id:
            self.messages.append(
                f"Visualizando {result.view_id}. Pulsa Esc para volver a la lista."
            )
        elif command.split()[0].casefold() in ("list", "ls"):
            label = f"@{result.list_group}" if result.list_group else result.list_prefix or "todos"
            self.messages.append(f"Lista activa: {label}")
        else:
            for block in result.lines:
                self.messages.extend(block.splitlines() or [""])
        if command.split()[0].casefold() in ("list", "ls"):
            self.list_prefix = result.list_prefix
            self.list_group = result.list_group
            self.view_id = None
            self.selected_index = 0
            self.tree_scroll = 0
            self.reload()
        if result.view_id:
            self.view_id = result.view_id
            self.modal_focus = "view"
            self.editor_buffer = None
            self._modal_size_key = None
            self._modal_size_locked = None
            self.modal_scroll = 0
            self.modal_selection = 0
            self.modal_endpoint = 0
            self.navigation_stack.clear()
        if result.graph:
            self._open_utility("graph")
        if result.refresh:
            self.reload()
        if result.exit_requested:
            self.running = False
        self.cli_scroll = 0

    def handle_key(self, key: str) -> None:
        if self.utility_modal:
            self._handle_utility_key(key)
            return
        if key == "F3" and self.view_id:
            if any(
                value is not None
                for value in (
                    self.editor_buffer,
                    self.action_buffer,
                    self.editor_option_index,
                    self.action_option_index,
                )
            ):
                self.messages.append("Termina o cancela la edición antes de seguir la conexión.")
            else:
                self._follow_connection()
            return
        if self.view_id and self.modal_focus == "editor":
            if key == "TAB":
                self.modal_focus = "menu" if self._is_device_detail() else "actions"
                self.editor_buffer = None
                self.editor_option_index = None
            elif key == "ESC" and self.editor_buffer is not None:
                self.editor_buffer = None
            elif key == "LEFT" and self.editor_option_index is not None:
                self.editor_option_index = None
            elif key == "RIGHT" and self.editor_buffer is None:
                options = self._editor_options(self._editor_field())
                if options:
                    self.editor_option_index = 0
            elif key == "ESC":
                if self.editor_option_index is not None:
                    self.editor_option_index = None
                else:
                    self.modal_focus = "menu" if self._is_device_detail() else "view"
            elif key in ("UP", "DOWN") and self.editor_option_index is not None:
                options = self._editor_options(self._editor_field())
                self.editor_option_index = max(
                    0, min(len(options) - 1, self.editor_option_index + (-1 if key == "UP" else 1))
                )
            elif key in ("UP", "DOWN") and self.editor_buffer is None:
                self._move_editor_selection(-1 if key == "UP" else 1)
            elif key == "ENTER":
                if self.editor_option_index is None:
                    field = self._editor_field()
                    options = self._editor_options(field)
                    if (
                        self.editor_buffer is None
                        and options
                        and (
                            field.label in {"type", "kind", "lanipDevice"}
                            or field.label.endswith((".kind", ".poe"))
                        )
                    ):
                        self.editor_option_index = 0
                    else:
                        self._edit_or_save_field()
                else:
                    self._apply_editor_option()
            elif key == "BACKSPACE" and self.editor_buffer is not None:
                self.editor_buffer = self.editor_buffer[:-1]
            elif self.editor_buffer is not None and len(key) == 1 and key.isprintable():
                self.editor_buffer += key
            return
        if self.view_id and self.modal_focus == "menu":
            if key in ("ESC", "TAB"):
                self.modal_focus = "view"
            elif key in ("UP", "DOWN"):
                self.menu_selection = max(
                    0, min(self._menu_count() - 1, self.menu_selection + (-1 if key == "UP" else 1))
                )
            elif key == "ENTER":
                self._choose_element_option()
            return
        if self.view_id and self.modal_focus == "actions":
            if key == "TAB":
                self.modal_focus = (
                    "view"
                    if (self._modal_record() or {}).get("data", {}).get("type") == "wire"
                    else "menu"
                )
                self.action_buffer = None
                self.action_option_index = None
                self.action_filter = ""
            elif self.action_option_index is not None and key == "LEFT":
                self.action_option_index = None
                self.action_filter = ""
            elif self.action_option_index is not None and key in ("UP", "DOWN"):
                options = self._action_options()
                self.action_option_index = max(
                    0,
                    min(len(options) - 1, self.action_option_index + (-1 if key == "UP" else 1)),
                )
            elif self.action_option_index is not None and key == "ENTER" and self.action_buffer:
                self.action_option_index = None
                self.action_filter = ""
                self._execute_connector_action()
            elif self.action_option_index is not None and key == "ENTER":
                options = self._action_options()
                if options:
                    self.action_buffer = options[self.action_option_index]
                    self.action_option_index = None
                    self.action_filter = ""
                    self._execute_connector_action()
            elif self.action_option_index is not None and key == "ESC":
                self.action_option_index = None
                self.action_filter = ""
            elif self.action_option_index is not None and key == "BACKSPACE":
                self.action_filter = self.action_filter[:-1]
                self.action_option_index = 0
            elif self.action_option_index is not None and len(key) == 1 and key.isprintable():
                self.action_filter += key
                self.action_option_index = 0
            elif key == "ESC" and self.action_buffer is not None:
                self.action_buffer = None
            elif key == "ESC":
                if (self._modal_record() or {}).get("data", {}).get("type") == "wire":
                    self.modal_focus = "view"
                else:
                    self.modal_focus = "menu"
            elif key in ("UP", "DOWN") and self.action_buffer is None:
                self._move_action_selection(-1 if key == "UP" else 1)
            elif key == "ENTER":
                self._execute_connector_action()
            elif key == "BACKSPACE" and self.action_buffer is not None:
                self.action_buffer = self.action_buffer[:-1]
            elif self.action_buffer is not None and len(key) == 1 and key.isprintable():
                self.action_buffer += key
            return
        if key == "F1":
            self._open_utility("help")
        elif key == "F7":
            self._open_utility("plugins")
        elif key == "F9":
            self._open_utility("project")
        elif key == "F12":
            self._open_utility("settings")
        elif key == "CTRL_H":
            self._open_utility("history")
        elif key == "CTRL_S":
            save_settings(self.settings)
            self.messages.append("Preferencias de LANWIRE guardadas.")
        elif key == "CTRL_C":
            self._copy_selected(as_json=False)
        elif key == "CTRL_J":
            self._copy_selected(as_json=True)
        elif key == "CTRL_Q":
            self.running = False
        elif key == "ESC" and self.view_id:
            self.view_id = None
            self.navigation_stack.clear()
        elif key == "TAB" and self.view_id:
            if self._is_device_detail():
                self.modal_focus = "menu"
                self.menu_selection = 0
            else:
                self.modal_focus = "editor"
                self.editor_scope = "general"
                self.editor_selection = 0
                self.editor_buffer = None
                self.editor_option_index = None
        elif key == "TAB" and not self.command:
            views = ("elements", "wires", "all")
            self.list_kind = views[(views.index(self.list_kind) + 1) % len(views)]
            self.selected_index = 0
            self.tree_scroll = 0
            self.reload()
            self.messages.append(
                f"Vista de {('WIRE' if self.list_kind == 'wires' else self.list_kind.upper())} activa."
            )
        elif key == "DELETE" and not self.view_id and not self.command and self.selected_id:
            self.delete_confirmation_id = self.selected_id
            self._open_utility("delete")
        elif key == "ENTER" and not self.view_id and not self.command and self.selected_id:
            self.view_id = self.selected_id
            self.modal_focus = "view"
            self.editor_buffer = None
            self._modal_size_key = None
            self._modal_size_locked = None
            self.modal_scroll = 0
            self.modal_selection = 0
            self.modal_endpoint = 0
            self.navigation_stack.clear()
        elif self.view_id and key in ("UP", "DOWN"):
            self._move_modal_selection(-1 if key == "UP" else 1)
        elif self.view_id and key in ("LEFT", "RIGHT"):
            self._move_cable_endpoint(-1 if key == "LEFT" else 1)
        elif self.view_id and key in ("PGUP", "PGDN"):
            self.modal_scroll = max(0, self.modal_scroll + (-5 if key == "PGUP" else 5))
        elif self.view_id and key == "ENTER":
            if self._is_device_detail():
                self.modal_focus = "menu"
                self.menu_selection = 0
            else:
                self._follow_connection()
        elif self.view_id and key == "BACKSPACE":
            self._navigate_back()
        elif self.view_id:
            return
        elif key == "ESC":
            self.running = False
        elif key == "ENTER":
            self.execute()
        elif key == "BACKSPACE":
            if self.command_cursor:
                self.command = (
                    self.command[: self.command_cursor - 1] + self.command[self.command_cursor :]
                )
                self.command_cursor -= 1
        elif key == "DELETE":
            self.command = (
                self.command[: self.command_cursor] + self.command[self.command_cursor + 1 :]
            )
        elif key == "LEFT" and self.command:
            self.command_cursor = max(0, self.command_cursor - 1)
        elif key == "RIGHT" and self.command:
            self.command_cursor = min(len(self.command), self.command_cursor + 1)
        elif key == "UP" and not self.command:
            self.selected_index = max(0, self.selected_index - 1)
        elif key == "DOWN" and not self.command:
            self.selected_index = min(max(0, len(self.records) - 1), self.selected_index + 1)
        elif key == "PGUP":
            self.cli_scroll += 1
        elif key == "PGDN":
            self.cli_scroll = max(0, self.cli_scroll - 1)
        elif len(key) == 1 and key.isprintable():
            self.command = (
                self.command[: self.command_cursor] + key + self.command[self.command_cursor :]
            )
            self.command_cursor += 1

    def _open_detail(self, identifier: str) -> None:
        self.view_id = identifier
        self.modal_focus = "view"
        self.editor_buffer = None
        self._modal_size_key = None
        self._modal_size_locked = None
        self.modal_scroll = 0
        self.modal_selection = 0
        self.modal_endpoint = 0
        self.navigation_stack.clear()

    def _open_utility(self, modal: str) -> None:
        self.utility_modal = modal
        self.utility_selection = 0
        self.help_tab = 0
        self.help_scroll = 0
        self.settings_draft = deepcopy(self.settings) if modal == "settings" else None

    def _handle_utility_key(self, key: str) -> None:
        if self.utility_modal == "help":
            if key in ("ESC", "F1"):
                self.utility_modal = None
            elif key in ("LEFT", "RIGHT"):
                self.help_tab = (self.help_tab + (-1 if key == "LEFT" else 1)) % 3
                self.help_scroll = 0
            elif key == "TAB":
                entry = COMMANDS[self.utility_selection]
                self.command = f"{entry.name} "
                self.command_cursor = len(self.command)
                self.utility_modal = None
            elif key == "ENTER" and self.help_tab == 0:
                self.help_tab = 1
                self.help_scroll = 0
            elif key in ("UP", "DOWN", "PGUP", "PGDN", "HOME", "END"):
                if self.help_tab == 0:
                    last = len(COMMANDS) - 1
                    if key == "HOME":
                        self.utility_selection = 0
                    elif key == "END":
                        self.utility_selection = last
                    else:
                        step = 10 if key in ("PGUP", "PGDN") else 1
                        delta = -step if key in ("UP", "PGUP") else step
                        self.utility_selection = max(0, min(last, self.utility_selection + delta))
                    visible = max(1, self.dimensions()[1] - 10)
                    self.help_scroll = max(
                        min(self.help_scroll, self.utility_selection),
                        self.utility_selection - visible + 1,
                    )
                else:
                    lines = KEYS if self.help_tab == 2 else ("",) * 9
                    maximum = max(0, len(lines) - max(1, self.dimensions()[1] - 10))
                    delta = (
                        -10 if key == "PGUP" else 10 if key == "PGDN" else -1 if key == "UP" else 1
                    )
                    self.help_scroll = (
                        0
                        if key == "HOME"
                        else maximum
                        if key == "END"
                        else max(0, min(maximum, self.help_scroll + delta))
                    )
            return
        if self.utility_modal == "delete":
            if key == "ENTER" and self.delete_confirmation_id:
                identifier = self.delete_confirmation_id
                try:
                    self.database.delete(identifier)
                    self.view_id = None
                    self.navigation_stack.clear()
                    self.selected_index = 0
                    self.tree_scroll = 0
                    self.reload()
                    self.messages.append(f"Eliminado {identifier}; enlaces físicos limpiados.")
                except KeyError:
                    self.messages.append(f"No existe {identifier}.")
                finally:
                    self.delete_confirmation_id = None
                    self.utility_modal = None
                return
            if key in ("ESC", "DELETE"):
                self.delete_confirmation_id = None
                self.utility_modal = None
            return
        if key in ("ESC", "F1", "F7", "F9", "F12"):
            self.utility_modal = None
            self.settings_draft = None
            return
        if self.utility_modal != "settings":
            return
        if key == "UP":
            self.utility_selection = max(0, self.utility_selection - 1)
        elif key == "DOWN":
            self.utility_selection = min(10, self.utility_selection + 1)
        elif key in ("LEFT", "RIGHT", "ENTER"):
            assert self.settings_draft is not None
            field = (
                "panelLayout",
                "cliHeight",
                "tableDensity",
                "showDescriptions",
                "showGroups",
                "confirmExit",
                "idf",
                "type",
                "name",
                "group",
                "description",
            )[self.utility_selection]
            if field in {"idf", "type", "name", "group", "description"}:
                minimum = 0 if field == "description" else 6
                delta = -1 if key == "LEFT" else 1
                self.settings_draft["columnWidths"][field] = max(
                    minimum, min(60, self.settings_draft["columnWidths"][field] + delta)
                )
                return
            if field == "panelLayout":
                self.settings_draft[field] = (
                    "cli.top" if self.settings_draft[field] == "cli.bottom" else "cli.bottom"
                )
                return
            if field == "cliHeight":
                delta = -1 if key == "LEFT" else 1
                self.settings_draft[field] = max(8, min(18, self.settings_draft[field] + delta))
            elif field == "tableDensity":
                self.settings_draft[field] = (
                    "compact" if self.settings_draft[field] == "comfortable" else "comfortable"
                )
            else:
                self.settings_draft[field] = not self.settings_draft[field]
        elif key == "CTRL_S":
            assert self.settings_draft is not None
            self.settings = deepcopy(self.settings_draft)
            save_settings(self.settings)
            self.messages.append("Configuración local de LANWIRE guardada.")

    def _copy_selected(self, *, as_json: bool) -> None:
        record = self._modal_record() or next(
            (item for item in self.all_records if item["id"] == self.selected_id), None
        )
        if record is None:
            self.messages.append("No hay un elemento seleccionado para copiar.")
            return
        payload = json.dumps(record, ensure_ascii=False, indent=2) if as_json else record["id"]
        self.clipboard_text = payload
        if os.name == "nt":
            with suppress(OSError):
                subprocess.run(["clip"], input=payload, text=True, check=True, capture_output=True)
        self.messages.append("JSON copiado." if as_json else f"IDF copiado: {record['id']}.")

    def _modal_record(self):
        return next((record for record in self.all_records if record["id"] == self.view_id), None)

    def _is_device_detail(self) -> bool:
        record = self._modal_record()
        return bool(
            record and str((record.get("data") or {}).get("type", "")).startswith("device.")
        )

    def _menu_count(self) -> int:
        context = self._selected_connector()
        return 7 if context and context[2] else 4

    def _choose_element_option(self) -> None:
        context = self._selected_connector()
        choice = self.menu_selection
        if choice in (0, 1):
            if choice == 1 and context is None:
                self.messages.append("Selecciona primero un puerto.")
                return
            self.editor_scope = "general" if choice == 0 else "port"
            self.modal_focus = "editor"
            self.editor_selection = 0
            self.editor_buffer = None
            self.editor_option_index = None
            return
        if choice == 3 and self.view_id:
            self.delete_confirmation_id = self.view_id
            self._open_utility("delete")
            return
        if context is None:
            self.messages.append("Selecciona primero un puerto.")
            return
        _record, _port, wire_id = context
        if choice == 2:
            if wire_id:
                self.messages.append("El puerto ya tiene cable. Usa Editar o Desconectar cable.")
                return
            self.modal_focus = "actions"
            self.action_selection = 0
            self.action_buffer = None
            self._execute_connector_action()
        elif choice == 4 and wire_id:
            self.modal_focus = "view"
            self._follow_connection()
        elif choice == 5 and wire_id:
            self._disconnect_selected_port()
            self.menu_selection = 2
        elif choice == 6 and wire_id:
            self.modal_focus = "actions"
            self.action_selection = 1
            self.action_buffer = None
            self._execute_connector_action()

    def _editing_fields(self, record: dict) -> list[EditableField]:
        ports = selectable_ports(record)
        selected_port = (
            ports[min(self.modal_selection, len(ports) - 1)]
            if ports and self.modal_selection >= 0
            else None
        )
        fields = editable_fields(record, selected_port, self.modal_endpoint)
        if self._is_device_detail():
            return [
                field
                for field in fields
                if (len(field.path) >= 2 and field.path[0] == "ports")
                == (self.editor_scope == "port")
            ]
        return fields

    def _move_editor_selection(self, delta: int) -> None:
        record = self._modal_record()
        if not record:
            return
        fields = self._editing_fields(record)
        self.editor_selection = max(0, min(len(fields) - 1, self.editor_selection + delta))

    def _editor_field(self):
        record = self._modal_record()
        if not record:
            raise RuntimeError("no hay elemento activo")
        fields = self._editing_fields(record)
        return fields[min(self.editor_selection, len(fields) - 1)]

    def _apply_editor_option(self) -> None:
        field = self._editor_field()
        options = self._editor_options(field)
        if self.editor_option_index is None or not options:
            return
        self.editor_buffer = options[self.editor_option_index]
        self.editor_option_index = None
        self._edit_or_save_field()

    @staticmethod
    def _editor_options(field) -> tuple[str, ...]:
        if field.label != "lanipDevice":
            return field_options(field)
        try:
            from lanctl.core.config import load_config
            from lanctl.core.database import DeviceDatabase

            devices = DeviceDatabase(load_config()["database"]).load()
        except (KeyError, OSError, ValueError):
            return ()
        values = []
        for device in devices:
            label = device.alias or device.name or device.ip or device.mac
            if label:
                values.append(str(label))
        return tuple(dict.fromkeys(values))

    def _selected_connector(self) -> tuple[dict, str, str | None] | None:
        record = self._modal_record()
        if not record or not str((record.get("data") or {}).get("type", "")).startswith("device."):
            return None
        if self.modal_selection < 0:
            return None
        ports = selectable_ports(record)
        if not ports:
            return None
        port = ports[min(self.modal_selection, len(ports) - 1)]
        return record, port, wire_for_port(record, self.all_records, port)

    def _move_action_selection(self, delta: int) -> None:
        record = self._modal_record()
        if record and (record.get("data") or {}).get("type") == "wire":
            self.action_selection = 0
            return
        context = self._selected_connector()
        actions = connector_actions(context[2]) if context else ["Sin acciones"]
        self.action_selection = max(0, min(len(actions) - 1, self.action_selection + delta))

    def _execute_connector_action(self) -> None:
        record = self._modal_record()
        if record and (record.get("data") or {}).get("type") == "wire":
            self._execute_wire_side_action(record)
            return
        context = self._selected_connector()
        if context is None:
            return
        record, port, wire_id = context
        actions = connector_actions(wire_id)
        self.action_selection = min(self.action_selection, len(actions) - 1)
        action = actions[self.action_selection]
        if action == "Editar cable":
            self.modal_focus = "view"
            self._follow_connection()
            return
        if action == "Desconectar":
            self._disconnect_selected_port()
            self.action_selection = 0
            return
        if self.action_buffer is None and action == "Mover":
            self.action_buffer = ""
            return
        if self.action_buffer is None:
            available = self._available_cables(record, port)
            if not available:
                self.messages.append("No hay cables libres y compatibles para este puerto.")
            self.action_option_index = 0
            self.action_filter = ""
            return
        target = self.action_buffer.strip().upper()
        try:
            if action == "Conectar":
                self._connect_selected_port(record, port, target)
            elif action == "Mover":
                self._move_selected_connection(record, port, wire_id, target)
            self.action_buffer = None
            self.action_selection = 0
            self.modal_focus = "menu"
        except (KeyError, TypeError, ValueError) as error:
            self.messages.append(f"No se pudo {action.casefold()}: {error}")

    def _available_cables(self, record: dict, port: str) -> tuple[str, ...]:
        """Solo ofrece cables con un extremo libre y medio compatible."""
        port_data = (record.get("data") or {}).get("ports", {}).get(port, {})
        candidates = []
        for wire in self.all_records:
            data = wire.get("data") or {}
            if (
                data.get("type") != "wire"
                or sum(side is not None for side in cable_sides(wire)) >= 2
            ):
                continue
            compatible, _reason = compatible_connection(data, port_data)
            if compatible:
                candidates.append(wire["id"])
        return tuple(candidates)

    def _available_cables_for_selected_port(self) -> tuple[str, ...]:
        context = self._selected_connector()
        return self._available_cables(context[0], context[1]) if context else ()

    def _available_ports_for_wire(self, wire: dict) -> tuple[str, ...]:
        candidates = []
        for record in self.all_records:
            if not str((record.get("data") or {}).get("type", "")).startswith("device."):
                continue
            for port, port_data in ((record.get("data") or {}).get("ports") or {}).items():
                compatible, _ = compatible_connection(wire.get("data") or {}, port_data)
                if compatible and not wire_for_port(record, self.all_records, port):
                    candidates.append(f"{record['id']}.{port}")
        return tuple(candidates)

    def _action_options(self) -> tuple[str, ...]:
        record = self._modal_record()
        if record and (record.get("data") or {}).get("type") == "wire":
            options = self._available_ports_for_wire(record)
        else:
            options = self._available_cables_for_selected_port()
        query = self.action_filter.casefold().strip()
        return tuple(option for option in options if query in option.casefold())

    def _execute_wire_side_action(self, wire: dict) -> None:
        side = cable_sides(wire)[min(self.modal_endpoint, 1)]
        if side is not None:
            data = dict(wire.get("data") or {})
            if side.get("external"):
                data.pop("source", None)
            else:
                data["endpoints"] = [
                    endpoint
                    for endpoint in data.get("endpoints", [])
                    if not (
                        endpoint.get("device") == side.get("device")
                        and str(endpoint.get("port")) == str(side.get("port"))
                    )
                ]
            self.database.update(wire["id"], data)
            self.reload()
            self.messages.append(f"Desconectado el lado {self.modal_endpoint + 1} de {wire['id']}")
            self.action_buffer = None
            return
        if self.action_buffer is None:
            available = self._available_ports_for_wire(wire)
            if available:
                self.action_option_index = 0
                self.action_filter = ""
            else:
                self.messages.append("No hay puertos libres y compatibles para este cable.")
            return
        destination = self.action_buffer.strip().upper()
        try:
            device_id, port = destination.rsplit(".", 1)
            device = next((item for item in self.all_records if item["id"] == device_id), None)
            if device is None or not str((device.get("data") or {}).get("type", "")).startswith(
                "device."
            ):
                raise ValueError(f"elemento inexistente: {device_id}")
            port_data = (device.get("data") or {}).get("ports", {}).get(port)
            if port_data is None:
                raise ValueError(f"puerto inexistente: {destination}")
            if wire_for_port(device, self.all_records, port):
                raise ValueError(f"{destination} ya está conectado")
            data = dict(wire.get("data") or {})
            endpoints = list(data.get("endpoints", []))
            compatible, reason = compatible_connection(data, port_data, wire_end=len(endpoints))
            if not compatible:
                raise ValueError(reason)
            if len(endpoints) >= 2:
                raise ValueError(f"{wire['id']} ya tiene dos extremos")
            endpoints.append({"device": device_id, "port": port})
            data["endpoints"] = endpoints
            self.database.update(wire["id"], data)
            self.reload()
            self.messages.append(f"Conectado {wire['id']} a {destination}")
            self.action_buffer = None
        except (ValueError, TypeError) as error:
            self.messages.append(f"No se pudo conectar: {error}")

    def _connect_selected_port(self, record: dict, port: str, wire_id: str) -> None:
        wire = next((item for item in self.all_records if item["id"] == wire_id), None)
        if wire is None or (wire.get("data") or {}).get("type") != "wire":
            raise ValueError(f"cable inexistente: {wire_id}")
        if wire_for_port(record, self.all_records, port):
            raise ValueError(f"{record['id']}.{port} ya está conectado")
        data = dict(wire.get("data") or {})
        endpoints = list(data.get("endpoints", []))
        if len(endpoints) >= 2:
            raise ValueError(f"{wire_id} ya tiene dos extremos")
        port_data = (record.get("data") or {}).get("ports", {}).get(port, {})
        compatible, reason = compatible_connection(data, port_data, wire_end=len(endpoints))
        if not compatible:
            raise ValueError(reason)
        endpoints.append({"device": record["id"], "port": port})
        data["endpoints"] = endpoints
        self.database.update(wire_id, data)
        self.reload()
        self.messages.append(f"Conectado {wire_id} a {record['id']}.{port}")

    def _move_selected_connection(
        self, record: dict, port: str, wire_id: str | None, target_port: str
    ) -> None:
        ports = (record.get("data") or {}).get("ports", {})
        if not wire_id:
            raise ValueError("el puerto no tiene cable")
        if target_port not in ports:
            raise ValueError(f"puerto inexistente: {target_port}")
        if wire_for_port(record, self.all_records, target_port):
            raise ValueError(f"{record['id']}.{target_port} ya está conectado")
        wire = next(item for item in self.all_records if item["id"] == wire_id)
        data = dict(wire.get("data") or {})
        compatible, reason = compatible_connection(data, ports[target_port])
        if not compatible:
            raise ValueError(reason)
        data["endpoints"] = [
            {**endpoint, "port": target_port}
            if endpoint.get("device") == record["id"] and str(endpoint.get("port")) == port
            else endpoint
            for endpoint in data.get("endpoints", [])
        ]
        self.database.update(wire_id, data)
        self.reload()
        selectable = selectable_ports(record)
        self.modal_selection = selectable.index(target_port)
        self.messages.append(
            f"Movido {wire_id}: {record['id']}.{port} -> {record['id']}.{target_port}"
        )

    def _edit_or_save_field(self) -> None:
        record = self._modal_record()
        if not record:
            return
        fields = self._editing_fields(record)
        if not fields:
            return
        self.editor_selection = min(self.editor_selection, len(fields) - 1)
        field = fields[self.editor_selection]
        if field.label == "Eliminar puerto":
            if self.editor_buffer is None:
                self.editor_buffer = "Pulsa Enter otra vez para eliminar"
            else:
                self._delete_selected_port()
            return
        if self.editor_buffer is None:
            self.editor_buffer = field.shown_value
            return
        if field.path[-1] in {"name", "position"} and field.path[0] == "ports":
            try:
                port = str(field.path[1])
                if field.path[-1] == "name":
                    updated = self.database.edit_port(record["id"], port, name=self.editor_buffer)
                    selected_name = self.editor_buffer.strip()
                else:
                    updated = self.database.edit_port(
                        record["id"], port, position=int(self.editor_buffer)
                    )
                    selected_name = port
                self.reload()
                self.modal_selection = selectable_ports(updated).index(selected_name)
                self.editor_buffer = None
                self._modal_size_key = None
                self._modal_size_locked = None
                self.messages.append(f"Actualizado {record['id']}.{port}: {field.path[-1]}")
            except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
                reported = write_exception(
                    error,
                    caused="lanwire.tui.editor",
                    code="LANWIRE_PORT_UPDATE_FAILED",
                    context={"idf": record["id"], "port": field.path[1], "field": field.path[-1]},
                )
                self.editor_buffer = None
                self.messages.append(f"Error [{reported.code}] editando puerto: {reported.text}")
            return
        try:
            data = deepcopy(record.get("data") or {})
            set_field(data, field, self.editor_buffer)
            removed_ports = set((record.get("data") or {}).get("ports") or {}) - set(
                data.get("ports") or {}
            )
            connected_ports = [
                port for port in removed_ports if wire_for_port(record, self.all_records, port)
            ]
            if connected_ports:
                raise ValueError(
                    f"desconecta antes los puertos: {', '.join(sorted(connected_ports))}"
                )
            self.database.update(record["id"], data)
            self.reload()
            self.editor_buffer = None
            self._modal_size_key = None
            self._modal_size_locked = None
            self.messages.append(f"Actualizado {record['id']}: {field.label}")
        except (KeyError, OSError, OverflowError, RuntimeError, TypeError, ValueError) as error:
            code = (
                "LANWIRE_PORT_COUNT_UPDATE_FAILED"
                if field.label in {"portCount", "portNaming"}
                else "LANWIRE_ELEMENT_UPDATE_FAILED"
            )
            reported = write_exception(
                error,
                caused="lanwire.tui.editor",
                code=code,
                context={"idf": record["id"], "field": field.label},
            )
            self.editor_buffer = None
            self.messages.append(f"Error [{reported.code}] editando {field.label}: {reported.text}")

    def _delete_selected_port(self) -> None:
        context = self._selected_connector()
        if context is None:
            self.editor_buffer = None
            self.messages.append("Selecciona primero un puerto para eliminar.")
            return
        record, port, connected_wire = context
        if connected_wire:
            self.editor_buffer = None
            self.messages.append(
                f"Desconecta {connected_wire} antes de eliminar {record['id']}.{port}."
            )
            return
        data = deepcopy(record.get("data") or {})
        ports = data.get("ports") or {}
        if port not in ports:
            self.editor_buffer = None
            return
        del ports[port]
        data["ports"] = ports
        try:
            self.database.update(record["id"], data)
            self.reload()
        except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
            reported = write_exception(
                error,
                caused="lanwire.tui.editor",
                code="LANWIRE_PORT_DELETE_FAILED",
                context={"idf": record["id"], "port": port},
            )
            self.editor_buffer = None
            self.messages.append(f"Error [{reported.code}] eliminando {port}: {reported.text}")
            return
        self.modal_selection = min(
            self.modal_selection, len(selectable_ports(self._modal_record())) - 1
        )
        self.modal_focus = "menu"
        self.menu_selection = 0
        self.editor_buffer = None
        self._modal_size_key = None
        self._modal_size_locked = None
        self.messages.append(f"Eliminado puerto {record['id']}.{port}.")

    def _move_modal_selection(self, delta: int) -> None:
        record = self._modal_record()
        if not record:
            return
        ports = selectable_ports(record)
        if ports:
            self.modal_selection = max(-1, min(len(ports) - 1, self.modal_selection + delta))
        else:
            endpoints = cable_endpoints(record)
            if endpoints:
                self.modal_endpoint = max(0, min(len(endpoints) - 1, self.modal_endpoint + delta))

    def _move_cable_endpoint(self, delta: int) -> None:
        record = self._modal_record()
        if record and (record.get("data") or {}).get("type") == "wire":
            self.modal_endpoint = max(0, min(1, self.modal_endpoint + delta))

    def _follow_connection(self) -> None:
        record = self._modal_record()
        if not record:
            return
        ports = selectable_ports(record)
        if (record.get("data") or {}).get("type") == "rack":
            if not ports:
                return
            unit = ports[min(self.modal_selection, len(ports) - 1)]
            target = rack_occupant(record, self.all_records, unit)
            if target is None:
                return
            self.navigation_stack.append((record["id"], self.modal_selection, self.modal_endpoint))
            self.view_id = target["id"]
            self.modal_focus = "view"
            self.modal_selection = 0
            self.modal_endpoint = 0
            self.modal_scroll = 0
            return
        if ports:
            if self.modal_selection < 0:
                self.messages.append("Selecciona un puerto para seguir su conexión.")
                return
            port = ports[min(self.modal_selection, len(ports) - 1)]
            wire_id = wire_for_port(record, self.all_records, port)
            if not wire_id:
                self.messages.append(f"{record['id']}.{port} no tiene cable conectado.")
                return
            self.navigation_stack.append((record["id"], self.modal_selection, self.modal_endpoint))
            wire = next(item for item in self.all_records if item["id"] == wire_id)
            endpoints = cable_sides(wire)
            self.view_id = wire_id
            self.modal_focus = "view"
            source_index = next(
                (
                    index
                    for index, endpoint in enumerate(endpoints)
                    if endpoint
                    and endpoint.get("device") == record["id"]
                    and str(endpoint.get("port")) == port
                ),
                0,
            )
            opposite_index = 1 - source_index
            self.modal_endpoint = (
                opposite_index if endpoints[opposite_index] is not None else source_index
            )
            self.modal_selection = 0
        else:
            endpoints = cable_sides(record)
            endpoint = endpoints[min(self.modal_endpoint, 1)]
            if endpoint is None:
                self.messages.append("Este extremo del cable está libre.")
                return
            target = next(
                (item for item in self.all_records if item["id"] == endpoint["device"]), None
            )
            if target is None:
                return
            self.navigation_stack.append((record["id"], self.modal_selection, self.modal_endpoint))
            target_ports = selectable_ports(target)
            self.view_id = target["id"]
            self.modal_focus = "view"
            self.modal_selection = (
                target_ports.index(str(endpoint["port"]))
                if str(endpoint["port"]) in target_ports
                else 0
            )
            self.modal_endpoint = 0
        self.modal_scroll = 0

    def _disconnect_selected_port(self) -> None:
        record = self._modal_record()
        if not record or not str((record.get("data") or {}).get("type", "")).startswith("device."):
            return
        ports = selectable_ports(record)
        if not ports:
            return
        port = ports[min(self.modal_selection, len(ports) - 1)]
        wire_id = wire_for_port(record, self.all_records, port)
        if wire_id is None:
            return
        wire = next((item for item in self.all_records if item["id"] == wire_id), None)
        if wire is None:
            return
        data = dict(wire.get("data") or {})
        data["endpoints"] = [
            endpoint
            for endpoint in data.get("endpoints", [])
            if not (endpoint.get("device") == record["id"] and str(endpoint.get("port")) == port)
        ]
        self.database.update(wire_id, data)
        self.reload()
        self._modal_size_key = None
        self._modal_size_locked = None
        self.messages.append(f"Desconectado {wire_id} de {record['id']}.{port}")

    def _navigate_back(self) -> None:
        if not self.navigation_stack:
            return
        self.view_id, self.modal_selection, self.modal_endpoint = self.navigation_stack.pop()
        self.modal_focus = "view"
        self.editor_buffer = None
        self.modal_scroll = 0

    def run(self) -> int:
        if not getattr(self.stream, "isatty", lambda: False)():
            raise RuntimeError("la TUI requiere una terminal interactiva")
        just_fix_windows_console()
        self.stream.write(ENTER_SCREEN)
        self.stream.flush()
        try:
            self.render()
            while self.running:
                key = read_key(0.1)
                size_changed = self.dimensions() != self._last_size
                if key is not None:
                    self.handle_key(key)
                if key is not None or size_changed:
                    self.render()
            return 0
        finally:
            self.stream.write(LEAVE_SCREEN)
            self.stream.flush()


def run_tui(database_path: str | Path = DEFAULT_DATABASE_PATH) -> int:
    return LanwireTui(database_path).run()


# Alias histórico conservado para plugins e importaciones existentes.
LanwreTui = LanwireTui
