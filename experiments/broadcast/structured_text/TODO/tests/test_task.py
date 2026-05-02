import pytest
from datetime import datetime, timezone, timedelta
from src.models.task import Task, CEST
from src.models.task_status import TaskStatus


def test_task_defaults():
    task = Task(title="Buy milk")
    assert task.title == "Buy milk"
    assert task.status == TaskStatus.PENDING
    assert task.description is None
    assert task.id is not None
    assert task.due_date is None


def test_task_unique_ids():
    a = Task(title="A")
    b = Task(title="B")
    assert a.id != b.id


def test_task_roundtrip():
    task = Task(title="Test", description="desc")
    restored = Task.from_dict(task.to_dict())
    assert restored.id == task.id
    assert restored.title == task.title
    assert restored.description == task.description
    assert restored.status == task.status
    assert restored.created_at == task.created_at
    assert restored.updated_at == task.updated_at
    assert restored.due_date == task.due_date


def test_task_status_serialisation():
    for status in TaskStatus:
        task = Task(title="x", status=status)
        restored = Task.from_dict(task.to_dict())
        assert restored.status == status


def test_task_due_date_default_is_none():
    """Test that due_date defaults to None."""
    task = Task(title="Test task")
    assert task.due_date is None


def test_task_due_date_can_be_set():
    """Test that due_date can be set and stored."""
    due = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    task = Task(title="Test task", due_date=due)
    assert task.due_date == due


def test_task_due_date_to_dict():
    """Test that due_date is serialized to ISO 8601 format in to_dict()."""
    due = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    task = Task(title="Test task", due_date=due)
    d = task.to_dict()
    assert d["due_date"] == "2025-12-31T23:59:59+00:00"


def test_task_due_date_none_to_dict():
    """Test that due_date serializes to None in to_dict() when not set."""
    task = Task(title="Test task")
    d = task.to_dict()
    assert d["due_date"] is None


def test_task_due_date_from_dict():
    """Test that due_date is deserialized from ISO 8601 format."""
    data = {
        "id": "test-id",
        "title": "Test task",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
        "due_date": "2025-12-31T23:59:59+00:00",
    }
    task = Task.from_dict(data)
    assert task.due_date is not None
    assert task.due_date == datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


def test_task_due_date_from_dict_none():
    """Test that due_date is None when not provided in from_dict()."""
    data = {
        "id": "test-id",
        "title": "Test task",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
    }
    task = Task.from_dict(data)
    assert task.due_date is None


def test_task_due_date_from_dict_explicit_none():
    """Test that due_date is None when explicitly set to None in from_dict()."""
    data = {
        "id": "test-id",
        "title": "Test task",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
        "due_date": None,
    }
    task = Task.from_dict(data)
    assert task.due_date is None


def test_task_due_date_invalid_format_backward_compat():
    """Test that invalid due_date format is handled gracefully for backward compatibility."""
    data = {
        "id": "test-id",
        "title": "Test task",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
        "due_date": "invalid-date",
    }
    task = Task.from_dict(data)
    assert task.due_date is None


def test_task_due_date_roundtrip():
    """Test that due_date survives a to_dict() and from_dict() roundtrip."""
    due = datetime(2025, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
    task = Task(title="Test task", due_date=due)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due
    assert restored.due_date.isoformat() == due.isoformat()


def test_task_is_overdue_not_set():
    """Test that is_overdue() returns False when due_date is not set."""
    task = Task(title="Test task")
    assert task.is_overdue() is False


def test_task_is_overdue_future_date():
    """Test that is_overdue() returns False for future due_date."""
    future = datetime.now(CEST) + timedelta(days=1)
    task = Task(title="Test task", due_date=future)
    assert task.is_overdue() is False


def test_task_is_overdue_past_date():
    """Test that is_overdue() returns True for past due_date."""
    past = datetime.now(CEST) - timedelta(days=1)
    task = Task(title="Test task", due_date=past)
    assert task.is_overdue() is True


def test_task_is_overdue_utc_to_cest_conversion():
    """Test that is_overdue() correctly handles UTC timezone conversion."""
    # Create a datetime in UTC that is in the past
    past_utc = datetime.now(timezone.utc) - timedelta(hours=3)
    task = Task(title="Test task", due_date=past_utc)
    assert task.is_overdue() is True


def test_task_is_overdue_cest_timezone():
    """Test that is_overdue() correctly handles CEST timezone."""
    past_cest = datetime.now(CEST) - timedelta(hours=1)
    task = Task(title="Test task", due_date=past_cest)
    assert task.is_overdue() is True


def test_mark_in_progress():
    """Test that mark_in_progress() transitions status to IN_PROGRESS."""
    task = Task(title="Test task")
    assert task.status == TaskStatus.PENDING
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS


def test_mark_done():
    """Test that mark_done() transitions status to DONE."""
    task = Task(title="Test task")
    assert task.status == TaskStatus.PENDING
    task.mark_done()
    assert task.status == TaskStatus.DONE


def test_reopen():
    """Test that reopen() transitions status to PENDING."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    assert task.status == TaskStatus.DONE
    task.reopen()
    assert task.status == TaskStatus.PENDING


def test_is_completed_when_done():
    """Test that is_completed() returns True when status is DONE."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_when_pending():
    """Test that is_completed() returns False when status is PENDING."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    assert task.is_completed() is False


def test_is_completed_when_in_progress():
    """Test that is_completed() returns False when status is IN_PROGRESS."""
    task = Task(title="Test task", status=TaskStatus.IN_PROGRESS)
    assert task.is_completed() is False


def test_is_pending_when_pending():
    """Test that is_pending() returns True when status is PENDING."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    assert task.is_pending() is True


def test_is_pending_when_in_progress():
    """Test that is_pending() returns False when status is IN_PROGRESS."""
    task = Task(title="Test task", status=TaskStatus.IN_PROGRESS)
    assert task.is_pending() is False


def test_is_pending_when_done():
    """Test that is_pending() returns False when status is DONE."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    assert task.is_pending() is False


def test_is_in_progress_when_in_progress():
    """Test that is_in_progress() returns True when status is IN_PROGRESS."""
    task = Task(title="Test task", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


def test_is_in_progress_when_pending():
    """Test that is_in_progress() returns False when status is PENDING."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    assert task.is_in_progress() is False


def test_is_in_progress_when_done():
    """Test that is_in_progress() returns False when status is DONE."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    assert task.is_in_progress() is False


def test_mark_in_progress_updates_updated_at():
    """Test that mark_in_progress() updates updated_at to current CEST time."""
    task = Task(title="Test task")
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.updated_at > original_updated_at


def test_mark_done_updates_updated_at():
    """Test that mark_done() updates updated_at to current CEST time."""
    task = Task(title="Test task")
    original_updated_at = task.updated_at
    task.mark_done()
    assert task.updated_at > original_updated_at


def test_reopen_updates_updated_at():
    """Test that reopen() updates updated_at to current CEST time."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    original_updated_at = task.updated_at
    task.reopen()
    assert task.updated_at > original_updated_at


def test_status_transition_pending_to_in_progress_to_done():
    """Test a complete status transition flow: PENDING -> IN_PROGRESS -> DONE."""
    task = Task(title="Test task")
    assert task.status == TaskStatus.PENDING
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    task.mark_done()
    assert task.status == TaskStatus.DONE


def test_status_transition_done_back_to_pending():
    """Test reopening a completed task."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    assert task.is_completed() is True
    task.reopen()
    assert task.is_completed() is False
    assert task.is_pending() is True
