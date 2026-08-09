from __future__ import annotations

import json
import os
import platform
import signal
import subprocess
import sys
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import ClassVar

from app.core.conditions import duration
from app.core.config import load_config, save_config
from app.core.database import DeviceDatabase
from app.core.history import HistoryService
from app.core.paths import application_path, data_root
from app.monitor.configuration import (
    AssignmentManager,
    ConfigProvider,
    MonitorProfile,
    ProfileManager,
    parse_duration,
    validate_monitor_settings,
)
from app.monitor.database import IncidentRepository as SqlIncidentRepository
from app.monitor.database import MetricsStore, MonitorDatabase
from app.monitor.database import SessionRepository as SqlSessionRepository
from app.monitor.incidents import IncidentManager
from app.monitor.lifecycle import SingletonLock
from app.monitor.models import MonitorTargetPlan
from app.monitor.operations import (
    BoundedRunner,
    identify_target,
    ping_targets,
    scan_target,
)
from app.monitor.reports import ReportBuilder
from app.monitor.service import MonitorService
from app.monitor.sessions import SessionManager


def register_monitor_command(commands):
    config = load_config()
    command = commands.add_parser("monitor", help="Opera sesiones y checks del monitor LAN.")
    command.add_argument(
        "words",
        nargs="*",
        help="attach, detach, status, once, session, incidents, incident, service o foreground.",
    )
    command.add_argument("--project")
    command.add_argument("--permanent", action="store_true")
    command.add_argument("--duration")
    command.add_argument(
        "--mode", choices=("permanent", "temporary", "diagnostic", "once"), default="temporary"
    )
    command.add_argument(
        "--authority", choices=("observe", "operate", "administer"), default="observe"
    )
    command.add_argument("--json", action="store_true")
    command.add_argument("--yes", action="store_true")
    command.add_argument("--interval")
    command.add_argument("--every")
    command.add_argument("--group")
    command.add_argument(
        "--type", choices=("presence", "services", "ports", "identity", "smb", "full")
    )
    command.add_argument("--fast", action="store_true")
    command.add_argument("--unknown", action="store_true")
    command.add_argument("--follow", action="store_true")
    command.add_argument(
        "--sessions", default=config["monitorRuntime"], help="Estado runtime de sesiones."
    )
    command.add_argument(
        "--incidents-store",
        default=config["monitorIncidents"],
        help="Estado runtime de incidencias.",
    )
    command.add_argument(
        "--lock", default=config["monitorLock"], help="Lock singleton del monitor."
    )
    command.add_argument(
        "--monitor-db", default=config["monitorDatabase"], help="Repositorio SQLite del monitor."
    )
    command.add_argument(
        "--profiles", default=config["monitorProfiles"], help="Perfiles personalizados."
    )
    command.add_argument(
        "--assignments-store",
        default=config["monitorAssignments"],
        help="Asignaciones persistentes.",
    )
    command.add_argument("--profile", help="Perfil monitor.")
    command.add_argument(
        "--priority",
        choices=("low", "normal", "high", "critical"),
        default="normal",
        help="Prioridad de asignación.",
    )
    command.add_argument("--check", action="append", default=[], help="Check ping, arp o port:NN.")
    command.add_argument("--presence", help="Intervalo de presencia.")
    command.add_argument("--discovery", help="Intervalo de descubrimiento.")
    command.add_argument("--services", help="Intervalo de servicios.")
    command.add_argument("--deep", help="Intervalo profundo.")
    command.add_argument("--workers", type=int, help="Workers del perfil.")
    command.add_argument("--timeout", type=float, help="Timeout del perfil.")
    for action in command._actions:
        if action.help is None:
            action.help = "Opción operativa del monitor."
    command.set_defaults(handler=run_monitor)


def _database(args):
    return MonitorDatabase(application_path(args.monitor_db))


def run_monitor(args):
    words = [x.casefold() for x in args.words]
    action = words[0] if words else "status"
    config = load_config()
    # Una sola conexión por comando evita descriptores huérfanos y garantiza
    # la reversión y el cierre incluso si una acción termina con una excepción.
    with _database(args) as database:
        sessions = SessionManager(SqlSessionRepository(database))
        payload = _run_monitor_action(args, sessions, config, words, action)

    print(
        json.dumps(payload, indent=2, ensure_ascii=False)
        if args.json or isinstance(payload, (dict, list))
        else payload
    )
    return (
        1
        if isinstance(payload, dict)
        and payload.get("status") in {"unsupported", "error", "blocked"}
        else 0
    )


