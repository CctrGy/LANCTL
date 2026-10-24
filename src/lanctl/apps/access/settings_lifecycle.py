"""Recoverable remote settings transaction; journals contain no authenticators."""

import hashlib
import json
import os
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from uuid import UUID, uuid4

from lanctl.core import config as program
from lanctl.core.file_transaction import atomic_write_json, locked_file
from lanctl.core.paths import application_path, scoped_data_paths

from . import runtime_state as state
from .keys import generate_host_key
from .processes import start_service_process
from .service import DEFAULT_CONFIG, AccessService

_FIELDS = {
    "enabled",
    "bind",
    "cidr",
    "port",
    "passwordAuthentication",
    "hostKey",
    "lifecycleRevision",
    "lifecycleBackend",
}
_PROCESS = {"processId", "processIdentity", "processToken"}


def _journal_path():
    return program.CONFIG_PATH.with_name(program.CONFIG_PATH.name + ".remote-transaction.json")


def _service(entry):
    # Settings never migrate or initialize authentication stores. In particular a
    # rollback must not revert sessions/users created while the listener runs.
    users = Path(entry["users"])
    legacy = users.with_name("users.json")
    if users.name == "users.dc" and not users.exists() and legacy.exists():
        users = legacy
    return AccessService(entry["path"], users)


def _projection(config):
    return {
        "ssh": {key: deepcopy(value) for key, value in config["ssh"].items() if key in _FIELDS},
        "forcedView": config["control"]["forcedView"],
    }


def _entry(config):
    scope = config["remoteAccessBackend"]
    with scoped_data_paths(scope):
        path = application_path(config["accessConfig"]).resolve()
        entry = {
            "scope": scope,
            "path": str(path),
            "users": str(application_path(config["accessUsers"]).resolve()),
            "existed": path.exists(),
        }
    service = _service(entry)
    stored = service.config()
    owner = state._read(service, "ssh")
    running = bool(owner.get("state") == "running" and state._alive(owner))
    if running:
        entry["runtimeBackend"] = owner["backend"]
    elif state._alive(stored["ssh"]):
        running = True
        entry["runtimeBackend"] = "user"
    else:
        entry["runtimeBackend"] = scope
    entry.update(before=_projection(stored), expected=_projection(stored), running=running)
    if os.name != "nt" and path.exists():
        info = path.stat()
        entry["permissions"] = [info.st_mode & 0o777, info.st_uid, info.st_gid]
    return entry


def _service_file(path):
    """Grant the installed service group access only to a newly managed file."""
    if os.name == "nt":
        return  # Installed/portable data directories supply the Windows ACL.
    import grp

    try:
        group = grp.getgrnam("lanctl").gr_gid
    except KeyError as error:
        raise RuntimeError("No está instalado el grupo del servicio LANCTL") from error
    os.chown(path, 0, group)
    Path(path).chmod(0o640)


def _write(journal, entry, desired):
    service = _service(entry)
    with locked_file(service.config_path):
        config = service.config()
        if _projection(config) != entry["expected"]:
            raise RuntimeError(
                "La configuración remota cambió durante la operación; recuperación pendiente"
            )
        # Persist intent BEFORE its write, including the version that may remain
        # on disk if atomic replacement succeeds but its observer raises.
        entry["previousExpected"] = entry["expected"]
        entry["expected"] = deepcopy(desired)
        atomic_write_json(_journal_path(), journal)
        for key in _FIELDS | _PROCESS:
            config["ssh"].pop(key, None)
        config["ssh"].update(desired["ssh"])
        config["control"]["forcedView"] = desired["forcedView"]
        service.save_config(config)
        if os.name != "nt":
            if entry.get("permissions"):
                mode, uid, gid = entry["permissions"]
                if os.geteuid() == 0:
                    os.chown(service.config_path, uid, gid)
                service.config_path.chmod(mode)
            elif desired["ssh"].get("lifecycleBackend") == "service" and desired["ssh"]["enabled"]:
                _service_file(service.config_path)


