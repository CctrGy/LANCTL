#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-0.3.2-beta.4}"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)\.[0-9]+)?$ ]] || { echo 'Invalid version' >&2; exit 2; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
python3 scripts/verify-version.py "$VERSION"
REVISION="$(git rev-parse HEAD)"
if [[ "${ALLOW_DIRTY:-0}" != 1 ]] && [[ -n "$(git status --porcelain)" ]]; then
  echo 'Working tree is dirty; commit changes or use ALLOW_DIRTY=1 for a local test build' >&2
  exit 2
fi
case "$(uname -m)" in x86_64|amd64) ARCH=amd64;; aarch64|arm64) ARCH=arm64;; *) echo 'Unsupported architecture' >&2; exit 1;; esac
python3 -m PyInstaller --clean --noconfirm LANCTL.spec
OUT="$ROOT/dist/release"; rm -rf -- "$OUT"; mkdir -p "$OUT"
PORTABLE="$ROOT/dist/portable-staging"; rm -rf -- "$PORTABLE"; mkdir -p "$PORTABLE/LANCTL"
install -m 0755 dist/LANCTL "$PORTABLE/LANCTL/lanctl"
install -m 0755 dist/lanip "$PORTABLE/LANCTL/lanip"
install -m 0755 dist/lanwire "$PORTABLE/LANCTL/lanwire"
install -m 0755 dist/lanmon "$PORTABLE/LANCTL/lanmon"
install -m 0755 dist/lanrack "$PORTABLE/LANCTL/lanrack"
install -m 0755 dist/lanaccess "$PORTABLE/LANCTL/lanaccess"
install -m 0644 packaging/portable/README-linux.txt "$PORTABLE/LANCTL/README-portable.txt"
printf '%s\n' 'LANCTL-PORTABLE-V1' > "$PORTABLE/LANCTL/LANCTL.portable"
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/LANCTL-$VERSION-linux-$ARCH.tar.gz" -C "$PORTABLE" LANCTL
PKG="$(mktemp -d -t lanctl-deb.XXXXXXXX)"; trap 'rm -rf -- "$PKG"' EXIT
mkdir -p "$PKG/DEBIAN" "$PKG/opt/lanctl" "$PKG/usr/bin" "$PKG/lib/systemd/system" \
  "$PKG/usr/share/doc/lanctl"
sed -e "s/@VERSION@/$VERSION/g" -e "s/@ARCH@/$ARCH/g" packaging/debian/control > "$PKG/DEBIAN/control"
install -m 0755 packaging/debian/postinst packaging/debian/prerm packaging/debian/postrm "$PKG/DEBIAN/"
install -m 0755 dist/LANCTL "$PKG/opt/lanctl/lanctl"
install -m 0755 dist/lanip "$PKG/opt/lanctl/lanip"
install -m 0755 dist/lanwire "$PKG/opt/lanctl/lanwire"
install -m 0755 dist/lanmon "$PKG/opt/lanctl/lanmon"
install -m 0755 dist/lanrack "$PKG/opt/lanctl/lanrack"
install -m 0755 dist/lanaccess "$PKG/opt/lanctl/lanaccess"
ln -s /opt/lanctl/lanctl "$PKG/usr/bin/lanctl"
ln -s /opt/lanctl/lanip "$PKG/usr/bin/lanip"
ln -s /opt/lanctl/lanwire "$PKG/usr/bin/lanwire"
ln -s /opt/lanctl/lanmon "$PKG/usr/bin/lanmon"
ln -s /opt/lanctl/lanrack "$PKG/usr/bin/lanrack"
ln -s /opt/lanctl/lanaccess "$PKG/usr/bin/lanaccess"
install -m 0644 packaging/systemd/lanctl-monitor.service "$PKG/lib/systemd/system/lanctl-monitor.service"
install -m 0644 docs/INSTALL.md "$PKG/usr/share/doc/lanctl/INSTALL.md"
install -m 0644 docs/BETA-TESTING.md "$PKG/usr/share/doc/lanctl/BETA-TESTING.md"
install -m 0644 docs/KNOWN-ISSUES.md "$PKG/usr/share/doc/lanctl/KNOWN-ISSUES.md"
dpkg-deb --root-owner-group --build "$PKG" "$OUT/lanctl_${VERSION}_${ARCH}.deb"
python3 scripts/release-metadata.py "$VERSION" "$REVISION" "$OUT"
python3 scripts/generate-hashes.py "$OUT"
python3 scripts/verify-release.py "$OUT"
