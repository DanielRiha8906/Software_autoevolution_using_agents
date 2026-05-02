import pytest
from datetime import datetime, timezone, timedelta
from src.models.workflow_run_attempt import WorkflowRunAttempt


CEST = timezone(timedelta(hours=2))


def _attempt(**kwargs):
    defaults = dict(
        id=1,
        run_id=42,
        attempt_number=1,
        status="completed",
        conclusion="success",
        created_at=datetime.now(CEST),
    )
    defaults.update(kwargs)
    return WorkflowRunAttempt(**defaults)


def test_attempt_can_be_created():
    assert _attempt() is not None


def test_attempt_number_must_be_positive():
    with pytest.raises(Exception):
        _attempt(attempt_number=0)


def test_created_at_must_use_cest():
    with pytest.raises(Exception):
        _attempt(created_at=datetime.now(timezone.utc))


def test_created_at_round_trips_as_cest():
    attempt = _attempt(created_at=datetime(2026, 1, 1, 12, 0, tzinfo=CEST))
    restored = WorkflowRunAttempt.from_dict(attempt.to_dict())
    assert restored.created_at.tzinfo == CEST


def test_serializes_to_dict():
    d = _attempt().to_dict()
    assert d["run_id"] == 42
    assert d["attempt_number"] == 1
    assert "created_at" in d


def test_round_trips_via_dict():
    attempt = _attempt()
    restored = WorkflowRunAttempt.from_dict(attempt.to_dict())
    assert restored.id == attempt.id
    assert restored.run_id == attempt.run_id


def test_optional_duration_seconds():
    assert _attempt(duration_seconds=5.5).duration_seconds == 5.5


def test_duration_seconds_defaults_to_none_or_zero():
    attempt = _attempt()
    assert attempt.duration_seconds is None or attempt.duration_seconds == 0.0
