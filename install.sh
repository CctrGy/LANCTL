#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="CctrGy/LANCTL"
CHANNEL="stable"; VERSION=""; MODE="standard"; CONFIGURE_ACCESS=0; ASSUME_YES=0; UNINSTALL=0; USE_TARBALL=0
usage() { cat <<'EOF'
LANCTL online installer
  ./install.sh [--channel stable|beta] [--version VERSION]
               [--mode standard|monitor] [--configure-access] [--yes]
               [--tarball] [--uninstall]
Remote access remains disabled unless its local interactive wizard succeeds.
EOF
}
while (($#)); do
  case "$1" in
    --channel) CHANNEL="${2:?missing channel}"; shift 2;;
    --version) VERSION="${2:?missing version}"; shift 2;;
    --mode) MODE="${2:?missing mode}"; shift 2;;
    --configure-access) CONFIGURE_ACCESS=1; shift;;
    --yes|-y) ASSUME_YES=1; shift;;
    --tarball) USE_TARBALL=1; shift;;
    --uninstall) UNINSTALL=1; shift;;
    --help|-h) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2;;
  esac
done
[[ "$CHANNEL" =~ ^(stable|beta)$ ]] || { echo 'Invalid channel' >&2; exit 2; }
[[ "$MODE" =~ ^(standard|monitor)$ ]] || { echo 'Invalid mode' >&2; exit 2; }
if [[ -n "$VERSION" && ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)\.[0-9]+)?$ ]]; then echo 'Invalid version' >&2; exit 2; fi
if ((UNINSTALL)); then
  ((ASSUME_YES)) || { read -r -p 'Uninstall LANCTL while preserving /var/lib/lanctl and /etc/lanctl? [y/N] ' answer; [[ "$answer" =~ ^[YySs]$ ]] || exit 1; }
  command -v apt-get >/dev/null || { echo 'DEB uninstall is unavailable on this platform' >&2; exit 1; }
  sudo apt-get remove lanctl
  exit 0
fi
for tool in curl sha256sum python3; do command -v "$tool" >/dev/null || { echo "Missing dependency: $tool" >&2; exit 1; }; done
api="https://api.github.com/repos/$REPOSITORY/releases"
if [[ -n "$VERSION" ]]; then release_url="$api/tags/v$VERSION"; else release_url="$api?per_page=50"; fi
tmp="$(mktemp -d -t lanctl-install.XXXXXXXX)"; trap 'rm -rf -- "$tmp"' EXIT INT TERM
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$release_url" -o "$tmp/release.json"
resolved="$(python3 - "$tmp/release.json" "$CHANNEL" "$VERSION" <<'PY'
import json,re,sys
data=json.load(open(sys.argv[1],encoding='utf-8')); channel=sys.argv[2]; requested=sys.argv[3]
items=[data] if isinstance(data,dict) else data
for item in items:
    if item.get('draft'): continue
    if not requested and bool(item.get('prerelease')) != (channel=='beta'): continue
    tag=item.get('tag_name','').removeprefix('v')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?',tag): raise SystemExit('Unsafe release tag')
    print(tag); break
else: raise SystemExit('No matching release')
PY
)"
case "$(uname -m)" in x86_64|amd64) arch=amd64;; aarch64|arm64) arch=arm64;; *) echo 'Unsupported architecture' >&2; exit 1;; esac
if ((USE_TARBALL)); then artifact="LANCTL-$resolved-linux-$arch.tar.gz"; else artifact="lanctl_${resolved}_${arch}.deb"; fi
if ((USE_TARBALL)) && [[ "$MODE" == monitor ]]; then echo 'Monitor mode requires the DEB package; portable tarballs do not install services.' >&2; exit 2; fi
base="https://github.com/$REPOSITORY/releases/download/v$resolved"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$base/$artifact" -o "$tmp/$artifact"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$base/SHA256SUMS.txt" -o "$tmp/SHA256SUMS.txt"
(cd "$tmp" && grep -E "^[0-9a-fA-F]{64}  ${artifact//./\\.}$" SHA256SUMS.txt > selected.sum && [[ -s selected.sum ]] && sha256sum --check --strict selected.sum)
if ((USE_TARBALL)); then
  python3 - "$tmp/$artifact" <<'PY'
import os,sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as archive:
    for member in archive.getmembers():
        if member.name.startswith('/') or '..' in member.name.split('/'): raise SystemExit('Unsafe tar entry')
PY
  staging="$(mktemp -d -p "$tmp" staging.XXXXXXXX)"; tar -xzf "$tmp/$artifact" -C "$staging"
  target="/opt/lanctl-$resolved"; [[ ! -e "$target" ]] || { echo "$target already exists" >&2; exit 1; }
  sudo install -d -m 0755 "$target"; sudo cp -a "$staging"/. "$target"/; sudo ln -sfn "$target/LANCTL/lanctl" /usr/local/bin/lanctl
else
  sudo apt-get install -y "$tmp/$artifact"
fi
if [[ "$MODE" == monitor ]]; then echo 'Monitor components installed. Attach a project before enabling lanctl-monitor.service.'; fi
if ((CONFIGURE_ACCESS)); then
  if ((ASSUME_YES)); then echo 'Remote access was not enabled: setup-wizard requires an interactive terminal.' >&2
  elif [[ "$MODE" == monitor ]]; then sudo lanctl access setup-wizard --scope service
  elif [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]]; then sudo -u "$SUDO_USER" lanctl access setup-wizard --scope user
  else lanctl access setup-wizard --scope user; fi
fi
