import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.database import DeviceDatabase
from app.core.paths import (
    application_directory,
    application_path,
    data_root,
    secret_root,
)


class ApplicationPathTests(unittest.TestCase):
    def test_source_paths_do_not_depend_on_current_directory(self):
        expected_root = Path(__file__).resolve().parents[1]
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("pathlib.Path.cwd", return_value=Path(directory)),
        ):
            # `application_path` no consulta el directorio actual; la base se
            # ancla al proyecto.
            path = DeviceDatabase("data/lc/devices.json").path
        self.assertEqual(path, expected_root / "data" / "lc" / "database" / "devices.json")

    @unittest.skipUnless(sys.platform == "win32", "semántica de rutas de Windows")
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
                Path(r"C:\ProgramData\LANCTL\config\config.json"),
            )

    @unittest.skipUnless(sys.platform == "win32", "semántica de rutas de Windows")
    def test_portable_and_override_priority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "LANCTL.exe"
            (root / "LANCTL.portable").write_text("LANCTL-PORTABLE-V1\n", encoding="ascii")
            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "executable", str(executable)),
                patch.dict("os.environ", {}, clear=True),
            ):
                self.assertEqual(data_root(), root / "data" / "lanctl")
                self.assertEqual(
                    application_path("data/lc/monitor.db"),
                    root / "data" / "lanctl" / "monitoring" / "monitor.db",
                )
            override = root / "explicit"
            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "executable", str(executable)),
                patch.dict("os.environ", {"LANCTL_DATA_DIR": str(override)}, clear=True),
            ):
                self.assertEqual(data_root(), override)

    @unittest.skipUnless(sys.platform == "win32", "semántica de rutas de Windows")
    def test_windows_service_secrets_are_not_taken_from_a_user_profile(self):
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "executable", r"C:\Program Files\LANCTL\LANCTL.exe"),
            patch.dict(
                "os.environ",
                {
                    "PROGRAMDATA": r"C:\ProgramData",
                    "LOCALAPPDATA": r"C:\Users\admin\AppData\Local",
                    "LANCTL_DATA_SCOPE": "service",
                },
                clear=True,
            ),
        ):
            self.assertEqual(secret_root(), Path(r"C:\ProgramData\LANCTL\access"))

    def test_relative_override_is_rejected(self):
        with (
            patch.dict("os.environ", {"LANCTL_DATA_DIR": "relative/data"}, clear=True),
            self.assertRaises(ValueError),
        ):
            data_root()

    def test_frozen_linux_separates_user_and_service_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            executable = home / "LANCTL"
            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "executable", str(executable)),
                patch("app.core.paths.platform.system", return_value="Linux"),
                patch("app.core.paths.Path.home", return_value=home),
                patch.dict("os.environ", {}, clear=True),
            ):
                self.assertEqual(data_root(), home / ".local/share/lanctl")
                self.assertEqual(secret_root(), home / ".config/lanctl/access")
            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "executable", str(executable)),
                patch("app.core.paths.platform.system", return_value="Linux"),
                patch.dict("os.environ", {"LANCTL_DATA_SCOPE": "service"}, clear=True),
            ):
                self.assertEqual(data_root(), Path("/var/lib/lanctl"))
                self.assertEqual(secret_root(), Path("/etc/lanctl/access"))

    def test_legacy_names_map_into_structured_layout(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict("os.environ", {"LANCTL_DATA_DIR": temporary}, clear=False),
        ):
            root = Path(temporary)
            self.assertEqual(
                application_path("data/lc/icons/router.png"), root / "config/icons/router.png"
            )
            self.assertEqual(application_path("data/lc/log/now.log"), root / "logs/now.log")
            self.assertEqual(
                application_path("data/lc/plugins/demo/plugin.info"),
                root / "plugins/demo/plugin.info",
            )


if __name__ == "__main__":
    unittest.main()
