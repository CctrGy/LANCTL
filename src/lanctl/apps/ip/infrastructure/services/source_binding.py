"""Explicit source adapters. Failures never fall back to another route."""

from __future__ import annotations

import ctypes
import ipaddress
import socket


def windows_ping(source: str, destination: str, timeout: float) -> bool:
    source, destination = (
        str(ipaddress.IPv4Address(source)),
        str(ipaddress.IPv4Address(destination)),
    )
    api = ctypes.WinDLL("iphlpapi.dll", use_last_error=True)
    api.IcmpCreateFile.argtypes = []
    api.IcmpCreateFile.restype = ctypes.c_void_p
    api.IcmpCloseHandle.argtypes = [ctypes.c_void_p]
    api.IcmpCloseHandle.restype = ctypes.c_int
    api.IcmpSendEcho2Ex.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_ushort,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
    ]
    api.IcmpSendEcho2Ex.restype = ctypes.c_uint32
    handle = api.IcmpCreateFile()
    if not handle or handle == ctypes.c_void_p(-1).value:
        raise OSError("No se pudo crear el canal ICMP con origen explícito")
    payload = ctypes.create_string_buffer(b"LANCTL")
    reply = ctypes.create_string_buffer(1024)
    try:
        count = api.IcmpSendEcho2Ex(
            handle,
            None,
            None,
            None,
            int.from_bytes(socket.inet_aton(source), "little"),
            int.from_bytes(socket.inet_aton(destination), "little"),
            payload,
            6,
            None,
            reply,
            len(reply),
            max(1, int(timeout * 1000)),
        )
        if not count and ctypes.get_last_error() in (50, 87, 1168):
            raise OSError("La interfaz seleccionada no permite emitir esta sonda ICMP")
        # IPAddr and Status are the first two DWORDs of ICMP_ECHO_REPLY.
        return bool(count and ctypes.c_uint32.from_buffer(reply, 4).value == 0)
    finally:
        api.IcmpCloseHandle(handle)
