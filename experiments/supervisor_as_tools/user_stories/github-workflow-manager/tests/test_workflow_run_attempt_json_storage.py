import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.attempt_run_status import RunAttemptStatus
from src.models.attempt_run_conclusion import RunAttemptConclusion
from src.storage.workflow_run_attempt_json_storage import WorkflowRunAttemptJsonStorage


@pytest.fixture
def tmp_storage(tmp_path):
    return WorkflowRunAttemptJsonStorage(str(tmp_path / "attempts.json"))


def _sample_attempt(
    id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    duration_seconds: float = None,
) -> WorkflowRunAttempt:
    return WorkflowRunAttempt(
        id=id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=RunAttemptStatus.COMPLETED,
        conclusion=RunAttemptConclusion.SUCCESS,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=duration_seconds,
    )


def test_load_empty(tmp_storage):
    assert tmp_storage.load() == []


def test_save_and_load_roundtrip(tmp_storage):
    attempt = _sample_attempt()
    tmp_storage.save([attempt])
    loaded = tmp_storage.load()
    assert len(loaded) == 1
    assert loaded[0].id == attempt.id
    assert loaded[0].run_id == attempt.run_id
    assert loaded[0].attempt_number == attempt.attempt_number
    assert loaded[0].status == attempt.status
    assert loaded[0].conclusion == attempt.conclusion


def test_save_persists_json_format(tmp_storage):
    attempt = _sample_attempt(id=1, run_id=5)
    tmp_storage.save([attempt])
    raw = json.loads(Path(tmp_storage.filepath).read_text())
    assert raw[0]["id"] == 1
    assert raw[0]["run_id"] == 5
    assert raw[0]["conclusion"] == "success"


def test_duration_seconds_optional_null(tmp_storage):
    attempt = _sample_attempt(duration_seconds=None)
    tmp_storage.save([attempt])
    loaded = tmp_storage.load()
    assert len(loaded) == 1
    assert loaded[0].duration_seconds is None


def test_multiple_roundtrip(tmp_storage):
    a1 = _sample_attempt(id=1, run_id=1, attempt_number=1, duration_seconds=10.5)
    a2 = _sample_attempt(id=2, run_id=1, attempt_number=2, duration_seconds=20.3)
    a3 = _sample_attempt(id=3, run_id=2, attempt_number=1)
    tmp_storage.save([a1, a2, a3])
    loaded = tmp_storage.load()
    assert len(loaded) == 3
    assert loaded[0].id == 1
    assert loaded[0].duration_seconds == 10.5
    assert loaded[1].id == 2
    assert loaded[1].duration_seconds == 20.3
    assert loaded[2].id == 3
    assert loaded[2].duration_seconds is None
