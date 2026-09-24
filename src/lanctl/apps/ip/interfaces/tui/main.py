from __future__ import annotations

import argparse
import io
import ipaddress
import json
import os
import queue
import re
import shutil
import sqlite3
import sys
import tempfile
import textwrap
import threading
import time
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

from colorama import Back, Fore, Style, just_fix_windows_console

from lanctl import __version__
from lanctl.apps.ip.infrastructure.services.lan_scanner import local_ipv4
from lanctl.apps.ip.interfaces.tui.controllers import ManagerController, SettingsEditor
from lanctl.apps.ip.interfaces.tui.keyboard import (
    CONFIGURABLE_TUI_KEYS,
    DEFAULT_TUI_KEY_BINDINGS,
    FOOTER_ACTIONS,
    normalize_footer_actions,
    normalize_key_bindings,
    posix_key_available,
    posix_terminal_mode,
    read_posix_key,
)
from lanctl.apps.ip.interfaces.tui.keyboard import read_windows_key as _read_windows_key
from lanctl.apps.ip.interfaces.tui.layout import (
    DEFAULT_COLUMN_SPECS,
    adaptive_layout,
    allocate_column_widths,
    minimum_terminal_width,
    normalize_cli_percent,
    normalize_column_specs,
    normalize_panel_layout,
    panel_rows,
)
from lanctl.apps.ip.interfaces.tui.managers import (
    plugin_detail as _plugin_detail,
)
from lanctl.apps.ip.interfaces.tui.managers import (
    plugin_manager_modal,
    project_manager_modal,
)
from lanctl.apps.ip.interfaces.tui.managers import (
    project_detail as _project_detail,
)
from lanctl.apps.ip.interfaces.tui.modal import HelpCommand, ModalState, SettingField
from lanctl.apps.ip.interfaces.tui.render import RichTuiRenderer
from lanctl.core.config import load_config
from lanctl.core.database import DeviceDatabase
from lanctl.core.layout import fit_text, terminal_columns, terminal_rows
from lanctl.core.output import (
    CNF_COLORS,
    DARK_CNF_COLORS,
    DARK_FIELD_COLORS,
    FIELD_COLORS,
)
from lanctl.core.projects import active_project_info

RESET = Style.RESET_ALL
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
CONTROL_CHARACTER = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TUI_ENTER_SCREEN = "\x1b[?1049h\x1b[?7l\x1b[2J\x1b[H"
TUI_LEAVE_SCREEN = "\x1b[?25h\x1b[?7h\x1b[?1049l"
LIST_ELEMENT_PANEL = "ListElement"
CLI_PANEL = "CLI"

TUI_ELEMENT_HELP = (
    "ELEMENT · gestión simplificada dentro del TUI",
    "  element                         Muestra el elemento seleccionado",
    "  element OBJETIVO                Selecciona por IP, MAC o alias",
    "  element -add MAC [-ip IP] [...] Añade un elemento no detectado",
    "  element -ip DIRECCION           Corrige o asigna la IPv4",
    "  element -name TEXTO             Cambia el nombre",
    "  element -alias TEXTO            Cambia el alias",
    "  element -description TEXTO      Cambia la descripción",
    "  element -idf ABC-012            Asigna el identificador físico IDF",
    "  element -group GRUPO            Añade al grupo",
    "  element -cnf O|X|-|S|F          F fija la selección en el TUI",
    "  element -delete                 Elimina tras confirmación",
    "Puedes escribir OBJETIVO antes de cualquier opción para no usar la fila resaltada.",
    "Usa ↑/↓ para elegir una opción y completa sus argumentos en el prompt.",
)

# La cadena insertada evita copiar los marcadores descriptivos (OBJETIVO,
# TEXTO, etc.) como si fueran argumentos reales.
TUI_ELEMENT_SUGGESTIONS = (
    (1, "element "),
    (2, "element "),
    (3, "element -add "),
    (4, "element -ip "),
    (5, "element -name "),
    (6, "element -alias "),
    (7, "element -description "),
    (8, "element -idf "),
    (9, "element -group "),
    (10, "element -cnf "),
    (11, "element -delete"),
)


def _inventory_cell(
    field: str,
    values: dict[str, str],
    widths: dict[str, int],
    *,
    active: bool,
    selected: bool,
) -> str:
    """Formatea una celda sin crear una función por cada fila renderizada."""

    value = fit_text(values[field], widths[field])
    value = (
        value.rjust(widths[field])
        if field == "responseMs"
        else value.center(widths[field])
        if field == "cnf"
        else value.ljust(widths[field])
    )
    palette = FIELD_COLORS if active else DARK_FIELD_COLORS
    color = palette[field]
    if field == "cnf":
        color = (CNF_COLORS if active else DARK_CNF_COLORS).get(values[field], color)
    intensity = Style.BRIGHT if active else Style.DIM
    background = Back.LIGHTBLACK_EX if selected else ""
    return f"{background}{intensity}{color}{value}{RESET}"


