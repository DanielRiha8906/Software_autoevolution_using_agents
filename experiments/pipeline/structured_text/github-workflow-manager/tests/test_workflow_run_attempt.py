"""
Tests for WorkflowRunAttempt dataclass.

Covers:
- to_dict / from_dict serialization
- Roundtrip serialization
- State query methods (is_terminal, is_running, is_successful, is_failed, is_cancelled)
- Validation (negative duration_seconds, invalid attempt_number)
"""

import pytest
from datetime import datetime, timezone

from src.models.workflow_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion


def _make_attempt(
    attempt_id: str = "attempt-1",
    run_id: str = "run-1",
    attempt_number: int = 1,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    started_at: datetime = None,
    completed_at: datetime = None,
    duration_seconds: float = 0.0,
    logs_url: str = None,
) -> WorkflowRunAttempt:
    """Helper to create a WorkflowRunAttempt with defaults."""
    if started_at is None:
        started_at = datetime.now(timezone.utc)
    if completed_at is None:
        completed_at = datetime.now(timezone.utc)
    return WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
        logs_url=logs_url,
    )


# ============================================================================
# Serialization Tests (to_dict / from_dict)
# ============================================================================

def test_to_dict_basic():
    """Test basic to_dict serialization."""
    now = datetime.now(timezone.utc)
    attempt = WorkflowRunAttempt(
        id="attempt-1",
        run_id="run-1",
        attempt_number=1,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        started_at=now,
        completed_at=now,
        duration_seconds=10.5,
        logs_url="https://example.com/logs",
    )
    data = attempt.to_dict()

    assert data["id"] == "attempt-1"
    assert data["run_id"] == "run-1"
    assert data["attempt_number"] == 1
    assert data["status"] == "completed"
    assert data["conclusion"] == "success"
    assert data["duration_seconds"] == 10.5
    assert data["logs_url"] == "https://example.com/logs"
    assert isinstance(data["started_at"], str)
    assert isinstance(data["completed_at"], str)


def test_to_dict_with_none_values():
    """Test to_dict with None values."""
    now = datetime.now(timezone.utc)
    attempt = WorkflowRunAttempt(
        id="attempt-1",
        run_id="run-1",
        attempt_number=1,
        status=WorkflowStatus.IN_PROGRESS,
        conclusion=None,
        started_at=now,
        completed_at=None,
        duration_seconds=0.0,
        logs_url=None,
    )
    data = attempt.to_dict()

    assert data["conclusion"] is None
    assert data["completed_at"] is None
    assert data["logs_url"] is None


def test_from_dict_basic():
    """Test basic from_dict deserialization."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    data = {
        "id": "attempt-1",
        "run_id": "run-1",
        "attempt_number": 1,
        "status": "completed",
        "conclusion": "success",
        "started_at": now_iso,
        "completed_at": now_iso,
        "duration_seconds": 10.5,
        "logs_url": "https://example.com/logs",
    }

    attempt = WorkflowRunAttempt.from_dict(data)

    assert attempt.id == "attempt-1"
    assert attempt.run_id == "run-1"
    assert attempt.attempt_number == 1
    assert attempt.status == WorkflowStatus.COMPLETED
    assert attempt.conclusion == WorkflowConclusion.SUCCESS
    assert attempt.duration_seconds == 10.5
    assert attempt.logs_url == "https://example.com/logs"


def test_from_dict_with_none_values():
    """Test from_dict with None values."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    data = {
        "id": "attempt-1",
        "run_id": "run-1",
        "attempt_number": 1,
        "status": "in_progress",
        "conclusion": None,
        "started_at": now_iso,
        "completed_at": None,
        "duration_seconds": 0.0,
        "logs_url": None,
    }

    attempt = WorkflowRunAttempt.from_dict(data)

    assert attempt.conclusion is None
    assert attempt.completed_at is None
    assert attempt.logs_url is None


