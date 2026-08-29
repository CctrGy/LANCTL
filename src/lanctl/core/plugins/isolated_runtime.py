from __future__ import annotations

import atexit
import importlib.machinery
import importlib.util
import multiprocessing
import os
import sys
import threading
import time
from contextlib import suppress
from ctypes import Structure, byref, c_size_t, sizeof, wintypes
from pathlib import Path
from types import ModuleType

_RUNTIMES: set[IsolatedPluginRuntime] = set()


class IsolatedPolicyViolation(PermissionError):
    """Operación del sistema prohibida para un plugin aislado."""


def _stop_all() -> None:
    for runtime in list(_RUNTIMES):
        runtime.stop()


atexit.register(_stop_all)


def _windows_memory_job(pid: int, megabytes: int):
    if sys.platform != "win32":
        return None
    import ctypes

    class BasicLimits(Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
            ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", c_size_t),
            ("MaximumWorkingSetSize", c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IoCounters(Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class ExtendedLimits(Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimits),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", c_size_t),
            ("JobMemoryLimit", c_size_t),
            ("PeakProcessMemoryUsed", c_size_t),
            ("PeakJobMemoryUsed", c_size_t),
        ]

    kernel = ctypes.windll.kernel32
    job = kernel.CreateJobObjectW(None, None)
    process = kernel.OpenProcess(0x0100 | 0x0400, False, pid)
    if not job or not process:
        if job:
            kernel.CloseHandle(job)
        raise OSError("no se pudo crear el límite de memoria del plugin")
    try:
        limits = ExtendedLimits()
        # Memoria por proceso, máximo de un proceso y cierre conjunto del Job.
        limits.BasicLimitInformation.LimitFlags = 0x100 | 0x8 | 0x2000
        limits.BasicLimitInformation.ActiveProcessLimit = 1
        limits.ProcessMemoryLimit = max(16, megabytes) * 1024 * 1024
        if not kernel.SetInformationJobObject(job, 9, byref(limits), sizeof(limits)):
            raise ctypes.WinError()
        if not kernel.AssignProcessToJobObject(job, process):
            # Algunos hosts (CI, Codex y servicios) ya ejecutan LANCTL dentro
            # de un Job que no permite anidación. El watchdog portátil aplica
            # el mismo límite desde el padre en ese caso.
            kernel.CloseHandle(job)
            return None
        return job
    except Exception:
        kernel.CloseHandle(job)
        raise
    finally:
        kernel.CloseHandle(process)


class _IsolatedApi:
    """API mínima transportable para código Python fuera del proceso principal."""

    def __init__(self, connection, plugin_id: str, max_calls: int) -> None:
        self.connection = connection
        self.plugin_id = plugin_id
        self.remaining = max_calls

    def log(self, message: str) -> None:
        self._call("log", str(message))

    def _call(self, method: str, *arguments) -> None:
        if self.remaining <= 0:
            raise RuntimeError("límite de llamadas del plugin agotado")
        self.remaining -= 1
        self.connection.send(("CALL", method, arguments))


def _apply_memory_limit(megabytes: int) -> None:
    if sys.platform == "win32":
        return
    try:
        import resource

        limit = max(16, megabytes) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    except (ImportError, OSError, ValueError):
        return


def _install_security_policy(connection, plugin_root: Path) -> None:
    """Bloquea filesystem, red, procesos y registro fuera de la API aislada."""

    readable_roots = tuple(
        path.resolve()
        for path in {plugin_root, Path(sys.base_prefix), Path(sys.prefix)}
        if path.exists()
    )
    denied_events = {
        "ctypes.dlopen",
        "os.system",
        "pty.spawn",
        "socket.__new__",
        "socket.bind",
        "socket.connect",
        "socket.getaddrinfo",
        "subprocess.Popen",
        "winreg.CreateKey",
        "winreg.DeleteKey",
        "winreg.DeleteValue",
        "winreg.OpenKey",
        "winreg.SetValue",
    }
    mutating_events = {
        "os.chmod",
        "os.chown",
        "os.link",
        "os.mkdir",
        "os.remove",
        "os.rename",
        "os.rmdir",
        "os.symlink",
        "os.truncate",
    }

    def violation(event: str, detail: object) -> None:
        with suppress(BrokenPipeError, EOFError, OSError):
            connection.send(("VIOLATION", event, str(detail)[:512]))
        raise IsolatedPolicyViolation(f"política de plugin aislado: {event}: {detail}")

    def allowed_read(value: object) -> bool:
        if isinstance(value, int):
            return True
        try:
            candidate = Path(os.fspath(value)).expanduser().resolve()
        except (OSError, TypeError, ValueError):
            return False
        return any(candidate == root or root in candidate.parents for root in readable_roots)

    def audit(event: str, arguments: tuple) -> None:
        if event in denied_events or event in mutating_events:
            violation(event, arguments)
        if event == "open":
            path = arguments[0] if arguments else ""
            mode = str(arguments[1]) if len(arguments) > 1 else "r"
            flags = int(arguments[2]) if len(arguments) > 2 and arguments[2] is not None else 0
            writing = any(marker in mode for marker in "wax+") or bool(
                flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            )
            if writing or not allowed_read(path):
                violation(event, (path, mode, flags))
        elif event in {"os.listdir", "os.scandir"} and arguments:
            if not allowed_read(arguments[0]):
                violation(event, arguments)

    sys.dont_write_bytecode = True
    sys.addaudithook(audit)


def _worker(connection, plugin_id: str, entry: str, memory_mb: int, max_calls: int) -> None:
    _apply_memory_limit(memory_mb)
    module: ModuleType | None = None
    try:
        _install_security_policy(connection, Path(entry).resolve().parent)
        module_name = "lanctl_isolated_" + plugin_id.replace(".", "_").replace("-", "_")
        loader = importlib.machinery.SourceFileLoader(module_name, entry)
        spec = importlib.util.spec_from_loader(module_name, loader)
        if spec is None:
            raise ImportError(f"no se puede cargar {entry}")
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        activate = getattr(module, "activate", None)
        if not callable(activate):
            raise ValueError("main.exec debe definir activate(api)")
        activate(_IsolatedApi(connection, plugin_id, max_calls))
        connection.send(("READY", os.getpid()))
        while True:
            try:
                command = connection.recv()
            except EOFError:
                return
            if command == "STOP":
                deactivate = getattr(module, "deactivate", None)
                if callable(deactivate):
                    deactivate()
                connection.send(("STOPPED", os.getpid()))
                return
    except Exception as error:  # noqa: BLE001 - frontera de código externo
        try:
            kind = "VIOLATION" if isinstance(error, IsolatedPolicyViolation) else "ERROR"
            connection.send((kind, type(error).__name__, str(error)))
        except (BrokenPipeError, EOFError, OSError):
            return
    finally:
        connection.close()


class IsolatedPluginRuntime:
    """Proceso restringido con handshake, timeout y presupuesto de llamadas."""

    def __init__(
        self,
        plugin_id: str,
        entry: Path,
        *,
        timeout: float = 5.0,
        memory_mb: int = 128,
        max_calls: int = 1000,
        audit=None,
    ) -> None:
        self.plugin_id = plugin_id
        self.entry = entry
        self.timeout = max(0.1, float(timeout))
        self.memory_mb = max(16, int(memory_mb))
        self.max_calls = max(1, int(max_calls))
        self.audit = audit or (lambda *_args: None)
        self.process = None
        self._connection = None
        self._job_handle = None
        self._watchdog_stop = threading.Event()
        self._watchdog_thread = None

    def _resident_memory(self) -> int:
        if self.process is None or self.process.pid is None:
            return 0
        if sys.platform == "win32":
            import ctypes

            class Counters(Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", c_size_t),
                    ("WorkingSetSize", c_size_t),
                    ("QuotaPeakPagedPoolUsage", c_size_t),
                    ("QuotaPagedPoolUsage", c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", c_size_t),
                    ("QuotaNonPagedPoolUsage", c_size_t),
                    ("PagefileUsage", c_size_t),
                    ("PeakPagefileUsage", c_size_t),
                ]

            kernel = ctypes.windll.kernel32
            handle = kernel.OpenProcess(0x0400, False, self.process.pid)
            if not handle:
                return 0
            try:
                counters = Counters()
                counters.cb = sizeof(counters)
                if ctypes.windll.psapi.GetProcessMemoryInfo(
                    handle, byref(counters), sizeof(counters)
                ):
                    return int(counters.WorkingSetSize)
            finally:
                kernel.CloseHandle(handle)
            return 0
        try:
            pages = int(Path(f"/proc/{self.process.pid}/statm").read_text().split()[1])
            return pages * os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError, IndexError):
            return 0

    def _watch_runtime(self) -> None:
        limit = self.memory_mb * 1024 * 1024
        while not self._watchdog_stop.wait(0.1):
            if self.process is None or not self.process.is_alive():
                return
            if self._connection is not None and self._connection.poll():
                try:
                    message = self._connection.recv()
                except (EOFError, OSError):
                    return
                if message[0] == "VIOLATION":
                    self.audit(
                        self.plugin_id,
                        "POLICY VIOLATION",
                        str(message[1]),
                        "BLOCKED",
                        str(message[2]),
                    )
                    self.process.terminate()
                    return
                if message[0] == "CALL" and message[1] == "log":
                    self.audit(self.plugin_id, "ISOLATED LOG", str(message[2][0]), "OK")
            used = self._resident_memory() if self._job_handle is None else 0
            if self._job_handle is None and used > limit:
                self.audit(
                    self.plugin_id,
                    "MEMORY LIMIT",
                    str(used),
                    "ERROR",
                    f"limit={limit}",
                )
                self.process.terminate()
                return

    @property
    def pid(self) -> int | None:
        return self.process.pid if self.process is not None else None

    def start(self) -> IsolatedPluginRuntime:
        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe()
        process = context.Process(
            target=_worker,
            args=(child, self.plugin_id, str(self.entry), self.memory_mb, self.max_calls),
            name=f"LANCTL plugin {self.plugin_id}",
            daemon=True,
        )
        process.start()
        child.close()
        deadline = time.monotonic() + self.timeout
        try:
            self._job_handle = _windows_memory_job(process.pid, self.memory_mb)
            while time.monotonic() < deadline:
                if parent.poll(min(0.05, max(0.0, deadline - time.monotonic()))):
                    message = parent.recv()
                    if message[0] == "CALL" and message[1] == "log":
                        self.audit(self.plugin_id, "ISOLATED LOG", str(message[2][0]), "OK")
                        continue
                    if message[0] == "READY":
                        self.process, self._connection = process, parent
                        _RUNTIMES.add(self)
                        self._watchdog_thread = threading.Thread(
                            target=self._watch_runtime,
                            name=f"LANCTL plugin watchdog {self.plugin_id}",
                            daemon=True,
                        )
                        self._watchdog_thread.start()
                        return self
                    if message[0] == "ERROR":
                        detail = message[2] if len(message) > 2 else message[1]
                        raise RuntimeError(detail)
                    if message[0] == "VIOLATION":
                        self.audit(
                            self.plugin_id,
                            "POLICY VIOLATION",
                            str(message[1]),
                            "BLOCKED",
                            str(message[2]),
                        )
                        raise PermissionError(f"incumplimiento de política: {message[1]}")
                if not process.is_alive():
                    raise RuntimeError("el proceso aislado terminó durante la activación")
            raise TimeoutError(f"timeout activando el plugin aislado {self.plugin_id}")
        except Exception:
            process.terminate()
            process.join(2)
            parent.close()
            raise

    def stop(self) -> None:
        if self.process is None or self._connection is None:
            return
        process, connection = self.process, self._connection
        self._watchdog_stop.set()
        if self._watchdog_thread:
            self._watchdog_thread.join(1)
            self._watchdog_thread = None
        try:
            if process.is_alive():
                connection.send("STOP")
                if connection.poll(self.timeout):
                    connection.recv()
                else:
                    process.terminate()
            process.join(self.timeout)
            if process.is_alive():
                process.kill()
                process.join(2)
        finally:
            connection.close()
            self.process = self._connection = None
            if self._job_handle:
                import ctypes

                ctypes.windll.kernel32.CloseHandle(self._job_handle)
                self._job_handle = None
            _RUNTIMES.discard(self)
