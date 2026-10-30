import ctypes
import ipaddress
import json
import socket
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from lanctl.apps.ip.infrastructure.services import lan_scanner, source_binding
from lanctl.core import network_interfaces

NIC = {
    "id": "7:10.20.1.2",
    "name": "Ethernet test",
    "index": 7,
    "address": "10.20.1.2",
    "prefixLength": 22,
    "network": "10.20.0.0/22",
}


@pytest.mark.parametrize(
    "system,document",
    [
        ("Windows", {"name": NIC["name"], "index": 7, "address": NIC["address"], "prefix": 22}),
        (
            "Linux",
            [
                {
                    "ifname": NIC["name"],
                    "ifindex": 7,
                    "addr_info": [
                        {"family": "inet", "local": NIC["address"], "prefixlen": 22},
                        {"family": "inet6", "local": "fe80::1", "prefixlen": 64},
                    ],
                }
            ],
        ),
    ],
)
def test_enumeration_uses_real_mask_and_does_not_probe(monkeypatch, system, document):
    monkeypatch.setattr(network_interfaces.platform, "system", lambda: system)
    # Simulate the complete Windows subprocess API when this test runs on Linux.
    if system == "Windows":
        monkeypatch.setattr(
            network_interfaces.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False
        )
    run = Mock(return_value=SimpleNamespace(stdout=json.dumps(document)))
    monkeypatch.setattr(network_interfaces.subprocess, "run", run)
    assert network_interfaces.ipv4_interfaces() == [NIC]
    command = run.call_args.args[0]
    assert command[0] in ("ip", "powershell.exe")
    assert not run.call_args.kwargs.get("shell")
    assert run.call_args.kwargs["timeout"] == 10
    assert run.call_args.kwargs["creationflags"] == (0x08000000 if system == "Windows" else 0)


@pytest.mark.parametrize(
    "document",
    [
        None,
        [1],
        [{"name": "eth0"}],
        {"name": "x", "index": True, "address": "1.2.3.4", "prefix": 24},
    ],
)
def test_malformed_inventory_rejected_without_default_route(monkeypatch, document):
    monkeypatch.setattr(network_interfaces.platform, "system", lambda: "Windows")
    monkeypatch.setattr(network_interfaces, "_read", lambda command: document)
    with pytest.raises(ValueError):
        network_interfaces.ipv4_interfaces()


def test_selection_rejects_disappeared_ambiguous_and_outside_network(monkeypatch):
    monkeypatch.setattr(network_interfaces, "ipv4_interfaces", lambda: [NIC])
    assert network_interfaces.select_interface(NIC["id"], "10.20.2.0/24") == NIC
    with pytest.raises(ValueError):
        lan_scanner.LanScanner(
            ipaddress.IPv4Network(NIC["network"]), 1, 0.1, 4096, source_address=""
        )
    with pytest.raises(ValueError, match="pertenecer"):
        network_interfaces.select_interface(NIC["id"], "10.0.0.0/8")
    with pytest.raises(ValueError, match="disponible"):
        network_interfaces.select_interface("8:10.20.1.2")
    monkeypatch.setattr(
        network_interfaces,
        "ipv4_interfaces",
        lambda: [NIC, {**NIC, "id": "8:10.20.1.2", "index": 8}],
    )
    with pytest.raises(ValueError, match="varias interfaces"):
        network_interfaces.select_interface(NIC["id"])


def test_interface_removed_before_scan_starts_no_probe(monkeypatch):
    monkeypatch.setattr(network_interfaces, "ipv4_interfaces", lambda: [NIC])
    scanner = lan_scanner.LanScanner(
        ipaddress.IPv4Network(NIC["network"]),
        workers=1,
        timeout=0.1,
        max_hosts=4096,
        source_address=NIC["id"],
    )
    probe = Mock(side_effect=AssertionError("must not probe"))
    monkeypatch.setattr(scanner, "_parallel_discovery", probe)
    monkeypatch.setattr(network_interfaces, "ipv4_interfaces", list)
    with pytest.raises(ValueError, match="disponible"):
        scanner.scan()
    probe.assert_not_called()


def test_linux_ping_and_arp_preserve_source_and_adapter(monkeypatch):
    monkeypatch.setattr(network_interfaces, "ipv4_interfaces", lambda: [NIC])
    monkeypatch.setattr(lan_scanner.platform, "system", lambda: "Linux")
    scanner = lan_scanner.LanScanner(
        ipaddress.IPv4Network(NIC["network"]),
        workers=1,
        timeout=0.1,
        max_hosts=4096,
        source_address=NIC["id"],
    )
    run = Mock(
        return_value=SimpleNamespace(returncode=0, stdout="10.20.1.9 lladdr AA:BB:CC:DD:EE:FF")
    )
    monkeypatch.setattr(lan_scanner.subprocess, "run", run)
    assert scanner._ping("10.20.1.9")
    command = run.call_args.args[0]
    assert command[-6:] == ["-I", NIC["name"], "-I", NIC["address"], "-n", "10.20.1.9"]
    assert scanner._arp("10.20.1.9") == "AA:BB:CC:DD:EE:FF"
    command = run.call_args.args[0]
    assert command[-5:] == ["-I", NIC["name"], "-s", NIC["address"], "10.20.1.9"]
    assert scanner._read_arp_table() == {"10.20.1.9": "AA:BB:CC:DD:EE:FF"}
    assert run.call_args.args[0] == ["ip", "-4", "neigh", "show", "dev", NIC["name"]]


