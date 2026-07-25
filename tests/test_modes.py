import unittest

from app.cli import build_parser
from app.commands.modes import _interactive_loop, run_virtual_mode


class LanctlModeTests(unittest.TestCase):
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