def _accept_interrupted_write(entry):
    current = _projection(_service(entry).config())
    if current == entry["expected"]:
        return
    if current == entry.get("previousExpected"):
        entry["expected"] = current
        return
    raise RuntimeError("Revisión remota ajena: se conserva el registro de recuperación")


def _stop(journal, entry):
    service = _service(entry)
    # The supervisor claims/builds under this same lock. It cannot open a
    # listener between the ownership snapshot and the disable request.
    with locked_file(service.config_path):
        settings = service.config()["ssh"]
        pending = entry.setdefault("stopping", [])
        owner = state._read(service, "ssh")
        if owner.get("state") == "running" and owner not in pending:
            pending.append(owner)
        if settings.get("processId"):
            process = {key: settings[key] for key in _PROCESS if key in settings}
            process["backend"] = "user"
            if process not in pending:
                pending.append(process)
        desired = deepcopy(entry["expected"])
        desired["ssh"].update(enabled=False, lifecycleRevision=uuid4().hex)
        _write(journal, entry, desired)
    for owner in pending:
        if not state._alive(owner):
            continue
        if owner.get("backend") == "user":
            state._stop_owner(owner)
        else:
            revision = state._revision(desired["ssh"])

            def stopped():
                current = state._read(service, "ssh")
                return not state._alive(owner) or (
                    current.get("state") == "stopped"
                    and current.get("revision") == revision
                    and current.get("processId") == owner.get("processId")
                    and current.get("processIdentity") == owner.get("processIdentity")
                    and current.get("token") == owner.get("token")
                )

            state._wait(stopped, "El servicio no confirmó la parada del listener")
    entry["stopping"] = []
    atomic_write_json(_journal_path(), journal)


def _start(entry):
    service = _service(entry)
    settings = service.config()["ssh"]
    if not settings["enabled"]:
        return
    backend = entry["runtimeBackend"]
    if state._ready(service, "ssh", settings, backend):
        return
    if backend == "user":
        with scoped_data_paths(entry["scope"]):
            start_service_process(service, "ssh")
    else:
        state._wait(
            lambda: state._ready(service, "ssh", settings, "service"),
            "El servicio permanente no confirmó la nueva revisión remota",
        )


def _rollback(journal):
    journal["phase"] = "rollback"
    atomic_write_json(_journal_path(), journal)
    # Stop all partial listeners before restoring either endpoint. A failed stop
    # retains the owner and journal; never start a competing listener afterwards.
    for entry in journal["entries"]:
        _accept_interrupted_write(entry)
        _stop(journal, entry)
    for entry in journal["entries"]:
        desired = deepcopy(entry["before"])
        desired["ssh"].update(
            lifecycleRevision=uuid4().hex, lifecycleBackend=entry["runtimeBackend"]
        )
        _write(journal, entry, desired)
        if entry["running"]:
            _start(entry)
    journal["phase"] = "restored"
    atomic_write_json(_journal_path(), journal)
    _cleanup_rollback(journal)


def _cleanup_rollback(journal):
    for entry in journal["entries"]:
        if not entry["existed"]:
            service = _service(entry)
            with locked_file(service.config_path):
                current = service.config()
                pristine = deepcopy(DEFAULT_CONFIG)
                pristine["ssh"] = current["ssh"]
                pristine["control"]["forcedView"] = current["control"]["forcedView"]
                if current == pristine and _projection(current) == entry["expected"]:
                    service.config_path.unlink(missing_ok=True)
    key = journal.get("createdKey")
    if key:
        Path(key).unlink(missing_ok=True)
    _journal_path().unlink(missing_ok=True)


def _digest(config):
    return hashlib.sha256(
        json.dumps(program.canonical_config(config), sort_keys=True).encode()
    ).hexdigest()


