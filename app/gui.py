from __future__ import annotations

import argparse
import base64
import contextlib
import io
import subprocess
import sys
import re
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from threading import RLock

from app import __version__
from app.commands.open import run_open
from app.core.config import load_config, save_config
from app.core.database import DeviceDatabase
from app.core.logger import write_log
from app.core.resources import bundled_path
from app.gui_theme import resolve_theme
from app.plugins.manager import get_plugin_manager
from app.assets.icons import get_icon_manager
from app.projects import (create_project, default_project_directory, inspect_project,
                          resolve_project_path, update_project, verify_project)
from app.services.element_scanner import ElementScanner, parse_ports
from app.services.lan_scanner import local_ipv4


class GuiApi:
    """Small allow-listed bridge between the WebView and LANCTL's core."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._window = None
        self._response_ms: dict[str, float | None] = {}
        self._activity: dict[str, bool] = {}
        try:
            self._local_ip = str(local_ipv4())
        except (OSError, ValueError):
            self._local_ip = ""

    def attach_window(self, window) -> None:
        self._window = window

    def select_project_file(self) -> dict:
        def operation() -> dict:
            if self._window is None:
                raise RuntimeError("la ventana gráfica todavía no está disponible")
            import webview
            selected = self._window.create_file_dialog(
                webview.FileDialog.OPEN, directory=str(default_project_directory()),
                file_types=("Proyecto LANCTL (*.vlf)",), allow_multiple=False,
            )
            return {"path": str(selected[0]) if selected else ""}
        return self._respond(operation)

    def select_project_directory(self) -> dict:
        def operation() -> dict:
            if self._window is None:
                raise RuntimeError("la ventana gráfica todavía no está disponible")
            import webview
            selected = self._window.create_file_dialog(
                webview.FileDialog.FOLDER, directory=str(default_project_directory()),
                allow_multiple=False,
            )
            return {"path": str(selected[0]) if selected else ""}
        return self._respond(operation)

    def bootstrap(self) -> dict:
        self._ensure_device_icons()
        return self._respond(lambda: {
            "version": __version__,
            "theme": resolve_theme(get_plugin_manager().extensions.list("theme")),
            **self._projects_payload(), "icons": self._icons_payload(),
            **self._inventory_payload(),
            "pluginPanels": self._plugin_panels(),
        })

    def list_plugin_panels(self) -> dict:
        return self._respond(lambda: {"pluginPanels": self._plugin_panels()})

    def monitor_data(self) -> dict:
        def operation():
            from app.monitor.database import MonitorDatabase
            from app.monitor.reports import monitor_view
            with MonitorDatabase(load_config()["monitorDatabase"]) as database:return {"data":{"success":True,"code":"OK","message":"","data":monitor_view(database)}}
        return self._respond(operation)

    def plugin_panel_data(self, panel_id: str, context: dict | None = None) -> dict:
        def operation():
            manager=get_plugin_manager(); panels={x.extension_id.casefold():x for x in manager.extensions.list("ui-panel")}
            panel=panels.get(str(panel_id).casefold())
            if not panel: raise ValueError("panel de plugin no disponible")
            function_id=str(panel.specification["dataProvider"])
            if manager.functions.owner(function_id) != panel.owner: raise PermissionError("proveedor ajeno al panel")
            result=manager.functions.call(function_id, dict(context or {}), caller="LANCTL.GUI")
            return {"panelId":panel.extension_id,"data":result.to_dict()}
        return self._respond(operation)

    def plugin_action(self, action_id: str, values: dict | None = None) -> dict:
        def operation():
            manager=get_plugin_manager(); actions={x.extension_id.casefold():x for x in manager.extensions.list("ui-action")}
            action=actions.get(str(action_id).casefold())
            if not action: raise ValueError("acción de plugin no disponible")
            specification=action.specification; function_id=specification["function"]
            if manager.functions.owner(function_id) != action.owner: raise PermissionError("una acción no puede llamar a otro plugin")
            payload=dict(values or {})
            if specification.get("requiresSelection") and not payload.get("itemId"): raise ValueError("la acción requiere selección")
            if specification.get("confirmation") and payload.pop("confirmed",False) is not True: raise PermissionError("confirmación requerida")
            result=manager.functions.call(function_id,payload,caller="LANCTL.GUI")
            return {"result":result.to_dict()}
        return self._respond(operation)

    @staticmethod
    def _plugin_panels() -> list[dict]:
        manager=get_plugin_manager(); actions=manager.extensions.list("ui-action")
        monitor={"id":"lanctl.monitor","owner":"LANCTL","title":"Monitorización","location":"main","order":150,"dataProvider":"LANCTL.Monitor.List","layout":"resource-browser","columns":[{"field":"device_id","label":"Dispositivo","type":"device"},{"field":"presence","label":"Presencia","type":"status"},{"field":"health","label":"Salud","type":"status"},{"field":"latency_ms","label":"Latencia","type":"text"},{"field":"updated_at","label":"Último cambio","type":"date"}],"emptyState":{"title":"Sin datos de monitorización","description":"Inicia una sesión para observar el estado de la red."},"actions":[]}
        return [monitor,*[{"id":x.extension_id,"owner":x.owner,**x.specification,
                 "actions":[{"id":a.extension_id,**a.specification} for a in actions if a.owner==x.owner]}
                for x in manager.extensions.list("ui-panel")]]

    def list_devices(self, query: str = "") -> dict:
        return self._respond(lambda: self._inventory_payload(query))

    def get_device(self, selector: str) -> dict:
        return self._respond(lambda: {"device": self._serialize(self._database().resolve(selector))})

    def update_device(self, selector: str, values: dict) -> dict:
        def operation() -> dict:
            if not isinstance(values, dict):
                raise ValueError("los cambios del dispositivo no son válidos")
            allowed = {"alias", "name", "description", "icon"}
            unknown = set(values) - allowed
            if unknown:
                raise ValueError(f"campos GUI no editables: {', '.join(sorted(unknown))}")
            database = self._database()
            device = database.resolve(selector)
            current_selector = device.device_id
            for field in ("alias", "name", "description"):
                if field in values:
                    device = database.edit_device(current_selector, field, str(values[field]).strip())
            if "icon" in values:
                icon_id = str(values["icon"]).strip().casefold()
                if icon_id:
                    get_icon_manager().get(icon_id)
                device = database.edit_device(current_selector, "icon", icon_id)
            return {"device": self._serialize(device), **self._inventory_payload()}
        return self._respond(operation)

    def scan_network(self, profile: str = "normal") -> dict:
        def operation() -> dict:
            if profile not in {"fast", "normal", "accurate"}:
                raise ValueError("perfil de escaneo GUI no válido")
            from app.cli import build_parser
            args = build_parser().parse_args([
                "list", "--profile", profile, "--no-progress",
                "--format", "json",
            ])
            def capture(rows, activity) -> None:
                for row, active in zip(rows, activity):
                    device_id = str(row.get("deviceId", ""))
                    if device_id:
                        self._response_ms[device_id] = row.get("responseMs")
                        self._activity[device_id] = bool(active)
            args.result_callback = capture
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = args.handler(args)
            if result:
                raise RuntimeError("el escaneo de red no pudo completarse")
            return {**self._inventory_payload(), "message": "Escaneo de red completado"}
        return self._respond(operation)

    def diagnose_device(self, selector: str) -> dict:
        def operation() -> dict:
            config = load_config()
            device = self._database().resolve(selector)
            if device.ip in ("", "-"):
                raise ValueError("el dispositivo no tiene una IP registrada")
            scanner = ElementScanner(timeout=float(config["timeout"]), workers=int(config["workers"]))
            result = scanner.scan(
                device.ip, parse_ports("common"), banners=True, identify=True,
                manufacturer=device.manufacturer,
            )
            write_log(f"GUI DIAGNOSE element={device.device_id} ip={device.ip} reachable={result.reachable}")
            payload = asdict(result)
            payload["open_ports"] = [asdict(port) for port in result.open_ports]
            detected = sorted({port.service for port in result.open_ports if port.service and port.service != "unknown"})
            database = self._database()
            for protocol in detected:
                database.set_protocol(device.device_id, protocol, True)
            payload["detected_protocols"] = detected
            return {"diagnostic": payload}
        return self._respond(operation)

    def get_device_details(self, selector: str) -> dict:
        """Return the stored identity plus a fresh, service-aware port inspection."""
        def operation() -> dict:
            device = self._database().resolve(selector)
            if device.ip in ("", "-"):
                raise ValueError("el dispositivo no tiene una IP registrada")
            diagnostic = self._diagnose(device)
            return {"device": self._serialize(device), "diagnostic": diagnostic}
        return self._respond(operation)

    def list_projects(self) -> dict:
        return self._respond(self._projects_payload)

    def use_project(self, path: str) -> dict:
        def operation() -> dict:
            resolved = resolve_project_path(path, load_config().get("projectsDirectory"))
            verify_project(resolved)
            config = load_config(); config["activeProject"] = str(resolved); save_config(config)
            info = inspect_project(resolved)
            get_plugin_manager().events.emit("LANCTL.Project.File.Open", {"path": str(resolved), "project_id": info.get("id")})
            return {**self._projects_payload(), "message": f"Proyecto cargado: {info.get('name') or resolved.stem}"}
        return self._respond(operation)

    def save_project(self) -> dict:
        def operation() -> dict:
            active = load_config().get("activeProject")
            if not active:
                raise ValueError("no hay un proyecto activo que guardar")
            result = update_project(active)
            return {**self._projects_payload(), "message": f"Proyecto guardado: {Path(result['path']).stem}"}
        return self._respond(operation)

    def create_project(self, name: str, directory: str = "") -> dict:
        def operation() -> dict:
            clean = str(name).strip()
            if not clean or len(clean) > 80:
                raise ValueError("indica un nombre de proyecto válido")
            filename = re.sub(r"[^A-Za-z0-9._ -]+", "", clean).strip(" .") or "Proyecto"
            destination = Path(directory).expanduser() / filename if directory else Path(filename)
            result = create_project(destination, name=clean)
            config = load_config(); config["activeProject"] = result["path"]; save_config(config)
            return {**self._projects_payload(), "message": f"Proyecto creado: {clean}"}
        return self._respond(operation)

    def open_device(self, selector: str, protocol: str = "auto") -> dict:
        def operation() -> dict:
            config = load_config()
            result = run_open(argparse.Namespace(
                selector=selector, protocol=protocol, port=None, path="", dry_run=False,
                database=config["database"], store=config["credentials"],
            ))
            return {"message": "Conexión iniciada", "result": result}
        return self._respond(operation)

    def open_service(self, selector: str, service: str, port: int) -> dict:
        """Open an interactive service using the native client for its protocol."""
        def operation() -> dict:
            device = self._database().resolve(selector)
            if device.ip in ("", "-"):
                raise ValueError("el dispositivo no tiene una IP registrada")
            selected_port = int(port)
            if not 1 <= selected_port <= 65535:
                raise ValueError("el puerto debe estar entre 1 y 65535")
            protocol = self._interactive_protocol(service)
            if protocol is None:
                raise ValueError(f"el servicio {service} no tiene una acción interactiva")
            if protocol == "ssh":
                flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
                subprocess.Popen(
                    ["ssh", "-p", str(selected_port), device.ip], creationflags=flags,
                )
                return {"message": f"Terminal SSH abierta para {device.ip}:{selected_port}"}
            config = load_config()
            run_open(argparse.Namespace(
                selector=device.device_id, protocol=protocol, port=selected_port,
                path="", dry_run=False, database=config["database"],
                store=config["credentials"],
            ))
            return {"message": f"{protocol.upper()} abierto en {device.ip}:{selected_port}"}
        return self._respond(operation)

    def open_terminal(self, selector: str) -> dict:
        def operation() -> dict:
            device = self._database().resolve(selector)
            if not device.protocols:
                raise ValueError("el dispositivo no tiene protocolos configurados")
            if getattr(sys, "frozen", False):
                command = [sys.executable, "terminal", device.device_id]
            else:
                command = [sys.executable, str(Path(__file__).resolve().parents[1] / "main.py"),
                           "terminal", device.device_id]
            flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            subprocess.Popen(command, creationflags=flags)
            return {"message": "Terminal iniciada en una ventana independiente"}
        return self._respond(operation)

    def wake_device(self, selector: str, options: dict | None = None) -> dict:
        def operation() -> dict:
            from app.cli import build_parser
            config = load_config(); values = options if isinstance(options, dict) else {}
            allowed = {"broadcast", "port", "repeat", "interval", "wait", "method", "checkPort"}
            if set(values) - allowed: raise ValueError("opciones WOL GUI no válidas")
            arguments = ["wol", selector, "wakeup", "--json", "--database", config["database"]]
            for key, flag in (("broadcast","--broadcast"),("port","--port"),("repeat","--repeat"),("interval","--interval"),("wait","--wait"),("method","--method"),("checkPort","--check-port")):
                if key in values: arguments.extend((flag, str(values[key])))
            parsed = build_parser().parse_args(arguments); output = io.StringIO()
            with contextlib.redirect_stdout(output): parsed.handler(parsed)
            payload = json.loads(output.getvalue())
            device = self._database().resolve(selector); name = device.alias or device.name or selector
            message = f"{name} está disponible" if payload["status"] == "online" else payload.get("error", {}).get("message", f"Señal de encendido enviada a {name}")
            return {"result": payload, "message": message}
        return self._respond(operation)

    def get_history(self, selector: str = "", filters: dict | None = None) -> dict:
        def operation() -> dict:
            from app.core.history import HistoryService
            values=filters if isinstance(filters,dict) else {}; allowed={"types","source","result","errors","search","limit","reverse"}
            if set(values)-allowed: raise ValueError("filtros de historial no válidos")
            rows=HistoryService().query(selector or None,types=tuple(values.get("types",())),source=values.get("source"),result=values.get("result"),errors=bool(values.get("errors",False)),search=values.get("search"),limit=int(values.get("limit",100)),reverse=bool(values.get("reverse",True)))
            return {"events":[event.to_dict() for event in rows]}
        return self._respond(operation)

    def _respond(self, operation) -> dict:
        try:
            with self._lock:
                return {"ok": True, **operation()}
        except Exception as error:
            write_log(f"GUI ERROR action={getattr(operation, '__name__', 'request')} detail={error}")
            return {"ok": False, "error": str(error)}

    def _diagnose(self, device) -> dict:
        config = load_config()
        scanner = ElementScanner(timeout=float(config["timeout"]), workers=int(config["workers"]))
        result = scanner.scan(
            device.ip, parse_ports("common"), banners=True, identify=True,
            manufacturer=device.manufacturer,
        )
        payload = asdict(result)
        payload["open_ports"] = [
            {**asdict(port), "label": self._service_label(port.service),
             "interactive": self._interactive_protocol(port.service) is not None}
            for port in result.open_ports
        ]
        payload["detected_protocols"] = sorted({
            port.service for port in result.open_ports
            if port.service and port.service != "unknown"
        })
        return payload

    @staticmethod
    def _interactive_protocol(service: str) -> str | None:
        normalized = str(service).strip().casefold()
        aliases = {
            "http-alt": "http", "http-proxy": "http", "upnp/http": "http",
            "https-alt": "https", "ftp-data": "ftp",
        }
        normalized = aliases.get(normalized, normalized)
        return normalized if normalized in {"ssh", "telnet", "http", "https", "ftp", "rdp", "rtsp", "smb"} else None

    @staticmethod
    def _service_label(service: str) -> str:
        labels = {
            "ssh": "SSH · Terminal segura", "telnet": "Telnet · Terminal remota",
            "http": "HTTP · Sitio web", "https": "HTTPS · Sitio web seguro",
            "http-alt": "HTTP · Sitio web", "http-proxy": "HTTP · Web/proxy",
            "https-alt": "HTTPS · Sitio web seguro", "upnp/http": "HTTP · Administración UPnP",
            "ftp": "FTP · Archivos", "ftp-data": "FTP · Datos",
            "rdp": "RDP · Escritorio remoto", "vnc": "VNC · Escritorio remoto",
            "smb": "SMB · Archivos compartidos", "rtsp": "RTSP · Vídeo en red",
            "ipp": "IPP · Impresora", "printer": "LPD · Impresora",
            "printer-raw": "RAW · Impresora", "snmp": "SNMP · Monitorización",
            "dns": "DNS · Resolución de nombres", "mqtt": "MQTT · Mensajería IoT",
            "mqtts": "MQTTS · Mensajería IoT segura",
        }
        clean = str(service or "unknown").casefold()
        return labels.get(clean, clean.upper() if clean != "unknown" else "Servicio desconocido")

    @staticmethod
    def _database() -> DeviceDatabase:
        return DeviceDatabase(load_config()["database"])

    def _inventory_payload(self, query: str = "") -> dict:
        devices = [self._serialize(device) for device in self._database().load()]
        wanted = str(query or "").strip().casefold()
        if wanted:
            devices = [device for device in devices if wanted in " ".join([
                device["alias"], device["name"], device["ip"], device["mac"],
                device["manufacturer"], " ".join(device["groups"]),
            ]).casefold()]
        active = sum(device["active"] for device in devices)
        return {"devices": devices, "summary": {
            "total": len(devices), "active": active,
            "alerts": len(devices) - active,
            "switches": sum("switch" in (device["name"] + " " + device["alias"]).casefold() or "snmp" in device["protocols"] for device in devices),
        }}

    def _serialize(self, device) -> dict:
        active = False
        if device.last_seen:
            try:
                seen = datetime.fromisoformat(device.last_seen)
                now = datetime.now(seen.tzinfo) if seen.tzinfo else datetime.now()
                active = seen >= now - timedelta(minutes=10)
            except ValueError:
                pass
        active = self._activity.get(device.device_id, active)
        return {
            "id": device.device_id, "ip": device.ip, "mac": device.mac,
            "alias": device.alias, "name": device.name,
            "manufacturer": device.manufacturer, "groups": list(device.groups),
            "description": device.description, "protocols": list(device.protocols),
            "wolAvailable": bool(device.mac and device.mac not in {"00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"} and device.protocol_options.get("wol", {}).get("enabled", True)),
            "cnf": "@" if device.ip == self._local_ip else device.cnf,
            "lastDiscovery": device.last_discovery, "lastSeen": device.last_seen,
            "active": active,
            "responseMs": self._response_ms.get(device.device_id),
            "iconId": device.icon_id or self._infer_icon(device),
        }

    def _projects_payload(self) -> dict:
        config = load_config(); configured = config.get("projectsDirectory")
        directory = resolve_project_path("placeholder.vlf", configured).parent if configured else default_project_directory()
        projects = []
        if directory.exists():
            for path in sorted(directory.glob("*.vlf"), key=lambda item: item.name.casefold()):
                try:
                    info = inspect_project(path)
                    projects.append({"path": str(path), "name": info.get("name") or path.stem, "id": info.get("id", "")})
                except (OSError, ValueError):
                    continue
        return {"projects": projects, "activeProject": str(config.get("activeProject") or "")}

    def _ensure_device_icons(self) -> None:
        manager = get_icon_manager(); manager.initialize()
        source = bundled_path("assets/device-icons")
        if not source.exists():
            return
        for path in sorted(source.glob("*.jpg")):
            icon_id = "device." + path.stem
            if any(item.icon_id == icon_id for item in manager.list()):
                continue
            manager.register(path, icon_id=icon_id, name=path.stem.replace("-", " ").title(), category="device", tags=(path.stem,))

    @staticmethod
    def _icons_payload() -> list[dict]:
        result = []
        for entry in get_icon_manager().list(category="device"):
            if not entry.path:
                continue
            encoded = base64.b64encode(entry.path.read_bytes()).decode("ascii")
            result.append({"id": entry.icon_id, "name": entry.name, "data": "data:image/jpeg;base64," + encoded})
        return result

    @staticmethod
    def _infer_icon(device) -> str:
        text = " ".join([device.alias, device.name, device.description, device.manufacturer, *device.groups]).casefold()
        if device.default_alias == "GATEWAY" or "router" in text or "gateway" in text: return "device.router"
        if device.default_alias == "BRODCAST" or "broadcast" in text: return "device.broadcast"
        if "switch" in text or "snmp" in device.protocols: return "device.switch"
        if any(word in text for word in ("laptop", "portatil", "portátil")): return "device.laptop"
        if any(word in text for word in ("mobile", "movil", "móvil", "phone", "tablet")): return "device.mobile-tablet"
        if any(word in text for word in ("nas", "server", "servidor")): return "device.server"
        if any(word in text for word in ("pc", "desktop", "ordenador", "workstation")): return "device.desktop"
        if any(word in text for word in ("iot", "esp", "camera", "cámara")): return "device.iot"
        return "device.generic"


def run_gui() -> int:
    try:
        import webview
    except ImportError as error:
        raise RuntimeError("La GUI requiere pywebview. Instala las dependencias del proyecto.") from error
    index = bundled_path("gui/index.html")
    if not index.is_file():
        raise RuntimeError(f"No se encontraron los recursos de la GUI: {index}")
    api = GuiApi()
    window = webview.create_window("LANCTL", index.as_uri(), js_api=api, width=1480, height=900,
                                   min_size=(1100, 700), background_color="#071522")
    api.attach_window(window)
    webview.start(debug=False)
    return 0
