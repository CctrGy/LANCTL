"""Fault injection and real listener regressions for REF-P69-remote-lifecycle."""

import json
import os
import socket
import subprocess
import sys
from copy import deepcopy
from unittest.mock import Mock

import pytest

from lanctl.apps.access import runtime_state as state
from lanctl.apps.access import settings_lifecycle as lifecycle
from lanctl.apps.access.service import AccessService
from lanctl.apps.suite.settings import save_form_values, save_program_changes
from lanctl.core import config
from lanctl.core.paths import application_path
from lanctl.core.settings_policy import SettingsContext


@pytest.fixture
def remote(tmp_path, monkeypatch):
    # Embedded service tests run as the current account, not an installed daemon.
    monkeypatch.setattr(lifecycle, "_service_file", lambda path: None)
    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LANCTL_SECRET_DIR", str(tmp_path / "access"))
    monkeypatch.delenv("LANCTL_SERVICE_MODE", raising=False)
    monkeypatch.delenv("LANCTL_ACCESS_START_TOKEN", raising=False)
    monkeypatch.setenv("LANCTL_DATA_SCOPE", "user")
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config" / "config.json")
    config.CONFIG_PATH.parent.mkdir()
    (config.CONFIG_PATH.parent / "migration-v2.complete").write_text("LANCTL-DATA-V2")
    original = deepcopy(config.DEFAULTS)
    original.update(remoteAccessBackend="user")
    config.save_config(original)
    service = AccessService(
        application_path(original["accessConfig"]), application_path(original["accessUsers"])
    )
    yield service
    # Only terminate processes registered in this test's isolated directory.
    record = state._read(service, "ssh")
    if record.get("backend") == "user" and state._alive(record):
        state._stop_owner(record)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def values(**changes):
    return {
        "remoteAccessEnabled": True,
        "remoteAccessBind": "127.0.0.1",
        "remoteAccessCidr": "127.0.0.0/8",
        "remoteAccessPort": free_port(),
        "remoteAccessBackend": "user",
        **changes,
    }


def save(**changes):
    return save_form_values(changes, SettingsContext("gui"))


def test_real_user_restart_and_confirmed_stop(remote):
    first = values()
    save(**first)
    initial = state._read(remote, "ssh")
    assert state._ready(remote, "ssh", remote.config()["ssh"], "user")
    assert not remote.store.path.exists()  # no empty credential file is required
    key = remote.config()["ssh"]["hostKey"]
    second = free_port()
    save(remoteAccessPort=second)
    assert not state._alive(initial)
    assert state._ready(remote, "ssh", remote.config()["ssh"], "user")
    assert remote.config()["ssh"]["hostKey"] == key
    assert config.load_config()["remoteAccessPort"] == second
    final = state._read(remote, "ssh")
    save(remoteAccessEnabled=False)
    assert not state._alive(final)
    assert not remote.config()["ssh"]["enabled"]
    assert not lifecycle._journal_path().exists()


def test_program_write_failure_restores_old_running_endpoint(remote, monkeypatch):
    save(**values())
    before = config.CONFIG_PATH.read_bytes()
    old = remote.config()["ssh"].copy()
    original = config.atomic_write_json

    def fail_program(path, value, **kwargs):
        if path == config.CONFIG_PATH:
            raise OSError("program disk full")
        return original(path, value, **kwargs)

    monkeypatch.setattr(config, "atomic_write_json", fail_program)
    with pytest.raises(OSError, match="program disk full"):
        save(remoteAccessPort=free_port())
    assert config.CONFIG_PATH.read_bytes() == before
    restored = remote.config()["ssh"]
    assert restored["port"] == old["port"]
    assert state._ready(remote, "ssh", restored, "user")
    assert not lifecycle._journal_path().exists()


def test_failed_start_removes_new_files_and_preserves_legacy_users(remote, monkeypatch):
    legacy = remote.store.path.with_name("users.json")
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "users": [],
                "sessions": [{"id": "keep"}],
                "roles": {},
                "pairings": [],
            }
        )
    )
    original = legacy.read_bytes()
    monkeypatch.setattr(
        lifecycle, "start_service_process", Mock(side_effect=OSError("start failed"))
    )
    with pytest.raises(OSError, match="start failed"):
        save(**values())
    assert not remote.config_path.exists()
    assert legacy.read_bytes() == original
    assert not remote.store.path.exists()
    assert not list(legacy.parent.glob("ssh_host_*.key"))
    assert not lifecycle._journal_path().exists()


