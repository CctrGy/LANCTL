from __future__ import annotations
import hashlib,re,sys
from pathlib import Path

root=Path(sys.argv[1] if len(sys.argv)>1 else "dist/release")
files=sorted(path for path in root.iterdir() if path.is_file() and path.name!="SHA256SUMS.txt")
if not files:raise SystemExit("no release artifacts")
for path in files:
    if not re.fullmatch(r"(?:LANCTL-.+|lanctl_.+|install\.(?:ps1|sh)|release-metadata\.json)",path.name):raise SystemExit(f"unexpected artifact: {path.name}")
lines=[f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in files]
(root/"SHA256SUMS.txt").write_text("\n".join(lines)+"\n",encoding="ascii",newline="\n")
print("\n".join(lines))