def _start_monitor(args, sessions, config, action):
    project = args.project or (
        args.words[1] if action == "attach" and len(args.words) > 1 else config.get("activeProject")
    )
    if not project:
        raise ValueError("indica --project o un proyecto activo")
    if args.authority != "observe":
        raise PermissionError(
            "operate/administer requiere una identidad de LAN confirmada por el proveedor de "
            "configuración"
        )
    seconds = duration(args.duration) if args.duration else None
    mode = "permanent" if args.permanent else args.mode
    session = sessions.start(
        platform.node() or "manager",
        str(project),
        mode=mode,
        authority=args.authority,
        duration=seconds,
    )
    process = _spawn_foreground(args)
    return {**asdict(session), "processId": process.pid}


def _stop_monitor(args, sessions):
    state = SingletonLock(application_path(args.lock)).status()
    if state.get("running"):
        os.kill(state["pid"], signal.SIGTERM)
    return asdict(sessions.stop("cancelled"))


def _monitor_status(args, sessions):
    active = sessions.repository.active()
    process = SingletonLock(application_path(args.lock)).status()
    return {"status": asdict(active) if active else None, "process": process}


def _monitor_once(args, sessions, config):
    if args.authority != "observe":
        raise PermissionError("monitor once solo permite observe sin identidad de LAN confirmada")
    project = args.project or config.get("activeProject") or "-"
    session = sessions.start(
        platform.node() or "manager", str(project), mode="once", authority=args.authority
    )
    from app.monitor.checks import availability

    store = MetricsStore(sessions.repository.db)
    results = []
    for device in DeviceDatabase(config["database"]).load():
        if not device.ip or device.ip == "-":
            continue
        checked = availability(device, float(config.get("timeout", 0.8)))
        store.write(checked, session.sessionId)
        results.append(asdict(checked))
    session.status = "completed"
    sessions.repository.save(session)
    report = ReportBuilder(
        sessions.repository.db,
        sessions.repository,
        SqlIncidentRepository(sessions.repository.db),
        config.get("activeProject"),
    ).completed(session)
    return {"session": asdict(session), "checks": results, "report": report}


def _required_word(words, index, message):
    if len(words) <= index:
        raise ValueError(message)
    return words[index]


def _incident_action(args, sessions, words, action):
    manager = IncidentManager(SqlIncidentRepository(sessions.repository.db))
    if action == "incidents":
        return [asdict(item) for item in manager.repository.list()]

    incident_id = _required_word(args.words, 1, "indica el identificador de incidencia")
    if len(args.words) == 2:
        incident = next(
            (item for item in manager.repository.list() if item.incidentId == incident_id), None
        )
        if incident is None:
            raise ValueError("incidencia no encontrada")
        return asdict(incident)

    verb = _required_word(words, 2, "indica acknowledge o close")
    if verb == "acknowledge":
        return asdict(manager.acknowledge(incident_id))
    if verb == "close":
        return asdict(manager.close(incident_id))
    raise ValueError("acción de incidencia no válida")


def _configure_monitor(args, config, words):
    monitor = dict(config.get("monitor", {}))
    mode = words[1] if len(words) > 1 else args.mode
    if mode == "temporary":
        mode = "diagnostic"
    monitor.update({"enabled": True, "mode": mode, "authority": args.authority})
    optional_values = {
        "profile": args.profile,
        "duration": args.duration,
        "workers": args.workers,
        "timeout": args.timeout,
    }
    monitor.update({key: value for key, value in optional_values.items() if value is not None})
    validate_monitor_settings(monitor)
    config["monitor"] = monitor
    save_config(config)
    return {"monitor": monitor}