def test_service_ack_and_switch_to_user_on_shared_path(remote, monkeypatch):
    from lanctl.apps.access.runtime import AccessRuntime

    monkeypatch.setattr("lanctl.core.local_permissions.require_admin", Mock())
    runtime = AccessRuntime(remote, poll_interval=0.5).start()
    try:
        save(**values(remoteAccessBackend="service"))
        assert state._ready(remote, "ssh", remote.config()["ssh"], "service")
        save(remoteAccessBackend="user")
        assert not runtime.instances
        assert state._ready(remote, "ssh", remote.config()["ssh"], "user")
        save(remoteAccessBackend="service")
        assert state._ready(remote, "ssh", remote.config()["ssh"], "service")
        save(remoteAccessEnabled=False)
        assert not runtime.instances
    finally:
        runtime.stop()


def test_missing_service_ack_rolls_back_without_success(remote, monkeypatch):
    monkeypatch.setattr("lanctl.core.local_permissions.require_admin", Mock())
    monkeypatch.setattr(state, "TIMEOUT", 0.15)
    before = config.CONFIG_PATH.read_bytes()
    with pytest.raises(TimeoutError, match="no confirmó"):
        save(**values(remoteAccessBackend="service"))
    assert config.CONFIG_PATH.read_bytes() == before
    assert not remote.config_path.exists()
    assert not lifecycle._journal_path().exists()


def test_denial_happens_before_journal_or_backend_writes(remote, monkeypatch):
    monkeypatch.setattr(
        "lanctl.core.local_permissions.require_admin", Mock(side_effect=PermissionError("admin"))
    )
    with pytest.raises(PermissionError):
        save(**values(remoteAccessBackend="service"))
    assert not remote.config_path.exists()
    assert not lifecycle._journal_path().exists()


def test_remote_context_cannot_open_transaction(remote, monkeypatch):
    transaction = Mock(side_effect=AssertionError("should not run"))
    monkeypatch.setattr(lifecycle, "remote_settings_transaction", transaction)
    with pytest.raises(ValueError, match="solo lectura"):
        save_program_changes({"access.remote.enabled": True}, SettingsContext("remote"))
    transaction.assert_not_called()


@pytest.mark.parametrize("after_replace", [False, True])
@pytest.mark.parametrize("write_number", range(1, 6))
def test_journal_write_faults_are_recoverable(remote, monkeypatch, write_number, after_replace):
    before = config.CONFIG_PATH.read_bytes()
    original = lifecycle.atomic_write_json
    count = 0

    def faulty(path, value, **kwargs):
        nonlocal count
        count += 1
        if count == write_number:
            if after_replace:
                original(path, value, **kwargs)
            raise OSError("journal write")
        return original(path, value, **kwargs)

    monkeypatch.setattr(lifecycle, "atomic_write_json", faulty)
    with pytest.raises(OSError, match="journal write"):
        save(remoteAccessPort=free_port())
    monkeypatch.setattr(lifecycle, "atomic_write_json", original)
    lifecycle.recover_remote_settings()
    assert config.CONFIG_PATH.read_bytes() == before
    assert not remote.config_path.exists()
    assert not lifecycle._journal_path().exists()


@pytest.mark.parametrize("after_replace", [False, True])
@pytest.mark.parametrize("write_number", [1, 2])
def test_backend_config_write_faults_restore_preimage(
    remote, monkeypatch, write_number, after_replace
):
    before = config.CONFIG_PATH.read_bytes()
    original = AccessService.save_config
    count = 0

    def faulty(self, value):
        nonlocal count
        count += 1
        if count == write_number:
            if after_replace:
                original(self, value)
            raise OSError("backend write")
        return original(self, value)

    monkeypatch.setattr(AccessService, "save_config", faulty)
    with pytest.raises(OSError, match="backend write"):
        save(remoteAccessPort=free_port())
    assert config.CONFIG_PATH.read_bytes() == before
    assert not remote.config_path.exists()
    assert not lifecycle._journal_path().exists()


