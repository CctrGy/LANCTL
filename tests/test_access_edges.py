from __future__ import annotations

import socket
from datetime import datetime, timedelta, timezone

import pytest

from lanctl.apps.access.models import AccessSession, RemoteUser
from lanctl.apps.access.network import port_available, source_allowed, validate_endpoint
from lanctl.apps.access.service import AccessService, access_process_running
from lanctl.apps.access.store import AccessStore


@pytest.mark.parametrize(
    ("bind", "cidr", "port", "interfaces"),
    [
        ("2001:db8::1", "2001:db8::/64", 443, None),
        ("192.168.2.1", "192.168.1.0/24", 443, None),
        ("192.168.1.1", "192.168.1.0/24", 0, None),
        ("192.168.1.1", "192.168.1.0/24", 65536, None),
        ("192.168.1.1", "192.168.1.0/24", 443, {"192.168.1.2"}),
    ],
)
def test_endpoint_validation_rejects_unsafe_combinations(bind, cidr, port, interfaces):
    with pytest.raises(ValueError):
        validate_endpoint(bind, cidr, port, interfaces=interfaces)


def test_source_and_port_helpers_fail_closed():
    assert not source_allowed("invalid", "192.168.1.0/24")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    try:
        assert not port_available("127.0.0.1", listener.getsockname()[1])
    finally:
        listener.close()
    assert port_available("127.0.0.1", 0)


def user(identifier="u1", username="alice"):
    return RemoteUser(identifier, username, ["viewer"])


def session(identifier="s1", user_id="u1"):
    now = datetime.now(timezone.utc)
    return AccessSession(
        identifier,
        user_id,
        "password",
        "127.0.0.1",
        now.isoformat(),
        (now + timedelta(minutes=5)).isoformat(),
    )


def test_access_store_user_and_session_lifecycle(tmp_path):
    store = AccessStore(tmp_path / "users.dc")
    alice = user()
    store.create_user(alice)
    with pytest.raises(ValueError, match="duplicado"):
        store.create_user(user("u2", "ALICE"))
    alice.enabled = False
    store.save_user(alice)
    assert store.users()[0].enabled is False
    updated = store.update_user("u1", lambda value: value)
    assert updated.userId == "u1"
    with pytest.raises(ValueError, match="no encontrado"):
        store.update_user("missing", lambda value: value)
    store.save_session(session())
    store.save_session(session())
    assert len(store.sessions()) == 1
    store.delete_user("u1")
    assert store.users() == [] and store.sessions() == []
    with pytest.raises(ValueError, match="no encontrado"):
        store.delete_user("u1")


def test_access_store_rejects_unknown_schema(tmp_path):
    path = tmp_path / "users.dc"
    path.write_text('{"schemaVersion":99}', encoding="utf-8")
    with pytest.raises(ValueError, match="version"):
        AccessStore(path).load()


def test_access_service_configuration_collision_and_disable(tmp_path):
    service = AccessService(tmp_path / "access.json", tmp_path / "users.dc")
    service.initialize()
    service.configure("https", bind="127.0.0.1", cidr="127.0.0.0/8", port=9443)
    service.update_config(lambda value: value["https"].update(enabled=True))
    with pytest.raises(ValueError, match="colisiona"):
        service.configure("ssh", bind="127.0.0.1", cidr="127.0.0.0/8", port=9443)
    with pytest.raises(ValueError, match="protocolo"):
        service.configure("telnet", bind="127.0.0.1", cidr="127.0.0.0/8", port=23)
    assert service.disable("https")["enabled"] is False
    with pytest.raises(ValueError, match="protocolo"):
        service.disable("telnet")


def test_process_running_rejects_missing_and_stale_identity(monkeypatch):
    assert not access_process_running({})
    monkeypatch.setattr(
        "lanctl.apps.monitor.lifecycle._process_identity", lambda _pid: "actual-identity"
    )
    assert not access_process_running({"processId": 123, "processIdentity": "stale"})
