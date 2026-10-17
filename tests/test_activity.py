import pytest

from lanctl.core.activity import ActivityStore
from lanctl.core.coordination import Coordinator


def test_two_independent_stores_filter_sessions_projects_and_keep_closed_history(tmp_path):
    c = Coordinator()
    a = c.register("lanctl", "gui", "a.vlf")
    b = c.register("lanip", "gui", "b.vlf")
    path = tmp_path / "activity.db"
    one, two = ActivityStore(path), ActivityStore(path)
    first = one.append("uno", launcher="lanctl", session=a, project="a.vlf")
    second = two.append("dos", launcher="lanip", session=b, project="b.vlf")
    assert two.query(session=a) == [first]
    assert one.query(project="b.vlf") == [second]
    assert one.query(after=first["seq"]) == [second]
    c.close(a)
    assert two.query(session=a) == [first]
    with pytest.raises(ValueError, match="vigentes"):
        one.append("closed", launcher="lanctl", session=a, project="a.vlf")
    two.owner = "another-user"
    assert two.query() == []


def test_mismatched_context_and_oversize_refused(tmp_path):
    c = Coordinator()
    sid = c.register("lanctl", "gui", "a.vlf")
    store = ActivityStore(tmp_path / "activity.db")
    with pytest.raises(ValueError):
        store.append("x", launcher="lanip", session=sid, project="a.vlf")
    with pytest.raises(ValueError):
        store.append("x", launcher="lanctl", session=sid, project="b.vlf")
    with pytest.raises(ValueError):
        store.append("x" * 4097, launcher="lanctl", session=sid, project="a.vlf")
    assert store.query() == []


def test_retention_and_controls(tmp_path, monkeypatch):
    monkeypatch.setattr("lanctl.core.activity.RETENTION", 2)
    sid = Coordinator().register("lanctl", "gui")
    store = ActivityStore(tmp_path / "activity.db")
    for text in ("old", "a\nb\x07", "last"):
        store.append(text, launcher="lanctl", session=sid)
    assert [r["message"] for r in store.query()] == ["a b", "last"]


def test_read_does_not_create_storage(tmp_path):
    path = tmp_path / "not-created" / "activity.db"
    assert ActivityStore(path).query() == []
    assert not path.parent.exists()


def test_recent_and_projectless_filters(tmp_path):
    c = Coordinator()
    sid = c.register("lanctl", "gui")
    other = c.register("lanip", "gui", "project.vlf")
    store = ActivityStore(tmp_path / "activity.db")
    for i in range(5):
        store.append(str(i), launcher="lanctl", session=sid)
    store.append("other", launcher="lanip", session=other, project="project.vlf")
    assert [r["message"] for r in store.query(limit=2, latest=True, project="")] == ["3", "4"]
    assert store.query(limit=1, latest=True)[0]["message"] == "other"


def test_activity_written_by_independent_process_survives_session_close(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    path = tmp_path / "activity.db"
    coordinator = Coordinator()
    script = """
import sys
from pathlib import Path
from lanctl.core import coordination
from lanctl.core.activity import ActivityStore
coordination.coordinator_path=lambda:Path(sys.argv[1])
c=coordination.Coordinator()
sid=c.register('lanctl','gui','project.vlf')
ActivityStore(sys.argv[2]).append('from child',launcher='lanctl',session=sid,project='project.vlf')
c.close(sid)
"""
    env = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        "LANCTL_DATA_DIR": str(tmp_path),
    }
    subprocess.run(
        [sys.executable, "-c", script, str(coordinator.path), str(path)],
        env=env,
        check=True,
        capture_output=True,
        timeout=15,
    )
    rows = ActivityStore(path).query(project="project.vlf")
    assert len(rows) == 1 and rows[0]["message"] == "from child"
