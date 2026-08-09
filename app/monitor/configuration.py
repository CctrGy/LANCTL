from __future__ import annotations

import ipaddress
import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from app.core.file_transaction import atomic_write_json, locked_file, update_json

from .models import AUTHORITIES, MODES, MonitorProfile

_DURATION = re.compile(r"^(\d+(?:\.\d+)?)(s|m|h|d)$", re.IGNORECASE)
PROFILE_ID = re.compile(r"^[a-z][a-z0-9]*(?:[-_.][a-z0-9]+)*$")


def utc_now():
    return datetime.now().astimezone().isoformat()


def parse_duration(value) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    match = _DURATION.fullmatch(str(value).strip())
    if not match:
        raise ValueError(f"duración no válida: {value}")
    return (
        float(match.group(1)) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2).casefold()]
    )


BUILTIN_PROFILES = {
    "light": MonitorProfile("light", 60, 30, 300, 1800, 86400, 0.8, 16, 0.1, 3, 2),
    "permanent-light": MonitorProfile(
        "permanent-light", 60, 30, 300, 1800, 86400, 0.8, 16, 0.1, 3, 2
    ),
    "normal": MonitorProfile("normal", 60, 15, 300, 1800, 86400, 0.8, 32, 0.1, 3, 2),
    "intensive": MonitorProfile("intensive", 15, 10, 120, 600, 21600, 0.8, 32, 0.1, 3, 2),
    "permanent-intensive": MonitorProfile(
        "permanent-intensive", 15, 10, 120, 600, 21600, 0.8, 32, 0.1, 3, 2
    ),
    "diagnostic-temporary": MonitorProfile(
        "diagnostic-temporary", 3, 3, 30, 120, 1800, 0.8, 16, 0.05, 2, 2
    ),
}


@dataclass(frozen=True)
class MonitorConfig:
    enabled: bool = False
    profile: str = "normal"
    mode: str = "permanent"
    authority: str = "observe"
    interface: str = ""
    cidr: str = ""
    duration: float | None = None

    def __post_init__(self):
        if self.profile != "custom" and self.profile not in BUILTIN_PROFILES:
            raise ValueError("perfil monitor no válido")
        if self.mode not in MODES or self.authority not in AUTHORITIES:
            raise ValueError("modo o authority monitor no válido")
        if self.cidr:
            network = ipaddress.ip_network(self.cidr, strict=False)
            if network.version != 4 or network.num_addresses > 65536:
                raise ValueError("CIDR monitor demasiado amplio")
        if self.mode in {"temporary", "diagnostic"} and (
            self.duration is None or not 10 <= self.duration <= 86400
        ):
            raise ValueError("modo temporal requiere duración entre 10s y 24h")


class ConfigProvider:
    def __init__(self, config=None, profiles=None):
        from app.core.config import load_config

        self.config = dict(config or load_config())
        self.profiles = profiles

    def monitor(self):
        value = self.config.get("monitor", {})
        return MonitorConfig(
            bool(value.get("enabled", False)),
            str(value.get("profile", "normal")),
            str(value.get("mode", "permanent")),
            str(value.get("authority", "observe")),
            str(value.get("interface", "")),
            str(value.get("cidr", "")),
            parse_duration(value["duration"]) if value.get("duration") else None,
        )

    def profile(self, profile_id="normal"):
        value = self.config.get("monitor", {})
        active_id = str(value.get("profile", "normal"))
        if profile_id == "default":
            profile_id = active_id
        if profile_id not in BUILTIN_PROFILES:
            if self.profiles:
                return self.profiles.profile(profile_id)
            raise ValueError("perfil monitor personalizado no disponible")
        base = BUILTIN_PROFILES[profile_id]
        if profile_id != active_id:
            return base
        intervals = value.get("intervals", {})
        profile = MonitorProfile(
            profile_id,
            parse_duration(intervals.get("deviceStatus", base.presence_interval)),
            parse_duration(intervals.get("criticalDevices", base.critical_interval)),
            parse_duration(intervals.get("networkDiscovery", base.discovery_interval)),
            parse_duration(intervals.get("serviceScan", base.services_interval)),
            parse_duration(intervals.get("fullScan", base.deep_interval)),
            float(value.get("timeout", base.timeout)),
            int(value.get("workers", base.workers)),
            base.jitter,
            int(value.get("failureThreshold", base.failure_threshold)),
            int(value.get("recoveryThreshold", base.recovery_threshold)),
        )
        return validate_profile(profile)

    def retention(self):
        return dict(self.config.get("monitor", {}).get("retention", {}))


