"""Entrada de desarrollo de LANIP sin requerir instalación previa."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from lanctl.bootstrap.lanip import main

if __name__ == "__main__":
    raise SystemExit(main())
