import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lanctl.apps.ip.interfaces.cli.commands.modes import (
    CliSelection,
    _clear_screen,
    _selected_command,
    run_global_cli,
)
from lanctl.apps.ip.interfaces.cli.main import _should_close_active_project, build_parser
from lanctl.core.database import DeviceDatabase
from lanctl.core.group_database import GroupDatabase


class LanctlModeTests(unittest.TestCase):
    def test_non_interactive_command_does_not_prompt_on_close_by_default(self):
        settings = {
            "projectSaveMode": "manual.inCloseConsult",
            "cliPromptSaveOnCommandExit": False,
        }
        self.assertFalse(_should_close_active_project(False, settings))
        self.assertTrue(_should_close_active_project(True, settings))
        settings["cliPromptSaveOnCommandExit"] = True
        self.assertTrue(_should_close_active_project(False, settings))

    def test_project_without_action_reports_the_active_project(self):
        args = build_parser().parse_args(["project"])
        output = io.StringIO()
        with (
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.project.active_project_info",
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

    def test_project_option_activates_the_vlf_before_opening_the_default_tui(self):
        from pathlib import Path

        from lanctl.apps.ip.interfaces.cli.main import main

        project_path = "C:/Users/Victor/Desktop/Casa.vlf"
        parser = build_parser(include_plugin_commands=False)
        workspace = SimpleNamespace(
            project=Path(project_path),
            project_id="project-casa",
        )
        with (
            patch("lanctl.apps.ip.interfaces.cli.main.configure_utf8_stdio"),
            patch("lanctl.core.data_migration.ensure_data_layout"),
            patch("lanctl.apps.ip.interfaces.cli.main.run_automatic_log_cleanup"),
            patch("lanctl.shared.i18n.initialize_language"),
            patch("lanctl.shared.assets.icons.initialize_icons"),
            patch("lanctl.apps.ip.interfaces.cli.main.load_plugin_safe_mode", return_value=True),
            patch("lanctl.core.plugins.get_plugin_manager") as manager_factory,
            patch("lanctl.apps.ip.interfaces.cli.main.write_log"),
            patch("lanctl.apps.ip.interfaces.cli.main.build_parser", return_value=parser),
            patch(
                "lanctl.core.projects.activate_project_workspace",
                return_value=workspace,
            ) as activate,
            patch("lanctl.apps.ip.interfaces.tui.main.run_tui", return_value=0) as tui,
        ):
            result = main(["--project", project_path])

        self.assertEqual(result, 0)
        activate.assert_called_once_with(project_path)
        tui.assert_called_once_with(None)
        manager_factory.return_value.events.emit.assert_called_with(
            "LANCTL.Project.File.Open",
            {"path": str(Path(project_path)), "project_id": "project-casa"},
        )

    def test_gui_is_disabled_without_the_legacy_development_switch(self):
        from lanctl.apps.ip.interfaces.cli.main import main

        with (
            patch.dict("os.environ", {"LANCTL_ENABLE_LEGACY_GUI": ""}),
            patch("lanctl.apps.ip.interfaces.cli.main.configure_utf8_stdio"),
            patch("lanctl.core.data_migration.ensure_data_layout"),
            patch("lanctl.apps.ip.interfaces.cli.main.run_automatic_log_cleanup"),
            patch("lanctl.shared.i18n.initialize_language"),
            patch("lanctl.shared.assets.icons.initialize_icons"),
            patch("lanctl.apps.ip.interfaces.cli.main.load_plugin_safe_mode", return_value=True),
            patch("lanctl.core.plugins.get_plugin_manager"),
            patch("lanctl.apps.ip.interfaces.cli.main.write_log"),
            patch("lanctl.apps.ip.interfaces.cli.main.print_error") as output,
        ):
            self.assertEqual(main(["--gui"]), 2)
        self.assertIn("congelada", output.call_args.args[0])

    def test_cli_flag_is_registered_without_a_scope(self):
        args = build_parser().parse_args(["--cli"])
        self.assertTrue(args.cli)
        self.assertIsNone(args.command)

    def test_cli_flag_opens_the_global_interactive_terminal(self):
        with patch(
            "lanctl.apps.ip.interfaces.cli.main.run_global_cli", return_value=0
        ) as interactive:
            from lanctl.apps.ip.interfaces.cli.main import main

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
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.modes.load_config",
                return_value={"database": "db.json"},
            ),
            patch("lanctl.apps.ip.interfaces.cli.commands.modes.DeviceDatabase") as database_type,
            patch(
                "lanctl.apps.ip.interfaces.cli.main.main",
                side_effect=lambda argv: dispatched.append(argv) or 0,
            ),
            patch("lanctl.apps.ip.interfaces.cli.commands.modes.ok"),
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

    def test_global_cli_executes_semicolon_chained_commands(self):
        values = iter(["element A -cnf O; element B -cnf X", "exit"])
        dispatched = []
        with (
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.modes.load_config",
                return_value={"database": "db.json", "cliCommandChaining": True},
            ),
            patch("lanctl.apps.ip.interfaces.cli.commands.modes.DeviceDatabase"),
            patch(
                "lanctl.apps.ip.interfaces.cli.main.main",
                side_effect=lambda argv: dispatched.append(argv) or 0,
            ),
        ):
            result = run_global_cli(input_fn=lambda _prompt: next(values))

        self.assertEqual(result, 0)
        self.assertEqual(
            dispatched,
            [["element", "A", "-cnf", "O"], ["element", "B", "-cnf", "X"]],
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
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.modes.load_config",
                return_value={"database": "db.json"},
            ),
            patch("lanctl.apps.ip.interfaces.cli.commands.modes.DeviceDatabase") as database_type,
            patch(
                "lanctl.apps.ip.interfaces.cli.main.main",
                side_effect=lambda argv: dispatched.append(argv) or 0,
            ),
            patch("lanctl.apps.ip.interfaces.cli.commands.modes.ok"),
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

    def test_name_and_alias_are_only_available_below_element(self):
        parser = build_parser()
        for removed in ("name", "alias"):
            with self.assertRaises(SystemExit):
                parser.parse_args([removed, "NAS", "valor"])

    def test_element_option_edits_explicit_device_name_and_alias(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = str(Path(temporary) / "devices.json")
            groups_path = str(Path(temporary) / "groups.json")
            database = DeviceDatabase(database_path)
            database.add_device("02:00:00:00:00:11", alias="OLD")
            parser = build_parser()

            for option, value in (("-name", "HomeNAS"), ("-alias", "NAS")):
                args = parser.parse_args(
                    [
                        "element",
                        "02:00:00:00:00:11",
                        option,
                        value,
                        "--database",
                        database_path,
                        "--groups",
                        groups_path,
                    ]
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(args.handler(args), 0)

            updated = database.resolve("02:00:00:00:00:11")
            self.assertEqual(updated.name, "HomeNAS")
            self.assertEqual(updated.alias, "NAS")

    def test_element_option_edits_can_be_chained_in_any_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = str(Path(temporary) / "devices.json")
            groups_path = str(Path(temporary) / "groups.json")
            database = DeviceDatabase(database_path)
            database.add_device("02:00:00:00:00:12", alias="OLD")
            GroupDatabase(groups_path, database).create("IOT")
            args = build_parser().parse_args(
                [
                    "element",
                    "OLD",
                    "-description",
                    "Sensor principal",
                    "-cnf",
                    "O",
                    "-group",
                    "IOT",
                    "-alias",
                    "SENSOR",
                    "-name",
                    "SensorCasa",
                    "-protocol",
                    "ssh",
                    "--database",
                    database_path,
                    "--groups",
                    groups_path,
                ]
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(args.handler(args), 0)

            updated = database.resolve("SENSOR")
            self.assertEqual(updated.name, "SensorCasa")
            self.assertEqual(updated.description, "Sensor principal")
            self.assertEqual(updated.cnf, "O")
            self.assertEqual(updated.groups, ["IOT"])
            self.assertEqual(updated.protocols, ["ssh"])


if __name__ == "__main__":
    unittest.main()
