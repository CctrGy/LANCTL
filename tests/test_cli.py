import ipaddress
import json
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from app import __version__
from app.cli import build_parser
from unittest.mock import patch

from colorama import Fore, Style

from app.commands.group import _paint
from app.commands.download_settings import lan_settings
from app.commands.list import active_flags, filter_rows, ip_in_range
from app.core.database import DeviceDatabase
from app.core.config import normalize_dhcp_range
from app.core.credentials import CredentialStore
from app.core.differences import compare_scan
from app.core.group_database import GroupDatabase
from app.core.logger import write_database_log, write_log
from app.core.log_cleanup import cleanup_old_logs
from app.core.tr064 import Tr064Client
from app.models import Device, normalize_cnf, normalize_mac
from app.core.output import STRIKETHROUGH, normalize_columns, render_records
from app.services.lan_scanner import LanScanner, resolve_network
from app.services.manufacturer import detect_manufacturer
from app.protocols.ssh import SSH_PROFILES, SshProfile, run_show_command
from app.commands.terminal import choose_terminal
from app.terminals.tr064 import parse_call


class OutputTests(unittest.TestCase):
    def test_response_ms_is_aligned_on_decimal_point(self):
        rendered = render_records(
            [
                {"IP": "192.168.1.1", "responseMs": 2.3},
                {"IP": "192.168.1.2", "responseMs": 12.3},
                {"IP": "192.168.1.3", "responseMs": 123.4},
            ],
            "table",
            columns=["ip", "ms"],
        )
        values = rendered.splitlines()[2:]
        self.assertEqual(len({line.index(".") for line in values}), 1)

    def test_table_shrinks_to_terminal_width(self):
        rendered = render_records(
            [Device(
                ip="192.168.100.250", mac="AA:BB:CC:DD:EE:FF",
                alias="ALIAS-MUY-LARGO", name="Nombre especialmente largo",
                description="Descripcion extensa de elemento",
            )],
            "table",
            max_width=80,
        )
        self.assertTrue(all(len(line) <= 80 for line in rendered.splitlines()))
        self.assertIn("…", rendered)

    def test_very_narrow_table_changes_to_vertical_view(self):
        rendered = render_records(
            [Device(ip="192.168.1.10", mac="AA:BB:CC:DD:EE:FF", alias="NAS")],
            "table",
            max_width=40,
        )
        self.assertTrue(all(len(line) <= 40 for line in rendered.splitlines()))
        self.assertIn("192.168.1.10", rendered)
        self.assertIn("AA:BB:CC:DD:EE:FF", rendered)

    def test_default_table_uses_standard_minimum_column_widths(self):
        rendered = render_records(
            [
                {
                    "IP": "192.168.1.1",
                    "cnf": "O",
                    "ALIAS": "GATEWAY",
                    "MAC": "80:23:95:AF:65:1B",
                    "NAME": "fritz.box",
                    "GROUP": ["BASIC"],
                    "description": "Puerta de enlace de la red",
                }
            ],
            "table",
        )
        self.assertEqual(
            rendered.splitlines()[1].split("  "),
            ["-" * 13, "-" * 3, "-" * 13, "-" * 19, "-" * 17, "-" * 8, "-" * 42],
        )

    def test_dhcp_range_is_delimited_with_table_separators(self):
        rendered = render_records(
            [
                {"IP": "192.168.1.11", "ALIAS": "NAS"},
                {"IP": "192.168.1.16", "ALIAS": "DHCP1"},
                {"IP": "192.168.1.42", "ALIAS": "DHCP2"},
                {"IP": "192.168.1.254", "ALIAS": "SW"},
                {"IP": "-", "ALIAS": "SIN_IP"},
            ],
            "table",
            columns=["ip", "alias"],
            section_ip_range="192.168.1.16-192.168.1.192",
        )
        lines = rendered.splitlines()
        separator = lines[1]
        self.assertEqual(lines.count(separator), 3)
        self.assertEqual(lines[3], separator)
        self.assertIn("192.168.1.16", lines[4])
        self.assertIn("192.168.1.42", lines[5])
        self.assertEqual(lines[6], separator)
        self.assertIn("192.168.1.254", lines[7])
        self.assertIn("SIN_IP", lines[8])

    def test_dhcp_separators_do_not_change_json(self):
        rendered = render_records(
            [{"IP": "192.168.1.20", "ALIAS": "PC"}],
            "json",
            columns=["ip", "alias"],
            section_ip_range="192.168.1.16-192.168.1.192",
        )
        self.assertEqual(
            json.loads(rendered),
            [{"IP": "192.168.1.20", "ALIAS": "PC"}],
        )

    def test_active_rows_are_bright_and_inactive_rows_are_dim(self):
        rendered = render_records(
            [
                {
                    "IP": "192.168.1.10",
                    "ALIAS": "ACTIVO",
                    "MAC": "00:11:22:33:44:55",
                },
                {
                    "IP": "192.168.1.20",
                    "ALIAS": "INACTIVO",
                    "MAC": "00:11:22:33:44:66",
                },
            ],
            "table",
            color=True,
            active_rows=[True, False],
        )
        self.assertIn(Style.BRIGHT + Fore.LIGHTBLUE_EX + "192.168.1.10", rendered)
        inactive_style = Style.DIM
        self.assertIn(inactive_style + Fore.BLUE + "192.168.1.20", rendered)
        self.assertIn(inactive_style + Fore.YELLOW + "INACTIVO", rendered)
        self.assertIn(
            inactive_style + Fore.MAGENTA + "00:11:22:33:44:66",
            rendered,
        )
        self.assertNotIn(STRIKETHROUGH, rendered)

    def test_columns_can_be_selected_and_ordered(self):
        rendered = render_records(
            [
                {
                    "IP": "192.168.1.1",
                    "ALIAS": "GATEWAY",
                    "MAC": "AA:BB:CC:DD:EE:FF",
                }
            ],
            "table",
            columns=["alias", "ip"],
        )
        header = rendered.splitlines()[0]
        self.assertLess(header.index("alias"), header.index("ip"))
        self.assertNotIn("mac", header)

    def test_json_respects_selected_columns(self):
        rendered = render_records(
            [{"IP": "192.168.1.1", "MAC": "AA:BB:CC:DD:EE:FF"}],
            "json",
            columns=["mac"],
        )
        self.assertEqual(
            json.loads(rendered),
            [{"MAC": "AA:BB:CC:DD:EE:FF"}],
        )