def test_windows_icmp_uses_native_source_not_unsupported_ping_switch(monkeypatch):
    native = SimpleNamespace(
        IcmpCreateFile=Mock(return_value=123),
        IcmpCloseHandle=Mock(),
        IcmpSendEcho2Ex=Mock(return_value=1),
    )
    monkeypatch.setattr(ctypes, "WinDLL", Mock(return_value=native), raising=False)
    assert source_binding.windows_ping(NIC["address"], "10.20.1.9", 0.5)
    args = native.IcmpSendEcho2Ex.call_args.args
    assert args[4] == int.from_bytes(socket.inet_aton(NIC["address"]), "little")
    assert args[5] == int.from_bytes(socket.inet_aton("10.20.1.9"), "little")
    assert args[-1] == 500
    native.IcmpCloseHandle.assert_called_once_with(123)


def test_windows_icmp_source_failure_closes_handle_without_fallback(monkeypatch):
    native = SimpleNamespace(
        IcmpCreateFile=Mock(return_value=123),
        IcmpCloseHandle=Mock(),
        IcmpSendEcho2Ex=Mock(return_value=0),
    )
    monkeypatch.setattr(ctypes, "WinDLL", Mock(return_value=native), raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: 87, raising=False)
    with pytest.raises(OSError, match="interfaz"):
        source_binding.windows_ping(NIC["address"], "10.20.1.9", 0.5)
    native.IcmpCloseHandle.assert_called_once_with(123)


def test_windows_arp_passes_selected_source(monkeypatch):
    monkeypatch.setattr(lan_scanner.platform, "system", lambda: "Windows")
    address = Mock(
        side_effect=lambda value: int.from_bytes(socket.inet_aton(value.decode()), "little")
    )
    send = Mock(return_value=0)
    dlls = SimpleNamespace(
        ws2_32=SimpleNamespace(inet_addr=address), iphlpapi=SimpleNamespace(SendARP=send)
    )
    monkeypatch.setattr(ctypes, "windll", dlls, raising=False)
    lan_scanner.active_arp_mac("10.20.1.9", source_address=NIC["address"])
    assert send.call_args.args[1] == int.from_bytes(socket.inet_aton(NIC["address"]), "little")


def test_bound_scan_omits_unbound_services_and_name_resolution(monkeypatch):
    monkeypatch.setattr(network_interfaces, "ipv4_interfaces", lambda: [NIC])
    scanner = lan_scanner.LanScanner(
        ipaddress.IPv4Network("10.20.1.0/30"),
        workers=1,
        timeout=0.1,
        max_hosts=4096,
        source_address=NIC["id"],
    )
    monkeypatch.setattr(scanner, "_parallel_discovery", lambda *a: (set(), {}))
    monkeypatch.setattr(scanner, "_read_arp_table", dict)
    monkeypatch.setattr(scanner, "_include_local_device", lambda records: None)
    monkeypatch.setattr(scanner, "_include_special_devices", lambda records, entries: records)
    service = Mock(return_value=({}, set()))
    enrich = Mock()
    monkeypatch.setattr(scanner, "_discover_extra_services", service)
    monkeypatch.setattr(scanner, "_enrich_records", enrich)
    scanner.scan(resolve_names=True, extra_methods=("mdns", "ssdp"))
    assert service.call_args.args[0] == ()
    assert enrich.call_args.args[1] is False


def test_cli_explicit_interface_defaults_to_real_subnet_without_route_lookup(monkeypatch, tmp_path):
    import importlib

    command = importlib.import_module("lanctl.apps.ip.interfaces.cli.commands.list")
    from lanctl.apps.ip.interfaces.cli.main import build_parser

    monkeypatch.setattr(network_interfaces, "ipv4_interfaces", lambda: [NIC])
    monkeypatch.setattr("lanctl.apps.ip.lab.LabRepository.active", lambda self: None)
    monkeypatch.setattr(command, "local_ipv4", Mock(side_effect=AssertionError("route lookup")))
    args = build_parser().parse_args(
        ["list", "--interface", NIC["id"], "--database", str(tmp_path / "devices.json")]
    )
    scanner = Mock(side_effect=RuntimeError("captured scanner"))
    monkeypatch.setattr(command, "LanScanner", scanner)
    with pytest.raises(RuntimeError, match="captured scanner"):
        command.run_list(args)
    assert str(scanner.call_args.kwargs["network"]) == NIC["network"]
    assert scanner.call_args.kwargs["source_address"] == NIC["id"]
    args = build_parser().parse_args(
        ["list", "--interface", NIC["id"], "--network", "192.0.2.0/24"]
    )
    scanner.reset_mock()
    with pytest.raises(ValueError, match="pertenecer"):
        command.run_list(args)
    scanner.assert_not_called()


