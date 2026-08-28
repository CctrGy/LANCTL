import json
import tempfile
import unittest
from pathlib import Path

from lanctl.apps.wire.idf import IDF, IDFSize
from lanctl.apps.wire.idf.database import IDFDatabaseManager


class IDFTests(unittest.TestCase):
    def test_short_and_long_format(self):
        self.assertEqual(str(IDF.build("ab", 7)), "AB-07")
        self.assertEqual(str(IDF.build("abcd", 42)), "ABCD-0042")
        self.assertEqual(IDF.parse("ab-07").size, IDFSize.SHORT)

    def test_string_and_repr_show_the_complete_code(self):
        identifier = IDF.parse("ab-12")
        self.assertEqual(str(identifier), "AB-12")
        self.assertEqual(repr(identifier), "IDF('AB-12')")

    def test_invalid_format_is_rejected(self):
        for value in ("A-01", "ABC-001", "AB-100", "ABCD-10000"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                IDF.parse(value)


class IDFDatabaseManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "physical.db"
        self.database = IDFDatabaseManager(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def test_database_is_json_with_db_extension(self):
        stored = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(stored["format"], "LANWRE-IDF-DB")

    def test_create_assigns_unique_sequential_ids(self):
        first = self.database.create("sw", data={"name": "Switch principal"})
        second = self.database.create("sw")
        self.assertEqual(first["id"], "SW-00")
        self.assertEqual(second["id"], "SW-01")
        self.assertEqual(len(self.database.all()), 2)

    def test_explicit_duplicate_is_rejected(self):
        self.database.add("AP-12")
        with self.assertRaises(ValueError):
            self.database.add("ap-12")

    def test_update_and_delete(self):
        self.database.add("RACK-0001")
        updated = self.database.update("RACK-0001", {"room": "CPD"})
        self.assertEqual(updated["data"], {"room": "CPD"})
        self.database.delete("RACK-0001")
        self.assertFalse(self.database.exists("RACK-0001"))

    def test_prefix_definitions_and_filtered_list(self):
        self.database.define_prefix("sw", "Switch", "Conmutador de red")
        self.database.add("SW-01")
        self.database.add("RT-01")
        self.assertEqual(self.database.get_prefix("SW")["name"], "Switch")
        self.assertEqual([record["id"] for record in self.database.list("sw")], ["SW-01"])


if __name__ == "__main__":
    unittest.main()
