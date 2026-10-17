"""Best-effort native Windows caption styling; native window controls remain intact."""

import sys

from lanctl.core.resources import bundled_path


def webview_icon_path(launcher: str) -> str:
    """WinForms constructs System.Drawing.Icon directly, so Windows requires ICO."""
    suffix = "ico" if sys.platform == "win32" else "png"
    return str(bundled_path(f"assets/launcher-icons/{launcher}.{suffix}"))


def apply_dark_caption(window, launcher="lanctl"):
    if sys.platform != "win32":
        return
    import ctypes

    try:
        handle = int(window.native.Handle.ToInt64())
        from lanctl.core.window_icons import apply_window_icon

        apply_window_icon(handle, launcher)
        dwm = ctypes.windll.dwmapi
        for attribute, value in ((20, 1), (35, 0x171410), (36, 0xF5F2EE)):
            number = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(
                ctypes.c_void_p(handle), attribute, ctypes.byref(number), ctypes.sizeof(number)
            )
    except (AttributeError, OSError, TypeError, ValueError):
        # Earlier Windows versions / other WebView backends retain their native caption.
        return
