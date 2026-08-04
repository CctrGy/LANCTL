import unittest
from pathlib import Path
from unittest import mock

from app.distribution.release import artifact_name,classify_channel,normalize_architecture,validate_version


class DistributionTests(unittest.TestCase):
    def test_versions_and_channels_are_closed(self):
        self.assertEqual(validate_version("v0.3.0-beta.2"),"0.3.0-beta.2")
        self.assertEqual(classify_channel("0.3.0-beta.2"),"beta")
        self.assertEqual(classify_channel("1.0.0"),"stable")
        for value in ("latest","../../bad","1.0","1.0.0-evil.1"):
            with self.assertRaises(ValueError):validate_version(value)

    def test_architecture_and_artifact_selection(self):
        self.assertEqual(normalize_architecture("aarch64"),"arm64")
        self.assertEqual(artifact_name("0.3.0-beta.2","Windows","amd64"),"LANCTL-0.3.0-beta.2-windows-x64-setup.exe")
        self.assertEqual(artifact_name("0.3.0-beta.2","Linux","arm64"),"lanctl_0.3.0-beta.2_arm64.deb")
        self.assertEqual(artifact_name("0.3.0-beta.2","Linux","amd64",True),"LANCTL-0.3.0-beta.2-linux-amd64.tar.gz")
        with self.assertRaises(ValueError):artifact_name("1.0.0","Windows","arm64")

    def test_installers_verify_hashes_and_do_not_evaluate_downloaded_content(self):
        root=Path(__file__).resolve().parents[1]
        powershell=(root/"install.ps1").read_text(encoding="utf-8")
        shell=(root/"install.sh").read_text(encoding="utf-8")
        self.assertIn("Assert-Hash",powershell);self.assertIn("Expand-SafeZip",powershell)
        self.assertNotIn("Invoke-Expression",powershell)
        self.assertIn("sha256sum --check --strict",shell);self.assertIn("Unsafe tar entry",shell)
        self.assertNotIn("eval ",shell);self.assertNotIn("source ",shell)

    def test_updates_preserve_data_and_access_is_never_silent(self):
        root=Path(__file__).resolve().parents[1]
        powershell=(root/"install.ps1").read_text(encoding="utf-8")
        shell=(root/"install.sh").read_text(encoding="utf-8")
        self.assertIn("preserve projects/configuration",powershell)
        self.assertNotIn("ProgramData\\LANCTL",powershell)
        self.assertIn("setup-wizard requires an interactive terminal",shell)
        self.assertNotIn("enable ssh",shell);self.assertNotIn("enable https",shell)

    def test_frozen_standard_and_portable_data_roots(self):
        import app.core.paths as paths
        with mock.patch.object(paths.sys,"frozen",True,create=True),mock.patch.object(paths.sys,"executable",r"C:\Program Files\LANCTL\LANCTL.exe"),mock.patch.object(paths.platform,"system",return_value="Windows"),mock.patch.dict(paths.os.environ,{"PROGRAMDATA":r"C:\ProgramData"},clear=False),mock.patch.object(Path,"exists",return_value=False):
            self.assertIn("ProgramData",str(paths.application_path("data/lc/access/config.json")))


if __name__=="__main__":unittest.main()
