from __future__ import annotations

import ctypes
import os

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


def copy_text(value: str) -> None:
    """Copia Unicode al portapapeles de Windows sin dependencias externas."""

    if os.name != "nt":
        raise OSError("el portapapeles del TUI solo está disponible en Windows")
    data = (str(value) + "\0").encode("utf-16-le")
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = (ctypes.c_uint, ctypes.c_size_t)
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = (ctypes.c_void_p,)
    kernel32.GlobalUnlock.argtypes = (ctypes.c_void_p,)
    kernel32.GlobalFree.argtypes = (ctypes.c_void_p,)
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = (ctypes.c_uint, ctypes.c_void_p)
    if not user32.OpenClipboard(None):
        raise OSError("Windows no ha permitido abrir el portapapeles")
    handle = None
    try:
        if not user32.EmptyClipboard():
            raise OSError("no se ha podido vaciar el portapapeles")
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            raise MemoryError("no se pudo reservar memoria para el portapapeles")
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise OSError("no se pudo bloquear la memoria del portapapeles")
        try:
            ctypes.memmove(pointer, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise OSError("Windows ha rechazado los datos del portapapeles")
        handle = None  # Windows pasa a ser propietario de la memoria.
    finally:
        if handle:
            kernel32.GlobalFree(handle)
        user32.CloseClipboard()
