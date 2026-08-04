from __future__ import annotations

import io
import ipaddress
import json
import os
import re
import shlex
import shutil
import sys
import textwrap
import time
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime

from colorama import Back, Fore, Style, just_fix_windows_console

from app import __version__
from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.core.layout import fit_text, shrink_widths, terminal_columns
from app.core.output import (
    CNF_COLORS, DARK_CNF_COLORS, DARK_FIELD_COLORS, FIELD_COLORS,
)
from app.services.lan_scanner import local_ipv4


RESET = Style.RESET_ALL
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
CONTROL_CHARACTER = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TUI_ENTER_SCREEN = "\x1b[?1049h\x1b[?7l\x1b[2J\x1b[H"
TUI_LEAVE_SCREEN = "\x1b[?25h\x1b[?7h\x1b[?1049l"

TUI_ELEMENT_HELP = (
    "ELEMENT · gestión simplificada dentro del TUI",
    "  element                         Muestra el elemento seleccionado",
    "  element OBJETIVO                Selecciona por IP, MAC o alias",
    "  element -add MAC [opciones]     Añade un elemento",
    "  element -name TEXTO             Cambia el nombre",
    "  element -alias TEXTO            Cambia el alias",
    "  element -description TEXTO      Cambia la descripción",
    "  element -group GRUPO            Añade al grupo",
    "  element -cnf O|X|-|S|F          F fija la selección en el TUI",
    "  element -delete                 Elimina tras confirmación",
    "Puedes escribir OBJETIVO antes de cualquier opción para no usar la fila resaltada.",
    "Usa ←/→ para elegir una opción y completa sus argumentos en el prompt.",
)

# La cadena insertada evita copiar los marcadores descriptivos (OBJETIVO,
# TEXTO, etc.) como si fueran argumentos reales.
TUI_ELEMENT_SUGGESTIONS = (
    (1, "element "),
    (2, "element "),
    (3, "element -add "),
    (4, "element -name "),
    (5, "element -alias "),
    (6, "element -description "),
    (7, "element -group "),
    (8, "element -cnf "),
    (9, "element -delete"),
)


