"""Build a locally signed Terminal Integration package; never publish the key."""

import os
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lanctl.core.plugins.package import build_package  # noqa: E402


def main():
    key = Path(os.environ["LOCALAPPDATA"]) / "LANCTL/publisher-keys/terminal-integration.pem"
    key.parent.mkdir(parents=True, exist_ok=True)
    identity = subprocess.check_output(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value",
        ],
        text=True,
    ).strip()
    subprocess.run(
        [
            "icacls",
            str(key.parent),
            "/inheritance:r",
            "/grant:r",
            f"*{identity}:(OI)(CI)F",
            "*S-1-5-18:(OI)(CI)F",
        ],
        check=True,
    )
    if not key.exists():
        private = Ed25519PrivateKey.generate()
        with key.open("xb") as stream:
            stream.write(
                private.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
    result = build_package(
        ROOT / "plugins-src/lanctl.integration.terminal",
        ROOT / "dist/plugins/lanctl.integration.terminal-1.0.0.lcp",
        overwrite=True,
        signing_key=key,
    )
    print(result["path"])
    print(result["signature"])


if __name__ == "__main__":
    main()
