import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.projects.paths import default_project_directory, resolve_project_path
from app.core.config import DEFAULTS


class ProjectPathTests(unittest.TestCase):
    def test_configuration_default_is_portable(self):
        self.assertIsNone(DEFAULTS["projectsDirectory"])

    def test_default_directory_uses_user_documents_lanctl(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "app.projects.paths._known_documents_directory", return_value=None
        ), patch.dict(os.environ, {"USERPROFILE": temporary}):
            self.assertEqual(
                default_project_directory(), Path(temporary) / "Documents" / "LanCTL"
            )

    def test_default_directory_uses_onedrive_known_folder(self):
        documents = Path(r"C:\Users\Victor\OneDrive\Documents")
        with patch(
            "app.projects.paths._known_documents_directory",
            return_value=documents,
        ):
            self.assertEqual(default_project_directory(), documents / "LanCTL")

    def test_relative_project_uses_configured_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(
                resolve_project_path("Hogar", temporary),
                (Path(temporary) / "Hogar.vlf").resolve(),
            )

    def test_environment_variable_in_configured_directory_is_expanded(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"USERPROFILE": temporary}
        ):
            expected = Path(temporary) / "Documents" / "LanCTL" / "Hogar.vlf"
            self.assertEqual(
                resolve_project_path("Hogar", r"%USERPROFILE%\Documents\LanCTL"),
                expected.resolve(),
            )

    def test_absolute_project_path_is_never_relocated(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "alternative" / "Red.vlf"
            self.assertEqual(resolve_project_path(target, "ignored"), target.resolve())

    def test_legacy_default_uses_redirected_documents_folder(self):
        documents = Path(r"C:\Users\Victor\OneDrive\Documents")
        with patch(
            "app.projects.paths._known_documents_directory",
            return_value=documents,
        ):
            self.assertEqual(
                resolve_project_path(
                    "Hogar", r"%USERPROFILE%\Documents\LanCTL"
                ),
                (documents / "LanCTL" / "Hogar.vlf").resolve(),
            )


if __name__ == "__main__":
    unittest.main()