class LanctlTui:
    """TUI de pantalla completa basada en el inventario persistente de LANCTL."""

    def __init__(self) -> None:
        config = load_config()
        self.screen = sys.stdout
        self.database = DeviceDatabase(config["database"])
        self.dhcp_range = config.get("dhcpRange")
        self.local_ip = str(local_ipv4())
        self.all_devices = []
        self.devices = []
        self.list_filter = ("all", "")
        self.index = 0
        self.scroll = 0
        self.command = ""
        self.cursor = 0
        self.messages = ["F5 actualiza la red. Escribe un comando y pulsa Enter."]
        self.output_focus = False
        self.output_index = 0
        self.output_scroll = 0
        self.output_selectable: list[int] = []
        self.command_suggestions: list[tuple[int, str]] = []
        self.suggestion_index = -1
        self.pending_confirmation: list[str] | None = None
        self.active_devices: set[str] = set()
        self.response_ms: dict[str, float] = {}
        self.running = True
        self.scanning = False
        self.spinner_index = 0
        self.scan_current = 0
        self.scan_total = 0
        self.scan_visible_devices: set[str] = set()
        self.scan_summary: dict[str, object] = {}
        self.detail_lines: list[str] = []
        self.detail_scroll = 0
        self.view_state = "inventory"
        self.history_events = []
        self.history_index = 0
        self.command_history: list[str] = []
        self.command_history_index = 0
        self.command_history_scroll = 0
        self.reload()

    @property
    def selected(self):
        return self.devices[self.index] if self.devices else None

    def reload(self) -> None:
        identity = self.selected.mac if self.selected else ""
        self.all_devices = self.database.load()
        self.devices = self._filtered_devices()
        if identity:
            self.index = next(
                (i for i, device in enumerate(self.devices) if device.mac == identity),
                min(self.index, max(0, len(self.devices) - 1)),
            )
        else:
            self.index = min(self.index, max(0, len(self.devices) - 1))
        self.scroll = min(self.scroll, max(0, len(self.devices) - 1))

    def _filtered_devices(self):
        mode, value = self.list_filter
        source = self.all_devices
        if self.scanning:
            source = [
                device for device in source
                if _device_key(device.mac, device.ip) in self.scan_visible_devices
            ]
        if mode == "connected":
            return [device for device in source if _device_key(device.mac, device.ip) in self.active_devices]
        if mode == "disconnected":
            return [device for device in source if _device_key(device.mac, device.ip) not in self.active_devices]
        if mode == "group":
            return [device for device in source if value.upper() in device.groups]
        if mode in ("dhcp", "statics"):
            in_dhcp = lambda device: _ip_in_range(device.ip, self.dhcp_range)
            return [device for device in source if in_dhcp(device) == (mode == "dhcp")]
        return list(source)

    def configure_list(self, parts: list[str]) -> bool:
        try:
            self.list_filter = _parse_list_filter(parts)
        except ValueError as error:
            self.messages = [str(error)]
            return False
        self.index = 0
        self.scroll = 0
        self.reload()
        mode, value = self.list_filter
        label = f"{mode}:{value}" if value else mode
        self.messages = [f"Filtro de lista: {label} | {len(self.devices)} elementos"]
        return True

    def move(self, delta: int) -> None:
        if self.selected and self.selected.cnf == "F":
            label = self.selected.alias or self.selected.name or self.selected.ip
            self.messages = [
                f"Selección fijada en {label}. Usa 'cnf' o 'cnf ESTADO' para liberarla."
            ]
            return
        if self.devices:
            self.index = max(0, min(len(self.devices) - 1, self.index + delta))

    def _dimensions(self) -> tuple[int, int]:
        size = shutil.get_terminal_size(fallback=(120, 30))
        return terminal_columns(self.screen) or size.columns, max(12, size.lines)

    def _inventory_lines(self, width: int, height: int) -> list[str]:
        first_dhcp, last_dhcp = _dhcp_boundary_indexes(
            self.devices, self.dhcp_range
        )
        # Reserva espacio para delimitar el bloque DHCP sin desplazar el panel.
        reserved = (2 if first_dhcp is not None else 0) + (1 if self.scan_total else 0)
        rows = max(1, height - reserved)
        if self.index < self.scroll:
            self.scroll = self.index
        elif self.index >= self.scroll + rows:
            self.scroll = self.index - rows + 1
        self.scroll = max(0, min(self.scroll, max(0, len(self.devices) - rows)))

        fields = ["IP", "responseMs", "cnf", "ALIAS", "MAC", "NAME", "GROUP", "description"]
        if width >= 135:
            fields.extend(("discoveryMethods", "lastSeen"))
        if width >= 170:
            fields.append("manufacturer")
        if width >= 205:
            fields.append("protocols")
        fields = tuple(fields)
        labels = {
            "IP": "IP", "responseMs": "ms", "cnf": "cnf", "ALIAS": "ALIAS",
            "MAC": "MAC", "NAME": "NAME", "GROUP": "GROUP",
            "description": "DESCRIPTION",
            "discoveryMethods": "DETECTION", "lastSeen": "LAST SEEN",
            "manufacturer": "MANUFACTURER", "protocols": "PROTOCOLS",
        }
        widths = {
            "IP": 15, "responseMs": 6, "cnf": 3, "ALIAS": 13,
            "MAC": 17, "NAME": 15, "GROUP": 8, "description": 42,
            "discoveryMethods": 16, "lastSeen": 19,
            "manufacturer": 18, "protocols": 12,
        }
        widths = {field: widths[field] for field in fields}
        gap = 1 if width < 100 else 2
        widths, too_narrow = shrink_widths(
            widths,
            {"IP": 7, "responseMs": 4, "cnf": 3, "ALIAS": 4, "MAC": 8,
             "NAME": 4, "GROUP": 4, "description": 4,
             "discoveryMethods": 8, "lastSeen": 12,
             "manufacturer": 8, "protocols": 7},
            fields, max(20, width - 2),
            ("description", "manufacturer", "NAME", "ALIAS", "GROUP",
             "lastSeen", "discoveryMethods", "protocols", "MAC", "IP", "responseMs"),
            gap=gap,
        )
        if too_narrow:
            gap = 1
            widths, _ = shrink_widths(
                widths,
                {field: 1 for field in fields},
                fields, max(20, width - 2),
                ("description", "manufacturer", "lastSeen", "discoveryMethods",
                 "protocols", "NAME", "ALIAS", "GROUP", "MAC", "IP",
                 "responseMs", "cnf"),
                gap=gap,
            )
        _expand_tui_widths(widths, fields, width - 2, gap)

        def header_cell(field: str) -> str:
            value = fit_text(labels[field], widths[field])
            if field == "responseMs":
                value = value.rjust(widths[field])
            else:
                value = value.ljust(widths[field])
            return f"{Style.BRIGHT}{Fore.CYAN}{value}{RESET}"

        joiner = " " * gap
        header = "  " + joiner.join(header_cell(field) for field in fields)
        separator = "  " + joiner.join("─" * widths[field] for field in fields)
        output = [header, f"{Style.DIM}{Fore.CYAN}{separator}{RESET}"]
        dhcp_separator = "  " + "-" * max(5, width - 2)
        visible = self.devices[self.scroll:self.scroll + rows]
        for offset, device in enumerate(visible):
            absolute = self.scroll + offset
            if absolute == first_dhcp:
                output.append(f"{Style.DIM}{Fore.YELLOW}{dhcp_separator}{RESET}")
            active = _device_key(device.mac, device.ip) in self.active_devices
            selected = absolute == self.index and not self.output_focus
            ms = self.response_ms.get(device.mac or device.ip)
            values = {
                "IP": device.ip or "-",
                "responseMs": "-" if ms is None else f"{ms:.1f}",
                "cnf": "@" if device.ip == self.local_ip else device.cnf,
                "ALIAS": device.alias or "-",
                "MAC": device.mac or "-",
                "NAME": device.name or "-",
                "GROUP": ",".join(device.groups) or "-",
                "description": device.description or "-",
                "discoveryMethods": "+".join(device.discovery_methods) or device.last_discovery or "-",
                "lastSeen": _compact_timestamp(device.last_seen),
                "manufacturer": device.manufacturer or "-",
                "protocols": ",".join(device.protocols) or "-",
            }

            def body_cell(field: str) -> str:
                value = fit_text(values[field], widths[field])
                value = (
                    value.rjust(widths[field]) if field == "responseMs"
                    else value.center(widths[field]) if field == "cnf"
                    else value.ljust(widths[field])
                )
                palette = FIELD_COLORS if active else DARK_FIELD_COLORS
                color = palette[field]
                if field == "cnf":
                    color = (CNF_COLORS if active else DARK_CNF_COLORS).get(values[field], color)
                intensity = Style.BRIGHT if active else Style.DIM
                background = Back.LIGHTBLACK_EX if selected else ""
                return f"{background}{intensity}{color}{value}{RESET}"

            marker = f"{Style.BRIGHT}{Fore.WHITE}{'▶' if selected else ' '}{RESET} "
            output.append(marker + joiner.join(body_cell(field) for field in fields))
            if absolute == last_dhcp:
                output.append(f"{Style.DIM}{Fore.YELLOW}{dhcp_separator}{RESET}")
        if self.scan_total:
            output.append(self._progress_line(width))
        while len(output) < height + 2:
            output.append("")
        return output

    def _progress_line(self, width: int) -> str:
        ratio = min(1.0, self.scan_current / max(1, self.scan_total))
        bar_width = max(8, min(36, width - 51))
        filled = round(bar_width * ratio)
        bar = "█" * filled + "─" * (bar_width - filled)
        state = "ESCANEO" if self.scanning else "COMPLETADO"
        color = Fore.YELLOW if self.scanning else Fore.GREEN
        line = (
            f"  {state} [{bar}] {ratio:6.1%} "
            f"{self.scan_current}/{self.scan_total} | encontrados {len(self.scan_visible_devices)}"
        )
        return f"{Style.BRIGHT}{color}{fit_text(line, width)}{RESET}"

    def _selection_label(self) -> str:
        device = self.selected
        if not device:
            return "-"
        if device.alias:
            return device.alias
        if _device_key(device.mac, device.ip) in self.active_devices and device.ip:
            return device.ip
        return device.mac or device.ip or "-"

    def _status_lines(self, width: int) -> list[str]:
        if self.scanning:
            return [
                f"{Style.BRIGHT}{Fore.YELLOW} ESCANEANDO {RESET} "
                f"{Fore.WHITE}Elementos encontrados: {len(self.scan_visible_devices)}{RESET}",
                f"{Fore.LIGHTBLACK_EX}La lista se completa en tiempo real.{RESET}",
            ]
        summary = self.scan_summary
        if not summary:
            return [
                f"{Style.BRIGHT}{Fore.CYAN} RED {RESET} Sin escaneo en esta sesión",
                f"{Fore.LIGHTBLACK_EX}Pulsa F5 para actualizar.{RESET}",
            ]
        return [
            f"{Style.BRIGHT}{Fore.CYAN} PERFIL {RESET} {Fore.WHITE}{summary['profile']}{RESET}  "
            f"{Style.BRIGHT}{Fore.CYAN} MÉTODO {RESET} {Fore.WHITE}{summary['discovery']}{RESET}  "
            f"{Style.BRIGHT}{Fore.GREEN} ACTIVOS {RESET} {summary['active']}/{summary['total']}",
            f"{Style.BRIGHT}{Fore.LIGHTBLUE_EX} ICMP {RESET} {summary['icmp']}  "
            f"{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} ARP {RESET} {summary['arp']}  "
            f"{Style.BRIGHT}{Fore.YELLOW} CACHE {RESET} {summary['cache']}  "
            f"{Style.BRIGHT}{Fore.CYAN} MOSTRADOS {RESET} {summary['shown']}",
        ]

    def render(self) -> None:
        width, height = self._dimensions()
        width = max(20, width)
        if self.detail_lines:
            self._render_detail(width, height)
            return
        compact = height < 20 or width < 70
        message_rows = 11 if not compact else 6
        list_height = max(3, height - message_rows - 8)
        title = f" LANCTL TUI {__version__} "
        mode, value = self.list_filter
        filter_name = f"{mode}:{value}" if value else mode
        if self.view_state == "history":
            counter = f" [history] {self.history_index + 1 if self.history_events else 0}/{len(self.history_events)} "
        elif self.view_state == "command-history":
            counter = f" [commands] {self.command_history_index + 1 if self.command_history else 0}/{len(self.command_history)} "
        else:
            counter = f" [{filter_name}] {self.index + 1 if self.devices else 0}/{len(self.devices)} "
        title_space = max(0, width - len(title) - len(counter))
        title_content = (
            f"{title}{'─' * title_space}{counter}"
            if len(title) + len(counter) <= width
            else fit_text(f"{title}{counter}", width)
        )
        lines = [
            f"{Style.BRIGHT}{Fore.CYAN}{title_content}{RESET}",
            *(
                self._history_lines(width, list_height)
                if self.view_state == "history"
                else self._command_history_lines(width, list_height)
                if self.view_state == "command-history"
                else self._inventory_lines(width, list_height)
            ),
            f"{Fore.CYAN}{'─' * width}{RESET}",
            *(_fit_ansi(line, width) for line in self._status_lines(width)),
        ]
        if self.output_focus and self.output_selectable:
            selected_line = self.output_selectable[self.output_index]
            if selected_line < self.output_scroll:
                self.output_scroll = selected_line
            elif selected_line >= self.output_scroll + message_rows:
                self.output_scroll = selected_line - message_rows + 1
            visible_output = self.messages[
                self.output_scroll:self.output_scroll + message_rows
            ]
            for offset, message in enumerate(visible_output):
                absolute = self.output_scroll + offset
                selected = absolute == selected_line
                marker = "▶ " if selected else "  "
                background = Back.LIGHTBLACK_EX if selected else ""
                intensity = Style.BRIGHT if selected else ""
                lines.append(
                    f"{background}{intensity}{Fore.WHITE}"
                    f"{fit_text(marker + message, width)}{RESET}"
                )
        elif self.command_suggestions:
            selected_line = (
                self.command_suggestions[self.suggestion_index][0]
                if self.suggestion_index >= 0 else -1
            )
            start = 0
            if selected_line >= message_rows:
                start = selected_line - message_rows + 1
            start = min(start, max(0, len(self.messages) - message_rows))
            wrapped = []
            for absolute in range(start, min(len(self.messages), start + message_rows)):
                message = self.messages[absolute]
                selected = absolute == selected_line
                marker = "▶ " if selected else "  "
                background = Back.LIGHTBLACK_EX if selected else ""
                intensity = Style.BRIGHT if selected else ""
                wrapped.append(
                    f"{background}{intensity}{Fore.WHITE}"
                    f"{fit_text(marker + message, width)}{RESET}"
                )
            lines.extend(wrapped[-message_rows:])
        else:
            wrapped: list[str] = []
            for message in self.messages[-12:]:
                wrapped.extend(textwrap.wrap(message, width=max(1, width - 2)) or [""])
            for message in wrapped[-message_rows:]:
                lines.append(f" {fit_text(message, width - 1)}")
        while len(lines) < height - 2:
            lines.append("")
        prompt_label = (
            _spinner_character(self.spinner_index) if self.scanning
            else "CONFIRM" if self.pending_confirmation else self._selection_label()
        )
        prompt_prefix = f"LANCTL[{prompt_label}]> "
        prompt_text = fit_text(f"{prompt_prefix}{self.command}", width)
        lines.append(f"{Fore.LIGHTGREEN_EX}{prompt_text}{RESET}")
        keys = _function_bar(width)
        lines.append(keys)
        cursor_column = min(width, len(prompt_prefix) + self.cursor + 1)
        self.screen.write(
            "\x1b[?25h\x1b[2J\x1b[H" + "\n".join(lines[:height])
            + f"\x1b[{height - 1};{cursor_column}H"
        )
        self.screen.flush()

    def show_history(self, selector: str | None = None) -> None:
        from app.core.history import HistoryService
        target = selector or ((self.selected.device_id or self.selected.mac or self.selected.ip) if self.selected else None)
        try:
            self.history_events = HistoryService().query(None if target == "all" else target, limit=1000, reverse=True)
            self.history_index = 0; self.view_state = "history"
            self.messages = [f"Historial: {len(self.history_events)} eventos | Enter detalle | Esc inventario"]
        except ValueError as error: self.messages = [str(error)]

    def show_command_history(self) -> None:
        self.view_state = "command-history"
        self.command_history_index = max(0, len(self.command_history) - 1)
        self.command_history_scroll = max(0, self.command_history_index)
        self.messages = [
            f"Historial de comandos: {len(self.command_history)} | "
            "Flechas seleccionan | Enter recupera | Esc inventario"
        ]

    def _command_history_lines(self, width: int, height: int) -> list[str]:
        if not self.command_history:
            return [" Sin comandos en esta sesion"]
        height = max(1, height)
        if self.command_history_index < self.command_history_scroll:
            self.command_history_scroll = self.command_history_index
        elif self.command_history_index >= self.command_history_scroll + height:
            self.command_history_scroll = self.command_history_index - height + 1
        maximum = max(0, len(self.command_history) - height)
        self.command_history_scroll = max(0, min(self.command_history_scroll, maximum))
        rows = []
        end = min(len(self.command_history), self.command_history_scroll + height)
        for index in range(self.command_history_scroll, end):
            marker = "▶" if index == self.command_history_index else " "
            rows.append(f"{marker} {index + 1:>4} | {self.command_history[index]}")
        return [fit_text(row, width) for row in rows]

    def _history_lines(self, width: int, height: int) -> list[str]:
        rows=[]
        for index,event in enumerate(self.history_events[:height]):
            marker="▶" if index==self.history_index else " "
            label=event.device.label if event.device else "LAN"
            rows.append(f"{marker} {event.timestamp[:19]} | {label} | {event.type} | {event.summary}")
        return [fit_text(line,width) for line in rows] or [" Sin eventos"]

    def show_history_detail(self) -> None:
        if not self.history_events: return
        event=self.history_events[self.history_index]; device=event.device
        self.detail_lines=[f"Tipo: {event.type}",f"Fecha: {event.timestamp}",f"Elemento: {device.label if device else '-'}",f"Source: {event.source}",f"Resultado: {event.result}",f"CorrelationId: {event.correlationId or '-'}",f"RunId: {event.runId or '-'}",f"TaskId: {event.taskId or '-'}",f"OperationId: {event.operationId or '-'}",f"Resumen: {event.summary}","Cambios:",* [f"  {x.get('field')}: {x.get('before')} => {x.get('after')}" for x in event.changes]]
        if event.error:self.detail_lines.extend((f"Error: {event.error.get('code','-')}",f"Origen: {event.error.get('origin','-')}",f"Mensaje: {event.error.get('message','-')}"))

    def _render_detail(self, width: int, height: int) -> None:
        rows = max(1, height - 4)
        maximum = max(0, len(self.detail_lines) - rows)
        self.detail_scroll = max(0, min(self.detail_scroll, maximum))
        visible = self.detail_lines[self.detail_scroll:self.detail_scroll + rows]
        title = " INFORMACION COMPLETA DEL ELEMENTO "
        lines = [f"{Style.BRIGHT}{Fore.CYAN}{fit_text(title + '-' * width, width)}{RESET}"]
        lines.extend(f" {fit_text(line, width - 1)}" for line in visible)
        while len(lines) < height - 2:
            lines.append("")
        position = (
            f"Lineas {self.detail_scroll + 1}-"
            f"{min(len(self.detail_lines), self.detail_scroll + rows)}"
            f"/{len(self.detail_lines)}"
        )
        lines.append(f"{Fore.CYAN}{fit_text(position, width)}{RESET}")
        footer = " Flechas/RePag/AvPag  Desplazar    F2/Esc  Volver "
        lines.append(f"{Style.BRIGHT}{Back.WHITE}{Fore.BLACK}{fit_text(footer, width):<{width}}{RESET}")
        self.screen.write("\x1b[?25l\x1b[2J\x1b[H" + "\n".join(lines[:height]))
        self.screen.flush()

    def discovery_found(self, keys: tuple[str, ...]) -> None:
        normalized = {str(key).strip().casefold() for key in keys if key}
        for device in self.all_devices:
            if device.ip.casefold() in normalized or device.mac.casefold() in normalized:
                key = _device_key(device.mac, device.ip)
                self.scan_visible_devices.add(key)
                self.active_devices.add(key)
        self.devices = self._filtered_devices()
        self.index = min(self.index, max(0, len(self.devices) - 1))

    def _capture(self, argv: list[str]) -> tuple[int, str]:
        from app.cli import main
        output = io.StringIO()
        try:
            with redirect_stdout(output), redirect_stderr(output):
                result = main(argv)
        except SystemExit as error:
            result = int(error.code or 0)
        return result, output.getvalue().strip()

    def refresh(self) -> None:
        self.scanning = True
        self.spinner_index = 0
        self.scan_current = 0
        self.scan_total = 0
        self.scan_visible_devices = set()
        self.scan_summary = {}
        self.active_devices = set()
        self.all_devices = self.database.load()
        self.devices = self._filtered_devices()
        self.messages = ["Buscando dispositivos en la LAN…"]
        self.render()
        from app.cli import build_parser
        captured_rows: list[dict] = []
        captured_activity: list[bool] = []
        output_buffer = io.StringIO()
        try:
            args = build_parser().parse_args(["list", "--no-progress"])
            def collect_result(rows, activity) -> None:
                captured_rows.extend(rows)
                captured_activity.extend(activity)
            args.result_callback = collect_result
            args.progress_instance = _TuiScanProgress(self)
            args.scan_summary_callback = self.scan_summary.update
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                result = args.handler(args)
        except (OSError, ValueError, SystemExit) as error:
            result = int(error.code or 1) if isinstance(error, SystemExit) else 1
            output_buffer.write(str(error))
        finally:
            self.scanning = False
            self.scan_current = 0
            self.scan_total = 0
        output = output_buffer.getvalue().strip()
        self.response_ms = {
            str(row.get("MAC") or row.get("IP")): float(row["responseMs"])
            for row in captured_rows if row.get("responseMs") is not None
        }
        self.active_devices = {
            _device_key(str(row.get("MAC", "")), str(row.get("IP", "")))
            for row, active in zip(captured_rows, captured_activity) if active
        }
        self.reload()
        summary = _last_meaningful_line(output)
        self.messages = (
            ["Escaneo completado. Pulsa F5 para actualizar de nuevo."]
            if result == 0 else [summary or "Error al actualizar la LAN."]
        )

    def _show_info_legacy(self) -> None:
        if not self.selected:
            self.messages = ["No hay ningún elemento seleccionado."]
            return
        result, output = self._capture([
            "element", self.selected.mac or self.selected.ip
        ])
        self._set_command_output(output, result)

    def show_info(self) -> None:
        device = self.selected
        if not device:
            self.messages = ["No hay ningun elemento seleccionado."]
            return
        self.messages = ["Obteniendo informacion completa del elemento..."]
        self.render()
        result, output = self._capture([
            "scan", device.mac or device.ip,
            "--identify", "--banners", "--json",
        ])
        try:
            payload = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            self._set_command_output(output, result)
            return
        observation = payload.get("observation", {})
        identification = observation.get("identification", {}) or {}
        match = observation.get("identityMatch")

        def shown(value) -> str:
            return "-" if value in (None, "", [], {}) else str(value)

        self.detail_lines = [
            "IDENTIDAD",
            f"  Estado: {'ACTIVO' if observation.get('reachable') else 'NO DETECTADO'}",
            f"  ID estable: {shown(device.device_id)}",
            f"  CNF: {shown(device.cnf)}",
            f"  IP registrada: {shown(device.ip)}",
            f"  MAC registrada: {shown(device.mac)}",
            f"  MAC observada: {shown(observation.get('observed_mac'))}",
            f"  Coincidencia: {'Si' if match is True else 'NO' if match is False else '-'}",
            "",
            "NOMBRES Y CLASIFICACION",
            f"  Alias: {shown(device.alias)}",
            f"  Alias detectado: {shown(device.default_alias)}",
            f"  Nombre: {shown(device.name)}",
            f"  Hostname detectado: {shown(observation.get('hostname') or device.default_name)}",
            f"  Descripcion: {shown(device.description)}",
            f"  Fabricante: {shown(payload.get('element', {}).get('manufacturer') or device.manufacturer)}",
            f"  Tipo probable: {shown(identification.get('device_type'))}",
            f"  Confianza: {shown(identification.get('confidence'))}",
            f"  Evidencias: {shown('; '.join(identification.get('evidence', [])))}",
            f"  Grupos: {shown(', '.join(device.groups))}",
            "",
            "RED Y DETECCION",
            f"  Latencia: {shown(observation.get('latency_ms'))} ms",
            f"  TTL: {shown(observation.get('ttl'))}",
            f"  Detectado por: {shown('+'.join(device.discovery_methods) or device.last_discovery)}",
            f"  Ultima deteccion: {shown(device.last_discovery)}",
            f"  Ultima vez visto: {shown(device.last_seen)}",
            "",
            "ACCESO Y CONFIGURACION",
            f"  Protocolos: {shown(', '.join(device.protocols))}",
            f"  Credenciales referenciadas: {shown(', '.join(f'{key}={value}' for key, value in device.credentials.items()))}",
            f"  Opciones de protocolo: {shown(json.dumps(device.protocol_options, ensure_ascii=False, sort_keys=True))}",
            "",
            "PUERTOS TCP (CONJUNTO HABITUAL)",
            f"  Puertos abiertos: {len(observation.get('open_ports', []))}",
            f"  Puertos examinados: {shown(observation.get('scanned_ports'))}",
            f"  Duracion del analisis: {shown(observation.get('duration'))} s",
        ]
        self.detail_scroll = 0

    def ping_selected(self) -> None:
        device = self.selected
        if not device:
            self.messages = ["No hay ningún elemento seleccionado para comprobar."]
            return
        result, output = self._capture([
            "ping", device.mac or device.ip
        ])
        if result == 0:
            self.active_devices.add(_device_key(device.mac, device.ip))
        self.reload()
        if output:
            self._set_command_output(output, result)
        else:
            self.messages = [
                "Ping completado." if result == 0 else "El elemento no ha respondido."
            ]

    def _set_command_output(self, output: str, result: int) -> None:
        self.messages = _clean_tui_output(output) if output else [f"Código de salida: {result}"]
        self.output_selectable = _selectable_output_indexes(self.messages)
        self.output_focus = bool(self.output_selectable)
        self.output_index = 0
        self.output_scroll = 0

    def _move_output(self, delta: int) -> None:
        if self.output_selectable:
            self.output_index = max(
                0, min(len(self.output_selectable) - 1, self.output_index + delta)
            )

    def _move_suggestion(self, delta: int) -> None:
        suggestions = getattr(self, "command_suggestions", [])
        if not suggestions:
            return
        current = getattr(self, "suggestion_index", -1)
        if current < 0:
            current = 0 if delta > 0 else len(suggestions) - 1
        else:
            current = (current + delta) % len(suggestions)
        self.suggestion_index = current
        self.command = suggestions[current][1]
        self.cursor = len(self.command)

    def _clear_suggestions(self) -> None:
        self.command_suggestions = []
        self.suggestion_index = -1

    def execute(self) -> None:
        raw = self.command.strip()
        self.command = ""
        self.cursor = 0
        if not raw:
            return
        if not hasattr(self, "command_history"):
            self.command_history = []
        if not self.command_history or self.command_history[-1] != raw:
            self.command_history.append(raw)
        if getattr(self, "pending_confirmation", None) is not None:
            answer = raw.casefold()
            if answer in ("s", "si", "sí", "y", "yes"):
                contextual = self.pending_confirmation
                self.pending_confirmation = None
                result, output = self._capture(contextual)
                self.reload()
                self._set_command_output(output, result)
            elif answer in ("n", "no", "cancel", "cancelar"):
                self.pending_confirmation = None
                self.messages = ["Operación cancelada; no se ha eliminado el elemento."]
            else:
                self.messages = ["Confirma escribiendo YES o cancela escribiendo NO."]
            return
        self.output_focus = False
        self.output_selectable = []
        self.output_index = 0
        self.output_scroll = 0
        try:
            parts = shlex.split(raw)
        except ValueError as error:
            self.messages = [str(error)]
            return
        command = parts[0].casefold()
        if command == "element" and any(
            part.casefold() in ("/?", "-h", "--help") for part in parts[1:]
        ):
            self.messages = list(TUI_ELEMENT_HELP)
            self.command_suggestions = list(TUI_ELEMENT_SUGGESTIONS)
            self.suggestion_index = -1
            return
        self._clear_suggestions()
        if command in ("exit", "quit", "salir"):
            self.running = False
            return
        if command in ("clear", "cls"):
            self.messages = []
            return
        if command in ("help", "?", "commands"):
            if len(parts) > 1 and parts[1].casefold() != "list":
                help_result, output = self._capture([parts[1], "/?"])
                self._set_command_output(output or "No hay ayuda disponible.", help_result)
            else:
                self.messages = [
                    "TUI: list --all | --connected | --disconnected | -group NOMBRE | -dhcp | -statics",
                    "Contexto: info, select ELEMENTO, clear, reload; group NOMBRE -add/-remove usa la selección.",
                    "Edición rápida: element -name|-alias|-description|-group|-cnf|-delete. Usa element /? a modo de ayuda.",
                ]
            return
        if command == "reload":
            self.reload()
            self.messages = [
                f"Inventario recargado | {len(self.devices)} elementos | sin escaneo de red."
            ]
            return
        if command == "list":
            if any(
                part.casefold() in ("-recurrent", "--recurrent")
                for part in parts[1:]
            ):
                result, output = self._capture(parts)
                self._set_command_output(output, result)
                return
            if self.configure_list(parts[1:]):
                self.refresh()
            return
        if command == "version":
            self.messages = [f"LANCTL {__version__}"]
            return
        if command in ("info", "selected"):
            self.show_info()
            return
        if command == "history":
            self.show_history(parts[1] if len(parts)>1 else None)
            return
        if command == "select" and len(parts) == 2:
            try:
                wanted = self.database.resolve(parts[1])
                if not any(item.mac == wanted.mac for item in self.devices):
                    self.list_filter = ("all", "")
                    self.reload()
                self.index = next(i for i, item in enumerate(self.devices) if item.mac == wanted.mac)
                self.messages = [f"Seleccionado: {wanted.alias or wanted.ip}"]
            except (ValueError, StopIteration) as error:
                self.messages = [str(error)]
            return
        contextual = list(parts)
        if command == "element":
            try:
                contextual = _translate_tui_element(
                    contextual,
                    (self.selected.mac or self.selected.ip) if self.selected else "",
                )
            except ValueError as error:
                self.messages = [str(error), "Escribe element /? para ver ejemplos."]
                return
            if (
                len(contextual) >= 3
                and contextual[0].casefold() == "element"
                and contextual[2].casefold() in ("delete", "del", "remove")
                and "--yes" not in [part.casefold() for part in contextual]
            ):
                self.pending_confirmation = [*contextual, "--yes"]
                target = contextual[1]
                if self.selected and target in (
                    self.selected.mac, self.selected.ip, self.selected.alias
                ):
                    target = self.selected.alias or self.selected.ip or self.selected.mac
                self.messages = [
                    f"Eliminar completamente {target}?",
                    "Escribe YES para confirmar o NO para cancelar.",
                ]
                return
        if self.selected:
            contextual = _inject_selected_group_element(
                contextual, self.selected.mac or self.selected.ip
            )
        if self.selected and command in {
            "alias", "call", "cnf", "credential", "name", "open",
            "ping", "protocol", "scan", "search", "ssh", "switch", "terminal",
        }:
            contextual.insert(1, self.selected.mac or self.selected.ip)
        result, output = self._capture(contextual)
        self.reload()
        self._set_command_output(output, result)

    def handle_key(self, key: str) -> None:
        if self.detail_lines:
            if key == "UP":
                self.detail_scroll -= 1
            elif key == "DOWN":
                self.detail_scroll += 1
            elif key == "PGUP":
                self.detail_scroll -= 10
            elif key == "PGDN":
                self.detail_scroll += 10
            elif key in ("F2", "ESC"):
                self.detail_lines = []
                self.detail_scroll = 0
            return
        if getattr(self, "view_state", "inventory") == "history":
            if key in ("UP","PGUP"): self.history_index=max(0,self.history_index-(10 if key=="PGUP" else 1))
            elif key in ("DOWN","PGDN"): self.history_index=min(max(0,len(self.history_events)-1),self.history_index+(10 if key=="PGDN" else 1))
            elif key == "ENTER": self.show_history_detail()
            elif key == "F5": self.show_history("all" if self.history_events and not self.history_events[0].device else None)
            elif key == "ESC": self.view_state="inventory"; self.messages=["Inventario restaurado"]
            return
        if getattr(self, "view_state", "inventory") == "command-history":
            if key in ("UP", "PGUP"):
                step = 10 if key == "PGUP" else 1
                self.command_history_index = max(0, self.command_history_index - step)
            elif key in ("DOWN", "PGDN"):
                step = 10 if key == "PGDN" else 1
                self.command_history_index = min(
                    max(0, len(self.command_history) - 1),
                    self.command_history_index + step,
                )
            elif key == "ENTER" and self.command_history:
                self.command = self.command_history[self.command_history_index]
                self.cursor = len(self.command)
                self.view_state = "inventory"
                self.messages = ["Comando recuperado; pulsa Enter para ejecutarlo."]
            elif key == "ESC":
                self.view_state = "inventory"
                self.messages = ["Inventario restaurado"]
            return
        if self.output_focus:
            if key == "UP":
                self._move_output(-1)
                return
            if key == "DOWN":
                self._move_output(1)
                return
            if key == "PGUP":
                self._move_output(-8)
                return
            if key == "PGDN":
                self._move_output(8)
                return
            if key == "ENTER" and not self.command:
                return
            if key == "ESC":
                self.output_focus = False
                self.output_selectable = []
                self.output_index = 0
                self.output_scroll = 0
                return
            self.output_focus = False
        if key in ("LEFT", "RIGHT") and getattr(self, "command_suggestions", []):
            self._move_suggestion(-1 if key == "LEFT" else 1)
            return
        if key == "UP":
            self.move(-1)
        elif key == "DOWN":
            self.move(1)
        elif key == "PGUP":
            self.move(-10)
        elif key == "PGDN":
            self.move(10)
        elif key == "F1":
            self.messages = [
                "F1 ayuda | F2 información | F3 ping | F5 escaneo | Ctrl+H comandos | flechas selección | Esc salir",
                "TUI: reload recarga el inventario sin escanear la red.",
                "Filtros: list --all|--connected|--disconnected|-group NOMBRE|-dhcp|-statics",
            ]
        elif key == "F2":
            self.show_info()
        elif key == "F3":
            self.ping_selected()
        elif key == "F5":
            self.refresh()
        elif key == "CTRL_H":
            self.show_command_history()
        elif key == "ENTER":
            self.execute()
        elif key == "BACKSPACE":
            self._clear_suggestions()
            if self.cursor:
                self.command = self.command[:self.cursor - 1] + self.command[self.cursor:]
                self.cursor -= 1
        elif key == "DELETE":
            self._clear_suggestions()
            self.command = self.command[:self.cursor] + self.command[self.cursor + 1:]
        elif key == "LEFT":
            self.cursor = max(0, self.cursor - 1)
        elif key == "RIGHT":
            self.cursor = min(len(self.command), self.cursor + 1)
        elif key == "HOME":
            self._clear_suggestions()
            self.cursor = 0
        elif key == "END":
            self._clear_suggestions()
            self.cursor = len(self.command)
        elif key == "ESC":
            self.running = False
        elif len(key) == 1 and key.isprintable():
            self._clear_suggestions()
            self.command = self.command[:self.cursor] + key + self.command[self.cursor:]
            self.cursor += 1

    def run(self) -> int:
        if os.name != "nt":
            raise OSError("LANCTL TUI utiliza actualmente la entrada de teclado de Windows")
        just_fix_windows_console()
        from msvcrt import getwch
        try:
            # La pantalla alternativa impide que cada repintado pase al
            # historial de la consola. Desactivar el ajuste automático evita
            # filas fantasma cuando una línea ocupa exactamente todo el ancho.
            self.screen.write(TUI_ENTER_SCREEN)
            self.screen.flush()
            self.refresh()
            while self.running:
                self.render()
                self.handle_key(_read_windows_key(getwch))
        finally:
            self.screen.write(TUI_LEAVE_SCREEN)
            self.screen.flush()
        return 0


