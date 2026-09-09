import tempfile
import unittest
from pathlib import Path

from lanctl.apps.ip.domain.discovery import DiscoveryProvider, require_real_target
from lanctl.apps.ip.lab import LabDiscoveryProvider, LabRepository, generate_scenario


class LabEmulatorTests(unittest.TestCase):
    def test_same_seed_is_reproducible(self):
        first = generate_scenario(name="office", profile="office", devices=30, seed=84521)
        second = generate_scenario(name="office", profile="office", devices=30, seed=84521)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["devices"], second["devices"])

    def test_different_seed_varies(self):
        first = generate_scenario(name="office", devices=10, seed=1)
        second = generate_scenario(name="office", devices=10, seed=2)
        self.assertNotEqual(first["devices"], second["devices"])

    def test_provider_is_virtual_and_uses_common_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = LabRepository(Path(directory))
            scenario = generate_scenario(name="safe", devices=8, seed=9, active_percent=100)
            repository.save(scenario)
            repository.set_active("safe")
            provider = LabDiscoveryProvider(repository)
            self.assertIsInstance(provider, DiscoveryProvider)
            result = provider.discover()
            self.assertTrue(result.simulated)
            self.assertEqual(result.seed, 9)
            self.assertEqual(len(result.devices), 8)
            self.assertTrue(all("SIMULATED" in item.discovery_methods for item in result.devices))
            with self.assertRaises(PermissionError):
                require_real_target(result.devices[0])

    def test_invalid_capacity_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_scenario(name="too-large", cidr="192.0.2.0/30", devices=4)


if __name__ == "__main__":
    unittest.main()
