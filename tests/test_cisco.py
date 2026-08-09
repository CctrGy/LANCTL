import json
import tempfile
import unittest
from pathlib import Path

from app.cisco.adapters import FakeCiscoAdapter
from app.cisco.context import CiscoContext
from app.cisco.executor import CiscoExecutor
from app.cisco.models import Risk
from app.cisco.planner import CiscoPlanner
from app.cisco.profiles import load_profile
from app.commands.switch import _device_profile
from app.models import Device


class CiscoCommandLayerTests(unittest.TestCase):
    def setUp(self):
        self.device = Device(
            ip="192.168.1.254",
            mac="5C:71:0D:BB:6A:3B",
            alias="SW",
        )
        self.profile = load_profile("cisco-s300-24", Path("missing-profiles.json"))
        self.planner = CiscoPlanner(self.device, self.profile)

    def test_historical_and_canonical_aliases_resolve_once(self):
        self.assertEqual(self.profile.resolve_port("x7").native, "gi1/0/7")
        self.assertEqual(self.profile.resolve_port("p7").id, "port:7")
        self.assertEqual(self.profile.resolve_port("xg1").id, "port:25")
        self.assertEqual(self.profile.resolve_port("xg2").id, "port:26")

    def test_read_only_plan_is_typed_and_rendered(self):
        plan = self.planner.plan(["port", "show", "x7", "status"])
        self.assertEqual(plan.risk, Risk.READ_ONLY)
        self.assertEqual(plan.target, "port:7")
        self.assertEqual(plan.native_commands, ("show interfaces status gi1/0/7",))

    def test_selected_port_can_omit_repeated_reference(self):
        context = CiscoContext(self.profile)
        context.select("x3")
        plan = self.planner.plan(["port", "show", "vlan"], context.selected_port)
        self.assertEqual(plan.native_target, "gi1/0/3")

        short_plan = self.planner.plan(["show", "status"], context.selected_port)
        self.assertEqual(short_plan.native_commands, ("show interfaces status gi1/0/3",))

        disable = self.planner.plan(["disable"], context.selected_port)
        self.assertEqual(disable.native_commands[-1], "shutdown")

    def test_stop_alias_maps_to_filtered_disable_plan(self):
        plan = self.planner.plan(["stop", "x2"])
        self.assertEqual(plan.command_id, "switch.port.disable")
        self.assertEqual(plan.risk, Risk.CONFIG_CHANGE)
        self.assertEqual(plan.native_commands[-1], "shutdown")

    def test_disruptive_and_persist_risks_are_distinct(self):
        reset = self.planner.plan(["port", "reset", "x1"])
        save = self.planner.plan(["save-config"])
        self.assertEqual(reset.risk, Risk.DISRUPTIVE)
        self.assertEqual(save.risk, Risk.PERSIST_CONFIG)
        self.assertTrue(reset.confirmation_required)

    def test_unknown_show_and_injected_value_are_rejected(self):
        with self.assertRaises(ValueError):
            self.planner.plan(["show", "invented-command"])
        with self.assertRaises(ValueError):
            self.planner.plan(["port", "set", "x1", "description", "NAS; shutdown"])

    def test_speed_and_duplex_are_typed(self):
        with self.assertRaises(ValueError):
            self.planner.plan(["port", "set", "x1", "speed", "2500"])
        plan = self.planner.plan(["port", "set", "x1", "duplex", "full"])
        self.assertEqual(plan.native_commands[-1], "duplex full")

    def test_fake_adapter_never_requires_a_connection(self):
        adapter = FakeCiscoAdapter()
        plan = self.planner.plan(["show", "version"])
        output = adapter.execute(plan)
        self.assertEqual(adapter.executed, [plan])
        self.assertEqual(output, ["SIMULADO: show version"])

    def test_executor_enforces_approval_independently_from_cli(self):
        adapter = FakeCiscoAdapter()
        executor = CiscoExecutor(adapter)
        plan = self.planner.plan(["port", "disable", "x1"])
        with self.assertRaises(ValueError):
            executor.execute(plan)
        self.assertEqual(adapter.executed, [])
        result = executor.execute(plan, dry_run=True)
        self.assertEqual(result.status, "DRY_RUN")
        self.assertEqual(adapter.executed, [])

    def test_external_profile_supports_human_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profiles.json"
            path.write_text(
                json.dumps(
                    {
                        "profiles": [
                            {
                                "id": "custom",
                                "model": "Custom",
                                "ports": [
                                    {
                                        "id": "port:7",
                                        "native": "GigabitEthernet1/7",
                                        "aliases": ["x7"],
                                        "label": "NAS",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            profile = load_profile("custom", path)
            self.assertEqual(profile.resolve_port("NAS").native, "GigabitEthernet1/7")

    def test_device_label_overlays_profile_without_changing_native_name(self):
        self.device.protocol_options["cisco-cli"] = {
            "profile": "cisco-s300-24",
            "portLabels": {"port:7": "NAS"},
        }
        overlaid = _device_profile(self.device, self.profile)
        self.assertEqual(overlaid.resolve_port("NAS").native, "gi1/0/7")
        self.assertEqual(self.profile.resolve_port("x7").label, "")


if __name__ == "__main__":
    unittest.main()
