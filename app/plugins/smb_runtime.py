from __future__ import annotations

import ctypes
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import uuid
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

from app.core.tasking import result, utc_now

SYSTEM_SHARES = {"ADMIN$", "IPC$", "PRINT$"}
ERROR_ACCESS_DENIED = 5
ERROR_SESSION_CREDENTIAL_CONFLICT = 1219
SHARE_TYPES = {0: "disk", 1: "printer", 3: "ipc"}


class SMBError(RuntimeError):
    def __init__(self, code: str, message: str, *, state: str = "error"):
        super().__init__(message)
        self.code, self.state = code, state


def validate_component(value: str) -> str:
    clean = str(value).strip()
    if not clean or clean in {".", ".."} or any(c in clean for c in '\\/:*?"<>|'):
        raise ValueError("nombre SMB no válido")
    return clean


def unc_path(host: str, share: str | None = None) -> str:
    clean_host = str(host).strip().strip("\\")
    if not clean_host or "\\" in clean_host or "/" in clean_host or clean_host in {".", ".."}:
        raise ValueError("servidor SMB no válido")
    return rf"\\{clean_host}" + (rf"\{validate_component(share)}" if share else "")


def classify_share(name: str, native_type: int) -> tuple[str, bool]:
    base = native_type & 0xFF
    special = bool(native_type & 0x80000000)
    upper = name.upper()
    administrative = upper in SYSTEM_SHARES or (upper.endswith("$") and base == 0)
    kind = "administrative" if administrative else SHARE_TYPES.get(base, "special")
    return kind, administrative or special


