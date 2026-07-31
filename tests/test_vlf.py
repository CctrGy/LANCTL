import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.projects.vlf import (
    REQUIRED_ENTRIES, _normalized_log_name, append_database_log, create_project,
    inspect_project, update_project, verify_project,
)


class VlfProjectTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.devices = self.root / "devices.json"
        self.groups = self.root / "groups.json"
        self.credentials = self.root / ".credentials"
        self.logs = self.root / "logs"
        self.database_logs = self.root / "db-logs"
        self.logs.mkdir()
        self.database_logs.mkdir()
        self.devices.write_text(json.dumps([
            {
                "IP": "192.168.50.10", "MAC": "AA:BB:CC:DD:EE:FF",
                "cnf": "O", "ALIAS": "NAS", "NAME": "Storage",
                "defaultName": "nas.local", "GROUP": ["ASSETS"],
                "description": "Almacenamiento", "protocols": ["ssh"],
                "discoveryMethods": ["ICMP", "ARP"],
            }
        ]), encoding="utf-8")
        self.groups.write_text(json.dumps([
            {"name": "ASSETS", "description": "-", "members": ["AA:BB:CC:DD:EE:FF"], "editable": True}
        ]), encoding="utf-8")
        self.credentials.write_bytes(b"opaque-encrypted-credentials")
        (self.logs / "2807-2026.log").write_text("20:00:00 TEST\n", encoding="utf-8")
        (self.database_logs / "2807-2026.log").write_text(
            "20:00:00 CAMBIO TEST\n", encoding="utf-8"
        )
        self.config = {
            "database": str(self.devices), "groups": str(self.groups),
            "credentials": str(self.credentials),
            "programLog": str(self.logs), "databaseLog": str(self.database_logs),
            "range": "192.168.50.0/24", "dhcpRange": "192.168.50.20-192.168.50.100",
            "discovery": "hybrid", "scanProfile": "normal",
        }

    def tearDown(self):
        self.temporary.cleanup()

    def test_create_builds_fixed_verified_structure_and_sqlite(self):
        project = self.root / "site.vlf"
        result = create_project(project, name="Site", config=self.config)
        self.assertTrue(result["valid"])
        self.assertEqual(inspect_project(project)["devices"], 1)
        with zipfile.ZipFile(project) as archive:
            names = set(archive.namelist())
            self.assertTrue(REQUIRED_ENTRIES <= names)
            self.assertIn("plugins/registry.json", names)
            self.assertIn("auth/keys/ssh/", names)
            self.assertIn("logs/28-07-2026.log", names)
            self.assertNotIn(b"20:00:00 TEST", archive.read("logs/28-07-2026.log"))
            self.assertIn(b"CAMBIO TEST", archive.read("logs/28-07-2026.log"))
            self.assertEqual(archive.read("auth/logins.lgn"), self.credentials.read_bytes())
            database = self.root / "exported.db"
            database.write_bytes(archive.read("devices/elements.db"))
        connection = sqlite3.connect(database)
        try:
            self.assertEqual(connection.execute("SELECT count(*) FROM devices").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM groups").fetchone()[0], 1)
        finally:
            connection.close()

    def test_update_preserves_uuid_and_creates_backup(self):
        project = self.root / "site.vlf"
        create_project(project, name="Site", location="Rack", config=self.config)
        original = inspect_project(project)
        changed = json.loads(self.devices.read_text(encoding="utf-8"))
        changed[0]["NAME"] = "Storage Updated"
        self.devices.write_text(json.dumps(changed), encoding="utf-8")
        result = update_project(project, config=self.config)
        updated = inspect_project(project)
        self.assertEqual(updated["id"], original["id"])
        self.assertEqual(updated["created"], original["created"])
        self.assertTrue(Path(result["backup"]).exists())
        self.assertTrue(verify_project(project)["valid"])
        with zipfile.ZipFile(project) as archive:
            current_db = self.root / "current.db"
            backup_db = self.root / "backup.db"
            current_db.write_bytes(archive.read("devices/elements.db"))
            backup_db.write_bytes(archive.read("devices/backup.db"))
        current = sqlite3.connect(current_db)
        backup = sqlite3.connect(backup_db)
        try:
            self.assertEqual(current.execute("SELECT name FROM devices").fetchone()[0], "Storage Updated")
            self.assertEqual(backup.execute("SELECT name FROM devices").fetchone()[0], "Storage")
        finally:
            current.close()
            backup.close()

    def test_duplicate_or_unsafe_zip_entries_are_rejected(self):
        unsafe = self.root / "unsafe.vlf"
        with zipfile.ZipFile(unsafe, "w") as archive:
            archive.writestr("../escape", "bad")
        with self.assertRaisesRegex(ValueError, "ruta insegura"):
            verify_project(unsafe)

    def test_legacy_log_filename_is_normalized(self):
        self.assertEqual(_normalized_log_name("2807-2026.log"), "28-07-2026.log")

    def test_database_audit_is_appended_inside_vlf_and_hashes_remain_valid(self):
        project = self.root / "site.vlf"
        create_project(project, name="Site", config=self.config)

        append_database_log(project, "CAMBIO device:test ALIAS:A=>B")

        self.assertTrue(verify_project(project)["valid"])
        with zipfile.ZipFile(project) as archive:
            daily_logs = [name for name in archive.namelist() if name.startswith("logs/") and name.endswith(".log")]
            content = b"\n".join(archive.read(name) for name in daily_logs)
        self.assertIn(b"CAMBIO device:test ALIAS:A=>B", content)


if __name__ == "__main__":
    unittest.main()
