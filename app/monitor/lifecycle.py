from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path


class SingletonLock:
    """Lock singleton que verifica PID y tiempo de creación del proceso."""

    def __init__(self, path):
        self.path = Path(path)
        self.owned = False
        self.identity = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        identity = _process_identity(os.getpid())
        record = {"pid": os.getpid(), "identity": identity}
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            existing = self._read()
            if existing:
                try:
                    current = _process_identity(int(existing["pid"]))
                except (OSError, ValueError, KeyError):
                    self.path.unlink(missing_ok=True)
                    return self.acquire()
                if not existing.get("identity"):
                    raise RuntimeError(
                        f"lock monitor heredado no verificable con PID {existing['pid']}"
                    )
                if current == existing["identity"]:
                    raise RuntimeError(f"monitor ya activo con PID {existing['pid']}")
            self.path.unlink(missing_ok=True)
            return self.acquire()
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(record, stream)
        self.identity = identity
        self.owned = True
        return self

    def release(self):
        if self.owned:
            current = self._read()
            if (
                current
                and current.get("pid") == os.getpid()
                and current.get("identity") == self.identity
            ):
                self.path.unlink(missing_ok=True)
            self.owned = False

    def status(self):
        record = self._read()
        if not record:
            return {"running": False}
        try:
            pid = int(record["pid"])
            identity = record.get("identity")
            current = _process_identity(pid)
        except (OSError, ValueError, KeyError):
            return {"running": False, "stale": True}
        if not identity:
            return {"running": False, "stale": False, "unverified": True, "pid": pid}
        if current != identity:
            return {"running": False, "stale": True, "pid": pid}
        return {"running": True, "verified": True, "pid": pid, "identity": identity}

    def _read(self):
        if not self.path.exists():
            return None
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *_):
        self.release()


def _process_identity(pid: int) -> dict:
    if pid <= 0:
        raise OSError("PID no válido")
    if os.name == "nt":
        return _windows_process_identity(pid)
    os.kill(pid, 0)
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        fields = stat.read_text(encoding="ascii").split()
        executable = str(Path(f"/proc/{pid}/exe").resolve())
        return {"started": fields[21], "executable": executable}
    return {"started": "unknown", "executable": "unknown"}


def _windows_process_identity(pid: int) -> dict:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("Kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetProcessTimes.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    ]
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        raise OSError("proceso no encontrado")
    try:
        creation = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel_time = wintypes.FILETIME()
        user_time = wintypes.FILETIME()
        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        ):
            raise OSError("no se pudo consultar el proceso")
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            raise OSError("no se pudo verificar el ejecutable")
        started = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        return {"started": str(started), "executable": os.path.normcase(buffer.value)}
    finally:
        kernel32.CloseHandle(handle)