def _profile_action(args, words):
    manager = ProfileManager(application_path(args.profiles))
    verb = words[1] if len(words) > 1 else "list"
    if verb == "list":
        return [asdict(item) for item in manager.list()]

    name = _required_word(words, 2, f"monitor profile {verb} requiere un nombre")
    if verb == "show":
        return asdict(manager.profile(name))
    if verb in {"create", "update"}:
        base = manager.profile(name) if verb == "update" else MonitorProfile(name)
        profile = MonitorProfile(
            name,
            parse_duration(args.presence) if args.presence else base.presence_interval,
            base.critical_interval,
            parse_duration(args.discovery) if args.discovery else base.discovery_interval,
            parse_duration(args.services) if args.services else base.services_interval,
            parse_duration(args.deep) if args.deep else base.deep_interval,
            args.timeout or base.timeout,
            args.workers or base.workers,
            base.jitter,
            base.failure_threshold,
            base.recovery_threshold,
        )
        manager.save(profile)
        return asdict(profile)
    if verb == "delete":
        manager.delete(name)
        return {"deleted": name}
    raise ValueError("acción de perfil no válida")


def _assignment_checks(args):
    checks = []
    for item in args.check:
        kind, _, argument = item.partition(":")
        spec = {"type": "port" if kind == "port" else kind, "interval": args.every or "60s"}
        if argument and kind == "port":
            spec["args"] = {"port": int(argument)}
        elif argument and kind == "service":
            spec["args"] = {"port": int(argument)} if argument.isdigit() else {"service": argument}
        checks.append(spec)
    return checks


def _assignment_action(args, config, action):
    manager = AssignmentManager(application_path(args.assignments_store))
    if action == "assignments":
        return [asdict(item) for item in manager.list()]
    if action == "unassign":
        selector = _required_word(args.words, 1, "monitor unassign requiere una asignación")
        manager.unassign(selector)
        return {"deleted": selector}

    selector = args.words[1] if len(args.words) > 1 else ""
    group = args.group or ""
    if not selector and not group:
        raise ValueError("monitor assign requiere un elemento o --group")
    device_id = ""
    if not group:
        device_id = DeviceDatabase(config["database"]).resolve(selector).device_id
    assignment = manager.assign(
        selector or group,
        device_id=device_id,
        group=group,
        priority=args.priority,
        profile=args.profile or "",
        checks=_assignment_checks(args),
    )
    return asdict(assignment)


def _report_action(args, sessions, config, words, action):
    database = sessions.repository.db
    repository = sessions.repository
    builder = ReportBuilder(
        database, repository, SqlIncidentRepository(database), config.get("activeProject")
    )
    if action == "session" and words[1] == "list":
        return [asdict(item) for item in repository.list()]

    rows = repository.list()
    if not rows:
        raise ValueError("no hay sesiones de monitor")
    identity = (
        _required_word(words, 2, "indica la sesión del informe")
        if action == "session"
        else words[1]
        if len(words) > 1 and words[1] != "latest"
        else rows[0].sessionId
    )
    report = builder.build(repository.get(identity))
    return report if args.json else {"report": builder.human(report), "data": report}


def _service_action(args, config, words):
    project = args.project or config.get("activeProject") or ""
    command = _lanctl_command(
        "monitor",
        "service-host",
        "--monitor-db",
        str(application_path(args.monitor_db)),
        "--profiles",
        str(application_path(args.profiles)),
        "--assignments-store",
        str(application_path(args.assignments_store)),
        "--lock",
        str(application_path(args.lock)),
    )
    if project:
        command.extend(("--project", str(project)))
    result = _platform().service(
        words[1] if len(words) > 1 else "status",
        confirm=args.yes,
        executable=sys.executable,
        command=command,
        data_dir=str(data_root()),
        project=project,
    )
    return asdict(result)


def _service_host_action(args, sessions):
    if platform.system() != "Windows":
        raise RuntimeError(
            "service-host sólo puede iniciarlo el Service Control Manager de Windows"
        )
    os.environ["LANCTL_DATA_SCOPE"] = "service"
    from app.platform.windows_service import WindowsServiceHost

    WindowsServiceHost().run(
        lambda stop: _run_foreground(args, sessions, stop, service_managed=True)
    )
    return {"status": "completed", "service": "LANCTLMonitor"}


