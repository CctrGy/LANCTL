from unittest.mock import patch

import pytest

from lanctl.bootstrap.lanctl import main
from lanctl.core.official_links import get_official_links, open_official_link


@pytest.mark.parametrize("key", ["web", "github", "reference"])
@pytest.mark.parametrize("prefix", ["-", "--"])
def test_cli_prints_and_opens_only_canonical_link(key, prefix, capsys):
    with patch("lanctl.core.official_links.webbrowser.open", return_value=True) as browser:
        assert main.__wrapped__([prefix + key]) == 0
    assert capsys.readouterr().out.strip() == get_official_links()[key]
    browser.assert_called_once_with(get_official_links()[key], new=2)


def test_links_copy_and_unsupported_browser():
    links = get_official_links()
    links["web"] = "https://attacker.invalid"
    with patch("lanctl.core.official_links.webbrowser.open", return_value=False) as browser:
        result = open_official_link("web")
    assert result == {"key": "web", "url": get_official_links()["web"], "opened": False}
    assert browser.call_args.args[0] != links["web"]


@pytest.mark.parametrize("key", ["file:///tmp/a", "https://attacker.invalid", [], None])
def test_arbitrary_destination_refused(key):
    with pytest.raises(ValueError, match="desconocido"):
        open_official_link(key)


@pytest.mark.parametrize("args", [["-web", "-github"], ["--gui", "-web"], ["-web", "lanip"]])
def test_incompatible_options_do_not_open_browser(args):
    with patch("lanctl.core.official_links.webbrowser.open") as browser, pytest.raises(SystemExit):
        main.__wrapped__(args)
    browser.assert_not_called()
