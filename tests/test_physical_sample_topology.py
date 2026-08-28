import tempfile
import unittest
from pathlib import Path

from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.idf.sample_topology import (
    sample_elements,
    seed_sample_topology,
    validate_topology,
)


class SampleTopologyTests(unittest.TestCase):
    def test_sample_is_valid_and_has_expected_connections(self):
        elements = sample_elements()
        validate_topology(elements)
        self.assertEqual(elements["WL-02"]["endpoints"][1], {"device": "SW-01", "port": "23"})
        self.assertTrue(elements["SW-03"]["ports"]["X1"]["poe"])
        self.assertFalse(elements["SW-03"]["ports"]["X5"]["poe"])
        self.assertEqual(elements["SW-02"]["ports"]["28"]["kind"], "wire.dac")
        self.assertEqual(len(elements["SW-01"]["ports"]), 24)
        self.assertNotIn("0", elements["SW-01"]["ports"])
        self.assertEqual(len(elements["SW-02"]["ports"]), 28)
        self.assertNotIn("0", elements["SW-02"]["ports"])

    def test_seed_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = IDFDatabaseManager(Path(temporary) / "idf.db")
            self.assertEqual(len(seed_sample_topology(database)), 32)
            self.assertEqual(seed_sample_topology(database), ())
            self.assertEqual(len(database.all()), 32)


if __name__ == "__main__":
    unittest.main()
