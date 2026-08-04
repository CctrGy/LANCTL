import contextlib,io,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.cli import configure_utf8_stdio, main


class CliFastPathTests(unittest.TestCase):
    def test_standard_text_output_is_configured_as_utf8(self):
        stdout = Mock()
        stderr = Mock()
        with patch("app.cli.sys.stdout", stdout), patch("app.cli.sys.stderr", stderr):
            configure_utf8_stdio()
        stdout.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
        stderr.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")

    def test_version_and_help_do_not_create_data(self):
        for arguments in (["--version"],["--help"],["access","--help"]):
            with self.subTest(arguments=arguments),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary)/"data"
                with patch.dict("os.environ",{"LANCTL_DATA_DIR":str(root)},clear=False),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as result:main(arguments)
                self.assertEqual(result.exception.code,0);self.assertFalse(root.exists())


if __name__=="__main__":unittest.main()