class LanctlTui:
    """TUI de pantalla completa basada en el inventario persistente de LANCTL."""

    def __init__(self, startup_modal: str | None = None) -> None:
        config = load_config()
        self.screen = sys.stdout
        self.renderer = RichTuiRenderer(self.screen)
        self.database = DeviceDatabase(config["database"])
        self.project_info = active_project_info(config)
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
        self.pending_project_path: str | None = None
        self.active_devices: set[str] = set()
        self.response_ms: dict[str, float] = {}
        self.running = True
        self.scanning = False
        self.spinner_index = 0
        self.scan_current = 0
        self.scan_total = 0
        self.scan_visible_devices: set[str] = set()
        self.scan_summary: dict[str, object] = {}
        self.scan_error = ""
        self.scan_error_after_discovery = False
        self._scan_previous_state: tuple[set[str], dict[str, float], dict[str, object]] | None = (
            None
        )
        self.detail_lines: list[str] = []
        self.detail_scroll = 0
        self.view_state = "inventory"
        self.history_events = []
        self.history_index = 0
        self.command_history: list[str] = []
        self.command_history_index = 0
        self.command_history_scroll = 0
        self.secret_prompt = ""
        self.modal: ModalState | None = None
        self._last_screen_lines: list[str] = []
        self.startup_modal = startup_modal.casefold() if startup_modal else None
        self.key_bindings = normalize_key_bindings(config.get("tuiKeyBindings"))
        self.footer_buttons = normalize_footer_actions(config.get("tuiFooterButtons"))
        self.panel_layout = normalize_panel_layout(config.get("tuiPanelLayout", "cli.bottom"))
        self.cli_height_percent = normalize_cli_percent(config.get("tuiCliHeightPercent", 28))
        self.column_widths = normalize_column_specs(config.get("tuiColumnWidths"))
        self.credential_users = _credential_user_map(config)
        self.remote_actions = queue.Queue()
        self.scan_events = queue.Queue()
        self._scan_cancel = threading.Event()
        self._scan_thread: threading.Thread | None = None
        self._read_key = None
        self.reload()

    @property
    def selected(self):
        return self.devices[self.index] if self.devices else None

    def reload(self) -> None:
        identity = self.selected.mac if self.selected else ""
        # `project use` puede cambiar el JSON que respalda el inventario.
        # Reconstruir el acceso evita conservar en memoria el proyecto anterior.
        config = load_config()
        self.database = DeviceDatabase(config["database"])
        self.project_info = active_project_info(config)
        self.dhcp_range = config.get("dhcpRange")
        self.key_bindings = normalize_key_bindings(config.get("tuiKeyBindings"))
        self.footer_buttons = normalize_footer_actions(config.get("tuiFooterButtons"))
        self.panel_layout = normalize_panel_layout(config.get("tuiPanelLayout", "cli.bottom"))
        self.cli_height_percent = normalize_cli_percent(config.get("tuiCliHeightPercent", 28))
        self.column_widths = normalize_column_specs(config.get("tuiColumnWidths"))
        self.credential_users = _credential_user_map(config)
        from lanctl.core.device_retention import with_session_devices

        self.all_devices = with_session_devices(self.database.path, self.database.load())
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
        if getattr(self, "scanning", False):
            source = [
                device
                for device in source
                if _device_key(device.mac, device.ip) in self.scan_visible_devices
            ]
        if mode == "connected":
            return [
                device
                for device in source
                if _device_key(device.mac, device.ip) in self.active_devices
            ]
        if mode == "disconnected":
            return [
                device
                for device in source
                if _device_key(device.mac, device.ip) not in self.active_devices
            ]
        if mode == "group":
            return [device for device in source if device.in_group(value)]
        if mode in ("dhcp", "statics"):

            def in_dhcp(device):
                return _ip_in_range(device.ip, self.dhcp_range)

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

    def cycle_list_view(self) -> None:
        """Alterna las vistas rápidas disponibles para el inventario con Tab.

        Los grupos se generan a partir del inventario actual, por lo que no se
        necesita un selector adicional ni se persiste un filtro temporal.
        """

        groups = sorted(
            {
                str(group).strip().upper()
                for device in self.all_devices
                for group in device.groups
                if str(group).strip()
            }
        )
        views = [
            ("all", ""),
            ("connected", ""),
            ("disconnected", ""),
            *(("group", group) for group in groups),
        ]
        if self.dhcp_range:
            views.extend((("dhcp", ""), ("statics", "")))

        try:
            position = views.index(self.list_filter)
        except ValueError:
            position = -1
        mode, value = views[(position + 1) % len(views)]
        parts = ["--" + mode] if mode != "group" else ["--group", value]
        self.configure_list(parts)

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
        return (
            terminal_columns(self.screen) or size.columns,
            max(12, terminal_rows(self.screen) or size.lines),
        )

    def _inventory_lines(self, width: int, height: int) -> list[str]:
        first_dhcp, last_dhcp = _dhcp_boundary_indexes(self.devices, self.dhcp_range)
        # Reserva espacio para delimitar el bloque DHCP sin desplazar el panel.
        reserved = (2 if first_dhcp is not None else 0) + (1 if self.scan_total else 0)
        rows = max(1, height - reserved)
        if self.index < self.scroll:
            self.scroll = self.index
        elif self.index >= self.scroll + rows:
            self.scroll = self.index - rows + 1
        self.scroll = max(0, min(self.scroll, max(0, len(self.devices) - rows)))

        fields = ["IP", "responseMs", "cnf", "ALIAS", "MAC", "NAME", "GROUP", "description"]
        if width >= 170:
            fields.append("manufacturer")
        if width >= 205:
            fields.append("users")
        gap = 1 if width < 100 else 2
        for optional in (
            "users",
            "manufacturer",
            "description",
            "GROUP",
            "NAME",
            "ALIAS",
            "responseMs",
            "cnf",
        ):
            if minimum_terminal_width(fields, gap) <= width:
                break
            if optional in fields:
                fields.remove(optional)
        fields = tuple(fields)
        labels = {
            "IP": "IP",
            "responseMs": "ms",
            "cnf": "cnf",
            "ALIAS": "ALIAS",
            "MAC": "MAC",
            "NAME": "NAME",
            "GROUP": "GROUP",
            "description": "DESCRIPTION",
            "manufacturer": "MANUFACTURER",
            "users": "USERS",
        }
        widths = allocate_column_widths(
            fields,
            max(20, width - 2),
            gap,
            getattr(self, "column_widths", DEFAULT_COLUMN_SPECS),
        )

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
        visible = self.devices[self.scroll : self.scroll + rows]
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
                "GROUP": ",".join(str(group).upper() for group in device.groups) or "-",
                "description": device.description or "-",
                "discoveryMethods": "+".join(device.discovery_methods)
                or device.last_discovery
                or "-",
                "lastSeen": _compact_timestamp(device.last_seen),
                "manufacturer": device.manufacturer or "-",
                "users": _device_user_labels(
                    device,
                    getattr(self, "credential_users", {}),
                ),
            }

            marker = f"{Style.BRIGHT}{Fore.WHITE}{'▶' if selected else ' '}{RESET} "
            output.append(
                marker
                + joiner.join(
                    _inventory_cell(
                        field,
                        values,
                        widths,
                        active=active,
                        selected=selected,
                    )
                    for field in fields
                )
            )
            if absolute == last_dhcp:
                output.append(f"{Style.DIM}{Fore.YELLOW}{dhcp_separator}{RESET}")
        # ``height`` representa las filas de datos; cabecera y subrayado
        # completan el tamaño real del panel ListElement. Si hay un escaneo,
        # su progreso ocupa siempre la última fila interna, no la primera fila
        # libre situada justo después del último dispositivo encontrado.
        panel_height = height + 2
        progress = self._progress_line(width) if self.scan_total else None
        content_height = panel_height - (1 if progress else 0)
        if len(output) > content_height:
            output = output[:content_height]
        while len(output) < content_height:
            output.append("")
        if progress:
            output.append(progress)
        return output

    def _progress_line(self, width: int) -> str:
        return RichTuiRenderer.progress_line(
            width=width,
            current=self.scan_current,
            total=self.scan_total,
            found=len(self.scan_visible_devices),
            scanning=self.scanning,
        )

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
        project_info = getattr(self, "project_info", None)
        project_name = project_info["name"] if project_info else "Sin proyecto"
        project_line = (
            f"{Style.BRIGHT}{Fore.CYAN} PROYECTO {RESET} {Fore.WHITE}{project_name}{RESET}"
        )
        if getattr(self, "scanning", False):
            return [
                project_line,
                (
                    f"{Style.BRIGHT}{Fore.YELLOW} ESCANEANDO {RESET} "
                    f"{Fore.WHITE}Elementos encontrados: "
                    f"{len(self.scan_visible_devices)}{RESET}"
                ),
                f"{Fore.LIGHTBLACK_EX}La lista se completa en tiempo real.{RESET}",
            ]
        scan_error = getattr(self, "scan_error", "")
        if scan_error:
            phase = (
                "Procesamiento/guardado fallido"
                if getattr(self, "scan_error_after_discovery", False)
                else "Descubrimiento fallido"
            )
            return [
                project_line,
                f"{Style.BRIGHT}{Fore.RED} ERROR DE ESCANEO {RESET} {phase}",
                f"{Fore.YELLOW}Se conserva el último estado válido; los datos no están actualizados.{RESET}",
            ]
        summary = self.scan_summary
        if not summary:
            return [
                project_line,
                f"{Style.BRIGHT}{Fore.CYAN} RED {RESET} Sin escaneo en esta sesión",
                f"{Fore.LIGHTBLACK_EX}Pulsa F5 para actualizar.{RESET}",
            ]
        return [
            project_line,
            (
                f"{Style.BRIGHT}{Fore.CYAN} PERFIL {RESET} "
                f"{Fore.WHITE}{summary['profile']}{RESET}  "
                f"{Style.BRIGHT}{Fore.CYAN} MÉTODO {RESET} "
                f"{Fore.WHITE}{summary['discovery']}{RESET}  "
                f"{Style.BRIGHT}{Fore.GREEN} ACTIVOS {RESET} "
                f"{summary['active']}/{summary['total']}"
            ),
            (
                f"{Style.BRIGHT}{Fore.LIGHTBLUE_EX} ICMP {RESET} "
                f"{summary['icmp']}  "
                f"{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} ARP {RESET} "
                f"{summary['arp']}  "
                f"{Style.BRIGHT}{Fore.YELLOW} CACHE {RESET} "
                f"{summary['cache']}  "
                f"{Style.BRIGHT}{Fore.CYAN} MOSTRADOS {RESET} "
                f"{summary['shown']}"
            ),
        ]

    def _message_lines(self, width: int, rows: int) -> list[str]:
        if rows <= 0:
            return []
        if self.output_focus and self.output_selectable:
            selected_line = self.output_selectable[self.output_index]
            if selected_line < self.output_scroll:
                self.output_scroll = selected_line
            elif selected_line >= self.output_scroll + rows:
                self.output_scroll = selected_line - rows + 1
            visible = self.messages[self.output_scroll : self.output_scroll + rows]
            rendered = []
            for offset, message in enumerate(visible):
                absolute = self.output_scroll + offset
                selected = absolute == selected_line
                marker = "▶ " if selected else "  "
                background = Back.LIGHTBLACK_EX if selected else ""
                intensity = Style.BRIGHT if selected else ""
                rendered.append(
                    f"{background}{intensity}{Fore.WHITE}{fit_text(marker + message, width)}{RESET}"
                )
            return rendered
        if self.command_suggestions:
            selected_line = (
                self.command_suggestions[self.suggestion_index][0]
                if self.suggestion_index >= 0
                else -1
            )
            start = max(0, selected_line - rows + 1) if selected_line >= rows else 0
            start = min(start, max(0, len(self.messages) - rows))
            rendered = []
            for absolute in range(start, min(len(self.messages), start + rows)):
                message = self.messages[absolute]
                selected = absolute == selected_line
                marker = "▶ " if selected else "  "
                background = Back.LIGHTBLACK_EX if selected else ""
                intensity = Style.BRIGHT if selected else ""
                rendered.append(
                    f"{background}{intensity}{Fore.WHITE}{fit_text(marker + message, width)}{RESET}"
                )
            return rendered[-rows:]
        wrapped: list[str] = []
        for message in self.messages[-max(12, rows) :]:
            wrapped.extend(textwrap.wrap(message, width=max(1, width - 2)) or [""])
        return [f" {fit_text(message, width - 1)}" for message in wrapped[-rows:]]

    def render(self) -> None:
        width, height = self._dimensions()
        width = max(20, width)
        if getattr(self, "modal", None):
            self._render_modal(width, height)
            return
        if self.detail_lines:
            self._render_detail(width, height)
            return
        list_rows, cli_rows = panel_rows(
            height,
            getattr(self, "cli_height_percent", 28),
        )
        panel_layout = normalize_panel_layout(getattr(self, "panel_layout", "cli.bottom"))
        title = f" LANCTL TUI {__version__} "
        mode, value = self.list_filter
        filter_name = f"{mode}:{value}" if value else mode
        if self.view_state == "history":
            counter = f" {LIST_ELEMENT_PANEL} [history] {self.history_index + 1 if self.history_events else 0}/{len(self.history_events)} "
        elif self.view_state == "command-history":
            counter = f" {LIST_ELEMENT_PANEL} [commands] {self.command_history_index + 1 if self.command_history else 0}/{len(self.command_history)} "
        else:
            counter = (
                f" {LIST_ELEMENT_PANEL} [{filter_name}] "
                f"{self.index + 1 if self.devices else 0}/{len(self.devices)} "
            )
        secret_prompt = getattr(self, "secret_prompt", "")
        prompt_label = (
            "SECRETO"
            if secret_prompt
            else _spinner_character(self.spinner_index)
            if self.scanning
            else "CONFIRM"
            if self.pending_confirmation
            else self._selection_label()
        )
        prompt_prefix = f"LANCTL[{prompt_label}]> "
        prompt_value = secret_prompt if secret_prompt else self.command
        prompt_text = fit_text(f"{prompt_prefix}{prompt_value}", width)
        prompt_line = f"{Fore.LIGHTGREEN_EX}{prompt_text}{RESET}"
        status_lines = [_fit_ansi(line, width) for line in self._status_lines(width)]
        # Título/separador y prompt consumen dos filas del bloque CLI. Incluso
        # en la altura mínima se reserva otra fila para el resultado de teclas
        # como Ctrl+S; las estadísticas ceden espacio antes que ocultarlo.
        status_lines = status_lines[: max(0, cli_rows - 3)]
        message_rows = max(1, cli_rows - len(status_lines) - 2)
        messages = self._message_lines(width, message_rows)
        message_padding = [""] * max(0, message_rows - len(messages))
        inventory_height = max(1, list_rows - 3)
        inventory = (
            self._history_lines(width, inventory_height + 2)
            if self.view_state == "history"
            else self._command_history_lines(width, inventory_height + 2)
            if self.view_state == "command-history"
            else self._inventory_lines(width, inventory_height)
        )
        inventory = list(inventory[: max(0, list_rows - 1)])
        inventory.extend([""] * max(0, list_rows - 1 - len(inventory)))

        if panel_layout == "cli.top":
            cli_title = (
                f"{title}{'─' * max(0, width - len(title) - len(CLI_PANEL) - 2)} {CLI_PANEL} "
            )
            list_separator = f" {counter.strip()} "
            list_separator += "─" * max(0, width - len(list_separator))
            lines = [
                f"{Style.BRIGHT}{Fore.CYAN}{fit_text(cli_title, width)}{RESET}",
                prompt_line,
                *messages,
                *message_padding,
                *status_lines,
                f"{Style.BRIGHT}{Fore.CYAN}{fit_text(list_separator, width)}{RESET}",
                *inventory,
            ]
            cursor_row = 2
        else:
            title_space = max(0, width - len(title) - len(counter))
            title_content = (
                f"{title}{'─' * title_space}{counter}"
                if len(title) + len(counter) <= width
                else fit_text(f"{title}{counter}", width)
            )
            lines = [
                f"{Style.BRIGHT}{Fore.CYAN}{title_content}{RESET}",
                *inventory,
                f"{Fore.CYAN} {CLI_PANEL} {'─' * max(0, width - len(CLI_PANEL) - 2)}{RESET}",
                *status_lines,
                *message_padding,
                *messages,
                prompt_line,
            ]
            cursor_row = height - 1
        keys = _function_bar(
            width,
            getattr(self, "footer_buttons", None),
            getattr(self, "key_bindings", None),
        )
        lines = lines[: height - 1]
        lines.extend([""] * max(0, height - 1 - len(lines)))
        lines.append(keys)
        cursor_offset = len(prompt_value) if self.secret_prompt else self.cursor
        cursor_column = min(width, len(prompt_prefix) + cursor_offset + 1)
        renderer = getattr(self, "renderer", None) or RichTuiRenderer(self.screen)
        self._last_screen_lines = list(lines[:height])
        renderer.render_screen(
            lines,
            width=width,
            height=height,
            cursor_row=cursor_row,
            cursor_column=cursor_column,
        )

    def _open_modal(self, modal: ModalState) -> None:
        modal.background = list(getattr(self, "_last_screen_lines", []))
        self.modal = modal

    def _render_modal(self, width: int, height: int) -> None:
        modal = self.modal
        if not modal:
            return
        settings_sized = modal.kind == "settings"
        maximum_width = modal.max_width or (130 if settings_sized else 100)
        maximum_height = modal.max_height or (36 if settings_sized else 30)
        geometry = adaptive_layout(width, height, settings=maximum_width > 100)
        body_rows = max(1, min(geometry.modal_height, maximum_height) - 7)
        content_width = max(24, min(geometry.modal_width, maximum_width) - 6)
        page = self._modal_page(modal, content_width=content_width)
        maximum = max(0, len(page) - body_rows)
        modal.scroll = max(0, min(modal.scroll, maximum))
        visible = page[modal.scroll : modal.scroll + body_rows]
        self.renderer.render_modal(
            modal.background,
            title=(
                f"{modal.title} / MENU[{modal.tabs[modal.tab_index]}]"
                f"{' / EDITANDO' if modal.editing else ''}"
                if modal.kind in {"settings", "info"} and modal.tabs
                else modal.title
            ),
            tabs=modal.tabs,
            selected_tab=modal.tab_index,
            body=visible,
            footer=modal.footer,
            width=width,
            height=height,
            max_width=maximum_width,
            max_height=maximum_height,
        )

    def _modal_page(self, modal: ModalState, content_width: int | None = None) -> list[str]:
        if modal.kind == "settings":
            if modal.tabs and modal.tabs[modal.tab_index] == "EXIT":
                return self._settings_exit_page(modal)
            available = content_width or 118
            return SettingsEditor.render_page(
                modal,
                description_width=max(24, available - 4),
                table_width=available,
            )
        if modal.kind == "project_create":
            return self._project_create_page(modal)
        if modal.kind == "info" and modal.tabs[modal.tab_index] != "Puertos":
            available = content_width or 88
            return [
                *SettingsEditor.render_page(
                    modal,
                    description_width=max(24, available - 4),
                    table_width=available,
                ),
                "",
                "  OBSERVACIONES Y DATOS REGISTRADOS",
                *modal.page,
            ]
        if modal.kind == "help" and modal.tab_index == 0:
            lines = []
            for index, entry in enumerate(modal.items):
                marker = "▶" if index == modal.selected else " "
                aliases = f" ({', '.join(entry.aliases)})" if entry.aliases else ""
                lines.append(f"{marker} {entry.name:<22}{aliases:<24} {entry.description}")
            return lines
        if (
            modal.kind in {"plugins", "projects", "commands", "remote_users", "project_close"}
            and modal.tab_index == 0
        ):
            lines = []
            for index, line in enumerate(modal.page):
                lines.append(("▶ " if index == modal.selected else "  ") + line)
            return lines
        return modal.page

    def show_history(self, selector: str | None = None) -> None:
        from lanctl.core.history import HistoryService

        target = selector or (
            (self.selected.device_id or self.selected.mac or self.selected.ip)
            if self.selected
            else None
        )
        try:
            self.history_events = HistoryService().query(
                None if target == "all" else target, limit=1000, reverse=True
            )
            self.history_index = 0
            self.view_state = "history"
            self.messages = [
                f"Historial: {len(self.history_events)} eventos | Enter detalle | Esc inventario"
            ]
        except ValueError as error:
            self.messages = [str(error)]

    def show_command_history(self) -> None:
        entries = self.command_history or ["(No hay comandos en esta sesión)"]
        self._open_modal(
            ModalState(
                kind="commands",
                title="COMANDOS",
                tabs=["Historial"],
                pages=[list(entries)],
                selected=max(0, len(entries) - 1),
                footer="↑/↓ seleccionar  Enter recuperar  Esc cerrar",
            )
        )

    def show_help_modal(self) -> None:
        entries = _help_command_entries()
        self._open_modal(
            ModalState(
                kind="help",
                title="HELP",
                tabs=["Comandos", "Detalle", "Teclas"],
                pages=[
                    [],
                    _help_command_detail(entries[0])
                    if entries
                    else ["No hay comandos registrados."],
                    [
                        "NAVEGACIÓN",
                        "  ←/→       Cambiar entre Comandos, Detalle y Teclas",
                        "  ↑/↓       Seleccionar un comando o desplazar contenido",
                        "  PgUp/PgDn Saltar diez comandos o líneas",
                        "  Home/End   Ir al primer o último comando",
                        "  Enter      Abrir el detalle del comando seleccionado",
                        "  Tab        Preparar el comando seleccionado en el prompt",
                        "  F1 / Esc   Cerrar esta ventana",
                        "",
                        "ACCESOS RÁPIDOS DEL TUI",
                        "  F2         Información completa del elemento",
                        "  F3         Ping del elemento seleccionado",
                        "  F5         Actualizar y descubrir la red",
                        "  F7         Gestor de plugins",
                        "  F9         Gestor de proyectos",
                        "  F12        Editor de configuración",
                        "  Ctrl+H     Historial de comandos",
                        "  Ctrl+F     Buscar o filtrar elementos",
                        "  Ctrl+R     Recargar inventario sin escanear",
                        "  Ctrl+E     Editar el elemento seleccionado",
                        "  Ctrl+G     Gestionar grupos",
                        "  Ctrl+P     Abrir la sección de puertos",
                        "  Ctrl+O     Abrir acceso SSH/HTTP/Telnet/...",
                        "  Ctrl+S     Guardar manualmente el proyecto",
                        "  Ctrl+D     Consultar cambios pendientes",
                        "  Ctrl+X/J   Copiar línea o JSON",
                        "  Ctrl+L     Limpiar y enfocar la consola",
                        "  Ctrl+Q     Iniciar el cierre seguro",
                    ],
                ],
                items=entries,
                footer="↑/↓ seleccionar  Enter detalle  Tab preparar  ←/→ sección  F1/Esc cerrar",
            )
        )

    def show_plugin_manager(self) -> None:
        try:
            from lanctl.core.plugins.manager import get_plugin_manager

            plugins = get_plugin_manager().list()
            self._open_modal(plugin_manager_modal(plugins))
        except (OSError, ValueError) as error:
            self.messages = [f"No se pudo cargar el gestor de plugins: {error}"]

    def show_project_manager(self) -> None:
        config = load_config()
        from lanctl.core.projects.catalog import ProjectCatalog
        from lanctl.core.projects.paths import default_project_directory

        configured = config.get("projectsDirectory")
        root = (
            Path(os.path.expandvars(str(configured))).expanduser()
            if configured
            else default_project_directory()
        )
        active = self.project_info.get("path", "") if self.project_info else ""
        try:
            projects = ProjectCatalog().refresh(root, active_path=active or None)
        except (OSError, sqlite3.DatabaseError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.Project.Catalog.Refresh",
                code="PROJECT.CATALOG.REFRESH_FAILED",
                level=24,
                print_output=False,
            )
            projects = []
            self.messages = [f"No se pudo actualizar projects.db: {error}"]
        self._open_modal(project_manager_modal(projects, active, root))

    def show_settings(self) -> None:
        config = load_config()
        key_bindings = normalize_key_bindings(config.get("tuiKeyBindings"))
        footer_buttons = normalize_footer_actions(config.get("tuiFooterButtons"))

        def text(key: str, fallback="") -> str:
            if key.startswith("tuiKey."):
                assigned = key_bindings[key.removeprefix("tuiKey.")]
                return assigned.replace("_", "+") if assigned else "None"
            if key == "tuiFooterButtons":
                return ",".join(footer_buttons)
            if key.startswith("tuiFooter."):
                return "on" if key.removeprefix("tuiFooter.") in footer_buttons else "off"
            if key.startswith("tuiColumn."):
                name = key.removeprefix("tuiColumn.")
                return str(config.get("tuiColumnWidths", DEFAULT_COLUMN_SPECS).get(name, ""))
            value = config.get(key, fallback)
            if isinstance(value, bool):
                return "on" if value else "off"
            if isinstance(value, list):
                return ",".join(str(item) for item in value)
            return "" if value is None else str(value)

        definitions = (
            (
                "GENERAL",
                "listColumns",
                "Columnas de lista",
                "--list-fields",
                "separadas por comas",
                "Define qué columnas aparecen en la lista normal y en el inventario del TUI, respetando el orden indicado.",
            ),
            (
                "APARIENCIA",
                "tuiPanelLayout",
                "Posición del CLI",
                "--tui-layout",
                "cli.top | cli.bottom",
                "Coloca el prompt y la salida del CLI por encima o por debajo de la ventana ListElement.",
            ),
            (
                "APARIENCIA",
                "tuiCliHeightPercent",
                "Proporción del CLI",
                "--tui-cli-percent",
                "15-75 %",
                "Porcentaje vertical reservado al CLI. ListElement siempre conserva como mínimo el 25% de las filas.",
            ),
            *tuple(
                (
                    "COLUMNAS",
                    f"tuiColumn.{name}",
                    name,
                    "--tui-column",
                    "caracteres" if name in {"IP", "MAC"} else "peso %",
                    (
                        f"Anchura fija de {name}; esta columna conserva todos sus caracteres."
                        if name in {"IP", "MAC"}
                        else f"Peso relativo de {name}. LANCTL aplica automáticamente sus límites mínimo y máximo."
                    ),
                )
                for name in DEFAULT_COLUMN_SPECS
            ),
            (
                "RED",
                "range",
                "Rango de red",
                "-range",
                "CIDR o vacío",
                "Red IPv4 que LANCTL analizará por defecto. Déjalo vacío para detectar la red desde la interfaz local.",
            ),
            (
                "RED",
                "dhcpRange",
                "Rango DHCP",
                "--dhcp-range",
                "INICIO-FIN u off",
                "Límites de direcciones entregadas dinámicamente por el servidor DHCP. Se usan para separar visualmente el inventario.",
            ),
            (
                "RED",
                "discovery",
                "Descubrimiento",
                "--discovery",
                "icmp | arp | hybrid",
                "Método base de descubrimiento: ICMP prueba respuesta, ARP consulta vecinos y hybrid combina ambos.",
            ),
            (
                "ESCANEO",
                "scanProfile",
                "Perfil de escaneo",
                "--scan-profile",
                "fast | normal | accurate",
                "Equilibra velocidad y profundidad. Accurate realiza más comprobaciones y puede tardar bastante más.",
            ),
            (
                "ESCANEO",
                "scanOrder",
                "Orden de escaneo",
                "--scan-order",
                "ascending | descending | random",
                "Orden en el que se prueban las direcciones del rango durante el descubrimiento.",
            ),
            (
                "ESCANEO",
                "workers",
                "Workers",
                "--workers",
                "entero positivo",
                "Número máximo de operaciones concurrentes. Un valor alto acelera el escaneo, pero consume más recursos.",
            ),
            (
                "ESCANEO",
                "timeout",
                "Timeout",
                "--timeout",
                "segundos",
                "Tiempo máximo de espera para cada operación de red antes de considerarla sin respuesta.",
            ),
            (
                "ESCANEO",
                "maxHosts",
                "Máximo de hosts",
                "--max-hosts",
                "entero positivo",
                "Límite de seguridad para impedir el escaneo accidental de redes excesivamente grandes.",
            ),
            (
                "ESCANEO",
                "progress",
                "Mostrar progreso",
                "--progress",
                "on | off",
                "Muestra u oculta la barra de progreso durante los escaneos interactivos.",
            ),
            (
                "ESCANEO",
                "serviceIdentification",
                "Identificar servicios",
                "--service-identification",
                "on | off",
                "Intenta reconocer servicios y protocolos expuestos por los dispositivos encontrados.",
            ),
            (
                "ESCANEO",
                "disconnectedRetention",
                "Retención al desconectar",
                "--disconnected-retention",
                "permanent | session | forget",
                "Decide si los elementos ausentes se conservan siempre, solo durante la sesión o se olvidan tras el escaneo.",
            ),
            (
                "ESCANEO",
                "disconnectedRetentionTarget",
                "Objetivo de retención",
                "--disconnected-target",
                "unconfirmed | all",
                "Limita la regla a elementos no reconocidos con CNF=X o la aplica a cualquier elemento desconectado.",
            ),
            (
                "ESCANEO",
                "disconnectedRetentionScope",
                "Alcance de retención",
                "--disconnected-scope",
                "all | dhcp",
                "Aplica la regla en toda la red o únicamente a direcciones incluidas en el rango DHCP configurado.",
            ),
            (
                "PROYECTOS",
                "projectsDirectory",
                "Directorio de proyectos",
                "--projects-directory",
                "ruta | auto",
                "Carpeta predeterminada para proyectos VLF. Auto utiliza Documents\\LanCTL del usuario actual.",
            ),
            (
                "PROYECTOS",
                "projectSaveMode",
                "Modo de guardado",
                "--save-mode",
                "SaveMode | list",
                "Política que decide cuándo se sincroniza el workspace activo con su archivo de proyecto VLF.",
            ),
            (
                "PROYECTOS",
                "projectSaveIntervalMinutes",
                "Intervalo de guardado",
                "--save-interval",
                "minutos",
                "Minutos entre guardados cuando SaveMode está configurado como automatic.timeToSave.",
            ),
            (
                "AVANZADO",
                "cliPromptSaveOnCommandExit",
                "Consultar guardado por comando",
                "--cli-exit-save-prompt",
                "on | off",
                "Pregunta si se guarda al finalizar cada comando lanzado desde CMD. Desactivado evita bloquear scripts y órdenes consecutivas.",
            ),
            (
                "AVANZADO",
                "cliCommandChaining",
                "Encadenar comandos CLI",
                "--cli-command-chaining",
                "on | off",
                "Permite ejecutar varias órdenes en una línea de la CLI interactiva separándolas con punto y coma.",
            ),
            (
                "ALMACENAMIENTO",
                "database",
                "Base de elementos",
                "--database",
                "ruta",
                "Archivo JSON que conserva el inventario de dispositivos, identidades, estados y datos descubiertos.",
            ),
            (
                "ALMACENAMIENTO",
                "physicalDatabase",
                "Base física LANWIRE",
                "--physical-database",
                "ruta SQLite",
                "Base física physical/idf.db administrada por LANWIRE; no se mezcla ni se abre como inventario JSON.",
            ),
            (
                "ALMACENAMIENTO",
                "groups",
                "Base de grupos",
                "--groups",
                "ruta",
                "Archivo que contiene los grupos y las relaciones entre estos y los elementos del inventario.",
            ),
            (
                "LOGS",
                "log",
                "Directorio de logs",
                "--log",
                "ruta",
                "Directorio donde LANCTL registra comandos, escaneos, cambios, plugins, resultados y errores.",
            ),
            (
                "LOGS",
                "logCleanupEnabled",
                "Limpieza de logs",
                "--log-cleanup",
                "on | off",
                "Activa la eliminación automática de registros que superen el periodo de retención configurado.",
            ),
            (
                "LOGS",
                "logRetentionDays",
                "Retención de logs",
                "--log-retention-days",
                "días",
                "Cantidad de días durante los que se conservarán los archivos de registro antes de poder eliminarlos.",
            ),
            (
                "LOGS",
                "errorLogLevel",
                "Nivel mínimo de errores",
                "--error-log-level",
                "entero 1-59",
                "Registra eventos con este nivel o superior; usa valores menores de 20 para diagnóstico detallado.",
            ),
            (
                "REMOTE ACCESS",
                "remoteAccessEnabled",
                "Acceso SSH remoto",
                "--remote-access",
                "on | off",
                "Activa el backend SSH restringido de LANCTL. No concede una shell del sistema operativo.",
            ),
            (
                "REMOTE ACCESS",
                "remoteAccessBind",
                "IP de enlace",
                "--remote-bind",
                "IPv4 local",
                "Dirección de la interfaz LAN en la que escuchará el servidor SSH remoto.",
            ),
            (
                "REMOTE ACCESS",
                "remoteAccessCidr",
                "Red permitida",
                "--remote-cidr",
                "CIDR",
                "Única red de origen autorizada para establecer conexiones con el backend.",
            ),
            (
                "REMOTE ACCESS",
                "remoteAccessPort",
                "Puerto SSH",
                "--remote-port",
                "1-65535",
                "Puerto TCP del servidor SSH restringido. El valor recomendado es 2222 para no colisionar con OpenSSH.",
            ),
            (
                "REMOTE ACCESS",
                "remoteAccessPasswordAuthentication",
                "Autenticación por contraseña",
                "--remote-password-auth",
                "on | off",
                "Permite contraseñas además de claves públicas. Por seguridad se recomienda mantenerla desactivada.",
            ),
            (
                "REMOTE ACCESS",
                "remoteAccessBackend",
                "Backend persistente",
                "--remote-backend",
                "service | user",
                "Service permanece activo sin abrir LANCTL; user permite lanzar ventanas visibles en la sesión del administrador.",
            ),
            (
                "REMOTE ACCESS",
                "remoteAccessForcedView",
                "Vista forzada predeterminada",
                "--remote-forced-view",
                "off | GUI | TUI | menú",
                "Vista que podrá solicitar el administrador remoto mediante root forced-view.",
            ),
            (
                "REMOTE ACCESS",
                "remoteAccessUsers",
                "Usuarios remotos",
                "",
                "Enter gestionar",
                "Abre la lista segura de usuarios SSH: permite crear cuentas, cambiar su contraseña y nivel de acceso, activarlas o eliminarlas.",
            ),
            *(
                (
                    "TECLADO",
                    f"tuiKey.{action}",
                    label,
                    "--tui-key",
                    "tecla disponible",
                    description,
                )
                for action, label, description in (
                    ("help", "Ayuda", "Atajo que abre la ayuda jerárquica del TUI."),
                    (
                        "info",
                        "Información",
                        "Atajo que abre la información del elemento seleccionado.",
                    ),
                    ("ping", "Ping", "Atajo que ejecuta un ping sobre el elemento seleccionado."),
                    (
                        "refresh",
                        "Actualizar",
                        "Atajo que vuelve a descubrir los elementos de la red.",
                    ),
                    ("plugins", "Plugins", "Atajo que abre el gestor de plugins."),
                    ("projects", "Proyectos", "Atajo que abre el gestor de proyectos."),
                    ("settings", "Settings", "Atajo que abre esta ventana de configuración."),
                    ("history", "Historial", "Atajo que abre el historial de comandos."),
                    ("search", "Buscar", "Prepara la búsqueda o filtrado de elementos."),
                    ("reload", "Recargar", "Recarga el inventario guardado sin escanear la red."),
                    ("edit", "Editar elemento", "Prepara la edición del elemento seleccionado."),
                    ("groups", "Gestionar grupos", "Prepara la gestión de grupos del inventario."),
                    (
                        "ports",
                        "Puertos",
                        "Abre directamente los puertos del elemento seleccionado.",
                    ),
                    ("open", "Abrir acceso", "Prepara la apertura de SSH, HTTP u otro protocolo."),
                    ("save", "Guardar proyecto", "Guarda manualmente el proyecto activo."),
                    (
                        "differences",
                        "Cambios pendientes",
                        "Indica si el proyecto activo contiene cambios sin guardar.",
                    ),
                    (
                        "copyLine",
                        "Copiar línea",
                        "Copia la fila completa seleccionada como texto tabulado.",
                    ),
                    (
                        "copyJson",
                        "Copiar JSON",
                        "Copia los campos principales de la selección como JSON.",
                    ),
                    (
                        "console",
                        "Consola",
                        "Limpia la salida y devuelve el foco al prompt del TUI.",
                    ),
                    ("quit", "Cierre seguro", "Inicia el cierre seguro de LANIP."),
                    (
                        "deviceHistory",
                        "Historial del elemento",
                        "Abre los eventos del elemento seleccionado.",
                    ),
                    (
                        "scanSelected",
                        "Escanear elemento",
                        "Prepara un análisis individual del elemento seleccionado.",
                    ),
                    (
                        "filterActive",
                        "Filtrar activos",
                        "Muestra únicamente los elementos activos del último escaneo.",
                    ),
                    (
                        "filterDisconnected",
                        "Filtrar desconectados",
                        "Muestra los elementos no detectados en el último escaneo.",
                    ),
                    ("filterAll", "Mostrar todos", "Elimina el filtro actual del inventario."),
                    ("ssh", "SSH", "Prepara una conexión SSH al elemento seleccionado."),
                    (
                        "terminal",
                        "Terminal del elemento",
                        "Prepara la terminal configurada del elemento seleccionado.",
                    ),
                    (
                        "credentials",
                        "Credenciales",
                        "Prepara la gestión de credenciales del elemento seleccionado.",
                    ),
                    (
                        "wakeOnLan",
                        "Wake-on-LAN",
                        "Prepara una acción Wake-on-LAN sobre el elemento seleccionado.",
                    ),
                    ("copyIp", "Copiar IP", "Copia únicamente la dirección IP seleccionada."),
                    ("copyMac", "Copiar MAC", "Copia únicamente la dirección MAC seleccionada."),
                    (
                        "projectStatus",
                        "Estado del proyecto",
                        "Muestra el estado y la política del proyecto activo.",
                    ),
                )
            ),
            *(
                (
                    "TECLADO",
                    f"tuiFooter.{action}",
                    f"Mostrar {label}",
                    "--tui-footer-button",
                    "on | off",
                    "Muestra u oculta este botón de ayuda en la última línea del TUI; la acción continúa disponible.",
                )
                for action, label in (
                    ("help", "Ayuda"),
                    ("info", "Información"),
                    ("ping", "Ping"),
                    ("refresh", "Actualizar"),
                    ("plugins", "Plugins"),
                    ("projects", "Proyectos"),
                    ("settings", "Settings"),
                    ("history", "Historial"),
                    ("search", "Buscar"),
                    ("reload", "Recargar"),
                    ("edit", "Editar"),
                    ("groups", "Grupos"),
                    ("ports", "Puertos"),
                    ("open", "Abrir acceso"),
                    ("save", "Guardar"),
                    ("differences", "Cambios"),
                    ("copyLine", "Copiar línea"),
                    ("copyJson", "Copiar JSON"),
                    ("console", "Consola"),
                    ("quit", "Cierre seguro"),
                    ("deviceHistory", "Historial elemento"),
                    ("scanSelected", "Escanear elemento"),
                    ("filterActive", "Solo activos"),
                    ("filterDisconnected", "Desconectados"),
                    ("filterAll", "Mostrar todos"),
                    ("ssh", "SSH"),
                    ("terminal", "Terminal"),
                    ("credentials", "Credenciales"),
                    ("wakeOnLan", "Wake-on-LAN"),
                    ("copyIp", "Copiar IP"),
                    ("copyMac", "Copiar MAC"),
                    ("projectStatus", "Estado proyecto"),
                    ("select", "Seleccionar"),
                    ("execute", "Ejecutar"),
                    ("exit", "Salir"),
                )
                if action in FOOTER_ACTIONS
            ),
        )
        fields = []
        for section, key, label, option, hint, description in definitions:
            # En TECLADO la asignación y la visibilidad son dos columnas de una
            # misma acción, no dos variables visuales independientes.
            if key.startswith("tuiFooter."):
                action = key.removeprefix("tuiFooter.")
                fixed_keys = {"select": "↑/↓", "execute": "Enter", "exit": "Esc"}
                if action not in fixed_keys:
                    continue
                visible = "ON" if action in footer_buttons else "OFF"
                fields.append(
                    SettingField(
                        f"tuiFixed.{action}",
                        label.removeprefix("Mostrar "),
                        "--tui-footer-button",
                        fixed_keys[action],
                        fixed_keys[action],
                        "tecla fija",
                        section,
                        description,
                        visible=visible,
                        original_visible=visible,
                    )
                )
                continue
            value = "Abrir lista…" if key == "remoteAccessUsers" else text(key)
            visible = None
            if key.startswith("tuiKey."):
                action = key.removeprefix("tuiKey.")
                visible = "ON" if action in footer_buttons else "OFF"
            fields.append(
                SettingField(
                    key,
                    label,
                    option,
                    value,
                    value,
                    hint,
                    section,
                    description,
                    visible=visible,
                    original_visible=visible,
                )
            )
        from lanctl.core.projects.save_policy import available_save_modes

        choices = {
            "discovery": ("icmp", "arp", "hybrid"),
            "scanProfile": ("fast", "normal", "accurate"),
            "scanOrder": ("ascending", "descending", "random"),
            "progress": ("on", "off"),
            "serviceIdentification": ("on", "off"),
            "disconnectedRetention": ("permanent", "session", "forget"),
            "disconnectedRetentionTarget": ("unconfirmed", "all"),
            "disconnectedRetentionScope": ("all", "dhcp"),
            "projectSaveMode": tuple(item.mode for item in available_save_modes()),
            "cliPromptSaveOnCommandExit": ("on", "off"),
            "cliCommandChaining": ("on", "off"),
            "logCleanupEnabled": ("on", "off"),
            "remoteAccessEnabled": ("on", "off"),
            "remoteAccessPasswordAuthentication": ("on", "off"),
            "remoteAccessBackend": ("service", "user"),
            "remoteAccessForcedView": ("off", "gui", "tui", "plugins", "projects", "settings"),
            "tuiPanelLayout": ("cli.bottom", "cli.top"),
        }
        for field in fields:
            field.choices = choices.get(field.key, ())
            if field.key.startswith("tuiKey."):
                field.choices = (
                    "None",
                    *(key.replace("_", "+") for key in CONFIGURABLE_TUI_KEYS),
                )
            elif field.key.startswith("tuiFooter."):
                field.choices = ("on", "off")
        tabs = [
            "GENERAL",
            "APARIENCIA",
            "COLUMNAS",
            "RED",
            "ESCANEO",
            "PROYECTOS",
            "ALMACENAMIENTO",
            "TECLADO",
            "LOGS",
            "REMOTE ACCESS",
            "EXIT",
        ]
        self._open_modal(
            ModalState(
                kind="settings",
                title="SETTINGS",
                tabs=tabs,
                pages=[[] for _ in tabs],
                items=fields,
                footer="←/→ menú  ↑/↓ variable  Tab editar  Esc salir",
            )
        )

    @staticmethod
    def _settings_exit_page(modal: ModalState) -> list[str]:
        changed = sum(
            field.value != field.original or field.visible != field.original_visible
            for field in modal.items
        )
        options = (
            "Salir y guardar",
            "Salir sin guardar",
            "Volver a configuración",
        )
        return [
            "",
            f"  Cambios pendientes: {changed}",
            "",
            *(
                f"  {'▶' if index == modal.selected else ' '} {label}"
                for index, label in enumerate(options)
            ),
            "",
            "  Selecciona cómo quieres cerrar la ventana de configuración.",
        ]

    def _open_settings_exit(self, modal: ModalState) -> None:
        if modal.editing:
            return
        modal.tab_selections[-1] = modal.tab_index
        modal.tab_index = modal.tabs.index("EXIT")
        modal.selected = 0
        modal.scroll = 0
        modal.footer = "↑/↓ seleccionar  Enter confirmar  Esc volver"

    def _leave_settings_exit(self, modal: ModalState) -> None:
        previous = modal.tab_selections.get(-1, max(0, modal.tab_index - 1))
        modal.tab_index = min(previous, max(0, len(modal.tabs) - 2))
        indices = self._settings_field_indices(modal)
        remembered = modal.tab_selections.get(modal.tab_index)
        modal.selected = remembered if remembered in indices else (indices[0] if indices else 0)
        modal.scroll = 0
        modal.footer = "←/→ menú  ↑/↓ variable  Tab editar  Esc salir"

    def _handle_settings_exit_key(self, modal: ModalState, key: str) -> None:
        if key in ("UP", "DOWN"):
            modal.selected = (modal.selected + (-1 if key == "UP" else 1)) % 3
        elif key in ("LEFT", "RIGHT", "ESC"):
            self._leave_settings_exit(modal)
        elif key == "ENTER":
            if modal.selected == 0:
                self._save_settings(modal)
            elif modal.selected == 1:
                self.modal = None
                self.messages = ["SETTINGS: cambios descartados."]
            else:
                self._leave_settings_exit(modal)

    def _remote_access_capture(self, arguments: list[str]) -> tuple[int, str]:
        """Ejecuta una acción de acceso sin dejar cambiado el ámbito del proceso TUI."""

        scope = str(load_config().get("remoteAccessBackend", "service")).casefold()
        previous = os.environ.get("LANCTL_DATA_SCOPE")
        try:
            return self._capture(["access", *arguments, "--scope", scope])
        finally:
            if previous is None:
                os.environ.pop("LANCTL_DATA_SCOPE", None)
            else:
                os.environ["LANCTL_DATA_SCOPE"] = previous

    def show_remote_users(self) -> None:
        result, output = self._remote_access_capture(["user", "list"])
        if result:
            self.messages = _clean_tui_output(output) or [
                "No se pudo abrir el almacén de usuarios."
            ]
            return
        try:
            users = json.loads(output)
        except json.JSONDecodeError:
            users = []
        rows = [
            f"{user['username']:<24} {','.join(user.get('roles', [])):<18} "
            f"{'ACTIVO' if user.get('enabled') else 'DESACTIVADO':<12} "
            f"{'CONFIGURADA' if user.get('passwordConfigured') else 'CLAVE/OTRO'}"
            for user in users
        ]
        if not rows:
            rows = ["No hay usuarios remotos. Pulsa N para crear el primero."]
        self._open_modal(
            ModalState(
                kind="remote_users",
                title="REMOTE ACCESS / USUARIOS",
                tabs=["Usuario / nivel de acceso"],
                pages=[rows],
                items=users,
                footer="N nuevo  P contraseña  R rol  E activar/desactivar  Supr eliminar  Esc volver",
            )
        )

    def _read_text(self, prompt: str) -> str:
        """Lee texto visible reutilizando la fila de entrada reservada del TUI."""

        read_key = self._dialog_key_reader()

        characters: list[str] = []
        try:
            while True:
                self.secret_prompt = prompt.strip() + " " + "".join(characters)
                self.render()
                key = read_key()
                if key == "ENTER":
                    return "".join(characters).strip()
                if key == "ESC":
                    return ""
                if key == "BACKSPACE":
                    if characters:
                        characters.pop()
                    continue
                if key == "DELETE":
                    characters.clear()
                    continue
                if len(key) == 1 and key.isprintable():
                    characters.append(key)
        finally:
            self.secret_prompt = ""
            self.render()

    def _begin_close(self) -> None:
        """Cierra directamente o solicita una decisión dentro del TUI."""

        from lanctl.core.projects.save_policy import (
            SaveMode,
            normalize_save_mode,
            workspace_is_dirty,
        )

        settings = load_config()
        mode = normalize_save_mode(str(settings.get("projectSaveMode", SaveMode.MANUAL.value)))
        active = str(settings.get("activeProject") or "").strip()
        if (
            mode != SaveMode.MANUAL_CLOSE_CONSULT.value
            or not active
            or not workspace_is_dirty(settings)
        ):
            self.running = False
            return
        self._open_modal(
            ModalState(
                kind="project_close",
                title="CAMBIOS SIN GUARDAR",
                tabs=["Cerrar proyecto"],
                pages=[
                    [
                        "Guardar las modificaciones y cerrar",
                        "Descartar las modificaciones y cerrar",
                    ]
                ],
                items=["save", "discard"],
                footer="←/→ o ↑/↓ seleccionar  Enter confirmar  Esc cancelar",
            )
        )

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
        rows = []
        for index, event in enumerate(self.history_events[:height]):
            marker = "▶" if index == self.history_index else " "
            label = event.device.label if event.device else "LAN"
            rows.append(
                f"{marker} {event.timestamp[:19]} | {label} | {event.type} | {event.summary}"
            )
        return [fit_text(line, width) for line in rows] or [" Sin eventos"]

    def show_history_detail(self) -> None:
        if not self.history_events:
            return
        event = self.history_events[self.history_index]
        device = event.device
        self.detail_lines = [
            f"Tipo: {event.type}",
            f"Fecha: {event.timestamp}",
            f"Elemento: {device.label if device else '-'}",
            f"Source: {event.source}",
            f"Resultado: {event.result}",
            f"CorrelationId: {event.correlationId or '-'}",
            f"RunId: {event.runId or '-'}",
            f"TaskId: {event.taskId or '-'}",
            f"OperationId: {event.operationId or '-'}",
            f"Resumen: {event.summary}",
            "Cambios:",
            *[f"  {x.get('field')}: {x.get('before')} => {x.get('after')}" for x in event.changes],
        ]
        if event.error:
            self.detail_lines.extend(
                (
                    f"Error: {event.error.get('code', '-')}",
                    f"Origen: {event.error.get('origin', '-')}",
                    f"Mensaje: {event.error.get('message', '-')}",
                )
            )

    def _render_detail(self, width: int, height: int) -> None:
        rows = max(1, height - 4)
        maximum = max(0, len(self.detail_lines) - rows)
        self.detail_scroll = max(0, min(self.detail_scroll, maximum))
        visible = self.detail_lines[self.detail_scroll : self.detail_scroll + rows]
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
        lines.append(
            f"{Style.BRIGHT}{Back.WHITE}{Fore.BLACK}{fit_text(footer, width):<{width}}{RESET}"
        )
        renderer = getattr(self, "renderer", None) or RichTuiRenderer(self.screen)
        renderer.render_screen(lines, width=width, height=height)

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
        from lanctl.apps.ip.interfaces.cli.main import main
        from lanctl.core.secret_input import use_secret_reader

        output = io.StringIO()
        try:
            with (
                use_secret_reader(self._read_secret),
                redirect_stdout(output),
                redirect_stderr(output),
            ):
                result = main(argv)
        except SystemExit as error:
            result = int(error.code or 0)
        return result, output.getvalue().strip()

    def _read_secret(self, prompt: str) -> str:
        """Solicita un secreto dentro de la fila de entrada reservada por el TUI."""

        read_key = self._dialog_key_reader()

        self.secret_prompt = prompt.strip()
        self.render()
        characters: list[str] = []
        try:
            while True:
                key = read_key()
                if key == "ENTER":
                    return "".join(characters)
                if key == "ESC":
                    raise KeyboardInterrupt
                if key == "BACKSPACE":
                    if characters:
                        characters.pop()
                    continue
                if key == "DELETE":
                    characters.clear()
                    continue
                if len(key) == 1 and key.isprintable():
                    characters.append(key)
        finally:
            self.secret_prompt = ""
            self.render()

    def _dialog_key_reader(self):
        """Devuelve el lector semántico activo en Windows o POSIX."""

        if callable(getattr(self, "_read_key", None)):
            return self._read_key
        if os.name == "nt":
            from msvcrt import getwch

            return lambda: _read_windows_key(getwch)
        return lambda: read_posix_key(sys.stdin)

    def refresh(self) -> None:
        """Inicia el descubrimiento sin bloquear teclado ni acciones remotas."""

        if self.scanning:
            self.messages = ["Ya hay un escaneo en curso. Pulsa Esc para cancelarlo."]
            return
        self.scanning = True
        self._scan_previous_state = (
            set(getattr(self, "active_devices", set())),
            dict(getattr(self, "response_ms", {})),
            dict(getattr(self, "scan_summary", {})),
        )
        self.spinner_index = 0
        self.scan_current = 0
        self.scan_total = 0
        self.scan_visible_devices = set()
        self.scan_summary = {}
        self.active_devices = set()
        self.scan_error = ""
        self.scan_error_after_discovery = False
        self.all_devices = self.database.load()
        self.devices = self._filtered_devices()
        self.messages = ["Buscando dispositivos en la LAN…"]
        self._scan_cancel = threading.Event()
        self._scan_thread = threading.Thread(
            target=self._run_refresh,
            name="lanctl-tui-scan",
            daemon=True,
        )
        self._scan_thread.start()

    def cancel_refresh(self) -> None:
        if self.scanning:
            self._scan_cancel.set()
            self.messages = ["Cancelando el escaneo de red…"]

    def _run_refresh(self) -> None:
        """Ejecuta el comando list en segundo plano y publica un resultado atómico."""

        from lanctl.apps.ip.interfaces.cli.main import build_parser

        captured_rows: list[dict] = []
        captured_activity: list[bool] = []
        output_buffer = io.StringIO()
        progress = _TuiScanProgress(self.scan_events, self._scan_cancel)
        try:
            args = build_parser().parse_args(["list", "--no-progress"])

            def collect_result(rows, activity) -> None:
                captured_rows.extend(rows)
                captured_activity.extend(activity)

            args.result_callback = collect_result
            args.progress_instance = progress
            args.scan_summary_callback = lambda summary: self.scan_events.put(
                ("summary", dict(summary))
            )
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                result = args.handler(args)
        except InterruptedError:
            result = 130
            output_buffer.write("Escaneo cancelado por el usuario.")
        except (OSError, RuntimeError, ValueError, sqlite3.DatabaseError, SystemExit) as error:
            result = int(error.code or 1) if isinstance(error, SystemExit) else 1
            if isinstance(error, SystemExit):
                output_buffer.write(str(error))
            else:
                from lanctl.core.errors import errors

                event = errors.from_exception(
                    error,
                    origin="LANCTL.TUI.Network.Scan",
                    code=(
                        "TUI.SCAN.POSTPROCESS_FAILED"
                        if progress.current >= progress.total
                        else "TUI.SCAN.DISCOVERY_FAILED"
                    ),
                    level=38,
                    details={
                        "discoveryCompleted": progress.current >= progress.total,
                        "found": len(self.scan_visible_devices),
                    },
                    print_output=False,
                )
                output_buffer.write(event.terminal_message())
        output = output_buffer.getvalue().strip()
        response_ms = {
            str(row.get("MAC") or row.get("IP")): float(row["responseMs"])
            for row in captured_rows
            if row.get("responseMs") is not None
        }
        active_devices = {
            _device_key(str(row.get("MAC", "")), str(row.get("IP", "")))
            for row, active in zip(captured_rows, captured_activity)
            if active
        }
        summary = _last_meaningful_line(output)
        self.scan_events.put(
            (
                "complete",
                result,
                summary,
                response_ms,
                active_devices,
                progress.current >= progress.total,
            )
        )

    def _drain_scan_events(self) -> bool:
        """Aplica eventos del worker exclusivamente desde el hilo de interfaz."""

        changed = False
        while True:
            try:
                event = self.scan_events.get_nowait()
            except queue.Empty:
                break
            changed = True
            kind, *payload = event
            if kind == "begin":
                self.scan_total = int(payload[0])
                self.scan_current = 0
            elif kind == "advance":
                self.scan_current = int(payload[0])
                self.spinner_index = (self.spinner_index + 1) % 4
            elif kind == "found":
                self.discovery_found(tuple(payload[0]))
            elif kind == "summary":
                self.scan_summary.update(payload[0])
            elif kind == "complete":
                result, summary, response_ms, active_devices, discovery_completed = payload
                self.scanning = False
                self.scan_current = 0
                self.scan_total = 0
                if result == 0:
                    self.response_ms = response_ms
                    self.active_devices = active_devices
                    self.scan_error = ""
                    self.scan_error_after_discovery = False
                else:
                    previous = getattr(self, "_scan_previous_state", None)
                    if previous is not None:
                        self.active_devices, self.response_ms, self.scan_summary = previous
                    self.scan_error = summary or "Error al actualizar la LAN."
                    self.scan_error_after_discovery = bool(discovery_completed)
                self._scan_previous_state = None
                self.reload()
                self.messages = (
                    ["Escaneo completado. Pulsa F5 para actualizar de nuevo."]
                    if result == 0
                    else [
                        self.scan_error,
                        (
                            "El descubrimiento terminó, pero falló su procesamiento o guardado. "
                            "Se conserva el último estado válido."
                            if discovery_completed
                            else "El descubrimiento no terminó. Se conserva el último estado válido."
                        ),
                    ]
                )
        return changed

    def show_info(self) -> None:
        device = self.selected
        if not device:
            self.messages = ["No hay ningun elemento seleccionado."]
            return
        self.messages = ["Obteniendo informacion completa del elemento..."]
        self.render()
        _result, output = self._capture(
            [
                "scan",
                device.mac or device.ip,
                "--identify",
                "--banners",
                "--json",
            ]
        )
        try:
            payload = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        element = payload.get("element")
        if not isinstance(element, dict):
            element = {}
        observation = payload.get("observation", {})
        if not isinstance(observation, dict):
            observation = {}
        identification = observation.get("identification", {}) or {}
        if not isinstance(identification, dict):
            identification = {}
        match = observation.get("identityMatch")

        def shown(value) -> str:
            return "-" if value in (None, "", [], {}) else str(value)

        identity = [
            f"  Estado: {'ACTIVO' if observation.get('reachable') else 'NO DETECTADO'}",
            f"  ID estable: {shown(device.device_id)}",
            f"  IP registrada: {shown(device.ip)}",
            f"  MAC registrada: {shown(device.mac)}",
            f"  MAC observada: {shown(observation.get('observed_mac'))}",
            f"  Coincidencia: {'Si' if match is True else 'NO' if match is False else '-'}",
        ]
        identity_fields = [
            SettingField(
                "cnf", "CNF", "-cnf", device.cnf, device.cnf,
                "O, X, -, S o F", "Identidad",
                "Estado de reconocimiento del elemento.", ("O", "X", "-", "S", "F"),
            ),
            SettingField(
                "alias", "ALIAS", "-alias", device.alias, device.alias,
                "texto único", "Identidad", "Alias corto asignado por el usuario.",
            ),
            SettingField(
                "name", "NAME", "-name", device.name, device.name,
                "texto", "Identidad", "Nombre legible del elemento.",
            ),
            SettingField(
                "description", "DESCRIPTION", "-description", device.description, device.description,
                "máximo 42", "Identidad", "Descripción breve del elemento.",
            ),
            SettingField(
                "idf", "IDF", "-idf", getattr(device, "idf", ""), getattr(device, "idf", ""),
                "AB-12 a ABCDE-12345", "Identidad",
                "Identificador físico manual y único, compartido conceptualmente con LANWIRE.",
            ),
            SettingField(
                "group", "AÑADIR GRUPO", "-group", "", "",
                "nombre de grupo", "Clasificación",
                "Añade el elemento a un grupo; los existentes aparecen debajo.",
            ),
            SettingField(
                "ip", "IP", "-ip", device.ip, device.ip,
                "IPv4 única", "Red", "Dirección IPv4 registrada para este elemento.",
            ),
            SettingField(
                "protocol", "PROTOCOLO", "-protocol", "", "",
                "ssh o del ssh", "Accesos",
                "Activa un protocolo; escribe del NOMBRE para desactivarlo.",
            ),
        ]
        classification = [
            f"  Alias: {shown(device.alias)}",
            f"  Alias detectado: {shown(device.default_alias)}",
            f"  Nombre: {shown(device.name)}",
            f"  Hostname detectado: {shown(observation.get('hostname') or device.default_name)}",
            f"  Descripcion: {shown(device.description)}",
            f"  Fabricante: {shown(element.get('manufacturer') or device.manufacturer)}",
            f"  Tipo probable: {shown(identification.get('device_type'))}",
            f"  Confianza: {shown(identification.get('confidence'))}",
            f"  Evidencias: {shown('; '.join(identification.get('evidence', [])))}",
            f"  Grupos: {shown(', '.join(device.groups))}",
        ]
        network = [
            f"  Latencia: {shown(observation.get('latency_ms'))} ms",
            f"  TTL: {shown(observation.get('ttl'))}",
            f"  Detectado por: {shown('+'.join(device.discovery_methods) or device.last_discovery)}",
            f"  Ultima deteccion: {shown(device.last_discovery)}",
            f"  Ultima vez visto: {shown(device.last_seen)}",
        ]
        access = [
            f"  Protocolos: {shown(', '.join(device.protocols))}",
            f"  Credenciales referenciadas: {shown(', '.join(f'{key}={value}' for key, value in device.credentials.items()))}",
            f"  Opciones de protocolo: {shown(json.dumps(device.protocol_options, ensure_ascii=False, sort_keys=True))}",
        ]
        open_ports = observation.get("open_ports", []) or []
        ports = [
            f"  Puertos abiertos: {len(observation.get('open_ports', []))}",
            f"  Puertos examinados: {shown(observation.get('scanned_ports'))}",
            f"  Duracion del analisis: {shown(observation.get('duration'))} s",
        ]
        if open_ports:
            ports.extend(["", "  PUERTO  SERVICIO       PRODUCTO / BANNER"])
            for item in open_ports:
                if isinstance(item, dict):
                    port = shown(item.get("port"))
                    service = shown(item.get("service"))
                    product = shown(item.get("product") or item.get("banner"))
                else:
                    port, service, product = shown(item), "-", "-"
                ports.append(f"  {port:<7} {service:<14} {product}")
        else:
            ports.extend(["", "  Ningún puerto abierto detectado."])
        self._open_modal(
            ModalState(
                kind="info",
                title=f"INFO · {device.alias or device.name or device.ip or device.mac}",
                tabs=["Identidad", "Clasificación", "Red", "Accesos", "Puertos"],
                pages=[identity, classification, network, access, ports],
                items=identity_fields,
                footer="←/→ sección  ↑/↓ campo  Tab editar  F2/Esc cerrar",
                max_width=90,
                max_height=30,
            )
        )

    def ping_selected(self) -> None:
        device = self.selected
        if not device:
            self.messages = ["No hay ningún elemento seleccionado para comprobar."]
            return
        result, output = self._capture(["ping", device.mac or device.ip])
        if result == 0:
            self.active_devices.add(_device_key(device.mac, device.ip))
        self.reload()
        if output:
            self._set_command_output(output, result)
        else:
            self.messages = ["Ping completado." if result == 0 else "El elemento no ha respondido."]

    def _set_command_output(self, output: str, result: int) -> None:
        self.messages = _clean_tui_output(output) if output else [f"Código de salida: {result}"]
        self.output_selectable = _selectable_output_indexes(self.messages)
        self.output_focus = bool(self.output_selectable)
        self.output_index = 0
        self.output_scroll = 0

    def _set_terminal_message(self, message: str) -> None:
        """Publica un aviso y restablece cualquier selección anterior del panel CLI."""
        self.messages = [message]
        self.output_focus = False
        self.output_selectable = []
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
            from lanctl.core.command_line import split_command_line

            parts = split_command_line(raw)
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
            self._begin_close()
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
                    'Proyecto: project | project status | project use "RUTA.vlf" | help project.',
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
            if any(part.casefold() in ("-recurrent", "--recurrent") for part in parts[1:]):
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
            self.show_history(parts[1] if len(parts) > 1 else None)
            return
        if command == "select" and len(parts) == 2:
            try:
                wanted = self.database.resolve(parts[1])
                if not any(item.mac == wanted.mac for item in self.devices):
                    self.list_filter = ("all", "")
                    self.reload()
                self.index = next(
                    i for i, item in enumerate(self.devices) if item.mac == wanted.mac
                )
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
                    self.selected.mac,
                    self.selected.ip,
                    self.selected.alias,
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
        if (
            self.selected
            and command
            in {
                "call",
                "cnf",
                "credential",
                "open",
                "ping",
                "protocol",
                "scan",
                "search",
                "ssh",
                "switch",
                "terminal",
                "wol",
            }
            and (len(contextual) == 1 or contextual[1].startswith("-"))
        ):
            contextual.insert(1, self.selected.mac or self.selected.ip)
        result, output = self._capture(contextual)
        self.reload()
        self._set_command_output(output, result)

    def _action_for_key(self, key: str) -> str | None:
        bindings = getattr(self, "key_bindings", DEFAULT_TUI_KEY_BINDINGS)
        return next((action for action, assigned in bindings.items() if assigned == key), None)

    def _manual_save(self) -> None:
        from lanctl.core.projects.save_policy import (
            SaveTrigger,
            save_active_project,
            workspace_is_dirty,
        )

        settings = {}
        try:
            settings = load_config()
            had_changes = workspace_is_dirty(settings)
            result = save_active_project(SaveTrigger.CHANGE, force=True, config=settings)
        except (OSError, RuntimeError, ValueError, sqlite3.DatabaseError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.TUI.Project.Save",
                code="PROJECT.SAVE.MANUAL_FAILED",
                level=38,
                details={"project": str(settings.get("activeProject") or "")},
                print_output=False,
            )
            self._set_terminal_message(f"No se pudo guardar el proyecto: {error}")
            return
        if result.saved:
            self.reload()
            state = "cambios aplicados" if had_changes else "sin cambios pendientes"
            self._set_terminal_message(f"Proyecto guardado correctamente: {result.path} ({state}).")
        elif result.reason == "no-active-project":
            self._set_terminal_message("No hay ningún proyecto activo que guardar.")
        else:
            self._set_terminal_message(f"El proyecto no necesitó guardarse: {result.reason}.")

    def _selected_clipboard_payload(self) -> dict[str, str]:
        device = self.selected
        if not device:
            return {}
        return {
            "idf": getattr(device, "idf", ""),
            "mac": device.mac,
            "ip": device.ip,
            "cnf": device.cnf,
            "alias": device.alias,
            "name": device.name,
            "group": ",".join(device.groups),
            "description": device.description,
        }

    def _copy_selected(self, *, as_json: bool) -> None:
        payload = self._selected_clipboard_payload()
        if not payload:
            self.messages = ["No hay ningún elemento seleccionado para copiar."]
            return
        value = (
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            if as_json
            else "\t".join(
                payload[key] or "-"
                for key in ("ip", "cnf", "alias", "mac", "name", "group", "description")
            )
        )
        try:
            from lanctl.apps.ip.interfaces.tui.clipboard import copy_text

            copy_text(value)
        except (MemoryError, OSError) as error:
            self.messages = [f"No se pudo copiar al portapapeles: {error}"]
            return
        label = self.selected.alias or self.selected.ip or self.selected.mac
        self.messages = [f"{'JSON' if as_json else 'Línea'} copiado: {label}"]

    def _prepare_shortcut_command(self, command: str, message: str) -> None:
        self.output_focus = False
        self.output_selectable = []
        self.command_suggestions = []
        self.suggestion_index = -1
        self.command = command
        self.cursor = len(command)
        self.messages = [message]

    def _copy_selected_field(self, field: str) -> None:
        payload = self._selected_clipboard_payload()
        value = payload.get(field, "")
        if not value:
            self.messages = [f"El elemento seleccionado no tiene {field.upper()} disponible."]
            return
        try:
            from lanctl.apps.ip.interfaces.tui.clipboard import copy_text

            copy_text(value)
        except (MemoryError, OSError) as error:
            self.messages = [f"No se pudo copiar al portapapeles: {error}"]
            return
        self.messages = [f"{field.upper()} copiada: {value}"]

    def _show_ports(self) -> None:
        self.show_info()
        if self.modal and self.modal.kind == "info" and "Puertos" in self.modal.tabs:
            self.modal.tab_index = self.modal.tabs.index("Puertos")
            self.modal.scroll = 0

    def _show_pending_changes(self) -> None:
        from lanctl.core.projects.save_policy import workspace_is_dirty

        settings = load_config()
        active = str(settings.get("activeProject") or "").strip()
        if not active:
            self.messages = ["No hay ningún proyecto activo."]
        elif workspace_is_dirty(settings):
            self.messages = ["El proyecto activo contiene cambios pendientes de guardar."]
        else:
            self.messages = ["El proyecto activo está sincronizado; no hay cambios pendientes."]

    def _focus_console(self) -> None:
        self.output_focus = False
        self.output_selectable = []
        self.output_index = 0
        self.output_scroll = 0
        self.command_suggestions = []
        self.command = ""
        self.cursor = 0
        self.messages = ["Consola preparada."]

    def handle_key(self, key: str) -> None:
        if getattr(self, "scanning", False) and key == "ESC" and not self.modal:
            self.cancel_refresh()
            return
        if getattr(self, "modal", None):
            # Settings conserva su guardado específico. En los demás overlays,
            # Ctrl+S sigue siendo el guardado manual global del proyecto.
            if key == "CTRL_S" and self.modal.kind not in {
                "settings",
                "remote_users",
                "project_close",
            }:
                active_modal = self.modal
                self._manual_save()
                if self.modal is active_modal:
                    if active_modal.kind == "projects":
                        self._update_manager_detail(active_modal)
                    confirmation = self.messages[-1] if self.messages else "Guardado completado."
                    active_modal.footer = f"{confirmation} · Esc cerrar"
                return
            self._handle_modal_key(key)
            return
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
            if key in ("UP", "PGUP"):
                self.history_index = max(0, self.history_index - (10 if key == "PGUP" else 1))
            elif key in ("DOWN", "PGDN"):
                self.history_index = min(
                    max(0, len(self.history_events) - 1),
                    self.history_index + (10 if key == "PGDN" else 1),
                )
            elif key == "ENTER":
                self.show_history_detail()
            elif key == "F5":
                self.show_history(
                    "all" if self.history_events and not self.history_events[0].device else None
                )
            elif key == "ESC":
                self.view_state = "inventory"
                self.messages = ["Inventario restaurado"]
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
        # La ayuda interactiva toma el foco vertical completo: mientras sus
        # sugerencias estén visibles, la selección superior no debe moverse.
        if key in ("UP", "DOWN") and getattr(self, "command_suggestions", []):
            self._move_suggestion(-1 if key == "UP" else 1)
            return
        if key == "TAB":
            self.cycle_list_view()
            return
        action = self._action_for_key(key)
        if key == "UP":
            self.move(-1)
        elif key == "DOWN":
            self.move(1)
        elif key == "PGUP":
            self.move(-10)
        elif key == "PGDN":
            self.move(10)
        elif action == "help":
            self.show_help_modal()
        elif action == "info":
            self.show_info()
        elif action == "ping":
            self.ping_selected()
        elif action == "refresh":
            self.refresh()
        elif action == "plugins":
            self.show_plugin_manager()
        elif action == "projects":
            self.show_project_manager()
        elif action == "settings":
            self.show_settings()
        elif action == "history":
            self.show_command_history()
        elif action == "search":
            self._prepare_shortcut_command("search ", "Buscar: escribe texto, IP, MAC o alias.")
        elif action == "reload":
            self.reload()
            self.messages = ["Inventario recargado sin ejecutar un escaneo."]
        elif action == "edit":
            self._prepare_shortcut_command(
                "element ",
                "Editar: completa una opción; se aplicará al elemento seleccionado.",
            )
        elif action == "groups":
            self._prepare_shortcut_command(
                "group ",
                "Grupos: indica el grupo y la acción; se usará el elemento seleccionado.",
            )
        elif action == "ports":
            self._show_ports()
        elif action == "open":
            self._prepare_shortcut_command(
                "open ",
                "Abrir acceso: escribe ssh, http, https, telnet u otro protocolo.",
            )
        elif action == "save":
            self._manual_save()
        elif action == "differences":
            self._show_pending_changes()
        elif action == "copyLine":
            self._copy_selected(as_json=False)
        elif action == "copyJson":
            self._copy_selected(as_json=True)
        elif action == "console":
            self._focus_console()
        elif action == "quit":
            self._begin_close()
        elif action == "deviceHistory":
            self.show_history()
        elif action == "scanSelected":
            self._prepare_shortcut_command(
                "scan ", "Escanear elemento: añade opciones o pulsa Enter para comenzar."
            )
        elif action == "filterActive":
            self.configure_list(["--active"])
        elif action == "filterDisconnected":
            self.configure_list(["--disconnected"])
        elif action == "filterAll":
            self.configure_list(["--all"])
        elif action == "ssh":
            self._prepare_shortcut_command(
                "ssh ", "SSH: indica probe, fingerprint, trust, open o show."
            )
        elif action == "terminal":
            self._prepare_shortcut_command(
                "terminal ", "Terminal: pulsa Enter o añade las opciones necesarias."
            )
        elif action == "credentials":
            self._prepare_shortcut_command(
                "credential ", "Credenciales: indica set, list o configure."
            )
        elif action == "wakeOnLan":
            self._prepare_shortcut_command(
                "wol ", "Wake-on-LAN: indica wakeup, status, schedule u otra acción."
            )
        elif action == "copyIp":
            self._copy_selected_field("ip")
        elif action == "copyMac":
            self._copy_selected_field("mac")
        elif action == "projectStatus":
            result, output = self._capture(["project", "status"])
            self._set_command_output(output, result)
        elif key == "ENTER":
            self.execute()
        elif key == "BACKSPACE":
            self._clear_suggestions()
            if self.cursor:
                self.command = self.command[: self.cursor - 1] + self.command[self.cursor :]
                self.cursor -= 1
        elif key == "DELETE":
            self._clear_suggestions()
            self.command = self.command[: self.cursor] + self.command[self.cursor + 1 :]
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
            self._begin_close()
        elif len(key) == 1 and key.isprintable():
            self._clear_suggestions()
            self.command = self.command[: self.cursor] + key + self.command[self.cursor :]
            self.cursor += 1

    def _handle_modal_key(self, key: str) -> None:
        modal = self.modal
        if not modal:
            return
        if modal.kind == "help":
            self._handle_help_key(modal, key)
            return
        if modal.kind == "settings":
            self._handle_settings_key(modal, key)
            return
        if modal.kind == "remote_users":
            self._handle_remote_users_key(modal, key)
            return
        if modal.kind == "project_close":
            self._handle_project_close_key(modal, key)
            return
        if modal.kind == "project_switch":
            self._handle_project_switch_key(modal, key)
            return
        if modal.kind == "project_create":
            self._handle_project_create_key(modal, key)
            return
        if modal.kind == "info":
            self._handle_info_key(modal, key)
            return
        if key in ("ESC", "F1") and not (key == "F1" and modal.kind != "help"):
            self.modal = None
            return
        if key == "LEFT":
            modal.change_tab(-1)
        elif key == "RIGHT":
            modal.change_tab(1)
        elif (
            key in ("UP", "DOWN")
            and modal.kind in {"plugins", "projects", "commands"}
            and modal.tab_index == 0
        ):
            delta = -1 if key == "UP" else 1
            ManagerController.move(modal, delta, self._update_manager_detail)
        elif key == "UP":
            modal.scroll -= 1
        elif key == "DOWN":
            modal.scroll += 1
        elif key == "PGUP":
            modal.scroll -= 10
        elif key == "PGDN":
            modal.scroll += 10
        elif key == "ENTER" and modal.kind == "commands" and self.command_history:
            self.command = self.command_history[modal.selected]
            self.cursor = len(self.command)
            self.modal = None
            self.messages = ["Comando recuperado; pulsa Enter para ejecutarlo."]
        elif key == "ENTER" and modal.kind == "projects" and modal.items:
            item = modal.items[modal.selected]
            path = item.path
            if not item.available:
                self.messages = [f"El proyecto ya no está disponible: {path}"]
                return
            self._request_project_activation(path)
        elif modal.kind == "projects" and key == "CTRL_N":
            self._create_project_from_manager()
        elif modal.kind == "projects" and key == "DELETE" and modal.items:
            self._delete_project_from_manager(modal.items[modal.selected])
        elif key == "CTRL_R":
            if modal.kind == "plugins":
                self.show_plugin_manager()
            elif modal.kind == "projects":
                self.show_project_manager()

    def _handle_info_key(self, modal: ModalState, key: str) -> None:
        """Edita la identidad visible sin confundir el IDF con el UUID interno."""

        if key == "F2" and not modal.editing:
            self.modal = None
            return
        if modal.tabs[modal.tab_index] == "Puertos":
            if key in ("ESC", "F2"):
                self.modal = None
            elif key == "LEFT":
                modal.change_tab(-1)
            elif key == "RIGHT":
                modal.change_tab(1)
            elif key == "UP":
                modal.scroll -= 1
            elif key == "DOWN":
                modal.scroll += 1
            elif key == "PGUP":
                modal.scroll -= 10
            elif key == "PGDN":
                modal.scroll += 10
            return

        # F2 durante una edición equivale a cancelar el valor en curso; evita
        # cerrar la ficha y perder de forma silenciosa lo que se estaba tecleando.
        effective_key = "ESC" if key == "F2" and modal.editing else key
        field = modal.items[modal.selected]
        was_editing = modal.editing
        previous_value = field.value
        SettingsEditor.handle_key(
            modal,
            effective_key,
            close=lambda: setattr(self, "modal", None),
            open_remote_users=lambda: None,
        )
        if not (was_editing and effective_key in ("TAB", "SHIFT_TAB") and not modal.editing):
            return
        if field.value == field.original:
            return

        device = self.selected
        selector = device.device_id or device.mac or device.ip
        try:
            if field.key == "group":
                from lanctl.core.config import load_config
                from lanctl.core.group_database import GroupDatabase

                _, updated = GroupDatabase(load_config()["groups"], self.database).add(
                    field.value, selector
                )
            elif field.key == "protocol":
                parts = field.value.split()
                if not parts:
                    raise ValueError("indica un protocolo")
                remove = len(parts) == 2 and parts[0].casefold() in {"del", "delete", "remove"}
                if len(parts) > 2 or (len(parts) == 2 and not remove):
                    raise ValueError("usa NOMBRE o del NOMBRE")
                updated = self.database.set_protocol(selector, parts[-1], not remove)
            else:
                updated = self.database.edit_device(selector, field.key, field.value)
        except (KeyError, OSError, ValueError) as error:
            field.value = previous_value
            modal.footer = f"No se pudo guardar: {error} · Tab editar · F2/Esc cerrar"
            return
        if field.key == "group":
            modal.pages[1] = [
                f"  Grupos: {', '.join(updated.groups) or '-'}"
                if line.startswith("  Grupos:") else line
                for line in modal.pages[1]
            ]
        elif field.key == "protocol":
            modal.pages[3] = [
                f"  Protocolos: {', '.join(updated.protocols) or '-'}"
                if line.startswith("  Protocolos:") else line
                for line in modal.pages[3]
            ]
        if field.key in {"group", "protocol"}:
            field.value = field.original = ""
            device.groups = updated.groups
            device.protocols = updated.protocols
        else:
            field.original = field.value
            setattr(device, field.key, getattr(updated, field.key))
        modal.footer = f"{field.label} guardado · ←/→ sección  ↑/↓ campo  Tab editar  F2/Esc cerrar"

    def _create_project_from_manager(self) -> None:
        from lanctl.core.projects.paths import default_project_directory
        from lanctl.core.projects.save_policy import workspace_is_dirty

        if getattr(self, "scanning", False):
            if self.modal:
                self.modal.footer = "Cierra esta ventana y pulsa Esc para cancelar el escaneo antes de crear un proyecto"
            return
        if workspace_is_dirty(load_config()):
            if self.modal:
                self.modal.footer = (
                    "Hay cambios pendientes · Ctrl+S guardar antes de crear otro proyecto"
                )
            return

        configured = load_config().get("projectsDirectory")
        default_root = (
            Path(os.path.expandvars(str(configured))).expanduser()
            if configured
            else default_project_directory()
        )
        fields = [
            SettingField(
                "name",
                "Nombre",
                "",
                "",
                "",
                "Nombre del proyecto y del archivo VLF.",
                "PROJECT",
            ),
            SettingField(
                "path",
                "Ruta",
                "",
                str(default_root),
                str(default_root),
                "Directorio donde se guardará el proyecto.",
                "PROJECT",
            ),
            SettingField(
                "description",
                "Descripción",
                "",
                "",
                "",
                "Descripción opcional del proyecto.",
                "PROJECT",
            ),
        ]
        self._open_modal(
            ModalState(
                kind="project_create",
                title="PROJECT MANAGER / NUEVO PROYECTO",
                tabs=["Datos"],
                pages=[[]],
                items=fields,
                editing=True,
                editor_fresh=True,
                footer="escribir editar  Enter siguiente/crear  ↑/↓ campo  Esc cancelar",
                max_width=120,
            )
        )

    @staticmethod
    def _project_create_page(modal: ModalState) -> list[str]:
        rows = [
            "  CAMPO                      VALOR",
            "  ─────────────────────────  ─────────────────────────────────────────────────────────────",
        ]
        for index, field in enumerate(modal.items):
            marker = "▶" if index == modal.selected else " "
            placeholder = {
                "name": "(escribe un nombre)",
                "path": "(indica una ruta)",
            }.get(field.key, "(opcional)")
            rows.append(f"{marker} {field.label:<25} {fit_text(field.value or placeholder, 62)}")
        selected = modal.items[modal.selected]
        rows.extend(("", "  DESCRIPCIÓN", f"  {selected.description}"))
        return rows

    def _handle_project_create_key(self, modal: ModalState, key: str) -> None:
        if key == "ESC":
            self.show_project_manager()
            return
        if key in ("UP", "DOWN", "TAB", "SHIFT_TAB"):
            backwards = key in ("UP", "SHIFT_TAB")
            modal.selected = (modal.selected + (-1 if backwards else 1)) % len(modal.items)
            modal.editor_fresh = True
            return
        field = modal.items[modal.selected]
        if key == "ENTER":
            if modal.selected < len(modal.items) - 1:
                modal.selected += 1
                modal.editor_fresh = True
            else:
                self._submit_project_creation(modal)
            return
        if key == "BACKSPACE":
            field.value = field.value[:-1]
            modal.editor_fresh = False
        elif key == "DELETE":
            field.value = ""
            modal.editor_fresh = False
        elif len(key) == 1 and key.isprintable():
            field.value = key if modal.editor_fresh else field.value + key
            modal.editor_fresh = False

    def _submit_project_creation(self, modal: ModalState) -> None:
        from lanctl.core.projects.catalog import ProjectCatalog
        from lanctl.core.projects.vlf import create_project
        from lanctl.core.projects.workspace import activate_project_workspace

        values = {field.key: field.value.strip() for field in modal.items}
        name = values["name"]
        if not name:
            modal.selected = 0
            modal.footer = "ERROR: escribe un nombre · Enter siguiente  Esc cancelar"
            return
        if any(character in name for character in '<>:"/\\|?*'):
            modal.selected = 0
            modal.footer = "ERROR: el nombre contiene caracteres no válidos · Esc cancelar"
            return
        directory_text = values["path"]
        if not directory_text:
            modal.selected = 1
            modal.footer = "ERROR: indica la ruta del proyecto · Esc cancelar"
            return
        directory = Path(os.path.expandvars(directory_text)).expanduser()
        description = values["description"]
        destination = directory / (name if name.casefold().endswith(".vlf") else f"{name}.vlf")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            # No heredar el inventario ni los grupos del proyecto activo.
            with tempfile.TemporaryDirectory(prefix="lanctl-project-create-") as temporary:
                empty_config = dict(load_config())
                empty_config["database"] = str(Path(temporary) / "devices.json")
                empty_config["groups"] = str(Path(temporary) / "groups.json")
                result = create_project(
                    destination,
                    name=Path(name).stem,
                    description=description,
                    config=empty_config,
                    initialize_reserved=False,
                )
            path = Path(result["path"])
            ProjectCatalog().register(path)
            activate_project_workspace(path)
            from lanctl.core.logger import write_log
            from lanctl.core.plugins import get_plugin_manager

            project_id = str(result.get("project", {}).get("id") or "")
            get_plugin_manager().events.emit(
                "LANCTL.Project.File.Open",
                {"path": str(path), "project_id": project_id or None},
            )
            write_log(f"PROJECT CREATE id={project_id or '-'} path={path} source=TUI")
            self.reload()
            self.messages = [f"Proyecto creado y activado: {path}"]
            self.show_project_manager()
        except (OSError, ValueError, sqlite3.DatabaseError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.TUI.ProjectManager.Create",
                code="PROJECT.MANAGER.CREATE_FAILED",
                level=34,
                details={"project": str(destination)},
                print_output=False,
            )
            self.messages = [f"No se pudo crear el proyecto: {error}"]

    def _delete_project_from_manager(self, item) -> None:
        from lanctl.core.projects.catalog import ProjectCatalog

        path = item.path.resolve()
        active = str((self.project_info or {}).get("path") or "")
        if active and str(path).casefold() == str(Path(active).resolve()).casefold():
            self.messages = [
                "No se puede eliminar el proyecto activo; activa otro proyecto primero."
            ]
            return
        confirmation = self._read_text(f"Escribe ELIMINAR para borrar {item.name}:")
        if confirmation != "ELIMINAR":
            self.messages = ["Eliminación cancelada."]
            return
        try:
            ProjectCatalog().remove(path, delete_file=True)
            from lanctl.core.logger import write_log
            from lanctl.core.plugins import get_plugin_manager

            get_plugin_manager().events.emit(
                "LANCTL.Project.File.Close",
                {"path": str(path), "project_id": item.project_id or None},
            )
            write_log(f"PROJECT DELETE id={item.project_id or '-'} path={path} source=TUI")
            self.messages = [f"Proyecto eliminado: {path}"]
            self.show_project_manager()
        except (OSError, sqlite3.DatabaseError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.TUI.ProjectManager.Delete",
                code="PROJECT.MANAGER.DELETE_FAILED",
                level=38,
                details={"project": str(path)},
                print_output=False,
            )
            self.messages = [f"No se pudo eliminar el proyecto: {error}"]

    def _handle_help_key(self, modal: ModalState, key: str) -> None:
        if key in ("ESC", "F1"):
            self.modal = None
            return
        if key in ("LEFT", "RIGHT"):
            modal.change_tab(-1 if key == "LEFT" else 1)
            return
        if modal.tab_index != 0:
            if key == "UP":
                modal.scroll -= 1
            elif key == "DOWN":
                modal.scroll += 1
            elif key == "PGUP":
                modal.scroll -= 10
            elif key == "PGDN":
                modal.scroll += 10
            elif key == "HOME":
                modal.scroll = 0
            elif key == "TAB" and modal.items:
                self._prepare_help_command(modal)
            return
        if not modal.items:
            return
        if key in ("UP", "DOWN", "PGUP", "PGDN", "HOME", "END"):
            if key == "HOME":
                modal.selected = 0
            elif key == "END":
                modal.selected = len(modal.items) - 1
            else:
                step = 10 if key in ("PGUP", "PGDN") else 1
                delta = -step if key in ("UP", "PGUP") else step
                modal.selected = max(0, min(len(modal.items) - 1, modal.selected + delta))
            modal.pages[1] = _help_command_detail(modal.items[modal.selected])
            modal.scroll = max(0, modal.selected - 5)
        elif key == "ENTER":
            modal.pages[1] = _help_command_detail(modal.items[modal.selected])
            modal.tab_index = 1
            modal.scroll = 0
        elif key == "TAB":
            self._prepare_help_command(modal)

    def _prepare_help_command(self, modal: ModalState) -> None:
        entry = modal.items[modal.selected]
        self.command = f"{entry.name} "
        self.cursor = len(self.command)
        self.modal = None
        self.messages = [f"Comando preparado: {entry.name}. Completa sus argumentos y pulsa Enter."]

    def _handle_settings_key(self, modal: ModalState, key: str) -> None:
        if modal.tabs and modal.tabs[modal.tab_index] == "EXIT":
            self._handle_settings_exit_key(modal, key)
            return
        previous_tab = modal.tab_index
        SettingsEditor.handle_key(
            modal,
            key,
            close=lambda: self._open_settings_exit(modal),
            open_remote_users=self.show_remote_users,
        )
        if modal.tabs and modal.tabs[modal.tab_index] == "EXIT":
            modal.tab_selections[-1] = previous_tab
            modal.selected = 0
            modal.footer = "↑/↓ seleccionar  Enter confirmar  Esc volver"

    def _handle_remote_users_key(self, modal: ModalState, key: str) -> None:
        if key == "ESC":
            self.show_settings()
            settings = self.modal
            if settings:
                settings.tab_index = settings.tabs.index("REMOTE ACCESS")
                indices = self._settings_field_indices(settings)
                settings.selected = indices[-1]
            return
        if key in ("UP", "DOWN") and modal.items:
            delta = -1 if key == "UP" else 1
            modal.selected = (modal.selected + delta) % len(modal.items)
            modal.scroll = max(0, modal.selected - 4)
            return
        if key.casefold() == "n":
            username = self._read_text("Nuevo usuario:")
            if not username:
                return
            role = self._read_text("Nivel [viewer/operator/manager/administrator]:") or "operator"
            result, output = self._remote_access_capture(
                ["user", "add", username, "--role", role, "--password-auth", "on"]
            )
            self._finish_remote_user_action(result, output)
            return
        if not modal.items:
            return
        username = modal.items[modal.selected]["username"]
        if key.casefold() == "p" or key == "ENTER":
            result, output = self._remote_access_capture(["user", "rotate-password", username])
        elif key.casefold() == "r":
            role = self._read_text("Nuevo nivel [viewer/operator/manager/administrator]:")
            if not role:
                return
            result, output = self._remote_access_capture(
                ["user", "set-role", username, "--role", role]
            )
        elif key.casefold() == "e":
            action = "disable" if modal.items[modal.selected].get("enabled") else "enable"
            result, output = self._remote_access_capture(["user", action, username])
        elif key == "DELETE":
            confirmation = self._read_text(f"Escribe ELIMINAR para borrar {username}:")
            if confirmation != "ELIMINAR":
                return
            result, output = self._remote_access_capture(["user", "delete", username])
        else:
            return
        self._finish_remote_user_action(result, output)

    def _handle_project_close_key(self, modal: ModalState, key: str) -> None:
        if key == "ESC":
            self.modal = None
            self.messages = ["Cierre cancelado; el proyecto continúa abierto."]
            return
        if key in ("LEFT", "UP", "RIGHT", "DOWN"):
            modal.selected = 1 - modal.selected
            return
        normalized = key.casefold()
        if normalized in {"s", "y"}:
            modal.selected = 0
        elif normalized == "n":
            modal.selected = 1
        elif key != "ENTER":
            return
        from lanctl.core.projects.save_policy import remember_close_answer

        remember_close_answer(str(modal.items[modal.selected]))
        self.modal = None
        self.running = False

    def _request_project_activation(self, path: Path) -> None:
        from lanctl.core.projects.save_policy import workspace_is_dirty

        if getattr(self, "scanning", False):
            self.messages = [
                "Cierra esta ventana y pulsa Esc para cancelar el escaneo antes de cambiar de proyecto."
            ]
            if self.modal:
                self.modal.footer = self.messages[0]
            return
        settings = load_config()
        current = str(settings.get("activeProject") or "").strip()
        target = str(path.resolve())
        if current and Path(current).resolve() != Path(target) and workspace_is_dirty(settings):
            self.pending_project_path = target
            self._open_modal(
                ModalState(
                    kind="project_switch",
                    title="CAMBIOS SIN GUARDAR",
                    tabs=["Cambiar proyecto"],
                    pages=[
                        [
                            "Guardar los cambios y abrir el proyecto seleccionado",
                            "Descartar los cambios y abrir el proyecto seleccionado",
                            "Cancelar y mantener el proyecto actual",
                        ]
                    ],
                    items=["save", "discard", "cancel"],
                    footer="↑/↓ seleccionar  Enter confirmar  Esc cancelar",
                    max_width=90,
                    max_height=14,
                )
            )
            return
        self._activate_project_path(target)

    def _activate_project_path(self, path: str, *, discard_changes: bool = False) -> None:
        from lanctl.core.projects.workspace import activate_project_workspace

        try:
            activate_project_workspace(path, discard_changes=discard_changes)
            self.modal = None
            self.reload()
            self._set_terminal_message(f"Proyecto activado: {path}")
        except (OSError, RuntimeError, ValueError, sqlite3.DatabaseError) as error:
            self._set_terminal_message(f"No se pudo cambiar de proyecto: {error}")
            self.show_project_manager()
            if self.modal:
                self.modal.footer = f"ERROR: {error} · Esc cerrar"

    def _handle_project_switch_key(self, modal: ModalState, key: str) -> None:
        if key == "ESC":
            self.pending_project_path = None
            self.show_project_manager()
            return
        if key in ("UP", "LEFT"):
            modal.selected = (modal.selected - 1) % len(modal.items)
            return
        if key in ("DOWN", "RIGHT"):
            modal.selected = (modal.selected + 1) % len(modal.items)
            return
        if key != "ENTER":
            return
        action = str(modal.items[modal.selected])
        target, self.pending_project_path = self.pending_project_path, None
        if action == "cancel" or not target:
            self.show_project_manager()
            return
        if action == "save":
            from lanctl.core.projects.save_policy import SaveTrigger, save_active_project

            try:
                save_active_project(SaveTrigger.CHANGE, force=True)
            except (OSError, RuntimeError, ValueError, sqlite3.DatabaseError) as error:
                modal.footer = f"ERROR al guardar: {error} · Esc cancelar"
                self.pending_project_path = target
                return
        self._activate_project_path(target, discard_changes=action == "discard")

    def _finish_remote_user_action(self, result: int, output: str) -> None:
        cleaned = _clean_tui_output(output)
        self.messages = cleaned[-2:] if cleaned else ["Usuario remoto actualizado."]
        if result == 0:
            self.show_remote_users()
        elif self.modal:
            self.modal.footer = (
                f"ERROR: {cleaned[-1] if cleaned else 'operación rechazada'} · Esc volver"
            )

    @staticmethod
    def _settings_field_indices(modal: ModalState) -> list[int]:
        return SettingsEditor.field_indices(modal)

    def _save_settings(self, modal: ModalState) -> None:
        changed = [
            field
            for field in modal.items
            if field.value != field.original or field.visible != field.original_visible
        ]
        if not changed:
            self.modal = None
            self.messages = ["SETTINGS: no había cambios pendientes."]
            return
        argv = ["settings"]
        for field in changed:
            value = field.value.strip()
            if field.key == "dhcpRange" and not value:
                value = "off"
            elif field.key == "projectsDirectory" and not value:
                value = "auto"
            elif not value:
                modal.footer = f"ERROR: {field.label} no puede quedar vacío · Esc cancelar"
                return
            if field.key.startswith("tuiKey."):
                action = field.key.removeprefix("tuiKey.")
                if field.value != field.original:
                    argv.extend((field.option, f"{action}={value}"))
                if field.visible != field.original_visible:
                    argv.extend(("--tui-footer-button", f"{action}={field.visible.casefold()}"))
                continue
            if field.key.startswith("tuiColumn."):
                name = field.key.removeprefix("tuiColumn.")
                argv.extend((field.option, f"{name}={value}"))
                continue
            if field.key.startswith("tuiFixed."):
                action = field.key.removeprefix("tuiFixed.")
                argv.extend(("--tui-footer-button", f"{action}={field.visible.casefold()}"))
                continue
            elif field.key.startswith("tuiFooter."):
                value = f"{field.key.removeprefix('tuiFooter.')}={value}"
            argv.extend((field.option, value))
        result, output = self._capture(argv)
        if result == 0:
            self.modal = None
            self.reload()
            self._set_command_output(output, result)
        else:
            cleaned = _clean_tui_output(output)
            detail = cleaned[-1] if cleaned else "no se pudo guardar"
            modal.footer = f"ERROR: {detail} · Enter reintentar · Esc volver"

    def _update_manager_detail(self, modal: ModalState) -> None:
        if not modal.items:
            return
        item = modal.items[modal.selected]
        if modal.kind == "plugins":
            modal.pages[1] = _plugin_detail(item)
        elif modal.kind == "projects":
            active = self.project_info.get("path", "") if self.project_info else ""
            modal.pages[1] = _project_detail(item, active)

    def run(self) -> int:
        if not _is_interactive_terminal(sys.stdin) or not _is_interactive_terminal(self.screen):
            raise OSError(
                "LANCTL TUI necesita una terminal interactiva; usa --cli o un comando "
                "normal cuando la entrada o la salida estén redirigidas"
            )
        if os.name == "nt":
            just_fix_windows_console()
            from msvcrt import getwch, kbhit

            key_available = kbhit

            def read_key() -> str:
                return _read_windows_key(getwch)

            terminal_mode = nullcontext()
        else:

            def key_available() -> bool:
                return posix_key_available(sys.stdin)

            def read_key() -> str:
                return read_posix_key(sys.stdin)

            terminal_mode = posix_terminal_mode(sys.stdin)

        self._read_key = read_key

        from lanctl.apps.access.root_control import RootInterfaceAgent

        agent = RootInterfaceAgent("tui", self.remote_actions.put).start()

        try:
            # La pantalla alternativa impide que cada repintado pase al
            # historial de la consola. Desactivar el ajuste automático evita
            # filas fantasma cuando una línea ocupa exactamente todo el ancho.
            self.screen.write(TUI_ENTER_SCREEN)
            self.screen.flush()
            if self.startup_modal:
                # Construye primero el fondo congelado sin forzar un escaneo:
                # los gestores no necesitan esperar a la detección de red.
                self.render()
                self._open_startup_modal()
            else:
                self.refresh()
            self.render()
            with terminal_mode:
                while self.running:
                    scan_changed = self._drain_scan_events()
                    if not self.remote_actions.empty():
                        self._apply_remote_action(self.remote_actions.get_nowait())
                        self.render()
                    elif key_available():
                        self.handle_key(read_key())
                        self.render()
                    elif scan_changed:
                        self.render()
                    else:
                        time.sleep(0.08)
        finally:
            self.cancel_refresh()
            if self._scan_thread is not None and self._scan_thread.is_alive():
                self._scan_thread.join(timeout=1.0)
            agent.stop()
            self._read_key = None
            self.screen.write(TUI_LEAVE_SCREEN)
            self.screen.flush()
        return 0

    def _apply_remote_action(self, command: dict) -> None:
        action = command.get("action")
        if action == "refresh":
            self.reload()
            self.messages = ["Inventario actualizado por una sesión SSH remota."]
            return
        if action != "view":
            return
        view = str(command.get("value", "tui")).casefold()
        if view == "tui":
            self.modal = None
        elif view == "plugins":
            self.show_plugin_manager()
        elif view == "projects":
            self.show_project_manager()
        elif view == "settings":
            self.show_settings()

    def _open_startup_modal(self) -> None:
        actions = {
            "plugins": self.show_plugin_manager,
            "projects": self.show_project_manager,
            "settings": self.show_settings,
        }
        try:
            actions[self.startup_modal]()
        except KeyError as error:
            raise ValueError(f"ventana TUI desconocida: {self.startup_modal}") from error


