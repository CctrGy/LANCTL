import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.database import DeviceDatabase
from app.core.paths import application_directory, application_path


class ApplicationPathTests(unittest.TestCase):
    def test_source_paths_do_not_depend_on_current_directory(self):
        expected_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory, patch(
            "pathlib.Path.cwd", return_value=Path(directory)
        ):
            # application_path no consulta cwd; la base se ancla al proyecto.
            path = DeviceDatabase("data/lc/devices.json").path
        self.assertEqual(path, expected_root / "data" / "lc" / "devices.json")

    def test_frozen_program_data_is_separate_from_executable(self):
        executable = r"C:\Program Files\LANCTL\LANCTL.exe"
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "executable", executable),
            patch.dict("os.environ", {"PROGRAMDATA": r"C:\ProgramData"}),
        ):
            self.assertEqual(
                application_directory(),
                Path(r"C:\Program Files\LANCTL"),
            )
            self.assertEqual(
                application_path("data/lc/.config"),
                Path(r"C:\ProgramData\LANCTL\.config"),
            )


if __name__ == "__main__":
    unittest.main()
