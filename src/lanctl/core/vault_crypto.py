"""Versioned portable envelope; algorithms and cost are deliberately not user supplied."""

from __future__ import annotations

import base64
import json
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b"LANCTLVAULT2\n"
MAX_BYTES = 8 * 1024 * 1024


def _key(password: str, salt: bytes) -> bytes:
    if len(password) < 12:
        raise ValueError("la contraseña del almacén requiere al menos 12 caracteres")
    return Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(password.encode("utf-8"))


def encrypt(payload: bytes, password: str) -> bytes:
    if len(payload) > MAX_BYTES:
        raise ValueError("almacén demasiado grande")
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    encrypted = AESGCM(_key(password, salt)).encrypt(nonce, payload, MAGIC)
    fields = [base64.b64encode(value).decode("ascii") for value in (salt, nonce, encrypted)]
    return MAGIC + json.dumps(fields, separators=(",", ":")).encode("ascii")


def decrypt(payload: bytes, password: str) -> bytes:
    if not payload.startswith(MAGIC) or len(payload) > MAX_BYTES * 2:
        raise ValueError("formato de almacén portable no compatible")
    try:
        fields = json.loads(payload[len(MAGIC) :])
        if not isinstance(fields, list) or len(fields) != 3:
            raise ValueError("cabecera inválida")
        salt, nonce, ciphertext = [base64.b64decode(item, validate=True) for item in fields]
        if len(salt) != 16 or len(nonce) != 12:
            raise ValueError("cabecera inválida")
        return AESGCM(_key(password, salt)).decrypt(nonce, ciphertext, MAGIC)
    except (InvalidTag, TypeError, ValueError, UnicodeError) as exc:
        raise ValueError("contraseña incorrecta o almacén alterado; no se ha modificado") from exc