def _is_interactive_terminal(stream) -> bool:
    """Consulta isatty sin asumir que el stream capturado implementa una consola."""
    try:
        return bool(stream.isatty())
    except (AttributeError, OSError, ValueError):
        return False


def _credential_user_map(config: dict) -> dict[str, str]:
    """Carga únicamente usuarios seguros; nunca expone contraseñas al TUI."""

    from lanctl.core.credentials import CredentialStore

    try:
        metadata = CredentialStore(
            str(config.get("credentials", "data/lc/.credentials"))
        ).metadata()
    except (OSError, ValueError):
        return {}
    return {
        str(entry.get("credentialId", "")): str(entry.get("username", "")).strip()
        for entry in metadata
        if str(entry.get("credentialId", "")).strip()
    }


def _device_user_labels(device, usernames: dict[str, str]) -> str:
    credentials = getattr(device, "credentials", {}) or {}
    labels = [
        f"{usernames.get(reference) or '?'}@{protocol}"
        for protocol, reference in credentials.items()
    ]
    return ",".join(labels) or "-"


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
        segment = value[position : match.start()]
        take = max(0, min(len(segment), target - visible))
        output.append(segment[:take])
        visible += take
        if visible >= target:
            break
        output.append(match.group(0))
        position = match.end()
    else:
        output.append(value[position : position + max(0, target - visible)])
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
        "-ip": "ip",
        "--ip": "ip",
        "ip": "ip",
        "-name": "name",
        "--name": "name",
        "name": "name",
        "-alias": "alias",
        "--alias": "alias",
        "alias": "alias",
        "-description": "description",
        "--description": "description",
        "description": "description",
        "-group": "group",
        "--group": "group",
        "group": "group",
        "-cnf": "cnf",
        "--cnf": "cnf",
        "cnf": "cnf",
        "-idf": "idf",
        "--idf": "idf",
        "idf": "idf",
        "-protocol": "protocol",
        "--protocol": "protocol",
        "protocol": "protocol",
        "-delete": "delete",
        "--delete": "delete",
        "-del": "delete",
        "-delate": "delete",
        "delete": "delete",
        "del": "delete",
        "remove": "delete",
    }
    first = parts[1].casefold()
    if first in option_map:
        if not selected:
            raise ValueError("no hay ningún elemento seleccionado")
        # Las opciones de edición son componibles. Inserta únicamente el
        # selector contextual y conserva todas las opciones para argparse.
        if first.startswith("-") and first not in (
            "-delete",
            "--delete",
            "-del",
            "-delate",
        ):
            return ["element", selected, *parts[1:]]
        target, option_index = selected, 1
    else:
        target, option_index = parts[1], 2
        if len(parts) == 2:
            return ["element", target]

    option = parts[option_index].casefold()
    if option not in option_map:
        # Conserva la sintaxis avanzada anterior: `element OBJETIVO edit ...`.
        return list(parts)
    action = option_map[option]
    if option.startswith("-") and action != "delete":
        return list(parts)
    values = parts[option_index + 1 :]
    if action == "delete":
        if values and values != ["--yes"]:
            raise ValueError("element -delete no acepta valores")
        return ["element", target, "delete", *values]
    if not values:
        raise ValueError(f"falta el valor para element {parts[option_index]}")
    return ["element", target, action, *values]


