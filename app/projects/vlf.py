from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path, PurePosixPath
from threading import RLock

from app import __version__
from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.core.file_transaction import transactional_path_argument
from app.core.group_database import GroupDatabase
from app.core.paths import application_path
from app.projects.paths import resolve_project_path

VLF_FORMAT_VERSION = "1.0"
MAX_ENTRY_SIZE = 256 * 1024 * 1024
MAX_TOTAL_SIZE = 512 * 1024 * 1024
REQUIRED_ENTRIES = {
    "project.info",
    "lan/lanIdentifier.info",
    "lan/network.config",
    "lan/vlan.config",
    "lan/topology.map",
    "auth/logins.lgn",
    "auth/keys/logon/access.info",
    "devices/backup.db",
    "devices/elements.db",
    "meta/version",
    "meta/created",
    "meta/checksum",
}
DIRECTORIES = (
    "lan/",
    "auth/",
    "auth/keys/",
    "auth/keys/ssh/",
    "auth/keys/api/",
    "auth/keys/device/",
    "auth/keys/logon/",
    "logs/",
    "devices/",
    "plugins/",
    "meta/",
)
_VLF_WRITE_LOCK = RLock()


@transactional_path_argument("output", transform=lambda value: _vlf_path(value))
def create_project(
    output: str | Path,
    *,
    name: str = "",
    description: str = "",
    author: str = "",
    lan_name: str = "",
    location: str = "",
    company: str = "",
    responsible: str = "",
    config: Mapping | None = None,
    identity: Mapping | None = None,
    template: str | Path | None = None,
    overwrite: bool = False,
) -> dict:
    destination = _vlf_path(output)
    if destination.exists() and not overwrite:
        raise ValueError(f"ya existe el proyecto VLF: {destination}; usa --force o project update")
    active = dict(config or load_config())
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    identity = dict(identity or {})
    project_id = str(identity.get("id") or uuid.uuid4())
    created = str(identity.get("created") or now)
    project_name = name or str(identity.get("name") or destination.stem)

    with tempfile.TemporaryDirectory(prefix="lanctl-vlf-") as temporary:
        root = Path(temporary)
        for directory in DIRECTORIES:
            (root / directory).mkdir(parents=True, exist_ok=True)
        if template:
            _copy_template_entries(_existing_vlf(template), root)

        database = DeviceDatabase(str(active["database"]))
        devices = database.load()
        groups = GroupDatabase(str(active["groups"]), database).load()
        _write_elements_database(root / "devices/elements.db", devices, groups)
        if not (root / "devices/backup.db").exists():
            shutil.copy2(root / "devices/elements.db", root / "devices/backup.db")

        network = _network_document(active, devices)
        _write_json(root / "lan/network.config", network)
        if not (root / "lan/vlan.config").exists():
            _write_json(
                root / "lan/vlan.config",
                {
                    "schemaVersion": 1,
                    "vlans": [],
                    "nativeVlan": None,
                    "managementVlan": None,
                },
            )
        topology_path = root / "lan/topology.map"
        old_topology = (
            json.loads(topology_path.read_text(encoding="utf-8"))
            if topology_path.exists()
            else None
        )
        _write_json(topology_path, _topology_document(devices, old_topology))
        old_lan = {}
        lan_identifier_path = root / "lan/lanIdentifier.info"
        if lan_identifier_path.exists():
            old_lan = json.loads(lan_identifier_path.read_text(encoding="utf-8"))
        _write_json(
            root / "lan/lanIdentifier.info",
            {
                "name": lan_name or old_lan.get("name") or project_name,
                "location": location or old_lan.get("location", ""),
                "company": company or old_lan.get("company", ""),
                "responsible": responsible or old_lan.get("responsible", ""),
                "description": description or old_lan.get("description", ""),
            },
        )

        # El proyecto conserva requisitos y estado de complementos, nunca su
        # código ejecutable. Cada plugin dispone de un espacio de nombres propio.
        try:
            from app.plugins import get_plugin_manager

            plugin_registry = get_plugin_manager().project_registry()
        except (OSError, ValueError):
            plugin_registry = {"schemaVersion": 1, "plugins": []}
        _write_json(root / "plugins/registry.json", plugin_registry)

        credentials = application_path(active.get("credentials", "data/lc/.credentials"))
        (root / "auth/logins.lgn").write_bytes(
            credentials.read_bytes() if credentials.exists() else b""
        )
        if not (root / "auth/keys/logon/access.info").exists():
            _write_json(
                root / "auth/keys/logon/access.info",
                {
                    "schemaVersion": 1,
                    "users": [],
                    "roles": [],
                    "note": "Las contraseñas deben permanecer cifradas; VLF no almacena texto plano.",
                },
            )
        _copy_logs(root / "logs", active)

        (root / "meta/version").write_text(VLF_FORMAT_VERSION + "\n", encoding="utf-8")
        (root / "meta/created").write_text(created + "\n", encoding="utf-8")
        content_hash = _hash_directory(root, {"project.info", "meta/checksum"})
        project_info = {
            "format": "LANCTL VLF",
            "formatVersion": VLF_FORMAT_VERSION,
            "name": project_name,
            "description": description or str(identity.get("description") or ""),
            "author": author or str(identity.get("author") or ""),
            "created": created,
            "updated": now,
            "lanctlVersion": __version__,
            "id": project_id,
            "contentHash": content_hash,
            "devices": len(devices),
            "groups": len(groups),
        }
        _write_json(root / "project.info", project_info)
        archive_hash = _hash_directory(root, {"meta/checksum"})
        _write_json(
            root / "meta/checksum",
            {
                "algorithm": "SHA-256",
                "hash": archive_hash,
                "scope": "all files except meta/checksum",
                "contentHash": content_hash,
            },
        )
        _write_archive(root, destination)
    result = verify_project(destination)
    result.update({"path": str(destination), "project": project_info})
    return result


