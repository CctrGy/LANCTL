"""TUI de pantalla completa de LANWIRE."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from colorama import just_fix_windows_console
from rich.text import Text

from lanctl.apps.wire.cli.commands import CommandProcessor
from lanctl.apps.wire.idf.database import DEFAULT_DATABASE_PATH, IDFDatabaseManager
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
    actions_view,
    connector_actions,
    editable_fields,
    editor_view,
    set_field,
)
from lanctl.apps.wire.tui.keyboard import read_key
from lanctl.apps.wire.tui.renderer import RichTuiRenderer, footer_bar

ENTER_SCREEN = "\x1b[?1049h\x1b[?7l\x1b[2J\x1b[H"
LEAVE_SCREEN = "\x1b[?25h\x1b[?7h\x1b[?1049l"


class LanwireTui:
    def __init__(self, database_path: str | Path = DEFAULT_DATABASE_PATH, stream=None) -> None:
        self.stream = stream or sys.stdout
        self.renderer = RichTuiRenderer(self.stream)
        self.database = IDFDatabaseManager(database_path)
        self.commands = CommandProcessor(self.database)
        self.all_records: list[dict] = []
        self.records: list[dict] = []
        self.list_prefix: str | None = None
        self.view_id: str | None = None
        self.modal_scroll = 0
        self.modal_selection = 0
        self.modal_endpoint = 0
        self._modal_size_key: tuple[str, int, int] | None = None
        self._modal_size_locked: tuple[int, int] | None = None
        self.modal_focus = "view"
        self.editor_selection = 0
        self.editor_buffer: str | None = None
        self.action_selection = 0
        self.action_buffer: str | None = None
        self.navigation_stack: list[tuple[str, int, int]] = []
        self.selected_index = 0
        self.tree_scroll = 0
        self.messages = ["LANWIRE preparado. Escribe 'help' para ver los comandos."]
        self.cli_scroll = 0
        self.command = ""
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
            if self.list_prefix is None or record["prefix"] == self.list_prefix
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

    @staticmethod
    def dimensions() -> tuple[int, int]:
        size = shutil.get_terminal_size(fallback=(120, 30))
        return max(40, size.columns), max(14, size.lines)

    @staticmethod
    def panel_heights(height: int) -> tuple[int, int]:
        usable = max(12, height - 1)
        # La consola recibe dos filas adicionales tomadas de INFO para que el
        # historial y el prompt tengan algo más de espacio vertical.
        lower = max(8, min(14, round(usable / 3) + 2))
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
        idf_width = 10
        type_width = min(20, max(10, table_width // 6))
        name_width = min(24, max(12, table_width // 5))
        description_width = max(10, table_width - idf_width - type_width - name_width - 9)
        header = (
            margin
            + f"{'IDF':<{idf_width}} | {'type':<{type_width}} | {'name':<{name_width}} | {'description':<{description_width}}"
        )
        divider = (
            margin
            + f"{'-' * idf_width}-+-{'-' * type_width}-+-{'-' * name_width}-+-{'-' * description_width}"
        )
        text = Text(header + "\n", style="bold bright_cyan")
        text.append(divider, style="bright_black")
        if not self.records:
            text.append("\n(sin registros para este filtro)", style="dim")
            return text
        visible = self.records[self.tree_scroll : self.tree_scroll + rows]
        for offset, record in enumerate(visible):
            index = self.tree_scroll + offset
            data = record.get("data") or {}
            definition = self.database.get_prefix(record["prefix"])
            element_type = definition["name"] if definition else data.get("type", "element")
            name = data.get("name") or data.get("alias") or ""
            description = data.get("description") or (
                definition.get("description", "") if definition else ""
            )
            line = (
                margin
                + f"{record['id']:<{idf_width}} | {str(element_type)[:type_width]:<{type_width}} | {str(name)[:name_width]:<{name_width}} | {str(description)[:description_width]:<{description_width}}"
            )
            text.append("\n")
            text.append(
                line, style="bold black on bright_cyan" if index == self.selected_index else "white"
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
        self._cli_prompt_line = len(visible) + 1
        text.append("lanwire> ", style="bold green")
        text.append(self.command, style="bright_white")
        return text

    def render(self) -> None:
        width, height = self.dimensions()
        upper_height, lower_height = self.panel_heights(height)
        detail_record = next(
            (record for record in self.all_records if record["id"] == self.view_id), None
        )
        upper = self.tree_view(upper_height - 1, width)
        modal = None
        modal_size = None
        if detail_record:
            modal_title = self._modal_title(detail_record)
            ports = selectable_ports(detail_record)
            selected_port = ports[min(self.modal_selection, len(ports) - 1)] if ports else None
            detail = element_detail(
                detail_record,
                self.all_records,
                max(20, width - 30),
                selected_port=selected_port,
                selected_endpoint=self.modal_endpoint,
            )
            fields = editable_fields(detail_record, selected_port, self.modal_endpoint)
            self.editor_selection = min(self.editor_selection, max(0, len(fields) - 1))
            is_device = str((detail_record.get("data") or {}).get("type", "")).startswith("device.")
            is_wire = (detail_record.get("data") or {}).get("type") == "wire"
            connected_wire = (
                wire_for_port(detail_record, self.all_records, selected_port)
                if selected_port and is_device
                else None
            )
            if self.modal_focus == "editor":
                sidebar = editor_view(fields, self.editor_selection, self.editor_buffer)
            elif self.modal_focus == "actions" and selected_port is not None and is_device:
                actions = connector_actions(connected_wire)
                self.action_selection = min(self.action_selection, len(actions) - 1)
                sidebar = actions_view(actions, self.action_selection, self.action_buffer)
            elif self.modal_focus == "actions" and is_wire:
                connected = cable_sides(detail_record)[min(self.modal_endpoint, 1)] is not None
                sidebar = actions_view(
                    ["Desconectar"] if connected else ["Conectar"], 0, self.action_buffer
                )
            else:
                sidebar = element_sidebar(
                    detail_record,
                    self.all_records,
                    selected_port=selected_port,
                    selected_endpoint=self.modal_endpoint,
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
        prompt_column = min(width, len("lanwire> ") + len(self.command) + 1)
        modal_title = self._modal_title(detail_record) if detail_record else "INFO"
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
        )
        self._last_size = (width, height)

    @staticmethod
    def _modal_title(record: dict) -> str:
        alias = (record.get("data") or {}).get("alias")
        return record["id"] + (f" · {alias}" if alias else "")

    def _fixed_modal_size(
        self, record: dict, width: int, height: int, title: str
    ) -> tuple[int, int]:
        """Calcula una vez el mayor contenido posible de la ventana actual."""
        key = (record["id"], width, height)
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
            sizes.append(self.renderer.modal_size(content, title, width, height))
            edit = editor_view(editable_fields(record, selected_port, selected_endpoint), 0)
            edit_content = combine_with_sidebar(detail, edit, max(20, width - 10))
            sizes.append(self.renderer.modal_size(edit_content, title, width, height))
            if selected_port is not None:
                for connected in (None, "XX-00"):
                    action_content = combine_with_sidebar(
                        detail, actions_view(connector_actions(connected), 0), max(20, width - 10)
                    )
                    sizes.append(self.renderer.modal_size(action_content, title, width, height))
        self._modal_size_key = key
        self._modal_size_locked = (max(size[0] for size in sizes), max(size[1] for size in sizes))
        return self._modal_size_locked

    def execute(self) -> None:
        command = self.command.strip()
        self.command = ""
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
            label = result.list_prefix or "todos"
            self.messages.append(f"Lista activa: {label}")
        else:
            for block in result.lines:
                self.messages.extend(block.splitlines() or [""])
        if command.split()[0].casefold() in ("list", "ls"):
            self.list_prefix = result.list_prefix
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
        if result.refresh:
            self.reload()
        if result.exit_requested:
            self.running = False
        self.cli_scroll = 0

    def handle_key(self, key: str) -> None:
        if self.view_id and self.modal_focus == "editor":
            if key == "TAB":
                self.modal_focus = "actions"
                self.editor_buffer = None
                self.action_selection = 0
                self.action_buffer = None
            elif key == "F2":
                self.view_id = None
                self.navigation_stack.clear()
                self.editor_buffer = None
            elif key == "ESC" and self.editor_buffer is not None:
                self.editor_buffer = None
            elif key == "ESC":
                self.view_id = None
                self.navigation_stack.clear()
            elif key in ("UP", "DOWN") and self.editor_buffer is None:
                self._move_editor_selection(-1 if key == "UP" else 1)
            elif key == "ENTER":
                self._edit_or_save_field()
            elif key == "BACKSPACE" and self.editor_buffer is not None:
                self.editor_buffer = self.editor_buffer[:-1]
            elif self.editor_buffer is not None and len(key) == 1 and key.isprintable():
                self.editor_buffer += key
            return
        if self.view_id and self.modal_focus == "actions":
            if key == "TAB":
                self.modal_focus = "view"
                self.action_buffer = None
            elif key == "F2":
                self.view_id = None
                self.navigation_stack.clear()
                self.action_buffer = None
            elif key == "ESC" and self.action_buffer is not None:
                self.action_buffer = None
            elif key == "ESC":
                self.view_id = None
                self.navigation_stack.clear()
            elif key in ("UP", "DOWN") and self.action_buffer is None:
                self._move_action_selection(-1 if key == "UP" else 1)
            elif key == "ENTER":
                self._execute_connector_action()
            elif key == "BACKSPACE" and self.action_buffer is not None:
                self.action_buffer = self.action_buffer[:-1]
            elif self.action_buffer is not None and len(key) == 1 and key.isprintable():
                self.action_buffer += key
            return
        if key in ("ESC", "F2") and self.view_id:
            self.view_id = None
            self.navigation_stack.clear()
        elif key == "TAB" and self.view_id:
            self.modal_focus = "editor"
            self.editor_selection = 0
            self.editor_buffer = None
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
            self.command = self.command[:-1]
        elif key == "UP" and not self.command:
            self.selected_index = max(0, self.selected_index - 1)
        elif key == "DOWN" and not self.command:
            self.selected_index = min(max(0, len(self.records) - 1), self.selected_index + 1)
        elif key == "PGUP":
            self.cli_scroll += 1
        elif key == "PGDN":
            self.cli_scroll = max(0, self.cli_scroll - 1)
        elif len(key) == 1 and key.isprintable():
            self.command += key

    def _modal_record(self):
        return next((record for record in self.all_records if record["id"] == self.view_id), None)

    def _move_editor_selection(self, delta: int) -> None:
        record = self._modal_record()
        if not record:
            return
        ports = selectable_ports(record)
        selected_port = ports[min(self.modal_selection, len(ports) - 1)] if ports else None
        fields = editable_fields(record, selected_port, self.modal_endpoint)
        self.editor_selection = max(0, min(len(fields) - 1, self.editor_selection + delta))

    def _selected_connector(self) -> tuple[dict, str, str | None] | None:
        record = self._modal_record()
        if not record or not str((record.get("data") or {}).get("type", "")).startswith("device."):
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
        if action == "Desconectar":
            self._disconnect_selected_port()
            self.action_selection = 0
            return
        if self.action_buffer is None:
            self.action_buffer = ""
            return
        target = self.action_buffer.strip().upper()
        try:
            if action == "Conectar":
                self._connect_selected_port(record, port, target)
            elif action == "Mover":
                self._move_selected_connection(record, port, wire_id, target)
            self.action_buffer = None
            self.action_selection = 0
        except (KeyError, TypeError, ValueError) as error:
            self.messages.append(f"No se pudo {action.casefold()}: {error}")

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
            self.action_buffer = ""
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
            if port_data.get("kind") != data.get("kind"):
                raise ValueError("el medio del cable no es compatible con el puerto")
            endpoints = list(data.get("endpoints", []))
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
        if port_data.get("kind") != data.get("kind"):
            raise ValueError("el medio del cable no es compatible con el puerto")
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
        if ports[target_port].get("kind") != data.get("kind"):
            raise ValueError("el puerto de destino usa otro medio")
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
        ports = selectable_ports(record)
        selected_port = ports[min(self.modal_selection, len(ports) - 1)] if ports else None
        fields = editable_fields(record, selected_port, self.modal_endpoint)
        if not fields:
            return
        self.editor_selection = min(self.editor_selection, len(fields) - 1)
        field = fields[self.editor_selection]
        if self.editor_buffer is None:
            self.editor_buffer = field.shown_value
            return
        try:
            data = dict(record.get("data") or {})
            set_field(data, field, self.editor_buffer)
            self.database.update(record["id"], data)
            self.reload()
            self.editor_buffer = None
            self._modal_size_key = None
            self._modal_size_locked = None
            self.messages.append(f"Actualizado {record['id']}: {field.label}")
        except (TypeError, ValueError) as error:
            self.messages.append(f"Error editando {field.label}: {error}")

    def _move_modal_selection(self, delta: int) -> None:
        record = self._modal_record()
        if not record:
            return
        ports = selectable_ports(record)
        if ports:
            self.modal_selection = max(0, min(len(ports) - 1, self.modal_selection + delta))
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
            port = ports[min(self.modal_selection, len(ports) - 1)]
            wire_id = wire_for_port(record, self.all_records, port)
            if not wire_id:
                return
            self.navigation_stack.append((record["id"], self.modal_selection, self.modal_endpoint))
            wire = next(item for item in self.all_records if item["id"] == wire_id)
            endpoints = cable_sides(wire)
            self.view_id = wire_id
            self.modal_focus = "view"
            self.modal_endpoint = next(
                (
                    index
                    for index, endpoint in enumerate(endpoints)
                    if endpoint
                    and endpoint.get("device") == record["id"]
                    and str(endpoint.get("port")) == port
                ),
                0,
            )
            self.modal_selection = 0
        else:
            endpoints = cable_sides(record)
            endpoint = endpoints[min(self.modal_endpoint, 1)]
            if endpoint is None:
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
