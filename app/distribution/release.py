from __future__ import annotations

import re

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?$")


def validate_version(value: str) -> str:
    version = value.removeprefix("v")
    if not VERSION_RE.fullmatch(version):
        raise ValueError("versión de LANCTL no válida")
    return version


def classify_channel(version: str) -> str:
    return "beta" if "-" in validate_version(version) else "stable"


def normalize_architecture(value: str) -> str:
    architecture = value.casefold()
    mapping = {
        "x86_64": "amd64", "amd64": "amd64", "x64": "amd64",
        "aarch64": "arm64", "arm64": "arm64",
    }
    if architecture not in mapping:
        raise ValueError(f"arquitectura no soportada: {value}")
    return mapping[architecture]


def artifact_name(version: str, system: str, architecture: str, portable: bool = False) -> str:
    version = validate_version(version)
    arch = normalize_architecture(architecture)
    platform = system.casefold()
    if platform == "windows":
        if arch != "amd64":
            raise ValueError("Windows solo está publicado para x64")
        suffix = "portable.zip" if portable else "setup.exe"
        return f"LANCTL-{version}-windows-x64-{suffix}"
    if platform == "linux":
        return f"LANCTL-{version}-linux-{arch}.tar.gz" if portable else f"lanctl_{version}_{arch}.deb"
    raise ValueError(f"sistema no soportado: {system}")