class SMBNative:
    """Win32 adapter. Tests replace it; production never enables SMB1."""

    def __init__(self):
        self._linux_sessions: dict[str, tuple[str, str]] = {}
        self._linux_identity: dict[str, dict] = {}
        self._session_lock = threading.RLock()

    def probe(self, host: str, timeout: float) -> bool:
        with socket.create_connection((host, 445), timeout=timeout):
            return True

    def resolve(self, host: str) -> str:
        return socket.gethostbyname(host)

    def identity(self, host: str) -> dict:
        if os.name != "nt":
            cached = self._linux_identity.get(host, {})
            return {
                "serverName": host,
                "hostname": socket.getfqdn(host),
                "workgroup": cached.get("workgroup", ""),
                "domain": cached.get("domain", ""),
                "source": "smbclient" if cached else "dns",
            }

        class SERVER_INFO_101(ctypes.Structure):
            _fields_ = [
                ("platform_id", wintypes.DWORD),
                ("name", wintypes.LPWSTR),
                ("version_major", wintypes.DWORD),
                ("version_minor", wintypes.DWORD),
                ("type", wintypes.DWORD),
                ("comment", wintypes.LPWSTR),
            ]

        buffer = ctypes.c_void_p()
        status = ctypes.windll.netapi32.NetServerGetInfo(unc_path(host), 101, ctypes.byref(buffer))
        if status:
            return {
                "serverName": host,
                "hostname": socket.getfqdn(host),
                "workgroup": "",
                "domain": "",
                "source": "dns",
            }
        try:
            info = ctypes.cast(buffer, ctypes.POINTER(SERVER_INFO_101)).contents
            result = {
                "serverName": info.name or host,
                "hostname": socket.getfqdn(host),
                "comment": info.comment or "",
                "workgroup": "",
                "domain": "",
                "source": "NetServerGetInfo",
            }
        finally:
            ctypes.windll.netapi32.NetApiBufferFree(buffer)

        class WKSTA_INFO_100(ctypes.Structure):
            _fields_ = [
                ("platform_id", wintypes.DWORD),
                ("computername", wintypes.LPWSTR),
                ("langroup", wintypes.LPWSTR),
                ("version_major", wintypes.DWORD),
                ("version_minor", wintypes.DWORD),
            ]

        workstation = ctypes.c_void_p()
        status = ctypes.windll.netapi32.NetWkstaGetInfo(
            unc_path(host), 100, ctypes.byref(workstation)
        )
        if not status:
            try:
                info = ctypes.cast(workstation, ctypes.POINTER(WKSTA_INFO_100)).contents
                result["serverName"] = info.computername or result["serverName"]
                result["workgroup"] = info.langroup or ""
                result["source"] += "+NetWkstaGetInfo"
            finally:
                ctypes.windll.netapi32.NetApiBufferFree(workstation)
        return result

    def shares(self, host: str) -> list[dict]:
        if os.name != "nt":
            return self._linux_shares(host)

        class SHARE_INFO_1(ctypes.Structure):
            _fields_ = [
                ("name", wintypes.LPWSTR),
                ("type", wintypes.DWORD),
                ("remark", wintypes.LPWSTR),
            ]

        buffer, read, total, resume = (
            ctypes.c_void_p(),
            wintypes.DWORD(),
            wintypes.DWORD(),
            wintypes.DWORD(),
        )
        status = ctypes.windll.netapi32.NetShareEnum(
            unc_path(host),
            1,
            ctypes.byref(buffer),
            0xFFFFFFFF,
            ctypes.byref(read),
            ctypes.byref(total),
            ctypes.byref(resume),
        )
        if status == ERROR_ACCESS_DENIED:
            raise SMBError("SMB.AUTH.ACCESS_DENIED", "acceso denegado", state="access-denied")
        if status:
            raise SMBError("SMB.SHARES.ENUMERATE_FAILED", f"NetShareEnum devolvió {status}")
        try:
            rows = ctypes.cast(buffer, ctypes.POINTER(SHARE_INFO_1))
            return [
                {
                    "name": rows[i].name,
                    "nativeType": int(rows[i].type),
                    "description": rows[i].remark or "",
                }
                for i in range(read.value)
            ]
        finally:
            if buffer:
                ctypes.windll.netapi32.NetApiBufferFree(buffer)

    def connect(self, host: str, username: str, password: str) -> None:
        if os.name != "nt":
            with self._session_lock:
                self._linux_sessions[host] = (username, password)
            try:
                self._linux_shares(host)
            except Exception:
                with self._session_lock:
                    self._linux_sessions.pop(host, None)
                raise
            return

        class NETRESOURCE(ctypes.Structure):
            _fields_ = [
                ("scope", wintypes.DWORD),
                ("type", wintypes.DWORD),
                ("display", wintypes.DWORD),
                ("usage", wintypes.DWORD),
                ("local", wintypes.LPWSTR),
                ("remote", wintypes.LPWSTR),
                ("comment", wintypes.LPWSTR),
                ("provider", wintypes.LPWSTR),
            ]

        resource = NETRESOURCE(0, 1, 0, 0, None, unc_path(host), None, None)
        status = ctypes.windll.mpr.WNetAddConnection2W(
            ctypes.byref(resource), password, username, 0
        )
        if status == ERROR_SESSION_CREDENTIAL_CONFLICT:
            raise SMBError(
                "SMB.AUTH.CREDENTIAL_CONFLICT",
                "Windows ya mantiene una sesión con otro usuario",
                state="blocked",
            )
        if status == ERROR_ACCESS_DENIED:
            raise SMBError("SMB.AUTH.ACCESS_DENIED", "credencial rechazada", state="access-denied")
        if status:
            raise SMBError("SMB.AUTH.CONNECT_FAILED", f"WNetAddConnection2 devolvió {status}")

    def disconnect(self, host: str) -> None:
        if os.name != "nt":
            with self._session_lock:
                self._linux_sessions.pop(host, None)
            return
        status = ctypes.windll.mpr.WNetCancelConnection2W(unc_path(host), 0, False)
        if status:
            raise SMBError(
                "SMB.SESSION.DISCONNECT_FAILED", f"WNetCancelConnection2 devolvió {status}"
            )

    def open_path(self, path: str) -> None:
        if os.name != "nt":
            uri = "smb:" + path.replace("\\", "/")
            opener = shutil.which("gio") or shutil.which("xdg-open")
            if not opener:
                raise SMBError(
                    "SMB.SHARE.OPEN_UNSUPPORTED", "falta gio o xdg-open", state="unsupported"
                )
            command = [opener, "open", uri] if Path(opener).name == "gio" else [opener, uri]
            completed = subprocess.run(command, check=False, capture_output=True, text=True)
            if completed.returncode:
                raise SMBError(
                    "SMB.SHARE.OPEN_FAILED",
                    completed.stderr.strip() or "no se pudo abrir el recurso",
                )
            return
        status = ctypes.windll.shell32.ShellExecuteW(None, "open", path, None, None, 1)
        if status <= 32:
            raise SMBError("SMB.SHARE.OPEN_FAILED", f"ShellExecute devolvió {status}")

    def connect_printer(self, path: str) -> None:
        if os.name != "nt":
            raise SMBError(
                "SMB.PRINTER.CONNECT_UNSUPPORTED",
                "la conexión automática de impresoras requiere Windows; usa CUPS",
                state="unsupported",
            )
        if not ctypes.windll.winspool.AddPrinterConnectionW(path):
            raise ctypes.WinError()

    def _linux_shares(self, host: str) -> list[dict]:
        executable = shutil.which("smbclient")
        if not executable:
            raise SMBError(
                "SMB.CAPABILITY.MISSING",
                "instala smbclient para enumerar SMB en Linux",
                state="unsupported",
            )
        with self._session_lock:
            credential = self._linux_sessions.get(host)
        command = [executable, "-g", "-L", f"//{host}", "-m", "SMB3"]
        auth_path: Path | None = None
        try:
            if credential:
                username, password = credential
                domain, separator, account = username.partition("\\")
                if not separator:
                    domain, account = "", username
                descriptor, name = tempfile.mkstemp(prefix="lanctl-smb-", suffix=".auth")
                auth_path = Path(name)
                os.fchmod(descriptor, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    stream.write(f"username = {account}\npassword = {password}\n")
                    if domain:
                        stream.write(f"domain = {domain}\n")
                command.extend(["-A", str(auth_path)])
            else:
                command.append("-N")
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise SMBError("SMB.SHARES.TIMEOUT", "smbclient agotó el timeout") from error
        finally:
            if auth_path:
                auth_path.unlink(missing_ok=True)
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).strip()
            state = (
                "access-denied"
                if any(
                    token in detail.upper()
                    for token in ("ACCESS_DENIED", "LOGON_FAILURE", "PASSWORD")
                )
                else "error"
            )
            code = (
                "SMB.AUTH.ACCESS_DENIED"
                if state == "access-denied"
                else "SMB.SHARES.ENUMERATE_FAILED"
            )
            raise SMBError(code, detail or "smbclient no pudo enumerar recursos", state=state)
        shares: list[dict] = []
        identity: dict[str, str] = {}
        for line in completed.stdout.splitlines():
            kind, separator, remainder = line.partition("|")
            if not separator:
                continue
            name, _, description = remainder.partition("|")
            if kind.casefold() == "workgroup":
                identity["workgroup"] = name
                continue
            native_type = {"disk": 0, "printer": 1, "ipc": 3}.get(kind.casefold())
            if native_type is not None and name:
                shares.append(
                    {
                        "name": name,
                        "nativeType": native_type,
                        "description": description,
                    }
                )
        self._linux_identity[host] = identity
        return shares


