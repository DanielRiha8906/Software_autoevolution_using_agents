import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.models.workflow_run_attempt import WorkflowRunAttempt
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
        duration_seconds=45.5,
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


def test_save_and_load_duration_roundtrip(tmp_storage):
    run = _sample_run()
    tmp_storage.save([run])
    loaded = tmp_storage.load()
    assert loaded[0].duration_seconds == 45.5


def test_duration_in_json(tmp_storage):
    run = _sample_run()
    tmp_storage.save([run])
    raw = json.loads(Path(tmp_storage.filepath).read_text())
    assert raw[0]["duration_seconds"] == 45.5


def test_load_json_without_duration_defaults_to_zero(tmp_storage):
    # Simulate old JSON file without duration_seconds field
    old_format = [
        {
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
    ]
    Path(tmp_storage.filepath).parent.mkdir(parents=True, exist_ok=True)
    Path(tmp_storage.filepath).write_text(json.dumps(old_format))
    loaded = tmp_storage.load()
    assert loaded[0].duration_seconds == 0.0


def test_save_and_load_run_with_attempts(tmp_storage):
    """Integration test: save and load WorkflowRun with nested attempts."""
    attempt1 = WorkflowRunAttempt(
        id=1,
        run_id=1,
        attempt_number=1,
        status="completed",
        conclusion="failure",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        duration_seconds=30.0,
    )
    attempt2 = WorkflowRunAttempt(
        id=2,
        run_id=1,
        attempt_number=2,
        status="completed",
        conclusion="success",
        created_at=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
        duration_seconds=25.0,
    )
    run = WorkflowRun(
        id="r1",
        workflow_name="Deploy",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=42,
        commit_sha="deadbeef",
        duration_seconds=55.0,
        attempts=[attempt1, attempt2],
    )
    tmp_storage.save([run])
    loaded = tmp_storage.load()

    assert len(loaded) == 1
    assert len(loaded[0].attempts) == 2
    assert loaded[0].attempts[0].attempt_number == 1
    assert loaded[0].attempts[0].conclusion == "failure"
    assert loaded[0].attempts[1].attempt_number == 2
    assert loaded[0].attempts[1].conclusion == "success"


def test_attempts_in_json_structure(tmp_storage):
    """Integration test: verify attempts are serialized in JSON structure."""
    attempt = WorkflowRunAttempt(
        id=1,
        run_id=1,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=42.5,
    )
    run = WorkflowRun(
        id="r1",
        workflow_name="Deploy",
        branch="main",
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=None,
        run_number=42,
        commit_sha="deadbeef",
        duration_seconds=45.5,
        attempts=[attempt],
    )
    tmp_storage.save([run])
    raw = json.loads(Path(tmp_storage.filepath).read_text())

    assert "attempts" in raw[0]
    assert len(raw[0]["attempts"]) == 1
    assert raw[0]["attempts"][0]["attempt_number"] == 1
    assert raw[0]["attempts"][0]["conclusion"] == "success"
    assert raw[0]["attempts"][0]["duration_seconds"] == 42.5


def test_load_json_without_attempts_defaults_to_empty_list(tmp_storage):
    """Backward compatibility: old JSON without attempts key loads with empty list."""
    old_format = [
        {
            "id": "r1",
            "workflow_name": "Deploy",
            "branch": "main",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": None,
            "run_number": 42,
            "commit_sha": "deadbeef",
            "duration_seconds": 45.5,
        }
    ]
    Path(tmp_storage.filepath).parent.mkdir(parents=True, exist_ok=True)
    Path(tmp_storage.filepath).write_text(json.dumps(old_format))
    loaded = tmp_storage.load()

    assert loaded[0].attempts == []
