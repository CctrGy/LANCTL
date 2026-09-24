import json
import tempfile
import unittest
from pathlib import Path

from lanctl.apps.wire.cli.commands import CommandProcessor
from lanctl.apps.wire.cli.main import _command_parts, build_parser
from lanctl.apps.wire.idf import IDF, IDFSize
from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.topology import apply_device_preset, build_ports, compatible_connection


class IDFTests(unittest.TestCase):
    def test_supported_uniform_lengths(self):
        self.assertEqual(str(IDF.build("ab", 7)), "AB-07")
        self.assertEqual(str(IDF.build("abc", 42)), "ABC-042")
        self.assertEqual(str(IDF.build("abcd", 42)), "ABCD-0042")
        self.assertEqual(str(IDF.build("abcde", 42)), "ABCDE-00042")
        self.assertEqual(IDF.parse("ab-07").size, IDFSize.SHORT)

    def test_prefix_and_number_widths_are_independent(self):
        self.assertEqual(str(IDF.parse("abc-12")), "ABC-12")
        self.assertEqual(str(IDF.parse("ab-00123")), "AB-00123")
        self.assertEqual(str(IDF.build("abc", 12, number_width=5)), "ABC-00012")

    def test_string_and_repr_show_the_complete_code(self):
        identifier = IDF.parse("ab-12")
        self.assertEqual(str(identifier), "AB-12")
        self.assertEqual(repr(identifier), "IDF('AB-12')")

    def test_invalid_format_is_rejected(self):
        for value in ("A-01", "ABCDEF-001", "AB-1", "AB-100000", "AB1-01"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                IDF.parse(value)

    def test_router_preset_and_connector_compatibility(self):
        router = apply_device_preset({}, "router")
        self.assertEqual(router["type"], "device.router")
        self.assertEqual(len(router["ports"]), 6)
        self.assertIn("FIBER", router["ports"])
        compatible, _ = compatible_connection(
            {"kind": "connection.rj45", "connectorGenders": ["male"]},
            {"kind": "wire.copper", "connectorGender": "female"},
            wire_end=0,
        )
        self.assertTrue(compatible)
        compatible, reason = compatible_connection(
            {"kind": "wire.fiber", "connectorGenders": ["male"]},
            {"kind": "wire.copper", "connectorGender": "female"},
            wire_end=0,
        )
        self.assertFalse(compatible)
        self.assertIn("fib", reason)

    def test_hardware_presets_create_expected_port_layouts(self):
        compatible, _ = compatible_connection({"kind": "wire.dac"}, {"kind": "wire.dac"})
        self.assertTrue(compatible)
        compatible, _ = compatible_connection({"kind": "wire.dac"}, {"kind": "wire.fiber"})
        self.assertFalse(compatible)
        self.assertEqual(len(apply_device_preset({}, "switch-12")["ports"]), 12)
        self.assertEqual(list(apply_device_preset({}, "switch-12")["ports"])[:2], ["X1", "X2"])
        self.assertEqual(list(apply_device_preset({}, "pc-2")["ports"]), ["LAN1", "LAN2"])

    def test_port_template_is_replicated_with_fixed_female_ports(self):
        ports = build_ports(2, "LAN{n}", kind="wire.copper", poe=True, speeds=["2.5G"])
        self.assertEqual(ports["LAN1"]["connectorGender"], "female")
        self.assertEqual(ports["LAN2"]["poe"], True)
        self.assertEqual(ports["LAN2"]["speeds"], ["2.5G"])

    def test_mixed_port_series_have_independent_numbers_and_fixed_fiber(self):
        ports = build_ports(6, "X{n}:4,XG{a}:2,FIBER")
        self.assertEqual(list(ports), ["X1", "X2", "X3", "X4", "XG1", "XG2", "FIBER"])
        self.assertEqual(ports["FIBER"]["kind"], "connection.fiber")
        with self.assertRaisesRegex(ValueError, "duplicado"):
            build_ports(2, "X{n}:2,X{a}:2")

    def test_male_device_port_is_not_compatible_with_fixed_male_wire(self):
        compatible, reason = compatible_connection(
            {"kind": "wire.copper"}, {"kind": "wire.copper", "connectorGender": "male"}
        )
        self.assertFalse(compatible)
        self.assertIn("hembra", reason)


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

    def test_cable_prefixes_create_cables_with_matching_medium(self):
        fiber = self.database.create("fb")
        copper = self.database.create("wl")
        self.assertEqual(fiber["data"], {"type": "wire", "kind": "wire.fiber", "endpoints": []})
        self.assertEqual(copper["data"]["kind"], "wire.copper")
        self.assertEqual(self.database.add("WE-01")["data"]["type"], "wire")
        explicit = self.database.add("FB-01", {"type": "device.switch", "name": "Excepción"})
        self.assertEqual(explicit["data"]["type"], "device.switch")

    def test_existing_untyped_fiber_is_migrated_without_overwriting_explicit_type(self):
        self.database.add("FB-02", {"type": "device.router", "name": "Explícito"})
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        raw["records"]["FB-00"] = self.database._new_record(
            IDF.parse("FB-00"), {"name": "Fibra antigua"}
        )
        raw["records"]["FB-00"]["data"] = {"name": "Fibra antigua"}
        self.path.write_text(json.dumps(raw), encoding="utf-8")
        reopened = IDFDatabaseManager(self.path)
        self.assertEqual(reopened.get("FB-00")["data"]["type"], "wire")
        self.assertEqual(reopened.get("FB-00")["data"]["kind"], "wire.fiber")
        self.assertEqual(reopened.get("FB-00")["data"]["name"], "Fibra antigua")
        self.assertEqual(reopened.get("FB-02")["data"]["type"], "device.router")

    def test_create_supports_custom_prefix_and_number_widths(self):
        self.assertEqual(self.database.create("swx")["id"], "SWX-000")
        self.assertEqual(self.database.create("ap", number_width=5)["id"], "AP-00000")

    def test_add_command_creates_multiple_clean_identifiers(self):
        result = CommandProcessor(self.database).execute("add sw --digits 5 -more 3")
        self.assertEqual(result.lines, ("Creados SW-00000, SW-00001, SW-00002",))
        self.assertEqual(self.database.get("SW-00000")["data"], {})
        self.assertEqual(
            CommandProcessor(self.database).execute("add rt --more=2").lines,
            ("Creados RT-00, RT-01",),
        )
        error = CommandProcessor(self.database).execute("add sw name=core")
        self.assertIn("no admite CLAVE=VALOR", error.lines[0])

    def test_idf_new_defines_profile_and_add_creates_typed_records(self):
        processor = CommandProcessor(self.database)
        result = processor.execute("idf new BR -type wire.fiber")
        self.assertEqual(result.lines, ("Prefijo BR definido como wire.fiber",))
        self.assertEqual(self.database.list("BR"), [])
        self.assertEqual(self.database.get_prefix("BR")["type_profile"], "wire.fiber")
        reopened = CommandProcessor(IDFDatabaseManager(self.path))
        result = reopened.execute(
            'idf add BR-10 -name fiber -alias Entrada -descriptionn "Fibra de la compañía"'
        )
        self.assertEqual(result.lines, ("Creado BR-10 (wire.fiber)",))
        fiber = self.database.get("BR-10")["data"]
        self.assertEqual(fiber["type"], "wire")
        self.assertEqual(fiber["kind"], "wire.fiber")
        self.assertEqual(fiber["name"], "fiber")
        self.assertEqual(fiber["alias"], "Entrada")
        self.assertEqual(fiber["description"], "Fibra de la compañía")
        self.assertEqual(fiber["endpoints"], [])

        processor.execute("idf new SW -type switch.12Ports")
        processor.execute("idf add SW-00 -name Core")
        switch = self.database.get("SW-00")["data"]
        self.assertEqual(switch["type"], "device.switch")
        self.assertEqual(switch["subtype"], "switch.12Ports")
        self.assertEqual(len(switch["ports"]), 12)
        self.assertEqual(switch["name"], "Core")

        processor.execute("idf new RT -type router.otg")
        processor.execute("idf add RT-01")
        router = self.database.get("RT-01")["data"]
        self.assertEqual(router["type"], "device.router")
        self.assertEqual(list(router["ports"]), ["FIBER", "WLAN"])
        self.assertEqual(router["ports"]["FIBER"]["kind"], "connection.fiber")
        self.assertEqual(router["ports"]["WLAN"]["kind"], "wire.copper")

    def test_idf_list_includes_defined_and_legacy_record_prefixes(self):
        processor = CommandProcessor(self.database)
        self.assertEqual(processor.execute("idf list").lines, ("No hay prefijos IDF.",))
        processor.execute("idf new FB -type wire.fiber")
        self.database.add("WR-00", {"type": "wire"})
        lines = processor.execute("idf list").lines
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].split(), ["FB", "wire.fiber", "0", "IDF"])
        self.assertEqual(lines[1].split(), ["WR", "sin", "perfil", "1", "IDF"])
        self.assertEqual(build_parser().parse_args(["idf", "list"]).idf_action, "list")
        self.assertIn("WR-00", processor.execute("idf list wr").lines[0])
        self.assertEqual(
            processor.execute("idf list FB").lines, ("No hay elementos con prefijo FB.",)
        )
        self.assertEqual(processor.execute("idf list wr").list_prefix, "WR")
        self.assertIn("Error [", processor.execute("idf list WR extra").lines[0])

    def test_idf_show_edit_delete_and_types(self):
        processor = CommandProcessor(self.database)
        self.assertIn("router.otg", processor.execute("idf types").lines)
        processor.execute("idf new RT -type router.otg")
        self.assertIn('"type_profile": "router.otg"', processor.execute("idf show RT").lines[0])
        processor.execute("idf add RT-00")
        self.assertIn('"id": "RT-00"', processor.execute("idf show RT-00").lines[0])
        self.assertIn(
            "Actualizado RT-00", processor.execute("idf edit RT-00 alias=Central").lines[0]
        )
        self.assertEqual(self.database.get("RT-00")["data"]["alias"], "Central")
        self.assertIn(
            "actualizado a router.gateway",
            processor.execute("idf edit RT -type router.gateway").lines[0],
        )
        processor.execute('idf edit RT -name "Router principal"')
        self.assertEqual(self.database.get_prefix("RT")["name"], "Router principal")
        self.assertEqual(self.database.get("RT-00")["data"]["subtype"], "router.otg")
        self.assertIn("Error [", processor.execute("idf delete RT").lines[0])
        self.assertEqual(processor.execute("idf delete RT-00").lines, ("Eliminado RT-00",))
        self.assertIsNotNone(self.database.get_prefix("RT"))

    def test_idf_new_accepts_coper_alias_and_rejects_invalid_options_before_creation(self):
        processor = CommandProcessor(self.database)
        self.assertIn("no tiene tipo", processor.execute("idf add BR-00").lines[0])
        self.assertFalse(self.database.exists("BR-00"))
        processor.execute("idf new WE -type wire.coper")
        processor.execute("idf add WE-01")
        self.assertEqual(self.database.get("WE-01")["data"]["kind"], "wire.copper")
        for command in (
            "idf new SW-01 -alias Core",
            "idf new SW-01 -type switch.99Ports",
            "idf new SW-01 -type switch.5Ports",
            "idf new SX -type switch.5Ports -alias",
            "idf new SW-01 -type switch.5Ports -unknown x",
            "idf add SW-01 -type wire.fiber",
        ):
            self.assertIn("Error [", processor.execute(command).lines[0])
            self.assertFalse(self.database.exists("SW-01"))

    def test_external_parser_accepts_idf_new_options(self):
        args = build_parser().parse_args(
            [
                "idf",
                "new",
                "SW",
                "-type",
                "switch.5Ports",
            ]
        )
        self.assertEqual(args.element_type, "switch.5Ports")
        result = CommandProcessor(self.database).execute_parts(_command_parts(args))
        self.assertEqual(result.lines, ("Prefijo SW definido como switch.5Ports",))
        self.assertIsNone(self.database.get("SW-01"))
        args = build_parser().parse_args(
            [
                "idf",
                "add",
                "SW-01",
                "-name",
                "Core",
                "-descriptionn",
                "Switch del rack",
            ]
        )
        result = CommandProcessor(self.database).execute_parts(_command_parts(args))
        self.assertEqual(result.lines, ("Creado SW-01 (switch.5Ports)",))
        self.assertEqual(self.database.get("SW-01")["data"]["description"], "Switch del rack")

    def test_element_command_updates_global_template_and_single_port_fields(self):
        self.database.add(
            "PC-01", {"type": "device.pc", "ports": {"LAN1": {"kind": "wire.copper"}}}
        )
        result = CommandProcessor(self.database).execute(
            "element PC-01 name=OTG ports=2 templatePoe=yes port.LAN2.speeds=1G/2.5G"
        )
        data = self.database.get("PC-01")["data"]
        self.assertIn("Actualizado PC-01", result.lines[0])
        self.assertEqual(data["name"], "OTG")
        self.assertEqual(list(data["ports"]), ["LAN1", "LAN2"])
        self.assertTrue(data["ports"]["LAN1"]["poe"])
        self.assertEqual(data["ports"]["LAN2"]["speeds"], ["1G", "2.5G"])

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

    def test_connected_port_cannot_be_removed_by_cli_or_database_update(self):
        self.database.add(
            "SW-01",
            {
                "type": "device.switch",
                "ports": {
                    "LAN1": {"kind": "wire.copper"},
                    "LAN2": {"kind": "wire.copper"},
                },
            },
        )
        self.database.add(
            "WL-01",
            {
                "type": "wire",
                "kind": "wire.copper",
                "endpoints": [
                    {"device": "SW-01", "port": "LAN2"},
                ],
            },
        )
        result = CommandProcessor(self.database).execute("idf edit SW-01 ports=1")
        self.assertIn("desconecta antes los puertos: LAN2", result.lines[0])
        with self.assertRaisesRegex(ValueError, "desconecta antes los puertos: LAN2"):
            self.database.update("SW-01", {"type": "device.switch", "ports": {"LAN1": {}}})
        self.assertIn("LAN2", self.database.get("SW-01")["data"]["ports"])
        self.assertEqual(
            self.database.get("WL-01")["data"]["endpoints"],
            [{"device": "SW-01", "port": "LAN2"}],
        )

    def test_port_rename_and_reorder_keep_connected_wire_consistent(self):
        self.database.add(
            "SW-01",
            {
                "type": "device.switch",
                "ports": {
                    "X1": {"kind": "wire.copper"},
                    "X2": {"kind": "wire.copper"},
                },
            },
        )
        self.database.add(
            "WL-01",
            {
                "type": "wire",
                "kind": "wire.copper",
                "endpoints": [
                    {"device": "SW-01", "port": "X1"},
                ],
            },
        )
        self.database.edit_port("SW-01", "X1", name="UPLINK")
        self.database.edit_port("SW-01", "UPLINK", position=2)
        self.assertEqual(list(self.database.get("SW-01")["data"]["ports"]), ["X2", "UPLINK"])
        self.assertEqual(self.database.get("WL-01")["data"]["endpoints"][0]["port"], "UPLINK")
        with self.assertRaisesRegex(ValueError, "ya existe"):
            self.database.edit_port("SW-01", "UPLINK", name="X2")

    def test_prefix_definitions_and_filtered_list(self):
        self.database.define_prefix("sw", "Switch", "Conmutador de red")
        self.database.add("SW-01")
        self.database.add("RT-01")
        self.assertEqual(self.database.get_prefix("SW")["name"], "Switch")
        self.assertEqual([record["id"] for record in self.database.list("sw")], ["SW-01"])


if __name__ == "__main__":
    unittest.main()