@transactional_path_argument("path", transform=lambda value: _vlf_path(value))
def update_project(path: str | Path, *, config: Mapping | None = None) -> dict:
    source = _existing_vlf(path)
    verify_project(source)
    info = inspect_project(source)
    temporary = source.with_name(source.stem + ".update.vlf")
    backup = source.with_suffix(source.suffix + ".bak")
    if temporary.exists():
        temporary.unlink()
    result = create_project(
        temporary,
        name=info["name"],
        description=info.get("description", ""),
        author=info.get("author", ""),
        config=config,
        identity=info,
        template=source,
    )
    if backup.exists():
        backup.unlink()
    shutil.copy2(source, backup)
    os.replace(temporary, source)
    result["path"] = str(source)
    result["backup"] = str(backup)
    return result


@transactional_path_argument("path", transform=lambda value: _vlf_path(value))
def append_database_log(path: str | Path, message: str, *, now: datetime | None = None) -> Path:
    """Añade una auditoría a ./logs/ dentro del VLF y renueva sus hashes."""
    source = _existing_vlf(path)
    verify_project(source)
    timestamp = now or datetime.now().astimezone()
    clean_message = " | ".join(str(message).splitlines()).strip()
    log_name = f"logs/{timestamp:%d-%m-%Y}.log"

    with _VLF_WRITE_LOCK, tempfile.TemporaryDirectory(prefix="lanctl-vlf-log-") as temporary:
        root = Path(temporary)
        with _safe_archive(source) as archive:
            archive.extractall(root)
        log_path = root / PurePosixPath(log_name)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8", newline="") as log:
            log.write(f"{timestamp:%H:%M:%S} {clean_message}\n")

        info = json.loads((root / "project.info").read_text(encoding="utf-8"))
        info["updated"] = timestamp.astimezone().isoformat(timespec="seconds")
        content_hash = _hash_directory(root, {"project.info", "meta/checksum"})
        info["contentHash"] = content_hash
        _write_json(root / "project.info", info)
        archive_hash = _hash_directory(root, {"meta/checksum"})
        _write_json(
            root / "meta/checksum",
            {
                "algorithm": "SHA-256",
                "hash": archive_hash,
                "scope": "all files except meta/checksum",
                "contentHash": content_hash,
            },
        )
        _write_archive(root, source)
    return source


