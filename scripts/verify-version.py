from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "lanctl" / "__init__.py"


def declared_versions() -> tuple[str, str]:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project_section = re.search(r"(?ms)^\[project\]\s*$\n(.*?)(?=^\[|\Z)", project)
    version_match = (
        re.search(r'^version\s*=\s*["\']([^"\']+)["\']\s*$', project_section.group(1), re.MULTILINE)
        if project_section
        else None
    )
    if version_match is None:
        raise SystemExit("pyproject.toml does not declare project.version")
    package_version = version_match.group(1)
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']\s*$', source, re.MULTILINE)
    if match is None:
        raise SystemExit("src/lanctl/__init__.py does not declare __version__")
    return package_version, match.group(1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify-version.py VERSION")
    requested = sys.argv[1].removeprefix("v")
    package_version, source_version = declared_versions()
    if len({requested, package_version, source_version}) != 1:
        raise SystemExit(
            "version mismatch: "
            f"requested={requested}, pyproject={package_version}, application={source_version}"
        )
    print(f"verified application version {requested}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