class CredentialTests(unittest.TestCase):
    def test_global_credential_list_has_no_element_selector(self):
        args = build_parser().parse_args(["credential", "list"])
        self.assertEqual(args.selector, "list")
        self.assertIsNone(args.action)

    def test_store_round_trip_and_file_does_not_contain_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".credentials"
            store = CredentialStore(
                str(path),
                protect=lambda value: b"encrypted:" + value[::-1],
                unprotect=lambda value: value.removeprefix(b"encrypted:")[::-1],
            )
            reference = store.set("dev_test", "tr-064", "api-user", "secret-value")
            self.assertEqual(store.get(reference)["username"], "api-user")
            self.assertEqual(store.get(reference)["password"], "secret-value")
            self.assertNotIn(b"secret-value", path.read_bytes())


class Tr064Tests(unittest.TestCase):
    def test_lan_settings_normalizes_network_and_dhcp(self):
        result = lan_settings(
            {
                "NewIPRouters": "192.168.1.1",
                "NewSubnetMask": "255.255.255.0",
                "NewMinAddress": "192.168.1.20",
                "NewMaxAddress": "192.168.1.200",
                "NewDHCPServerEnable": "1",
                "NewDHCPLeaseTime": "86400",
                "NewDNSServers": "192.168.1.1,1.1.1.1",
                "NewDomainName": "fritz.box",
            },
            "192.168.1.1",
            49000,
        )
        self.assertEqual(result["range"], "192.168.1.0/24")
        self.assertEqual(
            result["dhcpRange"], "192.168.1.20-192.168.1.200"
        )
        self.assertTrue(result["dhcpEnabled"])
        self.assertEqual(result["dhcpLeaseTime"], 86400)
        self.assertEqual(result["dnsServers"], ["192.168.1.1", "1.1.1.1"])

    def test_client_discovers_service_and_parses_soap_response(self):
        description = b"""<?xml version="1.0"?>
        <root xmlns="urn:dslforum-org:device-1-0">
          <device><serviceList><service>
            <serviceType>urn:dslforum-org:service:LANHostConfigManagement:1</serviceType>
            <serviceId>urn:LANHostConfigManagement-com:serviceId:LANHostConfigManagement1</serviceId>
            <controlURL>/upnp/control/lanhostconfigmgm</controlURL>
            <SCPDURL>/lanhostconfigmgmSCPD.xml</SCPDURL>
          </service></serviceList></device>
        </root>"""
        response = b"""<?xml version="1.0"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
          <s:Body>
            <u:GetInfoResponse xmlns:u="urn:dslforum-org:service:LANHostConfigManagement:1">
              <NewSubnetMask>255.255.255.0</NewSubnetMask>
              <NewMinAddress>192.168.1.20</NewMinAddress>
            </u:GetInfoResponse>
          </s:Body>
        </s:Envelope>"""

        class FakeResponse:
            def __init__(self, value):
                self.value = value

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return None

            def read(self):
                return self.value

        class FakeOpener:
            def __init__(self):
                self.requests = []

            def open(self, request, timeout):
                self.requests.append(request)
                return FakeResponse(description if isinstance(request, str) else response)

        opener = FakeOpener()
        client = Tr064Client("192.168.1.1", "user", "pass", opener=opener)
        values = client.call("LANHostConfigManagement", "GetInfo")
        self.assertEqual(values["NewSubnetMask"], "255.255.255.0")
        self.assertEqual(len(opener.requests), 2)
        request = opener.requests[1]
        self.assertEqual(
            request.headers["Soapaction"],
            '"urn:dslforum-org:service:LANHostConfigManagement:1#GetInfo"',
        )

    def test_device_protocol_and_credential_reference_survive_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [{"IP": "192.168.1.1", "MAC": "10:20:30:40:50:60"}]
            )
            device = database.resolve("192.168.1.1")
            database.bind_credential(
                "192.168.1.1", "TR_064", "cred_example"
            )
            rescanned = database.upsert(
                [{"IP": "192.168.1.2", "MAC": "10:20:30:40:50:60"}]
            )[0]
            self.assertEqual(rescanned.device_id, device.device_id)
            self.assertEqual(rescanned.protocols, ["tr-064"])
            self.assertEqual(
                rescanned.credentials, {"tr-064": "cred_example"}
            )

    def test_column_names_accept_commas_and_reject_unknown_values(self):
        self.assertEqual(
            normalize_columns(["ip,mac", "manufacturer", "IP"]),
            ["ip", "mac", "manufacturer"],
        )
        with self.assertRaises(ValueError):
            normalize_columns(["inventado"])

    def test_json_contract_uses_ip_and_mac(self):
        rendered = render_records(
            [
                {
                    "IP": "192.168.1.1",
                    "ALIAS": "GATEWAY",
                    "MAC": "AA:BB:CC:DD:EE:FF",
                    "NAME": "Mi router",
                    "defaultName": "router",
                }
            ],
            "json",
        )
        self.assertEqual(
            json.loads(rendered),
            [
                {
                    "IP": "192.168.1.1",
                    "ALIAS": "GATEWAY",
                    "MAC": "AA:BB:CC:DD:EE:FF",
                    "NAME": "Mi router",
                    "defaultName": "router",
                }
            ],
        )

    def test_empty_table_still_has_headers(self):
        self.assertIn("IP", render_records([], "table"))
        self.assertIn("mac", render_records([], "table"))

    def test_table_hides_default_name(self):
        rendered = render_records(
            [{"IP": "192.168.1.1", "defaultName": "router"}], "table"
        )
        self.assertNotIn("defaultName", rendered)
        self.assertNotIn("router", rendered)

    def test_manufacturer_is_only_shown_when_requested(self):
        record = {
            "IP": "192.168.1.1",
            "MAC": "00:11:22:33:44:55",
            "manufacturer": "Fabricante de prueba",
        }
        self.assertNotIn(
            "Fabricante de prueba",
            render_records([record], "table"),
        )
        self.assertIn(
            "Fabricante de prueba",
            render_records([record], "table", include_manufacturer=True),
        )

    def test_cnf_uses_visual_symbols(self):
        rendered = render_records(
            [
                {"IP": "192.168.1.1", "cnf": "O"},
                {"IP": "192.168.1.2", "cnf": "X"},
                {"IP": "192.168.1.3", "cnf": "-"},
                {"IP": "192.168.1.4", "cnf": "S"},
                {"IP": "192.168.1.5", "cnf": "@"},
            ],
            "table",
        )
        self.assertIn(" O ", rendered)
        self.assertIn(" X ", rendered)
        self.assertIn(" - ", rendered)
        self.assertIn(" S ", rendered)
        self.assertIn(" @ ", rendered)

    def test_cnf_states_use_their_configured_colors(self):
        rendered = render_records(
            [
                {"IP": "1.1.1.1", "cnf": "O"},
                {"IP": "1.1.1.2", "cnf": "X"},
                {"IP": "1.1.1.3", "cnf": "-"},
                {"IP": "1.1.1.4", "cnf": "S"},
                {"IP": "1.1.1.5", "cnf": "@"},
            ],
            "table",
            color=True,
        )
        self.assertIn(Fore.LIGHTGREEN_EX + " O ", rendered)
        self.assertIn(Fore.LIGHTRED_EX + " X ", rendered)
        self.assertIn(Fore.LIGHTYELLOW_EX + " - ", rendered)
        self.assertIn(Fore.LIGHTCYAN_EX + " S ", rendered)
        self.assertIn(Fore.LIGHTMAGENTA_EX + " @ ", rendered)

    def test_colored_table_uses_colorama_codes(self):
        rendered = render_records(
            [{"IP": "192.168.1.1", "ALIAS": "GATEWAY", "MAC": "", "NAME": ""}],
            "table",
            color=True,
        )
        self.assertIn(Fore.CYAN, rendered)
        self.assertIn(Fore.LIGHTYELLOW_EX, rendered)
        self.assertIn(Fore.LIGHTMAGENTA_EX, rendered)
        self.assertIn(Fore.LIGHTGREEN_EX, rendered)

    def test_difference_table_uses_requested_cell_colors(self):
        rendered = render_records(
            [
                {
                    "IP": "192.168.1.2",
                    "cnf": False,
                    "ALIAS": "NAS",
                    "MAC": "AA:BB:CC:DD:EE:FF",
                    "NAME": "Servidor",
                }
            ],
            "table",
            color=True,
            cell_colors=[
                {
                    "IP": "red",
                    "MAC": "blue",
                    "cnf": "white",
                    "ALIAS": "white",
                    "NAME": "white",
                }
            ],
        )
        self.assertIn(Fore.RED + "192.168.1.2", rendered)
        self.assertIn(Fore.BLUE + "AA:BB:CC:DD:EE:FF", rendered)
        self.assertIn(Fore.WHITE + "NAS", rendered)


