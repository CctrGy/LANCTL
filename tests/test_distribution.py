import unittest
from pathlib import Path
from unittest import mock

from app.distribution.release import (
    artifact_name,
    classify_channel,
    normalize_architecture,
    validate_version,
)


class DistributionTests(unittest.TestCase):
    def test_versions_and_channels_are_closed(self):
        self.assertEqual(validate_version("v0.3.0-beta.2"), "0.3.0-beta.2")
        self.assertEqual(classify_channel("0.3.0-beta.2"), "beta")
        self.assertEqual(classify_channel("1.0.0"), "stable")
        for value in ("latest", "../../bad", "1.0", "1.0.0-evil.1"):
            with self.assertRaises(ValueError):
                validate_version(value)

    def test_architecture_and_artifact_selection(self):
        self.assertEqual(normalize_architecture("aarch64"), "arm64")
        self.assertEqual(
            artifact_name("0.3.0-beta.2", "Windows", "amd64"),
            "LANCTL-0.3.0-beta.2-windows-x64-setup.exe",
        )
        self.assertEqual(
            artifact_name("0.3.0-beta.2", "Linux", "arm64"), "lanctl_0.3.0-beta.2_arm64.deb"
        )
        self.assertEqual(
            artifact_name("0.3.0-beta.2", "Linux", "amd64", True),
            "LANCTL-0.3.0-beta.2-linux-amd64.tar.gz",
        )
        with self.assertRaises(ValueError):
            artifact_name("1.0.0", "Windows", "arm64")

    def test_installers_verify_hashes_and_do_not_evaluate_downloaded_content(self):
        root = Path(__file__).resolve().parents[1]
        powershell = (root / "install.ps1").read_text(encoding="utf-8")
        shell = (root / "install.sh").read_text(encoding="utf-8")
        self.assertIn("Assert-Hash", powershell)
        self.assertIn("Expand-SafeZip", powershell)
        self.assertNotIn("Invoke-Expression", powershell)
        self.assertIn("sha256sum --check --strict", shell)
        self.assertIn("Unsafe tar entry", shell)
        self.assertNotIn("eval ", shell)
        self.assertNotIn("source ", shell)

    def test_updates_preserve_data_and_access_is_never_silent(self):
        root = Path(__file__).resolve().parents[1]
        powershell = (root / "install.ps1").read_text(encoding="utf-8")
        shell = (root / "install.sh").read_text(encoding="utf-8")
        self.assertIn("preserve projects/configuration", powershell)
        self.assertNotIn("ProgramData\\LANCTL", powershell)
        self.assertIn("setup-wizard requires an interactive terminal", shell)
        self.assertNotIn("enable ssh", shell)
        self.assertNotIn("enable https", shell)
        self.assertIn("setup-wizard --scope service", shell)
        self.assertIn("setup-wizard --scope user", shell)
        self.assertIn("'--scope','service'", powershell)

    def test_linux_portable_and_service_use_distinct_valid_paths(self):
        root = Path(__file__).resolve().parents[1]
        shell = (root / "install.sh").read_text(encoding="utf-8")
        build = (root / "scripts/build-linux.sh").read_text(encoding="utf-8")
        unit = (root / "packaging/systemd/lanctl-monitor.service").read_text(encoding="utf-8")
        self.assertIn("$target/LANCTL/lanctl", shell)
        self.assertIn("$PORTABLE/LANCTL/lanctl", build)
        self.assertIn("LANCTL_DATA_DIR=/var/lib/lanctl", unit)
        self.assertIn("LANCTL_SECRET_DIR=/etc/lanctl/access", unit)
        self.assertIn(
            "-m 0770 /etc/lanctl/access",
            (root / "packaging/debian/postinst").read_text(encoding="utf-8"),
        )

    def test_frozen_standard_and_portable_data_roots(self):
        import app.core.paths as paths

        with (
            mock.patch.object(paths.sys, "frozen", True, create=True),
            mock.patch.object(paths.sys, "executable", r"C:\Program Files\LANCTL\LANCTL.exe"),
            mock.patch.object(paths.platform, "system", return_value="Windows"),
            mock.patch.dict(
                paths.os.environ,
                {
                    "PROGRAMDATA": r"C:\ProgramData",
                    "LOCALAPPDATA": r"C:\Users\tester\AppData\Local",
                },
                clear=False,
            ),
        ):
            self.assertIn("ProgramData", str(paths.application_path("data/lc/monitor.db")))
            self.assertIn("AppData", str(paths.application_path("data/lc/access/config.json")))

    def test_onefile_and_clean_installer_contract(self):
        root = Path(__file__).resolve().parents[1]
        spec = (root / "LANCTL.spec").read_text(encoding="utf-8")
        build = (root / "scripts/build-windows.ps1").read_text(encoding="utf-8")
        inno = (root / "packaging/inno/LANCTL.iss").read_text(encoding="utf-8")
        self.assertNotIn("COLLECT(", spec)
        self.assertIn("a.datas", spec)
        self.assertIn("dist\\LANCTL.exe", build)
        self.assertIn("dist\\LANCTL-GUI.exe", build)
        self.assertNotIn("_internal", build)
        self.assertIn('Source: "{#BuildRoot}\\LANCTL.exe"', inno)
        self.assertNotIn("recursesubdirs", inno)
        self.assertIn('Source: "{#BuildRoot}\\LANCTL-GUI.exe"', inno)
        self.assertIn('Filename: "{app}\\LANCTL-GUI.exe"', inno)
        self.assertNotIn("recurrent-elements.json", spec)
        self.assertIn("{commonappdata}\\LANCTL\\database", inno)
        self.assertIn("admins-full system-full", inno)

    def test_github_actions_enforce_quality_and_security_gates(self):
        root = Path(__file__).resolve().parents[1]
        release = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
        ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        security = (root / ".github/workflows/security.yml").read_text(encoding="utf-8")
        for expected in ("--fail-under=60", "ruff check", "bandit", "pip_audit", "shellcheck"):
            self.assertIn(expected, release)
        for expected in ("pull_request", "--source=app", "pip_audit", "git diff --check"):
            self.assertIn(expected, ci)
        self.assertIn("--ignore-vuln PYSEC-2026-3552", ci)
        self.assertIn("--ignore-vuln PYSEC-2026-2858", ci)
        app_source = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (root / "app").rglob("*.py")
        )
        self.assertNotIn("pkcs7_decrypt_", app_source)
        self.assertIn("github/codeql-action/analyze", security)
        self.assertIn("dependency-review-action", security)
        self.assertTrue((root / ".github/dependabot.yml").is_file())


if __name__ == "__main__":
    unittest.main()
