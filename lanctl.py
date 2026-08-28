"""Entrada de desarrollo de la suite LANCTL sin instalación previa."""

import sys
from pathlib import Path

_SOURCE_ROOT = Path(__file__).resolve().parent / "src"
_PACKAGE_ROOT = _SOURCE_ROOT / "lanctl"
sys.path.insert(0, str(_SOURCE_ROOT))

# El lanzador histórico comparte nombre con el paquete. Al importarse desde el
# checkout (por ejemplo durante pytest), se comporta también como el paquete
# ``lanctl`` para no eclipsar el src-layout.
if __name__ == "lanctl":
    __path__ = [str(_PACKAGE_ROOT)]
    exec(
        compile(
            (_PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8"),
            str(_PACKAGE_ROOT / "__init__.py"),
            "exec",
        ),
        globals(),
    )

from lanctl.bootstrap.lanctl import main  # noqa: E402 - src-layout bootstrap

if __name__ == "__main__":
    raise SystemExit(main())
