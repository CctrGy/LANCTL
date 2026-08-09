import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from app.cli import build_parser


class RecurrentCommandTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        recurrent_path = Path(self.temporary_directory.name) / "recurrent-elements.json"
        recurrent_path.write_text(
            json.dumps(
                [
                    {"cnf": "S", "ALIAS": "VM1", "MAC": "5E:8C:B3:08:05:D4", "NAME": "VM1"},
                    {
                        "cnf": "S",
                        "ALIAS": "LV1",
                        "MAC": "AA:BB:CC:DD:EE:FF",
                        "NAME": "LaptopVictor1",
                    },
                ]
            ),
            encoding="utf-8",
        )
        path_patch = patch(
            "app.core.recurrent_elements.application_path",
            return_value=recurrent_path,
        )
        path_patch.start()
        self.addCleanup(path_patch.stop)

    def _run(self, arguments: list[str]) -> str:
        args = build_parser().parse_args([*arguments])
        output = io.StringIO()
        with redirect_stdout(output):
            result = args.handler(args)
        self.assertEqual(result, 0)
        return output.getvalue()

    def test_list_recurrent_does_not_include_ip(self):
        output = self._run(["list", "-recurrent"])
        header = output.splitlines()[0]
        self.assertNotIn("IP", header.split())
        self.assertIn("VM1", output)
        self.assertIn("5E:8C:B3:08:05:D4", output)

    def test_recurrent_list_has_the_same_ip_free_view(self):
        output = self._run(["recurrent", "-list"])
        header = output.splitlines()[0]
        self.assertNotIn("IP", header.split())
        self.assertIn("LV1", output)
        self.assertNotIn("192.168.", output)

    def test_json_output_omits_ip_field(self):
        output = self._run(["recurrent", "-list", "--format", "json"])
        self.assertNotIn('"IP"', output)
        self.assertIn('"MAC"', output)


if __name__ == "__main__":
    unittest.main()
