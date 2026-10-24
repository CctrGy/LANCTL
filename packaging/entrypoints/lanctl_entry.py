"""Entrada PyInstaller del orquestador LANCTL."""

from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()
    from lanctl.bootstrap.lanctl import main

    raise SystemExit(main())
