# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


PROJECT_ROOT = Path(SPECPATH)
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))
VERSION_INFO = os.environ.get("LANCTL_VERSION_INFO", "packaging/windows_version_info.txt")


datas = collect_data_files("manuf") + [
    ("gui", "gui"),
    ("bundled/lanctl.theme.default.lcp", "bundled"),
    ("bundled/lanctl.analysis.mac-vendor.lcp", "bundled"),
    ("bundled/lanctl.discovery.mdns-ssdp.lcp", "bundled"),
    ("bundled/lanctl.discovery.windows-smb.lcp", "bundled"),
    ("bundled/lanctl.network.wol.lcp", "bundled"),
    ("bundled/plugin-catalog.json", "bundled"),
    ("assets/lanctl-icon-v3.png", "assets"),
    ("assets/device-icons", "assets/device-icons"),
    ("errorList.txt", "."),
]

a = Analysis(
    ["packaging/entrypoints/lanctl_entry.py"],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=datas,
    # Los comandos se registran por nombre para mantener --help/--version
    # ligeros. PyInstaller no puede descubrir esos imports sin esta lista.
    hiddenimports=["paramiko", "cryptography"] + collect_submodules("lanctl"),
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
    icon="assets/lanctl-v3.ico",
    version=VERSION_INFO,
)

gui_exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LANCTL-GUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="assets/lanctl-v3.ico",
    version=VERSION_INFO,
)

# Entrada directa de la aplicación lógica LANIP. El orquestador LANCTL y este
# ejecutable consumen exactamente el mismo paquete de aplicación.
ip_a = Analysis(
    ["packaging/entrypoints/lanip_entry.py"],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=datas,
    # LANIP aún expone comandos compartidos de proyectos, acceso y monitor
    # durante la transición, por lo que empaqueta la suite completa.
    hiddenimports=["paramiko", "cryptography"] + collect_submodules("lanctl"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
ip_pyz = PYZ(ip_a.pure)

ip_exe = EXE(
    ip_pyz,
    ip_a.scripts,
    ip_a.binaries,
    ip_a.datas,
    [],
    name="lanip",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon="assets/lanctl-v3.ico",
    version=VERSION_INFO,
)

# LANWIRE es la segunda entrada de la misma suite. Mantiene su propio archivo
# raíz y ejecutable, pero consume el paquete físico y el contrato de rutas de
# este repositorio.
physical_a = Analysis(
    ["packaging/entrypoints/lanwire_entry.py"],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules("lanctl.apps.wire"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PIL", "numpy"],
    noarchive=False,
    optimize=0,
)
physical_pyz = PYZ(physical_a.pure)

physical_exe = EXE(
    physical_pyz,
    physical_a.scripts,
    physical_a.binaries,
    physical_a.datas,
    [],
    name="lanwire",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon="assets/lanctl-v3.ico",
    version=VERSION_INFO,
)

# Entradas especializadas para operaciones de monitorización y para el
# recorrido reproducible de presentación. Comparten el mismo núcleo LANCTL.
monitor_a = Analysis(
    ["packaging/entrypoints/lanmon_entry.py"],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["paramiko", "cryptography"] + collect_submodules("lanctl"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
monitor_pyz = PYZ(monitor_a.pure)
monitor_exe = EXE(
    monitor_pyz,
    monitor_a.scripts,
    monitor_a.binaries,
    monitor_a.datas,
    [],
    name="lanmon",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon="assets/lanctl-v3.ico",
    version=VERSION_INFO,
)

demo_a = Analysis(
    ["packaging/entrypoints/landemo_entry.py"],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["paramiko", "cryptography"] + collect_submodules("lanctl"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
demo_pyz = PYZ(demo_a.pure)
demo_exe = EXE(
    demo_pyz,
    demo_a.scripts,
    demo_a.binaries,
    demo_a.datas,
    [],
    name="landemo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon="assets/lanctl-v3.ico",
    version=VERSION_INFO,
)
