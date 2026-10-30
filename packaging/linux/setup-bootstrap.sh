#!/usr/bin/env bash
# Self-extracting LANCTL Linux wizard. The generated archive follows the marker.
set -euo pipefail
if [[ ${1:-} == --help ]]; then
    echo 'LANCTL Linux setup: run as your desktop user, without sudo.'
    echo 'Uso: bash LANCTL-*-linux-*-setup.run [--check | --extract NEW_DIRECTORY]'
    exit 0
fi
if [[ ${1:-} == --extract ]]; then
    [[ $# == 2 && ! -e $2 ]] || { echo 'Choose a new destination directory.' >&2; exit 2; }
    mkdir -m 700 -- "$2"
    destination=$(cd -- "$2" && pwd)
else
    [[ $# == 0 || ( $# == 1 && $1 == --check ) ]] || { echo 'Unknown option.' >&2; exit 2; }
    destination=$(mktemp -d /tmp/lanctl-setup.XXXXXXXX)
    trap 'rm -rf -- "$destination"' EXIT
fi
archive_line=$(awk '/^__LANCTL_ARCHIVE_BELOW__$/ { print NR + 1; exit }' "$0")
tail -n +"$archive_line" "$0" | tar -xf - -C "$destination"
if [[ ${1:-} == --extract ]]; then
    printf 'Extracted to: %s\n' "$destination"
    exit 0
fi
# The service account helper drops root and must still load its bundled runtime.
# The extracted directory contains application code/packages only, never credentials.
chmod 0711 -- "$destination"
cd -- "$destination"
sha256sum --check SHA256SUMS.txt
if [[ ${1:-} != --check ]]; then
    [[ $EUID != 0 ]] || { echo 'Run without sudo / Ejecuta sin sudo.' >&2; exit 2; }
    [[ -n ${DISPLAY:-}${WAYLAND_DISPLAY:-} ]] || { echo 'A graphical desktop session is required / Se requiere una sesión gráfica.' >&2; exit 2; }
    # Qt is bundled; these small system libraries and Polkit may still be absent.
    missing=()
    command -v pkexec >/dev/null || missing+=(pkexec)
    command -v xdg-user-dir >/dev/null || missing+=(xdg-user-dirs)
    if ldd wizard/_internal/PyQt6/Qt6/plugins/platforms/libqxcb.so | grep -q 'not found'; then
        missing+=(libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libegl1 libgl1)
    fi
    if (( ${#missing[@]} )); then
        echo 'Installing setup prerequisites / Instalando requisitos del asistente…'
        if command -v pkexec >/dev/null; then
            pkexec /usr/bin/apt-get install --yes "${missing[@]}"
        elif [[ -t 0 ]]; then
            sudo /usr/bin/apt-get install --yes "${missing[@]}"
        else
            echo 'Open a terminal and run / Abre una terminal y ejecuta:' >&2
            printf 'sudo apt-get install pkexec xdg-user-dirs\n' >&2
            echo 'Then run this setup again / Después vuelve a abrir este instalador.' >&2
            exit 2
        fi
    fi
fi
command -v dpkg-deb >/dev/null || { echo 'This installer requires Debian/Ubuntu and APT.' >&2; exit 2; }
./wizard/lanctl-setup --distribution "$destination" "$@"
exit $?
__LANCTL_ARCHIVE_BELOW__
