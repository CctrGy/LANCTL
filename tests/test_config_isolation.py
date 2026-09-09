import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lanctl.apps.ip.domain.models import Device
from lanctl.core.config import CONFIG_SCHEMA_VERSION, load_config, save_config


class ConfigIsolationTests(unittest.TestCase):
    def test_missing_config_returns_independent_nested_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing.json"
            with patch("lanctl.core.config.CONFIG_PATH", missing):
                first = load_config()
                first["wol"]["port"] = 1
                first["listColumns"].append("temporary")
                second = load_config()

            self.assertEqual(second["wol"]["port"], 9)
            self.assertNotIn("temporary", second["listColumns"])
            self.assertEqual(
                second["database"],
                "data/lc/projects/workspaces/default/database/devices.json",
            )
            self.assertEqual(
                second["tuiFooterButtons"],
                [
                    "help",
                    "info",
                    "ping",
                    "refresh",
                    "plugins",
                    "projects",
                    "settings",
                    "select",
                ],
            )

    def test_tui_v1_default_footer_is_compacted_but_custom_footer_is_preserved(self):
        from lanctl.core.config import canonical_config

        legacy_default = {
            "schemaVersion": 2,
            "tui": {
                "schemaVersion": 1,
                "footerButtons": [
                    "help",
                    "info",
                    "ping",
                    "refresh",
                    "plugins",
                    "projects",
                    "settings",
                    "history",
                    "search",
                    "reload",
                    "edit",
                    "groups",
                    "ports",
                    "open",
                    "save",
                    "differences",
                    "copyLine",
                    "copyJson",
                    "console",
                    "quit",
                    "select",
                    "execute",
                    "exit",
                ],
            },
        }
        migrated = canonical_config(legacy_default)
        self.assertEqual(
            migrated["tui"]["footerButtons"],
            ["help", "info", "ping", "refresh", "plugins", "projects", "settings", "select"],
        )
        custom = canonical_config(
            {
                "schemaVersion": 2,
                "tui": {"schemaVersion": 1, "footerButtons": ["help", "save", "exit"]},
            }
        )
        self.assertEqual(custom["tui"]["footerButtons"], ["help", "save", "exit"])

    def test_device_group_lookup_uses_model_normalization(self):
        device = Device("192.168.1.10", groups=["Portátiles"])
        self.assertTrue(device.in_group("  portátiles "))
        self.assertFalse(device.in_group("servidores"))

    def test_legacy_config_is_saved_as_grouped_schema_v2(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "database": "custom/devices.json",
                        "workers": 17,
                        "monitorDatabase": "custom/monitor.db",
                        "monitor": {"enabled": True, "timeout": 1.25},
                    }
                ),
                encoding="utf-8",
            )
            with patch("lanctl.core.config.CONFIG_PATH", path):
                config = load_config()
                self.assertEqual(config["database"], "custom/devices.json")
                self.assertEqual(config["workers"], 17)
                self.assertTrue(config["monitor"]["enabled"])
                save_config(config)

            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(stored["schemaVersion"], CONFIG_SCHEMA_VERSION)
            self.assertEqual(
                stored["projects"]["workspace"]["databases"]["devices"],
                "custom/devices.json",
            )
            self.assertEqual(stored["ip"]["workers"], 17)
            self.assertEqual(
                stored["projects"]["workspace"]["databases"]["monitor"],
                "custom/monitor.db",
            )
            self.assertEqual(stored["monitor"]["execution"]["timeout"], 1.25)
            self.assertNotIn("monitorDatabase", stored)

    def test_grouped_config_keeps_legacy_runtime_access_and_nested_unknown_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 2,
                        "projects": {
                            "workspace": {"databases": {"devices": "custom/devices.json"}}
                        },
                        "ip": {"workers": 12},
                        "futureApplication": {"enabled": True},
                    }
                ),
                encoding="utf-8",
            )
            with patch("lanctl.core.config.CONFIG_PATH", path):
                config = load_config()
                self.assertEqual(config["database"], "custom/devices.json")
                self.assertEqual(config["workers"], 12)
                config["timeout"] = 2.5
                save_config(config)

            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(stored["ip"]["timeout"], 2.5)
            self.assertEqual(stored["futureApplication"], {"enabled": True})

    def test_early_v2_database_groups_are_moved_into_the_project_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 2,
                        "storage": {
                            "database": "old/devices.json",
                            "groups": "old/groups.json",
                        },
                        "monitor": {"storage": {"database": "old/monitor.db"}},
                    }
                ),
                encoding="utf-8",
            )
            with patch("lanctl.core.config.CONFIG_PATH", path):
                config = load_config()
                self.assertEqual(config["database"], "old/devices.json")
                self.assertEqual(config["groups"], "old/groups.json")
                self.assertEqual(config["monitorDatabase"], "old/monitor.db")
                save_config(config)

            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("database", stored["storage"])
            self.assertNotIn("storage", stored["monitor"])


if __name__ == "__main__":
    unittest.main()
