"""GUI subsystem entry point; no console allocation or terminal manipulation."""

from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()
    from lanctl.bootstrap.gui import main

    raise SystemExit(main())