def test_partial_key_creation_is_removed_on_failure(remote, monkeypatch):
    original = lifecycle.generate_host_key

    def faulty(path):
        original(path)
        raise OSError("key metadata failed")

    monkeypatch.setattr(lifecycle, "generate_host_key", faulty)
    with pytest.raises(OSError, match="key metadata"):
        save(**values())
    assert not list(remote.config_path.parent.glob("ssh_host_*.key"))
    assert not remote.config_path.exists()


def test_failed_stop_retains_owner_and_is_retryable(remote, monkeypatch):
    save(**values())
    old = remote.config()["ssh"].copy()
    owner = state._read(remote, "ssh")
    before = config.CONFIG_PATH.read_bytes()
    original = state._stop_owner
    monkeypatch.setattr(state, "_stop_owner", Mock(side_effect=PermissionError("stop denied")))
    with pytest.raises(RuntimeError, match="Recuperación remota pendiente") as failure:
        save(remoteAccessPort=free_port())
    assert isinstance(failure.value.__cause__, PermissionError)
    assert state._alive(owner)
    journal = json.loads(lifecycle._journal_path().read_text())
    assert journal["entries"][0]["stopping"][0]["processIdentity"] == owner["processIdentity"]
    assert config.CONFIG_PATH.read_bytes() == before
    monkeypatch.setattr(state, "_stop_owner", original)
    lifecycle.recover_remote_settings()
    assert not state._alive(owner)
    assert state._ready(remote, "ssh", remote.config()["ssh"], "user")
    assert remote.config()["ssh"]["port"] == old["port"]
    assert not lifecycle._journal_path().exists()


def test_rollback_preserves_concurrent_https_and_user_changes(remote, monkeypatch):
    def fail(service, protocol):
        service.update_config(lambda cfg: cfg["https"].update(port=9443))
        service.store.update(lambda store: store.update(roles={"custom": ["inventory.read"]}))
        raise OSError("start")

    monkeypatch.setattr(lifecycle, "start_service_process", fail)
    with pytest.raises(OSError, match="start"):
        save(**values())
    assert remote.config()["https"]["port"] == 9443
    assert remote.store.load()["roles"] == {"custom": ["inventory.read"]}
    assert not remote.config()["ssh"]["enabled"]


def test_conflicting_revision_is_not_overwritten(remote, monkeypatch):
    def fail(service, protocol):
        service.update_config(lambda cfg: cfg["ssh"].update(port=9443))
        raise OSError("concurrent edit")

    monkeypatch.setattr(lifecycle, "start_service_process", fail)
    with pytest.raises(RuntimeError, match="Recuperación remota pendiente"):
        save(**values())
    with pytest.raises(RuntimeError, match="Revisión remota ajena"):
        lifecycle.recover_remote_settings()
    assert remote.config()["ssh"]["port"] == 9443
    assert lifecycle._journal_path().exists()


def test_error_after_program_replace_keeps_committed_backend(remote, monkeypatch):
    monkeypatch.setattr(
        "lanctl.core.session.commit_config", Mock(side_effect=RuntimeError("observer"))
    )
    port = free_port()
    with pytest.raises(RuntimeError, match="observer"):
        save(remoteAccessPort=port)
    assert config.load_config()["remoteAccessPort"] == port
    assert remote.config()["ssh"]["port"] == port
    assert not lifecycle._journal_path().exists()


