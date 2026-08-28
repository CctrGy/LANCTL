import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from lanctl.apps.wire.log import cleanup_old_logs, write_log
from lanctl.apps.wire.path import application_path, data_root
from lanctl.apps.wire.xfile import read, update_json, write


class CoreLibraryTests(unittest.TestCase):
    def test_data_path_uses_configured_root(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict("os.environ", {"LANWRE_DATA_DIR": temporary}),
        ):
            self.assertEqual(
                application_path("data/example.json"), Path(temporary) / "example.json"
            )

    def test_lanctl_root_has_priority_and_physical_database_is_namespaced(self):
        with (
            tempfile.TemporaryDirectory() as shared,
            tempfile.TemporaryDirectory() as legacy,
            patch.dict("os.environ", {"LANCTL_DATA_DIR": shared, "LANWRE_DATA_DIR": legacy}),
        ):
            self.assertEqual(data_root(), Path(shared))
            self.assertEqual(
                application_path("data/lw/idf.db"), Path(shared) / "physical" / "idf.db"
            )

    def test_config_and_language_files_use_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("settings.config", "spanish.lang"):
                target = root / name
                write(target, {"name": "España"})
                self.assertEqual(read(target), {"name": "España"})

    def test_json_update_is_persisted(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "state.json"
            result = update_json(
                target, lambda: {"count": 0}, lambda value: {"count": value["count"] + 1}
            )
            self.assertEqual(result, {"count": 1})
            self.assertEqual(read(target), {"count": 1})

    def test_log_write_and_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            written = write_log("inicio\ncorrecto", root)
            self.assertIn("inicio | correcto", written.read_text(encoding="utf-8"))
            old = root / "2024-01-01.log"
            old.write_text("old", encoding="utf-8")
            ignored = root / "manual.log"
            ignored.write_text("keep", encoding="utf-8")
            deleted = cleanup_old_logs(root, 30, today=date(2024, 3, 1))
            self.assertEqual(deleted, (old.resolve(),))
            self.assertTrue(ignored.exists())


if __name__ == "__main__":
    unittest.main()
