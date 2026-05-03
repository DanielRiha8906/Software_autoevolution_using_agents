import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.storage.attempt_json_storage import AttemptJsonStorage


@pytest.fixture
def tmp_storage(tmp_path):
    return AttemptJsonStorage(str(tmp_path / "attempts.json"))


def _sample_attempt() -> WorkflowRunAttempt:
    return WorkflowRunAttempt(
        id=1,
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=10.5,
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
    assert loaded[0].duration_seconds == attempt.duration_seconds


def test_save_persists_json(tmp_storage):
    attempt = _sample_attempt()
    tmp_storage.save([attempt])
    raw = json.loads(Path(tmp_storage.filepath).read_text())
    assert raw[0]["id"] == 1
    assert raw[0]["run_id"] == 42
    assert raw[0]["attempt_number"] == 1
    assert raw[0]["status"] == "completed"
    assert raw[0]["conclusion"] == "success"
    assert raw[0]["duration_seconds"] == 10.5
