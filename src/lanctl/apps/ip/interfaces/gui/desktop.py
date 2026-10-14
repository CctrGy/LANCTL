"""LANIP desktop adapter. The legacy RPC contract remains available to remote clients."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from threading import Event

from lanctl.apps.ip.interfaces.gui.main import GuiApi
from lanctl.core.config import load_config
from lanctl.core.progress import ScanProgress
from lanctl.core.projects import (
    activate_project_workspace,
    create_project,
    inspect_project,
    resolve_project_path,
)
from lanctl.core.projects.save_policy import workspace_is_dirty
from lanctl.core.resources import bundled_path


class DesktopProgress(ScanProgress):
    def __init__(self):
        super().__init__(False)
        self.stop = Event()

    def cancelled(self):
        return self.stop.is_set()

    def snapshot(self):
        with self._lock:
            return {"current": self.current, "total": self.total, "found": len(self._found_keys)}


# Explicit allow-list: never expose arbitrary CLI execution through the WebView.
SETTINGS = (
    ("Red", "range", "Red autorizada (CIDR)", "-range"),
    ("Red", "discovery", "Detección: icmp / arp / hybrid", "--discovery"),
    ("Escaneo", "scanProfile", "Perfil: fast / normal / accurate", "--scan-profile"),
    ("Escaneo", "workers", "Procesos concurrentes", "--workers"),
    ("Escaneo", "timeout", "Timeout (segundos)", "--timeout"),
    ("Escaneo", "maxHosts", "Límite de hosts", "--max-hosts"),
    ("Proyectos", "projectsDirectory", "Carpeta de proyectos (auto)", "--projects-directory"),
    ("Proyectos", "projectSaveMode", "Política de guardado", "--save-mode"),
    ("Logs", "errorLogLevel", "Nivel de registro (1-59)", "--error-log-level"),
)


class DesktopApi(GuiApi):
    def __init__(self):
        super().__init__()
        self._scan_progress = DesktopProgress()
        self._running = Event()
        self._closing = False

    def bootstrap(self):
        # Icon registration is also serialized; two concurrent initializations
        # must not replace the same asset while another thread is reading it.
        return self._respond(lambda: super(DesktopApi, self).bootstrap())

    def _serialize(self, device):
        result = super()._serialize(device)
        result["active"] = self._activity.get(device.device_id, False)
        result["editableCnf"] = device.cnf
        result["editRevision"] = self._edit_revision(device)
        return result

    def _edit_revision(self, device):
        return hashlib.sha256(
            json.dumps(self._editable_snapshot(device), sort_keys=True).encode()
        ).hexdigest()

    def update_device(self, selector, values, expected_revision=None):
        def operation():
            from lanctl.apps.ip.interfaces.gui.main import GuiEdit
            from lanctl.core.projects.save_policy import SaveTrigger, save_active_project

            if not isinstance(values, dict) or set(values) - {
                "alias",
                "name",
                "description",
                "cnf",
                "icon",
            }:
                raise ValueError("Campos de edición no válidos.")
            config = load_config()
            database = self._database()
            groups = self._groups(config, database)
            from lanctl.core.file_transaction import locked_files

            with locked_files((database.path, groups.path)):
                device = database.resolve(selector)
                if expected_revision is not None and expected_revision != self._edit_revision(
                    device
                ):
                    raise ValueError(
                        "El elemento cambió en otra sesión. Recarga y revisa los cambios antes de aplicar la edición."
                    )
                before = self._editable_snapshot(device)
                edits = [
                    (key, str(value).strip())
                    for key, value in values.items()
                    if str(value).strip() != before[key]
                ]
                if edits:
                    device = groups.edit_device_fields(device.device_id, edits)
            if edits:
                after = self._editable_snapshot(device)
                history = self._edit_history(database)
                history.undo.append(
                    GuiEdit(
                        device.device_id,
                        device.alias or device.mac,
                        {key: before[key] for key, _ in edits},
                        {key: after[key] for key, _ in edits},
                    )
                )
                del history.undo[:-100]
                history.redo.clear()
                save_active_project(SaveTrigger.CHANGE)
            return {**self._inventory_payload(), "message": "Elemento actualizado"}

        return self._respond(operation)

    def group_action(self, action, name, selector=""):
        def operation():
            from lanctl.core.projects.save_policy import SaveTrigger, save_active_project

            groups = self._groups(load_config(), self._database())
            if action == "create":
                groups.create(name)
            elif action == "add":
                groups.add(name, selector)
            elif action == "remove":
                groups.remove(name, selector)
            else:
                raise ValueError("Acción de grupo no válida.")
            save_active_project(SaveTrigger.CHANGE)
            return {**self._inventory_payload(), "message": "Grupo actualizado"}

        return self._respond(operation)

    def _respond(self, operation):
        # Do not queue stale edits/project changes behind a long-running scan.
        if not self._lock.acquire(blocking=False):
            return {
                "ok": False,
                "error": "Hay una operación en curso; espera o cancela el escaneo.",
            }
        try:
            from lanctl.core.session import task

            with task("LANCTL.GUI.Desktop.Operation"):
                return {"ok": True, **operation()}
        except Exception as error:  # noqa: BLE001 - desktop RPC boundary
            from lanctl.core.errors import errors

            event = errors.from_exception(
                error,
                origin="LANCTL.GUI.Desktop.Response",
                code="GUI.DESKTOP.FAILED",
                level=25 if isinstance(error, InterruptedError) else 43,
                print_output=False,
            )
            return {"ok": False, "error": event.message, "errorId": event.error_id}
        finally:
            self._lock.release()

    def scan_network(self, profile="normal"):
        if not self._lock.acquire(blocking=False):
            return {"ok": False, "error": "Hay una operación en curso."}
        try:
            self._scan_progress = DesktopProgress()
            self._running.set()
            self._activity.clear()
            self._response_ms.clear()
            return super().scan_network(profile)
        finally:
            self._running.clear()
            self._lock.release()

    def scan_status(self):
        return {"ok": True, "running": self._running.is_set(), **self._scan_progress.snapshot()}

    def cancel_scan(self):
        self._scan_progress.stop.set()
        return {"ok": True, "message": "Cancelación solicitada; finalizando las sondas en curso."}

    def project_state(self):
        return self._respond(lambda: {"dirty": workspace_is_dirty(load_config())})

    def _discard_current(self):
        config = load_config()
        if config.get("activeProject") and workspace_is_dirty(config):
            activate_project_workspace(config["activeProject"], refresh=True, discard_changes=True)

    def use_project(self, path, discard=False):
        def operation():
            if workspace_is_dirty(load_config()) and discard is not True:
                raise ValueError("Guarda los cambios pendientes o confirma descartarlos.")
            resolved = resolve_project_path(path, load_config().get("projectsDirectory"))
            inspect_project(resolved)
            if discard is True:
                self._discard_current()
            activate_project_workspace(resolved, discard_changes=discard is True)
            self._activity.clear()
            self._response_ms.clear()
            from lanctl.core.plugins.manager import get_plugin_manager

            get_plugin_manager().events.emit("LANCTL.Project.File.Open", {"path": str(resolved)})
            return {
                **self._projects_payload(),
                **self._inventory_payload(),
                "message": f"Proyecto cargado: {resolved.stem}",
            }

        return self._respond(operation)

    def create_project(self, name, directory="", discard=False):
        def operation():
            if workspace_is_dirty(load_config()) and discard is not True:
                raise ValueError("Guarda los cambios pendientes antes de crear otro proyecto.")
            clean = str(name).strip()
            if not clean or len(clean) > 80 or any(c in clean for c in '/\\:<>"|?*'):
                raise ValueError("Nombre de proyecto no válido.")
            destination = resolve_project_path(
                clean + ".vlf", directory or load_config().get("projectsDirectory")
            )
            # Creation must not copy the active inventory into the new project.
            with tempfile.TemporaryDirectory(prefix="lanip-empty-") as temporary:
                config = dict(load_config())
                config.update(
                    database=str(Path(temporary) / "devices.json"),
                    groups=str(Path(temporary) / "groups.json"),
                    credentials=str(Path(temporary) / "credentials"),
                    log=str(Path(temporary) / "logs"),
                    programLog=str(Path(temporary) / "logs"),
                    databaseLog=None,
                )
                result = create_project(
                    destination, name=clean, config=config, initialize_reserved=False
                )
            if discard is True:
                self._discard_current()
            activate_project_workspace(result["path"], discard_changes=discard is True)
            self._activity.clear()
            self._response_ms.clear()
            return {
                **self._projects_payload(),
                **self._inventory_payload(),
                "message": f"Proyecto vacío creado: {clean}",
            }

        return self._respond(operation)

    def open_terminal(self, selector):
        return self.open_device(selector, "auto")

    def open_device(self, selector, protocol="auto", port=None):
        def operation():
            from lanctl.apps.ip.domain.discovery import require_real_target
            from lanctl.apps.ip.interfaces.cli.commands.open import OPEN_PROTOCOLS

            device = self._database().resolve(selector)
            require_real_target(device)
            if protocol not in OPEN_PROTOCOLS or not device.ip or device.ip == "-":
                raise ValueError("El dispositivo no dispone de un acceso válido.")
            if port is not None and not 1 <= int(port) <= 65535:
                raise ValueError("El puerto debe estar entre 1 y 65535.")
            if getattr(sys, "frozen", False):
                command = [
                    str(
                        Path(sys.executable).with_name(
                            "lanip.exe" if sys.platform == "win32" else "lanip"
                        )
                    )
                ]
            else:
                command = [sys.executable, "-m", "lanctl.apps.ip"]
            project = load_config().get("activeProject")
            if project:
                command.extend(["-project", project])
            command.extend(["open", device.device_id, protocol])
            if port is not None:
                command.extend(["--port", str(int(port))])
            if sys.platform == "win32":
                subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                terminal = shutil.which("x-terminal-emulator") or shutil.which("xterm")
                if not terminal:
                    raise RuntimeError(
                        "Instala x-terminal-emulator o xterm para abrir accesos interactivos."
                    )
                subprocess.Popen([terminal, "-e", *command])
            return {"message": "Acceso abierto en una terminal independiente"}

        return self._respond(operation)

    def open_service(self, selector, service, port):
        protocol = self._interactive_protocol(service)
        return self.open_device(selector, protocol or "unsupported", port)

    def _mutation(self, operation):
        def run():
            from lanctl.core.projects.save_policy import SaveTrigger, save_active_project

            result = operation()
            if result.get("ok", True):
                save_active_project(SaveTrigger.CHANGE)
            return result

        return self._respond(run)

    def delete_device(self, selector, confirmed=False):
        return self._mutation(lambda: super(DesktopApi, self).delete_device(selector, confirmed))

    def undo_edit(self):
        return self._mutation(lambda: self._apply_edit_history(undo=True))

    def redo_edit(self):
        return self._mutation(lambda: self._apply_edit_history(undo=False))

    def get_settings(self):
        def operation():
            config = load_config()
            return {
                "fields": [
                    {"section": section, "key": key, "label": label, "value": config.get(key)}
                    for section, key, label, _ in SETTINGS
                ]
            }

        return self._respond(operation)

    def save_settings(self, values):
        def operation():
            from lanctl.apps.ip.interfaces.cli.main import build_parser

            options = {key: option for _, key, _, option in SETTINGS}
            if not isinstance(values, dict) or set(values) - options.keys():
                raise ValueError("Configuración gráfica no válida.")
            argv = ["settings"]
            for key, value in values.items():
                argv.extend([options[key], str(value)])
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    args = build_parser().parse_args(argv)
                    result = args.handler(args)
            except SystemExit as error:
                raise ValueError("Valores de configuración no válidos.") from error
            if result:
                raise ValueError("No se pudo guardar la configuración.")
            return {"message": "Configuración guardada correctamente"}

        return self._respond(operation)

    def request_close(self, decision="cancel"):
        def operation():
            if decision not in {"save", "discard"}:
                return {"closed": False}
            if decision == "save" and workspace_is_dirty(load_config()):
                saved = self.save_project()
                if not saved["ok"]:
                    return saved
            if decision == "discard":
                config = load_config()
                if config.get("activeProject") and workspace_is_dirty(config):
                    activate_project_workspace(
                        config["activeProject"], refresh=True, discard_changes=True
                    )
            self._closing = True
            if self._window:
                self._window.destroy()
            return {"closed": True}

        return self._respond(operation)


def run_gui():
    try:
        import webview
    except ImportError as error:
        raise RuntimeError('Instala la interfaz gráfica con: pip install -e ".[gui]"') from error
    api = DesktopApi()
    window = webview.create_window(
        "LANIP · Inventario de red",
        bundled_path("gui/index.html").as_uri(),
        js_api=api,
        width=1440,
        height=900,
        min_size=(960, 640),
        background_color="#101820",
    )
    api.attach_window(window)

    def closing():
        if api._closing:
            return True
        window.evaluate_js("desktopClose()")
        return False

    window.events.closing += closing
    from lanctl.apps.access.root_control import RootInterfaceAgent

    def remote_action(command):
        if command.get("action") in {"data-changed", "refresh"}:
            window.evaluate_js("window.desktopDataChanged = true")
        elif command.get("action") == "view" and command.get("value") == "gui":
            window.restore()
            window.show()

    agent = RootInterfaceAgent("gui", remote_action).start()
    try:
        webview.start(debug=False)
    finally:
        agent.stop()
    return 0