def validate_profile(profile: MonitorProfile) -> MonitorProfile:
    if not PROFILE_ID.fullmatch(profile.profile_id):
        raise ValueError("id de perfil no válido")
    intervals = (
        profile.presence_interval,
        profile.critical_interval,
        profile.discovery_interval,
        profile.services_interval,
        profile.deep_interval,
    )
    if min(intervals) < 1 or max(intervals) > 31 * 86400:
        raise ValueError("intervalo monitor fuera de rango")
    if (
        profile.discovery_interval < 30
        or profile.services_interval < 60
        or profile.deep_interval < 300
    ):
        raise ValueError("configuración monitor saturaría la red")
    if not 1 <= profile.workers <= 128 or not 0.05 <= profile.timeout <= 120:
        raise ValueError("workers/timeout monitor no válidos")
    if not 1 <= profile.failure_threshold <= 20 or not 1 <= profile.recovery_threshold <= 20:
        raise ValueError("threshold monitor no válido")
    return profile


def validate_monitor_settings(value: dict) -> dict:
    config = dict(value)
    retention = dict(config.get("retention", {}))
    raw = parse_duration(retention.get("rawSamples", "24h"))
    five = parse_duration(retention.get("fiveMinuteAggregates", "30d"))
    hourly = parse_duration(retention.get("hourlyAggregates", "365d"))
    if not raw <= five <= hourly:
        raise ValueError("la retención debe cumplir raw <= 5m <= hourly")
    intervals = config.get("intervals", {})
    profile = MonitorProfile(
        str(config.get("profile", "normal")),
        parse_duration(intervals.get("deviceStatus", 60)),
        parse_duration(intervals.get("criticalDevices", 15)),
        parse_duration(intervals.get("networkDiscovery", 300)),
        parse_duration(intervals.get("serviceScan", 1800)),
        parse_duration(intervals.get("fullScan", 86400)),
        float(config.get("timeout", 0.8)),
        int(config.get("workers", 32)),
        0.1,
        int(config.get("failureThreshold", 3)),
        int(config.get("recoveryThreshold", 2)),
    )
    validate_profile(profile)
    return config


class JsonDocument:
    def __init__(self, path):
        self.path = Path(path)

    def load(self, default):
        if not self.path.exists():
            return default
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if value.get("schemaVersion") != 1:
            raise ValueError("versión futura/no compatible")
        return value

    def save(self, value):
        with locked_file(self.path):
            atomic_write_json(self.path, value)

    def update(self, default, operation):
        def validate(value):
            if value.get("schemaVersion") != 1:
                raise ValueError("versión futura/no compatible")

        return update_json(self.path, lambda: default, operation, validate=validate)


