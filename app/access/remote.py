from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import ClassVar

READ_COMMANDS = {
    "list": "inventory.read",
    "search": "inventory.read",
    "ping": "inventory.read",
    "history": "history.read",
    "smb": "smb.read",
}
WRITE_COMMANDS = {
    "scan": "scan.run",
    "wol": "wol.send",
    "recurrent": "automation.manage",
    "alias": "system.configure",
    "cnf": "system.configure",
    "element": "system.configure",
    "group": "system.configure",
    "name": "system.configure",
    "protocol": "system.configure",
    "settings": "system.configure",
    "switch": "system.configure",
}
MAX_COMMAND_LENGTH = 4096
MAX_ARGUMENTS = 64
MAX_OUTPUT = 1024 * 1024
FORBIDDEN_PATH_OPTIONS = {
    "--assignments-store",
    "--config",
    "--database",
    "--groups",
    "--incidents-store",
    "--lock",
    "--monitor-db",
    "--profiles",
    "--project",
    "--registry",
    "--runtime",
    "--sequences",
    "--sessions",
    "--storage",
    "--store",
    "--users",
}


def required_permission(arguments: list[str]) -> str:
    """Mapea una orden LANCTL a un permiso; nunca habilita una shell del SO."""
    if not arguments:
        raise ValueError("indica un comando LANCTL")
    command = arguments[0].casefold()
    if command in READ_COMMANDS:
        return READ_COMMANDS[command]
    if command in WRITE_COMMANDS:
        return WRITE_COMMANDS[command]
    if command == "monitor":
        action = arguments[1].casefold() if len(arguments) > 1 else "status"
        return (
            "monitor.read" if action in {"status", "list", "show", "report"} else "monitor.control"
        )
    if command == "project":
        action = arguments[1].casefold() if len(arguments) > 1 else "status"
        return (
            "inventory.read"
            if action in {"status", "list", "show", "current"}
            else "project.manage"
        )
    raise PermissionError(f"comando no disponible en acceso remoto: {command}")


def parse_remote_command(command: str) -> list[str]:
    if not isinstance(command, str) or not command.strip():
        raise ValueError("indica un comando LANCTL")
    if len(command) > MAX_COMMAND_LENGTH or any(
        ord(char) < 32 and char not in "\t" for char in command
    ):
        raise ValueError("comando remoto demasiado largo o no valido")
    try:
        arguments = shlex.split(command, posix=True)
    except ValueError as error:
        raise ValueError("sintaxis de comando no valida") from error
    if arguments and arguments[0].casefold() in {"lanctl", "lanctl.exe", "als"}:
        arguments.pop(0)
    if not arguments or len(arguments) > MAX_ARGUMENTS:
        raise ValueError("numero de argumentos no valido")
    if arguments[0].startswith("-"):
        raise PermissionError("las opciones globales no estan disponibles en remoto")
    for argument in arguments[1:]:
        option = argument.casefold().split("=", 1)[0]
        if option in FORBIDDEN_PATH_OPTIONS:
            raise PermissionError(f"ruta de datos no configurable en remoto: {option}")
    return arguments


class LanctlCommandAdapter:
    """Ejecuta exclusivamente subcomandos LANCTL autorizados y sin shell."""

    def __init__(self, authorization, timeout=60, runner=None):
        self.authorization = authorization
        self.timeout = timeout
        self.runner = runner or subprocess.run

    @staticmethod
    def command(arguments: list[str]) -> list[str]:
        if getattr(sys, "frozen", False):
            return [sys.executable, *arguments]
        return [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "main.py"),
            *arguments,
        ]

    def execute(self, user, command: str) -> tuple[int, str]:
        arguments = parse_remote_command(command)
        permission = required_permission(arguments)
        self.authorization.require(user, permission)
        environment = dict(os.environ)
        environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        try:
            completed = self.runner(
                self.command(arguments),
                shell=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                env=environment,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return 124, "Tiempo de ejecucion agotado."
        output = (completed.stdout or "") + (completed.stderr or "")
        if len(output.encode("utf-8")) > MAX_OUTPUT:
            output = output.encode("utf-8")[:MAX_OUTPUT].decode("utf-8", "ignore")
            output += "\n[Salida truncada]"
        return int(completed.returncode), output.rstrip() or f"Resultado: {completed.returncode}"


class RemoteGuiApi:
    """Puente RPC con lista blanca y permisos para la interfaz HTTPS."""

    METHODS: ClassVar[dict[str, tuple[str, str]]] = {
        "bootstrap": ("inventory.read", "bootstrap"),
        "list_devices": ("inventory.read", "list_devices"),
        "get_device": ("inventory.read", "get_device"),
        "get_history": ("history.read", "get_history"),
        "monitor_data": ("monitor.read", "monitor_data"),
        "list_projects": ("inventory.read", "list_projects"),
        "scan_network": ("scan.run", "scan_network"),
        "diagnose_device": ("scan.run", "diagnose_device"),
        "get_device_details": ("scan.run", "get_device_details"),
        "wake_device": ("wol.send", "wake_device"),
        "update_device": ("system.configure", "update_device"),
        "use_project": ("project.manage", "use_project"),
        "save_project": ("project.manage", "save_project"),
        "create_project": ("project.manage", "create_project"),
    }

    def __init__(self, authorization, api=None):
        if api is None:
            from app.gui import GuiApi

            api = GuiApi()
        self.authorization = authorization
        self.api = api

    def call(self, user, method: str, arguments):
        if method == "plugin_panel_data":
            self.authorization.require(user, "smb.read")
            if (
                not isinstance(arguments, list)
                or not arguments
                or arguments[0] != "windows-smb.resources"
            ):
                raise PermissionError("panel de plugin remoto no permitido")
            return self.api.plugin_panel_data(*arguments)
        if method == "plugin_action":
            self.authorization.require(user, "scan.run")
            if (
                not isinstance(arguments, list)
                or not arguments
                or arguments[0] != "windows-smb.scan"
            ):
                raise PermissionError("accion de plugin remota no permitida")
            return self.api.plugin_action(*arguments)
        specification = self.METHODS.get(str(method))
        if specification is None:
            raise PermissionError("metodo remoto no permitido")
        permission, attribute = specification
        self.authorization.require(user, permission)
        if not isinstance(arguments, list) or len(arguments) > 8:
            raise ValueError("argumentos RPC no validos")
        response = getattr(self.api, attribute)(*arguments)
        if method == "bootstrap" and response.get("ok"):
            # La interfaz remota no ejecuta acciones arbitrarias de plugins.
            response["pluginPanels"] = [
                {
                    **item,
                    "actions": [
                        action
                        for action in item.get("actions", [])
                        if action.get("id") == "windows-smb.scan"
                    ],
                }
                for item in response.get("pluginPanels", [])
                if item.get("owner") == "LANCTL" or item.get("id") == "windows-smb.resources"
            ]
            response["remote"] = True
        return response