class DeviceModelTests(unittest.TestCase):
    def test_new_fields_have_safe_defaults(self):
        device = Device(ip="192.168.1.20")
        self.assertEqual(device.cnf, "X")
        self.assertEqual(device.description, "-")
        self.assertEqual(device.groups, [])
        self.assertEqual(device.manufacturer, "")

    def test_cnf_normalizes_legacy_and_named_states(self):
        self.assertEqual(normalize_cnf(True), "O")
        self.assertEqual(normalize_cnf(False), "X")
        self.assertEqual(normalize_cnf("OK"), "O")
        self.assertEqual(normalize_cnf("UNKNOWN"), "X")
        self.assertEqual(normalize_cnf("UNRECOGNIZED"), "-")
        self.assertEqual(normalize_cnf("MARKED"), "S")
        with self.assertRaises(ValueError):
            normalize_cnf("otro")

    def test_private_mac_has_explanatory_manufacturer(self):
        self.assertEqual(
            detect_manufacturer("92:0E:76:02:39:B2"),
            "MAC privada/aleatoria",
        )

    def test_device_description_limit(self):
        with self.assertRaises(ValueError):
            Device(ip="192.168.1.20", description="x" * 43)

    def test_mac_with_hyphens_is_normalized(self):
        self.assertEqual(
            normalize_mac("2c-f0-5d-34-12-19"),
            "2C:F0:5D:34:12:19",
        )
        self.assertEqual(
            Device(ip="-", mac="2c-f0-5d-34-12-19").mac,
            "2C:F0:5D:34:12:19",
        )

    def test_invalid_mac_characters_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_mac("2C-F0-5D-34-12-ZZ")


