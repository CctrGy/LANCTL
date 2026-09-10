import hashlib
import ipaddress
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lanctl.apps.ip.domain.models import Device
from lanctl.apps.ip.infrastructure.repositories import MemoryDeviceRepository
from lanctl.apps.ip.interfaces.cli.main import main


class _FakeScanner:
    def __init__(self, *_args, **_kwargs):
        self.device = Device(
            ip="192.0.2.2",
            mac="AA:BB:CC:DD:EE:02",
            default_name="temporary.example",
        )

    def scan(self, **_options):
        return [self.device]

    def discovery_for(self, _device):
        return "ICMP+ARP"

    def is_confirmed(self, _device):
        return True

    def response_time_for(self, _device):
        return 1.25


class EphemeralScanTests(unittest.TestCase):
    def test_memory_repository_discards_its_inventory(self):
        repository = MemoryDeviceRepository()
        with repository:
            repository.replace([Device(ip="192.0.2.2", mac="AA:BB:CC:DD:EE:02")])
            self.assertEqual(len(repository.all()), 1)
        self.assertEqual(repository.all(), ())

    def test_ephemeral_scan_does_not_change_persistent_files_or_autosave(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "database" / "devices.json"
            project = root / "projects" / "home.vlf"
            database.parent.mkdir(parents=True)
            project.parent.mkdir(parents=True)
            database.write_text('[{"IP":"10.0.0.2","MAC":"AA:AA:AA:AA:AA:AA"}]', encoding="utf-8")
            project.write_bytes(b"unchanged-project")

            def digest(path):
                return hashlib.sha256(path.read_bytes()).hexdigest()

            before = (digest(database), digest(project))
            with (
                patch.dict("os.environ", {"LANCTL_DATA_DIR": temporary}),
                patch(
                    "lanctl.apps.ip.interfaces.cli.commands.ephemeral.LanScanner",
                    _FakeScanner,
                ),
                patch(
                    "lanctl.apps.ip.interfaces.cli.commands.ephemeral.local_ipv4",
                    return_value=ipaddress.IPv4Address("192.0.2.10"),
                ),
                patch(
                    "lanctl.core.projects.save_policy.start_autosave_scheduler"
                ) as start_autosave,
                patch("lanctl.core.projects.save_policy.save_active_project") as save_project,
            ):
                result = main(
                    ["-e", "--fast", "--range", "192.0.2.0/24", "--json"],
                    program_name="LANIP",
                )

            self.assertEqual(result, 0)
            self.assertEqual((digest(database), digest(project)), before)
            start_autosave.assert_not_called()
            save_project.assert_not_called()

    def test_ephemeral_rejects_explicit_project_before_activation(self):
        with patch("lanctl.core.projects.activate_project_workspace") as activate:
            result = main(
                ["--project", "home.vlf", "ephemeral", "--range", "192.0.2.0/24"],
                program_name="LANIP",
            )
        self.assertEqual(result, 2)
        activate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