class SMBService:
    def __init__(self, native=None):
        self.native = native or SMBNative()

    def inspect(
        self, device, *, timeout=0.8, include_system=False, credential=None, run_id=None
    ) -> tuple[dict, list[dict]]:
        host = device.name or device.ip
        trace = []
        run_id = run_id or str(uuid.uuid4())

        def step(op, status="success", **kw):
            started = kw.pop("started", utc_now())
            item = result("smb.scan", op, host, status, started, run_id=run_id, **kw).to_dict()
            trace.append(item)

        started = utc_now()
        try:
            ip = self.native.resolve(host)
            step("smb.resolve.host", started=started, detail={"ip": ip})
        except OSError as error:
            step(
                "smb.resolve.host",
                "error",
                started=started,
                code="SMB.RESOLVE.FAILED",
                message=str(error),
            )
            raise SMBError("SMB.PROBE.UNREACHABLE", str(error), state="unreachable")
        started = utc_now()
        try:
            available = self.native.probe(ip, timeout)
        except OSError:
            available = False
        if not available:
            step(
                "smb.probe.port",
                "error",
                started=started,
                code="SMB.PROBE.UNREACHABLE",
                message="TCP/445 no accesible",
            )
            raise SMBError("SMB.PROBE.UNREACHABLE", "TCP/445 no accesible", state="unreachable")
        step("smb.probe.port", started=started, detail={"port": 445})
        identity = self.native.identity(host)
        step("smb.identity.query", detail={k: v for k, v in identity.items() if k != "comment"})
        authentication = "anonymous"
        try:
            raw = self.native.shares(host)
        except SMBError as error:
            if error.state not in {"access-denied", "authentication-required"}:
                step("smb.shares.enumerate", "error", code=error.code, message=str(error))
                raise
            if credential is None:
                step(
                    "smb.shares.enumerate",
                    "blocked",
                    code="SMB.AUTH.REQUIRED",
                    message="se requiere autenticación",
                )
                raise SMBError(
                    "SMB.AUTH.REQUIRED",
                    "se requiere una credencial SMB",
                    state="authentication-required",
                )
            self.native.connect(host, credential["username"], credential["password"])
            authentication = "credential"
            step("smb.auth.connect")
            raw = self.native.shares(host)
        refreshed = self.native.identity(host)
        identity.update({key: value for key, value in refreshed.items() if value})
        if authentication == "credential":
            try:
                self.native.disconnect(host)
                step("smb.auth.disconnect")
            except (OSError, SMBError) as error:
                step(
                    "smb.auth.disconnect",
                    "error",
                    code="SMB.SESSION.DISCONNECT_FAILED",
                    message=str(error),
                )
        shares = []
        for item in raw:
            kind, system = classify_share(item["name"], item.get("nativeType", 0))
            if system and not include_system:
                continue
            shares.append(
                {
                    "name": item["name"],
                    "type": kind,
                    "path": unc_path(host, item["name"]),
                    "description": item.get("description", ""),
                    "access": "unknown",
                    "system": system,
                }
            )
        step("smb.shares.enumerate", detail={"count": len(shares)})
        now = datetime.now().astimezone().isoformat()
        return {
            "deviceId": device.device_id,
            "host": host,
            "ip": ip,
            "state": "available",
            "observedAt": now,
            "smb": {
                "available": True,
                "port": 445,
                **identity,
                "authentication": authentication,
                "lastScan": now,
                "shares": shares,
            },
        }, trace

    def open_share(self, host, share, *, dry_run=False, credential=None):
        path = unc_path(host, share)
        if not dry_run:
            if credential:
                self.native.connect(host, credential["username"], credential["password"])
            self.native.open_path(path)
        return {"path": path, "dryRun": bool(dry_run)}

    def printer(self, host, name, action, *, yes=False, credential=None):
        path = unc_path(host, name)
        if credential:
            self.native.connect(host, credential["username"], credential["password"])
        if action == "connect":
            if not yes:
                raise SMBError(
                    "SMB.PRINTER.CONFIRMATION_REQUIRED", "usa --yes para confirmar", state="blocked"
                )
            self.native.connect_printer(path)
        else:
            self.native.open_path(path)
        return {"path": path, "action": action}
