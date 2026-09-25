from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {
    ".env",
    "authorized_keys",
    "device-credentials.dat",
    "host_key",
    "known_hosts",
    "users.dc",
}
FORBIDDEN_SUFFIXES = {
    ".db",
    ".jks",
    ".key",
    ".lgn",
    ".log",
    ".msi",
    ".msix",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".vlf",
    ".vault",
}
FORBIDDEN_PARTS = {"credentials", "data", "secrets"}
SECRET_PATTERNS = {
    "clave privada": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "token GitHub": re.compile(rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b"),
    "token GitHub moderno": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    "clave AWS": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}
# Esta prueba contiene deliberadamente una clave ficticia para verificar el
# redactor. La excepción sólo cubre ese patrón concreto, no otros secretos.
ALLOWED_FINDINGS = {(PurePosixPath("tests/test_errors.py"), "clave privada")}


def repository_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def forbidden_reason(path: Path) -> str | None:
    relative = PurePosixPath(path.relative_to(ROOT).as_posix())
    lowered_parts = tuple(part.casefold() for part in relative.parts)
    name = relative.name.casefold()
    if name == ".env.example":
        return None
    if name in FORBIDDEN_NAMES or name.startswith(".env."):
        return "archivo de credenciales o configuración privada"
    if name.startswith(("id_rsa", "id_ed25519", "host_key.")):
        return "material de identidad SSH"
    if any(part in FORBIDDEN_PARTS for part in lowered_parts[:-1]):
        return "directorio de datos o secretos locales"
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return "formato de estado, credenciales o artefacto local"
    if name.endswith((".db-journal", ".db-shm", ".db-wal")):
        return "archivo auxiliar de SQLite"
    return None


def main() -> int:
    findings: list[str] = []
    for path in repository_files():
        if not path.exists():
            # `git ls-files --cached` también devuelve borrados pendientes.
            continue
        relative = PurePosixPath(path.relative_to(ROOT).as_posix())
        reason = forbidden_reason(path)
        if reason:
            findings.append(f"{path.relative_to(ROOT)}: {reason}")
            continue
        try:
            payload = path.read_bytes()
        except OSError as error:
            findings.append(f"{path.relative_to(ROOT)}: no se pudo inspeccionar ({error})")
            continue
        if b"\0" in payload[:8192]:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(payload) and (relative, label) not in ALLOWED_FINDINGS:
                findings.append(f"{path.relative_to(ROOT)}: posible {label}")
    if findings:
        print("Archivos no aptos para Git:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("Higiene del repositorio: correcta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