def _spinner_character(index: int) -> str:
    sequence = "\\|/-"
    return sequence[index % len(sequence)]


class _TuiScanProgress:
    """Publica progreso thread-safe y expone cancelación cooperativa."""

    def __init__(self, events: queue.Queue, cancel_event: threading.Event) -> None:
        self.events = events
        self.cancel_event = cancel_event
        self.total = 1
        self.current = 0

    def _check_cancelled(self) -> None:
        if self.cancel_event.is_set():
            raise InterruptedError("escaneo cancelado")

    def cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def begin(
        self,
        total: int,
        phase: str = "Search",
        found_total: int = 0,
        known_identities: dict[str, str] | None = None,
    ) -> None:
        self._check_cancelled()
        self.total = max(1, total)
        self.current = 0
        self.events.put(("begin", self.total))

    def phase(self, phase: str) -> None:
        self._check_cancelled()

    def found(self, *keys: str) -> None:
        self._check_cancelled()
        self.events.put(("found", keys))

    def advance(self, amount: int = 1) -> None:
        self._check_cancelled()
        self.current = min(self.total, self.current + amount)
        self.events.put(("advance", self.current))

    def complete(self) -> None:
        self._check_cancelled()
        self.current = self.total
        self.events.put(("advance", self.current))

    def clear(self) -> None:
        return


