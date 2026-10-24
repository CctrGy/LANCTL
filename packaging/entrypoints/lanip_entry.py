"""Entrada PyInstaller de LANIP."""

from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()
    from lanctl.bootstrap.lanip import main

    raise SystemExit(main())
