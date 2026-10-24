"""Remote-user CLI output must not turn stored authenticators into console logs."""

import argparse
import json
from dataclasses import asdict, make_dataclass

import pytest

from lanctl.apps.access.auth import AuthenticationService, verify_password
from lanctl.apps.access.store import AccessStore
from lanctl.apps.ip.interfaces.cli.commands import access


@pytest.mark.parametrize("with_password", [True, False])
def test_user_add_keeps_metadata_but_never_prints_authenticator(
    tmp_path, monkeypatch, capsys, with_password
):
    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LANCTL_DATA_SCOPE", "user")
    users_path = tmp_path / "users.dc"
    monkeypatch.setattr(
        access,
        "load_config",
        lambda: {"accessConfig": str(tmp_path / "config.json"), "accessUsers": str(users_path)},
    )
    password = "regression-password-for-CLI"
    monkeypatch.setattr(access.getpass, "getpass", lambda _prompt: password)
    public_key = tmp_path / "id_ed25519.pub"
    public_key.write_text("ssh-ed25519 dGVzdC1rZXk= test-only", encoding="utf-8")
    parser = argparse.ArgumentParser()
    access.register_access_command(parser.add_subparsers())
    command = ["access", "user", "add", "operator", "--role", "operator", "--json"]
    command += ["--password-auth", "on"] if with_password else ["--ssh-key", str(public_key)]
    args = parser.parse_args(command)

    assert args.handler(args) == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    user = AuthenticationService(AccessStore(users_path)).user("operator")
    assert password not in captured.out + captured.err
    assert not user.passwordHash or user.passwordHash not in captured.out + captured.err
    # Keep the existing JSON key and type for compatibility, always redacted.
    assert payload["passwordHash"] == ""
    assert payload["passwordConfigured"] is with_password
    for name, value in asdict(user).items():
        if name != "passwordHash":
            assert payload[name] == value
    if with_password:
        assert verify_password(password, user.passwordHash)


def test_user_output_does_not_serialize_future_private_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path))
    user = AuthenticationService(AccessStore(tmp_path / "users.dc")).add_user(
        "operator", password="regression-password-for-CLI"
    )
    extended_user = make_dataclass("ExtendedUser", [("privateToken", str, "")], bases=(type(user),))
    user = extended_user(**asdict(user), privateToken="future-private-value")

    payload = access._public_user(user)

    assert "privateToken" not in payload
    assert "future-private-value" not in json.dumps(payload)
