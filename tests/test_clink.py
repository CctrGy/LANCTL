import unittest
import argparse
from pathlib import Path

from app.cli import LEGACY_VIRTUAL_COMMANDS, build_parser


class ClinkCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (
            Path(__file__).resolve().parents[1] / "packaging/clink/lanctl.lua"
        ).read_text(encoding="utf-8")

    def test_matcher_registers_all_executable_names(self):
        self.assertIn(
            'clink.argmatcher("lanctl", "lanctl.exe", "als", "als.exe")',
            self.script,
        )

    def test_all_core_legacy_commands_are_represented(self):
        missing = sorted(
            command for command in LEGACY_VIRTUAL_COMMANDS
            if f'"{command}"' not in self.script
        )
        self.assertEqual(missing, [])

    def test_clink_installation_instructions_are_shipped(self):
        readme = (
            Path(__file__).resolve().parents[1] / "packaging/clink/README.md"
        ).read_text(encoding="utf-8")
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
