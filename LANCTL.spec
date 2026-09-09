# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


PROJECT_ROOT = Path(SPECPATH)
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))
VERSION_INFO = os.environ.get("LANCTL_VERSION_INFO", "packaging/windows_version_info.txt")
LEGACY_GUI_EXCLUDES = ["webview"]


def collect_runtime_modules():
    """Incluye el núcleo RPC reutilizado por remoto, pero no su motor visual."""
    return collect_submodules("lanctl")


datas = collect_data_files("manuf") + [
    ("bundled/lanctl.theme.default.lcp", "bundled"),
    ("bundled/lanctl.analysis.mac-vendor.lcp", "bundled"),
    ("bundled/lanctl.discovery.mdns-ssdp.lcp", "bundled"),
    ("bundled/lanctl.discovery.windows-smb.lcp", "bundled"),
    ("bundled/lanctl.network.wol.lcp", "bundled"),
    ("bundled/lanctl.lab.network-emulator.lcp", "bundled"),
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
    hiddenimports=["paramiko", "cryptography"] + collect_runtime_modules(),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=LEGACY_GUI_EXCLUDES,
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

# Entrada directa de la aplicación lógica LANIP. El orquestador LANCTL y este
# ejecutable consumen exactamente el mismo paquete de aplicación.
ip_a = Analysis(
    ["packaging/entrypoints/lanip_entry.py"],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=datas,
    # LANIP aún expone comandos compartidos de proyectos, acceso y monitor
    # durante la transición, por lo que empaqueta la suite completa.
    hiddenimports=["paramiko", "cryptography"] + collect_runtime_modules(),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=LEGACY_GUI_EXCLUDES,
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
    hiddenimports=["paramiko", "cryptography"] + collect_runtime_modules(),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=LEGACY_GUI_EXCLUDES,
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

rack_a = Analysis(
    ["packaging/entrypoints/lanrack_entry.py"],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["paramiko", "cryptography"] + collect_runtime_modules(),
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=LEGACY_GUI_EXCLUDES,
    noarchive=False, optimize=0,
)
rack_pyz = PYZ(rack_a.pure)
rack_exe = EXE(
    rack_pyz, rack_a.scripts, rack_a.binaries, rack_a.datas, [], name="lanrack",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=True,
    icon="assets/lanctl-v3.ico", version=VERSION_INFO,
)

access_a = Analysis(
    ["packaging/entrypoints/lanaccess_entry.py"],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["paramiko", "cryptography"] + collect_runtime_modules(),
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=LEGACY_GUI_EXCLUDES,
    noarchive=False, optimize=0,
)
access_pyz = PYZ(access_a.pure)
access_exe = EXE(
    access_pyz, access_a.scripts, access_a.binaries, access_a.datas, [], name="lanaccess",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=True,
    icon="assets/lanctl-v3.ico", version=VERSION_INFO,
)