@pytest.mark.parametrize("commit", [False, True])
def test_recovery_after_abrupt_parent_exit(remote, commit):
    port = free_port()
    script = """
import os, sys
from lanctl.core.config import load_config, save_config
from lanctl.apps.access.settings_lifecycle import remote_settings_transaction
previous = load_config()
candidate = dict(previous, remoteAccessEnabled=True, remoteAccessBind='127.0.0.1',
                 remoteAccessCidr='127.0.0.0/8', remoteAccessPort=int(sys.argv[1]))
transaction = remote_settings_transaction(previous, candidate)
transaction.__enter__()
if sys.argv[2] == 'True':
    save_config(candidate)
os._exit(23)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(port), str(commit)],
        env=dict(os.environ),
        capture_output=True,
        timeout=25,
    )
    assert result.returncode == 23, result.stderr.decode(errors="replace")
    assert lifecycle._journal_path().exists()
    owner = state._read(remote, "ssh")
    assert state._alive(owner)
    if commit:
        config.update_config(lambda cfg: cfg.update(workers=9))
    lifecycle.recover_remote_settings()
    assert not lifecycle._journal_path().exists()
    if commit:
        assert state._ready(remote, "ssh", remote.config()["ssh"], "user")
        assert config.load_config()["remoteAccessPort"] == port
        assert config.load_config()["workers"] == 9
    else:
        assert not state._alive(owner)
        assert not remote.config_path.exists()


def test_recycled_pid_is_never_signalled(remote):
    owner = state._owner()
    owner["processIdentity"]["started"] = "wrong-creation-time"
    assert not state._alive(owner)
    state._stop_owner(owner)


def test_corrupt_recovery_record_is_not_treated_as_empty(remote):
    lifecycle._journal_path().write_text('{"schemaVersion":999}')
    with pytest.raises(ValueError, match="no compatible"):
        lifecycle.recover_remote_settings()
    assert lifecycle._journal_path().exists()


def test_runtime_retains_thread_when_stop_is_unconfirmed(remote):
    from lanctl.apps.access.runtime import AccessRuntime

    runtime = AccessRuntime(remote)
    server, thread = Mock(), Mock()
    thread.is_alive.return_value = True
    runtime.instances["ssh"] = ((), server, thread)
    with pytest.raises(TimeoutError):
        runtime._stop_protocol("ssh")
    assert runtime.instances["ssh"][2] is thread


def test_supervisors_in_same_process_do_not_duplicate_listeners(remote, monkeypatch):
    from lanctl.apps.access.runtime import AccessRuntime

    monkeypatch.setattr("lanctl.core.local_permissions.require_admin", Mock())
    first = AccessRuntime(remote, poll_interval=0.5).start()
    second = AccessRuntime(remote)
    try:
        save(**values(remoteAccessBackend="service"))
        second.reconcile()
        assert "ssh" in first.instances
        assert not second.instances
        assert state._read(remote, "ssh")["token"] == first.owner_token
    finally:
        second.stop()
        first.stop()


def test_https_stop_before_serve_does_not_wait_for_unstarted_loop(remote):
    from lanctl.apps.access.https_server import HttpsAccessServer
    from lanctl.apps.access.keys import generate_certificate

    certificate, key = generate_certificate(
        remote.config_path.parent / "cert.pem", remote.config_path.parent / "tls.key", "127.0.0.1"
    )
    server = HttpsAccessServer(
        "127.0.0.1",
        0,
        "127.0.0.0/8",
        certificate,
        key,
        remote.auth,
        remote.authorization,
        remote.status,
    )
    server.stop()
    server.serve_forever()  # no reopening after stop


def test_listener_identity_write_failure_terminates_the_claimed_child(remote, monkeypatch):
    from lanctl.apps.access.processes import start_service_process

    remote.save_config(remote.config())
    original = remote.update_config

    def fail_once(mutator):
        monkeypatch.setattr(remote, "update_config", original)
        raise OSError("identity write failed")

    monkeypatch.setattr(remote, "update_config", fail_once)
    with pytest.raises(OSError, match="identity write failed"):
        start_service_process(remote, "ssh")
    assert not state._alive(state._read(remote, "ssh"))
    assert not remote.config()["ssh"].get("processId")


def test_startup_retries_pending_recovery_and_reports_failure(remote, monkeypatch):
    from lanctl.core.errors import errors

    attempt = Mock(side_effect=PermissionError("elevation"))
    monkeypatch.setattr(lifecycle, "recover_remote_settings", attempt)
    reporter = Mock()
    monkeypatch.setattr(errors, "from_exception", reporter)
    lifecycle._recover_on_startup()
    attempt.assert_called_once()
    assert reporter.call_args.kwargs["origin"] == "LANCTL.Access.Settings.StartupRecovery"


def test_incomplete_recovery_record_is_rejected(remote):
    lifecycle._journal_path().write_text('{"schemaVersion":1}')
    with pytest.raises(ValueError, match="incompleto"):
        lifecycle.recover_remote_settings()
    assert lifecycle._journal_path().exists()


def test_existing_default_host_key_is_reused_without_rotation(remote):
    from pathlib import Path

    from lanctl.apps.access.keys import generate_host_key

    key = Path(generate_host_key(remote.config_path.parent / "ssh_host_ed25519_key"))
    before = key.read_bytes()
    save(**values())
    assert Path(remote.config()["ssh"]["hostKey"]) == key
    assert key.read_bytes() == before


def test_service_key_permission_failure_is_compensated(remote, monkeypatch):
    monkeypatch.setattr("lanctl.core.local_permissions.require_admin", Mock())
    monkeypatch.setattr(
        lifecycle, "_service_file", Mock(side_effect=PermissionError("key permissions"))
    )
    with pytest.raises(PermissionError, match="key permissions"):
        save(**values(remoteAccessBackend="service"))
    assert not remote.config_path.exists()
    assert not list(remote.config_path.parent.glob("ssh_host_*.key"))


def test_switch_between_separate_scope_paths_stops_previous_listener(remote, monkeypatch, tmp_path):
    from lanctl.apps.access import settings
    from lanctl.apps.access.runtime import AccessRuntime
    from lanctl.core.paths import service_data_scope

    original = lifecycle.application_path
    service_root = tmp_path / "service-access"

    def scoped_path(path):
        base = original(path)
        return service_root / base.name if service_data_scope() else base

    monkeypatch.setattr(lifecycle, "application_path", scoped_path)
    monkeypatch.setattr(settings, "application_path", scoped_path)
    monkeypatch.setattr("lanctl.core.local_permissions.require_admin", Mock())
    target = AccessService(
        service_root / remote.config_path.name, service_root / remote.store.path.name
    )
    runtime = AccessRuntime(target, poll_interval=0.5).start()
    try:
        save(**values())
        owner = state._read(remote, "ssh")
        save(remoteAccessBackend="service")
        assert not state._alive(owner)
        assert not remote.config()["ssh"]["enabled"]
        assert state._ready(target, "ssh", target.config()["ssh"], "service")
        save(remoteAccessBackend="user")
        assert not runtime.instances
        assert not target.config()["ssh"]["enabled"]
        assert state._ready(remote, "ssh", remote.config()["ssh"], "user")
    finally:
        runtime.stop()


@pytest.mark.parametrize("operation", ["load", "save", "update"])
def test_open_legacy_store_follows_concurrent_migration(remote, operation):
    from lanctl.apps.access.store import AccessStore

    legacy = remote.store.path.with_name("users.json")
    legacy.parent.mkdir(parents=True, exist_ok=True)
    data = AccessStore._empty()
    data["roles"] = {"kept": ["inventory.read"]}
    legacy.write_text(json.dumps(data))
    reader = AccessStore(legacy)
    canonical = AccessStore(legacy.with_name("users.dc"))
    if operation == "load":
        assert reader.load()["roles"] == data["roles"]
    elif operation == "save":
        reader.save(data)
    else:
        reader.update(lambda value: value["roles"].update(added=["inventory.read"]))
    assert canonical.load()["roles"]["kept"] == ["inventory.read"]
    assert reader.path == canonical.path
    assert not legacy.exists()


def test_rollback_retains_standalone_process_using_service_scope(remote, monkeypatch):
    save(**values())
    config.update_config(lambda cfg: cfg.update(remoteAccessBackend="service"))
    monkeypatch.setattr("lanctl.core.local_permissions.require_admin", Mock())
    previous = remote.config()["ssh"]["port"]
    entry = lifecycle._entry(config.load_config())
    assert entry["scope"] == "service"
    assert entry["runtimeBackend"] == "user"
    monkeypatch.setattr(config, "atomic_write_json", Mock(side_effect=OSError("program write")))
    with pytest.raises(OSError, match="program write"):
        save(remoteAccessPort=free_port(), remoteAccessBackend="user")
    assert remote.config()["ssh"]["port"] == previous
    assert state._ready(remote, "ssh", remote.config()["ssh"], "user")
    assert not lifecycle._journal_path().exists()
