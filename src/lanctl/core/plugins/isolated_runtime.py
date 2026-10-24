from __future__ import annotations

import atexit
import importlib.machinery
import importlib.util
import json
import math
import multiprocessing
import os
import queue
import sys
import threading
import time
from contextlib import suppress
from ctypes import Structure, byref, c_size_t, sizeof, wintypes
from pathlib import Path
from types import ModuleType

_RUNTIMES: set[IsolatedPluginRuntime] = set()
_MAX_MESSAGE_BYTES = 64 * 1024


def _send_message(connection, message) -> None:
    payload = json.dumps(message, ensure_ascii=True, allow_nan=False).encode("utf-8")
    if len(payload) > _MAX_MESSAGE_BYTES:
        raise ValueError("mensaje IPC de plugin demasiado grande")
    connection.send_bytes(payload)


def _receive_message(connection):
    # Nunca usar Connection.recv(): el emisor es código externo y pickle
    # ejecuta constructores antes de que el host pueda validar el mensaje.
    try:
        message = json.loads(connection.recv_bytes(_MAX_MESSAGE_BYTES).decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ValueError("mensaje IPC de plugin no válido") from error
    valid = False
    if isinstance(message, list) and message:
        kind = message[0]
        if kind in ("BOOTED", "READY", "STOPPED"):
            valid = len(message) == 2 and type(message[1]) is int and message[1] > 0
        elif kind in ("ERROR", "VIOLATION"):
            valid = len(message) == 3 and all(isinstance(x, str) for x in message[1:])
        elif kind == "CALL":
            valid = (
                len(message) == 3
                and message[1] == "log"
                and isinstance(message[2], list)
                and len(message[2]) == 1
                and isinstance(message[2][0], str)
            )
        elif kind == "STOP":
            valid = len(message) == 1
    if not valid:
        raise ValueError("contrato IPC de plugin no válido")
    return message


class _MessageReader:
    """Un frame incompleto no bloquea los plazos del padre ni el watchdog."""

    def __init__(self, connection, receive=None):
        self.connection = connection
        self._receive = receive or _receive_message
        self.messages = queue.Queue(maxsize=1)
        self.closed = threading.Event()
        self.pending = None
        self.thread = threading.Thread(target=self._read, name="LANCTL plugin IPC", daemon=True)
        self.thread.start()

    def _read(self):
        while not self.closed.is_set():
            try:
                item = (True, self._receive(self.connection))
            except (EOFError, OSError, ValueError) as error:
                item = (False, error)
            while not self.closed.is_set():
                try:
                    self.messages.put(item, timeout=0.1)
                    break
                except queue.Full:
                    continue
            if not item[0]:
                return

    def poll(self, timeout=0):
        if self.pending is None:
            try:
                self.pending = self.messages.get(timeout=timeout)
            except queue.Empty:
                return False
        return True

    def receive(self):
        if not self.poll():
            raise RuntimeError("no hay un mensaje IPC completo disponible")
        succeeded, value = self.pending
        self.pending = None
        if not succeeded:
            raise value
        return value

    def close(self):
        self.closed.set()
        self.thread.join(1)


class IsolatedPolicyViolation(PermissionError):
    """Operación del sistema prohibida para un plugin aislado."""


def _stop_all() -> None:
    for runtime in list(_RUNTIMES):
        runtime.stop()


atexit.register(_stop_all)


def _windows_kernel():
    import ctypes

    kernel = ctypes.windll.kernel32
    for name, arguments, result in (
        ("CreateJobObjectW", [ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
        ("OpenProcess", [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        (
            "SetInformationJobObject",
            [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD],
            wintypes.BOOL,
        ),
        ("AssignProcessToJobObject", [wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
        ("CloseHandle", [wintypes.HANDLE], wintypes.BOOL),
    ):
        function = getattr(kernel, name)
        function.argtypes, function.restype = arguments, result
    return kernel


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

    kernel = _windows_kernel()
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

    def __init__(self, connection, plugin_id: str, max_calls: int, settings=None) -> None:
        self.connection = connection
        self.plugin_id = plugin_id
        self.remaining = max_calls
        self.settings = dict(settings or {})

    def log(self, message: str) -> None:
        self._call("log", str(message))

    def _call(self, method: str, *arguments) -> None:
        if self.remaining <= 0:
            raise RuntimeError("límite de llamadas del plugin agotado")
        self.remaining -= 1
        _send_message(self.connection, ("CALL", method, arguments))


def _apply_memory_limit(megabytes: int) -> None:
    if sys.platform == "win32":
        return
    try:
        import resource

        limit = max(16, megabytes) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    except (ImportError, OSError, ValueError):
        return


def _install_security_policy(connection, plugin_root: Path, report=None) -> None:
    """Bloquea filesystem, red, procesos y registro fuera de la API aislada."""

    readable_roots = tuple(
        path.resolve()
        for path in {plugin_root, Path(sys.base_prefix), Path(sys.prefix)}
        if path.exists()
    )
    denied_events = {
        "ctypes.dlopen",
        "os.exec",
        "os.fork",
        "os.forkpty",
        "os.kill",
        "os.killpg",
        "os.posix_spawn",
        "os.spawn",
        "os.startfile",
        "os.startfile/2",
        "os.system",
        "pty.spawn",
        "signal.pthread_kill",
        "socket.__new__",
        "socket.bind",
        "socket.connect",
        "socket.getaddrinfo",
        "subprocess.Popen",
        "_winapi.CreateProcess",
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
            if report is None:
                _send_message(connection, ("VIOLATION", event, str(detail)[:512]))
            else:
                report(event, str(detail)[:512])
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


def _watch_parent():
    """Do not leave native threads orphaned when the host disappears."""
    parent = multiprocessing.parent_process()
    if parent is not None:

        def watch():
            while True:
                time.sleep(0.2)
                if not parent.is_alive():
                    os._exit(1)

        threading.Thread(target=watch, name="plugin parent watcher", daemon=True).start()


def _worker(
    connection, plugin_id: str, entry: str, memory_mb: int, max_calls: int, settings=None
) -> None:
    _apply_memory_limit(memory_mb)
    _watch_parent()
    module: ModuleType | None = None
    try:
        _install_security_policy(connection, Path(entry).resolve().parent)
        # El arranque mediante ``spawn`` puede ser sensiblemente más lento que
        # el presupuesto concedido al código del plugin (especialmente en
        # Windows). Este handshake permite que el padre empiece a contar el
        # timeout justo antes de cargar y activar código externo.
        _send_message(connection, ("BOOTED", os.getpid()))
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
        activate(_IsolatedApi(connection, plugin_id, max_calls, settings))
        _send_message(connection, ("READY", os.getpid()))
        while True:
            try:
                command = _receive_message(connection)
            except EOFError:
                return
            if command == ["STOP"]:
                deactivate = getattr(module, "deactivate", None)
                if callable(deactivate):
                    deactivate()
                _send_message(connection, ("STOPPED", os.getpid()))
                return
    except Exception as error:  # noqa: BLE001 - frontera de código externo
        try:
            kind = "VIOLATION" if isinstance(error, IsolatedPolicyViolation) else "ERROR"
            _send_message(connection, (kind, type(error).__name__, str(error)[:4096]))
        except (BrokenPipeError, EOFError, OSError, ValueError):
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
        settings=None,
    ) -> None:
        self.plugin_id = plugin_id
        self.entry = entry
        timeout = float(timeout)
        if not math.isfinite(timeout):
            raise ValueError("el timeout del plugin debe ser finito")
        self.timeout = max(0.1, timeout)
        self.memory_mb = max(16, int(memory_mb))
        self.max_calls = max(1, int(max_calls))
        self.audit = audit or (lambda *_args: None)
        self.settings = dict(settings or {})
        self.process = None
        self._connection = None
        self._reader = None
        self._job_handle = None
        self._watchdog_stop = threading.Event()
        self._watchdog_thread = None
        self._calls = 0
        self._stop_lock = threading.Lock()

    def _log_call(self, message) -> None:
        self._calls += 1
        if self._calls > self.max_calls:
            raise RuntimeError("límite de llamadas del plugin agotado")
        self.audit(self.plugin_id, "ISOLATED LOG", message[2][0], "OK")

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

            kernel = _windows_kernel()
            handle = kernel.OpenProcess(0x0400, False, self.process.pid)
            if not handle:
                return 0
            try:
                counters = Counters()
                counters.cb = sizeof(counters)
                memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
                memory_info.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
                memory_info.restype = wintypes.BOOL
                if memory_info(handle, byref(counters), sizeof(counters)):
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
            if self._reader is not None and self._reader.poll():
                try:
                    message = self._reader.receive()
                    if message[0] == "CALL":
                        self._log_call(message)
                    elif message[0] not in ("VIOLATION", "ERROR"):
                        raise ValueError("mensaje IPC inesperado tras activar el plugin")
                except (EOFError, OSError, ValueError, RuntimeError) as error:
                    self.audit(self.plugin_id, "POLICY VIOLATION", "IPC", "BLOCKED", str(error))
                    self.process.terminate()
                    return
                if message[0] in ("VIOLATION", "ERROR"):
                    self.audit(
                        self.plugin_id,
                        "POLICY VIOLATION",
                        str(message[1]),
                        "BLOCKED",
                        str(message[2]),
                    )
                    self.process.terminate()
                    return
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
        self._calls = 0
        self._watchdog_stop.clear()
        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe()
        process = context.Process(
            target=_worker,
            args=(
                child,
                self.plugin_id,
                str(self.entry),
                self.memory_mb,
                self.max_calls,
                self.settings,
            ),
            name=f"LANCTL plugin {self.plugin_id}",
            daemon=True,
        )
        try:
            process.start()
        except Exception:
            child.close()
            parent.close()
            raise
        child.close()
        reader = _MessageReader(parent)
        self.process, self._connection, self._reader = process, parent, reader
        _RUNTIMES.add(self)
        # El presupuesto del manifiesto limita exclusivamente la carga y la
        # activación del plugin. El bootstrap de multiprocessing es trabajo del
        # host y dispone de un margen independiente y acotado.
        startup_deadline = time.monotonic() + max(5.0, self.timeout)
        activation_deadline: float | None = None
        try:
            self._job_handle = _windows_memory_job(process.pid, self.memory_mb)
            while True:
                deadline = activation_deadline or startup_deadline
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    if activation_deadline is None:
                        raise TimeoutError(f"timeout iniciando el proceso aislado {self.plugin_id}")
                    raise TimeoutError(f"timeout activando el plugin aislado {self.plugin_id}")
                if reader.poll(min(0.05, remaining)):
                    message = reader.receive()
                    if message[0] == "BOOTED":
                        if activation_deadline is not None or message[1] != process.pid:
                            raise ValueError("handshake IPC de plugin no válido")
                        # Un pequeño margen cubre la entrega del mensaje de
                        # política del hijo sin convertirla erróneamente en un
                        # timeout del host bajo carga alta.
                        activation_deadline = time.monotonic() + self.timeout + 0.25
                        continue
                    if message[0] == "CALL" and message[1] == "log":
                        self._log_call(message)
                        continue
                    if message[0] == "READY":
                        if activation_deadline is None or message[1] != process.pid:
                            raise ValueError("handshake IPC de plugin no válido")
                        self.process, self._connection = process, parent
                        self._reader = reader
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
                    raise ValueError("mensaje IPC inesperado durante la activación")
                if not process.is_alive():
                    raise RuntimeError("el proceso aislado terminó durante la activación")
        except Exception:
            self.stop()
            raise

    def _close_job(self):
        if self._job_handle:
            _windows_kernel().CloseHandle(self._job_handle)
            self._job_handle = None

    def stop(self) -> None:
        with self._stop_lock:
            self._stop_process()

    def _stop_process(self) -> None:
        if self.process is None or self._connection is None:
            return
        process, connection = self.process, self._connection
        self._watchdog_stop.set()
        if self._watchdog_thread and self._watchdog_thread is not threading.current_thread():
            self._watchdog_thread.join(1)
            self._watchdog_thread = None
        if process.is_alive():
            with suppress(EOFError, OSError, ValueError):
                _send_message(connection, ["STOP"])
                if self._reader.poll(min(self.timeout, 0.2)):
                    self._reader.receive()
        process.join(min(self.timeout, 0.2))
        if process.is_alive():
            process.terminate()
            process.join(0.5)
        if process.is_alive():
            process.kill()
            process.join(0.5)
        if process.is_alive():
            # Keep ownership and allow an explicit retry; a finished cleanup
            # thread alone is never evidence that executable code has stopped.
            raise RuntimeError("no se ha confirmado la terminación del plugin aislado")
        self._reader.close()
        self._reader = None
        connection.close()
        self.process = self._connection = None
        self._close_job()
        _RUNTIMES.discard(self)
