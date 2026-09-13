import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lanctl.apps.ip.interfaces.cli.commands.lanwire import (
    _environment,
    lanwire_command,
    run_lanwire,
)
from lanctl.apps.ip.interfaces.cli.main import build_parser


class LanwireIntegrationTests(unittest.TestCase):
    def test_parser_exposes_lanwire_and_forwards_arguments(self):
        args = build_parser().parse_args(["lanwire", "list"])
        self.assertEqual(args.arguments, ["list"])
        self.assertIs(args.handler, run_lanwire)

    def test_lanwire_version_is_not_consumed_by_lanctl_fast_path(self):
        args = build_parser().parse_args(["lanwire", "--version"])
        self.assertTrue(args.lanwire_version)
        self.assertEqual(args.arguments, [])
        self.assertIs(args.handler, run_lanwire)

    def test_frozen_launcher_uses_executable_beside_lanctl(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "lanwire.exe"
            executable.touch()
            with (
                patch.object(sys, "frozen", True, create=True),
                patch(
                    "lanctl.apps.ip.interfaces.cli.commands.lanwire.application_directory",
                    return_value=root,
                ),
            ):
                self.assertEqual(lanwire_command(["list"]), [str(executable), "list"])

    def test_development_launcher_uses_root_entrypoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entrypoint = root / "lanwire.py"
            entrypoint.write_text("", encoding="utf-8")
            with (
                patch.object(sys, "frozen", False, create=True),
                patch(
                    "lanctl.apps.ip.interfaces.cli.commands.lanwire.application_directory",
                    return_value=root,
                ),
            ):
                self.assertEqual(
                    lanwire_command(["list"]), [sys.executable, str(entrypoint), "list"]
                )

    def test_shared_data_root_is_exported_to_child(self):
        with patch(
            "lanctl.apps.ip.interfaces.cli.commands.lanwire.data_root",
            return_value=Path("C:/shared/LANCTL"),
        ):
            self.assertEqual(
                _environment()["LANCTL_DATA_DIR"], str(Path("C:/shared/LANCTL"))
            )

    def test_arguments_run_in_current_console(self):
        args = SimpleNamespace(arguments=["list"], new_window=False)
        completed = SimpleNamespace(returncode=7)
        with (
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.lanwire.lanwire_command",
                return_value=["lanwire.exe", "list"],
            ),
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.lanwire._environment",
                return_value={"LANCTL_DATA_DIR": "X:\\data"},
            ),
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.lanwire.subprocess.run",
                return_value=completed,
            ) as run,
        ):
            self.assertEqual(run_lanwire(args), 7)
        run.assert_called_once_with(
            ["lanwire.exe", "list"], env={"LANCTL_DATA_DIR": "X:\\data"}, check=False
        )


if __name__ == "__main__":
    unittest.main()
