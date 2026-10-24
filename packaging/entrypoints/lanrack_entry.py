"""Entrada PyInstaller de LANRACK."""

from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()
    from lanctl.bootstrap.lanrack import main

    raise SystemExit(main())
