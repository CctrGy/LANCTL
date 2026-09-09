import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lanctl.infrastructure.distribution.release import (
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
        self.assertIn("$target/LANCTL/lanwire", shell)
        self.assertIn("$target/LANCTL/lanmon", shell)
        self.assertNotIn("$target/LANCTL/landemo", shell)
        self.assertIn("$PORTABLE/LANCTL/lanctl", build)
        self.assertIn("$PORTABLE/LANCTL/lanwire", build)
        self.assertIn("$PKG/opt/lanctl/lanwire", build)
        self.assertIn("$PKG/usr/bin/lanwire", build)
        self.assertIn("$PKG/usr/bin/lanmon", build)
        self.assertNotIn("$PKG/usr/bin/landemo", build)
        self.assertIn("LANCTL_DATA_DIR=/var/lib/lanctl", unit)
        self.assertIn("LANCTL_SECRET_DIR=/etc/lanctl/access", unit)
        self.assertIn(
            "-m 0770 /etc/lanctl/access",
            (root / "packaging/debian/postinst").read_text(encoding="utf-8"),
        )

    def test_frozen_standard_and_portable_data_roots(self):
        import lanctl.core.paths as paths

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
        self.assertIn('LEGACY_GUI_EXCLUDES = ["webview"]', spec)
        self.assertIn("excludes=LEGACY_GUI_EXCLUDES", spec)
        self.assertNotIn('("gui", "gui")', spec)
        self.assertIn('["packaging/entrypoints/lanctl_entry.py"]', spec)
        self.assertNotIn('["main.py"]', spec)
        self.assertIn("a.datas", spec)
        self.assertIn('icon="assets/lanctl-v3.ico"', spec)
        self.assertIn('["packaging/entrypoints/lanip_entry.py"]', spec)
        self.assertIn('["packaging/entrypoints/lanwire_entry.py"]', spec)
        self.assertIn('["packaging/entrypoints/lanmon_entry.py"]', spec)
        self.assertNotIn('["packaging/entrypoints/landemo_entry.py"]', spec)
        self.assertIn('["packaging/entrypoints/lanrack_entry.py"]', spec)
        self.assertIn('["packaging/entrypoints/lanaccess_entry.py"]', spec)
        self.assertIn('collect_submodules("lanctl.apps.wire")', spec)
        self.assertIn('("assets/lanctl-icon-v3.png", "assets")', spec)
        self.assertNotIn("lanctl-v2.ico", spec)
        self.assertIn("SetupIconFile=..\\..\\assets\\lanctl-v3.ico", inno)
        self.assertIn("dist\\LANCTL.exe", build)
        self.assertNotIn("dist\\LANCTL-GUI.exe", build)
        self.assertIn("dist\\lanip.exe", build)
        self.assertIn("dist\\lanwire.exe", build)
        self.assertIn("dist\\lanmon.exe", build)
        self.assertNotIn("dist\\landemo.exe", build)
        self.assertIn("dist\\lanrack.exe", build)
        self.assertIn("dist\\lanaccess.exe", build)
        self.assertNotIn("LANWIRE_ROOT", build)
        self.assertNotIn("packaging\\windows\\lanwire.exe", build)
        self.assertTrue((root / "lanwire.py").is_file())
        self.assertTrue((root / "lanip.py").is_file())
        self.assertTrue((root / "lanmon.py").is_file())
        self.assertFalse((root / "landemo.py").exists())
        self.assertTrue((root / "lanrack.py").is_file())
        self.assertTrue((root / "lanaccess.py").is_file())
        self.assertNotIn("_internal", build)
        self.assertIn('Source: "{#BuildRoot}\\LANCTL.exe"', inno)
        self.assertNotIn("recursesubdirs", inno)
        self.assertNotIn('Source: "{#BuildRoot}\\LANCTL-GUI.exe"', inno)
        self.assertIn('Source: "{#BuildRoot}\\lanip.exe"', inno)
        self.assertIn('Source: "{#BuildRoot}\\lanwire.exe"', inno)
        self.assertIn('Source: "{#BuildRoot}\\lanmon.exe"', inno)
        self.assertNotIn('Source: "{#BuildRoot}\\landemo.exe"', inno)
        self.assertIn('Source: "{#BuildRoot}\\lanrack.exe"', inno)
        self.assertIn('Source: "{#BuildRoot}\\lanaccess.exe"', inno)
        self.assertIn('Filename: "{app}\\lanwire.exe"', inno)
        self.assertNotIn('Filename: "{app}\\LANCTL-GUI.exe"', inno)
        self.assertIn('Filename: "{app}\\LANCTL.exe"; Parameters: "--tui"', inno)
        self.assertIn('Filename: "{app}\\LANCTL.exe"; Parameters: "--cli"', inno)
        self.assertNotIn("recurrent-elements.json", spec)
        self.assertIn("{commonappdata}\\LANCTL\\database", inno)
        self.assertIn("{commonappdata}\\LANCTL\\physical", inno)
        self.assertIn("admins-full system-full", inno)

    def test_windows_installers_require_all_tools_in_standard_and_portable_layouts(self):
        root = Path(__file__).resolve().parents[1]
        installer = (root / "install.ps1").read_text(encoding="utf-8")
        portable = (root / "packaging/portable/README-portable.txt").read_text(encoding="utf-8")
        self.assertGreaterEqual(installer.count("lanip.exe"), 2)
        self.assertGreaterEqual(installer.count("lanwire.exe"), 2)
        self.assertGreaterEqual(installer.count("lanmon.exe"), 2)
        self.assertNotIn("landemo.exe", installer)
        self.assertGreaterEqual(installer.count("lanrack.exe"), 2)
        self.assertGreaterEqual(installer.count("lanaccess.exe"), 2)
        self.assertIn("lanaccess.exe or lanmon.exe", portable)
        self.assertIn("physical/idf.db", portable)

    def test_github_actions_enforce_quality_and_security_gates(self):
        root = Path(__file__).resolve().parents[1]
        release = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
        ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        security = (root / ".github/workflows/security.yml").read_text(encoding="utf-8")
        for expected in ("--fail-under=60", "ruff check", "bandit", "pip_audit", "shellcheck"):
            self.assertIn(expected, release)
        for expected in ("pull_request", "--source=src", "pip_audit", "git diff --check"):
            self.assertIn(expected, ci)
        self.assertIn("--ignore-vuln PYSEC-2026-3552", ci)
        self.assertIn("--ignore-vuln PYSEC-2026-2858", ci)
        app_source = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (root / "src").rglob("*.py")
        )
        self.assertNotIn("pkcs7_decrypt_", app_source)
        self.assertIn("github/codeql-action/analyze", security)
        self.assertIn("dependency-review-action", security)
        self.assertIn("generate_cli_reference.py --check", ci)
        self.assertIn("generate_cli_reference.py --check", release)
        # Dependabot es opcional: el repositorio puede desactivarlo para evitar
        # ramas automáticas sin rebajar las puertas de CI y seguridad anteriores.

    def test_release_hash_generation_and_verification_are_separate(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary)
            artifact = release / "LANCTL-0.3.0-windows-x64-portable.zip"
            artifact.write_bytes(b"release")
            subprocess.run(
                [sys.executable, str(root / "scripts/generate-hashes.py"), str(release)],
                check=True,
                capture_output=True,
                text=True,
            )
            verified = subprocess.run(
                [sys.executable, str(root / "scripts/verify-release.py"), str(release)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("verified 1", verified.stdout)
            artifact.write_bytes(b"tampered")
            failed = subprocess.run(
                [sys.executable, str(root / "scripts/verify-release.py"), str(release)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("checksum mismatch", failed.stderr)

        build = (root / "scripts/build-windows.ps1").read_text(encoding="utf-8")
        self.assertIn("Release builds require a clean Git working tree", build)
        self.assertIn("git rev-parse HEAD", build)
        self.assertIn("scripts/generate-hashes.py", build)
        self.assertIn("scripts/verify-release.py", build)
        self.assertIn("Sign-And-Verify", build)
        self.assertIn("Get-AuthenticodeSignature", build)

    def test_windows_version_metadata_contains_exact_git_revision(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "version.txt"
            revision = "a" * 40
            subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts/generate-windows-version-info.py"),
                    "0.3.0-beta.20",
                    revision,
                    str(output),
                ],
                check=True,
            )
            metadata = output.read_text(encoding="utf-8")
            self.assertIn("ProductVersion', u'0.3.0-beta.20", metadata)
            self.assertIn(f"PrivateBuild', u'{revision}", metadata)

        spec = (root / "LANCTL.spec").read_text(encoding="utf-8")
        build = (root / "scripts/build-windows.ps1").read_text(encoding="utf-8")
        self.assertIn("LANCTL_VERSION_INFO", spec)
        self.assertIn("generate-windows-version-info.py", build)

    def test_builds_reject_a_version_different_from_the_application(self):
        from lanctl import __version__

        root = Path(__file__).resolve().parents[1]
        verifier = root / "scripts/verify-version.py"
        accepted = subprocess.run(
            [sys.executable, str(verifier), __version__], capture_output=True, text=True
        )
        rejected = subprocess.run(
            [sys.executable, str(verifier), "9.9.9"], capture_output=True, text=True
        )
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("version mismatch", rejected.stderr)
        self.assertIn(
            "scripts/verify-version.py $Version",
            (root / "scripts/build-windows.ps1").read_text(encoding="utf-8"),
        )
        self.assertIn(
            'scripts/verify-version.py "$VERSION"',
            (root / "scripts/build-linux.sh").read_text(encoding="utf-8"),
        )

    def test_machine_plugin_directory_is_not_user_writable(self):
        root = Path(__file__).resolve().parents[1]
        inno = (root / "packaging/inno/LANCTL.iss").read_text(encoding="utf-8")
        plugin_directory = next(line for line in inno.splitlines() if 'LANCTL\\plugins"' in line)
        self.assertIn("admins-full system-full", plugin_directory)
        self.assertNotIn("users-modify", plugin_directory)

    def test_official_windows_release_requires_authenticode_secrets(self):
        root = Path(__file__).resolve().parents[1]
        release = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("WINDOWS_SIGNING_CERTIFICATE_BASE64", release)
        self.assertIn("WINDOWS_SIGNING_CERTIFICATE_PASSWORD", release)
        self.assertIn("-RequireSignature", release)
        self.assertIn("Clean Windows install, update, demo and uninstall", release)
        self.assertIn("User data was not preserved", release)
        self.assertNotIn('landemo.exe" --output', release)
        self.assertIn('lanip.exe" demo --output', release)


if __name__ == "__main__":
    unittest.main()