def test_from_dict_missing_duration_defaults_to_zero():
    """Test from_dict defaults duration_seconds to 0.0 if missing."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    data = {
        "id": "attempt-1",
        "run_id": "run-1",
        "attempt_number": 1,
        "status": "completed",
        "conclusion": "success",
        "started_at": now_iso,
        "completed_at": now_iso,
    }

    attempt = WorkflowRunAttempt.from_dict(data)
    assert attempt.duration_seconds == 0.0


def test_roundtrip_serialization():
    """Test that to_dict -> from_dict roundtrip preserves data."""
    now = datetime.now(timezone.utc)
    original = WorkflowRunAttempt(
        id="attempt-1",
        run_id="run-1",
        attempt_number=1,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        started_at=now,
        completed_at=now,
        duration_seconds=10.5,
        logs_url="https://example.com/logs",
    )

    data = original.to_dict()
    restored = WorkflowRunAttempt.from_dict(data)

    assert restored.id == original.id
    assert restored.run_id == original.run_id
    assert restored.attempt_number == original.attempt_number
    assert restored.status == original.status
    assert restored.conclusion == original.conclusion
    assert restored.duration_seconds == original.duration_seconds
    assert restored.logs_url == original.logs_url


def test_roundtrip_with_none_values():
    """Test roundtrip with None values."""
    now = datetime.now(timezone.utc)
    original = WorkflowRunAttempt(
        id="attempt-1",
        run_id="run-1",
        attempt_number=1,
        status=WorkflowStatus.IN_PROGRESS,
        conclusion=None,
        started_at=now,
        completed_at=None,
        duration_seconds=0.0,
        logs_url=None,
    )

    data = original.to_dict()
    restored = WorkflowRunAttempt.from_dict(data)

    assert restored.conclusion is None
    assert restored.completed_at is None
    assert restored.logs_url is None


# ============================================================================
# State Query Methods Tests
# ============================================================================

def test_is_terminal_completed():
    """Test is_terminal returns True for COMPLETED status."""
    attempt = _make_attempt(status=WorkflowStatus.COMPLETED)
    assert attempt.is_terminal() is True


def test_is_terminal_non_completed(
):
    """Test is_terminal returns False for non-COMPLETED statuses."""
    for status in [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                   WorkflowStatus.WAITING, WorkflowStatus.REQUESTED,
                   WorkflowStatus.PENDING]:
        attempt = _make_attempt(status=status, conclusion=None)
        assert attempt.is_terminal() is False, f"Expected is_terminal=False for {status}"


def test_is_running_non_completed():
    """Test is_running returns True for non-COMPLETED statuses."""
    for status in [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                   WorkflowStatus.WAITING, WorkflowStatus.REQUESTED,
                   WorkflowStatus.PENDING]:
        attempt = _make_attempt(status=status, conclusion=None)
        assert attempt.is_running() is True, f"Expected is_running=True for {status}"


def test_is_running_completed():
    """Test is_running returns False for COMPLETED status."""
    attempt = _make_attempt(status=WorkflowStatus.COMPLETED)
    assert attempt.is_running() is False


def test_is_successful_with_success():
    """Test is_successful returns True for COMPLETED + SUCCESS."""
    attempt = _make_attempt(
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
    )
    assert attempt.is_successful() is True


def test_is_successful_with_other_conclusions():
    """Test is_successful returns False for COMPLETED + non-SUCCESS conclusions."""
    conclusions = [
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ]
    for conclusion in conclusions:
        attempt = _make_attempt(
            status=WorkflowStatus.COMPLETED,
            conclusion=conclusion,
        )
        assert attempt.is_successful() is False, f"Expected is_successful=False for {conclusion}"


def test_is_successful_non_completed():
    """Test is_successful returns False for non-COMPLETED statuses."""
    for status in [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                   WorkflowStatus.WAITING, WorkflowStatus.REQUESTED,
                   WorkflowStatus.PENDING]:
        attempt = _make_attempt(status=status, conclusion=None)
        assert attempt.is_successful() is False, f"Expected is_successful=False for {status}"


def test_is_failed_with_failure():
    """Test is_failed returns True for COMPLETED + FAILURE."""
    attempt = _make_attempt(
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.FAILURE,
    )
    assert attempt.is_failed() is True


def test_is_failed_with_timed_out():
    """Test is_failed returns True for COMPLETED + TIMED_OUT."""
    attempt = _make_attempt(
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.TIMED_OUT,
    )
    assert attempt.is_failed() is True


def test_is_failed_with_action_required():
    """Test is_failed returns True for COMPLETED + ACTION_REQUIRED."""
    attempt = _make_attempt(
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.ACTION_REQUIRED,
    )
    assert attempt.is_failed() is True


def test_is_failed_with_other_conclusions():
    """Test is_failed returns False for COMPLETED + non-failure conclusions."""
    conclusions = [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.CANCELLED,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ]
    for conclusion in conclusions:
        attempt = _make_attempt(
            status=WorkflowStatus.COMPLETED,
            conclusion=conclusion,
        )
        assert attempt.is_failed() is False, f"Expected is_failed=False for {conclusion}"


def test_is_failed_non_completed():
    """Test is_failed returns False for non-COMPLETED statuses."""
    for status in [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                   WorkflowStatus.WAITING, WorkflowStatus.REQUESTED,
                   WorkflowStatus.PENDING]:
        attempt = _make_attempt(status=status, conclusion=None)
        assert attempt.is_failed() is False, f"Expected is_failed=False for {status}"


def test_is_cancelled_with_cancelled():
    """Test is_cancelled returns True for COMPLETED + CANCELLED."""
    attempt = _make_attempt(
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.CANCELLED,
    )
    assert attempt.is_cancelled() is True


def test_is_cancelled_with_other_conclusions():
    """Test is_cancelled returns False for COMPLETED + non-CANCELLED conclusions."""
    conclusions = [
        WorkflowConclusion.SUCCESS,
        WorkflowConclusion.FAILURE,
        WorkflowConclusion.SKIPPED,
        WorkflowConclusion.TIMED_OUT,
        WorkflowConclusion.ACTION_REQUIRED,
        WorkflowConclusion.NEUTRAL,
        WorkflowConclusion.STALE,
    ]
    for conclusion in conclusions:
        attempt = _make_attempt(
            status=WorkflowStatus.COMPLETED,
            conclusion=conclusion,
        )
        assert attempt.is_cancelled() is False, f"Expected is_cancelled=False for {conclusion}"


def test_is_cancelled_non_completed():
    """Test is_cancelled returns False for non-COMPLETED statuses."""
    for status in [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                   WorkflowStatus.WAITING, WorkflowStatus.REQUESTED,
                   WorkflowStatus.PENDING]:
        attempt = _make_attempt(status=status, conclusion=None)
        assert attempt.is_cancelled() is False, f"Expected is_cancelled=False for {status}"


# ============================================================================
# Validation Tests
# ============================================================================

def test_from_dict_negative_duration_raises():
    """Test from_dict raises ValueError for negative duration_seconds."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    data = {
        "id": "attempt-1",
        "run_id": "run-1",
        "attempt_number": 1,
        "status": "completed",
        "conclusion": "success",
        "started_at": now_iso,
        "completed_at": now_iso,
        "duration_seconds": -5.0,
    }

    with pytest.raises(ValueError) as exc_info:
        WorkflowRunAttempt.from_dict(data)
    assert "non-negative" in str(exc_info.value).lower()


