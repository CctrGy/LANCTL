import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from lanctl.apps.ip.interfaces.cli.main import _run_handler, configure_utf8_stdio, main


class CliFastPathTests(unittest.TestCase):
    def test_importing_cli_does_not_eagerly_import_command_modules(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; import lanctl.apps.ip.interfaces.cli.main; "
                    "print(any(name.startswith('lanctl.apps.ip.interfaces.cli.commands.') "
                    "for name in sys.modules))"
                ),
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "False")

    def test_importing_a_plugin_contract_does_not_load_the_plugin_manager(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; import lanctl.core.plugins.contracts; "
                    "print('lanctl.core.plugins.manager' in sys.modules)"
                ),
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "False")

    def test_importing_project_metadata_does_not_load_the_vlf_engine(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; from lanctl.core.projects import active_project_info; "
                    "print('lanctl.core.projects.vlf' in sys.modules)"
                ),
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "False")

    def test_standard_text_output_is_configured_as_utf8(self):
        stdout = Mock()
        stderr = Mock()
        with (
            patch("lanctl.apps.ip.interfaces.cli.main.sys.stdout", stdout),
            patch("lanctl.apps.ip.interfaces.cli.main.sys.stderr", stderr),
        ):
            configure_utf8_stdio()
        stdout.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
        stderr.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")

    def test_version_and_help_do_not_create_data(self):
        for arguments in (["--version"], ["--help"], ["access", "--help"]):
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "data"
                with (
                    patch.dict("os.environ", {"LANCTL_DATA_DIR": str(root)}, clear=False),
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                    self.assertRaises(SystemExit) as result,
                ):
                    main(arguments)
                self.assertEqual(result.exception.code, 0)
                self.assertFalse(root.exists())

    def test_quiet_suppresses_success_output_but_preserves_exit_code(self):
        args = SimpleNamespace(
            quiet=True,
            verbose=False,
            command="demo",
            handler=lambda _args: print("success") or 7,
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = _run_handler(args)
        self.assertEqual(result, 7)
        self.assertEqual(output.getvalue(), "")

    def test_verbose_reports_command_code_and_elapsed_without_arguments(self):
        args = SimpleNamespace(
            quiet=False,
            verbose=True,
            command="demo",
            secret="must-not-appear",
            handler=lambda _args: 0,
        )
        diagnostics = io.StringIO()
        with contextlib.redirect_stderr(diagnostics):
            self.assertEqual(_run_handler(args), 0)
        value = diagnostics.getvalue()
        self.assertIn("command=demo phase=start", value)
        self.assertIn("phase=end code=0 elapsed=", value)
        self.assertNotIn("must-not-appear", value)


def test_main_reports_startup_oserror_without_masking_it():
    with (
        patch("lanctl.core.data_migration.ensure_data_layout", side_effect=OSError("denied")),
        patch("lanctl.apps.ip.interfaces.cli.main.print_error") as report,
    ):
        assert main(["list"]) == 2
    report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
