import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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
    assert restored.due_date is None


def test_task_status_serialisation():
    for status in TaskStatus:
        task = Task(title="x", status=status)
        restored = Task.from_dict(task.to_dict())
        assert restored.status == status


def test_task_with_due_date():
    """Test that a task can be created with a timezone-aware due date."""
    due_date = datetime(2026, 12, 25, 15, 30, 0, tzinfo=timezone.utc)
    task = Task(title="Christmas task", due_date=due_date)
    assert task.due_date == due_date


def test_task_with_cest_due_date():
    """Test that a task can be created with a CEST timezone-aware due date."""
    due_date = datetime(2026, 12, 25, 15, 30, 0, tzinfo=CEST)
    task = Task(title="Christmas task", due_date=due_date)
    assert task.due_date == due_date
    assert task.due_date.tzinfo == CEST


def test_task_due_date_serialization():
    """Test that due_date is serialized to ISO 8601 format."""
    due_date = datetime(2026, 12, 25, 15, 30, 0, tzinfo=timezone.utc)
    task = Task(title="Test", due_date=due_date)
    task_dict = task.to_dict()
    assert "due_date" in task_dict
    assert task_dict["due_date"] == due_date.isoformat()


def test_task_due_date_roundtrip():
    """Test that due_date survives serialization/deserialization."""
    due_date = datetime(2026, 12, 25, 15, 30, 0, tzinfo=timezone.utc)
    task = Task(title="Test", due_date=due_date)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due_date


def test_task_without_due_date_in_serialized():
    """Test that tasks without due_date don't include it in the dict."""
    task = Task(title="Test")
    task_dict = task.to_dict()
    assert "due_date" not in task_dict


def test_task_backward_compatibility_no_due_date():
    """Test that old tasks without due_date field load correctly."""
    old_task_dict = {
        "id": "test-id",
        "title": "Old task",
        "description": "A task created before due_date support",
        "status": "pending",
        "created_at": "2026-01-01T10:00:00+00:00",
        "updated_at": "2026-01-01T10:00:00+00:00",
    }
    task = Task.from_dict(old_task_dict)
    assert task.id == "test-id"
    assert task.title == "Old task"
    assert task.due_date is None


def test_task_validation_rejects_naive_datetime():
    """Test that providing a naive (timezone-unaware) datetime is rejected."""
    naive_date = datetime(2026, 12, 25, 15, 30, 0)
    with pytest.raises(ValueError, match="must be timezone-aware"):
        Task(title="Test", due_date=naive_date)


def test_task_validation_rejects_non_datetime():
    """Test that providing a non-datetime value is rejected."""
    with pytest.raises(ValueError, match="must be a datetime object"):
        Task(title="Test", due_date="2026-12-25")


def test_task_due_date_with_cest_serialization():
    """Test that CEST due dates are properly serialized and deserialized."""
    due_date = datetime(2026, 12, 25, 17, 0, 0, tzinfo=CEST)
    task = Task(title="CEST task", due_date=due_date)
    restored = Task.from_dict(task.to_dict())
    # The datetime values should be equal (same instant in time)
    assert restored.due_date == due_date
    # ISO serialization preserves the offset but not the timezone name
    assert restored.due_date.tzinfo is not None
    assert restored.due_date.utcoffset() == due_date.utcoffset()


# Status transition method tests

def test_mark_in_progress_from_pending():
    """Test marking a pending task as in progress."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > old_updated_at


def test_mark_in_progress_idempotent():
    """Test that marking in progress twice is a no-op the second time."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == old_updated_at


def test_mark_in_progress_from_done():
    """Test that marking a done task as in progress is a no-op."""
    task = Task(title="Test", status=TaskStatus.DONE)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.DONE
    assert task.updated_at == old_updated_at


def test_mark_done_from_pending():
    """Test marking a pending task as done."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at > old_updated_at


def test_mark_done_from_in_progress():
    """Test marking an in-progress task as done."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at > old_updated_at


def test_mark_done_idempotent():
    """Test that marking done twice is a no-op the second time."""
    task = Task(title="Test", status=TaskStatus.DONE)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at == old_updated_at


def test_reopen_from_done():
    """Test reopening a done task."""
    task = Task(title="Test", status=TaskStatus.DONE)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at > old_updated_at


def test_reopen_from_pending_is_noop():
    """Test that reopening a pending task is a no-op."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at == old_updated_at


def test_reopen_from_in_progress_is_noop():
    """Test that reopening an in-progress task is a no-op."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == old_updated_at


def test_is_pending():
    """Test is_pending predicate."""
    pending_task = Task(title="Test", status=TaskStatus.PENDING)
    in_progress_task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    done_task = Task(title="Test", status=TaskStatus.DONE)

    assert pending_task.is_pending() is True
    assert in_progress_task.is_pending() is False
    assert done_task.is_pending() is False


def test_is_in_progress():
    """Test is_in_progress predicate."""
    pending_task = Task(title="Test", status=TaskStatus.PENDING)
    in_progress_task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    done_task = Task(title="Test", status=TaskStatus.DONE)

    assert pending_task.is_in_progress() is False
    assert in_progress_task.is_in_progress() is True
    assert done_task.is_in_progress() is False


def test_is_completed():
    """Test is_completed predicate."""
    pending_task = Task(title="Test", status=TaskStatus.PENDING)
    in_progress_task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    done_task = Task(title="Test", status=TaskStatus.DONE)

    assert pending_task.is_completed() is False
    assert in_progress_task.is_completed() is False
    assert done_task.is_completed() is True


def test_is_overdue_no_due_date():
    """Test that a task without due_date is not overdue."""
    task = Task(title="Test")
    assert task.is_overdue() is False


def test_is_overdue_future_due_date():
    """Test that a task with future due_date is not overdue."""
    future_date = datetime(2030, 12, 25, 15, 0, 0, tzinfo=CEST)
    task = Task(title="Test", due_date=future_date)
    assert task.is_overdue() is False


def test_is_overdue_past_due_date():
    """Test that a task with past due_date is overdue."""
    past_date = datetime(2020, 1, 1, 10, 0, 0, tzinfo=CEST)
    task = Task(title="Test", due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_completed_task():
    """Test that a completed task is never overdue."""
    past_date = datetime(2020, 1, 1, 10, 0, 0, tzinfo=CEST)
    task = Task(title="Test", status=TaskStatus.DONE, due_date=past_date)
    assert task.is_overdue() is False


def test_updated_at_in_cest():
    """Test that updated_at is set in CEST timezone."""
    task = Task(title="Test")
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.updated_at.tzinfo == CEST


def test_status_transition_sequence():
    """Test a typical sequence of status transitions."""
    task = Task(title="Buy groceries")
    assert task.is_pending()

    task.mark_in_progress()
    assert task.is_in_progress()
    assert not task.is_pending()

    task.mark_done()
    assert task.is_completed()
    assert not task.is_in_progress()

    task.reopen()
    assert task.is_pending()
    assert not task.is_completed()
