"""Registered owners serialize closing and block cooperating late writes."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.core.coordination import Coordinator
from lanctl.core.database import DeviceDatabase
from lanctl.core.projects.provisional import (
    cancel_provisional_close,
    claim_provisional_close,
    complete_provisional_close,
    join_provisional_workspace,
    prepare_provisional_close,
    prepare_provisional_workspace,
    provisional_operation,
    validate_provisional_close,
)


def test_intermediate_close_claim_blocks_join_and_writes_until_cancelled(tmp_path):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    first = coordinator.register("lanip", "gui", None)
    second = coordinator.register("lanwire", "gui", None)
    workspace = prepare_provisional_workspace(root=tmp_path / "provisional")
    for owner in (first, second):
        join_provisional_workspace(workspace, owner, coordinator=coordinator)
    with provisional_operation(workspace, first, coordinator=coordinator, base={}) as settings:
        DeviceDatabase(settings["database"]).add_manual_device(idf="PC-001")
    claim = claim_provisional_close(workspace, first, coordinator=coordinator)
    assert not claim["last"] and claim["dirty"]
    with pytest.raises(RuntimeError):
        claim_provisional_close(workspace, second, coordinator=coordinator)
    with pytest.raises(RuntimeError):
        join_provisional_workspace(workspace, second, coordinator=coordinator)
    with (
        pytest.raises(RuntimeError),
        provisional_operation(workspace, second, coordinator=coordinator, base={}),
    ):
        pytest.fail("write entered while close was pending")
    with pytest.raises(RuntimeError):
        cancel_provisional_close(workspace, first, "stale-token", coordinator=coordinator)
    cancel_provisional_close(workspace, first, claim["token"], coordinator=coordinator)
    with provisional_operation(workspace, second, coordinator=coordinator, base={}) as settings:
        assert len(DeviceDatabase(settings["database"]).load()) == 1


def test_concurrent_close_claims_have_one_owner_and_no_duplicate_decision(tmp_path):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    owners = [coordinator.register(name, "gui", None) for name in ("lanip", "lanwire")]
    workspace = prepare_provisional_workspace(root=tmp_path / "provisional")
    for owner in owners:
        join_provisional_workspace(workspace, owner, coordinator=coordinator)

    def claim(owner):
        try:
            return claim_provisional_close(workspace, owner, coordinator=coordinator)
        except RuntimeError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim, owners))
    assert sum(item is not None for item in claims) == 1


def test_unknown_owner_cannot_join_or_claim_and_dead_peer_is_not_last_owner(tmp_path):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    owner = coordinator.register("lanip", "gui", None)
    peer = coordinator.register("lanwire", "gui", None)
    workspace = prepare_provisional_workspace(root=tmp_path / "provisional")
    with pytest.raises(ValueError):
        join_provisional_workspace(workspace, "foreign-owner", coordinator=coordinator)
    for identifier in (owner, peer):
        join_provisional_workspace(workspace, identifier, coordinator=coordinator)
    coordinator.close(peer)
    claim = claim_provisional_close(workspace, owner, coordinator=coordinator)
    assert claim["last"] and not claim["dirty"]


@pytest.mark.parametrize("decision", ["save", "discard"])
def test_only_last_owner_decides_and_source_survives_native_close(workspace, tmp_path, decision):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    first, second = [coordinator.register(name, "gui", None) for name in ("lanip", "lanwire")]
    provisional = prepare_provisional_workspace(root=tmp_path / "provisional")
    for owner in (first, second):
        join_provisional_workspace(provisional, owner, coordinator=coordinator)
    with provisional_operation(
        provisional, first, coordinator=coordinator, base=workspace
    ) as settings:
        DeviceDatabase(settings["database"]).add_manual_device(idf="PC-001")
    claim = claim_provisional_close(provisional, first, coordinator=coordinator)
    assert prepare_provisional_close(provisional, first, claim["token"], coordinator=coordinator)[
        "ready"
    ]
    assert not complete_provisional_close(
        provisional, first, claim["token"], coordinator=coordinator
    )["last"]
    claim = claim_provisional_close(provisional, second, coordinator=coordinator)
    pending = prepare_provisional_close(
        provisional, second, claim["token"], coordinator=coordinator
    )
    assert pending["needsDecision"] and not pending["ready"]
    with pytest.raises(RuntimeError):
        complete_provisional_close(provisional, second, claim["token"], coordinator=coordinator)
    result = prepare_provisional_close(
        provisional,
        second,
        claim["token"],
        coordinator=coordinator,
        decision=decision,
        destination=tmp_path / "Saved.vlf",
        name="Saved",
        base=workspace,
    )
    assert result["ready"] and result["last"]
    assert complete_provisional_close(provisional, second, claim["token"], coordinator=coordinator)[
        "closed"
    ]
    assert len(DeviceDatabase(settings["database"]).load()) == 1
    with pytest.raises(RuntimeError):
        join_provisional_workspace(provisional, second, coordinator=coordinator)


def test_failed_save_can_cancel_close_and_continue_working(workspace, tmp_path):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    owner = coordinator.register("lanip", "gui", None)
    provisional = prepare_provisional_workspace(root=tmp_path / "provisional")
    join_provisional_workspace(provisional, owner, coordinator=coordinator)
    with provisional_operation(
        provisional, owner, coordinator=coordinator, base=workspace
    ) as settings:
        DeviceDatabase(settings["database"]).add_manual_device(idf="PC-001")
    claim = claim_provisional_close(provisional, owner, coordinator=coordinator)
    destination = tmp_path / "Existing.vlf"
    destination.write_bytes(b"untouched")
    with pytest.raises(ValueError):
        prepare_provisional_close(
            provisional,
            owner,
            claim["token"],
            coordinator=coordinator,
            decision="save",
            destination=destination,
            name="Existing",
            base=workspace,
        )
    cancel_provisional_close(provisional, owner, claim["token"], coordinator=coordinator)
    with provisional_operation(
        provisional, owner, coordinator=coordinator, base=workspace
    ) as settings:
        assert len(DeviceDatabase(settings["database"]).load()) == 1
    assert destination.read_bytes() == b"untouched"


@pytest.mark.parametrize(
    "change", [{"schemaVersion": 999}, {"principal": "foreign-user"}, {"owners": "invalid"}]
)
def test_invalid_owner_metadata_is_rejected_without_rewriting(tmp_path, change):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    owner = coordinator.register("lanip", "gui", None)
    provisional = prepare_provisional_workspace(root=tmp_path / "provisional")
    metadata = provisional.root / "workspace.json"
    document = json.loads(metadata.read_text())
    document.update(change)
    metadata.write_text(json.dumps(document))
    before = metadata.read_bytes()
    with pytest.raises(ValueError):
        join_provisional_workspace(provisional, owner, coordinator=coordinator)
    assert metadata.read_bytes() == before


@pytest.mark.parametrize("next_decision", ["ask", "save"])
def test_changed_close_decision_cannot_reuse_previous_discard(workspace, tmp_path, next_decision):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    owner = coordinator.register("lanip", "gui", None)
    draft = prepare_provisional_workspace(root=tmp_path / "provisional")
    join_provisional_workspace(draft, owner, coordinator=coordinator)
    with provisional_operation(draft, owner, coordinator=coordinator, base=workspace) as settings:
        DeviceDatabase(settings["database"]).add_manual_device(idf="PC-001")
    claim = claim_provisional_close(draft, owner, coordinator=coordinator)
    assert prepare_provisional_close(
        draft, owner, claim["token"], coordinator=coordinator, decision="discard"
    )["ready"]
    if next_decision == "save":
        destination = tmp_path / "Existing.vlf"
        destination.write_bytes(b"preserve")
        with pytest.raises(ValueError):
            prepare_provisional_close(
                draft,
                owner,
                claim["token"],
                coordinator=coordinator,
                decision="save",
                destination=destination,
                name="Existing",
                base=workspace,
            )
        assert destination.read_bytes() == b"preserve"
    else:
        assert prepare_provisional_close(draft, owner, claim["token"], coordinator=coordinator)[
            "needsDecision"
        ]
    with pytest.raises(RuntimeError):
        complete_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    cancel_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    with provisional_operation(draft, owner, coordinator=coordinator, base=workspace) as settings:
        assert DeviceDatabase(settings["database"]).load()[0].idf == "PC-001"


@pytest.mark.parametrize("damage", ["missing", "replaced"])
def test_saved_project_must_survive_until_close_confirmation(workspace, tmp_path, damage):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    owner = coordinator.register("lanip", "gui", None)
    draft = prepare_provisional_workspace(root=tmp_path / "provisional")
    join_provisional_workspace(draft, owner, coordinator=coordinator)
    with provisional_operation(draft, owner, coordinator=coordinator, base=workspace) as settings:
        DeviceDatabase(settings["database"]).add_manual_device(idf="PC-001")
    claim = claim_provisional_close(draft, owner, coordinator=coordinator)
    destination = tmp_path / "Saved.vlf"
    result = prepare_provisional_close(
        draft,
        owner,
        claim["token"],
        coordinator=coordinator,
        decision="save",
        destination=destination,
        name="Saved",
        base=workspace,
    )
    assert result["ready"]
    assert validate_provisional_close(draft, owner, claim["token"], coordinator=coordinator)[
        "ready"
    ]
    if damage == "missing":
        destination.unlink()
    else:
        destination.write_bytes(b"replaced archive")
    with pytest.raises((RuntimeError, OSError)):
        validate_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    with pytest.raises((RuntimeError, OSError)):
        complete_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    cancel_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    with provisional_operation(draft, owner, coordinator=coordinator, base=workspace) as settings:
        assert DeviceDatabase(settings["database"]).load()[0].idf == "PC-001"


def test_preflight_retains_owner_and_requires_native_confirmation(tmp_path):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    owner = coordinator.register("lanip", "gui", None)
    draft = prepare_provisional_workspace(root=tmp_path / "provisional")
    join_provisional_workspace(draft, owner, coordinator=coordinator)
    claim = claim_provisional_close(draft, owner, coordinator=coordinator)
    with pytest.raises(RuntimeError):
        validate_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    prepare_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    metadata = draft.root / "workspace.json"
    before = json.loads(metadata.read_text())
    for _ in range(2):
        assert validate_provisional_close(
            draft, owner, claim["token"], coordinator=coordinator
        ) == {"ready": True, "last": True}
        assert json.loads(metadata.read_text()) == before
    # Native destruction may still fail: cancellation must remain possible.
    cancel_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    with provisional_operation(draft, owner, coordinator=coordinator, base={}):
        pass
    claim = claim_provisional_close(draft, owner, coordinator=coordinator)
    prepare_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    validate_provisional_close(draft, owner, claim["token"], coordinator=coordinator)
    assert complete_provisional_close(draft, owner, claim["token"], coordinator=coordinator)[
        "closed"
    ]
