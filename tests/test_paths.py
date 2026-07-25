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
            path = DeviceDatabase("data/als/devices.json").path
        self.assertEqual(path, expected_root / "data" / "als" / "devices.json")

    def test_frozen_paths_are_relative_to_executable(self):
        executable = r"C:\Program Files\LANCTL\LANCTL.exe"
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "executable", executable),
        ):
            self.assertEqual(
                application_directory(),
                Path(r"C:\Program Files\LANCTL"),
            )
            self.assertEqual(
                application_path("data/als/.config"),
                Path(r"C:\Program Files\LANCTL\data\als\.config"),
            )


if __name__ == "__main__":
    unittest.main()
