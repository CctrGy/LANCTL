"""Keep the new process coordinator out of developer/user runtime data."""

import pytest


@pytest.fixture(autouse=True)
def isolated_coordinator(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "lanctl.core.coordination.coordinator_path", lambda: tmp_path / "runtime.db"
    )
