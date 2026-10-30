"""Build the standalone Qt wizard around an already built, version-matched DEB."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lanctl import __version__  # noqa: E402
from lanctl.core.installation_languages import available_languages  # noqa: E402


def digest(path):
    with path.open("rb") as stream:
        hasher = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
        return hasher.hexdigest()


def build(package, output):
    package, output = package.resolve(), output.resolve()
    arch = {"x86_64": "amd64", "aarch64": "arm64"}[platform.machine()]
    fields = subprocess.check_output(
        ["dpkg-deb", "--field", str(package), "Package", "Version", "Architecture"], text=True
    )
    if dict(line.split(": ", 1) for line in fields.strip().splitlines()) != {
        "Package": "lanctl",
        "Version": __version__,
        "Architecture": arch,
    }:
        raise ValueError(
            "Build a DEB matching the current application version and architecture first"
        )
    staging = ROOT / "build/linux-setup/payload"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--name",
            "lanctl-setup",
            "--distpath",
            str(ROOT / "build/linux-setup/dist"),
            "--workpath",
            str(ROOT / "build/linux-setup/work"),
            "--specpath",
            str(ROOT / "build/linux-setup"),
            "--paths",
            str(ROOT / "src"),
            "--add-data",
            f"{ROOT / 'bundled/languages'}:bundled/languages",
            "--exclude-module",
            "PyQt6.QtWebEngineCore",
            "--exclude-module",
            "PyQt6.QtWebEngineWidgets",
            "--exclude-module",
            "webview",
            str(ROOT / "packaging/linux/setup_gui.py"),
        ],
        check=True,
        cwd=ROOT,
    )
    shutil.copytree(ROOT / "build/linux-setup/dist/lanctl-setup", staging / "wizard")
    shutil.copyfile(package, staging / package.name)
    metadata = {
        "schemaVersion": 1,
        "version": __version__,
        "arch": arch,
        "package": package.name,
        "sha256": digest(package),
        "languages": [
            {"code": code, "nativeName": catalog.native_name}
            for code, catalog in available_languages().items()
        ],
    }
    (staging / "setup.json").write_text(json.dumps(metadata, indent=2) + "\n")
    # Runtime libraries must remain readable after the privileged account helper
    # drops to the service UID. No credentials are stored in this payload.
    for path in staging.rglob("*"):
        if not path.is_symlink():
            path.chmod(0o755 if path.is_dir() or path.stat().st_mode & 0o111 else 0o644)
    files = sorted(path for path in staging.rglob("*") if path.is_file())
    (staging / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(path)}  {path.relative_to(staging)}\n" for path in files)
    )
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f"LANCTL-{__version__}-linux-{arch}-setup.run"
    with destination.open("wb") as stream:
        stream.write((ROOT / "packaging/linux/setup-bootstrap.sh").read_bytes())
        # Libraries and DEB are already compressed where appropriate. Avoid re-compressing the DEB.
        with tarfile.open(fileobj=stream, mode="w|") as archive:
            for item in sorted(staging.iterdir()):
                archive.add(item, arcname=item.name)
    destination.chmod(0o755)
    print(destination)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/release")
    args = parser.parse_args()
    build(args.package, args.output)
