from __future__ import annotations

import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/release")
files = sorted(
    path
    for path in root.iterdir()
    if path.is_file() and path.name not in {"SHA256SUMS.txt", "SHA256SUMS.txt.asc"}
)
if not files:
    raise SystemExit("no release artifacts")
lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in files]
(root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
print("\n".join(lines))
