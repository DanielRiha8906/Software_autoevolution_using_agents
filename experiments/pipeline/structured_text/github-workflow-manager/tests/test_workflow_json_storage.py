import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.storage.workflow_json_storage import WorkflowJsonStorage


@pytest.fixture
def tmp_storage(tmp_path):
    return WorkflowJsonStorage(str(tmp_path / "runs.json"))


def _sample_run() -> WorkflowRun:
    return WorkflowRun(
        id="r1",
        workflow_name="Deploy",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=42,
        commit_sha="deadbeef",
    )


def test_load_empty(tmp_storage):
    assert tmp_storage.load() == []


def test_save_and_load_roundtrip(tmp_storage):
    run = _sample_run()
    tmp_storage.save([run])
    loaded = tmp_storage.load()
    assert len(loaded) == 1
    assert loaded[0].id == run.id
    assert loaded[0].workflow_name == run.workflow_name
    assert loaded[0].status == run.status
    assert loaded[0].conclusion == run.conclusion
    assert loaded[0].run_number == run.run_number
    assert loaded[0].commit_sha == run.commit_sha


def test_save_persists_json(tmp_storage):
    run = _sample_run()
    tmp_storage.save([run])
    raw = json.loads(Path(tmp_storage.filepath).read_text())
    assert raw[0]["id"] == "r1"
    assert raw[0]["conclusion"] == "success"


def test_duration_seconds_roundtrip(tmp_storage):
    """Verify duration_seconds is saved and loaded correctly."""
    run = WorkflowRun(
        id="r_duration",
        workflow_name="Deploy",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=42,
        commit_sha="deadbeef",
        duration_seconds=123.45,
    )
    tmp_storage.save([run])
    loaded = tmp_storage.load()
    assert len(loaded) == 1
    assert loaded[0].duration_seconds == 123.45


def test_duration_seconds_default(tmp_storage):
    """Verify missing duration_seconds in JSON defaults to 0.0."""
    # Manually create JSON without duration_seconds to simulate old data
    old_data = [
        {
            "id": "r_old",
            "workflow_name": "Deploy",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": None,
            "run_number": 42,
            "commit_sha": "deadbeef",
        }
    ]
    Path(tmp_storage.filepath).write_text(json.dumps(old_data))
    loaded = tmp_storage.load()
    assert len(loaded) == 1
    assert loaded[0].duration_seconds == 0.0


def test_duration_seconds_validation_negative():
    """Verify WorkflowRun.from_dict raises ValueError for negative duration_seconds."""
    data = {
        "id": "r_neg",
        "workflow_name": "Deploy",
        "branch": "main",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": None,
        "run_number": 42,
        "commit_sha": "deadbeef",
        "duration_seconds": -5.0,
    }
    with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
        WorkflowRun.from_dict(data)