class NetworkTests(unittest.TestCase):
    def test_list_filters_are_combinable(self):
        devices = [
            Device(
                ip="192.168.1.20",
                cnf="O",
                mac="00:11:22:33:44:55",
                groups=["IOT"],
            ),
            Device(
                ip="192.168.1.21",
                cnf="X",
                mac="00:11:22:33:44:66",
                groups=["IOT"],
            ),
            Device(
                ip="192.168.1.254",
                cnf="O",
                mac="00:11:22:33:44:77",
                groups=["GESTOR"],
            ),
        ]
        args = SimpleNamespace(
            connected=True,
            disconnected=False,
            cnf_state="O",
            group="iot",
            dhcp_only=True,
            dhcp_range="192.168.1.16-192.168.1.192",
        )
        selected = filter_rows(devices, [True, True, True], args)
        self.assertEqual([device.ip for device, _ in selected], ["192.168.1.20"])

    def test_ip_range_ignores_devices_without_ip(self):
        self.assertTrue(
            ip_in_range(
                "192.168.1.42",
                "192.168.1.16-192.168.1.192",
            )
        )
        self.assertFalse(
            ip_in_range("-", "192.168.1.16-192.168.1.192")
        )

    def test_dhcp_range_is_normalized_and_validated(self):
        self.assertEqual(
            normalize_dhcp_range("192.168.1.20 - 192.168.1.200"),
            "192.168.1.20-192.168.1.200",
        )
        self.assertIsNone(normalize_dhcp_range("off"))
        with self.assertRaises(ValueError):
            normalize_dhcp_range("192.168.1.200-192.168.1.20")

    def test_activity_is_matched_by_mac_not_stale_ip(self):
        devices = [
            Device(ip="192.168.1.10", mac="AA:AA:AA:AA:AA:AA"),
            Device(ip="192.168.1.10", mac="BB:BB:BB:BB:BB:BB"),
        ]
        records = [
            Device(ip="192.168.1.10", mac="BB:BB:BB:BB:BB:BB"),
        ]
        self.assertEqual(active_flags(devices, records), [False, True])

    def test_host_address_is_normalized_to_network(self):
        self.assertEqual(
            resolve_network("192.168.5.20/24"),
            ipaddress.IPv4Network("192.168.5.0/24"),
        )

    def test_ipv6_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_network("2001:db8::/64")

    def test_stale_arp_entry_is_not_considered_active(self):
        scanner = LanScanner(
            ipaddress.IPv4Network("192.168.1.0/29"),
            workers=2,
            timeout=0.1,
            max_hosts=16,
        )
        with (
            patch.object(
                scanner,
                "_ping",
                side_effect=lambda ip: ip == "192.168.1.3",
            ),
            patch.object(
                scanner,
                "_read_arp_table",
                return_value={
                    "192.168.1.2": "AA:AA:AA:AA:AA:AA",
                    "192.168.1.3": "BB:BB:BB:BB:BB:BB",
                },
            ),
            patch.object(scanner, "_local_mac", return_value="CC:CC:CC:CC:CC:CC"),
            patch.object(scanner, "_resolve_name", return_value=""),
            patch(
                "app.services.lan_scanner.local_ipv4",
                return_value=ipaddress.IPv4Address("192.168.1.6"),
            ),
        ):
            records = scanner.scan()

        ips = {device.ip for device in records}
        self.assertNotIn("192.168.1.2", ips)
        self.assertIn("192.168.1.3", ips)

    def test_active_arp_discovers_device_that_blocks_ping(self):
        scanner = LanScanner(
            ipaddress.IPv4Network("192.168.1.40/29"),
            workers=2,
            timeout=0.1,
            max_hosts=16,
        )
        target_mac = "DE:AD:BE:EF:FE:ED"
        with (
            patch.object(scanner, "_ping", return_value=False),
            patch.object(scanner, "_read_arp_table", return_value={}),
            patch.object(scanner, "_local_mac", return_value=""),
            patch.object(scanner, "_resolve_name", return_value=""),
            patch(
                "app.services.lan_scanner.active_arp_mac",
                side_effect=lambda ip, _timeout: (
                    target_mac if ip == "192.168.1.44" else ""
                ),
            ),
            patch(
                "app.services.lan_scanner.local_ipv4",
                return_value=ipaddress.IPv4Address("192.168.1.46"),
            ),
        ):
            records = scanner.scan(discovery="hybrid")

        target = next(record for record in records if record.ip == "192.168.1.44")
        self.assertEqual(target.mac, target_mac)
        self.assertEqual(scanner.discovery_for(target), "ARP")

    def test_first_icmp_and_arp_probes_share_the_bounded_pool(self):
        scanner = LanScanner(
            ipaddress.IPv4Network("192.168.1.0/30"),
            workers=2,
            timeout=0.1,
            max_hosts=4,
        )
        rendezvous = threading.Barrier(2)

        def ping(_ip):
            rendezvous.wait(timeout=1)
            return True

        def arp(_ip, _timeout):
            rendezvous.wait(timeout=1)
            return "DE:AD:BE:EF:FE:ED"

        with (
            patch.object(scanner, "_ping", side_effect=ping),
            patch("app.services.lan_scanner.active_arp_mac", side_effect=arp),
        ):
            alive, macs = scanner._parallel_discovery(
                ["192.168.1.1"], use_icmp=True, use_arp=True
            )

        self.assertEqual(alive, {"192.168.1.1"})
        self.assertEqual(macs, {"192.168.1.1": "DE:AD:BE:EF:FE:ED"})
        device = Device(ip="192.168.1.1", mac="DE:AD:BE:EF:FE:ED")
        self.assertIsNotNone(scanner.response_time_for(device))
        self.assertNotIn("responseMs", device.to_dict())

    def test_runtime_response_ms_can_be_rendered_without_device_storage(self):
        rendered = render_records(
            [{"IP": "192.168.1.1", "responseMs": 12.345}],
            "table",
            columns=["ip", "ms"],
        )
        self.assertIn("ms", rendered.splitlines()[0])
        self.assertIn("12.3", rendered)

    def test_discovery_mode_is_validated(self):
        scanner = LanScanner(
            ipaddress.IPv4Network("192.168.1.0/30"),
            workers=1,
            timeout=0.1,
            max_hosts=4,
        )
        with self.assertRaises(ValueError):
            scanner.scan(discovery="inventado")

    def test_arp_cache_can_be_imported_without_marking_device_active(self):
        scanner = LanScanner(
            ipaddress.IPv4Network("192.168.1.40/29"),
            workers=2,
            timeout=0.1,
            max_hosts=16,
        )
        with (
            patch.object(scanner, "_ping", return_value=False),
            patch.object(
                scanner,
                "_read_arp_table",
                return_value={"192.168.1.44": "DE:AD:BE:EF:FE:ED"},
            ),
            patch.object(scanner, "_local_mac", return_value=""),
            patch.object(scanner, "_resolve_name", return_value=""),
            patch(
                "app.services.lan_scanner.local_ipv4",
                return_value=ipaddress.IPv4Address("192.168.1.46"),
            ),
        ):
            records = scanner.scan(
                discovery="icmp", include_arp_cache=True
            )

        target = next(record for record in records if record.ip == "192.168.1.44")
        self.assertEqual(scanner.discovery_for(target), "CACHE")
        self.assertFalse(scanner.is_confirmed(target))


