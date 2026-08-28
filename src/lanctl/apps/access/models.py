from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

PERMISSIONS = {
    "inventory.read",
    "history.read",
    "monitor.read",
    "monitor.control",
    "scan.run",
    "wol.send",
    "smb.read",
    "device.connect",
    "automation.manage",
    "project.manage",
    "users.manage",
    "system.configure",
}
ROLE_PERMISSIONS = {
    "viewer": {"inventory.read", "history.read", "monitor.read", "smb.read"},
    "operator": {
        "inventory.read",
        "history.read",
        "monitor.read",
        "monitor.control",
        "scan.run",
        "wol.send",
        "smb.read",
        "device.connect",
    },
    "manager": {
        "inventory.read",
        "history.read",
        "monitor.read",
        "monitor.control",
        "scan.run",
        "wol.send",
        "smb.read",
        "device.connect",
        "automation.manage",
        "project.manage",
    },
    "administrator": set(PERMISSIONS),
}


@dataclass
class RemoteUser:
    userId: str
    username: str
    roles: list[str]
    enabled: bool = True
    expiresAt: str | None = None
    lockedUntil: str | None = None
    failedAttempts: int = 0
    passwordHash: str = ""
    sshKeys: list[str] = field(default_factory=list)
    createdAt: str = ""
    updatedAt: str = ""
    passwordRotatedAt: str | None = None


@dataclass
class AccessSession:
    sessionId: str
    userId: str
    authenticator: str
    sourceIp: str
    createdAt: str
    expiresAt: str
    csrfHash: str = ""
    revokedAt: str | None = None


def aware(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("fecha de acceso requiere zona horaria")
    return parsed
