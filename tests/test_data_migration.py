import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.data_migration import ensure_data_layout, migrate_config_paths


class DataMigrationTests(unittest.TestCase):
    def test_legacy_directory_is_renamed_when_destination_is_absent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "data/als"
            legacy.mkdir(parents=True)
            (legacy / "devices.json").write_text("legacy", encoding="utf-8")
            with patch("app.core.data_migration.application_directory", return_value=root):
                current = ensure_data_layout()
            self.assertEqual(current, (root / "data/lc").resolve())
            self.assertEqual((root / "data/lc/devices.json").read_text(), "legacy")
            self.assertFalse(legacy.exists())

    def test_conflicting_legacy_file_is_preserved_in_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data/als").mkdir(parents=True)
            (root / "data/lc").mkdir(parents=True)
            (root / "data/als/devices.json").write_text("old", encoding="utf-8")
            (root / "data/lc/devices.json").write_text("new", encoding="utf-8")
            with patch("app.core.data_migration.application_directory", return_value=root):
                ensure_data_layout()
            self.assertEqual((root / "data/lc/devices.json").read_text(), "new")
            self.assertEqual((root / "data/lc/migration-backup-als/devices.json").read_text(), "old")
            self.assertFalse((root / "data/als").exists())

    def test_paths_inside_configuration_are_migrated_recursively(self):
        value = {"database": "data/als/devices.json", "items": [r"data\als\log"]}
        self.assertEqual(migrate_config_paths(value), {
            "database": "data/lc/devices.json", "items": [r"data\lc\log"]
        })


if __name__ == "__main__":
    unittest.main()
