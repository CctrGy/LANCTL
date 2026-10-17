"""Local IPv4 interface inventory. Enumeration never sends discovery probes."""

from __future__ import annotations

import ipaddress
import json
import platform
import subprocess


def _read(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
    )
    if len(result.stdout) > 1024 * 1024:
        raise ValueError("La lista de interfaces supera el límite admitido")
    return json.loads(result.stdout or "[]")


def ipv4_interfaces() -> list[dict]:
    if platform.system() == "Windows":
        document = _read(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); "
                    "@(Get-NetIPConfiguration -All -ErrorAction Stop | "
                    "Where-Object {$_.NetAdapter.Status -eq 'Up'} | ForEach-Object {"
                    "$c=$_; $_.IPv4Address | ForEach-Object {"
                    "[pscustomobject]@{name=$c.InterfaceAlias;index=$c.InterfaceIndex;"
                    "address=$_.IPAddress;prefix=$_.PrefixLength}}}) | ConvertTo-Json -Compress"
                ),
            ]
        )
        raw = [document] if isinstance(document, dict) else document
    elif platform.system() == "Linux":
        document = _read(["ip", "-j", "-4", "address", "show", "up"])
        if not isinstance(document, list):
            raise ValueError("Inventario de interfaces no válido")
        raw = []
        for item in document:
            if not isinstance(item, dict) or not isinstance(item.get("addr_info"), list):
                raise ValueError("Inventario de interfaces no válido")
            for address in item["addr_info"]:
                if not isinstance(address, dict):
                    raise ValueError("Dirección de interfaz no válida")
                if address.get("family") == "inet":
                    raw.append(
                        {
                            "name": item.get("ifname"),
                            "index": item.get("ifindex"),
                            "address": address.get("local"),
                            "prefix": address.get("prefixlen"),
                        }
                    )
    else:
        raise OSError("La selección de interfaz requiere Windows o Linux")
    if not isinstance(raw, list):
        raise ValueError("Inventario de interfaces no válido")
    result = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Datos de interfaz no válidos")
        name, index, prefix = item.get("name"), item.get("index"), item.get("prefix")
        if (
            not isinstance(name, str)
            or not name
            or len(name) > 256
            or any(not ch.isprintable() for ch in name)
            or type(index) is not int
            or index < 1
            or type(prefix) is not int
            or not 0 <= prefix <= 32
        ):
            raise ValueError("Datos de interfaz no válidos")
        if not isinstance(item.get("address"), str):
            raise ValueError("Dirección de interfaz no válida")
        address = ipaddress.IPv4Address(item["address"])
        if address.is_loopback or address.is_multicast or address.is_unspecified:
            continue
        network = ipaddress.IPv4Network(f"{address}/{prefix}", strict=False)
        result.append(
            {
                "id": f"{index}:{address}",
                "name": name,
                "index": index,
                "address": str(address),
                "prefixLength": prefix,
                "network": str(network),
            }
        )
    return sorted(result, key=lambda item: (item["index"], item["address"]))


def select_interface(source: str, network=None) -> dict:
    # Accept an explicit address or the inventory's stable index/address pair.
    if not isinstance(source, str) or len(source) > 80:
        raise ValueError("Interfaz de origen no válida")
    interfaces = ipv4_interfaces()
    matches = [item for item in interfaces if source in (item["id"], item["address"])]
    if len(matches) != 1:
        raise ValueError("La interfaz ya no está disponible o es ambigua; vuelve a seleccionar")
    selected = matches[0]
    if sum(item["address"] == selected["address"] for item in interfaces) != 1:
        raise ValueError("La dirección de origen está asignada a varias interfaces")
    if network is not None:
        requested = ipaddress.ip_network(network, strict=False)
        if not isinstance(requested, ipaddress.IPv4Network) or not requested.subnet_of(
            ipaddress.IPv4Network(selected["network"])
        ):
            raise ValueError("El rango confirmado debe pertenecer a la interfaz seleccionada")
    return selected