def _remote_digest(config):
    values = program.canonical_config(config)["access"]
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def _program_committed(journal):
    stored = program._load_config()
    return (
        journal["phase"] == "applied"
        and journal.get("programAfter") is not None
        and (
            (
                journal["programAfter"] != journal["programBefore"]
                and _digest(stored) == journal["programAfter"]
            )
            or (
                journal["remoteAfter"] != journal["remoteBefore"]
                and _remote_digest(stored) == journal["remoteAfter"]
            )
        )
    )


def _recover():
    path = _journal_path()
    if not path.exists():
        return
    journal = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(journal, dict) or journal.get("schemaVersion") != 1:
        raise ValueError("Registro de recuperación remota no compatible")
    _validate_journal(journal)
    if journal.get("requestedScope") == "service" or any(
        entry["scope"] == "service" or entry["runtimeBackend"] == "service"
        for entry in journal["entries"]
    ):
        from lanctl.core.local_permissions import require_admin

        require_admin()
    if journal["phase"] == "restored":
        _cleanup_rollback(journal)
    elif _program_committed(journal):
        for entry in journal["entries"]:
            _accept_interrupted_write(entry)
        _start(
            {
                **journal["entries"][journal["target"]],
                "scope": journal["activeScope"],
                "runtimeBackend": journal["activeScope"],
            }
        )
        path.unlink()
    else:
        _rollback(journal)