@transactional_path_argument("path", transform=lambda value: _vlf_path(value))
def append_history_event(
    path: str | Path, payload: Mapping, *, now: datetime | None = None
) -> Path:
    """Añade una línea JSONL estructurada y renueva los hashes del VLF."""
    source = _existing_vlf(path)
    verify_project(source)
    timestamp = now or datetime.now().astimezone()
    name = f"logs/events/{timestamp:%Y-%m-%d}.jsonl"
    line = json.dumps(dict(payload), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with _VLF_WRITE_LOCK, tempfile.TemporaryDirectory(prefix="lanctl-vlf-event-") as temporary:
        root = Path(temporary)
        with _safe_archive(source) as archive:
            archive.extractall(root)
        target = root / PurePosixPath(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8", newline="") as stream:
            stream.write(line + "\n")
        info = json.loads((root / "project.info").read_text(encoding="utf-8"))
        info["updated"] = timestamp.astimezone().isoformat(timespec="seconds")
        content_hash = _hash_directory(root, {"project.info", "meta/checksum"})
        info["contentHash"] = content_hash
        _write_json(root / "project.info", info)
        archive_hash = _hash_directory(root, {"meta/checksum"})
        _write_json(
            root / "meta/checksum",
            {
                "algorithm": "SHA-256",
                "hash": archive_hash,
                "scope": "all files except meta/checksum",
                "contentHash": content_hash,
            },
        )
        _write_archive(root, source)
    return source


@transactional_path_argument("path", transform=lambda value: _vlf_path(value))
def append_monitor_document(
    path: str | Path, entry: str, payload: Mapping, *, now: datetime | None = None
) -> Path:
    """Escribe un resumen monitor portable; nunca incluye monitor.db."""
    source = _existing_vlf(path)
    verify_project(source)
    timestamp = now or datetime.now().astimezone()
    relative = PurePosixPath(entry)
    if (
        not str(relative).startswith("monitoring/")
        or ".." in relative.parts
        or relative.suffix != ".json"
    ):
        raise ValueError("entrada monitor VLF no válida")
    with _VLF_WRITE_LOCK, tempfile.TemporaryDirectory(prefix="lanctl-vlf-monitor-") as temporary:
        root = Path(temporary)
        with _safe_archive(source) as archive:
            archive.extractall(root)
        _write_json(root / relative, dict(payload))
        info = json.loads((root / "project.info").read_text(encoding="utf-8"))
        info["updated"] = timestamp.astimezone().isoformat(timespec="seconds")
        content_hash = _hash_directory(root, {"project.info", "meta/checksum"})
        info["contentHash"] = content_hash
        _write_json(root / "project.info", info)
        archive_hash = _hash_directory(root, {"meta/checksum"})
        _write_json(
            root / "meta/checksum",
            {
                "algorithm": "SHA-256",
                "hash": archive_hash,
                "scope": "all files except meta/checksum",
                "contentHash": content_hash,
            },
        )
        _write_archive(root, source)
    return source


@transactional_path_argument("path", transform=lambda value: _vlf_path(value))
def inspect_project(path: str | Path) -> dict:
    source = _existing_vlf(path)
    with _safe_archive(source) as archive:
        return _read_json_entry(archive, "project.info")


@transactional_path_argument("path", transform=lambda value: _vlf_path(value))
def list_project_entries(path: str | Path) -> list[dict]:
    source = _existing_vlf(path)
    with _safe_archive(source) as archive:
        return [
            {"path": item.filename, "size": item.file_size, "compressed": item.compress_size}
            for item in archive.infolist()
            if not item.is_dir()
        ]


@transactional_path_argument("path", transform=lambda value: _vlf_path(value))
def verify_project(path: str | Path) -> dict:
    source = _existing_vlf(path)
    with _safe_archive(source) as archive:
        names = {item.filename for item in archive.infolist() if not item.is_dir()}
        missing = sorted(REQUIRED_ENTRIES - names)
        if missing:
            raise ValueError("VLF incompleto; faltan: " + ", ".join(missing))
        info = _read_json_entry(archive, "project.info")
        checksum = _read_json_entry(archive, "meta/checksum")
        if str(info.get("formatVersion")) != VLF_FORMAT_VERSION:
            raise ValueError(f"versión VLF no compatible: {info.get('formatVersion')}")
        content_hash = _hash_archive(archive, {"project.info", "meta/checksum"})
        archive_hash = _hash_archive(archive, {"meta/checksum"})
        if info.get("contentHash") != content_hash:
            raise ValueError("contentHash de project.info no coincide")
        if checksum.get("contentHash") != content_hash:
            raise ValueError("contentHash de meta/checksum no coincide")
        if checksum.get("hash") != archive_hash:
            raise ValueError("checksum global del VLF no coincide")
        database_bytes = archive.read("devices/elements.db")
        _verify_sqlite(database_bytes)
        _verify_sqlite(archive.read("devices/backup.db"))
        return {
            "valid": True,
            "formatVersion": VLF_FORMAT_VERSION,
            "contentHash": content_hash,
            "checksum": archive_hash,
            "entries": len(names),
            "size": source.stat().st_size,
        }


def _write_elements_database(path: Path, devices, groups) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executescript("""
            PRAGMA user_version = 1;
            CREATE TABLE devices (
                device_id TEXT PRIMARY KEY, ip TEXT NOT NULL, mac TEXT,
                cnf TEXT NOT NULL, alias TEXT, name TEXT, default_name TEXT,
                description TEXT, manufacturer TEXT, groups_json TEXT NOT NULL,
                protocols_json TEXT NOT NULL, discovery_methods_json TEXT NOT NULL,
                last_seen TEXT, raw_json TEXT NOT NULL
            );
            CREATE UNIQUE INDEX devices_mac ON devices(mac) WHERE mac <> '';
            CREATE INDEX devices_ip ON devices(ip);
            CREATE TABLE groups (
                name TEXT PRIMARY KEY, description TEXT, editable INTEGER NOT NULL
            );
            CREATE TABLE group_members (
                group_name TEXT NOT NULL, device_id TEXT NOT NULL,
                PRIMARY KEY(group_name, device_id),
                FOREIGN KEY(group_name) REFERENCES groups(name),
                FOREIGN KEY(device_id) REFERENCES devices(device_id)
            );
        """)
        for device in devices:
            raw = device.to_dict()
            connection.execute(
                "INSERT INTO devices VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    device.device_id,
                    device.ip,
                    device.mac,
                    device.cnf,
                    device.alias,
                    device.name,
                    device.default_name,
                    device.description,
                    device.manufacturer,
                    json.dumps(device.groups, ensure_ascii=False),
                    json.dumps(device.protocols, ensure_ascii=False),
                    json.dumps(device.discovery_methods, ensure_ascii=False),
                    device.last_seen,
                    json.dumps(raw, ensure_ascii=False, sort_keys=True),
                ),
            )
        by_mac = {device.mac: device.device_id for device in devices if device.mac}
        for group in groups:
            connection.execute(
                "INSERT INTO groups VALUES (?,?,?)",
                (group.name, group.description, int(group.editable)),
            )
            for mac in group.members:
                if mac in by_mac:
                    connection.execute(
                        "INSERT OR IGNORE INTO group_members VALUES (?,?)",
                        (group.name, by_mac[mac]),
                    )
        connection.commit()
    finally:
        connection.close()


def _network_document(config: Mapping, devices) -> dict:
    configured = config.get("range")
    network = ipaddress.ip_network(configured, strict=False) if configured else None
    gateway = next((device.ip for device in devices if device.alias == "GATEWAY"), "")
    return {
        "schemaVersion": 1,
        "network": str(network.network_address) if network else "",
        "netmask": str(network.netmask) if network else "",
        "cidr": str(network) if network else "",
        "prefixLength": network.prefixlen if network else None,
        "gateway": gateway,
        "dns": [],
        "dhcpRange": config.get("dhcpRange"),
        "discovery": config.get("discovery"),
        "scanProfile": config.get("scanProfile"),
        "scanOrder": config.get("scanOrder", "ascending"),
        "saveMode": config.get("projectSaveMode", "manual"),
        "saveIntervalMinutes": config.get("projectSaveIntervalMinutes", 5),
    }


def _topology_document(devices, previous: Mapping | None = None) -> dict:
    previous = dict(previous or {})
    prior_nodes = {
        node.get("id"): dict(node) for node in previous.get("nodes", []) if isinstance(node, dict)
    }
    nodes = []
    for device in devices:
        node = prior_nodes.get(device.device_id, {})
        node.update(
            {
                "id": device.device_id,
                "ip": device.ip,
                "mac": device.mac,
                "alias": device.alias,
                "name": device.name,
                "groups": list(device.groups),
                "type": node.get("type", "device"),
            }
        )
        nodes.append(node)
    return {
        "schemaVersion": 1,
        "nodes": nodes,
        "links": previous.get("links", []),
        "physical": previous.get("physical", {"racks": [], "wires": [], "ports": []}),
        "logical": previous.get("logical", {"segments": [], "vlans": []}),
    }


def _copy_logs(destination: Path, config: Mapping) -> None:
    # Por compatibilidad solo se importan auditorías antiguas. El registro
    # operativo del programa nunca forma parte del proyecto VLF.
    configured = config.get("databaseLog")
    if not configured:
        return
    root = application_path(configured)
    if not root.exists():
        return
    for source in sorted(root.glob("*.log")):
        target = destination / _normalized_log_name(source.name)
        target.write_bytes(source.read_bytes())


def _copy_template_entries(source: Path, destination: Path) -> None:
    preserved = {
        "lan/lanIdentifier.info",
        "lan/vlan.config",
        "lan/topology.map",
        "auth/keys/logon/access.info",
    }
    with _safe_archive(source) as archive:
        # La base principal anterior pasa a ser el punto de restauración.
        (destination / "devices/backup.db").write_bytes(archive.read("devices/elements.db"))
        for item in archive.infolist():
            name = item.filename
            if item.is_dir():
                continue
            if not (
                name in preserved
                or name.startswith(
                    (
                        "auth/keys/ssh/",
                        "auth/keys/api/",
                        "auth/keys/device/",
                        "logs/",
                        "plugins/",
                    )
                )
            ):
                continue
            target = destination / PurePosixPath(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))


