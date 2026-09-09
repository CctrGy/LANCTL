import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lanctl.core.data_migration import ensure_data_layout, migrate_config_paths


class DataMigrationTests(unittest.TestCase):
    def test_clean_install_creates_complete_valid_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "lanctl-data"
            with (
                patch(
                    "lanctl.core.data_migration.application_directory", return_value=Path(temporary)
                ),
                patch.dict("os.environ", {"LANCTL_DATA_DIR": str(root)}, clear=False),
            ):
                current = ensure_data_layout()

            self.assertEqual(current, root.resolve())
            for relative in (
                "config/icons",
                "config/languages",
                "logs",
                "plugins/storage",
                "projects/workspaces",
                "automation",
                "access",
            ):
                self.assertTrue((root / relative).is_dir(), relative)

            for relative in (
                "config/config.json",
                "projects/workspaces/default/database/devices.json",
                "projects/workspaces/default/database/groups.json",
                "recurrent-elements.json",
                "plugins/registry.json",
                "automation/wol-sequences.json",
                "projects/workspaces/default/monitoring/sessions.json",
                "projects/workspaces/default/monitoring/incidents.json",
                "projects/workspaces/default/monitoring/profiles.json",
                "projects/workspaces/default/monitoring/assignments.json",
                "config/cisco_profiles.json",
                "projects/workspaces/default/physical/idf.db",
            ):
                with self.subTest(relative=relative):
                    json.loads((root / relative).read_text(encoding="utf-8"))
            physical = json.loads(
                (root / "projects/workspaces/default/physical/idf.db").read_text(encoding="utf-8")
            )
            self.assertEqual(physical["format"], "LANWRE-IDF-DB")
            config = json.loads((root / "config/config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["schemaVersion"], 2)
            self.assertEqual(
                config["projects"]["workspace"]["databases"]["devices"],
                "data/lc/projects/workspaces/default/database/devices.json",
            )

    def test_bootstrap_does_not_overwrite_existing_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "lanctl-data"
            database = root / "database/devices.json"
            database.parent.mkdir(parents=True)
            database.write_text('[{"IP":"192.0.2.1","MAC":"00:11:22:33:44:55"}]', encoding="utf-8")
            with (
                patch(
                    "lanctl.core.data_migration.application_directory", return_value=Path(temporary)
                ),
                patch.dict("os.environ", {"LANCTL_DATA_DIR": str(root)}, clear=False),
            ):
                ensure_data_layout()
            self.assertIn("192.0.2.1", database.read_text(encoding="utf-8"))

    def test_legacy_directory_is_copied_without_deleting_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "data/als"
            legacy.mkdir(parents=True)
            (legacy / "devices.json").write_text("legacy", encoding="utf-8")
            with (
                patch("lanctl.core.data_migration.application_directory", return_value=root),
                patch.dict("os.environ", {"LANCTL_DATA_DIR": str(root / "data/lc")}, clear=False),
            ):
                current = ensure_data_layout()
            self.assertEqual(current, (root / "data/lc").resolve())
            self.assertEqual((root / "data/lc/database/devices.json").read_text(), "legacy")
            self.assertTrue(legacy.exists())

    def test_conflicting_legacy_file_stops_migration_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data/als").mkdir(parents=True)
            (root / "data/lc").mkdir(parents=True)
            (root / "data/als/devices.json").write_text("old", encoding="utf-8")
            (root / "data/lc/database").mkdir(parents=True)
            (root / "data/lc/database/devices.json").write_text("new", encoding="utf-8")
            with (
                patch("lanctl.core.data_migration.application_directory", return_value=root),
                patch.dict("os.environ", {"LANCTL_DATA_DIR": str(root / "data/lc")}, clear=False),
                self.assertRaisesRegex(ValueError, "conflictos"),
            ):
                ensure_data_layout()
            self.assertEqual((root / "data/lc/database/devices.json").read_text(), "new")
            self.assertEqual((root / "data/als/devices.json").read_text(), "old")

    def test_paths_inside_configuration_are_migrated_recursively(self):
        value = {"database": "data/als/devices.json", "items": [r"data\als\log"]}
        self.assertEqual(
            migrate_config_paths(value),
            {"database": "data/lc/devices.json", "items": [r"data\lc\log"]},
        )

    @unittest.skipUnless(sys.platform == "win32", "semántica Windows")
    def test_installed_legacy_data_is_copied_out_of_program_files(self):
        import lanctl.core.paths as paths

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            installed = base / "Program Files/LANCTL"
            legacy = installed / "data/lc"
            legacy.mkdir(parents=True)
            (legacy / "devices.json").write_text("legacy", encoding="utf-8")
            program_data = base / "ProgramData"
            local_data = base / "LocalAppData"
            with (
                patch.object(paths.sys, "frozen", True, create=True),
                patch.object(paths.sys, "executable", str(installed / "LANCTL.exe")),
                patch.object(paths.platform, "system", return_value="Windows"),
                patch.dict(
                    "os.environ",
                    {"PROGRAMDATA": str(program_data), "LOCALAPPDATA": str(local_data)},
                    clear=False,
                ),
            ):
                ensure_data_layout()
            self.assertEqual((program_data / "LANCTL/database/devices.json").read_text(), "legacy")
            self.assertTrue((legacy / "devices.json").exists())
            self.assertFalse((installed / "data/lc/database").exists())


if __name__ == "__main__":
    unittest.main()
