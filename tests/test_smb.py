import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.core.plugin_storage import PluginStorage
from app.plugins.smb_runtime import SMBError, SMBService, classify_share, unc_path
from app.plugins.ui_contracts import (
    validate_form_schema,
    validate_ui_action,
    validate_ui_panel,
)


class NativeFake:
    def __init__(self, denied=False):
        self.denied = denied
        self.opened = []
        self.connected = []

    def resolve(self, host):
        return "192.168.1.30"

    def probe(self, host, timeout):
        return True

    def identity(self, host):
        return {"serverName": host, "workgroup": "OFICINA", "source": "test"}

    def shares(self, host):
        if self.denied:
            raise SMBError("SMB.AUTH.ACCESS_DENIED", "denied", state="access-denied")
        return [
            {"name": "Public", "nativeType": 0, "description": "Files"},
            {"name": "HP", "nativeType": 1},
            {"name": "ADMIN$", "nativeType": 0x80000000},
        ]

    def connect(self, host, username, password):
        self.connected.append((host, username, password))
        self.denied = False

    def disconnect(self, host):
        self.connected.append((host, "disconnect", ""))

    def open_path(self, path):
        self.opened.append(path)

    def connect_printer(self, path):
        self.opened.append(path)


class SMBTests(unittest.TestCase):
    def test_unc_rejects_traversal_and_injection(self):
        self.assertEqual(unc_path("NAS", "Public"), r"\\NAS\Public")
        for value in ("..", "a\\b", "a/b", "a|b"):
            with self.assertRaises(ValueError):
                unc_path("NAS", value)

    def test_classifies_and_hides_system_shares(self):
        self.assertEqual(classify_share("HP", 1), ("printer", False))
        self.assertEqual(classify_share("ADMIN$", 0), ("administrative", True))
        device = SimpleNamespace(name="NAS", ip="192.168.1.30", device_id="dev_1")
        observation, trace = SMBService(NativeFake()).inspect(device)
        self.assertEqual([x["name"] for x in observation["smb"]["shares"]], ["Public", "HP"])
        self.assertEqual(trace[-1]["operationId"], "smb.shares.enumerate")

    def test_authentication_uses_injected_session_without_exposing_secret(self):
        native = NativeFake(True)
        device = SimpleNamespace(name="NAS", ip="x", device_id="dev_1")
        observation, trace = SMBService(native).inspect(
            device, credential={"username": "OFFICE\\user", "password": "secret"}
        )
        self.assertEqual(observation["smb"]["authentication"], "credential")
        self.assertNotIn("secret", str(observation) + str(trace))

    def test_dry_run_does_not_open(self):
        native = NativeFake()
        result = SMBService(native).open_share("NAS", "Public", dry_run=True)
        self.assertTrue(result["dryRun"])
        self.assertEqual(native.opened, [])

    def test_linux_smbclient_parses_workgroups_shares_and_printers(self):
        from app.plugins.smb_runtime import SMBNative

        completed = SimpleNamespace(
            returncode=0,
            stdout="Disk|Public|Files\nPrinter|HP|Office\nWorkgroup|OFICINA|MASTER\n",
            stderr="",
        )
        native = SMBNative()
        with (
            patch("app.plugins.smb_runtime.os.name", "posix"),
            patch("app.plugins.smb_runtime.shutil.which", return_value="/usr/bin/smbclient"),
            patch("app.plugins.smb_runtime.subprocess.run", return_value=completed) as run,
        ):
            shares = native.shares("nas")
            identity = native.identity("nas")
        self.assertEqual([row["name"] for row in shares], ["Public", "HP"])
        self.assertEqual(identity["workgroup"], "OFICINA")
        self.assertIn("-N", run.call_args.args[0])

    def test_printer_requires_confirmation(self):
        with self.assertRaisesRegex(SMBError, "--yes"):
            SMBService(NativeFake()).printer("NAS", "HP", "connect")

    def test_storage_is_transactional_and_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = PluginStorage(temporary, "lanctl.discovery.windows-smb")
            store.put_observation("dev_1", {"state": "available"})
            self.assertEqual(store.load()["observations"]["dev_1"]["state"], "available")
            self.assertFalse(Path(temporary, "lanctl.discovery.windows-smb.tmp").exists())

    def test_storage_writes_observation_batches_in_one_transaction(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = PluginStorage(temporary, "lanctl.discovery.windows-smb")
            store.put_observations(
                {
                    "dev_1": {"state": "available"},
                    "dev_2": {"state": "authentication-required"},
                }
            )
            observations = store.load()["observations"]
            self.assertEqual(set(observations), {"dev_1", "dev_2"})
            self.assertEqual(observations["dev_2"]["state"], "authentication-required")

    def test_ui_contracts_reject_code_and_cross_shape(self):
        panel = validate_ui_panel(
            {
                "title": "Resources",
                "location": "main",
                "dataProvider": "WindowsSMB.Resources.List",
                "layout": "resource-browser",
            }
        )
        self.assertEqual(panel["layout"], "resource-browser")
        with self.assertRaises(ValueError):
            validate_ui_panel(
                {"title": "x", "location": "main", "dataProvider": "x", "layout": "<script>"}
            )
        with self.assertRaises(ValueError):
            validate_ui_action({"label": "x", "function": "javascript:alert(1)"})
        self.assertEqual(
            validate_form_schema({"fields": [{"name": "password", "type": "secret"}]})["fields"][0][
                "type"
            ],
            "secret",
        )
        with self.assertRaises(ValueError):
            validate_form_schema(
                {"fields": [{"name": "password", "type": "secret", "default": "leak"}]}
            )


if __name__ == "__main__":
    unittest.main()
