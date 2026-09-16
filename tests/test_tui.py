import io
import json
import queue
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from lanctl.apps.ip.interfaces.cli.main import build_parser
from lanctl.apps.ip.interfaces.tui.keyboard import DEFAULT_TUI_KEY_BINDINGS, read_posix_key
from lanctl.apps.ip.interfaces.tui.main import (
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
    _device_user_labels,
    _dhcp_boundary_indexes,
    _fit_ansi,
    _function_bar,
    _help_command_entries,
    _inject_selected_group_element,
    _is_interactive_terminal,
    _last_meaningful_line,
    _parse_list_filter,
    _read_windows_key,
    _selectable_output_indexes,
    _spinner_character,
    _translate_tui_element,
    _TuiScanProgress,
)
from lanctl.apps.ip.interfaces.tui.modal import HelpCommand, ModalState, SettingField


class TuiTests(unittest.TestCase):
    def test_users_column_describes_credential_accesses_not_device_capabilities(self):
        device = SimpleNamespace(
            protocols=["ssh", "https"],
            credentials={"ssh": "cred_admin", "tr-064": "cred_router"},
        )
        self.assertEqual(
            _device_user_labels(
                device,
                {"cred_admin": "admin", "cred_router": "operator"},
            ),
            "admin@ssh,operator@tr-064",
        )
        self.assertEqual(_device_user_labels(device, {}), "?@ssh,?@tr-064")

    def test_text_and_secret_dialogs_use_platform_independent_semantic_keys(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.secret_prompt = ""
        tui.render = Mock()
        keys = iter(("h", "o", "BACKSPACE", "i", "ENTER"))
        tui._read_key = lambda: next(keys)

        self.assertEqual(tui._read_text("Nombre:"), "hi")

        keys = iter(("s", "3", "BACKSPACE", "e", "ENTER"))
        tui._read_key = lambda: next(keys)
        self.assertEqual(tui._read_secret("Clave:"), "se")
        self.assertEqual(tui.secret_prompt, "")

    def test_scan_progress_publishes_events_and_honours_cancellation(self):
        events = queue.Queue()
        cancelled = threading.Event()
        progress = _TuiScanProgress(events, cancelled)
        progress.begin(10)
        progress.found("192.0.2.1")
        progress.advance(2)

        self.assertEqual(events.get_nowait(), ("begin", 10))
        self.assertEqual(events.get_nowait(), ("found", ("192.0.2.1",)))
        self.assertEqual(events.get_nowait(), ("advance", 2))
        cancelled.set()
        with self.assertRaises(InterruptedError):
            progress.advance()

    def test_refresh_starts_a_background_worker_and_second_request_does_not_overlap(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.scanning = False
        tui.database = Mock()
        tui.database.load.return_value = []
        tui.list_filter = ("all", "")
        tui.scan_events = queue.Queue()
        tui.messages = []
        started = []

        class FakeThread:
            def __init__(self, *, target, **_kwargs):
                self.target = target

            def start(self):
                started.append(self.target)

        with patch("lanctl.apps.ip.interfaces.tui.main.threading.Thread", FakeThread):
            tui.refresh()
            tui.refresh()

        self.assertTrue(tui.scanning)
        self.assertEqual(started, [tui._run_refresh])
        self.assertIn("Ya hay un escaneo", tui.messages[0])

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
            patch("lanctl.apps.ip.interfaces.tui.main.os.name", "nt"),
            patch("lanctl.apps.ip.interfaces.tui.main.sys.stdin", io.StringIO()),
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
        self.assertEqual(_read_windows_key(lambda: "\x18"), "CTRL_X")
        self.assertEqual(_read_windows_key(lambda: "\x0a"), "CTRL_J")
        self.assertEqual(_read_windows_key(lambda: "\x06"), "CTRL_F")
        self.assertEqual(_read_windows_key(lambda: "\x12"), "CTRL_R")
        self.assertEqual(_read_windows_key(lambda: "\x05"), "CTRL_E")
        self.assertEqual(_read_windows_key(lambda: "\x07"), "CTRL_G")
        self.assertEqual(_read_windows_key(lambda: "\x10"), "CTRL_P")
        self.assertEqual(_read_windows_key(lambda: "\x0f"), "CTRL_O")
        self.assertEqual(_read_windows_key(lambda: "\x04"), "CTRL_D")
        self.assertEqual(_read_windows_key(lambda: "\x0c"), "CTRL_L")
        self.assertEqual(_read_windows_key(lambda: "\x0e"), "CTRL_N")
        self.assertEqual(_read_windows_key(lambda: "\x11"), "CTRL_Q")

    def test_ctrl_n_creates_projects_only_inside_project_manager(self):
        tui = LanctlTui.__new__(LanctlTui)
        calls = []
        tui._create_project_from_manager = lambda: calls.append("new")
        tui.modal = ModalState("projects", "PROJECT MANAGER", ["Proyectos"], [[]])
        tui._handle_modal_key("CTRL_N")
        self.assertEqual(calls, ["new"])

        tui.modal = ModalState("plugins", "PLUGIN", ["Plugins"], [[]])
        tui._handle_modal_key("CTRL_N")
        self.assertEqual(calls, ["new"])

    def test_ctrl_s_saves_active_project_while_project_manager_is_open(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.modal = ModalState("projects", "PROJECT MANAGER", ["Proyectos"], [[]])
        tui.messages = []
        tui._manual_save = Mock(side_effect=lambda: tui.messages.append("Proyecto guardado"))
        tui._update_manager_detail = Mock()

        tui.handle_key("CTRL_S")

        tui._manual_save.assert_called_once_with()
        self.assertIn("Proyecto guardado", tui.modal.footer)

    def test_ctrl_s_does_not_save_settings_directly(self):
        field = SettingField("workers", "Workers", "--workers", "64", "64", "entero")
        tui = LanctlTui.__new__(LanctlTui)
        tui.modal = ModalState("settings", "SETTINGS", ["GENERAL"], [[]], items=[field])
        tui._manual_save = Mock()
        tui._save_settings = Mock()

        tui.handle_key("CTRL_S")

        tui._manual_save.assert_not_called()
        tui._save_settings.assert_not_called()

    def test_settings_exit_menu_saves_through_the_settings_command(self):
        tui = LanctlTui.__new__(LanctlTui)
        fields = [
            SettingField("workers", "Workers", "--workers", "64", "64", "entero"),
            SettingField("timeout", "Timeout", "--timeout", "0.8", "0.8", "segundos"),
        ]
        tui.modal = ModalState(
            "settings", "SETTINGS", ["Configuración", "EXIT"], [[], []], items=fields
        )
        captured = []
        tui._capture = lambda argv: captured.append(argv) or (0, "guardado")
        tui.reload = lambda: None
        tui._set_command_output = lambda output, result: None

        tui.handle_key("TAB")
        tui.handle_key("1")
        tui.handle_key("2")
        tui.handle_key("8")
        tui.handle_key("TAB")
        tui.handle_key("ESC")
        self.assertEqual(tui.modal.tabs[tui.modal.tab_index], "EXIT")
        tui.handle_key("ENTER")

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

    def test_settings_escape_opens_exit_menu_and_can_discard(self):
        field = SettingField("workers", "Workers", "--workers", "32", "64")
        tui = LanctlTui.__new__(LanctlTui)
        tui.messages = []
        tui.modal = ModalState("settings", "SETTINGS", ["GENERAL", "EXIT"], [[], []], items=[field])

        tui._handle_settings_key(tui.modal, "ESC")
        self.assertEqual(tui.modal.tabs[tui.modal.tab_index], "EXIT")
        self.assertIn("Cambios pendientes: 1", "\n".join(tui._modal_page(tui.modal)))
        tui._handle_settings_key(tui.modal, "DOWN")
        tui._handle_settings_key(tui.modal, "ENTER")

        self.assertIsNone(tui.modal)
        self.assertEqual(tui.messages, ["SETTINGS: cambios descartados."])

    def test_project_manager_new_project_opens_inline_form(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui._last_screen_lines = []
        tui.modal = ModalState("projects", "PROJECT MANAGER", ["Proyectos"], [[]])

        with (
            patch("lanctl.apps.ip.interfaces.tui.main.load_config", return_value={}),
            patch(
                "lanctl.core.projects.paths.default_project_directory",
                return_value=Path("C:/Projects"),
            ),
        ):
            tui._create_project_from_manager()

        self.assertEqual(tui.modal.kind, "project_create")
        self.assertEqual(tui.modal.selected, 0)
        self.assertEqual(tui.modal.items[0].key, "name")
        for key in "Casa":
            tui._handle_project_create_key(tui.modal, key)
        tui._handle_project_create_key(tui.modal, "ENTER")
        self.assertEqual(tui.modal.items[0].value, "Casa")
        self.assertEqual(tui.modal.selected, 1)
        self.assertEqual(tui.modal.items[1].value, str(Path("C:/Projects")))

    def test_project_switch_with_pending_changes_requires_an_explicit_decision(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui._last_screen_lines = []
        tui.pending_project_path = None
        tui.modal = ModalState("projects", "PROJECT MANAGER", ["Proyectos"], [[]])

        with (
            patch(
                "lanctl.apps.ip.interfaces.tui.main.load_config",
                return_value={"activeProject": "C:/Projects/Actual.vlf"},
            ),
            patch("lanctl.core.projects.save_policy.workspace_is_dirty", return_value=True),
        ):
            tui._request_project_activation(Path("C:/Projects/Otro.vlf"))

        self.assertEqual(tui.modal.kind, "project_switch")
        self.assertEqual(tui.modal.items, ["save", "discard", "cancel"])
        self.assertTrue(tui.pending_project_path.endswith("Otro.vlf"))

    def test_project_switch_discard_is_explicit(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.pending_project_path = "C:/Projects/Otro.vlf"
        tui.modal = ModalState(
            "project_switch",
            "CAMBIOS SIN GUARDAR",
            ["Cambiar proyecto"],
            [[]],
            selected=1,
            items=["save", "discard", "cancel"],
        )
        calls = []
        tui._activate_project_path = lambda path, discard_changes=False: calls.append(
            (path, discard_changes)
        )

        tui._handle_project_switch_key(tui.modal, "ENTER")

        self.assertEqual(calls, [("C:/Projects/Otro.vlf", True)])
        self.assertIsNone(tui.pending_project_path)

    def test_settings_uses_category_menus_and_contextual_descriptions(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui._last_screen_lines = []
        tui.modal = None

        tui.show_settings()

        self.assertEqual(
            tui.modal.tabs,
            [
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
            ],
        )
        general_page = "\n".join(tui._modal_page(tui.modal))
        self.assertIn("DESCRIPCIÓN", general_page)
        self.assertIn("Define qué columnas", general_page)
        tui.modal.tab_index = tui.modal.tabs.index("TECLADO")
        keyboard_page = "\n".join(tui._modal_page(tui.modal))
        self.assertIn("CAMPO", keyboard_page)
        self.assertIn("TECLA/VALOR", keyboard_page)
        self.assertIn("VISIBLE", keyboard_page)
        self.assertIn("Ayuda", keyboard_page)
        self.assertIn("F1", keyboard_page)
        self.assertNotIn("Mostrar Ayuda", keyboard_page)
        self.assertIn("Historial del elemento", keyboard_page)
        self.assertIn("None", keyboard_page)
        keyboard_indices = tui._settings_field_indices(tui.modal)
        tui.modal.selected = keyboard_indices[0]
        selected_keyboard = tui.modal.items[tui.modal.selected]
        previous_visibility = selected_keyboard.visible
        tui._handle_settings_key(tui.modal, "ENTER")
        self.assertNotEqual(selected_keyboard.visible, previous_visibility)
        self.assertEqual(selected_keyboard.value, selected_keyboard.original)
        tui.modal.tab_index = 0

        tui._handle_settings_key(tui.modal, "RIGHT")
        self.assertEqual(tui.modal.tabs[tui.modal.tab_index], "APARIENCIA")
        selected = tui.modal.items[tui.modal.selected]
        self.assertEqual(selected.section, "APARIENCIA")
        first_key = selected.key
        tui._handle_settings_key(tui.modal, "DOWN")
        self.assertNotEqual(tui.modal.items[tui.modal.selected].key, first_key)

    def test_remote_access_settings_opens_the_masked_user_manager(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui._last_screen_lines = []
        tui.modal = None
        tui.messages = []
        tui.show_settings()
        tui.modal.tab_index = tui.modal.tabs.index("REMOTE ACCESS")
        remote_indices = tui._settings_field_indices(tui.modal)
        tui.modal.selected = remote_indices[-1]

        with patch.object(
            tui,
            "_remote_access_capture",
            return_value=(
                0,
                json.dumps(
                    [
                        {
                            "username": "administrator",
                            "roles": ["administrator"],
                            "enabled": True,
                            "passwordConfigured": True,
                        }
                    ]
                ),
            ),
        ):
            tui._handle_settings_key(tui.modal, "ENTER")

        self.assertEqual(tui.modal.kind, "remote_users")
        rendered = "\n".join(tui._modal_page(tui.modal))
        self.assertIn("administrator", rendered)
        self.assertIn("CONFIGURADA", rendered)
        self.assertNotIn("passwordHash", rendered)

    def test_manual_consult_to_close_opens_a_modal_and_can_cancel_exit(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui._last_screen_lines = ["INVENTARIO"]
        tui.modal = None
        tui.messages = []
        tui.running = True
        settings = {
            "projectSaveMode": "manual.consultToClose",
            "activeProject": "C:/Projects/office.vlf",
        }
        with (
            patch("lanctl.apps.ip.interfaces.tui.main.load_config", return_value=settings),
            patch("lanctl.core.projects.save_policy.workspace_is_dirty", return_value=True),
        ):
            tui._begin_close()

        self.assertEqual(tui.modal.kind, "project_close")
        self.assertTrue(tui.running)
        tui._handle_project_close_key(tui.modal, "ESC")
        self.assertIsNone(tui.modal)
        self.assertTrue(tui.running)

    def test_close_modal_passes_discard_decision_to_common_shutdown(self):
        from lanctl.core.projects.save_policy import _consume_close_answer

        tui = LanctlTui.__new__(LanctlTui)
        tui.running = True
        tui.modal = ModalState(
            "project_close",
            "CAMBIOS SIN GUARDAR",
            ["Cerrar"],
            [["Guardar", "Descartar"]],
            items=["save", "discard"],
            selected=1,
        )

        tui._handle_project_close_key(tui.modal, "ENTER")

        self.assertFalse(tui.running)
        self.assertEqual(_consume_close_answer(), "discard")

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
        with patch("lanctl.core.history.HistoryService") as service:
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

    def test_secret_input_uses_the_tui_prompt_and_never_echoes_characters(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.secret_prompt = ""
        observed_prompts = []
        tui.render = lambda: observed_prompts.append(tui.secret_prompt)

        with (
            patch("lanctl.apps.ip.interfaces.tui.main.os.name", "nt"),
            patch.dict(
                "sys.modules",
                {
                    "msvcrt": SimpleNamespace(
                        getwch=Mock(side_effect=["s", "e", "x", "\x08", "c", "\r"])
                    )
                },
            ),
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
            ["element", selected, "-name", "Rack", "Principal"],
        )
        self.assertEqual(
            _translate_tui_element(["element", "192.168.1.35", "-alias", "RPI"], selected),
            ["element", "192.168.1.35", "-alias", "RPI"],
        )
        self.assertEqual(
            _translate_tui_element(
                ["element", "-name", "Rack", "-alias", "RACK", "-cnf", "O"],
                selected,
            ),
            [
                "element",
                selected,
                "-name",
                "Rack",
                "-alias",
                "RACK",
                "-cnf",
                "O",
            ],
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
        from lanctl.apps.ip.interfaces.tui.main import LanctlTui

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
        self.assertEqual((tui.modal.max_width, tui.modal.max_height), (90, 26))
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

    def test_help_modal_navigates_commands_and_opens_live_detail(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui._last_screen_lines = ["PANTALLA PRINCIPAL"]
        tui.modal = None
        tui.command = ""
        tui.cursor = 0
        tui.messages = []

        tui.show_help_modal()
        first = tui.modal.items[0]
        tui._handle_help_key(tui.modal, "DOWN")
        selected = tui.modal.items[tui.modal.selected]

        self.assertNotEqual(selected.name, first.name)
        self.assertIn(f"LANCTL {selected.name}", "\n".join(tui.modal.pages[1]))
        tui._handle_help_key(tui.modal, "ENTER")
        self.assertEqual(tui.modal.tab_index, 1)

    def test_help_tab_prepares_selected_command_in_prompt(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.command = ""
        tui.cursor = 0
        tui.messages = []
        entry = HelpCommand("scan", "Escanea un elemento", "Usage: LANCTL scan")
        tui.modal = ModalState(
            "help",
            "HELP",
            ["Comandos", "Detalle", "Teclas"],
            [[], [], []],
            items=[entry],
        )

        tui._handle_help_key(tui.modal, "TAB")

        self.assertIsNone(tui.modal)
        self.assertEqual(tui.command, "scan ")
        self.assertEqual(tui.cursor, len(tui.command))
        self.assertIn("Comando preparado", tui.messages[0])

    def test_help_catalog_is_generated_from_the_real_parser(self):
        entries = _help_command_entries()
        names = {entry.name for entry in entries}

        self.assertIn("list", names)
        self.assertIn("settings", names)
        self.assertIn("project", names)
        project = next(entry for entry in entries if entry.name == "project")
        self.assertIn("create", project.subcommands)
        self.assertTrue(project.usage)

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
                "lanctl.apps.ip.interfaces.tui.main.load_config",
                return_value={
                    "database": "projects/casa/devices.json",
                    "dhcpRange": "192.168.1.20-192.168.1.100",
                },
            ),
            patch("lanctl.apps.ip.interfaces.tui.main.DeviceDatabase") as database_type,
            patch(
                "lanctl.apps.ip.interfaces.tui.main.active_project_info",
                return_value={"name": "Casa"},
            ),
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

    def test_posix_control_and_escape_keys_are_decoded(self):
        self.assertEqual(read_posix_key(io.StringIO("\x13")), "CTRL_S")
        self.assertEqual(read_posix_key(io.StringIO("\x0e")), "CTRL_N")
        stream = io.StringIO("\x1b[A")
        with patch("select.select", return_value=([stream], [], [])):
            self.assertEqual(read_posix_key(stream), "UP")
        stream = io.StringIO("\x1b[24~")
        with patch("select.select", return_value=([stream], [], [])):
            self.assertEqual(read_posix_key(stream), "F12")

    def test_posix_fragmented_arrow_waits_for_complete_sequence(self):
        class FragmentedInput:
            def __init__(self, delay):
                self.clock = 0.0
                self.events = [(0.0, "\x1b"), (delay, "["), (delay, "B")]

            def read(self, _size):
                return self.events.pop(0)[1]

            def select(self, streams, _write, _errors, timeout):
                if self.events and self.events[0][0] <= self.clock + timeout:
                    self.clock = max(self.clock, self.events[0][0])
                    return streams, [], []
                self.clock += timeout
                return [], [], []

        for delay in (0.03, 0.05, 0.08):
            with self.subTest(delay=delay):
                stream = FragmentedInput(delay)
                with (
                    patch("select.select", side_effect=stream.select),
                    patch("time.monotonic", side_effect=lambda: stream.clock),
                ):
                    self.assertEqual(read_posix_key(stream), "DOWN")

    def test_posix_ss3_arrows_and_all_function_keys_are_decoded(self):
        sequences = {
            "OA": "UP",
            "OB": "DOWN",
            "OC": "RIGHT",
            "OD": "LEFT",
            "OP": "F1",
            "OQ": "F2",
            "OR": "F3",
            "OS": "F4",
            "[15~": "F5",
            "[17~": "F6",
            "[18~": "F7",
            "[19~": "F8",
            "[20~": "F9",
            "[21~": "F10",
            "[23~": "F11",
            "[24~": "F12",
        }
        for sequence, expected in sequences.items():
            with self.subTest(sequence=sequence):
                stream = io.StringIO("\x1b" + sequence)
                with patch("select.select", return_value=([stream], [], [])):
                    self.assertEqual(read_posix_key(stream), expected)

    def test_posix_standalone_escape_waits_until_deadline(self):
        stream = io.StringIO("\x1b")
        clock = [0.0]

        def unavailable(_read, _write, _errors, timeout):
            clock[0] += timeout
            return [], [], []

        with (
            patch("select.select", side_effect=unavailable),
            patch("time.monotonic", side_effect=lambda: clock[0]),
        ):
            self.assertEqual(read_posix_key(stream), "ESC")
        self.assertAlmostEqual(clock[0], 0.15)

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

    def test_inventory_hides_detection_dates_and_gives_group_more_width(self):
        from rich.text import Text

        tui = object.__new__(LanctlTui)
        tui.devices = [
            SimpleNamespace(
                ip="192.168.1.10",
                mac="AA:BB:CC:DD:EE:FF",
                cnf="O",
                alias="SW",
                name="Switch",
                groups=["INFRAESTRUCTURA"],
                description="-",
                discovery_methods=["ICMP", "ARP"],
                last_discovery="ICMP+ARP",
                last_seen="2026-09-12T12:30:00+02:00",
                manufacturer="Cisco",
                protocols=[],
            )
        ]
        tui.dhcp_range = None
        tui.scan_total = 0
        tui.index = 0
        tui.scroll = 0
        tui.output_focus = False
        tui.active_devices = {_device_key(tui.devices[0].mac, tui.devices[0].ip)}
        tui.response_ms = {}
        tui.local_ip = ""

        lines = tui._inventory_lines(210, 4)
        header = Text.from_ansi(lines[0]).plain

        self.assertNotIn("DETECTION", header)
        self.assertNotIn("LAST SEEN", header)
        self.assertIn("GROUP", header)
        self.assertIn("USERS", header)
        self.assertNotIn("PROTOCOLS", header)
        self.assertIn("INFRAESTRUCTURA", Text.from_ansi(lines[2]).plain)

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
        wide = Text.from_ansi(_function_bar(210)).plain
        self.assertGreater(wide.index("F2") - wide.index("Ayuda"), 5)
        for expected in ("F1", "F2", "F3", "F5", "F7", "F9", "F12", "↑↓"):
            self.assertIn(expected, wide)
        for hidden in ("Ctrl+H", "Ctrl+F", "Ctrl+S", "Enter", "Esc"):
            self.assertNotIn(hidden, wide)

    def test_function_bar_respects_visible_buttons_and_custom_keys(self):
        from rich.text import Text

        rendered = Text.from_ansi(
            _function_bar(
                100,
                ["help", "copyJson", "exit"],
                {"help": "F4", "copyJson": "CTRL_X"},
            )
        ).plain
        self.assertIn("F4", rendered)
        self.assertIn("Ctrl+X", rendered)
        self.assertIn("Esc", rendered)
        self.assertNotIn("F2", rendered)
        unassigned = Text.from_ansi(_function_bar(100, ["deviceHistory", "exit"], {})).plain
        self.assertNotIn("Historial", unassigned)
        self.assertIn("Esc", unassigned)

    def test_copy_selected_supports_full_line_and_requested_json_shape(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.devices = [
            SimpleNamespace(
                device_id="dev_123",
                mac="AA:BB:CC:DD:EE:FF",
                ip="192.168.1.20",
                cnf="O",
                alias="NAS",
                name="Storage",
                groups=["ASSETS"],
                description="Almacenamiento",
            )
        ]
        tui.index = 0
        copied = []
        with patch(
            "lanctl.apps.ip.interfaces.tui.clipboard.copy_text",
            side_effect=copied.append,
        ):
            tui._copy_selected(as_json=False)
            tui._copy_selected(as_json=True)

        self.assertEqual(
            copied[0],
            "192.168.1.20\tO\tNAS\tAA:BB:CC:DD:EE:FF\tStorage\tASSETS\tAlmacenamiento",
        )
        self.assertEqual(
            list(json.loads(copied[1])),
            ["idf", "mac", "ip", "cnf", "alias", "name", "group", "description"],
        )

    def test_configured_key_dispatches_manual_save(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.modal = None
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.output_focus = False
        tui.command_suggestions = []
        tui.command = ""
        tui.cursor = 0
        tui.key_bindings = {**DEFAULT_TUI_KEY_BINDINGS, "save": "F4"}
        tui._manual_save = Mock()

        tui.handle_key("F4")

        tui._manual_save.assert_called_once_with()

    def test_manual_save_reports_updated_project_in_cli_panel(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.messages = []
        tui.output_focus = True
        tui.output_selectable = [8]
        tui.output_index = 0
        tui.output_scroll = 8
        tui.reload = Mock()
        saved = SimpleNamespace(saved=True, path="C:/Projects/Casa.vlf", reason="saved")

        with (
            patch("lanctl.apps.ip.interfaces.tui.main.load_config", return_value={}),
            patch("lanctl.core.projects.save_policy.workspace_is_dirty", return_value=True),
            patch("lanctl.core.projects.save_policy.save_active_project", return_value=saved),
        ):
            tui._manual_save()

        self.assertEqual(
            tui.messages,
            ["Proyecto guardado correctamente: C:/Projects/Casa.vlf (cambios aplicados)."],
        )
        self.assertFalse(tui.output_focus)
        self.assertEqual(tui.output_selectable, [])
        self.assertEqual(tui.output_scroll, 0)
        tui.reload.assert_called_once_with()

    def test_manual_save_reports_saved_project_when_already_synchronized(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.messages = []
        tui.output_focus = False
        tui.output_selectable = []
        tui.output_index = 0
        tui.output_scroll = 0
        tui.reload = Mock()
        saved = SimpleNamespace(saved=True, path="C:/Projects/Casa.vlf", reason="saved")

        with (
            patch("lanctl.apps.ip.interfaces.tui.main.load_config", return_value={}),
            patch("lanctl.core.projects.save_policy.workspace_is_dirty", return_value=False),
            patch("lanctl.core.projects.save_policy.save_active_project", return_value=saved),
        ):
            tui._manual_save()

        self.assertEqual(
            tui.messages,
            ["Proyecto guardado correctamente: C:/Projects/Casa.vlf (sin cambios pendientes)."],
        )

    def test_navigation_shortcuts_prepare_contextual_commands(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.modal = None
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.output_focus = False
        tui.output_selectable = []
        tui.command_suggestions = []
        tui.suggestion_index = -1
        tui.command = ""
        tui.cursor = 0
        tui.key_bindings = DEFAULT_TUI_KEY_BINDINGS

        for key, expected in (
            ("CTRL_F", "search "),
            ("CTRL_E", "element "),
            ("CTRL_G", "group "),
            ("CTRL_O", "open "),
        ):
            tui.handle_key(key)
            self.assertEqual(tui.command, expected)

    def test_reload_shortcut_does_not_start_network_scan(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.modal = None
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.output_focus = False
        tui.command_suggestions = []
        tui.command = ""
        tui.cursor = 0
        tui.key_bindings = DEFAULT_TUI_KEY_BINDINGS
        tui.reload = Mock()
        tui.refresh = Mock()

        tui.handle_key("CTRL_R")

        tui.reload.assert_called_once_with()
        tui.refresh.assert_not_called()

    def test_optional_action_does_nothing_until_the_user_assigns_a_key(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.modal = None
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.output_focus = False
        tui.command_suggestions = []
        tui.command = ""
        tui.cursor = 0
        tui.key_bindings = {**DEFAULT_TUI_KEY_BINDINGS, "deviceHistory": "F6"}
        tui.show_history = Mock()

        tui.handle_key("F6")

        tui.show_history.assert_called_once_with()

    def test_scan_spinner_uses_requested_sequence(self):
        self.assertEqual(
            [_spinner_character(index) for index in range(8)],
            ["\\", "|", "/", "-", "\\", "|", "/", "-"],
        )

    def test_cli_top_places_prompt_on_second_terminal_row(self):
        tui = LanctlTui.__new__(LanctlTui)
        tui.modal = None
        tui.detail_lines = []
        tui.view_state = "inventory"
        tui.list_filter = ("all", "")
        tui.devices = []
        tui.index = 0
        tui.history_events = []
        tui.history_index = 0
        tui.command_history = []
        tui.command_history_index = 0
        tui.output_focus = False
        tui.output_selectable = []
        tui.output_index = 0
        tui.output_scroll = 0
        tui.command_suggestions = []
        tui.suggestion_index = -1
        tui.messages = ["salida del comando"]
        tui.secret_prompt = ""
        tui.scanning = False
        tui.pending_confirmation = None
        tui.spinner_index = 0
        tui.command = "list"
        tui.cursor = 4
        tui.panel_layout = "cli.top"
        tui.cli_height_percent = 30
        tui.footer_buttons = []
        tui.key_bindings = {}
        tui.renderer = Mock()
        tui.screen = io.StringIO()
        tui._dimensions = lambda: (100, 30)
        tui._status_lines = lambda _width: []
        tui._inventory_lines = lambda _width, height: ["INVENTARIO"] * (height + 2)

        tui.render()

        lines = tui.renderer.render_screen.call_args.args[0]
        self.assertIn("LANCTL[-]> list", lines[1])
        self.assertEqual(tui.renderer.render_screen.call_args.kwargs["cursor_row"], 2)
        self.assertTrue(any("ListElement" in line for line in lines[2:]))

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
