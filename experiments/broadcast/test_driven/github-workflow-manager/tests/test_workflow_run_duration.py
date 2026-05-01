import pytest
from datetime import datetime, timezone
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _run(**kwargs):
    defaults = dict(
        id="run-1", workflow_name="CI", branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None, run_number=1, commit_sha=None,
    )
    defaults.update(kwargs)
    return WorkflowRun(**defaults)


def test_workflow_run_has_duration_seconds():
    assert hasattr(_run(), "duration_seconds")


def test_duration_seconds_defaults_to_zero():
    assert _run().duration_seconds == 0.0


def test_duration_seconds_can_be_set():
    assert _run(duration_seconds=42.5).duration_seconds == 42.5


def test_negative_duration_raises():
    with pytest.raises(Exception):
        _run(duration_seconds=-1.0)


def test_duration_seconds_in_to_dict():
    d = _run(duration_seconds=10.0).to_dict()
    assert "duration_seconds" in d
    assert d["duration_seconds"] == 10.0


def test_duration_seconds_round_trips_via_dict():
    run = _run(duration_seconds=10.0)
    assert WorkflowRun.from_dict(run.to_dict()).duration_seconds == 10.0

def test_old_dict_without_duration_seconds_loads_with_default():
    run = _run()
    data = run.to_dict()
    data.pop("duration_seconds", None)

    restored = WorkflowRun.from_dict(data)

    assert restored.duration_seconds == 0.0

def test_existing_fields_unchanged():
    run = _run()
    assert run.workflow_name == "CI"
    assert run.branch == "main"
    assert run.status == WorkflowStatus.COMPLETED
