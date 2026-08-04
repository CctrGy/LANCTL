import unittest
import json
from unittest.mock import patch
from types import SimpleNamespace

from app.cli import build_parser
from app.tui import (
    LanctlTui,
    TUI_ENTER_SCREEN, TUI_LEAVE_SCREEN,
    _clean_tui_output, _compact_timestamp, _device_key, _dhcp_boundary_indexes,
    _expand_tui_widths, _fit_ansi, _function_bar,
    _inject_selected_group_element,
    _last_meaningful_line, _parse_list_filter, _selectable_output_indexes,
    _read_windows_key, _spinner_character, _translate_tui_element,
)


class TuiTests(unittest.TestCase):
    def test_history_view_replaces_inventory_and_escape_restores_selection(self):
        tui=LanctlTui.__new__(LanctlTui); device=SimpleNamespace(device_id="dev_nas",mac="02:11:22:33:44:55",ip="192.168.1.8",alias="NAS",name="NAS")
        tui.devices=[device]; tui.index=0; tui.scroll=4; tui.messages=[]; tui.view_state="inventory"; tui.history_events=[]; tui.history_index=0; tui.detail_lines=[]; tui.output_focus=False
        event=SimpleNamespace(timestamp="2026-08-03T10:00:00+02:00",type="device.detected",summary="Detectado",result="success",source="test",correlationId=None,runId=None,taskId=None,operationId=None,error=None,changes=(),device=SimpleNamespace(label="NAS"))
        with patch("app.core.history.HistoryService") as service:
            service.return_value.query.return_value=[event]; tui.show_history()
        self.assertEqual(tui.view_state,"history"); self.assertEqual(tui.selected,device)
        tui.handle_key("ENTER"); self.assertTrue(tui.detail_lines)
        tui.handle_key("ESC"); self.assertFalse(tui.detail_lines); self.assertEqual(tui.view_state,"history")
        tui.handle_key("ESC"); self.assertEqual(tui.view_state,"inventory"); self.assertEqual(tui.scroll,4)

    def test_tui_uses_an_alternate_non_wrapping_screen(self):
        self.assertIn("\x1b[?1049h", TUI_ENTER_SCREEN)
        self.assertIn("\x1b[?7l", TUI_ENTER_SCREEN)
        self.assertIn("\x1b[?7h", TUI_LEAVE_SCREEN)
        self.assertTrue(TUI_LEAVE_SCREEN.endswith("\x1b[?1049l"))

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
            _translate_tui_element(
                ["element", "192.168.1.35", "-alias", "RPI"], selected
            ),
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

    def test_f2_detail_reports_port_count_without_listing_ports(self):
        from app.tui import LanctlTui

        tui = LanctlTui.__new__(LanctlTui)
        tui.devices = [SimpleNamespace(
            device_id="dev_test", cnf="O", ip="192.168.1.10",
            mac="AA:BB:CC:DD:EE:FF", alias="SW", default_alias="",
            name="Switch", default_name="switch.local", description="Rack",
            manufacturer="Cisco", groups=["GESTOR"], discovery_methods=["ARP"],
            last_discovery="ARP", last_seen="2026-07-26T01:00:00+02:00",
            protocols=["ssh"], credentials={"ssh": "cred_sw"},
            protocol_options={},
        )]
        tui.index = 0
        tui.messages = []
        tui.detail_lines = []
        tui.detail_scroll = 0
        tui.render = lambda: None
        payload = {
            "element": {"manufacturer": "Cisco"},
            "observation": {
                "reachable": True, "observed_mac": "AA:BB:CC:DD:EE:FF",
                "identityMatch": True, "hostname": "switch.local",
                "latency_ms": 1.2, "ttl": 64, "scanned_ports": 51,
                "open_ports": [{"port": 22}, {"port": 443}], "duration": 0.5,
                "identification": {"device_type": "switch", "confidence": "high", "evidence": ["ssh"]},
            },
        }
        tui._capture = lambda _argv: (0, json.dumps(payload))

        tui.show_info()

        detail = "\n".join(tui.detail_lines)
        self.assertIn("Puertos abiertos: 2", detail)
        self.assertNotIn("443", detail)
        self.assertNotIn("22", detail)
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
        self.assertTrue(args.tui)
        self.assertIsNone(args.command)

    def test_windows_function_and_arrow_keys_are_decoded(self):
        values = iter(["\xe0", "H"])
        self.assertEqual(_read_windows_key(lambda: next(values)), "UP")
        values = iter(["\x00", "?"])
        self.assertEqual(_read_windows_key(lambda: next(values)), "F5")
        values = iter(["\x00", "="])
        self.assertEqual(_read_windows_key(lambda: next(values)), "F3")

    def test_element_help_suggestions_cycle_with_lateral_arrows(self):
        tui = object.__new__(LanctlTui)
        tui.command = ""
        tui.cursor = 0
        tui.command_suggestions = [(1, "element "), (2, "element -add ")]
        tui.suggestion_index = -1
        tui.output_focus = False
        tui.detail_lines = []

        tui.handle_key("RIGHT")
        self.assertEqual(tui.command, "element ")
        self.assertEqual(tui.cursor, len("element "))
        tui.handle_key("RIGHT")
        self.assertEqual(tui.command, "element -add ")
        tui.handle_key("LEFT")
        self.assertEqual(tui.command, "element ")

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
            _inject_selected_group_element(
                ["group", "ASSETS", "-add", "NAS"], mac
            ),
            ["group", "ASSETS", "-add", "NAS"],
        )
        self.assertEqual(
            _inject_selected_group_element(["group", "ASSETS", "-remove"], mac),
            ["group", "ASSETS", "-remove", mac],
        )


if __name__ == "__main__":
    unittest.main()