class DatabaseTests(unittest.TestCase):
    def test_inventory_audit_describes_changes_and_hides_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "devices.json"
            database = DeviceDatabase(str(path))
            before = Device(
                ip="192.168.1.10", mac="10:20:30:40:50:60", alias="OLD",
                credentials={"ssh": "credential-1"},
            )
            after = before.copy()
            after.alias = "NEW"
            after.credentials = {"ssh": "credential-2"}
            with (
                patch("app.core.database.load_config", return_value={"database": str(path)}),
                patch("app.core.database.write_database_log") as audit,
            ):
                database._audit_changes([before], [after])

            message = audit.call_args.args[0]
            self.assertIn('ALIAS:"OLD"=>"NEW"', message)
            self.assertIn("credentials:[OCULTO]=>[OCULTO]", message)
            self.assertNotIn("credential-1", message)
            self.assertNotIn("credential-2", message)

    def test_detection_history_accumulates_and_updates_last_seen(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert([
                {
                    "IP": "192.168.1.44", "MAC": "DE:AD:BE:EF:FE:ED",
                    "discoveryMethods": ["ARP"], "lastDiscovery": "ARP",
                    "lastSeen": "2026-07-25T20:00:00+02:00",
                }
            ])
            updated = database.record_detection(
                "DE:AD:BE:EF:FE:ED", ["PING"],
                seen_at="2026-07-25T21:00:00+02:00",
            )
            self.assertEqual(updated.discovery_methods, ["ARP", "PING"])
            self.assertEqual(updated.last_discovery, "PING")
            self.assertEqual(updated.last_seen, "2026-07-25T21:00:00+02:00")

    def test_rescan_without_detection_metadata_preserves_history(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert([
                {
                    "IP": "192.168.1.44", "MAC": "DE:AD:BE:EF:FE:ED",
                    "discoveryMethods": ["ARP"], "lastDiscovery": "ARP",
                    "lastSeen": "2026-07-25T20:00:00+02:00",
                }
            ])
            device = database.upsert([
                {"IP": "192.168.1.44", "MAC": "DE:AD:BE:EF:FE:ED"}
            ])[0]
            self.assertEqual(device.discovery_methods, ["ARP"])
            self.assertEqual(device.last_discovery, "ARP")

    def test_search_finds_alias_name_ip_and_mac(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [
                    {
                        "IP": "192.168.1.11",
                        "MAC": "24:5E:BE:65:C0:EC",
                        "ALIAS": "NAS",
                        "NAME": "HomeNAS",
                        "defaultName": "HomeNAS",
                    }
                ]
            )
            for selector in (
                "nas",
                "homenas",
                "192.168.1.11",
                "24-5e-be-65-c0-ec",
            ):
                self.assertEqual(database.search(selector)[0].alias, "NAS")

    def test_search_returns_duplicate_names_and_rejects_missing_value(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [
                    {
                        "IP": "192.168.1.10",
                        "MAC": "00:11:22:33:44:55",
                        "NAME": "Echo",
                        "defaultName": "Echo",
                    },
                    {
                        "IP": "192.168.1.20",
                        "MAC": "00:11:22:33:44:66",
                        "NAME": "Echo",
                        "defaultName": "Echo",
                    },
                ]
            )
            self.assertEqual(len(database.search("echo")), 2)
            with self.assertRaises(ValueError):
                database.search("inexistente")

    def test_scan_differences_detect_ip_change_by_mac(self):
        saved = [
            Device(
                ip="192.168.1.10",
                mac="AA:BB:CC:DD:EE:FF",
                name="NAS",
            )
        ]
        records = [{"IP": "192.168.1.20", "MAC": "AA:BB:CC:DD:EE:FF"}]
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.save_devices(saved)
            result = compare_scan(records, saved, database.preview(records))

        self.assertEqual(result.ip_changes, 1)
        self.assertEqual(result.mac_conflicts, 0)
        self.assertEqual(result.colors[0]["IP"], "red")
        self.assertEqual(result.colors[0]["MAC"], "blue")

    def test_scan_differences_detect_mac_conflict_at_saved_ip(self):
        saved = [
            Device(ip="192.168.1.10", mac="AA:BB:CC:DD:EE:FF")
        ]
        records = [{"IP": "192.168.1.10", "MAC": "11:22:33:44:55:66"}]
        result = compare_scan(
            records,
            saved,
            [Device(ip="192.168.1.10", mac="11:22:33:44:55:66")],
        )

        self.assertEqual(result.mac_conflicts, 1)
        self.assertEqual(result.colors[0]["IP"], "blue")
        self.assertEqual(result.colors[0]["MAC"], "red")

    def test_new_mac_on_used_ip_is_added_without_erasing_old_mac(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [{"IP": "192.168.1.10", "MAC": "AA:BB:CC:DD:EE:FF"}]
            )
            devices = database.upsert(
                [{"IP": "192.168.1.10", "MAC": "11:22:33:44:55:66"}]
            )
            self.assertEqual(len(devices), 2)
            self.assertEqual(
                {device.mac for device in devices},
                {"AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"},
            )

    def test_add_device_requires_only_mac(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            device = database.add_device("2C-F0-5D-34-12-19")
            self.assertEqual(device.ip, "-")
            self.assertEqual(device.mac, "2C:F0:5D:34:12:19")
            self.assertEqual(device.description, "-")

    def test_editing_name_or_alias_confirms_device(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [{"IP": "192.168.1.20", "MAC": "10:20:30:40:50:60"}]
            )
            named = database.set_name("10:20:30:40:50:60", "Sensor")
            self.assertEqual(named.cnf, "O")
            database.edit_device("10:20:30:40:50:60", "cnf", "X")
            aliased = database.set_alias("10:20:30:40:50:60", "SENSOR")
            self.assertEqual(aliased.cnf, "O")

    def test_upsert_preserves_and_updates_devices(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert([{"IP": "192.168.1.2", "MAC": "AA:AA:AA:AA:AA:AA"}])
            devices = database.upsert(
                [
                    {"IP": "192.168.1.2", "MAC": "BB:BB:BB:BB:BB:BB"},
                    {"IP": "192.168.1.3", "MAC": "CC:CC:CC:CC:CC:CC"},
                ]
            )
            self.assertEqual(len(devices), 3)
            self.assertEqual(
                {device["MAC"] for device in devices},
                {
                    "AA:AA:AA:AA:AA:AA",
                    "BB:BB:BB:BB:BB:BB",
                    "CC:CC:CC:CC:CC:CC",
                },
            )
            self.assertIn("defaultAlias", devices[0])
            self.assertIn("nameDeleted", devices[0])

    def test_empty_mac_does_not_erase_known_mac(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert([{"IP": "192.168.1.2", "MAC": "AA:AA:AA:AA:AA:AA"}])
            devices = database.upsert([{"IP": "192.168.1.2", "MAC": ""}])
            self.assertEqual(devices[0]["MAC"], "AA:AA:AA:AA:AA:AA")

    def test_empty_scan_manufacturer_preserves_known_value(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [
                    {
                        "IP": "192.168.1.20",
                        "MAC": "00:11:22:33:44:55",
                        "manufacturer": "Fabricante guardado",
                    }
                ]
            )
            devices = database.upsert(
                [{"IP": "192.168.1.20", "MAC": "00:11:22:33:44:55"}]
            )
            self.assertEqual(devices[0]["manufacturer"], "Fabricante guardado")

    def test_old_database_is_migrated_and_custom_alias_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "devices.json"
            path.write_text(
                '[{"IP": "192.168.1.2", "MAC": "AA:AA:AA:AA:AA:AA"}]',
                encoding="utf-8",
            )
            database = DeviceDatabase(str(path))
            migrated = database.upsert(
                [
                    {
                        "IP": "192.168.1.2",
                        "ALIAS": "PC",
                        "MAC": "",
                        "NAME": "",
                        "defaultName": "desk",
                    }
                ]
            )
            self.assertEqual(migrated[0]["ALIAS"], "PC")
            self.assertEqual(migrated[0]["NAME"], "desk")
            self.assertEqual(migrated[0]["defaultName"], "desk")

    def test_user_name_is_never_overwritten_by_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "devices.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "IP": "192.168.1.2",
                            "ALIAS": "",
                            "MAC": "AA:AA:AA:AA:AA:AA",
                            "NAME": "Servidor de casa",
                            "defaultName": "old-host",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            devices = DeviceDatabase(str(path)).upsert(
                [
                    {
                        "IP": "192.168.1.2",
                        "MAC": "AA:AA:AA:AA:AA:AA",
                        "defaultName": "new-host",
                    }
                ]
            )
            self.assertEqual(devices[0]["NAME"], "Servidor de casa")
            self.assertEqual(devices[0]["defaultName"], "new-host")

    def test_default_name_initializes_name_only_once(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            first = database.upsert(
                [
                    {
                        "IP": "192.168.1.4",
                        "MAC": "11:22:33:44:55:66",
                        "defaultName": "first-host",
                    }
                ]
            )
            self.assertEqual(first[0]["NAME"], "first-host")

            second = database.upsert(
                [
                    {
                        "IP": "192.168.1.4",
                        "MAC": "11:22:33:44:55:66",
                        "defaultName": "renamed-host",
                    }
                ]
            )
            self.assertEqual(second[0]["NAME"], "first-host")
            self.assertEqual(second[0]["defaultName"], "renamed-host")

    def test_name_follows_mac_when_ip_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [
                    {
                        "IP": "192.168.1.20",
                        "MAC": "AA:BB:CC:DD:EE:FF",
                        "NAME": "",
                    }
                ]
            )
            database.set_name("aa-bb-cc-dd-ee-ff", "Impresora")
            devices = database.upsert(
                [
                    {
                        "IP": "192.168.1.80",
                        "MAC": "AA:BB:CC:DD:EE:FF",
                        "defaultName": "printer",
                    }
                ]
            )
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]["IP"], "192.168.1.80")
            self.assertEqual(devices[0]["NAME"], "Impresora")

    def test_delete_and_default_modes_for_name_and_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [
                    {
                        "IP": "192.168.1.1",
                        "ALIAS": "AUTO",
                        "defaultAlias": "AUTO",
                        "MAC": "AA:BB:CC:DD:EE:FF",
                        "defaultName": "router",
                    }
                ]
            )
            database.set_value("AUTO", "NAME", "delete")
            deleted = database.set_value("AUTO", "ALIAS", "delete")
            self.assertEqual(deleted["NAME"], "")
            self.assertEqual(deleted["ALIAS"], "")

            database.set_value("AA:BB:CC:DD:EE:FF", "NAME", "default")
            restored = database.set_value(
                "AA:BB:CC:DD:EE:FF", "ALIAS", "default"
            )
            self.assertEqual(restored["NAME"], "router")
            self.assertEqual(restored["ALIAS"], "AUTO")

    def test_alias_call_resolves_ip_and_mac(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [
                    {
                        "IP": "192.168.1.50",
                        "ALIAS": "CAMARA",
                        "MAC": "10:20:30:40:50:60",
                    }
                ]
            )
            device = database.resolve("camara")
            self.assertEqual(device["IP"], "192.168.1.50")
            self.assertEqual(device["MAC"], "10:20:30:40:50:60")

    def test_aliases_must_be_unique(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [
                    {"IP": "192.168.1.2", "MAC": "10:20:30:40:50:60"},
                    {"IP": "192.168.1.3", "MAC": "AA:BB:CC:DD:EE:FF"},
                ]
            )
            database.set_alias("192.168.1.2", "EQUIPO")
            with self.assertRaises(ValueError):
                database.set_alias("192.168.1.3", "equipo")

    def test_gateway_and_broadcast_aliases_are_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [
                    {
                        "IP": "192.168.1.1",
                        "ALIAS": "GATEWAY",
                        "defaultAlias": "GATEWAY",
                        "MAC": "10:20:30:40:50:60",
                    },
                    {
                        "IP": "192.168.1.255",
                        "ALIAS": "BRODCAST",
                        "defaultAlias": "BRODCAST",
                        "MAC": "FF:FF:FF:FF:FF:FF",
                    },
                ]
            )
            with self.assertRaises(ValueError):
                database.set_value("GATEWAY", "ALIAS", "value", "ROUTER")
            with self.assertRaises(ValueError):
                database.set_value("BRODCAST", "ALIAS", "delete")

    def test_ip_change_preserves_user_alias_by_mac(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            database.upsert(
                [{"IP": "192.168.1.20", "MAC": "10:20:30:40:50:60"}]
            )
            database.set_alias("10:20:30:40:50:60", "CAMARA")
            devices = database.upsert(
                [{"IP": "192.168.1.90", "MAC": "10:20:30:40:50:60"}]
            )
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]["IP"], "192.168.1.90")
            self.assertEqual(devices[0]["ALIAS"], "CAMARA")


