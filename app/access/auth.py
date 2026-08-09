from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta

from .models import PERMISSIONS, ROLE_PERMISSIONS, AccessSession, RemoteUser, aware


def now():
    return datetime.now().astimezone()


def hash_password(password):
    if len(password) < 12:
        raise ValueError("la contrasena web debe tener al menos 12 caracteres")
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return (
        "scrypt$16384$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(derived).decode()
    )


def verify_password(password, encoded):
    try:
        kind, n, salt, wanted = encoded.split("$")
        if kind != "scrypt" or n != "16384":
            return False
        salt_bytes = base64.b64decode(salt, validate=True)
        wanted_bytes = base64.b64decode(wanted, validate=True)
        if len(salt_bytes) != 16 or len(wanted_bytes) != 32:
            return False
        actual = hashlib.scrypt(
            password.encode(),
            salt=salt_bytes,
            n=16384,
            r=8,
            p=1,
            dklen=32,
        )
    except (AttributeError, ValueError, TypeError, binascii.Error):
        return False
    return kind == "scrypt" and hmac.compare_digest(actual, wanted_bytes)


def fingerprint_key(key):
    """Calcula la huella OpenSSH del blob, sin incluir su comentario."""
    parts = str(key).strip().split()
    if len(parts) < 2 or not parts[0].startswith(("ssh-", "ecdsa-", "sk-")):
        raise ValueError("clave publica OpenSSH no valida")
    try:
        blob = base64.b64decode(parts[1].encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as error:
        raise ValueError("clave publica OpenSSH no valida") from error
    if not blob:
        raise ValueError("clave publica OpenSSH vacia")
    return "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode().rstrip("=")


class AuthorizationService:
    def __init__(self, store):
        self.store = store

    def permissions(self, user):
        custom = self.store.load().get("roles", {})
        result = set()
        for role in user.roles:
            result.update(custom.get(role, ROLE_PERMISSIONS.get(role, set())))
        return result

    def require(self, user, permission):
        if permission not in PERMISSIONS or permission not in self.permissions(user):
            raise PermissionError(f"permiso requerido: {permission}")
        return True


class AuthenticationService:
    def __init__(self, store, audit=None, clock=now):
        self.store = store
        self.audit = audit or (lambda *a, **k: None)
        self.clock = clock

    def add_user(self, username, roles=("viewer",), password=None, ssh_keys=(), expires_at=None):
        clean = username.strip().casefold()
        if not re.fullmatch(r"[a-z][a-z0-9._-]{2,63}", clean):
            raise ValueError("usuario remoto no valido o duplicado")
        custom_roles = self.store.load().get("roles", {})
        if any(role not in ROLE_PERMISSIONS and role not in custom_roles for role in roles):
            raise ValueError("rol no valido")
        if expires_at and aware(expires_at) <= self.clock():
            raise ValueError("la caducidad debe ser futura")
        stamp = self.clock().isoformat()
        user = RemoteUser(
            str(uuid.uuid4()),
            clean,
            list(dict.fromkeys(roles)),
            passwordHash=hash_password(password) if password else "",
            sshKeys=list(dict.fromkeys(fingerprint_key(x) for x in ssh_keys)),
            createdAt=stamp,
            updatedAt=stamp,
            expiresAt=expires_at,
        )
        if not user.passwordHash and not user.sshKeys:
            raise ValueError("configura un autenticador web o una clave SSH")
        self.store.create_user(user)
        self.audit("access.user.created", user, "success")
        return user

    def user(self, username):
        found = next(
            (
                x
                for x in self.store.users()
                if x.username == username.casefold() or x.userId == username
            ),
            None,
        )
        if not found:
            raise ValueError("usuario remoto no encontrado")
        return found

    def _usable(self, user):
        current = self.clock()
        if not user.enabled:
            raise PermissionError("cuenta desactivada")
        if user.expiresAt and current >= aware(user.expiresAt):
            raise PermissionError("cuenta caducada")
        if user.lockedUntil and current < aware(user.lockedUntil):
            raise PermissionError("cuenta bloqueada temporalmente")

    def authenticate_password(self, username, password, source_ip):
        user = self.user(username)
        succeeded = False

        def attempt(current):
            nonlocal succeeded
            self._usable(current)
            succeeded = bool(
                current.passwordHash and verify_password(password, current.passwordHash)
            )
            if not succeeded:
                current.failedAttempts += 1
                if current.failedAttempts >= 5:
                    current.lockedUntil = (self.clock() + timedelta(minutes=15)).isoformat()
                return current
            current.failedAttempts = 0
            current.lockedUntil = None
            current.updatedAt = self.clock().isoformat()
            return current

        user = self.store.update_user(user.userId, attempt)
        if not succeeded:
            if user.lockedUntil:
                self.audit("access.user.locked", user, "blocked")
            self.audit("access.login.failed", user, "error", source_ip)
            raise PermissionError("autenticacion rechazada")
        self.audit("access.login.succeeded", user, "success", source_ip)
        return user

    def authenticate_ssh_key(self, username, public_key, source_ip):
        user = self.user(username)
        supplied = fingerprint_key(public_key)
        matched = False

        def attempt(current):
            nonlocal matched
            self._usable(current)
            matched = any(hmac.compare_digest(saved, supplied) for saved in current.sshKeys)
            return current

        user = self.store.update_user(user.userId, attempt)
        if not matched:
            self.audit("access.login.failed", user, "error", source_ip)
            raise PermissionError("clave SSH rechazada")
        self.audit("access.login.succeeded", user, "success", source_ip)
        return user

    def create_session(self, user, authenticator, source_ip, ttl=3600):
        csrf = secrets.token_urlsafe(32)
        stamp = self.clock()
        session = AccessSession(
            str(uuid.uuid4()),
            user.userId,
            authenticator,
            source_ip,
            stamp.isoformat(),
            (stamp + timedelta(seconds=ttl)).isoformat(),
            hashlib.sha256(csrf.encode()).hexdigest(),
        )
        self.store.save_session(session)
        return session, csrf

    def validate_session(self, session_id, source_ip, csrf=None):
        session = next((x for x in self.store.sessions() if x.sessionId == session_id), None)
        if (
            not session
            or session.revokedAt
            or self.clock() >= aware(session.expiresAt)
            or session.sourceIp != source_ip
        ):
            raise PermissionError("sesion no valida")
        if csrf is not None and not hmac.compare_digest(
            session.csrfHash, hashlib.sha256(csrf.encode()).hexdigest()
        ):
            raise PermissionError("token CSRF no valido")
        user = self.user(session.userId)
        self._usable(user)
        return user

    def revoke(self, session_id):
        session = next((x for x in self.store.sessions() if x.sessionId == session_id), None)
        if not session:
            raise ValueError("sesion no encontrada")
        session.revokedAt = self.clock().isoformat()
        self.store.save_session(session)
        self.audit("access.session.revoked", None, "success")
        return session

    def create_pairing(self, user_id, ttl=300):
        user = self.user(user_id)
        code = f"{secrets.randbelow(1000000):06d}"
        item = {
            "id": str(uuid.uuid4()),
            "userId": user.userId,
            "hash": hashlib.sha256(code.encode()).hexdigest(),
            "expiresAt": (self.clock() + timedelta(seconds=ttl)).isoformat(),
            "consumedAt": None,
        }
        self.store.update(lambda value: value["pairings"].append(item))
        self.audit("access.pairing.created", user, "success")
        return code

    def consume_pairing(self, code):
        digest = hashlib.sha256(code.encode()).hexdigest()

        def consume(value):
            item = next(
                (x for x in value["pairings"] if hmac.compare_digest(x["hash"], digest)), None
            )
            if not item or item["consumedAt"] or self.clock() >= aware(item["expiresAt"]):
                raise PermissionError("codigo de emparejamiento no valido")
            item["consumedAt"] = self.clock().isoformat()
            return item["userId"]

        user = self.user(self.store.update(consume))
        self.audit("access.pairing.consumed", user, "success")
        return user
