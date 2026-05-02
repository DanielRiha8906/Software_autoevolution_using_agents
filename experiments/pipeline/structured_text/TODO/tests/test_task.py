import pytest
from datetime import datetime, timezone, timedelta
from src.models.task import Task
from src.models.task_status import TaskStatus


def test_task_defaults():
    task = Task(title="Buy milk")
    assert task.title == "Buy milk"
    assert task.status == TaskStatus.PENDING
    assert task.description is None
    assert task.id is not None


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


def test_task_status_serialisation():
    for status in TaskStatus:
        task = Task(title="x", status=status)
        restored = Task.from_dict(task.to_dict())
        assert restored.status == status


def test_task_due_date_defaults_to_none():
    """Test that due_date field defaults to None."""
    task = Task(title="Task without due date")
    assert task.due_date is None


def test_task_with_due_date():
    """Test that due_date can be set when creating a Task."""
    due_date = datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone(timedelta(hours=2)))
    task = Task(title="Task with due date", due_date=due_date)
    assert task.due_date == due_date


def test_task_due_date_serialization():
    """Test that due_date is correctly serialized to ISO 8601 format."""
    due_date = datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone(timedelta(hours=2)))
    task = Task(title="Task with due date", due_date=due_date)
    task_dict = task.to_dict()
    assert "due_date" in task_dict
    assert task_dict["due_date"] == "2026-05-15T14:30:00+02:00"


def test_task_due_date_roundtrip():
    """Test that due_date survives serialization and deserialization."""
    due_date = datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone(timedelta(hours=2)))
    task = Task(title="Task with due date", due_date=due_date)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due_date
    assert restored.due_date.isoformat() == "2026-05-15T14:30:00+02:00"


def test_task_backward_compatibility_missing_due_date():
    """Test that old Task JSON without due_date field can be loaded (backward compatibility)."""
    old_task_dict = {
        "id": "test-id-123",
        "title": "Old task",
        "description": "A task created before due_date feature",
        "status": "pending",
        "created_at": "2026-01-01T10:00:00+00:00",
        "updated_at": "2026-01-01T10:00:00+00:00",
    }
    task = Task.from_dict(old_task_dict)
    assert task.title == "Old task"
    assert task.due_date is None


def test_task_is_overdue_returns_false_when_no_due_date():
    """Test that is_overdue() returns False when due_date is None."""
    task = Task(title="Task without due date")
    assert task.is_overdue() is False


def test_task_is_overdue_returns_false_when_future():
    """Test that is_overdue() returns False when due_date is in the future."""
    future_date = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone(timedelta(hours=2)))
    task = Task(title="Future task", due_date=future_date)
    assert task.is_overdue() is False


def test_task_is_overdue_returns_true_when_past():
    """Test that is_overdue() returns True when due_date is in the past."""
    past_date = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    task = Task(title="Overdue task", due_date=past_date)
    assert task.is_overdue() is True


# Status Transition Tests
def test_mark_in_progress_from_pending():
    """Test mark_in_progress transitions from PENDING to IN_PROGRESS."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS


def test_mark_in_progress_from_done():
    """Test mark_in_progress transitions from DONE to IN_PROGRESS."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS


def test_mark_in_progress_idempotent():
    """Test mark_in_progress is idempotent when already IN_PROGRESS."""
    task = Task(title="Test task", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == old_updated_at


def test_mark_done_from_pending():
    """Test mark_done transitions from PENDING to DONE."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    task.mark_done()
    assert task.status == TaskStatus.DONE


def test_mark_done_from_in_progress():
    """Test mark_done transitions from IN_PROGRESS to DONE."""
    task = Task(title="Test task", status=TaskStatus.IN_PROGRESS)
    task.mark_done()
    assert task.status == TaskStatus.DONE


def test_mark_done_idempotent():
    """Test mark_done is idempotent when already DONE."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at == old_updated_at


def test_reopen_from_in_progress():
    """Test reopen transitions from IN_PROGRESS to PENDING."""
    task = Task(title="Test task", status=TaskStatus.IN_PROGRESS)
    task.reopen()
    assert task.status == TaskStatus.PENDING


def test_reopen_from_done():
    """Test reopen transitions from DONE to PENDING."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    task.reopen()
    assert task.status == TaskStatus.PENDING


def test_reopen_idempotent():
    """Test reopen is idempotent when already PENDING."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at == old_updated_at


# Predicate Tests
def test_is_completed_returns_true_when_done():
    """Test is_completed returns True when status is DONE."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_returns_false_when_pending():
    """Test is_completed returns False when status is PENDING."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    assert task.is_completed() is False


def test_is_completed_returns_false_when_in_progress():
    """Test is_completed returns False when status is IN_PROGRESS."""
    task = Task(title="Test task", status=TaskStatus.IN_PROGRESS)
    assert task.is_completed() is False


# Timestamp Update Tests
def test_mark_in_progress_updates_timestamp():
    """Test mark_in_progress updates the timestamp to a later time."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.updated_at > old_updated_at


def test_mark_done_updates_timestamp():
    """Test mark_done updates the timestamp to a later time."""
    task = Task(title="Test task", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.updated_at > old_updated_at


def test_reopen_updates_timestamp():
    """Test reopen updates the timestamp to a later time."""
    task = Task(title="Test task", status=TaskStatus.DONE)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.updated_at > old_updated_at


def test_mark_in_progress_uses_cest_timezone():
    """Test mark_in_progress sets updated_at with CEST timezone offset."""
    task = Task(title="Test task", status=TaskStatus.PENDING)
    task.mark_in_progress()
    cest = timezone(timedelta(hours=2))
    assert task.updated_at.tzinfo == cest
