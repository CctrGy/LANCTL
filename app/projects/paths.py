from __future__ import annotations

import ctypes
import os
from pathlib import Path
from uuid import UUID


FOLDERID_DOCUMENTS = UUID("fdd39ad0-238f-46af-adb4-6c85480369c7")
LEGACY_PROJECTS_DIRECTORY = r"%USERPROFILE%\Documents\LanCTL"


class _Guid(ctypes.Structure):
    _fields_ = (
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    )


def _guid(value: UUID) -> _Guid:
    fields = value.fields
    tail = bytes((fields[3], fields[4])) + fields[5].to_bytes(6, "big")
    return _Guid(fields[0], fields[1], fields[2], (ctypes.c_ubyte * 8)(*tail))


def _known_documents_directory() -> Path | None:
    """Consulta FOLDERID_Documents, incluida su redirección a OneDrive."""
    if os.name != "nt":
        return None
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    ole32 = ctypes.WinDLL("ole32", use_last_error=True)
    path = ctypes.c_wchar_p()
    folder_id = _guid(FOLDERID_DOCUMENTS)
    shell32.SHGetKnownFolderPath.argtypes = (
        ctypes.POINTER(_Guid), ctypes.c_uint32, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_wchar_p),
    )
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long
    result = shell32.SHGetKnownFolderPath(
        ctypes.byref(folder_id), 0, None, ctypes.byref(path)
    )
    if result != 0 or not path.value:
        return None
    try:
        return Path(path.value)
    finally:
        ole32.CoTaskMemFree(path)


def windows_documents_directory() -> Path:
    """Documentos real del usuario, aunque Windows lo redirija a OneDrive."""
    try:
        known = _known_documents_directory()
    except (AttributeError, OSError):
        known = None
    if known is not None:
        return known
    profile = os.environ.get("USERPROFILE")
    return (Path(profile) if profile else Path.home()) / "Documents"


def default_project_directory() -> Path:
    return windows_documents_directory() / "LanCTL"


def resolve_project_path(
    value: str | Path, configured_directory: str | Path | None = None
) -> Path:
    """Las rutas relativas pertenecen a Documentos/LanCTL."""
    expanded = Path(os.path.expandvars(str(value))).expanduser()
    if not expanded.is_absolute():
        configured = str(configured_directory or "")
        use_known_documents = (
            not configured
            or configured.replace("/", "\\").casefold()
            == LEGACY_PROJECTS_DIRECTORY.casefold()
        )
        root = (
            default_project_directory()
            if use_known_documents
            else Path(os.path.expandvars(configured)).expanduser()
        )
        expanded = root / expanded
    if expanded.suffix.casefold() != ".vlf":
        expanded = expanded.with_suffix(".vlf")
    return expanded.resolve()
