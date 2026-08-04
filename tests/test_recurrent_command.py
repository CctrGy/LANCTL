import io
import unittest
from contextlib import redirect_stdout

from app.cli import build_parser


class RecurrentCommandTests(unittest.TestCase):
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
