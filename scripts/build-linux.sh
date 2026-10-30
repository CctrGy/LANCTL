#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-0.3.4-alpha.2}"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)\.[0-9]+)?$ ]] || { echo 'Invalid version' >&2; exit 2; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
python3 scripts/verify-version.py "$VERSION"
python3 tools/generate_installer_languages.py --check
if [[ "${ALLOW_DIRTY:-0}" != 1 ]] && [[ -n "$(git status --porcelain)" ]]; then
  echo 'Working tree is dirty; commit changes or use ALLOW_DIRTY=1 for a local test build' >&2
  exit 2
fi
case "$(uname -m)" in x86_64|amd64) ARCH=amd64;; aarch64|arm64) ARCH=arm64;; *) echo 'Unsupported architecture' >&2; exit 1;; esac
python3 -m PyInstaller --clean --noconfirm LANCTL.spec
bash scripts/package-linux.sh "$VERSION"