class LoggerTests(unittest.TestCase):
    def test_program_and_database_logs_use_independent_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program = write_log("programa", root / "program")
            database = write_database_log("cambio", root / "database")

            self.assertEqual(program.parent.name, "program")
            self.assertEqual(database.parent.name, "database")
            self.assertIn("programa", program.read_text(encoding="utf-8"))
            self.assertIn("cambio", database.read_text(encoding="utf-8"))

    def test_log_uses_daily_file_and_one_timestamped_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_log("primera línea\nsegunda línea", Path(directory))
            self.assertRegex(path.name, r"^\d{2}-\d{2}-\d{4}\.log$")
            content = path.read_text(encoding="utf-8")
            self.assertRegex(
                content,
                r"^\d{2}:\d{2}:\d{2} primera línea \| segunda línea\n$",
            )


    def test_cleanup_removes_only_recognized_logs_older_than_retention(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_log = root / "01-01-2026.log"
            boundary_log = root / "10-01-2026.log"
            current_log = root / "20-01-2026.log"
            unknown_log = root / "aplicacion.log"
            for path in (old_log, boundary_log, current_log, unknown_log):
                path.write_text("test\n", encoding="utf-8")

            deleted = cleanup_old_logs(
                root, 10, today=date(2026, 1, 20)
            )

            self.assertEqual(deleted, (old_log.resolve(),))
            self.assertFalse(old_log.exists())
            self.assertTrue(boundary_log.exists())
            self.assertTrue(current_log.exists())
            self.assertTrue(unknown_log.exists())

    def test_cleanup_rejects_invalid_retention(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                cleanup_old_logs(directory, 0)


class GroupTests(unittest.TestCase):
    def test_group_output_supports_colorama(self):
        self.assertIn(Fore.CYAN, _paint("GROUP", Fore.CYAN, True))
        self.assertEqual(_paint("GROUP", Fore.CYAN, False), "GROUP")

    def test_group_membership_is_stored_on_both_sides(self):
        with tempfile.TemporaryDirectory() as directory:
            devices = DeviceDatabase(str(Path(directory) / "devices.json"))
            devices.upsert(
                [{"IP": "192.168.1.20", "MAC": "10:20:30:40:50:60"}]
            )
            groups = GroupDatabase(str(Path(directory) / "groups.json"), devices)
            groups.create("cameras")
            group, device = groups.add("CAMERAS", "192.168.1.20")
            self.assertIn(device.mac, group.members)
            self.assertIn("CAMERAS", device.groups)

    def test_delete_device_removes_inventory_and_every_group_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            devices = DeviceDatabase(str(Path(directory) / "devices.json"))
            devices.upsert(
                [{"IP": "192.168.1.18", "MAC": "10:20:30:40:50:60"}]
            )
            groups = GroupDatabase(str(Path(directory) / "groups.json"), devices)
            groups.create("IOT")
            groups.add("IOT", "10:20:30:40:50:60")

            deleted = groups.delete_device("192.168.1.18")

            self.assertEqual(deleted.mac, "10:20:30:40:50:60")
            self.assertEqual(devices.load(), [])
            self.assertNotIn("10:20:30:40:50:60", groups.load()[1].members)

    def test_reserved_devices_cannot_be_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            devices = DeviceDatabase(str(Path(directory) / "devices.json"))
            devices.upsert(
                [{
                    "IP": "192.168.1.1",
                    "MAC": "10:20:30:40:50:60",
                    "ALIAS": "GATEWAY",
                    "defaultAlias": "GATEWAY",
                }]
            )
            groups = GroupDatabase(str(Path(directory) / "groups.json"), devices)
            with self.assertRaises(ValueError):
                groups.delete_device("GATEWAY")

    def test_group_description_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            devices = DeviceDatabase(str(Path(directory) / "devices.json"))
            groups = GroupDatabase(str(Path(directory) / "groups.json"), devices)
            groups.create("TEST")
            with self.assertRaises(ValueError):
                groups.set_description("TEST", "x" * 43)

    def test_basic_group_is_created_for_reserved_devices(self):
        with tempfile.TemporaryDirectory() as directory:
            devices = DeviceDatabase(str(Path(directory) / "devices.json"))
            stored = devices.upsert(
                [
                    {
                        "IP": "192.168.1.1",
                        "ALIAS": "GATEWAY",
                        "defaultAlias": "GATEWAY",
                        "MAC": "10:20:30:40:50:60",
                    }
                ]
            )
            groups = GroupDatabase(str(Path(directory) / "groups.json"), devices)
            basic = groups.ensure_basic(stored)[0]
            self.assertEqual(basic.name, "BASIC")
            self.assertFalse(basic.editable)
            self.assertIn("10:20:30:40:50:60", basic.members)

    def test_non_editable_group_rejects_every_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            devices = DeviceDatabase(str(Path(directory) / "devices.json"))
            stored = devices.upsert(
                [
                    {
                        "IP": "192.168.1.1",
                        "ALIAS": "GATEWAY",
                        "defaultAlias": "GATEWAY",
                        "MAC": "10:20:30:40:50:60",
                    }
                ]
            )
            groups = GroupDatabase(str(Path(directory) / "groups.json"), devices)
            groups.ensure_basic(stored)
            with self.assertRaises(ValueError):
                groups.delete("BASIC")
            with self.assertRaises(ValueError):
                groups.rename("BASIC", "OTHER")
            with self.assertRaises(ValueError):
                groups.set_description("BASIC", "Otra")
            with self.assertRaises(ValueError):
                groups.remove("BASIC", "GATEWAY")


class LegacySshTests(unittest.TestCase):
    def test_legacy_algorithms_are_scoped_to_openssh_process(self):
        profile = SshProfile.from_options(
            {
                "port": 22,
                "driver": "cisco_s300",
                "hostKeyAlgorithms": ["ssh-rsa"],
                "kexAlgorithms": ["diffie-hellman-group14-sha1"],
            }
        )
        arguments = profile.openssh_arguments("192.168.1.37", "admin")
        self.assertIn("-oHostKeyAlgorithms=+ssh-rsa", arguments)
        self.assertIn("-oKexAlgorithms=+diffie-hellman-group14-sha1", arguments)
        self.assertEqual(arguments[-1], "admin@192.168.1.37")

    def test_automated_ssh_rejects_configuration_commands(self):
        profile = SshProfile(driver="cisco_s300")
        with self.assertRaises(ValueError):
            run_show_command(
                "192.168.1.37",
                "admin",
                "not-used",
                profile,
                "configure terminal",
                connector=lambda **kwargs: None,
            )

    def test_esp32_rack_profile_uses_modern_ssh(self):
        profile_options = SSH_PROFILES["ssh_esp32_rack_monitor"]
        profile = SshProfile.from_options(profile_options)
        self.assertEqual(profile.port, 22)
        self.assertEqual(profile.host_key_algorithms, ())
        self.assertEqual(profile.kex_algorithms, ())
        self.assertEqual(profile_options["terminalAdapter"], "esp32_rack_monitor")


class TerminalTests(unittest.TestCase):
    def test_terminal_is_selected_from_device_protocols(self):
        ssh = Device(ip="192.168.1.2", mac="10:20:30:40:50:60", protocols=["ssh"])
        tr064 = Device(ip="192.168.1.1", mac="10:20:30:40:50:61", protocols=["tr-064"])
        self.assertEqual(choose_terminal(ssh, None), "ssh")
        self.assertEqual(choose_terminal(tr064, None), "tr-064")

    def test_terminal_can_request_native_ssh_fallback(self):
        args = build_parser().parse_args([
            "terminal", "SW", "--native"
        ])
        self.assertTrue(args.native)

    def test_tr064_terminal_rejects_write_actions(self):
        self.assertEqual(
            parse_call(["call", "LANHostConfigManagement", "GetInfo"]),
            ("LANHostConfigManagement", "GetInfo", {}),
        )
        with self.assertRaises(ValueError):
            parse_call(["call", "WLANConfiguration", "SetEnable", "NewEnable=0"])


class VersionTests(unittest.TestCase):
    def test_package_and_cli_versions_match(self):
        project = (Path(__file__).parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        declared = next(
            line for line in project.splitlines() if line.startswith("version = ")
        ).split('"', 2)[1]
        self.assertEqual(declared, __version__)


if __name__ == "__main__":
    unittest.main()
