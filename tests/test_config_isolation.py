import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.config import load_config
from app.models import Device


class ConfigIsolationTests(unittest.TestCase):
    def test_missing_config_returns_independent_nested_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing.json"
            with patch("app.core.config.CONFIG_PATH", missing):
                first = load_config()
                first["wol"]["port"] = 1
                first["listColumns"].append("temporary")
                second = load_config()

            self.assertEqual(second["wol"]["port"], 9)
            self.assertNotIn("temporary", second["listColumns"])

    def test_device_group_lookup_uses_model_normalization(self):
        device = Device("192.168.1.10", groups=["Portátiles"])
        self.assertTrue(device.in_group("  portátiles "))
        self.assertFalse(device.in_group("servidores"))


if __name__ == "__main__":
    unittest.main()
