import contextlib
import importlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from lanctl import __version__
from lanctl.apps.wire.cli.main import build_parser, main
from lanctl.apps.wire.idf.database import DEFAULT_DATABASE_PATH


class PhysicalEntrypointTests(unittest.TestCase):
    def test_suite_version_and_common_modes_are_exposed(self):
        help_text = build_parser().format_help()
        self.assertIn("--version", help_text)
        self.assertIn("--tui", help_text)
        self.assertIn("--cli", help_text)
        self.assertEqual(DEFAULT_DATABASE_PATH, "data/lc/physical/idf.db")

        output = io.StringIO()
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn(__version__, output.getvalue())

    def test_help_accepts_windows_compatibility_token(self):
        output = io.StringIO()
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["/?"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("LANWIRE", output.getvalue())

    def test_list_reads_the_shared_physical_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "idf.db"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--database", str(database), "list"])
            self.assertEqual(code, 0)
            self.assertIn("vacía", output.getvalue())

    def test_idf_commands_are_callable_directly_with_spaced_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = str(Path(temporary) / "idf.db")

            def call(*command: str) -> str:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main(["--database", database, *command]), 0)
                return output.getvalue()

            self.assertIn("idf list", call("help"))
            self.assertIn("Prefijo FB", call("idf", "new", "FB", "-type", "wire.fiber"))
            self.assertIn("FB", call("idf", "list"))
            self.assertIn(
                "Creado FB-00",
                call("idf", "add", "FB-00", "-description", "Fibra de compañía"),
            )
            self.assertIn("FB-00", call("idf", "list", "FB"))
            self.assertIn("Fibra de compañía", call("element", "FB-00"))
            self.assertIn("wire.fiber", call("idf", "types"))
            self.assertIn("FB-00", call("idf", "show", "FB-00"))
            self.assertIn("Actualizado", call("idf", "edit", "FB-00", "alias=Uplink"))
            self.assertIn("Eliminado", call("idf", "delete", "FB-00"))

    def test_explicit_tui_and_cli_modes_are_dispatched(self):
        cli_module = importlib.import_module("lanctl.apps.wire.cli.main")
        # The active project may override the default; keep this dispatch test isolated.
        with patch.object(
            cli_module, "load_config", return_value={"physicalDatabase": DEFAULT_DATABASE_PATH}
        ):
            with patch("lanctl.apps.wire.tui.run_tui", return_value=7) as tui:
                self.assertEqual(main(["--tui"]), 7)
            tui.assert_called_once_with(DEFAULT_DATABASE_PATH)

            with patch.object(cli_module, "run_cli", return_value=8) as cli:
                self.assertEqual(main(["--cli"]), 8)
            cli.assert_called_once_with(DEFAULT_DATABASE_PATH)


if __name__ == "__main__":
    unittest.main()


@pytest.fixture(autouse=True)
def spanish_regression_labels(tmp_path, monkeypatch):
    from pathlib import Path

    from lanctl.shared import i18n

    manager = i18n.LanguageManager(tmp_path / "test-languages")
    manager.initialize("en")
    manager.install(Path(__file__).resolve().parents[1] / "bundled/languages/spanish.lang")
    monkeypatch.setattr(i18n, "_MANAGER", manager)
    with i18n.language_context("es"):
        yield
