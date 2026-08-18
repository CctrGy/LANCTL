import io
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.cli import build_parser
from app.tui import (
    CLI_PANEL,
    LIST_ELEMENT_PANEL,
    TUI_ELEMENT_HELP,
    TUI_ELEMENT_SUGGESTIONS,
    TUI_ENTER_SCREEN,
    TUI_LEAVE_SCREEN,
    LanctlTui,
    _clean_tui_output,
    _compact_timestamp,
    _device_key,
    _dhcp_boundary_indexes,
    _expand_tui_widths,
    _fit_ansi,
    _function_bar,
    _inject_selected_group_element,
    _is_interactive_terminal,
    _last_meaningful_line,
    _parse_list_filter,
    _read_windows_key,
    _selectable_output_indexes,
    _spinner_character,
    _translate_tui_element,
)
from app.tui_modal import ModalState, SettingField


class TuiTests(unittest.TestCase):
    def test_status_identifies_the_active_project(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.project_info = {"name": "Casa"}
        tui.scanning = False
        tui.scan_summary = {}
        rendered = " ".join(tui._status_lines(100))
        self.assertIn("PROYECTO", rendered)
        self.assertIn("Casa", rendered)

    def test_redirected_tui_stops_cleanly_before_writing_terminal_codes(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.screen = io.StringIO()
        with (
            patch("app.tui.os.name", "nt"),
            patch("app.tui.sys.stdin", io.StringIO()),
            self.assertRaisesRegex(OSError, "terminal interactiva"),
        ):
            tui.run()
        self.assertEqual(tui.screen.getvalue(), "")
        self.assertFalse(_is_interactive_terminal(tui.screen))

    def test_lowercase_h_is_written_in_the_command_editor(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.output_focus = False
        tui.command_suggestions = []
        tui.command = ""
        tui.cursor = 0
        tui.running = True
        tui._clear_suggestions = lambda: None
        tui.show_history = lambda: self.fail("lowercase h opened history")

        tui.handle_key("h")

        self.assertEqual(tui.command, "h")
        self.assertEqual(tui.cursor, 1)

    def test_uppercase_h_is_also_available_to_the_command_editor(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.output_focus = False
        tui.command_suggestions = []
        tui.command = ""
        tui.cursor = 0
        tui._clear_suggestions = lambda: None

        tui.handle_key("H")

        self.assertEqual(tui.command, "H")

    def test_ctrl_h_is_distinguished_from_backspace(self):
        keys = iter(["\x08", "\x08"])
        self.assertEqual(_read_windows_key(lambda: next(keys), lambda: True), "CTRL_H")
        self.assertEqual(_read_windows_key(lambda: next(keys), lambda: False), "BACKSPACE")

    def test_ctrl_r_has_a_dedicated_key_code(self):
        self.assertEqual(_read_windows_key(lambda: "\x12"), "CTRL_R")

    def test_settings_navigation_and_control_keys(self):
        extended = iter(["\x00", "\x86", "\x00", "\x0f"])
        self.assertEqual(_read_windows_key(lambda: next(extended)), "F12")
        self.assertEqual(_read_windows_key(lambda: next(extended)), "SHIFT_TAB")
        self.assertEqual(_read_windows_key(lambda: "\t"), "TAB")
        self.assertEqual(_read_windows_key(lambda: "\x13"), "CTRL_S")

    def test_settings_tab_edits_and_saves_through_the_settings_command(self):
        tui = LanctlTui.__new__(LanctlTui)
        fields = [
            SettingField("workers", "Workers", "--workers", "64", "64", "entero"),
            SettingField("timeout", "Timeout", "--timeout", "0.8", "0.8", "segundos"),
        ]
        tui.modal = ModalState("settings", "SETTINGS", ["Configuración"], [[]], items=fields)
        captured = []
        tui._capture = lambda argv: captured.append(argv) or (0, "guardado")
        tui.reload = lambda: None
        tui._set_command_output = lambda output, result: None

        tui.handle_key("TAB")
        tui.handle_key("1")
        tui.handle_key("2")
        tui.handle_key("8")
        tui.handle_key("TAB")
        tui.handle_key("CTRL_S")

        self.assertEqual(captured, [["settings", "--workers", "128"]])
        self.assertIsNone(tui.modal)

    def test_settings_tab_separates_navigation_from_choice_editing(self):
        tui = LanctlTui.__new__(LanctlTui)
        fields = [
            SettingField(
                "discovery",
                "Descubrimiento",
                "--discovery",
                "hybrid",
                "hybrid",
                "icmp | arp | hybrid",
                "RED",
                choices=("icmp", "arp", "hybrid"),
            ),
            SettingField(
                "range", "Rango", "-range", "192.168.1.0/24", "192.168.1.0/24", section="RED"
            ),
        ]
        tui.modal = ModalState("settings", "SETTINGS", ["RED", "PROYECTOS"], [[], []], items=fields)

        tui._handle_settings_key(tui.modal, "TAB")
        self.assertTrue(tui.modal.editing)
        tui._handle_settings_key(tui.modal, "RIGHT")
        self.assertEqual(tui.modal.items[0].value, "icmp")
        self.assertEqual(tui.modal.tab_index, 0)
        tui._handle_settings_key(tui.modal, "TAB")
        self.assertFalse(tui.modal.editing)
        tui._handle_settings_key(tui.modal, "DOWN")
        self.assertEqual(tui.modal.selected, 1)

    def test_settings_escape_cancels_only_the_active_field_edit(self):
        tui = LanctlTui.__new__(LanctlTui)
        field = SettingField("workers", "Workers", "--workers", "64", "64")
        tui.modal = ModalState("settings", "SETTINGS", ["GENERAL"], [[]], items=[field])

        tui._handle_settings_key(tui.modal, "TAB")
        tui._handle_settings_key(tui.modal, "1")
        self.assertEqual(field.value, "1")
        tui._handle_settings_key(tui.modal, "ESC")

        self.assertEqual(field.value, "64")
        self.assertFalse(tui.modal.editing)

    def test_settings_uses_category_menus_and_contextual_descriptions(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui._last_screen_lines = []
        tui.modal = None

        tui.show_settings()

        self.assertEqual(
            tui.modal.tabs,
            [
                "GENERAL",
                "RED",
                "ESCANEO",
                "PROYECTOS",
                "ALMACENAMIENTO",
                "LOGS",
                "REMOTE ACCESS",
            ],
        )
        general_page = "\n".join(tui._modal_page(tui.modal))
        self.assertIn("DESCRIPCIÓN", general_page)
        self.assertIn("Define qué columnas", general_page)

        tui._handle_settings_key(tui.modal, "RIGHT")
        self.assertEqual(tui.modal.tabs[tui.modal.tab_index], "RED")
        selected = tui.modal.items[tui.modal.selected]
        self.assertEqual(selected.section, "RED")
        first_key = selected.key
        tui._handle_settings_key(tui.modal, "DOWN")
        self.assertNotEqual(tui.modal.items[tui.modal.selected].key, first_key)

    def test_command_history_opens_modal_and_recovers_selection(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.output_focus = False
        tui.command_suggestions = []
        tui.command = ""
        tui.cursor = 0
        tui.messages = []
        tui.command_history = ["list --all", "scan", "monitor status"]
        tui.command_history_index = 0
        tui.command_history_scroll = 0
        tui.modal = None
        tui._last_screen_lines = ["INVENTARIO"]

        tui.handle_key("CTRL_H")
        self.assertEqual(tui.modal.kind, "commands")
        self.assertEqual(tui.modal.selected, 2)
        tui.handle_key("UP")
        self.assertEqual(tui.modal.selected, 1)
        tui.handle_key("ENTER")

        self.assertIsNone(tui.modal)
        self.assertEqual(tui.command, "scan")
        self.assertEqual(tui.cursor, 4)

    def test_command_history_lines_scroll_only_the_command_list(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.command_history = [f"command {index}" for index in range(20)]
        tui.command_history_index = 19
        tui.command_history_scroll = 0

        lines = tui._command_history_lines(80, 4)

        self.assertEqual(len(lines), 4)
        self.assertIn("command 19", lines[-1])
        self.assertEqual(tui.command_history_scroll, 16)

    def test_history_view_replaces_inventory_and_escape_restores_selection(self):
        tui = LanctlTui.__new__(LanctlTui)
        device = SimpleNamespace(
            device_id="dev_nas", mac="02:11:22:33:44:55", ip="192.168.1.8", alias="NAS", name="NAS"
        )
        tui.devices = [device]
        tui.index = 0
        tui.scroll = 4
        tui.messages = []
        tui.view_state = "inventory"
        tui.history_events = []
        tui.history_index = 0
        tui.detail_lines = []
        tui.output_focus = False
        event = SimpleNamespace(
            timestamp="2026-08-03T10:00:00+02:00",
            type="device.detected",
            summary="Detectado",
            result="success",
            source="test",
            correlationId=None,
            runId=None,
            taskId=None,
            operationId=None,
            error=None,
            changes=(),
            device=SimpleNamespace(label="NAS"),
        )
        with patch("app.core.history.HistoryService") as service:
            service.return_value.query.return_value = [event]
            tui.show_history()
        self.assertEqual(tui.view_state, "history")
        self.assertEqual(tui.selected, device)
        tui.handle_key("ENTER")
        self.assertTrue(tui.detail_lines)
        tui.handle_key("ESC")
        self.assertFalse(tui.detail_lines)
        self.assertEqual(tui.view_state, "history")
        tui.handle_key("ESC")
        self.assertEqual(tui.view_state, "inventory")
        self.assertEqual(tui.scroll, 4)

    def test_tui_uses_an_alternate_non_wrapping_screen(self):
        self.assertIn("\x1b[?1049h", TUI_ENTER_SCREEN)
        self.assertIn("\x1b[?7l", TUI_ENTER_SCREEN)
        self.assertIn("\x1b[?7h", TUI_LEAVE_SCREEN)
        self.assertTrue(TUI_LEAVE_SCREEN.endswith("\x1b[?1049l"))

    @unittest.skipUnless(os.name == "nt", "msvcrt solo está disponible en Windows")
    def test_secret_input_uses_the_tui_prompt_and_never_echoes_characters(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.secret_prompt = ""
        observed_prompts = []
        tui.render = lambda: observed_prompts.append(tui.secret_prompt)

        with (
            patch("app.tui.os.name", "nt"),
            patch("msvcrt.getwch", side_effect=["s", "e", "x", "\x08", "c", "\r"]),
        ):
            secret = tui._read_secret("Contraseña (no se mostrará): ")

        self.assertEqual(secret, "sec")
        self.assertEqual(observed_prompts[0], "Contraseña (no se mostrará):")
        self.assertEqual(observed_prompts[-1], "")
        self.assertNotIn("sec", "".join(observed_prompts))

    def test_command_output_is_safe_for_terminal_panel(self):
        self.assertEqual(
            _clean_tui_output("\x1b[31mERROR\x1b[0m\r\nvalor\t2\x07"),
            ["ERROR", "valor   2"],
        )

    def test_colored_status_is_fitted_by_visible_width(self):
        from colorama import Fore, Style

        rendered = _fit_ansi(Fore.CYAN + "estado demasiado largo" + Style.RESET_ALL, 10)
        plain = __import__("re").sub(r"\x1b\[[0-9;]*m", "", rendered)
        self.assertEqual(len(plain), 10)
        self.assertTrue(plain.endswith("…"))

    def test_short_element_commands_use_tui_selection_or_explicit_target(self):
        selected = "02:00:3F:00:51:0C"
        self.assertEqual(
            _translate_tui_element(["element", "-name", "Rack", "Principal"], selected),
            ["element", selected, "name", "Rack", "Principal"],
        )
        self.assertEqual(
            _translate_tui_element(["element", "192.168.1.35", "-alias", "RPI"], selected),
            ["element", "192.168.1.35", "alias", "RPI"],
        )
        self.assertEqual(
            _translate_tui_element(["element", "-delate"], selected),
            ["element", selected, "delete"],
        )
        self.assertEqual(
            _translate_tui_element(["element", "-add", "AA:BB:CC:DD:EE:FF"], selected),
            ["element", "-add", "AA:BB:CC:DD:EE:FF"],
        )

    def test_table_output_rows_become_selectable(self):
        lines = [
            "GROUP  ELEMENTS  DESCRIPTION",
            "-----  --------  -----------",
            "ASSETS        2  -",
            "IOT           3  -",
        ]
        self.assertEqual(_selectable_output_indexes(lines), [2, 3])

    def test_f2_modal_splits_information_and_lists_ports(self):
        from app.tui import LanctlTui

        tui = LanctlTui.__new__(LanctlTui)
        tui.devices = [
            SimpleNamespace(
                device_id="dev_test",
                cnf="O",
                ip="192.168.1.10",
                mac="AA:BB:CC:DD:EE:FF",
                alias="SW",
                default_alias="",
                name="Switch",
                default_name="switch.local",
                description="Rack",
                manufacturer="Cisco",
                groups=["GESTOR"],
                discovery_methods=["ARP"],
                last_discovery="ARP",
                last_seen="2026-07-26T01:00:00+02:00",
                protocols=["ssh"],
                credentials={"ssh": "cred_sw"},
                protocol_options={},
            )
        ]
        tui.index = 0
        tui.messages = []
        tui.detail_lines = []
        tui.detail_scroll = 0
        tui._last_screen_lines = ["INVENTARIO"]
        tui.render = lambda: None
        payload = {
            "element": {"manufacturer": "Cisco"},
            "observation": {
                "reachable": True,
                "observed_mac": "AA:BB:CC:DD:EE:FF",
                "identityMatch": True,
                "hostname": "switch.local",
                "latency_ms": 1.2,
                "ttl": 64,
                "scanned_ports": 51,
                "open_ports": [{"port": 22}, {"port": 443}],
                "duration": 0.5,
                "identification": {
                    "device_type": "switch",
                    "confidence": "high",
                    "evidence": ["ssh"],
                },
            },
        }
        tui._capture = lambda _argv: (0, json.dumps(payload))

        tui.show_info()

        self.assertEqual(tui.modal.kind, "info")
        self.assertEqual(len(tui.modal.tabs), 5)
        ports = "\n".join(tui.modal.pages[4])
        self.assertIn("Puertos abiertos: 2", ports)
        self.assertIn("443", ports)
        self.assertIn("22", ports)

    def test_modal_freezes_background_and_consumes_navigation(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui._last_screen_lines = ["PANTALLA PRINCIPAL"]
        tui.modal = None
        tui._open_modal(ModalState("help", "HELP", ["A", "B"], [["uno"], ["dos"]]))

        tui.handle_key("RIGHT")

        self.assertEqual(tui.modal.tab_index, 1)
        self.assertEqual(tui.modal.background, ["PANTALLA PRINCIPAL"])

    def test_reload_is_an_internal_tui_command(self):
        tui = object.__new__(LanctlTui)
        tui.command = "reload"
        tui.cursor = len(tui.command)
        tui.messages = []
        tui.devices = [object(), object()]
        calls = []
        tui.reload = lambda: calls.append("reload")
        tui.execute()
        self.assertEqual(calls, ["reload"])
        self.assertIn("2 elementos", tui.messages[0])

    def test_list_refreshes_the_network_after_setting_the_filter(self):
        tui = object.__new__(LanctlTui)
        tui.command = "list --connected"
        tui.cursor = len(tui.command)
        tui.messages = []
        tui.output_focus = False
        tui.output_selectable = []
        tui.output_index = 0
        tui.output_scroll = 0
        tui.pending_confirmation = None
        tui.command_suggestions = []
        calls = []
        tui.configure_list = lambda parts: calls.append(("filter", parts)) or True
        tui.refresh = lambda: calls.append(("refresh", []))

        tui.execute()

        self.assertEqual(
            calls,
            [("filter", ["--connected"]), ("refresh", [])],
        )

    def test_invalid_list_filter_does_not_scan(self):
        tui = object.__new__(LanctlTui)
        tui.command = "list --inventado"
        tui.cursor = len(tui.command)
        tui.messages = []
        tui.output_focus = False
        tui.output_selectable = []
        tui.output_index = 0
        tui.output_scroll = 0
        tui.pending_confirmation = None
        tui.command_suggestions = []
        calls = []
        tui.configure_list = lambda _parts: False
        tui.refresh = lambda: calls.append("refresh")

        tui.execute()

        self.assertEqual(calls, [])

    def test_last_seen_uses_compact_tui_format(self):
        self.assertEqual(
            _compact_timestamp("2026-07-26T17:43:35+02:00"),
            "07/26 17:43",
        )
        self.assertEqual(_compact_timestamp(""), "-")

    def test_dhcp_boundaries_delimit_the_configured_ip_range(self):
        devices = [
            SimpleNamespace(ip="192.168.1.11"),
            SimpleNamespace(ip="192.168.1.16"),
            SimpleNamespace(ip="192.168.1.42"),
            SimpleNamespace(ip="192.168.1.254"),
        ]
        self.assertEqual(
            _dhcp_boundary_indexes(devices, "192.168.1.16-192.168.1.192"),
            (1, 2),
        )

    def test_tui_list_filters_accept_documented_aliases(self):
        self.assertEqual(_parse_list_filter(["--connected"]), ("connected", ""))
        self.assertEqual(_parse_list_filter(["--disconect"]), ("disconnected", ""))
        self.assertEqual(_parse_list_filter(["-group", "mam"]), ("group", "MAM"))
        self.assertEqual(_parse_list_filter(["-dhcp"]), ("dhcp", ""))
        self.assertEqual(_parse_list_filter(["-statics"]), ("statics", ""))

    def test_activity_identity_prefers_mac_and_supports_ip_only_rows(self):
        self.assertEqual(_device_key("aa:bb:cc:dd:ee:ff", "192.168.1.4"), "mac:AA:BB:CC:DD:EE:FF")
        self.assertEqual(_device_key("", "192.168.1.4"), "ip:192.168.1.4")

    def test_tui_flag_is_registered(self):
        args = build_parser().parse_args(["-tui"])
        self.assertEqual(args.tui, "inventory")
        self.assertIsNone(args.command)

    def test_tui_flag_accepts_direct_modal_shortcuts_case_insensitively(self):
        for value in ("PLUGINS", "projects", "Settings"):
            args = build_parser().parse_args(["--tui", value])
            self.assertEqual(args.tui, value.casefold())

    def test_startup_modal_dispatches_to_the_requested_window(self):
        tui = LanctlTui.__new__(LanctlTui)
        calls = []
        tui.show_plugin_manager = lambda: calls.append("plugins")
        tui.show_project_manager = lambda: calls.append("projects")
        tui.show_settings = lambda: calls.append("settings")

        for modal in ("plugins", "projects", "settings"):
            tui.startup_modal = modal
            tui._open_startup_modal()

        self.assertEqual(calls, ["plugins", "projects", "settings"])

    def test_project_can_be_selected_before_opening_the_tui(self):
        path = "C:/Users/Victor/Desktop/Casa.vlf"
        long_option = build_parser().parse_args(["--tui", "--project", path])
        compatible_option = build_parser().parse_args(["--tui", "-project", path])
        self.assertTrue(long_option.tui)
        self.assertEqual(long_option.startup_project, path)
        self.assertEqual(compatible_option.startup_project, path)

    def test_reload_reopens_the_database_after_a_project_change(self):
        old = SimpleNamespace(mac="AA:BB:CC:DD:EE:01")
        new = SimpleNamespace(mac="AA:BB:CC:DD:EE:02")
        tui = object.__new__(LanctlTui)
        tui.devices = [old]
        tui.index = 0
        tui.scroll = 0
        tui.list_filter = ("all", "")
        tui.scanning = False
        tui.active_devices = set()
        tui.scan_visible_devices = set()

        with (
            patch(
                "app.tui.load_config",
                return_value={
                    "database": "projects/casa/devices.json",
                    "dhcpRange": "192.168.1.20-192.168.1.100",
                },
            ),
            patch("app.tui.DeviceDatabase") as database_type,
            patch("app.tui.active_project_info", return_value={"name": "Casa"}),
        ):
            database_type.return_value.load.return_value = [new]
            tui.reload()

        database_type.assert_called_once_with("projects/casa/devices.json")
        self.assertIs(tui.database, database_type.return_value)
        self.assertEqual(tui.devices, [new])
        self.assertEqual(tui.project_info["name"], "Casa")

    def test_windows_function_and_arrow_keys_are_decoded(self):
        values = iter(["\xe0", "H"])
        self.assertEqual(_read_windows_key(lambda: next(values)), "UP")
        values = iter(["\x00", "?"])
        self.assertEqual(_read_windows_key(lambda: next(values)), "F5")
        values = iter(["\x00", "="])
        self.assertEqual(_read_windows_key(lambda: next(values)), "F3")

    def test_element_help_suggestions_take_vertical_focus_from_inventory(self):
        tui = object.__new__(LanctlTui)
        tui.command = ""
        tui.cursor = 0
        tui.command_suggestions = [(1, "element "), (2, "element -add ")]
        tui.suggestion_index = -1
        tui.output_focus = False
        tui.detail_lines = []
        tui.move = lambda _delta: self.fail("las flechas movieron el inventario superior")

        tui.handle_key("DOWN")
        self.assertEqual(tui.command, "element ")
        self.assertEqual(tui.cursor, len("element "))
        tui.handle_key("DOWN")
        self.assertEqual(tui.command, "element -add ")
        tui.handle_key("UP")
        self.assertEqual(tui.command, "element ")

    def test_full_suggestion_panel_keeps_cursor_on_the_prompt_row(self):
        tui = object.__new__(LanctlTui)
        tui.screen = io.StringIO()
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.list_filter = ("all", "")
        tui.devices = []
        tui.index = 0
        tui.messages = list(TUI_ELEMENT_HELP)
        tui.command_suggestions = list(TUI_ELEMENT_SUGGESTIONS)
        tui.suggestion_index = -1
        tui.output_focus = False
        tui.output_selectable = []
        tui.scanning = False
        tui.pending_confirmation = None
        tui.secret_prompt = ""
        tui.command = ""
        tui.cursor = 0
        tui._dimensions = lambda: (100, 30)
        tui._inventory_lines = lambda _width, height: ["INVENTORY"] * (height + 2)
        tui._status_lines = lambda _width: ["STATUS"] * 3
        tui._selection_label = lambda: "-"

        tui.render()

        rendered, cursor = tui.screen.getvalue().rsplit("\x1b[", 1)
        rows = rendered.splitlines()
        self.assertEqual(len(rows), 30)
        self.assertIn(LIST_ELEMENT_PANEL, rendered)
        self.assertIn(CLI_PANEL, rendered)
        self.assertIn("LANCTL[-]>", rows[28])
        self.assertIn("F1", rows[29])
        self.assertTrue(cursor.startswith("29;"))

    def test_scan_progress_uses_last_list_element_row(self):
        tui = object.__new__(LanctlTui)
        tui.devices = []
        tui.dhcp_range = None
        tui.scan_total = 100
        tui.scan_current = 25
        tui.scan_visible_devices = set()
        tui.scanning = True
        tui.index = 0
        tui.scroll = 0
        tui.output_focus = False
        tui.active_devices = set()
        tui.response_ms = {}
        tui._progress_line = lambda _width: "SCAN-PROGRESS"

        lines = tui._inventory_lines(100, 10)

        self.assertEqual(len(lines), 12)
        self.assertEqual(lines[-1], "SCAN-PROGRESS")
        self.assertTrue(all(not line for line in lines[2:-1]))

    def test_typing_after_suggestion_returns_arrows_to_cursor_control(self):
        tui = object.__new__(LanctlTui)
        tui.command = "element -name "
        tui.cursor = len(tui.command)
        tui.command_suggestions = [(1, tui.command)]
        tui.suggestion_index = 0
        tui.output_focus = False
        tui.detail_lines = []

        tui.handle_key("R")
        self.assertEqual(tui.command, "element -name R")
        self.assertEqual(tui.command_suggestions, [])
        tui.handle_key("LEFT")
        self.assertEqual(tui.cursor, len(tui.command) - 1)

    def test_last_status_line_ignores_empty_lines(self):
        self.assertEqual(_last_meaningful_line("uno\n\ndos\n"), "dos")

    def test_function_bar_uses_keycap_background(self):
        from colorama import Back, Fore

        rendered = _function_bar(120)
        self.assertIn(Back.WHITE + Fore.BLACK + " F1 ", rendered)
        self.assertIn(Back.WHITE + Fore.BLACK + " F3 ", rendered)
        self.assertIn(Back.BLACK + Fore.WHITE + " Ayuda", rendered)

    def test_function_bar_resizes_and_distributes_shortcuts(self):
        from rich.text import Text

        for width in (40, 80, 120, 210):
            rendered = _function_bar(width)
            self.assertEqual(Text.from_ansi(rendered).cell_len, width)
            self.assertIn("F1", Text.from_ansi(rendered).plain)
            self.assertIn("Esc", Text.from_ansi(rendered).plain)
        wide = Text.from_ansi(_function_bar(210)).plain
        self.assertGreater(wide.index("F2") - wide.index("Ayuda"), 5)

    def test_scan_spinner_uses_requested_sequence(self):
        self.assertEqual(
            [_spinner_character(index) for index in range(8)],
            ["\\", "|", "/", "-", "\\", "|", "/", "-"],
        )

    def test_inventory_expands_columns_to_available_width(self):
        fields = ("IP", "description", "manufacturer")
        widths = {"IP": 15, "description": 42, "manufacturer": 18}
        _expand_tui_widths(widths, fields, available=100, gap=2)
        self.assertEqual(sum(widths.values()) + 4, 100)

    def test_group_add_and_remove_inherit_selected_tui_element(self):
        mac = "02:00:3F:00:51:0C"
        self.assertEqual(
            _inject_selected_group_element(["group", "ASSETS", "-add"], mac),
            ["group", "ASSETS", "-add", mac],
        )
        self.assertEqual(
            _inject_selected_group_element(["group", "ASSETS", "-add", "NAS"], mac),
            ["group", "ASSETS", "-add", "NAS"],
        )
        self.assertEqual(
            _inject_selected_group_element(["group", "ASSETS", "-remove"], mac),
            ["group", "ASSETS", "-remove", mac],
        )


if __name__ == "__main__":
    unittest.main()
