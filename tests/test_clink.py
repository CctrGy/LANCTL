import argparse
import unittest
from pathlib import Path

from lanctl.apps.access.manager_cli import build_parser as build_access_parser
from lanctl.apps.ip.interfaces.cli.main import build_parser
from lanctl.apps.rack.cli import build_parser as build_rack_parser
from lanctl.apps.wire.cli.main import build_parser as build_wire_parser
from lanctl.bootstrap.lanctl import build_parser as build_suite_parser
from lanctl.bootstrap.lanmon import build_parser as build_monitor_parser


class ClinkCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (Path(__file__).resolve().parents[1] / "packaging/clink/lanctl.lua").read_text(
            encoding="utf-8"
        )

    def test_matcher_registers_all_executable_names(self):
        self.assertIn('clink.argmatcher("lanctl", "lanctl.exe", "LANCTL.exe")', self.script)
        self.assertIn('clink.argmatcher("lanip", "lanip.exe", "als", "als.exe")', self.script)
        for executable in ("lanwire", "lanrack", "lanaccess", "lanmon"):
            self.assertIn(f'clink.argmatcher("{executable}", "{executable}.exe")', self.script)

    def test_script_identifies_its_compatible_release(self):
        self.assertIn("Compatible con LANCTL 0.3.2-beta.1", self.script)

    def test_suite_launcher_aliases_are_completed(self):
        for launcher in (
            "lanip",
            "ip",
            "lanwire",
            "wire",
            "lanrack",
            "rack",
            "lanaccess",
            "access",
            "lanmon",
            "monitor",
        ):
            self.assertIn(f'"{launcher}" ..', self.script)

    def test_all_root_commands_are_represented(self):
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
        )
        missing = sorted(
            command for command in subparsers.choices if f'"{command}"' not in self.script
        )
        self.assertEqual(missing, [])

    def test_removed_scope_is_not_completed(self):
        self.assertNotIn('"virtual"', self.script)

    def test_error_log_level_completes_the_valid_integer_range(self):
        self.assertIn("local error_log_levels = integer_range(1, 59)", self.script)
        self.assertIn('"--error-log-level" .. error_log_levels', self.script)
        self.assertNotIn('"--error-log-level" .. history_value', self.script)

    def test_clink_installation_instructions_are_shipped(self):
        readme = (Path(__file__).resolve().parents[1] / "packaging/clink/README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("clink installscripts", readme)
        self.assertIn("clink uninstallscripts", readme)

    def test_all_published_parser_options_and_commands_are_represented(self):
        roots = (
            build_suite_parser(),
            build_parser(),
            build_wire_parser(),
            build_rack_parser(),
            build_access_parser(),
            build_monitor_parser(),
        )
        for root in roots:
            pending = [root]
            options = set()
            commands = set()
            while pending:
                parser = pending.pop()
                for action in parser._actions:
                    options.update(action.option_strings)
                    if isinstance(action, argparse._SubParsersAction):
                        commands.update(action.choices)
                        pending.extend(action.choices.values())
            missing_options = sorted(
                option for option in options if f'"{option}"' not in self.script
            )
            missing_commands = sorted(
                command for command in commands if f'"{command}"' not in self.script
            )
            with self.subTest(parser=root.prog):
                self.assertEqual(missing_options, [])
                self.assertEqual(missing_commands, [])

    def test_stable_release_rules_freeze_the_clink_contract(self):
        rules = (Path(__file__).resolve().parents[1] / "docs/DEVELOPMENT-RULES.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("tests/test_clink.py", rules)
        self.assertIn("Windows y Linux", rules)
        self.assertIn("sistemas Apple quedan", rules)


if __name__ == "__main__":
    unittest.main()