def _windows_control_pressed() -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes
        return bool(ctypes.windll.user32.GetKeyState(0x11) & 0x8000)
    except (AttributeError, OSError):
        return False


def _read_windows_key(getwch, control_pressed=None) -> str:
    first = getwch()
    if first in ("\x00", "\xe0"):
        return {
            "H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT",
            "I": "PGUP", "Q": "PGDN", "G": "HOME", "O": "END",
            "S": "DELETE", ";": "F1", "<": "F2", "=": "F3", "?": "F5",
        }.get(getwch(), "UNKNOWN")
    if first == "\x08":
        pressed = control_pressed or _windows_control_pressed
        return "CTRL_H" if pressed() else "BACKSPACE"
    return {
        "\r": "ENTER", "\n": "ENTER",
        "\x1b": "ESC", "\x03": "ESC",
    }.get(first, first)


def _device_key(mac: str, ip: str) -> str:
    return f"mac:{mac.upper()}" if mac else f"ip:{ip}"


def _clean_tui_output(value: str) -> list[str]:
    """Normaliza retornos externos antes de colocarlos en el panel inferior."""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = ANSI_ESCAPE.sub("", normalized)
    normalized = CONTROL_CHARACTER.sub("", normalized).expandtabs(4)
    lines = [line.rstrip() for line in normalized.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines or [""]


def _fit_ansi(value: str, width: int) -> str:
    """Recorta texto coloreado contando solo caracteres visibles."""
    if width <= 0:
        return ""
    plain = ANSI_ESCAPE.sub("", value)
    if len(plain) <= width:
        return value
    target = max(0, width - 1)
    output: list[str] = []
    visible = 0
    position = 0
    for match in ANSI_ESCAPE.finditer(value):
        segment = value[position:match.start()]
        take = max(0, min(len(segment), target - visible))
        output.append(segment[:take])
        visible += take
        if visible >= target:
            break
        output.append(match.group(0))
        position = match.end()
    else:
        output.append(value[position:position + max(0, target - visible)])
    return "".join(output) + "…" + RESET


def _selectable_output_indexes(lines: list[str]) -> list[int]:
    """Localiza las filas de datos situadas tras separadores de tabla."""
    selectable: list[int] = []
    inside_table = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped and re.fullmatch(r"[-─═=\s]+", stripped):
            inside_table = True
            continue
        if inside_table and stripped.startswith("["):
            inside_table = False
            continue
        if inside_table and stripped:
            # Una nueva cabecera seguida de otro separador se descartará al
            # recalcular el bloque; las filas ordinarias quedan navegables.
            selectable.append(index)
        elif inside_table and not stripped:
            inside_table = False
    return selectable


def _compact_timestamp(value: str) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%m/%d %H:%M")
    except ValueError:
        return value


def _inject_selected_group_element(parts: list[str], selector: str) -> list[str]:
    """Completa -add/-remove con el elemento resaltado dentro del TUI."""
    contextual = list(parts)
    if (
        selector
        and len(contextual) >= 3
        and contextual[0].casefold() == "group"
        and contextual[-1].casefold() in ("-add", "-remove")
    ):
        contextual.append(selector)
    return contextual


def _translate_tui_element(parts: list[str], selected: str) -> list[str]:
    """Traduce la sintaxis corta del TUI al comando element canónico."""
    if not parts or parts[0].casefold() != "element":
        return list(parts)
    if len(parts) == 1:
        if not selected:
            raise ValueError("selecciona un elemento o indica su IP, MAC o alias")
        return ["element", selected]

    add_aliases = ("-add", "--add")
    if parts[1].casefold() in add_aliases:
        if len(parts) < 3:
            raise ValueError("usa: element -add MAC [-name ...] [-alias ...]")
        return list(parts)

    option_map = {
        "-name": "name", "--name": "name", "name": "name",
        "-alias": "alias", "--alias": "alias", "alias": "alias",
        "-description": "description", "--description": "description",
        "description": "description",
        "-group": "group", "--group": "group", "group": "group",
        "-cnf": "cnf", "--cnf": "cnf", "cnf": "cnf",
        "-protocol": "protocol", "--protocol": "protocol", "protocol": "protocol",
        "-delete": "delete", "--delete": "delete", "-del": "delete",
        "-delate": "delete", "delete": "delete", "del": "delete",
        "remove": "delete",
    }
    first = parts[1].casefold()
    if first in option_map:
        if not selected:
            raise ValueError("no hay ningún elemento seleccionado")
        target, option_index = selected, 1
    else:
        target, option_index = parts[1], 2
        if len(parts) == 2:
            return ["element", target]

    option = parts[option_index].casefold()
    if option not in option_map:
        # Conserva la sintaxis avanzada anterior: element OBJETIVO edit ...
        return list(parts)
    action = option_map[option]
    values = parts[option_index + 1:]
    if action == "delete":
        if values and values != ["--yes"]:
            raise ValueError("element -delete no acepta valores")
        return ["element", target, "delete", *values]
    if not values:
        raise ValueError(f"falta el valor para element {parts[option_index]}")
    return ["element", target, action, *values]


def _expand_tui_widths(
    widths: dict[str, int], fields: tuple[str, ...], available: int, gap: int
) -> None:
    """Distribuye el ancho sobrante para que el inventario ocupe la ventana."""
    used = sum(widths.values()) + gap * max(0, len(fields) - 1)
    surplus = max(0, available - used)
    limits = {
        "description": 42, "manufacturer": 26, "lastSeen": 25,
        "discoveryMethods": 22, "protocols": 18, "NAME": 20,
        "ALIAS": 18, "GROUP": 12,
    }
    for field in (
        "description", "manufacturer", "discoveryMethods", "lastSeen",
        "NAME", "ALIAS", "protocols", "GROUP",
    ):
        if not surplus or field not in widths:
            continue
        growth = min(surplus, max(0, limits[field] - widths[field]))
        widths[field] += growth
        surplus -= growth
    if surplus and "description" in widths:
        widths["description"] += surplus


def _spinner_character(index: int) -> str:
    sequence = "\\|/-"
    return sequence[index % len(sequence)]


class _TuiScanProgress:
    """Adapta el progreso del escáner al refresco de pantalla completa."""

    def __init__(self, tui: LanctlTui) -> None:
        self.tui = tui
        self.total = 1
        self.current = 0
        self.last_draw = 0.0

    def begin(
        self,
        total: int,
        phase: str = "Search",
        found_total: int = 0,
        known_identities: dict[str, str] | None = None,
    ) -> None:
        self.total = max(1, total)
        self.current = 0
        self.tui.scan_total = self.total
        self.tui.scan_current = 0
        self.tui.spinner_index = 0
        self._draw(force=True)

    def phase(self, phase: str) -> None:
        self._draw()

    def found(self, *keys: str) -> None:
        self.tui.discovery_found(keys)
        self._draw(force=True)

    def advance(self, amount: int = 1) -> None:
        self.current = min(self.total, self.current + amount)
        self.tui.scan_current = self.current
        self.tui.spinner_index = (self.tui.spinner_index + 1) % 4
        self._draw()

    def complete(self) -> None:
        self.current = self.total
        self.tui.scan_current = self.total
        self._draw(force=True)

    def clear(self) -> None:
        return

    def _draw(self, force: bool = False) -> None:
        now = time.monotonic()
        if force or now - self.last_draw >= 0.06:
            self.tui.render()
            self.last_draw = now


def _dhcp_boundary_indexes(devices, configured_range: str | None):
    indexes = [
        index for index, device in enumerate(devices)
        if _ip_in_range(device.ip, configured_range)
    ]
    if not indexes:
        return None, None
    return indexes[0], indexes[-1]


def _ip_in_range(value: str, configured_range: str | None) -> bool:
    if not configured_range:
        return False
    try:
        start_text, end_text = configured_range.split("-", 1)
        address = ipaddress.IPv4Address(value)
        return ipaddress.IPv4Address(start_text.strip()) <= address <= ipaddress.IPv4Address(end_text.strip())
    except (ValueError, ipaddress.AddressValueError):
        return False


def _parse_list_filter(parts: list[str]) -> tuple[str, str]:
    if not parts or [part.casefold() for part in parts] in (["--all"], ["-all"]):
        return "all", ""
    lowered = [part.casefold() for part in parts]
    if lowered in (["--connected"], ["-connected"], ["--active"]):
        return "connected", ""
    if lowered in (
        ["--disconnected"], ["--disconect"], ["-disconnected"],
        ["-disconect"], ["--offline"],
    ):
        return "disconnected", ""
    if lowered in (["-dhcp"], ["--dhcp"]):
        return "dhcp", ""
    if lowered in (["-statics"], ["--statics"], ["--static"]):
        return "statics", ""
    if len(parts) == 2 and lowered[0] in ("-group", "--group"):
        return "group", parts[1].upper()
    raise ValueError(
        "usa: list --all|--connected|--disconnected|-group NOMBRE|-dhcp|-statics"
    )


def _last_meaningful_line(value: str) -> str:
    return next((line.strip() for line in reversed(value.splitlines()) if line.strip()), "")


def _function_bar(width: int) -> str:
    buttons = (
        ("F1", "Ayuda"), ("F2", "Info"), ("F3", "Ping"),
        ("F5", "Actualizar"), ("Ctrl+H", "Comandos"),
        ("↑↓", "Seleccionar"), ("Enter", "Ejecutar"), ("Esc", "Salir"),
    )
    output = ""
    visible = 0
    for index, (key, label) in enumerate(buttons):
        spacing = "   " if index else ""
        plain = f"{spacing} {key}  {label}"
        if visible + len(plain) > width:
            break
        output += f"{Back.BLACK}{spacing}{RESET}" + (
            f"{Style.BRIGHT}{Back.WHITE}{Fore.BLACK} {key} {RESET}"
            f"{Back.BLACK}{Fore.WHITE} {label}{RESET}"
        )
        visible += len(plain)
    return output + f"{Back.BLACK}{' ' * max(0, width - visible)}{RESET}"


def run_tui() -> int:
    return LanctlTui().run()
