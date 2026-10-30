"""Linux installer plan: system installation and user preferences stay separate."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

PLUGINS = {
    "lanctl.example.network-summary": ("Network summary", "Resumen de red"),
    "lanctl.analysis.mac-vendor": ("MAC vendors", "Fabricantes MAC"),
    "lanctl.discovery.mdns-ssdp": ("mDNS / SSDP", "mDNS / SSDP"),
    "lanctl.discovery.windows-smb": ("Windows / SMB", "Windows / SMB"),
    "lanctl.network.wol": ("Wake-on-LAN", "Wake-on-LAN"),
    "lanctl.lab.network-emulator": ("Network laboratory", "Laboratorio de red"),
}
THEMES = ("graphite", "midnight", "forest", "violet", "light")


def load_distribution(directory: Path) -> dict:
    metadata = json.loads((directory / "setup.json").read_text())
    if metadata.get("schemaVersion") != 1:
        raise ValueError("Unsupported setup manifest")
    name = metadata["package"]
    if not isinstance(name, str) or Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError("Invalid package filename")
    package = directory / name
    if package.is_symlink() or not package.is_file():
        raise ValueError("Missing package")
    with package.open("rb") as stream:
        hasher = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
        digest = hasher.hexdigest()
    if digest != metadata["sha256"]:
        raise ValueError("Package checksum mismatch")
    actual = subprocess.check_output(
        ["/usr/bin/dpkg-deb", "--field", str(package), "Package", "Version", "Architecture"],
        text=True,
    )
    fields = dict(line.split(": ", 1) for line in actual.strip().splitlines())
    if fields != {
        "Package": "lanctl",
        "Version": metadata["version"],
        "Architecture": metadata["arch"],
    }:
        raise ValueError("Package metadata mismatch")
    arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(platform.machine())
    if metadata["arch"] != arch:
        raise ValueError("This installer does not match the computer architecture")
    languages = metadata["languages"]
    if not languages or "en" not in {item["code"] for item in languages}:
        raise ValueError("Missing English language catalog")
    return metadata


@dataclass
class Selection:
    language: str = "en"
    theme: str = "graphite"
    plugins: list[str] = field(default_factory=lambda: list(PLUGINS))
    change_language: bool = False
    monitor: bool = False
    completion: bool = True
    desktop: bool = False
    ipgui: bool = False
    events: bool = False
    access_admin: bool = False
    remote_account: bool = False
    first_scan: bool = False
    network_tools: bool = True
    open_gui: bool = True

    def defaults_command(self) -> list[str]:
        if self.theme not in THEMES or any(item not in PLUGINS for item in self.plugins):
            raise ValueError("Invalid installation selection")
        command = [
            "/opt/lanctl/lanctl",
            "setup-defaults",
            "--theme",
            self.theme,
            "--plugins",
            ",".join(self.plugins) or "none",
            "--language",
            self.language,
        ]
        return command + (["--change-language"] if self.change_language else [])


def clean_environment() -> dict[str, str]:
    """Do not leak development data paths or PyInstaller's library path into installed apps."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("LANCTL_")}
    original = env.pop("LD_LIBRARY_PATH_ORIG", None)
    env.pop("LD_LIBRARY_PATH", None)
    if original:
        env["LD_LIBRARY_PATH"] = original
    env.pop("PYTHONPATH", None)
    return env


def install_command(package: Path, selection: Selection) -> list[str]:
    packages = [str(package.resolve())]
    if selection.network_tools:
        packages += ["iputils-ping", "arping", "smbclient", "xdg-utils", "openssh-client"]
    if selection.completion:
        packages.append("bash-completion")
    # apt resolves the DEB's GUI dependencies and reports network/package-manager errors.
    return [
        "/usr/bin/pkexec",
        "/usr/bin/apt-get",
        "install",
        "--yes",
        "--no-install-recommends",
        *packages,
    ]


def write_shortcuts(selection: Selection, home: Path) -> None:
    """User-only integration; no shell startup file or global PATH is rewritten."""
    applications = home / ".local/share/applications"
    applications.mkdir(parents=True, exist_ok=True)
    entries = [("lanctl", "LANCTL", "/opt/lanctl/lanctl --gui", False)]
    if selection.ipgui:
        entries.append(("lanip", "LANIP", "/opt/lanctl/lanip --gui", False))
    if selection.events:
        entries.append(("lanmon", "LANMON", "/opt/lanctl/lanmon --tui", True))
    if selection.access_admin:
        entries.append(
            (
                "lanaccess",
                "LANACCESS",
                "sudo /usr/bin/env LANCTL_DATA_SCOPE=service /opt/lanctl/lanaccess --tui",
                True,
            )
        )
    for slug, title, command, terminal in entries:
        content = (
            f"[Desktop Entry]\nType=Application\nName={title}\nExec={command}\n"
            f"Terminal={str(terminal).lower()}\nCategories=Network;Utility;\n"
        )
        (applications / f"{slug}-setup.desktop").write_text(content)
        if slug == "lanctl" and selection.desktop:
            # xdg-user-dir respects localized Desktop directories.
            result = subprocess.run(
                ["xdg-user-dir", "DESKTOP"],
                capture_output=True,
                text=True,
                check=True,
                env=clean_environment(),
            )
            desktop = Path(result.stdout.strip())
            if not desktop.is_absolute() or desktop == home or not desktop.is_dir():
                raise ValueError("No desktop directory is configured")
            target = desktop / "LANCTL.desktop"
            target.write_text(content)
            target.chmod(0o755)
    completion = home / ".local/share/bash-completion/completions/lanctl"
    if selection.completion:
        completion.parent.mkdir(parents=True, exist_ok=True)
        completion.write_text(
            "# LANCTL installer: native Bash completion (Clink is Windows-only).\n"
            "_lanctl_setup_complete() {\n"
            "  local words='--gui --cli --tui --help --version lanip lanwire lanrack "
            "lanaccess lanmon settings language plugin monitor backend'\n"
            "  COMPREPLY=()\n"
            "  if (( COMP_CWORD == 1 )); then\n"
            '    mapfile -t COMPREPLY < <(compgen -W "$words" -- "${COMP_WORDS[COMP_CWORD]}")\n'
            "  fi\n}\ncomplete -F _lanctl_setup_complete lanctl\n"
        )
    elif completion.is_file() and "# LANCTL installer:" in completion.read_text():
        completion.unlink()
