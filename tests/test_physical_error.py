import json
import tempfile
import unittest
from pathlib import Path

from lanctl.apps.wire.error import Error, ErrorLevel
from lanctl.apps.wire.log import write_exception


class ErrorTests(unittest.TestCase):
    def test_original_constructor_remains_compatible(self):
        error = Error(40, "idf.database", "IDF duplicado", True)
        self.assertEqual(error.level, 40)
        self.assertTrue(error.br)
        self.assertIsInstance(error, Exception)

    def test_string_and_repr_are_informative(self):
        error = Error(ErrorLevel.ERROR, "idf", "formato inválido", code="IDF_FORMAT")
        self.assertEqual(str(error), "[IDF_FORMAT] idf: formato inválido")
        self.assertIn("Error(level=40", repr(error))

    def test_error_can_be_serialized_to_json(self):
        error = Error(
            ErrorLevel.WARNING,
            "manager",
            "registro no encontrado",
            context={"idf": "AP-12"},
        )
        payload = error.to_dict()
        json.dumps(payload)
        restored = Error.from_dict(payload)
        self.assertEqual(restored.context, {"idf": "AP-12"})
        self.assertEqual(restored.created_at, error.created_at)

    def test_wrap_preserves_original_exception(self):
        original = ValueError("JSON incorrecto")
        error = Error.wrap(original, caused="xfile.read", code="INVALID_JSON")
        self.assertIs(error.cause, original)
        self.assertEqual(error.to_dict()["cause"]["type"], "ValueError")

    def test_error_writes_a_structured_log_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            error = Error(
                ErrorLevel.ERROR,
                "idf.database",
                "IDF duplicado",
                True,
                code="IDF_DUPLICATED",
                context={"idf": "SW-12"},
            )
            path = error.write_log(temporary)
            line = path.read_text(encoding="utf-8")
            self.assertIn("level=ERROR | code=IDF_DUPLICATED", line)
            self.assertIn('context={"idf":"SW-12"}', line)

    def test_regular_exception_is_wrapped_and_logged(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = ValueError("JSON incorrecto")
            error = write_exception(
                original,
                caused="xfile.read",
                directory=temporary,
                code="INVALID_JSON",
            )
            self.assertIs(error.cause, original)
            logs = list(Path(temporary).glob("*.log"))
            self.assertEqual(len(logs), 1)
            self.assertIn("cause_type=ValueError", logs[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
