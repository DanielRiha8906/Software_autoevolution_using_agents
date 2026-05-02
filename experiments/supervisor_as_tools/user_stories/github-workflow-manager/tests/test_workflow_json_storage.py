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


def _sample_run(duration_seconds: float = 0.0) -> WorkflowRun:
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
        duration_seconds=duration_seconds,
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
    run = _sample_run(duration_seconds=456.78)
    tmp_storage.save([run])
    loaded = tmp_storage.load()
    assert len(loaded) == 1
    assert loaded[0].duration_seconds == 456.78


def test_duration_seconds_missing_defaults_to_zero(tmp_storage):
    # Simulate loading old JSON without duration_seconds
    run_data = {
        "id": "r1",
        "workflow_name": "Deploy",
        "branch": "main",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": None,
        "run_number": 42,
        "commit_sha": "deadbeef",
    }
    Path(tmp_storage.filepath).write_text(json.dumps([run_data]))
    loaded = tmp_storage.load()
    assert len(loaded) == 1
    assert loaded[0].duration_seconds == 0.0


def test_duration_seconds_persisted_in_json(tmp_storage):
    run = _sample_run(duration_seconds=789.01)
    tmp_storage.save([run])
    raw = json.loads(Path(tmp_storage.filepath).read_text())
    assert raw[0]["duration_seconds"] == 789.01
