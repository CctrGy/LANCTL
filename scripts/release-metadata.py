from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

# Al ejecutarse como ``python scripts/release-metadata.py``, Python sitúa
# scripts/ (no la raíz del checkout) en sys.path. Añadimos explícitamente la
# raíz para que el script funcione igual en GitHub Actions y localmente.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.distribution.release import validate_version

version=validate_version(sys.argv[1]);revision=sys.argv[2]
if len(revision)!=40 or any(character not in "0123456789abcdef" for character in revision.casefold()):raise SystemExit("invalid revision")
root=Path(sys.argv[3]);payload={"schemaVersion":1,"version":version,"revision":revision,"createdAt":datetime.now(timezone.utc).isoformat(),"artifacts":sorted(path.name for path in root.iterdir() if path.is_file())}
(root/"release-metadata.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8",newline="\n")