def test_from_dict_all_status_values():
    """Test from_dict works with all WorkflowStatus values."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    for status in WorkflowStatus:
        data = {
            "id": f"attempt-{status.value}",
            "run_id": "run-1",
            "attempt_number": 1,
            "status": status.value,
            "conclusion": "success" if status == WorkflowStatus.COMPLETED else None,
            "started_at": now_iso,
            "completed_at": now_iso if status == WorkflowStatus.COMPLETED else None,
            "duration_seconds": 0.0,
        }

        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.status == status


def test_from_dict_all_conclusion_values():
    """Test from_dict works with all WorkflowConclusion values."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    for conclusion in WorkflowConclusion:
        data = {
            "id": f"attempt-{conclusion.value}",
            "run_id": "run-1",
            "attempt_number": 1,
            "status": "completed",
            "conclusion": conclusion.value,
            "started_at": now_iso,
            "completed_at": now_iso,
            "duration_seconds": 0.0,
        }

        attempt = WorkflowRunAttempt.from_dict(data)
        assert attempt.conclusion == conclusion


def test_zero_duration_is_valid():
    """Test that zero duration_seconds is valid."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    data = {
        "id": "attempt-1",
        "run_id": "run-1",
        "attempt_number": 1,
        "status": "completed",
        "conclusion": "success",
        "started_at": now_iso,
        "completed_at": now_iso,
        "duration_seconds": 0.0,
    }

    attempt = WorkflowRunAttempt.from_dict(data)
    assert attempt.duration_seconds == 0.0


def test_large_duration_is_valid():
    """Test that large duration_seconds values are valid."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    data = {
        "id": "attempt-1",
        "run_id": "run-1",
        "attempt_number": 1,
        "status": "completed",
        "conclusion": "success",
        "started_at": now_iso,
        "completed_at": now_iso,
        "duration_seconds": 999999.99,
    }

    attempt = WorkflowRunAttempt.from_dict(data)
    assert attempt.duration_seconds == 999999.99


# ============================================================================
# State Exclusivity Tests
# ============================================================================

def test_terminal_and_running_mutually_exclusive():
    """Test that is_terminal and is_running are mutually exclusive."""
    # Test all running states
    for status in [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                   WorkflowStatus.WAITING, WorkflowStatus.REQUESTED,
                   WorkflowStatus.PENDING]:
        attempt = _make_attempt(status=status, conclusion=None)
        assert attempt.is_terminal() is not attempt.is_running()

    # Test all terminal states
    for conclusion in WorkflowConclusion:
        attempt = _make_attempt(status=WorkflowStatus.COMPLETED, conclusion=conclusion)
        assert attempt.is_terminal() is not attempt.is_running()


def test_successful_and_failed_mutually_exclusive():
    """Test that is_successful and is_failed can never both be True."""
    # Test all possible combinations
    statuses = [WorkflowStatus.QUEUED, WorkflowStatus.IN_PROGRESS,
                WorkflowStatus.COMPLETED, WorkflowStatus.WAITING,
                WorkflowStatus.REQUESTED, WorkflowStatus.PENDING]
    conclusions = [None] + list(WorkflowConclusion)

    for status in statuses:
        for conclusion in conclusions:
            # Skip invalid combinations
            if status != WorkflowStatus.COMPLETED and conclusion is not None:
                continue
            if status == WorkflowStatus.COMPLETED and conclusion is None:
                continue

            attempt = _make_attempt(status=status, conclusion=conclusion)
            assert not (attempt.is_successful() and attempt.is_failed()), \
                f"is_successful and is_failed both True for {status} + {conclusion}"
