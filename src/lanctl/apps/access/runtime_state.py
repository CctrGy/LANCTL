"""Private, versioned acknowledgements from the process owning a listener."""

import hashlib
import json
import os
import signal
import time
from contextlib import contextmanager
from pathlib import Path

from lanctl.core.file_transaction import atomic_write_json, locked_file

TIMEOUT = 8.0


def _revision(settings):
    return (
        settings.get("lifecycleRevision")
        or hashlib.sha256(
            json.dumps(
                {
                    k: v
                    for k, v in settings.items()
                    if k not in {"processId", "processIdentity", "processToken"}
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
    )


def _path(service, protocol):
    return service.config_path.with_name(service.config_path.name + f".{protocol}.runtime.json")


def _read(service, protocol):
    path = _path(service, protocol)
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise ValueError("Estado de ejecución remota no compatible")
    return value


def _owner():
    from lanctl.apps.monitor.lifecycle import _process_identity

    return {"processId": os.getpid(), "processIdentity": _process_identity(os.getpid())}


@contextmanager
def _windows_handle(record, *, terminate=False):
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    for name, arguments, result in (
        ("OpenProcess", [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        ("CloseHandle", [wintypes.HANDLE], wintypes.BOOL),
        ("WaitForSingleObject", [wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        ("TerminateProcess", [wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
        (
            "GetProcessTimes",
            [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4,
            wintypes.BOOL,
        ),
    ):
        function = getattr(kernel, name)
        function.argtypes, function.restype = arguments, result
    handle = kernel.OpenProcess(0x1000 | 0x100000 | int(terminate), False, record["processId"])
    if not handle:
        code = ctypes.get_last_error()
        if code == 87:  # PID no longer exists; access denied is NOT confirmation of exit.
            yield kernel, None
            return
        raise ctypes.WinError(code)
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        started = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        expected = record["processIdentity"].get("started")
        yield kernel, handle if str(started) == str(expected) else None
    finally:
        kernel.CloseHandle(handle)


def _alive(record):
    if not record.get("processId"):
        return False
    if not record.get("processIdentity"):
        raise RuntimeError("Propietario remoto sin identidad verificable")
    if (
        type(record["processId"]) is not int
        or record["processId"] <= 0
        or not isinstance(record["processIdentity"], dict)
    ):
        raise ValueError("Identidad de proceso remoto no válida")
    if os.name == "nt":
        with _windows_handle(record) as (kernel, handle):
            if not handle:
                return False
            result = kernel.WaitForSingleObject(handle, 0)
            if result not in (0, 258):
                raise OSError("No se pudo confirmar el estado del proceso remoto")
            return result == 258
    from lanctl.apps.monitor.lifecycle import _process_identity

    try:
        if _process_identity(int(record["processId"])) != record["processIdentity"]:
            return False
        stat = Path(f"/proc/{int(record['processId'])}/stat").read_text(encoding="ascii")
        return stat.rpartition(") ")[2].split()[0] != "Z"
    except (ProcessLookupError, FileNotFoundError):
        return False


def _stop_owner(record):
    if not _alive(record):
        return
    if record["processId"] == os.getpid():
        raise RuntimeError("No se puede terminar el proceso administrador")
    if os.name == "nt":
        import ctypes

        with _windows_handle(record, terminate=True) as (kernel, handle):
            if not handle:
                return
            if not kernel.TerminateProcess(handle, 0):
                raise ctypes.WinError(ctypes.get_last_error())
            if kernel.WaitForSingleObject(handle, int(TIMEOUT * 1000)) != 0:
                raise TimeoutError("No se confirmó la parada del proceso remoto")
        return
    # A pidfd addresses the verified process even if its numeric PID is reused.
    if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
        raise RuntimeError("La parada remota requiere soporte pidfd del sistema")
    try:
        descriptor = os.pidfd_open(record["processId"])
    except ProcessLookupError:
        return
    try:
        if _alive(record):
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        _wait(lambda: not _alive(record), "No se confirmó la parada del proceso remoto")
    finally:
        os.close(descriptor)


def _publish(service, protocol, settings, state, backend, *, token=None):
    owner = _owner()
    with locked_file(_path(service, protocol)):
        current = _read(service, protocol)
        if (
            current.get("state") in {"running", "starting"}
            and (current.get("processId") != owner["processId"] or current.get("token") != token)
            and _alive(current)
        ):
            raise RuntimeError("Otro proceso conserva el listener remoto")
        atomic_write_json(
            _path(service, protocol),
            {
                "schemaVersion": 1,
                **owner,
                "revision": _revision(settings),
                "state": state,
                "backend": backend,
                "token": token,
            },
        )


def _wait(predicate, message):
    deadline = time.monotonic() + TIMEOUT
    while not predicate():
        if time.monotonic() >= deadline:
            raise TimeoutError(message)
        time.sleep(0.05)


def _ready(service, protocol, settings, backend):
    record = _read(service, protocol)
    return (
        record.get("revision") == _revision(settings)
        and record.get("backend") == backend
        and record.get("state") == "running"
        and _alive(record)
    )
