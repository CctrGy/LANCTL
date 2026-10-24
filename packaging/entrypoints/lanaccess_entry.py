"""Entrada PyInstaller de LANACCESS."""

from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()
    from lanctl.bootstrap.lanaccess import main

    raise SystemExit(main())
