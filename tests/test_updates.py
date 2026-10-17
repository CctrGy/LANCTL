from unittest.mock import Mock

import pytest

from lanctl.core.updates import DAY, UpdateService, version_key


def release(tag, **values):
    return {
        "tag_name": tag,
        "published_at": "2026-10-17T00:00:00Z",
        "draft": False,
        "prerelease": False,
        "body": "notes",
        **values,
    }


@pytest.fixture(autouse=True)
def quiet_errors(monkeypatch):
    monkeypatch.setattr("lanctl.core.errors.errors.from_exception", Mock())
    monkeypatch.setattr("lanctl.core.updates.__version__", "0.3.3")


def test_highest_semantic_published_stable_not_first_or_latest_date(tmp_path):
    fetch = Mock(
        return_value=[
            release("v0.3.4"),
            release("v0.9.0"),
            release("v0.10.0-beta.2"),
            release("v1.0.0", prerelease=True),
            release("v2.0.0", draft=True),
            release("v3.0.0", published_at=None),
            release("evil"),
            release("v0.3.2"),
        ]
    )
    result = UpdateService(tmp_path / "cache.json", fetcher=fetch).check()
    assert result["available"] == "0.10.0-beta.2"
    assert result["url"] == "https://github.com/CctrGy/LANCTL/releases/tag/v0.10.0-beta.2"
    assert result["status"] == "available"


def test_daily_cache_failure_and_manual_retry(tmp_path):
    fetch = Mock(side_effect=OSError("offline"))
    now = [100000.0]
    service = UpdateService(tmp_path / "cache.json", fetcher=fetch, clock=lambda: now[0])
    assert service.check()["status"] == "unavailable"
    assert service.check()["cached"]
    assert fetch.call_count == 1
    fetch.side_effect = None
    fetch.return_value = []
    assert service.check(manual=True)["status"] == "current"
    now[0] += DAY
    assert service.check()["status"] == "current"
    assert fetch.call_count == 3


def test_reminder_persists_and_only_defers_same_version(tmp_path):
    now = [100000.0]
    fetch = Mock(return_value=[release("v0.4.0")])
    service = UpdateService(tmp_path / "cache.json", fetcher=fetch, clock=lambda: now[0])
    assert not service.check()["deferred"]
    service.remind_later("0.4.0")
    assert service.check()["deferred"]
    fetch.return_value = [release("v0.5.0")]
    assert not service.check(manual=True)["deferred"]


def test_corrupt_cache_not_rewritten(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text('{"schemaVersion":999}')
    fetch = Mock()
    assert UpdateService(path, fetcher=fetch).check()["status"] == "unavailable"
    fetch.assert_not_called()
    assert path.read_text() == '{"schemaVersion":999}'


def test_semver_prerelease_and_build_metadata():
    assert (
        version_key("1.0.0-beta.2")
        < version_key("1.0.0-beta.11")
        < version_key("1.0.0-rc.1")
        < version_key("1.0.0")
    )
    assert version_key("v1.0.0+build") == version_key("1.0.0")
    for invalid in (None, "1.01.0", "1.0.0-beta.01", "1.0", "1.0.0;cmd"):
        with pytest.raises(ValueError):
            version_key(invalid)


def test_parallel_launcher_uses_reserved_daily_check(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    started, release_fetch = Event(), Event()

    def fetch():
        started.set()
        assert release_fetch.wait(3)
        return [release("v0.4.0")]

    path = tmp_path / "cache.json"
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(UpdateService(path, fetcher=fetch).check)
        try:
            assert started.wait(3)
            other = Mock(side_effect=AssertionError("duplicate network call"))
            assert UpdateService(path, fetcher=other).check()["cached"]
            other.assert_not_called()
        finally:
            release_fetch.set()
        assert pending.result()["status"] == "available"


def test_modified_cache_cannot_supply_external_download_link(tmp_path):
    import json

    path = tmp_path / "cache.json"
    service = UpdateService(path, fetcher=lambda: [release("v0.4.0")])
    service.check()
    data = json.loads(path.read_text(encoding="utf-8"))
    data["result"]["url"] = "https://attacker.invalid/installer.exe"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert service.check()["status"] == "unavailable"
