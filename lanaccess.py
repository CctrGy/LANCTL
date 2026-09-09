"""Lanzador de desarrollo de LANACCESS."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from lanctl.bootstrap.lanaccess import main

if __name__ == "__main__":
    raise SystemExit(main())