def test_first_scan_choices_are_read_only_and_preserve_real_mask(monkeypatch, tmp_path):
    from lanctl.core import first_scan

    monkeypatch.setattr(first_scan, "_path", lambda: tmp_path / "request.json")
    monkeypatch.setattr(first_scan, "load_config", lambda: {"range": "192.0.2.0/24"})
    enumerate_interfaces = Mock(return_value=[NIC])
    monkeypatch.setattr(network_interfaces, "ipv4_interfaces", enumerate_interfaces)
    assert not first_scan.scan_choices()["requested"]
    enumerate_interfaces.assert_not_called()
    first_scan.request_first_scan()
    options = first_scan.scan_choices()
    assert options["networks"] == [NIC]
    assert options["interfaceSelectionAvailable"]
    assert options["requested"] and first_scan.scan_choices()["requested"]
    assert "ICMP/ARP" in options["notice"]


def test_first_scan_enumeration_failure_has_no_default_interface(monkeypatch, tmp_path):
    from lanctl.core import first_scan

    monkeypatch.setattr(first_scan, "_path", lambda: tmp_path / "request.json")
    monkeypatch.setattr(first_scan, "load_config", lambda: {"range": "192.0.2.0/24"})
    monkeypatch.setattr(
        network_interfaces, "ipv4_interfaces", Mock(side_effect=OSError("not available"))
    )
    first_scan.request_first_scan()
    options = first_scan.scan_choices()
    assert options["requested"] and options["networks"] == []
    assert not options["interfaceSelectionAvailable"]
    assert options["routing"] == "unavailable"


def test_linux_cache_uses_ip_without_net_tools(monkeypatch):
    monkeypatch.setattr(lan_scanner.platform, "system", lambda: "Linux")
    run = Mock(
        return_value=SimpleNamespace(
            returncode=0, stdout="10.20.1.9 dev eth0 lladdr aa:bb:cc:dd:ee:ff STALE"
        )
    )
    monkeypatch.setattr(lan_scanner.subprocess, "run", run)
    scanner = lan_scanner.LanScanner(
        ipaddress.IPv4Network("10.20.1.0/24"), workers=1, timeout=0.1, max_hosts=256
    )
    assert scanner._read_arp_table() == {"10.20.1.9": "AA:BB:CC:DD:EE:FF"}
    assert run.call_args.args[0] == ["ip", "-4", "neigh", "show"]


@pytest.mark.parametrize(
    "failure",
    [
        FileNotFoundError("missing"),
        lan_scanner.subprocess.TimeoutExpired("ip", 10),
        SimpleNamespace(returncode=1, stdout=""),
    ],
)
def test_unavailable_cache_does_not_abort_scan(monkeypatch, failure):
    monkeypatch.setattr(lan_scanner.platform, "system", lambda: "Linux")
    run = (
        Mock(side_effect=failure) if isinstance(failure, Exception) else Mock(return_value=failure)
    )
    monkeypatch.setattr(lan_scanner.subprocess, "run", run)
    scanner = lan_scanner.LanScanner(
        ipaddress.IPv4Network("10.20.1.0/30"), workers=1, timeout=0.1, max_hosts=256
    )
    monkeypatch.setattr(scanner, "_parallel_discovery", lambda *args: ({"10.20.1.1"}, {}))
    monkeypatch.setattr(scanner, "_include_local_device", lambda records: None)
    records = scanner.scan(resolve_names=False)
    assert "10.20.1.1" in [record.ip for record in records]


def test_linux_cache_falls_back_to_arp(monkeypatch):
    monkeypatch.setattr(lan_scanner.platform, "system", lambda: "Linux")
    run = Mock(
        side_effect=[
            FileNotFoundError("ip"),
            SimpleNamespace(
                returncode=0, stdout="host (10.20.1.9) at aa:bb:cc:dd:ee:ff [ether] on eth0"
            ),
        ]
    )
    monkeypatch.setattr(lan_scanner.subprocess, "run", run)
    scanner = lan_scanner.LanScanner(
        ipaddress.IPv4Network("10.20.1.0/24"), workers=1, timeout=0.1, max_hosts=256
    )
    assert scanner._read_arp_table() == {"10.20.1.9": "AA:BB:CC:DD:EE:FF"}
    assert run.call_args.args[0] == ["arp", "-a"]