def _ping_action(args, sessions, config):
    inventory = DeviceDatabase(config["database"])
    selector = args.words[1] if len(args.words) > 1 else None
    targets = _targets(inventory, selector, args.group)
    interval = parse_duration(args.interval or "2s")
    span = parse_duration(args.duration or "10m")
    session = sessions.repository.active()
    owned = session is None
    if owned:
        session = sessions.start(
            platform.node() or "manager",
            str(config.get("activeProject") or "-"),
            mode="diagnostic",
            authority="observe",
            duration=span,
        )
    try:
        payload = ping_targets(
            targets,
            MetricsStore(sessions.repository.db),
            session.sessionId,
            interval=interval,
            duration=span,
            timeout=float(config.get("timeout", 0.8)),
        )
    except KeyboardInterrupt:
        payload = {"status": "cancelled", "samples": 0}
    if owned:
        session.status = "cancelled" if payload["status"] == "cancelled" else "completed"
        sessions.repository.save(session)
    return payload


def _smb_scan(args, config):
    from app.plugins.manager import get_plugin_manager

    manager = get_plugin_manager()
    plugin_id = "lanctl.discovery.windows-smb"
    installed = {item.manifest.plugin_id for item in manager.list()}
    plugin = manager.get(plugin_id) if plugin_id in installed else None
    if not plugin or plugin.state.value != "ENABLED":
        return {
            "status": "unsupported",
            "operationId": "monitor.scan.smb",
            "message": "El proveedor SMB no está habilitado",
        }

    from app.plugins.smb_runtime import SMBService

    selector = args.words[1] if len(args.words) > 1 else None
    targets = _targets(DeviceDatabase(config["database"]), selector, args.group)
    service = SMBService()
    return {
        "status": "completed",
        "results": [
            service.inspect(target, timeout=float(config.get("timeout", 0.8)))[0]
            for target in targets
        ],
    }


def _scan_action(args, config):
    scan_type = args.type or "presence"
    if scan_type == "smb":
        return _smb_scan(args, config)

    selector = args.words[1] if len(args.words) > 1 else None
    targets = _targets(DeviceDatabase(config["database"]), selector, args.group)
    every = parse_duration(args.every) if args.every else 1
    span = parse_duration(args.duration) if args.duration else 0
    results = []

    def scan_all():
        results.extend(
            scan_target(
                target,
                scan_type,
                float(config.get("timeout", 0.8)),
                int(config.get("workers", 32)),
            )
            for target in targets
        )
        return True

    try:
        BoundedRunner().run(scan_all, interval=every, duration=span)
    except KeyboardInterrupt:
        return {"status": "cancelled", "results": results}
    return {"status": "completed", "type": scan_type, "results": results}


def _identify_action(args, config):
    inventory = DeviceDatabase(config["database"])
    timeout = min(float(config.get("timeout", 0.8)), 0.5 if args.fast else 2)
    if len(args.words) > 1:
        targets = [inventory.resolve(args.words[1])]
    elif args.unknown:
        from app.services.lan_scanner import LanScanner, resolve_network

        scanner = LanScanner(
            resolve_network(config.get("range")),
            min(int(config.get("workers", 32)), 64),
            timeout,
            int(config.get("maxHosts", 4096)),
            config.get("scanOrder", "ascending"),
        )
        discovered = scanner.scan(
            include_unknown=True,
            resolve_names=not args.fast,
            discovery="hybrid",
            include_arp_cache=True,
        )
        known_macs = {device.mac.casefold() for device in inventory.load() if device.mac}
        targets = [
            device
            for device in discovered
            if not device.mac or device.mac.casefold() not in known_macs
        ]
    else:
        targets = inventory.load()

    results = [identify_target(target, timeout) for target in targets]
    if args.unknown:
        results = [
            item for item in results if item["confidence"] in {"unknown", "conflict", "medium"}
        ]
    return {
        "status": "completed",
        "operationId": "monitor.network.identify",
        "results": results,
    }


def _health_action(args, sessions, config):
    selector = args.words[1] if len(args.words) > 1 else None
    database = sessions.repository.db
    if not selector:
        from app.monitor.reports import monitor_view

        return monitor_view(database)

    device = DeviceDatabase(config["database"]).resolve(selector)
    state = database.execute(
        "SELECT * FROM device_state WHERE device_id=?", (device.device_id,)
    ).fetchone()
    samples = database.execute(
        "SELECT COUNT(*) samples,AVG(presence)*100 availability,"
        "MIN(latency_ms) latencyMin,AVG(latency_ms) latencyAvg,"
        "MAX(latency_ms) latencyMax FROM samples WHERE device_id=?",
        (device.device_id,),
    ).fetchone()
    incidents = [
        dict(row)
        for row in database.execute(
            "SELECT * FROM incidents WHERE device_id=? AND status IN ('open','acknowledged')",
            (device.device_id,),
        )
    ]
    return {
        "deviceId": device.device_id,
        "state": dict(state) if state else None,
        "metrics": dict(samples),
        "incidents": incidents,
    }


