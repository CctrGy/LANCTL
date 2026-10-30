"""Pipe-only first-account setup; authenticate as root, then write as the service user."""

from __future__ import annotations

import json
import os
import pwd
import re
import stat
import sys
from pathlib import Path


class AccountSetupError(ValueError):
    """Public diagnostic code, without any submitted credential values."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def validate_request(document):
    if not isinstance(document, dict) or any(
        not isinstance(document.get(key), str) for key in ("username", "password", "confirmation")
    ):
        raise AccountSetupError("invalid-request")
    username = document["username"].strip().casefold()
    if not re.fullmatch(r"[a-z][a-z0-9._-]{2,63}", username):
        raise AccountSetupError("invalid-username")
    if not 12 <= len(document["password"]) <= 1024:
        raise AccountSetupError("password-length")
    if document["password"] != document["confirmation"]:
        raise AccountSetupError("password-mismatch")
    return username, document["password"]


def create_account(document, root=Path("/etc/lanctl/access")):
    if os.geteuid() != 0:
        raise PermissionError("Administrator authentication is required")
    # No caller-supplied path is accepted by the executable. Include legacy migration paths.
    paths = (
        root.parent,
        root,
        *(root / name for name in ("users.dc", "users.dc.lock", "users.json", "users.json.lock")),
    )
    if any(path.is_symlink() for path in paths):
        raise ValueError("Redirected service credential paths are not supported")
    try:
        service = pwd.getpwnam("lanctl")
    except KeyError as error:
        raise AccountSetupError("service-account-missing") from error
    for path in paths:
        if path.exists():
            info = path.stat()
            if info.st_uid not in {0, service.pw_uid} or info.st_mode & stat.S_IWOTH:
                raise PermissionError("Service credential paths must be protected")
    if not root.is_dir():
        raise ValueError("Install the LANCTL package first")
    # The store belongs to the account used by systemd. Drop root permanently before
    # following locks, legacy migrations or store writes in that service-owned directory.
    os.setgroups([service.pw_gid])
    os.setgid(service.pw_gid)
    os.setuid(service.pw_uid)
    os.umask(0o077)
    from lanctl.apps.access.auth import AuthenticationService
    from lanctl.apps.access.store import AccessStore
    from lanctl.core.file_transaction import locked_file

    with locked_file(root / "users.dc"):
        store = AccessStore(root / "users.dc")
        if store.users():
            return {"created": False, "preservedExistingUsers": True}
        username, password = validate_request(document)
        user = AuthenticationService(store).add_user(
            username, roles=("administrator",), password=password
        )
    return {"created": True, "username": user.username, "scope": "service"}


def main():
    try:
        os.environ["LANCTL_DATA_SCOPE"] = "service"
        os.environ["LANCTL_DATA_DIR"] = "/var/lib/lanctl"
        os.environ["LANCTL_SECRET_DIR"] = "/etc/lanctl/access"
        raw = sys.stdin.buffer.read(16385)
        if len(raw) > 16384:
            raise ValueError("Account request too large")
        result = create_account(json.loads(raw))
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        code = (
            error.code
            if isinstance(error, AccountSetupError)
            else "service-permission"
            if isinstance(error, PermissionError)
            else "service-files-missing"
            if isinstance(error, FileNotFoundError)
            else "account-error"
        )
        print(json.dumps({"error": code}))
        return 2