def _validate_journal(journal):
    try:
        identifier = journal["id"]
        if len(identifier) != 32 or UUID(identifier).hex != identifier:
            raise ValueError("Identificador de recuperación no válido")
        entries = journal["entries"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= 2:
            raise ValueError("Recursos de recuperación no válidos")
        if type(journal["target"]) is not int or not 0 <= journal["target"] < len(entries):
            raise ValueError("Destino de recuperación no válido")
        if journal["phase"] not in {"prepared", "applied", "rollback", "restored"}:
            raise ValueError("Fase de recuperación no válida")
        for entry in entries:
            if entry["scope"] not in {"user", "service"} or entry["runtimeBackend"] not in {
                "user",
                "service",
            }:
                raise ValueError("Ámbito de recuperación no válido")
            if not Path(entry["path"]).is_absolute() or not Path(entry["users"]).is_absolute():
                raise ValueError("Rutas de recuperación no válidas")
            for name in ("before", "expected"):
                if (
                    not isinstance(entry[name]["ssh"], dict)
                    or set(entry[name]["ssh"]) - _FIELDS
                    or not set(DEFAULT_CONFIG["ssh"]).issubset(entry[name]["ssh"])
                ):
                    raise ValueError("Snapshot de recuperación no válido")
                entry[name]["forcedView"]
        if journal["requestedScope"] not in {"user", "service"}:
            raise ValueError("Ámbito solicitado no válido")
        key = journal.get("createdKey")
        if key:
            with scoped_data_paths(journal["requestedScope"]):
                expected = application_path(f"data/lc/access/ssh_host_{identifier}.key").resolve()
            if Path(key) != expected or Path(key).is_symlink():
                raise ValueError("La clave de recuperación no pertenece a esta operación")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Registro de recuperación remota incompleto") from error


def recover_remote_settings():
    """Retry an interrupted local operation with the same authorization checks."""
    # Read-only fast path preserves help/status and does not create directories.
    if not _journal_path().exists():
        return
    with locked_file(program.CONFIG_PATH), locked_file(_journal_path()):
        _recover()


def _recover_on_startup():
    try:
        recover_remote_settings()
    except (OSError, ValueError, RuntimeError) as error:
        from lanctl.core.errors import errors

        errors.from_exception(
            error,
            origin="LANCTL.Access.Settings.StartupRecovery",
            code="ACCESS.SETTINGS.RECOVERY.STARTUP.PENDING",
            level=47,
        )


@contextmanager
def remote_settings_transaction(previous, candidate, *, persist_program=True):
    from .settings import validate_remote_settings

    # Pending operations are retried before endpoint/key preflight: either may
    # be precisely the interrupted state that needs repair. Authorization is
    # checked from the persisted scopes by _recover, never bypassed.
    recover_remote_settings()
    validate_remote_settings(previous, candidate)
    with locked_file(program.CONFIG_PATH), locked_file(_journal_path()):
        _recover()
        target = _entry(candidate)
        entries = [target]
        if previous["remoteAccessEnabled"]:
            old = _entry(previous)
            entries = [old] if Path(old["path"]) == Path(target["path"]) else [old, target]
        target_index = len(entries) - 1
        # For a shared portable path, retain the old owner for compensation, but
        # choose the new backend only when starting the final desired revision.
        from lanctl.core.session import prepare_config_save

        stored = program._load_config()
        journal = {
            "schemaVersion": 1,
            "id": uuid4().hex,
            "phase": "prepared",
            "entries": entries,
            "target": target_index,
            "requestedScope": candidate["remoteAccessBackend"],
            "programBefore": _digest(stored),
            "remoteBefore": _remote_digest(stored),
            "remoteAfter": _remote_digest(candidate),
            "programAfter": _digest(prepare_config_save(candidate, stored))
            if persist_program
            else None,
        }
        atomic_write_json(_journal_path(), journal)
        try:
            for entry in entries:
                _stop(journal, entry)
            entry = entries[target_index]
            desired = deepcopy(entry["expected"])
            desired["forcedView"] = candidate["remoteAccessForcedView"]
            desired["ssh"].update(
                enabled=candidate["remoteAccessEnabled"],
                bind=candidate["remoteAccessBind"].strip() or None,
                cidr=candidate["remoteAccessCidr"].strip() or None,
                port=candidate["remoteAccessPort"],
                passwordAuthentication=candidate["remoteAccessPasswordAuthentication"],
                lifecycleBackend=candidate["remoteAccessBackend"],
                lifecycleRevision=uuid4().hex,
            )
            if desired["ssh"]["enabled"] and not desired["ssh"].get("hostKey"):
                with scoped_data_paths(candidate["remoteAccessBackend"]):
                    key = application_path(f"data/lc/access/ssh_host_{journal['id']}.key").resolve()
                    existing = application_path("data/lc/access/ssh_host_ed25519_key").resolve()
                if existing.is_file():
                    desired["ssh"]["hostKey"] = str(existing)
                else:
                    if key.exists():
                        raise FileExistsError("La nueva host key ya existe")
                    journal["createdKey"] = str(key)
                    atomic_write_json(_journal_path(), journal)
                    desired["ssh"]["hostKey"] = generate_host_key(key)
                    if candidate["remoteAccessBackend"] == "service":
                        _service_file(key)
            _write(journal, entry, desired)
            active = {
                **entry,
                "scope": candidate["remoteAccessBackend"],
                "runtimeBackend": candidate["remoteAccessBackend"],
            }
            _start(active)
            journal["phase"] = "applied"
            journal["activeScope"] = candidate["remoteAccessBackend"]
            atomic_write_json(_journal_path(), journal)
            yield
        except BaseException as error:
            try:
                if not _program_committed(journal):
                    _rollback(journal)
                else:
                    _journal_path().unlink(missing_ok=True)
            except Exception as recovery_error:  # noqa: BLE001 - retain both failures at the recovery boundary
                from lanctl.core.errors import errors

                errors.from_exception(
                    recovery_error,
                    origin="LANCTL.Access.Settings.Recovery",
                    code="ACCESS.SETTINGS.RECOVERY.PENDING",
                    level=47,
                    details={"operation": journal["id"], "initialError": type(error).__name__},
                    print_output=False,
                )
                raise RuntimeError(
                    f"Recuperación remota pendiente ({type(recovery_error).__name__}: {recovery_error})"
                ) from error
            raise
        else:
            _journal_path().unlink()
