from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
from typing import Callable
from app.core.paths import application_path


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(value: bytes) -> tuple[_DataBlob, object]:
    buffer = ctypes.create_string_buffer(value)
    return _DataBlob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def protect_secret(value: bytes) -> bytes:
    """Cifra con DPAPI; el secreto solo puede abrirlo este usuario de Windows."""
    if os.name != "nt":
        raise OSError("el almacén cifrado requiere Windows DPAPI")
    source, source_buffer = _blob(value)
    entropy, entropy_buffer = _blob(b"ALS credentials v1")
    output = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    if not crypt32.CryptProtectData(
        ctypes.byref(source), "ALS", ctypes.byref(entropy), None, None, 1,
        ctypes.byref(output),
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)
        _ = (source_buffer, entropy_buffer)


def unprotect_secret(value: bytes) -> bytes:
    if os.name != "nt":
        raise OSError("el almacén cifrado requiere Windows DPAPI")
    source, source_buffer = _blob(value)
    entropy, entropy_buffer = _blob(b"ALS credentials v1")
    output = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source), None, ctypes.byref(entropy), None, None, 1,
        ctypes.byref(output),
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)
        _ = (source_buffer, entropy_buffer)


class CredentialStore:
    def __init__(
        self,
        path: str,
        protect: Callable[[bytes], bytes] = protect_secret,
        unprotect: Callable[[bytes], bytes] = unprotect_secret,
    ):
        self.path = application_path(path)
        self._protect = protect
        self._unprotect = unprotect

    @staticmethod
    def identifier(device_id: str, protocol: str) -> str:
        digest = hashlib.sha256(f"{device_id}:{protocol}".encode()).hexdigest()[:24]
        return f"cred_{digest}"

    def _load(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "entries": {}}
        try:
            encrypted = base64.b64decode(self.path.read_bytes().strip(), validate=True)
            value = json.loads(self._unprotect(encrypted).decode("utf-8"))
        except (ValueError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"almacén de credenciales inválido: {self.path}") from error
        if value.get("version") != 1 or not isinstance(value.get("entries"), dict):
            raise ValueError(f"formato de credenciales no compatible: {self.path}")
        return value

    def _save(self, value: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        clear = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
        encoded = base64.b64encode(self._protect(clear))
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_bytes(encoded + b"\n")
        temporary.replace(self.path)

    def set(
        self, device_id: str, protocol: str, username: str, password: str
    ) -> str:
        credential_id = self.identifier(device_id, protocol)
        value = self._load()
        value["entries"][credential_id] = {
            "deviceId": device_id,
            "protocol": protocol,
            "username": username,
            "password": password,
        }
        self._save(value)
        return credential_id

    def get(self, credential_id: str) -> dict[str, str]:
        entry = self._load()["entries"].get(credential_id)
        if entry is None:
            raise ValueError(f"credencial no encontrada: {credential_id}")
        return dict(entry)

    def delete(self, credential_id: str) -> bool:
        value = self._load()
        existed = value["entries"].pop(credential_id, None) is not None
        if existed:
            self._save(value)
        return existed
