from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
from collections.abc import Callable
from ctypes import wintypes

from lanctl.core.file_transaction import atomic_write_bytes, transactional_method
from lanctl.core.paths import application_path


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(value: bytes) -> tuple[_DataBlob, object]:
    buffer = ctypes.create_string_buffer(value)
    return _DataBlob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def _dpapi():
    """Carga DPAPI con firmas de puntero correctas para Windows x64."""
    crypt32 = ctypes.WinDLL("Crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("Kernel32", use_last_error=True)
    blob_pointer = ctypes.POINTER(_DataBlob)
    crypt32.CryptProtectData.argtypes = [
        blob_pointer,
        wintypes.LPCWSTR,
        blob_pointer,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.DWORD,
        blob_pointer,
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    crypt32.CryptUnprotectData.argtypes = [
        blob_pointer,
        ctypes.POINTER(wintypes.LPWSTR),
        blob_pointer,
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.DWORD,
        blob_pointer,
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel32.LocalFree.restype = wintypes.HLOCAL
    return crypt32, kernel32


def protect_secret(value: bytes) -> bytes:
    """Cifra con DPAPI; el secreto solo puede abrirlo este usuario de Windows."""
    if os.name != "nt":
        raise OSError("el almacén cifrado requiere Windows DPAPI")
    source, source_buffer = _blob(value)
    entropy, entropy_buffer = _blob(b"ALS credentials v1")
    output = _DataBlob()
    crypt32, kernel32 = _dpapi()
    if not crypt32.CryptProtectData(
        ctypes.byref(source),
        "ALS",
        ctypes.byref(entropy),
        None,
        None,
        1,
        ctypes.byref(output),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output.pbData, wintypes.HLOCAL))
        _ = (source_buffer, entropy_buffer)


def unprotect_secret(value: bytes) -> bytes:
    if os.name != "nt":
        raise OSError("el almacén cifrado requiere Windows DPAPI")
    source, source_buffer = _blob(value)
    entropy, entropy_buffer = _blob(b"ALS credentials v1")
    output = _DataBlob()
    crypt32, kernel32 = _dpapi()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(source),
        None,
        ctypes.byref(entropy),
        None,
        None,
        1,
        ctypes.byref(output),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output.pbData, wintypes.HLOCAL))
        _ = (source_buffer, entropy_buffer)


class CredentialStore:
    def __init__(
        self,
        path: str,
        protect: Callable[[bytes], bytes] = protect_secret,
        unprotect: Callable[[bytes], bytes] = unprotect_secret,
        *,
        cipher: str = "auto",
        password: str | None = None,
    ):
        self.path = application_path(path)
        self._protect = protect
        self._unprotect = unprotect
        if cipher not in {"auto", "dpapi", "portable"}:
            raise ValueError("proveedor de cifrado no disponible")
        self.cipher = cipher
        self._password = password

    def _vault_password(self) -> str:
        if self._password is None:
            from lanctl.core.secret_input import read_secret

            self._password = read_secret("Contraseña del almacén cifrado: ")
            if not self.path.exists() and self._password != read_secret(
                "Repite la contraseña del nuevo almacén: "
            ):
                self._password = None
                raise ValueError("las contraseñas no coinciden; almacén no creado")
        return self._password

    @staticmethod
    def identifier(device_id: str, protocol: str) -> str:
        digest = hashlib.sha256(f"{device_id}:{protocol}".encode()).hexdigest()[:24]
        return f"cred_{digest}"

    def _load(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "entries": {}}
        try:
            from lanctl.core.vault_crypto import MAGIC, MAX_BYTES, decrypt

            if self.path.stat().st_size > MAX_BYTES * 3:
                raise ValueError("almacén demasiado grande")
            encrypted = base64.b64decode(self.path.read_bytes().strip(), validate=True)
            portable = encrypted.startswith(MAGIC)
            actual = "portable" if portable else "dpapi"
            if self.cipher not in {"auto", actual}:
                raise ValueError("el cifrado no coincide; utiliza export/import para convertir")
            self.cipher = actual
            clear = (
                decrypt(encrypted, self._vault_password())
                if portable
                else self._unprotect(encrypted)
            )
            value = json.loads(clear.decode("utf-8"))
        except (ValueError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"almacén de credenciales inválido: {self.path}") from error
        if (
            not isinstance(value, dict)
            or value.get("version") != 1
            or not isinstance(value.get("entries"), dict)
        ):
            raise ValueError(f"formato de credenciales no compatible: {self.path}")
        for identifier, entry in value["entries"].items():
            if (
                not isinstance(entry, dict)
                or not all(
                    isinstance(entry.get(key), str)
                    for key in ("deviceId", "protocol", "username", "password")
                )
                or identifier != self.identifier(entry["deviceId"], entry["protocol"])
            ):
                raise ValueError("entrada de credencial inválida")
        return value

    @transactional_method
    def _save(self, value: dict) -> None:
        clear = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
        from lanctl.core.vault_crypto import encrypt

        encoded = base64.b64encode(
            encrypt(clear, self._vault_password())
            if self.cipher == "portable"
            else self._protect(clear)
        )
        atomic_write_bytes(self.path, encoded + b"\n")

    @transactional_method
    def set(self, device_id: str, protocol: str, username: str, password: str) -> str:
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

    def metadata(self) -> list[dict[str, str]]:
        """Lista metadatos seguros sin descifrar secretos fuera del almacén."""
        return [
            {
                "credentialId": identifier,
                "deviceId": str(entry.get("deviceId", "")),
                "protocol": str(entry.get("protocol", "")),
                "username": str(entry.get("username", "")),
            }
            for identifier, entry in sorted(self._load()["entries"].items())
        ]

    @transactional_method
    def delete(self, credential_id: str) -> bool:
        value = self._load()
        existed = value["entries"].pop(credential_id, None) is not None
        if existed:
            self._save(value)
        return existed
