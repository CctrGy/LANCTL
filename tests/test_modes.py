import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.cli import build_parser
from app.commands.modes import (
    CliSelection, _interactive_loop, _selected_command, run_global_cli,
    run_virtual_mode,
)


class LanctlModeTests(unittest.TestCase):
    def test_gui_flag_is_registered_without_a_scope(self):
        args = build_parser().parse_args(["--gui"])
        self.assertTrue(args.gui)
        self.assertIsNone(args.command)

    def test_selected_element_is_injected_into_contextual_commands(self):
        database = SimpleNamespace(
            resolve=lambda value: (_ for _ in ()).throw(ValueError())
        )
        selected = CliSelection(selector="device:abc", label="SW")
        self.assertEqual(
            _selected_command(["scan", "--ports", "22"], selected, database),
            ["scan", "device:abc", "--ports", "22"],
        )
        self.assertEqual(_selected_command(["list"], selected, database), ["list"])

    def test_global_cli_selects_and_reuses_device(self):
        device = SimpleNamespace(
            device_id="device:sw", mac="AA:BB:CC:DD:EE:FF",
            ip="192.168.1.10", alias="SW", name="Switch",
        )
        values = iter(["select SW", "scan --ports 22", "exit"])
        dispatched = []
        with (
            patch("app.commands.modes.load_config", return_value={"database": "db.json"}),
            patch("app.commands.modes.DeviceDatabase") as database_type,
            patch("app.cli.main", side_effect=lambda argv: dispatched.append(argv) or 0),
            patch("app.commands.modes.ok"),
        ):
            database_type.return_value.resolve.side_effect = (
                lambda selector: device if selector == "SW"
                else (_ for _ in ()).throw(ValueError())
            )
            result = run_global_cli(input_fn=lambda _prompt: next(values))
        self.assertEqual(result, 0)
        self.assertEqual(
            dispatched,
            [["virtual", "scan", "AA:BB:CC:DD:EE:FF", "--ports", "22"]],
        )

    def test_virtual_commands_are_nested(self):
        args = build_parser().parse_args(["virtual", "scan", "ESP", "--ports", "22"])
        self.assertEqual(args.command, "virtual")
        self.assertEqual(args.virtual_command, "scan")
        self.assertEqual(args.selector, "ESP")

    def test_virtual_cli_is_registered_and_physical_scope_is_absent(self):
        virtual = build_parser().parse_args(["virtual", "--cli"])
        self.assertTrue(virtual.cli)
        self.assertIs(virtual.handler, run_virtual_mode)
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["physical", "--cli"])
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["phisic", "--cli"])

    def test_list_active_is_the_connected_filter_alias(self):
        args = build_parser().parse_args(["virtual", "list", "--active"])
        self.assertTrue(args.connected)
        self.assertFalse(args.disconnected)

    def test_element_delete_accepts_mac_and_non_interactive_confirmation(self):
        args = build_parser().parse_args(
            ["virtual", "element", "10:20:30:40:50:60", "delete", "--yes"]
        )
        self.assertEqual(args.action, "delete")
        self.assertTrue(args.yes)

    def test_interactive_scope_dispatches_without_run_prefix(self):
        values = iter(["scan ESP --ports 22", "exit"])
        dispatched = []
        result = _interactive_loop(
            "virtual", "help", dispatched.append,
            input_fn=lambda _prompt: next(values),
        )
        self.assertEqual(result, 0)
        self.assertEqual(dispatched, [["scan", "ESP", "--ports", "22"]])


if __name__ == "__main__":
    unittest.main()
