# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files


datas = collect_data_files("manuf") + [
    ("gui", "gui"),
    ("bundled/lanctl.theme.default.lcp", "bundled"),
    ("bundled/lanctl.discovery.windows-smb.lcp", "bundled"),
    ("bundled/lanctl.network.wol.lcp", "bundled"),
    ("bundled/recurrent-elements.json", "bundled"),
    ("assets/lanctl-icon-v2.png", "assets"),
    ("assets/device-icons", "assets/device-icons"),
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["paramiko", "cryptography"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LANCTL",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon="assets/lanctl-v2.ico",
    version="packaging/windows_version_info.txt",
)
