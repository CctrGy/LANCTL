import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.cli import build_parser
from app.commands.wol import _validate_graph, run_wol
from app.core.conditions import ConditionContext, evaluate, parse_condition
from app.core.database import DeviceDatabase
from app.plugins.package import verify_package
from app.plugins.wol_runtime import magic_packet, send_magic_packet, validate_mac


class WolTests(unittest.TestCase):
    def test_bundled_lcp_is_valid_trusted_and_narrowly_permissioned(self):
        package = Path(__file__).resolve().parents[1] / "bundled/lanctl.network.wol.lcp"
        manifest = verify_package(package)["manifest"]
        self.assertEqual(manifest.plugin_id, "lanctl.network.wol")
        self.assertEqual(manifest.runtime, "trusted")
        self.assertIn("network.udp", manifest.permissions)

    def test_packet_has_standard_layout_and_rejects_unsafe_macs(self):
        packet = magic_packet("02:11:22:33:44:55")
        self.assertEqual(len(packet), 102)
        self.assertEqual(packet[:6], b"\xff" * 6)
        for value in ("00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF", "01:00:00:00:00:01", "bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_mac(value)

    def test_sender_is_injectable_and_never_uses_shell(self):
        sock = MagicMock()
        factory = MagicMock(return_value=sock)
        count = send_magic_packet("02:11:22:33:44:55", repeat=2, interval=0, socket_factory=factory)
        self.assertEqual(count, 2)
        self.assertEqual(sock.sendto.call_count, 2)
        sock.close.assert_called_once()

    def test_parser_defaults_to_wakeup_and_stacks_conditions(self):
        args = build_parser().parse_args(
            ["wol", "PC", "-if", "offline", "--if", "time after 07:00", "--dry-run"]
        )
        self.assertEqual(args.words, ["PC"])
        self.assertEqual(args.conditions, ["offline", "time after 07:00"])

    def test_closed_condition_parser_and_combinators(self):
        context = ConditionContext(
            online=lambda name: name == "up",
            target="down",
            now=datetime(2026, 8, 3, 8, 0).astimezone(),
        )
        self.assertTrue(evaluate(parse_condition("offline"), context))
        self.assertTrue(evaluate(parse_condition("device up online"), context))
        with self.assertRaises(ValueError):
            parse_condition("__import__('os').system('x')")

    def test_graph_rejects_cycles_and_missing_dependencies(self):
        with self.assertRaisesRegex(ValueError, "ciclo"):
            _validate_graph([{"id": "a", "requires": ["b"]}, {"id": "b", "requires": ["a"]}])
        with self.assertRaisesRegex(ValueError, "inexistente"):
            _validate_graph([{"id": "a", "requires": ["missing"]}])

    def test_dry_run_resolves_device_without_sending(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "devices.json")
            db = DeviceDatabase(path)
            device = db.upsert([{"IP": "192.168.1.8", "MAC": "02:11:22:33:44:55", "ALIAS": "PC"}])[
                0
            ]
            args = build_parser().parse_args(
                ["wol", device.device_id, "--dry-run", "--json", "--database", path]
            )
            with (
                patch("app.commands.wol._online", return_value=False),
                patch("app.commands.wol.send_magic_packet") as send,
                patch("app.commands.wol.write_log"),
            ):
                import contextlib
                from io import StringIO

                output = StringIO()
                with contextlib.redirect_stdout(output):
                    code = run_wol(args)
            self.assertEqual(code, 0)
            send.assert_not_called()
            self.assertEqual(json.loads(output.getvalue())["status"], "sent")

    def test_remote_power_is_blocked_without_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "devices.json")
            DeviceDatabase(path).upsert(
                [{"IP": "192.168.1.8", "MAC": "02:11:22:33:44:55", "ALIAS": "PC"}]
            )
            args = build_parser().parse_args(
                ["wol", "PC", "shutdown", "-t", "10m", "--json", "--database", path]
            )
            with patch("app.commands.wol.write_log"):
                import contextlib
                from io import StringIO

                output = StringIO()
                with contextlib.redirect_stdout(output):
                    code = run_wol(args)
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["error"]["code"], "WOL.POWER.UNSUPPORTED")

    def test_ssh_power_transport_can_be_configured_and_planned(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "devices.json")
            database = DeviceDatabase(path)
            device = database.upsert(
                [
                    {
                        "IP": "192.168.1.8",
                        "MAC": "02:11:22:33:44:55",
                        "ALIAS": "PC",
                    }
                ]
            )[0]
            database.set_protocol(device.device_id, "ssh", True)
            database.bind_credential(device.device_id, "ssh", "cred_test")
            configure = build_parser().parse_args(
                [
                    "wol",
                    device.device_id,
                    "configure",
                    "--power-transport",
                    "ssh",
                    "--power-platform",
                    "windows",
                    "--database",
                    path,
                    "--json",
                ]
            )
            plan = build_parser().parse_args(
                [
                    "wol",
                    device.device_id,
                    "shutdown",
                    "-t",
                    "30s",
                    "--dry-run",
                    "--database",
                    path,
                    "--json",
                ]
            )
            import contextlib
            from io import StringIO

            with patch("app.commands.wol.write_log"):
                with contextlib.redirect_stdout(StringIO()):
                    self.assertEqual(run_wol(configure), 0)
                output = StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(run_wol(plan), 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["status"], "success")
            self.assertIn("shutdown.exe /s /t 30", payload["detail"]["command"])

    def test_false_condition_skips_without_sending(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "devices.json")
            DeviceDatabase(path).upsert(
                [{"IP": "192.168.1.8", "MAC": "02:11:22:33:44:55", "ALIAS": "PC"}]
            )
            args = build_parser().parse_args(
                ["wol", "PC", "-if", "online", "--json", "--database", path]
            )
            with (
                patch("app.commands.wol._online", return_value=False),
                patch("app.commands.wol.send_magic_packet") as send,
                patch("app.commands.wol.write_log"),
            ):
                import contextlib
                from io import StringIO

                output = StringIO()
                with contextlib.redirect_stdout(output):
                    code = run_wol(args)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "skipped")
            send.assert_not_called()

    def test_all_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "devices.json")
            DeviceDatabase(path).upsert([{"IP": "192.168.1.8", "MAC": "02:11:22:33:44:55"}])
            args = build_parser().parse_args(["wol", "placeholder", "--all", "--database", path])
            with self.assertRaisesRegex(ValueError, "--yes"):
                run_wol(args)

    def test_group_wakeup_reuses_one_inventory_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "devices.json")
            database = DeviceDatabase(path)
            database.upsert(
                [
                    {"IP": "192.168.1.8", "MAC": "02:11:22:33:44:55", "GROUP": ["MOVILES"]},
                    {"IP": "192.168.1.9", "MAC": "02:11:22:33:44:66", "GROUP": ["MOVILES"]},
                ]
            )
            args = build_parser().parse_args(
                [
                    "wol",
                    "--group",
                    "moviles",
                    "--dry-run",
                    "--json",
                    "--database",
                    path,
                ]
            )
            import contextlib
            from io import StringIO

            with (
                patch.object(DeviceDatabase, "load", wraps=database.load) as load,
                patch("app.commands.wol._online", return_value=False),
                patch("app.commands.wol.write_log"),
                contextlib.redirect_stdout(StringIO()),
            ):
                self.assertEqual(run_wol(args), 0)
            self.assertEqual(load.call_count, 1)


if __name__ == "__main__":
    unittest.main()
