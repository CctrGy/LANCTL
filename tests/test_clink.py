import argparse
import unittest
from pathlib import Path

from lanctl.apps.ip.interfaces.cli.main import build_parser


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
        self.assertIn("Compatible con LANCTL 0.3.1-beta.3", self.script)

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

    def test_all_core_parser_options_are_represented(self):
        pending = [build_parser()]
        options = set()
        while pending:
            parser = pending.pop()
            for action in parser._actions:
                options.update(action.option_strings)
                if isinstance(action, argparse._SubParsersAction):
                    pending.extend(action.choices.values())
        missing = sorted(option for option in options if f'"{option}"' not in self.script)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