def _dhcp_boundary_indexes(devices, configured_range: str | None):
    indexes = [
        index for index, device in enumerate(devices) if _ip_in_range(device.ip, configured_range)
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
        return (
            ipaddress.IPv4Address(start_text.strip())
            <= address
            <= ipaddress.IPv4Address(end_text.strip())
        )
    except (ValueError, ipaddress.AddressValueError):
        return False


def _parse_list_filter(parts: list[str]) -> tuple[str, str]:
    if not parts or [part.casefold() for part in parts] in (["--all"], ["-all"]):
        return "all", ""
    lowered = [part.casefold() for part in parts]
    if lowered in (["--connected"], ["-connected"], ["--active"]):
        return "connected", ""
    if lowered in (
        ["--disconnected"],
        ["--disconect"],
        ["-disconnected"],
        ["-disconect"],
        ["--offline"],
    ):
        return "disconnected", ""
    if lowered in (["-dhcp"], ["--dhcp"]):
        return "dhcp", ""
    if lowered in (["-statics"], ["--statics"], ["--static"]):
        return "statics", ""
    if len(parts) == 2 and lowered[0] in ("-group", "--group"):
        return "group", parts[1].upper()
    raise ValueError("usa: list --all|--connected|--disconnected|-group NOMBRE|-dhcp|-statics")


def _last_meaningful_line(value: str) -> str:
    return next((line.strip() for line in reversed(value.splitlines()) if line.strip()), "")


def _command_tree_lines() -> list[str]:
    """Genera el árbol desde argparse para que F1 no quede desactualizado."""
    from lanctl.apps.ip.interfaces.cli.main import build_parser

    root = build_parser(include_plugin_commands=True)
    command_action = next(
        (action for action in root._actions if isinstance(action, argparse._SubParsersAction)),
        None,
    )
    if not command_action:
        return ["LANCTL", "└── (sin comandos registrados)"]
    unique: list[tuple[str, argparse.ArgumentParser]] = []
    seen: set[int] = set()
    for name, parser in command_action.choices.items():
        if id(parser) not in seen:
            seen.add(id(parser))
            unique.append((name, parser))
    lines = ["LANCTL"]
    for index, (name, parser) in enumerate(unique):
        last = index == len(unique) - 1
        lines.append(f"{'└──' if last else '├──'} {name}")
        nested = next(
            (
                action
                for action in parser._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
            None,
        )
        if nested:
            names, nested_seen = [], set()
            for child, child_parser in nested.choices.items():
                if id(child_parser) not in nested_seen:
                    nested_seen.add(id(child_parser))
                    names.append(child)
            branch = "    " if last else "│   "
            for child_index, child in enumerate(names):
                lines.append(f"{branch}{'└──' if child_index == len(names) - 1 else '├──'} {child}")
    return lines


def _help_command_entries() -> list[HelpCommand]:
    """Construye un catálogo navegable desde el parser real de LANCTL."""
    from lanctl.apps.ip.interfaces.cli.main import build_parser

    root = build_parser(include_plugin_commands=True)
    command_action = next(
        (action for action in root._actions if isinstance(action, argparse._SubParsersAction)),
        None,
    )
    if command_action is None:
        return []
    descriptions = {
        action.dest: str(action.help or "Sin descripción.")
        for action in command_action._choices_actions
    }
    names_by_parser: dict[int, list[str]] = {}
    parsers: dict[int, argparse.ArgumentParser] = {}
    for name, parser in command_action.choices.items():
        names_by_parser.setdefault(id(parser), []).append(name)
        parsers[id(parser)] = parser

    entries = []
    for parser_id, names in names_by_parser.items():
        parser = parsers[parser_id]
        canonical, *aliases = names
        nested = next(
            (
                action
                for action in parser._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
            None,
        )
        subcommands: list[str] = []
        if nested:
            seen: set[int] = set()
            for name, child_parser in nested.choices.items():
                if id(child_parser) not in seen:
                    seen.add(id(child_parser))
                    subcommands.append(name)
        options = []
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                continue
            label = _help_action_label(action)
            if label:
                options.append(f"{label:<30} {action.help or '-'}")
        usage = ANSI_ESCAPE.sub("", parser.format_usage()).strip()
        entries.append(
            HelpCommand(
                name=canonical,
                description=descriptions.get(canonical, parser.description or "Sin descripción."),
                usage=usage,
                aliases=tuple(aliases),
                subcommands=tuple(subcommands),
                options=tuple(options),
            )
        )
    return entries


def _help_action_label(action: argparse.Action) -> str:
    if action.option_strings:
        label = ", ".join(action.option_strings)
    elif action.dest not in (argparse.SUPPRESS, "==SUPPRESS=="):
        label = str(action.metavar or action.dest).upper()
    else:
        return ""
    if action.nargs != 0 and action.option_strings:
        label += f" {action.metavar or action.dest.upper()}"
    return label


def _help_command_detail(entry: HelpCommand) -> list[str]:
    lines = [f"COMANDO  LANCTL {entry.name}", ""]
    lines.extend(textwrap.wrap(entry.description, width=92) or ["Sin descripción."])
    lines.extend(("", "USO", f"  {entry.usage}"))
    if entry.aliases:
        lines.extend(("", "ALIAS", f"  {', '.join(entry.aliases)}"))
    if entry.subcommands:
        lines.extend(("", "SUBCOMANDOS", f"  {', '.join(entry.subcommands)}"))
    if entry.options:
        lines.extend(("", "OPCIONES", *(f"  {option}" for option in entry.options)))
    lines.extend(("", "Tab prepara este comando en el prompt del TUI."))
    return lines


def _function_bar(
    width: int,
    visible_actions: list[str] | None = None,
    key_bindings: dict[str, str | None] | None = None,
) -> str:
    bindings = normalize_key_bindings(key_bindings)
    visible = normalize_footer_actions(visible_actions)
    labels = {
        "help": "Ayuda",
        "info": "Info",
        "ping": "Ping",
        "refresh": "Actualizar",
        "plugins": "Plugin",
        "projects": "Proyectos",
        "settings": "Settings",
        "history": "Comandos",
        "search": "Buscar",
        "reload": "Recargar",
        "edit": "Editar",
        "groups": "Grupos",
        "ports": "Puertos",
        "open": "Abrir",
        "save": "Guardar",
        "differences": "Cambios",
        "copyLine": "Copiar",
        "copyJson": "JSON",
        "console": "Consola",
        "quit": "Cerrar",
        "deviceHistory": "Historial",
        "scanSelected": "Escanear",
        "filterActive": "Activos",
        "filterDisconnected": "Offline",
        "filterAll": "Todos",
        "ssh": "SSH",
        "terminal": "Terminal",
        "credentials": "Credenciales",
        "wakeOnLan": "WOL",
        "copyIp": "IP",
        "copyMac": "MAC",
        "projectStatus": "Proyecto",
        "select": "Seleccionar",
        "execute": "Ejecutar",
        "exit": "Salir",
    }
    fixed_keys = {"select": "↑↓", "execute": "Enter", "exit": "Esc"}

    def display_key(value: str) -> str:
        normalized = value.replace("_", "+")
        return "Ctrl+" + normalized[5:] if normalized.startswith("CTRL+") else normalized

    buttons = []
    for action in visible:
        assigned = fixed_keys.get(action) or bindings[action]
        if assigned:
            buttons.append((display_key(assigned), labels[action]))
    compact_labels = {
        "Actualizar": "Act.",
        "Proyectos": "Proy.",
        "Settings": "Config.",
        "Comandos": "Cmd.",
        "Recargar": "Rec.",
        "Puertos": "Ports",
        "Cambios": "Camb.",
        "Consola": "CLI",
        "Guardar": "Guard.",
        "Copiar": "Cop.",
        "Seleccionar": "Selec.",
        "Ejecutar": "Ej.",
    }

    def button_width(item: tuple[str, str]) -> int:
        key, label = item
        return len(key) + len(label) + 3

    # Primero se compactan las etiquetas; si aún no caben, se eliminan de
    # forma ordenada las acciones menos esenciales. Ayuda, selección, ejecutar
    # y salir permanecen disponibles incluso en terminales estrechas.
    if sum(map(button_width, buttons)) + len(buttons) - 1 > width:
        buttons = [(key, compact_labels.get(label, label)) for key, label in buttons]
    removable_actions = (
        "projectStatus",
        "copyMac",
        "copyIp",
        "wakeOnLan",
        "credentials",
        "terminal",
        "ssh",
        "filterAll",
        "filterDisconnected",
        "filterActive",
        "scanSelected",
        "deviceHistory",
        "console",
        "differences",
        "groups",
        "ports",
        "open",
        "edit",
        "reload",
        "search",
        "quit",
        "copyJson",
        "copyLine",
        "save",
        "plugins",
        "projects",
        "history",
        "ping",
        "info",
        "settings",
        "refresh",
    )
    removable = [display_key(bindings[action]) for action in removable_actions if bindings[action]]
    for key in removable:
        if sum(map(button_width, buttons)) + max(0, len(buttons) - 1) <= width:
            break
        buttons = [item for item in buttons if item[0] != key]
    while buttons and sum(map(button_width, buttons)) + max(0, len(buttons) - 1) > width:
        buttons.pop(-2 if len(buttons) > 1 else -1)

    content = sum(map(button_width, buttons))
    gaps = max(0, len(buttons) - 1)
    free = max(0, width - content)
    gap_width, extra = divmod(free, gaps) if gaps else (0, 0)
    output = ""
    visible = 0
    for index, (key, label) in enumerate(buttons):
        spacing = "" if index == 0 else " " * (gap_width + (1 if index <= extra else 0))
        output += (
            f"{Back.BLACK}{spacing}{RESET}"
            f"{Style.BRIGHT}{Back.WHITE}{Fore.BLACK} {key} {RESET}"
            f"{Back.BLACK}{Fore.WHITE} {label}{RESET}"
        )
        visible += len(spacing) + button_width((key, label))
    return output + f"{Back.BLACK}{' ' * max(0, width - visible)}{RESET}"


def run_tui(startup_modal: str | None = None) -> int:
    return LanctlTui(startup_modal=startup_modal).run()
