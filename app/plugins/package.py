from __future__ import annotations

import base64
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from app.plugins.models import PluginManifest

MAX_ENTRY_SIZE = 64 * 1024 * 1024
MAX_TOTAL_SIZE = 256 * 1024 * 1024
REQUIRED = {"plugin.info", "meta/version", "meta/created", "meta/checksum"}


def inspect_package(path: str | Path) -> PluginManifest:
    with safe_package(path) as archive:
        return PluginManifest.from_dict(json.loads(archive.read("plugin.info").decode("utf-8")))


def verify_package(path: str | Path) -> dict:
    source = Path(path).expanduser().resolve()
    with safe_package(source) as archive:
        names = {item.filename for item in archive.infolist() if not item.is_dir()}
        missing = sorted(REQUIRED - names)
        if missing:
            raise ValueError(f"LCP incompleto; faltan: {', '.join(missing)}")
        manifest = PluginManifest.from_dict(json.loads(archive.read("plugin.info").decode("utf-8")))
        expected = archive.read("meta/checksum").decode("ascii").strip().split()[-1].casefold()
        actual = archive_hash(archive, {"meta/checksum", "meta/signature"})
        if expected != actual:
            raise ValueError("checksum SHA-256 del LCP no coincide")
        signature = "UNSIGNED"
        if "meta/signature" in names:
            signature = _verify_signature(archive, actual, names)
        return {
            "valid": True,
            "path": str(source),
            "manifest": manifest,
            "checksum": actual,
            "signature": signature,
            "entries": len(names),
        }


def install_package(path: str | Path, destination_root: Path) -> tuple[PluginManifest, Path, dict]:
    result = verify_package(path)
    manifest = result["manifest"]
    destination = destination_root / manifest.plugin_id
    destination_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lanctl-lcp-") as temporary:
        staging = Path(temporary) / manifest.plugin_id
        staging.mkdir()
        with safe_package(path) as archive:
            for item in archive.infolist():
                if item.is_dir():
                    continue
                target = staging.joinpath(*PurePosixPath(item.filename).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
        old = destination.with_name(destination.name + ".old")
        if old.exists():
            shutil.rmtree(old)
        if destination.exists():
            destination.replace(old)
        try:
            shutil.copytree(staging, destination)
        except Exception:
            if old.exists() and not destination.exists():
                old.replace(destination)
            raise
        if old.exists():
            shutil.rmtree(old)
    return manifest, destination, result


def build_package(source: str | Path, output: str | Path, *, overwrite: bool = False) -> dict:
    root = Path(source).expanduser().resolve()
    destination = Path(output).expanduser().resolve()
    if destination.suffix.casefold() != ".lcp":
        destination = destination.with_suffix(".lcp")
    if destination.exists() and not overwrite:
        raise ValueError(f"ya existe el paquete: {destination}")
    info = root / "plugin.info"
    if not info.is_file():
        raise ValueError("el directorio no contiene plugin.info")
    manifest = PluginManifest.from_dict(json.loads(info.read_text(encoding="utf-8")))
    with tempfile.TemporaryDirectory(prefix="lanctl-lcp-build-") as temporary:
        staging = Path(temporary) / "package"
        shutil.copytree(root, staging)
        meta = staging / "meta"
        meta.mkdir(parents=True, exist_ok=True)
        (meta / "version").write_text(str(manifest.schema_version) + "\n", encoding="ascii")
        if not (meta / "created").exists():
            (meta / "created").write_text(
                datetime.now().astimezone().isoformat(timespec="seconds") + "\n", encoding="utf-8"
            )
        checksum = directory_hash(staging, {"meta/checksum", "meta/signature"})
        (meta / "checksum").write_text(checksum + "\n", encoding="ascii")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_zip = destination.with_suffix(destination.suffix + ".tmp")
        with zipfile.ZipFile(temporary_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(staging).as_posix())
        temporary_zip.replace(destination)
    result = verify_package(destination)
    result["path"] = str(destination)
    return result


def archive_hash(archive: zipfile.ZipFile, excluded: set[str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(
        item.filename
        for item in archive.infolist()
        if not item.is_dir() and item.filename not in excluded
    ):
        data = archive.read(name)
        digest.update(name.encode("utf-8") + b"\0" + len(data).to_bytes(8, "big") + data)
    return digest.hexdigest()


def _verify_signature(archive: zipfile.ZipFile, checksum: str, names: set[str]) -> str:
    if "meta/public-key.pem" not in names:
        raise ValueError("el LCP contiene firma pero no meta/public-key.pem")
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        document = json.loads(archive.read("meta/signature").decode("utf-8"))
        if str(document.get("algorithm", "")).casefold() != "ed25519":
            raise ValueError("algoritmo de firma LCP no soportado")
        public_key = serialization.load_pem_public_key(archive.read("meta/public-key.pem"))
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("la clave de firma LCP no es Ed25519")
        public_key.verify(
            base64.b64decode(document["value"], validate=True), checksum.encode("ascii")
        )
        fingerprint = hashlib.sha256(
            public_key.public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
            )
        ).hexdigest()
        return f"VALID_ED25519:{fingerprint}"
    except Exception as error:
        raise ValueError(f"firma LCP no válida: {error}") from error


def directory_hash(root: Path, excluded: set[str]) -> str:
    digest = hashlib.sha256()
    files = (item for item in root.rglob("*") if item.is_file())
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        name = path.relative_to(root).as_posix()
        if name in excluded:
            continue
        data = path.read_bytes()
        digest.update(name.encode("utf-8") + b"\0" + len(data).to_bytes(8, "big") + data)
    return digest.hexdigest()


def safe_package(path: str | Path):
    source = Path(path).expanduser().resolve()
    if source.suffix.casefold() != ".lcp":
        raise ValueError("el paquete debe utilizar la extensión .lcp")
    if not source.is_file() or not zipfile.is_zipfile(source):
        raise ValueError(f"LCP no válido: {source}")
    archive = zipfile.ZipFile(source, "r")
    seen: set[str] = set()
    total = 0
    try:
        for item in archive.infolist():
            name = item.filename
            pure = PurePosixPath(name)
            if (
                not name
                or name.startswith(("/", "\\"))
                or "\\" in name
                or ".." in pure.parts
                or pure.is_absolute()
            ):
                raise ValueError(f"ruta no segura dentro del LCP: {name}")
            folded = name.casefold()
            if folded in seen:
                raise ValueError(f"entrada duplicada dentro del LCP: {name}")
            seen.add(folded)
            if item.file_size > MAX_ENTRY_SIZE:
                raise ValueError(f"entrada LCP demasiado grande: {name}")
            total += item.file_size
            if total > MAX_TOTAL_SIZE:
                raise ValueError("contenido expandido del LCP demasiado grande")
        return archive
    except Exception:
        archive.close()
        raise
