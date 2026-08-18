from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
from contextlib import suppress
from pathlib import Path
from uuid import uuid4

from app.core.file_transaction import atomic_write_json, locked_file
from app.core.paths import application_path, data_root


def _control_root() -> Path:
    # En Windows, GUI de usuario y servicio viven en ámbitos de secretos
    # distintos. El canal no contiene credenciales y debe ser común a ambos.
    if os.name == "nt" and getattr(sys, "frozen", False):
        return Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "LANCTL" / "runtime"
    return data_root() / "runtime"


RUNTIME_PATH = _control_root() / "root-interface.json"
COMMAND_PATH = _control_root() / "root-commands.json"
INTERFACE_TIMEOUT = 8.0
VIEWS = {"gui", "tui", "plugins", "projects", "settings"}


def _identity(pid: int):
    try:
        from app.monitor.lifecycle import _process_identity

        return _process_identity(pid)
    except (OSError, ValueError):
        return None


def interface_status(path: Path = RUNTIME_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        pid = int(value["pid"])
        alive = bool(value.get("identity")) and _identity(pid) == value.get("identity")
        fresh = time.time() - float(value.get("heartbeat", 0)) <= INTERFACE_TIMEOUT
        if alive and fresh:
            return {**value, "running": True}
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        pass
    return {"running": False, "mode": None, "pid": None, "interactive": False}


def root_status() -> dict:
    from app.access.service import AccessService
    from app.core.config import load_config

    config = load_config()
    access = AccessService(
        application_path(config["accessConfig"]), application_path(config["accessUsers"])
    ).status()
    interface = interface_status()
    ssh_settings = access["ssh"]
    listening = False
    if ssh_settings.get("enabled") and ssh_settings.get("bind") and ssh_settings.get("port"):
        try:
            with socket.create_connection(
                (ssh_settings["bind"], int(ssh_settings["port"])), timeout=0.25
            ):
                listening = True
        except OSError:
            pass
    backend = bool(listening or access["ssh"].get("running") or access["https"].get("running"))
    ssh_settings["listening"] = listening
    return {
        "backend": {"running": backend, "ssh": access["ssh"], "https": access["https"]},
        "interface": interface,
        "state": f"{interface.get('mode', '').upper()}+BACKEND"
        if interface["running"] and backend
        else interface.get("mode", "").upper()
        if interface["running"]
        else "BACKEND"
        if backend
        else "STOPPED",
    }


def default_forced_view() -> str:
    from app.access.service import AccessService
    from app.core.config import load_config

    config = load_config()
    service = AccessService(
        application_path(config["accessConfig"]), application_path(config["accessUsers"])
    )
    return str(service.config().get("control", {}).get("forcedView", "off"))


def enqueue(action: str, value: str | None = None) -> dict:
    status = interface_status()
    if not status["running"]:
        raise RuntimeError("no hay una GUI/TUI raíz abierta para recibir la orden")
    command = {
        "id": uuid4().hex,
        "action": action,
        "value": value,
        "targetPid": status["pid"],
        "created": time.time(),
    }
    COMMAND_PATH.parent.mkdir(parents=True, exist_ok=True)
    with locked_file(COMMAND_PATH):
        try:
            values = json.loads(COMMAND_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            values = []
        values = [item for item in values if time.time() - item.get("created", 0) < 60]
        values.append(command)
        atomic_write_json(COMMAND_PATH, values)
    return {"queued": True, "commandId": command["id"], "target": status}


def _command(*arguments: str) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, *arguments]
    return [sys.executable, str(Path(__file__).resolve().parents[2] / "main.py"), *arguments]


def forced_view(view: str) -> dict:
    normalized = view.casefold()
    if normalized not in VIEWS:
        raise ValueError("vista no válida: gui, tui, plugins, projects o settings")
    current = interface_status()
    if current["running"] and (current.get("mode") == "tui" or normalized == current.get("mode")):
        return enqueue("view", normalized)
    arguments = ["--gui"] if normalized == "gui" else ["--tui", normalized]
    flags = 0
    if platform.system() == "Windows":
        flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            if normalized == "gui"
            else getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        )
    detached_stdio = normalized == "gui"
    process = subprocess.Popen(
        _command(*arguments),
        creationflags=flags,
        close_fds=True,
        stdin=subprocess.DEVNULL if detached_stdio else None,
        stdout=subprocess.DEVNULL if detached_stdio else None,
        stderr=subprocess.DEVNULL if detached_stdio else None,
    )
    return {
        "launched": True,
        "pid": process.pid,
        "view": normalized,
        "warning": (
            "Un servicio de Windows en Session 0 no puede mostrar ventanas en el escritorio; "
            "usa backend=user o mantén una GUI/TUI agente abierta."
            if os.name == "nt" and not current.get("interactive")
            else ""
        ),
    }


class RootInterfaceAgent:
    def __init__(self, mode: str, handler, runtime_path=RUNTIME_PATH, command_path=COMMAND_PATH):
        self.mode, self.handler = mode, handler
        self.runtime_path, self.command_path = Path(runtime_path), Path(command_path)
        self.pid = os.getpid()
        self.identity = _identity(self.pid)
        self.stop_event = threading.Event()
        self.thread = None

    def _publish(self):
        self.runtime_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(
            self.runtime_path,
            {
                "pid": self.pid,
                "identity": self.identity,
                "mode": self.mode,
                "interactive": True,
                "heartbeat": time.time(),
            },
        )

    def _commands(self):
        with locked_file(self.command_path):
            try:
                values = json.loads(self.command_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                values = []
            mine = [item for item in values if item.get("targetPid") == self.pid]
            remaining = [item for item in values if item.get("targetPid") != self.pid]
            atomic_write_json(self.command_path, remaining)
        return mine

    def _run(self):
        while not self.stop_event.wait(1):
            try:
                self._publish()
                for command in self._commands():
                    self.handler(command)
            except (OSError, ValueError):
                continue

    def start(self):
        self._publish()
        self.thread = threading.Thread(target=self._run, name="lanctl-root-control", daemon=True)
        self.thread.start()
        return self

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(2)
        current = interface_status(self.runtime_path)
        if current.get("pid") == self.pid:
            with suppress(OSError):
                self.runtime_path.unlink()
