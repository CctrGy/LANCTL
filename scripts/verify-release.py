from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/release")
manifest = root / "SHA256SUMS.txt"
if not manifest.is_file():
    raise SystemExit("missing SHA256SUMS.txt; generate hashes before verification")
expected: dict[str, str] = {}
for line in manifest.read_text(encoding="ascii").splitlines():
    match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", line)
    if not match or match.group(2) in expected:
        raise SystemExit(f"invalid checksum line: {line}")
    expected[match.group(2)] = match.group(1)
files = sorted(
    path
    for path in root.iterdir()
    if path.is_file() and path.name not in {"SHA256SUMS.txt", "SHA256SUMS.txt.asc"}
)
if set(expected) != {path.name for path in files}:
    raise SystemExit("checksum manifest does not match the artifact set")
for path in files:
    if not re.fullmatch(
        r"(?:LANCTL-.+|lanctl_.+|install\.(?:ps1|sh)|release-metadata\.json)", path.name
    ):
        raise SystemExit(f"unexpected artifact: {path.name}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected[path.name]:
        raise SystemExit(f"checksum mismatch: {path.name}")
print(f"verified {len(files)} release artifacts")
