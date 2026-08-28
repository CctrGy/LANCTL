"""Entrada de desarrollo de LANWIRE sin requerir instalación previa."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from lanctl.bootstrap.lanwire import main

if __name__ == "__main__":
    raise SystemExit(main())
