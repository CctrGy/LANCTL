from __future__ import annotations

import re
import sys
from pathlib import Path


def numeric_version(version: str) -> tuple[int, int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-(?:alpha|beta|rc)\.(\d+))?", version)
    if not match:
        raise ValueError("invalid release version")
    return tuple(int(value or 0) for value in match.groups())


def render(version: str, revision: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("invalid Git revision")
    numbers = numeric_version(version)
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers}, prodvers={numbers}, mask=0x3f,
    flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable(u'040904B0', [
    StringStruct(u'CompanyName', u'LANCTL Project'),
    StringStruct(u'FileDescription', u'LANCTL - LAN Control'),
    StringStruct(u'FileVersion', u'{version}'),
    StringStruct(u'InternalName', u'LANCTL'),
    StringStruct(u'LegalCopyright', u'Copyright © 2026 Victor'),
    StringStruct(u'OriginalFilename', u'LANCTL.exe'),
    StringStruct(u'ProductName', u'LANCTL'),
    StringStruct(u'ProductVersion', u'{version}'),
    StringStruct(u'Comments', u'Git revision {revision}'),
    StringStruct(u'PrivateBuild', u'{revision}')
  ])]), VarFileInfo([VarStruct(u'Translation', [1033, 1200])])]
)
"""


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: generate-windows-version-info.py VERSION REVISION OUTPUT")
    destination = Path(sys.argv[3])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(sys.argv[1], sys.argv[2]), encoding="utf-8", newline="\n")