def _normalized_log_name(name: str) -> str:
    stem = Path(name).stem
    if len(stem) == 9 and stem[:4].isdigit() and stem[4] == "-":
        return f"{stem[:2]}-{stem[2:]}{Path(name).suffix}"
    return name


def _write_archive(root: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for directory in DIRECTORIES:
                archive.writestr(directory, b"")
            for source in sorted(path for path in root.rglob("*") if path.is_file()):
                archive.write(source, source.relative_to(root).as_posix())
        os.replace(temporary, destination)
    finally:
        # Si la compresión falla, no deja residuos ni sustituye el VLF válido.
        temporary.unlink(missing_ok=True)


def _safe_archive(path: Path):
    archive = zipfile.ZipFile(path, "r")
    seen: set[str] = set()
    total = 0
    try:
        for item in archive.infolist():
            normalized = PurePosixPath(item.filename)
            if normalized.is_absolute() or ".." in normalized.parts or "\\" in item.filename:
                raise ValueError(f"ruta insegura dentro del VLF: {item.filename}")
            if item.filename in seen:
                raise ValueError(f"entrada duplicada dentro del VLF: {item.filename}")
            seen.add(item.filename)
            if item.file_size > MAX_ENTRY_SIZE:
                raise ValueError(f"entrada VLF demasiado grande: {item.filename}")
            total += item.file_size
            if total > MAX_TOTAL_SIZE:
                raise ValueError("contenido VLF demasiado grande")
        return archive
    except Exception:
        archive.close()
        raise


def _verify_sqlite(payload: bytes) -> None:
    with tempfile.TemporaryDirectory(prefix="lanctl-vlf-db-") as directory:
        database = Path(directory) / "elements.db"
        database.write_bytes(payload)
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        try:
            result = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise ValueError(f"elements.db no supera integrity_check: {result}")
            required = {"devices", "groups", "group_members"}
            tables = {
                row[0]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            if not required <= tables:
                raise ValueError("elements.db no contiene el esquema VLF requerido")
        finally:
            connection.close()


def _hash_directory(root: Path, excluded: set[str]) -> str:
    digest = hashlib.sha256()
    for source in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = source.relative_to(root).as_posix()
        if relative in excluded:
            continue
        _hash_item(digest, relative, source.read_bytes())
    return digest.hexdigest().upper()


def _hash_archive(archive: zipfile.ZipFile, excluded: set[str]) -> str:
    digest = hashlib.sha256()
    names = sorted(
        item.filename
        for item in archive.infolist()
        if not item.is_dir() and item.filename not in excluded
    )
    for name in names:
        _hash_item(digest, name, archive.read(name))
    return digest.hexdigest().upper()


def _hash_item(digest, name: str, payload: bytes) -> None:
    encoded = name.encode("utf-8")
    digest.update(len(encoded).to_bytes(4, "big"))
    digest.update(encoded)
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)


def _write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json_entry(archive: zipfile.ZipFile, name: str) -> dict:
    try:
        value = json.loads(archive.read(name).decode("utf-8"))
    except (KeyError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"entrada VLF inválida: {name}") from error
    if not isinstance(value, dict):
        raise ValueError(f"la entrada VLF debe ser un objeto: {name}")
    return value


def _vlf_path(value: str | Path) -> Path:
    configured = load_config().get("projectsDirectory")
    return resolve_project_path(value, configured)


def _existing_vlf(value: str | Path) -> Path:
    path = _vlf_path(value)
    if not path.exists():
        raise ValueError(f"no existe el proyecto VLF: {path}")
    if not zipfile.is_zipfile(path):
        raise ValueError(f"el archivo no es un contenedor VLF/ZIP válido: {path}")
    return path
