"""Best-effort native Windows caption styling; native window controls remain intact."""

import sys


def apply_dark_caption(window):
    if sys.platform != "win32":
        return
    import ctypes

    try:
        handle = int(window.native.Handle.ToInt64())
        dwm = ctypes.windll.dwmapi
        for attribute, value in ((20, 1), (35, 0x171410), (36, 0xF5F2EE)):
            number = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(
                ctypes.c_void_p(handle), attribute, ctypes.byref(number), ctypes.sizeof(number)
            )
    except (AttributeError, OSError, TypeError, ValueError):
        # Earlier Windows versions / other WebView backends retain their native caption.
        return