class ProfileManager:
    def __init__(self, path):
        self.document = JsonDocument(path)

    def list(self):
        custom = self.document.load({"schemaVersion": 1, "profiles": {}})["profiles"]
        return [*BUILTIN_PROFILES.values(), *(MonitorProfile(**value) for value in custom.values())]

    def profile(self, profile_id="normal"):
        return next((p for p in self.list() if p.profile_id == profile_id), None) or (
            _ for _ in ()
        ).throw(ValueError("perfil monitor no encontrado"))

    def save(self, profile: MonitorProfile):
        validate_profile(profile)
        if profile.profile_id in BUILTIN_PROFILES:
            raise ValueError("los perfiles integrados están protegidos")

        def store(value):
            value["profiles"][profile.profile_id] = asdict(profile)

        self.document.update({"schemaVersion": 1, "profiles": {}}, store)
        return profile

    def delete(self, profile_id):
        if profile_id in BUILTIN_PROFILES:
            raise ValueError("los perfiles integrados están protegidos")

        def remove(value):
            if value["profiles"].pop(profile_id, None) is None:
                raise ValueError("perfil monitor no encontrado")

        self.document.update({"schemaVersion": 1, "profiles": {}}, remove)


@dataclass(frozen=True)
class MonitorAssignment:
    assignmentId: str
    selector: str
    deviceId: str = ""
    group: str = ""
    priority: str = "normal"
    profile: str = ""
    checks: tuple[dict, ...] = ()
    enabled: bool = True
    source: str = "user"
    createdAt: str = field(default_factory=utc_now)
    updatedAt: str = field(default_factory=utc_now)

    def __post_init__(self):
        if not self.assignmentId or bool(self.deviceId) == bool(self.group):
            raise ValueError("asignación requiere exactamente deviceId o group")
        if self.priority not in {"low", "normal", "high", "critical"}:
            raise ValueError("prioridad no válida")
        for check in self.checks:
            if (
                check.get("type") not in {"ping", "arp", "port", "service", "availability"}
                or parse_duration(check.get("interval", 60)) < 5
            ):
                raise ValueError("check de asignación no válido")
            arguments = check.get("args", {})
            if check.get("type") == "port" and not 1 <= int(arguments.get("port", 0)) <= 65535:
                raise ValueError("el check port requiere un puerto entre 1 y 65535")
            if "timeout" in check and not 0.05 <= float(check["timeout"]) <= 120:
                raise ValueError("timeout de check no válido")


class AssignmentManager:
    def __init__(self, path):
        self.document = JsonDocument(path)

    def list(self):
        return [
            MonitorAssignment(**{**x, "checks": tuple(x.get("checks", ()))})
            for x in self.document.load({"schemaVersion": 1, "assignments": []})["assignments"]
        ]

    def assign(self, selector, *, device_id="", group="", priority="normal", profile="", checks=()):
        result = []
        key = (device_id.casefold(), group.casefold())

        def store(value):
            rows = [
                MonitorAssignment(**{**x, "checks": tuple(x.get("checks", ()))})
                for x in value["assignments"]
            ]
            existing = next(
                (x for x in rows if (x.deviceId.casefold(), x.group.casefold()) == key), None
            )
            item = MonitorAssignment(
                existing.assignmentId if existing else "assign_" + uuid.uuid4().hex[:20],
                selector,
                device_id,
                group,
                priority,
                profile,
                tuple(checks),
                createdAt=existing.createdAt if existing else utc_now(),
                updatedAt=utc_now(),
            )
            result.append(item)
            value["assignments"] = [
                asdict(x) for x in rows if x.assignmentId != item.assignmentId
            ] + [asdict(item)]

        self.document.update({"schemaVersion": 1, "assignments": []}, store)
        return result[0]

    def unassign(self, selector):
        def remove(value):
            rows = [
                MonitorAssignment(**{**x, "checks": tuple(x.get("checks", ()))})
                for x in value["assignments"]
            ]
            kept = [
                x
                for x in rows
                if selector.casefold()
                not in {
                    x.assignmentId.casefold(),
                    x.selector.casefold(),
                    x.deviceId.casefold(),
                    x.group.casefold(),
                }
            ]
            if len(kept) == len(rows):
                raise ValueError("asignación no encontrada")
            value["assignments"] = [asdict(x) for x in kept]

        self.document.update({"schemaVersion": 1, "assignments": []}, remove)

    def targets(self, session):
        return [x for x in self.list() if x.enabled]
