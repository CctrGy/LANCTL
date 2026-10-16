"""Local icon resources for native captions and classic Windows consoles."""

import sys

from lanctl.core.resources import bundled_path

_handles = {}  # Keep HICON resources alive for the process lifetime.


def icon_path(name):
    return bundled_path(f"assets/launcher-icons/{name}.ico")


def apply_window_icon(handle, name):
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes

    user = ctypes.windll.user32
    user.LoadImageW.argtypes = [
        wintypes.HINSTANCE,
        wintypes.LPCWSTR,
        wintypes.UINT,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user.LoadImageW.restype = wintypes.HANDLE
    user.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.SendMessageW.restype = ctypes.c_ssize_t
    for kind, size in ((0, 16), (1, 32)):
        key = (name, size)
        if key not in _handles:
            _handles[key] = user.LoadImageW(None, str(icon_path(name)), 1, size, size, 0x10)
        if _handles[key]:
            user.SendMessageW(handle, 0x80, kind, _handles[key])


def apply_terminal_icon(launcher):
    if sys.platform != "win32" or not sys.stdout.isatty():
        return
    import ctypes

    kernel = ctypes.windll.kernel32
    kernel.GetConsoleWindow.restype = ctypes.c_void_p
    kernel.SetConsoleTitleW(f"{launcher.upper()} · Terminal")
    handle = kernel.GetConsoleWindow()
    if handle:
        apply_window_icon(handle, "terminal")
