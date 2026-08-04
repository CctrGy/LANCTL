#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-0.3.0-beta.3}"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)\.[0-9]+)?$ ]] || { echo 'Invalid version' >&2; exit 2; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
case "$(uname -m)" in x86_64|amd64) ARCH=amd64;; aarch64|arm64) ARCH=arm64;; *) echo 'Unsupported architecture' >&2; exit 1;; esac
python3 -m PyInstaller --clean --noconfirm LANCTL.spec
OUT="$ROOT/dist/release"; mkdir -p "$OUT"
PORTABLE="$ROOT/dist/portable-staging"; rm -rf -- "$PORTABLE"; mkdir -p "$PORTABLE/LANCTL"
install -m 0755 dist/LANCTL "$PORTABLE/LANCTL/lanctl"
install -m 0644 packaging/portable/README-portable.txt "$PORTABLE/LANCTL/README-portable.txt"
printf '%s\n' 'LANCTL-PORTABLE-V1' > "$PORTABLE/LANCTL/LANCTL.portable"
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/LANCTL-$VERSION-linux-$ARCH.tar.gz" -C "$PORTABLE" LANCTL
PKG="$(mktemp -d -t lanctl-deb.XXXXXXXX)"; trap 'rm -rf -- "$PKG"' EXIT
mkdir -p "$PKG/DEBIAN" "$PKG/opt/lanctl" "$PKG/usr/bin" "$PKG/lib/systemd/system"
sed -e "s/@VERSION@/$VERSION/g" -e "s/@ARCH@/$ARCH/g" packaging/debian/control > "$PKG/DEBIAN/control"
install -m 0755 packaging/debian/postinst packaging/debian/prerm "$PKG/DEBIAN/"
install -m 0755 dist/LANCTL "$PKG/opt/lanctl/lanctl"
ln -s /opt/lanctl/lanctl "$PKG/usr/bin/lanctl"
install -m 0644 packaging/systemd/lanctl-monitor.service "$PKG/lib/systemd/system/lanctl-monitor.service"
dpkg-deb --root-owner-group --build "$PKG" "$OUT/lanctl_${VERSION}_${ARCH}.deb"
