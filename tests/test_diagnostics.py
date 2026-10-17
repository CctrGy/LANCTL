import json
from urllib.parse import parse_qs, urlparse

import pytest

from lanctl.apps.monitor.bug_reports import bug_report_url
from lanctl.core.diagnostics import diagnostic_markdown, export_diagnostic, prepare_diagnostic


@pytest.mark.parametrize("anonymize", [True, False])
def test_credentials_removed_even_without_identity_anonymization(anonymize):
    # Synthetic framing assembled at runtime; no PEM key is stored in the repository.
    key_label = "PRIVATE KEY"
    report = prepare_diagnostic(
        anonymize=anonymize,
        description='password="secret words" Bearer super-token https://admin:private@example.test/x',
        logs=[
            '{"api_key":"secret-key"}',
            f"-----BEGIN {key_label}-----\nPRIVATECONTENT\n-----END {key_label}-----",
        ],
        errors=[
            {
                "origin": "LANCTL.Test.Demo",
                "code": "FAILED",
                "details": {"token": "nestedsecret", "password": "nestedpass"},
            }
        ],
    )
    text = json.dumps(report)
    for secret in (
        "secret words",
        "super-token",
        "admin:private",
        "secret-key",
        "PRIVATECONTENT",
        "nestedsecret",
        "nestedpass",
    ):
        assert secret not in text


def test_anonymization_and_explicit_evidence_limits():
    report = prepare_diagnostic(
        description=r"C:\Users\Victor\project.vlf /home/victor/a.vlf 192.168.1.7 aa:bb:cc:dd:ee:ff user@example.test 2001:db8::1",
        logs=["line"] * 1000,
        context={
            "project": "private-name",
            "session": "session-id",
            "vault": {"password": "secret"},
        },
    )
    assert len(report["logs"]) == 200
    assert report["context"] == {"project": "[PRIVATE]", "session": "session-id"}
    assert all(
        x not in report["description"]
        for x in ("Victor", "victor", "192.168.1.7", "aa:bb", "user@", "2001:db8")
    )


def test_errors_grouped_without_combining_distinct_origins():
    a = {"origin": "LANCTL.Test.One", "code": "FAILED", "message": "x"}
    b = {**a, "origin": "LANCTL.Test.Two"}
    result = prepare_diagnostic(errors=[a, a, b])
    assert [r["count"] for r in result["errors"]] == [2, 1]


def test_export_rescrubs_edited_preview_and_url_is_bounded(tmp_path):
    report = prepare_diagnostic(description="á" * 4096)
    report["logs"] = ["password=after-preview-secret"]
    report["description"] += " token=edited-secret"
    path = tmp_path / "report.md"
    assert export_diagnostic(report, path) == str(path.resolve())
    assert "after-preview-secret" not in path.read_text(encoding="utf-8")
    url = bug_report_url(report)
    assert len(url) <= 6000
    assert urlparse(url).netloc == "github.com"
    assert urlparse(url).path == "/CctrGy/LANCTL/issues/new"
    body = parse_qs(urlparse(url).query)["body"][0]
    assert "edited-secret" not in body
    assert "after-preview-secret" not in body


def test_draft_does_not_read_inventory_or_require_project():
    report = prepare_diagnostic(description="manual report")
    assert report["context"] == {}
    assert report["logs"] == []
    assert "manual report" in diagnostic_markdown(report)
