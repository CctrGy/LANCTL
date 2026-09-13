from __future__ import annotations

import base64
import ctypes
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import lanctl.core.credentials as credential_module
from lanctl.core.credentials import CredentialStore, _blob, _dpapi, protect_secret, unprotect_secret


def _store(path: Path) -> CredentialStore:
    return CredentialStore(
        str(path),
        protect=lambda value: b"encrypted:" + value[::-1],
        unprotect=lambda value: value.removeprefix(b"encrypted:")[::-1],
    )


def test_blob_keeps_payload_and_buffer_alive():
    blob, buffer = _blob(b"secret-bytes")
    assert blob.cbData == len(b"secret-bytes")
    assert buffer.raw.startswith(b"secret-bytes")


def test_dpapi_operations_fail_closed_outside_windows(monkeypatch):
    monkeypatch.setattr(credential_module, "os", SimpleNamespace(name="posix"))
    with pytest.raises(OSError, match="Windows DPAPI"):
        protect_secret(b"secret")
    with pytest.raises(OSError, match="Windows DPAPI"):
        unprotect_secret(b"encrypted")


class _NativeCall:
    def __init__(self, result=True, payload=b""):
        self.result = result
        self.payload = payload
        self.buffer = None

    def __call__(self, *_args):
        if self.result and self.payload:
            output = _args[-1]._obj
            self.buffer = ctypes.create_string_buffer(self.payload)
            output.cbData = len(self.payload)
            output.pbData = ctypes.cast(self.buffer, ctypes.POINTER(ctypes.c_byte))
        return self.result


class _Crypt32:
    def __init__(self, *, protect=True, unprotect=True):
        self.CryptProtectData = _NativeCall(protect, b"protected")
        self.CryptUnprotectData = _NativeCall(unprotect, b"clear")


class _Kernel32:
    def __init__(self):
        self.LocalFree = _NativeCall()


def test_dpapi_loader_assigns_native_signatures(monkeypatch):
    crypt32, kernel32 = _Crypt32(), _Kernel32()
    monkeypatch.setattr(
        credential_module.ctypes,
        "WinDLL",
        lambda name, **_options: crypt32 if name == "Crypt32" else kernel32,
        raising=False,
    )
    loaded_crypt32, loaded_kernel32 = _dpapi()
    assert loaded_crypt32 is crypt32 and loaded_kernel32 is kernel32
    assert crypt32.CryptProtectData.restype is credential_module.wintypes.BOOL
    assert crypt32.CryptUnprotectData.argtypes
    assert kernel32.LocalFree.argtypes


def test_dpapi_protect_and_unprotect_release_native_memory(monkeypatch):
    crypt32, kernel32 = _Crypt32(), _Kernel32()
    monkeypatch.setattr(credential_module, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(credential_module, "_dpapi", lambda: (crypt32, kernel32))
    assert protect_secret(b"clear") == b"protected"
    assert unprotect_secret(b"protected") == b"clear"


@pytest.mark.parametrize("operation", ["protect", "unprotect"])
def test_dpapi_native_failure_is_raised(monkeypatch, operation):
    crypt32 = _Crypt32(protect=operation != "protect", unprotect=operation != "unprotect")
    monkeypatch.setattr(credential_module, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(credential_module, "_dpapi", lambda: (crypt32, _Kernel32()))
    monkeypatch.setattr(credential_module.ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(
        credential_module.ctypes,
        "WinError",
        lambda _code: OSError("native error"),
        raising=False,
    )
    with pytest.raises(OSError, match="native error"):
        (protect_secret if operation == "protect" else unprotect_secret)(b"value")


def test_identifier_is_stable_and_protocol_scoped():
    first = CredentialStore.identifier("device-1", "ssh")
    assert first == CredentialStore.identifier("device-1", "ssh")
    assert first != CredentialStore.identifier("device-1", "https")
    assert first.startswith("cred_") and len(first) == 29


def test_store_lifecycle_and_missing_entry(tmp_path):
    store = _store(tmp_path / "credentials.dc")
    assert store._load() == {"version": 1, "entries": {}}
    credential_id = store.set("device-1", "ssh", "operator", "top-secret")
    assert store.get(credential_id) == {
        "deviceId": "device-1",
        "protocol": "ssh",
        "username": "operator",
        "password": "top-secret",
    }
    assert b"top-secret" not in store.path.read_bytes()
    assert store.delete(credential_id)
    assert not store.delete(credential_id)
    with pytest.raises(ValueError, match="no encontrada"):
        store.get(credential_id)


@pytest.mark.parametrize(
    "payload",
    [
        b"not-base64",
        base64.b64encode(b"encrypted:" + b"not-json"[::-1]),
    ],
)
def test_store_rejects_corrupt_payloads(tmp_path, payload):
    path = tmp_path / "credentials.dc"
    path.write_bytes(payload)
    with pytest.raises(ValueError, match="almacén de credenciales inválido"):
        _store(path)._load()


@pytest.mark.parametrize(
    "document",
    [
        {"version": 2, "entries": {}},
        {"version": 1, "entries": []},
        {"entries": {}},
    ],
)
def test_store_rejects_incompatible_schema(tmp_path, document):
    path = tmp_path / "credentials.dc"
    clear = json.dumps(document).encode()
    path.write_bytes(base64.b64encode(b"encrypted:" + clear[::-1]))
    with pytest.raises(ValueError, match="formato de credenciales no compatible"):
        _store(path)._load()
