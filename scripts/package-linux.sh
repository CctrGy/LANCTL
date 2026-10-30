#!/usr/bin/env bash
# Package existing frozen launchers; also used by build-linux.sh after compilation.
set -euo pipefail
VERSION="${1:?usage: package-linux.sh VERSION}"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
python3 scripts/verify-version.py "$VERSION"
REVISION="$(git rev-parse HEAD)"
case "$(uname -m)" in x86_64|amd64) ARCH=amd64;; aarch64|arm64) ARCH=arm64;; *) exit 1;; esac
# Version checks are read-only and must not migrate or touch user data.
CHECK_DATA="$(mktemp -d -t lanctl-package-check.XXXXXXXX)"
trap 'rm -rf -- "$CHECK_DATA"' EXIT
mkdir -p "$CHECK_DATA/config"
printf '%s\n' LANCTL-DATA-V2 > "$CHECK_DATA/config/migration-v2.complete"
for launcher in LANCTL lanip lanwire lanmon lanrack lanaccess; do
    actual=$(LANCTL_DATA_DIR="$CHECK_DATA" "dist/$launcher" --version)
    [[ "$actual" == *" $VERSION" ]] || { echo "Version mismatch: $launcher" >&2; exit 2; }
done
rm -rf -- "$CHECK_DATA"
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
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner -I 'gzip -1' -cf "$OUT/LANCTL-$VERSION-linux-$ARCH.tar.gz" -C "$PORTABLE" LANCTL
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
dpkg-deb --root-owner-group -Zgzip -z1 --build "$PKG" "$OUT/lanctl_${VERSION}_${ARCH}.deb"
python3 scripts/build-linux-setup.py "$OUT/lanctl_${VERSION}_${ARCH}.deb"
python3 scripts/release-metadata.py "$VERSION" "$REVISION" "$OUT"
python3 scripts/generate-hashes.py "$OUT"
python3 scripts/verify-release.py "$OUT"