def _recent_monitor_events():
    return [
        event.to_dict()
        for event in HistoryService().query(source="lanctl.monitor", limit=100, reverse=True)
    ]


def _events_action(args):
    if not args.follow:
        return {"status": "completed", "events": _recent_monitor_events()}

    seen = set()
    events = []
    try:
        while True:
            for event in _recent_monitor_events():
                if event["eventId"] in seen:
                    continue
                seen.add(event["eventId"])
                events.append(event)
                print(json.dumps(event, ensure_ascii=False), flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        return {"status": "cancelled", "events": events}


def _restart_action(args, sessions):
    active = sessions.repository.active()
    lock = SingletonLock(application_path(args.lock))
    state = lock.status()
    if not active or not state.get("running"):
        return {"status": "not-running", "message": "No hay un monitor activo que reiniciar"}

    old_pid = state["pid"]
    os.kill(old_pid, signal.SIGTERM)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and lock.status().get("running"):
        time.sleep(0.1)
    if lock.status().get("running"):
        return {"status": "error", "message": "El proceso monitor no se detuvo dentro del límite"}

    replacement = sessions.start(
        active.managerId,
        active.projectId,
        active.network,
        active.interface,
        active.localIp,
        active.mode,
        active.authority,
        None,
    )
    process = _spawn_foreground(args)
    return {
        "status": "restarted",
        "previousPid": old_pid,
        "processId": process.pid,
        "sessionId": replacement.sessionId,
    }


def _run_monitor_action(args, sessions, config, words, action):
    if action in {"attach", "start"} or (
        action == "session" and len(words) > 1 and words[1] == "start"
    ):
        return _start_monitor(args, sessions, config, action)
    elif action in {"detach", "stop"} or (
        action == "session" and len(words) > 1 and words[1] == "stop"
    ):
        return _stop_monitor(args, sessions)
    elif action == "status":
        return _monitor_status(args, sessions)
    elif action == "once":
        return _monitor_once(args, sessions, config)
    elif action in {"incidents", "incident"}:
        return _incident_action(args, sessions, words, action)
    elif action == "configure":
        return _configure_monitor(args, config, words)
    elif action == "profile":
        return _profile_action(args, words)
    elif action in {"assign", "unassign", "assignments"}:
        return _assignment_action(args, config, action)
    elif action == "report" or (
        action == "session" and len(words) > 1 and words[1] in {"list", "report"}
    ):
        return _report_action(args, sessions, config, words, action)
    elif action == "service":
        return _service_action(args, config, words)
    elif action == "service-host":
        return _service_host_action(args, sessions)
    elif action == "foreground":
        return _run_foreground(args, sessions)
    elif action == "ping":
        return _ping_action(args, sessions, config)
    elif action == "scan":
        return _scan_action(args, config)
    elif action == "identify":
        return _identify_action(args, config)
    elif action == "health":
        return _health_action(args, sessions, config)
    elif action == "events":
        return _events_action(args)
    elif action == "restart":
        return _restart_action(args, sessions)
    else:
        raise ValueError("acción monitor no válida")


def _platform():
    system = platform.system()
    if system == "Linux":
        from app.platform.linux import LinuxPlatform

        return LinuxPlatform()
    if system == "Windows":
        from app.platform.windows import WindowsPlatform

        return WindowsPlatform()
    from app.platform.base import PlatformAdapter

    return PlatformAdapter()


class InventoryAssignments:
    """Resuelve asignaciones persistentes contra el inventario vivo."""

    _PRIORITY: ClassVar[dict[str, int]] = {"low": 0, "normal": 1, "high": 2, "critical": 3}

    def __init__(self, args, config):
        self.args = args
        self.config = config
        self.inventory = DeviceDatabase(config["database"])
        self.manager = AssignmentManager(application_path(args.assignments_store))

    def plans(self, _session):
        devices = self.inventory.load()
        configured = [item for item in self.manager.list() if item.enabled]
        if not configured:
            return [MonitorTargetPlan(device) for device in devices]
        selected = {}
        for assignment in configured:
            if assignment.deviceId:
                matches = [device for device in devices if device.device_id == assignment.deviceId]
            else:
                matches = [device for device in devices if device.in_group(assignment.group)]
            for device in matches:
                previous = selected.get(device.device_id)
                if (
                    previous
                    and self._PRIORITY[previous.priority] > self._PRIORITY[assignment.priority]
                ):
                    priority = previous.priority
                    profile_id = previous.profile_id or assignment.profile
                else:
                    priority = assignment.priority
                    profile_id = assignment.profile or (previous.profile_id if previous else "")
                checks = (*(previous.checks if previous else ()), *assignment.checks)
                selected[device.device_id] = MonitorTargetPlan(device, priority, profile_id, checks)
        return list(selected.values())

    def discover(self, _session, timeout):
        from app.services.lan_scanner import LanScanner, resolve_network

        monitor = self.config.get("monitor", {})
        network = resolve_network(monitor.get("cidr") or self.config.get("range"))
        scanner = LanScanner(
            network,
            min(int(monitor.get("workers", self.config.get("workers", 32))), 64),
            float(timeout),
            int(self.config.get("maxHosts", 4096)),
            monitor.get("scanOrder", self.config.get("scanOrder", "ascending")),
        )
        records = scanner.scan(
            include_unknown=True,
            resolve_names=False,
            discovery="hybrid",
            include_arp_cache=True,
            attempts=1,
        )
        seen = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        for record in records:
            methods = [
                item
                for item in scanner.discovery_for(record).split("+")
                if item not in {"-", "CACHE", "BASIC"}
            ]
            if scanner.is_confirmed(record) and methods:
                record.discovery_methods = methods
                record.last_discovery = "+".join(methods)
                record.last_seen = seen
        self.inventory.upsert(records)
        return records


def _run_foreground(args, sessions, stop_event=None, service_managed=False):
    active = sessions.repository.active()
    if not active:
        project = args.project or load_config().get("activeProject") or "-"
        active = sessions.start(
            platform.node() or "manager", str(project), mode="permanent", authority="observe"
        )
    config = load_config()
    provider = ConfigProvider(config, ProfileManager(application_path(args.profiles)))
    assignments = InventoryAssignments(args, config)
    if stop_event is None:
        stop_event = threading.Event()
    if not service_managed:

        def stopping(*_):
            stop_event.set()

        signal.signal(signal.SIGTERM, stopping)
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, stopping)
    database = sessions.repository.db
    incidents = SqlIncidentRepository(database)
    service = MonitorService(
        config=provider,
        assignments=assignments,
        metrics=MetricsStore(database),
        sessions=sessions.repository,
        incidents=incidents,
        reports=ReportBuilder(
            database, sessions.repository, incidents, config.get("activeProject")
        ),
    )
    from app.plugins.manager import get_plugin_manager

    get_plugin_manager().monitor_service = service
    failed = False
    with SingletonLock(application_path(args.lock)):
        from app.access.runtime import AccessRuntime

        remote = AccessRuntime().start()
        try:
            service.start(active, provider.monitor().profile)
            try:
                service.foreground(stop_event=stop_event)
            except Exception as error:
                failed = True
                active.error = {"type": type(error).__name__, "message": str(error)[:500]}
                sessions.repository.save(active)
                raise
            finally:
                service.stop(
                    "error" if failed else "cancelled" if stop_event.is_set() else "completed"
                )
        finally:
            remote.stop()
    return {"status": "completed", "sessionId": active.sessionId}


def _targets(database, selector=None, group=None):
    if selector:
        return [database.resolve(selector)]
    rows = database.load()
    if group:
        rows = [device for device in rows if device.in_group(group)]
    if not rows:
        raise ValueError("no hay dispositivos para la operación monitor")
    return rows


def _lanctl_command(*arguments):
    return (
        [sys.executable, *arguments]
        if getattr(sys, "frozen", False)
        else [sys.executable, str(Path(__file__).resolve().parents[2] / "main.py"), *arguments]
    )


def _spawn_foreground(args):
    command = _lanctl_command(
        "monitor",
        "foreground",
        "--monitor-db",
        args.monitor_db,
        "--profiles",
        args.profiles,
        "--assignments-store",
        args.assignments_store,
        "--lock",
        args.lock,
    )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if platform.system() == "Windows" else 0
    return subprocess.Popen(
        command, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
