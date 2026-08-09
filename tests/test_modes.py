import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.cli import build_parser
from app.commands.modes import (
    CliSelection,
    _clear_screen,
    _selected_command,
    run_global_cli,
)


class LanctlModeTests(unittest.TestCase):
    def test_project_without_action_reports_the_active_project(self):
        args = build_parser().parse_args(["project"])
        output = io.StringIO()
        with (
            patch(
                "app.commands.project.active_project_info",
                return_value={
                    "path": "C:/Projects/Casa.vlf",
                    "name": "Casa",
                    "id": "project-1",
                    "available": True,
                    "valid": True,
                },
            ),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(args.handler(args), 0)
        self.assertIn("Casa", output.getvalue())
        self.assertIn("C:/Projects/Casa.vlf", output.getvalue())

    def test_clear_screen_uses_ansi_without_spawning_a_shell(self):
        import io

        stream = io.StringIO()
        _clear_screen(stream)
        self.assertEqual(stream.getvalue(), "\x1b[2J\x1b[H")

    def test_gui_flag_is_registered_without_a_scope(self):
        args = build_parser().parse_args(["--gui"])
        self.assertTrue(args.gui)
        self.assertIsNone(args.command)

    def test_project_option_activates_the_vlf_before_opening_the_gui(self):
        from pathlib import Path

        from app.cli import main

        project_path = "C:/Users/Victor/Desktop/Casa.vlf"
        parser = build_parser(include_plugin_commands=False)
        workspace = SimpleNamespace(
            project=Path(project_path),
            project_id="project-casa",
        )
        with (
            patch("app.cli.configure_utf8_stdio"),
            patch("app.core.data_migration.ensure_data_layout"),
            patch("app.cli.run_automatic_log_cleanup"),
            patch("app.i18n.initialize_language"),
            patch("app.assets.icons.initialize_icons"),
            patch("app.cli.load_plugin_safe_mode", return_value=True),
            patch("app.plugins.get_plugin_manager") as manager_factory,
            patch("app.cli.write_log"),
            patch("app.cli.build_parser", return_value=parser),
            patch(
                "app.projects.activate_project_workspace",
                return_value=workspace,
            ) as activate,
            patch("app.gui.run_gui", return_value=0) as gui,
        ):
            result = main(["--project", project_path])

        self.assertEqual(result, 0)
        activate.assert_called_once_with(project_path)
        gui.assert_called_once_with()
        manager_factory.return_value.events.emit.assert_called_with(
            "LANCTL.Project.File.Open",
            {"path": str(Path(project_path)), "project_id": "project-casa"},
        )

    def test_cli_flag_is_registered_without_a_scope(self):
        args = build_parser().parse_args(["--cli"])
        self.assertTrue(args.cli)
        self.assertIsNone(args.command)

    def test_cli_flag_opens_the_global_interactive_terminal(self):
        with patch("app.cli.run_global_cli", return_value=0) as interactive:
            from app.cli import main

            self.assertEqual(main(["--cli"]), 0)
        interactive.assert_called_once_with()

    def test_selected_element_is_injected_into_contextual_commands(self):
        database = SimpleNamespace(resolve=lambda value: (_ for _ in ()).throw(ValueError()))
        selected = CliSelection(selector="device:abc", label="SW")
        self.assertEqual(
            _selected_command(["scan", "--ports", "22"], selected, database),
            ["scan", "device:abc", "--ports", "22"],
        )
        self.assertEqual(_selected_command(["list"], selected, database), ["list"])

    def test_global_cli_selects_and_reuses_device(self):
        device = SimpleNamespace(
            device_id="device:sw",
            mac="AA:BB:CC:DD:EE:FF",
            ip="192.168.1.10",
            alias="SW",
            name="Switch",
        )
        values = iter(["select SW", "scan --ports 22", "exit"])
        dispatched = []
        with (
            patch("app.commands.modes.load_config", return_value={"database": "db.json"}),
            patch("app.commands.modes.DeviceDatabase") as database_type,
            patch("app.cli.main", side_effect=lambda argv: dispatched.append(argv) or 0),
            patch("app.commands.modes.ok"),
        ):
            database_type.return_value.resolve.side_effect = lambda selector: (
                device if selector == "SW" else (_ for _ in ()).throw(ValueError())
            )
            result = run_global_cli(input_fn=lambda _prompt: next(values))
        self.assertEqual(result, 0)
        self.assertEqual(
            dispatched,
            [["scan", "AA:BB:CC:DD:EE:FF", "--ports", "22"]],
        )

    def test_info_displays_the_selected_element(self):
        device = SimpleNamespace(
            device_id="device:sw",
            mac="AA:BB:CC:DD:EE:FF",
            ip="192.168.1.10",
            alias="SW",
            name="Switch",
        )
        values = iter(["select SW", "info", "exit"])
        dispatched = []
        with (
            patch("app.commands.modes.load_config", return_value={"database": "db.json"}),
            patch("app.commands.modes.DeviceDatabase") as database_type,
            patch("app.cli.main", side_effect=lambda argv: dispatched.append(argv) or 0),
            patch("app.commands.modes.ok"),
        ):
            database_type.return_value.resolve.return_value = device
            run_global_cli(input_fn=lambda _prompt: next(values))
        self.assertEqual(
            dispatched,
            [["element", "AA:BB:CC:DD:EE:FF"]],
        )

    def test_commands_are_registered_at_root(self):
        args = build_parser().parse_args(["scan", "ESP", "--ports", "22"])
        self.assertEqual(args.command, "scan")
        self.assertEqual(args.selector, "ESP")

    def test_removed_scope_is_rejected_and_global_cli_remains(self):
        args = build_parser().parse_args(["--cli"])
        self.assertTrue(args.cli)
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["virtual", "list"])
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["physical", "--cli"])
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["phisic", "--cli"])

    def test_list_active_is_the_connected_filter_alias(self):
        args = build_parser().parse_args(["list", "--active"])
        self.assertTrue(args.connected)
        self.assertFalse(args.disconnected)

    def test_element_delete_accepts_mac_and_non_interactive_confirmation(self):
        args = build_parser().parse_args(["element", "10:20:30:40:50:60", "delete", "--yes"])
        self.assertEqual(args.action, "delete")
        self.assertTrue(args.yes)


if __name__ == "__main__":
    unittest.main()
