import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app.cli import build_parser
from app.core.database import DeviceDatabase
from app.core.history import DeviceSnapshot, HistoryEvent, HistoryReader, HistoryService
from app.projects.vlf import append_database_log, create_project, verify_project


class HistoryTests(unittest.TestCase):
    def project(self, root):
        database = root / "devices.json"
        groups = root / "groups.json"
        credentials = root / "credentials"
        DeviceDatabase(database).upsert(
            [{"IP": "192.168.1.8", "MAC": "02:11:22:33:44:55", "ALIAS": "NAS"}]
        )
        groups.write_text("[]", encoding="utf-8")
        credentials.write_bytes(b"opaque")
        return Path(
            create_project(
                root / "test.vlf",
                config={
                    "database": str(database),
                    "groups": str(groups),
                    "credentials": str(credentials),
                },
            )["path"]
        )

    def test_redaction_is_recursive_and_file_never_contains_secret(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(Path(temporary))
            service = HistoryService(project)
            event = HistoryEvent(
                "device.credential.bound",
                "lanctl.test",
                "local",
                "success",
                "credencial",
                device=DeviceSnapshot("dev", "02:11:22:33:44:55", "192.168.1.8", "NAS"),
                details={"password": "hunter2", "nested": {"apiToken": "abc"}},
                changes=({"field": "credentials.smb", "before": "old", "after": "new"},),
            )
            service.write(event)
            verify_project(project)
            raw = project.read_bytes()
            self.assertNotIn(b"hunter2", raw)
            self.assertNotIn(b"abc", raw)
            loaded = HistoryReader(project).read()[-1].to_dict()
            self.assertEqual(loaded["details"]["password"], "[OCULTO]")

    def test_structured_and_legacy_events_are_read_and_historical_ip_resolves(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(Path(temporary))
            service = HistoryService(project)
            service.write(
                HistoryEvent(
                    "device.ip.changed",
                    "lanctl.database",
                    "local",
                    "success",
                    "IP cambiada",
                    device=DeviceSnapshot("dev-x", "02:11:22:33:44:55", "192.168.1.7", "NAS"),
                    changes=({"field": "IP", "before": "192.168.1.6", "after": "192.168.1.7"},),
                )
            )
            append_database_log(
                project, "CAMBIO dev-x ALIAS:A=>B", now=datetime(2026, 8, 3, 10, 0).astimezone()
            )
            rows = HistoryService(project).query("192.168.1.6")
            self.assertTrue(any(e.type == "device.ip.changed" for e in rows))
            self.assertTrue(
                any(e.details.get("format") == "legacy" for e in HistoryReader(project).read())
            )
            verify_project(project)

    def test_reader_skips_truncated_jsonl_unless_strict(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(Path(temporary))
            service = HistoryService(project)
            service.write(HistoryEvent("device.detected", "test", "local", "success", "ok"))
            self.assertEqual(len(HistoryReader(project).read()), 1)

    def test_cli_json_and_no_active_project_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(Path(temporary))
            HistoryService(project).write(
                HistoryEvent(
                    "device.detected",
                    "test",
                    "local",
                    "success",
                    "detectado",
                    device=DeviceSnapshot("dev", "02:11:22:33:44:55", "192.168.1.8", "NAS"),
                )
            )
            args = build_parser().parse_args(["history", "NAS", "--format", "json"])
            output = io.StringIO()
            with (
                patch("app.core.history.load_config", return_value={"activeProject": str(project)}),
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(args.handler(args), 0)
            self.assertEqual(json.loads(output.getvalue())[0]["type"], "device.detected")
            with (
                patch("app.core.history.load_config", return_value={"activeProject": None}),
                self.assertRaisesRegex(ValueError, "proyecto VLF activo"),
            ):
                HistoryService()

    def test_filter_limit_reverse(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(Path(temporary))
            service = HistoryService(project)
            for kind, result in (
                ("device.detected", "success"),
                ("smb.authentication.failed", "error"),
            ):
                service.write(
                    HistoryEvent(
                        kind,
                        "test",
                        "local",
                        result,
                        kind,
                        error={"code": "X", "origin": "test", "message": "safe"}
                        if result == "error"
                        else None,
                    )
                )
            self.assertEqual(service.query(errors=True)[0].type, "smb.authentication.failed")
            self.assertEqual(len(service.query(limit=1, reverse=True)), 1)


if __name__ == "__main__":
    unittest.main()
