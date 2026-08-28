from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .base import PlatformAdapter, ServiceResult
from .windows_service import SERVICE_NAME


class WindowsPlatform(PlatformAdapter):
    DISPLAY_NAME = "LANCTL Monitor"
    ACCOUNT = r"NT AUTHORITY\LocalService"

    def service(self, action, **kwargs):
        action = str(action).casefold()
        if action == "status":
            return self._status()
        if action in {"install", "uninstall"} and not kwargs.get("confirm"):
            return ServiceResult(
                True, "blocked", "La operación requiere --yes y privilegios de administrador"
            )
        if action == "install":
            return self._install(kwargs)
        if action == "uninstall":
            return self._uninstall()
        if action in {"start", "stop", "restart"}:
            return self._control(action)
        return super().service(action, **kwargs)

    def _install(self, options):
        command = list(options.get("command") or ())
        if not command:
            executable = Path(str(options.get("executable", ""))).expanduser()
            if not executable.is_absolute():
                return ServiceResult(
                    True, "error", "El ejecutable del servicio debe usar una ruta absoluta"
                )
            command = [str(executable), "monitor", "service-host"]
        if not Path(command[0]).is_absolute() or any(
            any(ord(ch) < 32 for ch in str(part)) for part in command
        ):
            return ServiceResult(True, "error", "Comando de servicio no válido")
        data_dir = Path(str(options.get("data_dir", ""))).expanduser()
        if not data_dir.is_absolute():
            return ServiceResult(
                True, "error", "El directorio de datos del servicio debe ser absoluto"
            )
        for child in ("monitoring", "database", "logs", "config"):
            (data_dir / child).mkdir(parents=True, exist_ok=True)
        acl = self._run(["icacls.exe", str(data_dir), "/grant", "*S-1-5-19:(OI)(CI)M", "/T", "/C"])
        if acl.returncode:
            return self._result(
                "error", "No se pudieron preparar los permisos de LocalService", acl
            )
        bin_path = subprocess.list2cmdline(command)
        installed = self._status().detail.get("installed", False)
        verb = "config" if installed else "create"
        arguments = [
            "sc.exe",
            verb,
            SERVICE_NAME,
            f"binPath= {bin_path}",
            "start= auto",
            f"obj= {self.ACCOUNT}",
            f"DisplayName= {self.DISPLAY_NAME}",
        ]
        completed = self._run(arguments)
        if completed.returncode:
            return self._result("error", "No se pudo registrar el servicio", completed)
        self._run(
            [
                "sc.exe",
                "description",
                SERVICE_NAME,
                "Monitorización permanente y acotada de la red LAN",
            ]
        )
        self._run(
            [
                "sc.exe",
                "failure",
                SERVICE_NAME,
                "reset= 86400",
                "actions= restart/5000/restart/15000",
            ]
        )
        if options.get("start", True):
            started = self._control("start")
            if started.status == "error":
                return started
        result = self._status()
        return ServiceResult(True, result.status, "Servicio instalado correctamente", result.detail)

    def _uninstall(self):
        state = self._status()
        if not state.detail.get("installed", False):
            return ServiceResult(
                True, "not-installed", "El servicio no está instalado", state.detail
            )
        if state.detail.get("running"):
            stopped = self._control("stop")
            if stopped.status == "error":
                return stopped
        completed = self._run(["sc.exe", "delete", SERVICE_NAME])
        if completed.returncode:
            return self._result("error", "No se pudo eliminar el servicio", completed)
        return ServiceResult(
            True, "uninstalled", "Servicio desinstalado", self._detail(False, False)
        )

    def _control(self, action):
        state = self._status()
        if not state.detail.get("installed", False):
            return ServiceResult(
                True, "not-installed", "El servicio no está instalado", state.detail
            )
        if action == "restart":
            stopped = self._control("stop")
            if stopped.status == "error":
                return stopped
            return self._control("start")
        running = state.detail.get("running", False)
        if action == "start" and running:
            return ServiceResult(True, "running", "El servicio ya está iniciado", state.detail)
        if action == "stop" and not running:
            return ServiceResult(True, "stopped", "El servicio ya está detenido", state.detail)
        completed = self._run(["sc.exe", action, SERVICE_NAME])
        if completed.returncode:
            return self._result("error", f"No se pudo {action} el servicio", completed)
        expected = action == "start"
        return self._wait(expected)

    def _wait(self, running, timeout=20):
        deadline = time.monotonic() + timeout
        latest = self._status()
        while (
            latest.detail.get("installed")
            and latest.detail.get("running") != running
            and time.monotonic() < deadline
        ):
            time.sleep(0.2)
            latest = self._status()
        if latest.detail.get("running") == running:
            status = "running" if running else "stopped"
            return ServiceResult(True, status, f"Servicio {status}", latest.detail)
        return ServiceResult(
            True, "error", "El servicio no alcanzó el estado esperado", latest.detail
        )

    def _status(self):
        completed = self._run(["sc.exe", "query", SERVICE_NAME])
        output = f"{completed.stdout}\n{completed.stderr}"
        if completed.returncode:
            missing = (
                "1060" in output
                or "does not exist" in output.casefold()
                or "no existe" in output.casefold()
            )
            status = "not-installed" if missing else "error"
            return ServiceResult(
                True, status, output.strip() or "Servicio no disponible", self._detail(False, False)
            )
        running = "RUNNING" in output.upper() or "EN EJECUCIÓN" in output.upper()
        status = "running" if running else "stopped"
        return ServiceResult(True, status, output.strip(), self._detail(True, running))

    @staticmethod
    def _run(arguments):
        try:
            return subprocess.run(
                arguments, capture_output=True, text=True, errors="replace", timeout=30, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return subprocess.CompletedProcess(arguments, 1, "", str(error))

    @staticmethod
    def _result(status, message, completed):
        return ServiceResult(
            True,
            status,
            message,
            {
                "returnCode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            },
        )

    @classmethod
    def _detail(cls, installed, running):
        return {
            "serviceName": SERVICE_NAME,
            "displayName": cls.DISPLAY_NAME,
            "account": cls.ACCOUNT,
            "installed": installed,
            "running": running,
        }
