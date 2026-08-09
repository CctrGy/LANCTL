from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes

from app.core.logger import write_log

SERVICE_NAME = "LANCTLMonitor"
SERVICE_STOPPED = 1
SERVICE_START_PENDING = 2
SERVICE_STOP_PENDING = 3
SERVICE_RUNNING = 4
SERVICE_ACCEPT_STOP = 0x00000001
SERVICE_ACCEPT_SHUTDOWN = 0x00000004
SERVICE_CONTROL_STOP = 1
SERVICE_CONTROL_SHUTDOWN = 5
SERVICE_WIN32_OWN_PROCESS = 0x00000010


class ServiceStatus(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", ctypes.c_ulong),
        ("dwCurrentState", ctypes.c_ulong),
        ("dwControlsAccepted", ctypes.c_ulong),
        ("dwWin32ExitCode", ctypes.c_ulong),
        ("dwServiceSpecificExitCode", ctypes.c_ulong),
        ("dwCheckPoint", ctypes.c_ulong),
        ("dwWaitHint", ctypes.c_ulong),
    ]


CallbackFactory = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
HandlerCallback = CallbackFactory(
    ctypes.c_ulong,
    ctypes.c_ulong,
    ctypes.c_ulong,
    ctypes.c_void_p,
    ctypes.c_void_p,
)
ServiceMainCallback = CallbackFactory(None, ctypes.c_ulong, ctypes.POINTER(ctypes.c_wchar_p))


class ServiceTableEntry(ctypes.Structure):
    _fields_ = [("lpServiceName", ctypes.c_wchar_p), ("lpServiceProc", ServiceMainCallback)]


class WindowsServiceHost:
    """Puente mínimo entre SCM y el bucle cooperativo de MonitorService."""

    def __init__(self, name=SERVICE_NAME):
        self.name = name
        self.stop_event = threading.Event()
        self.status_handle = None
        self.status = ServiceStatus(
            SERVICE_WIN32_OWN_PROCESS, SERVICE_START_PENDING, 0, 0, 0, 1, 15000
        )
        self._handler_callback = HandlerCallback(self._control_handler)
        self._service_callback = None
        self._runner = None

    def run(self, runner):
        if not hasattr(ctypes, "windll"):
            raise OSError("el host SCM sólo está disponible en Windows")
        self._configure_api()
        self._runner = runner
        self._service_callback = ServiceMainCallback(self._service_main)
        table = (ServiceTableEntry * 2)()
        table[0] = ServiceTableEntry(self.name, self._service_callback)
        table[1] = ServiceTableEntry(None, ServiceMainCallback())
        if not self._advapi32.StartServiceCtrlDispatcherW(table):
            raise ctypes.WinError(ctypes.get_last_error())

    def _configure_api(self):
        """Declara tipos de puntero para no truncar handles en Windows x64."""
        self._advapi32 = ctypes.WinDLL("Advapi32", use_last_error=True)
        self._advapi32.StartServiceCtrlDispatcherW.argtypes = [ctypes.POINTER(ServiceTableEntry)]
        self._advapi32.StartServiceCtrlDispatcherW.restype = wintypes.BOOL
        self._advapi32.RegisterServiceCtrlHandlerExW.argtypes = [
            wintypes.LPCWSTR,
            HandlerCallback,
            wintypes.LPVOID,
        ]
        self._advapi32.RegisterServiceCtrlHandlerExW.restype = wintypes.HANDLE
        self._advapi32.SetServiceStatus.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ServiceStatus),
        ]
        self._advapi32.SetServiceStatus.restype = wintypes.BOOL

    def _service_main(self, _argc, _argv):
        self.status_handle = self._advapi32.RegisterServiceCtrlHandlerExW(
            self.name,
            self._handler_callback,
            None,
        )
        if not self.status_handle:
            return
        self._set_status(SERVICE_START_PENDING, checkpoint=1, wait_hint=15000)
        try:
            self._set_status(
                SERVICE_RUNNING, controls=SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN
            )
            self._runner(self.stop_event)
        except Exception as error:  # noqa: BLE001 - frontera del SCM de Windows
            write_log(f"WINDOWS SERVICE ERROR name={self.name} detail={error}")
            self._set_status(SERVICE_STOPPED, win32_exit=1)
        else:
            self._set_status(SERVICE_STOPPED)

    def _control_handler(self, control, _event_type, _event_data, _context):
        if control in {SERVICE_CONTROL_STOP, SERVICE_CONTROL_SHUTDOWN}:
            self._set_status(SERVICE_STOP_PENDING, checkpoint=1, wait_hint=15000)
            self.stop_event.set()
        return 0

    def _set_status(self, state, *, controls=0, checkpoint=0, wait_hint=0, win32_exit=0):
        self.status.dwCurrentState = state
        self.status.dwControlsAccepted = controls
        self.status.dwCheckPoint = checkpoint
        self.status.dwWaitHint = wait_hint
        self.status.dwWin32ExitCode = win32_exit
        if self.status_handle:
            self._advapi32.SetServiceStatus(self.status_handle, ctypes.byref(self.status))
