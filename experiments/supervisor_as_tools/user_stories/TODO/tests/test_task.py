import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
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


def test_task_with_due_date():
    cest = ZoneInfo("Europe/Paris")
    due_dt = datetime(2025, 12, 31, 23, 59, tzinfo=cest)
    task = Task(title="Buy milk", due_date=due_dt)
    assert task.due_date == due_dt


def test_task_due_date_roundtrip():
    cest = ZoneInfo("Europe/Paris")
    due_dt = datetime(2025, 12, 31, 23, 59, tzinfo=cest)
    task = Task(title="Buy milk", due_date=due_dt)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due_dt


def test_task_due_date_none():
    task = Task(title="Buy milk", due_date=None)
    assert task.due_date is None
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date is None


def test_task_backward_compatibility_missing_due_date():
    """Test that tasks without due_date field (legacy) deserialize correctly."""
    data = {
        "id": "123",
        "title": "Test",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
    }
    task = Task.from_dict(data)
    assert task.due_date is None


# Tests for status transition action methods


def test_mark_in_progress():
    """Test that mark_in_progress() transitions status to IN_PROGRESS."""
    task = Task(title="Test")
    assert task.status == TaskStatus.PENDING
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS


def test_mark_in_progress_updates_timestamp():
    """Test that mark_in_progress() updates updated_at to CEST timezone."""
    cest = ZoneInfo("Europe/Paris")
    task = Task(title="Test")
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.updated_at != old_updated_at
    assert task.updated_at.tzinfo == cest


def test_mark_done():
    """Test that mark_done() transitions status to DONE."""
    task = Task(title="Test")
    task.status = TaskStatus.IN_PROGRESS
    task.mark_done()
    assert task.status == TaskStatus.DONE


def test_mark_done_updates_timestamp():
    """Test that mark_done() updates updated_at to CEST timezone."""
    cest = ZoneInfo("Europe/Paris")
    task = Task(title="Test")
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.updated_at != old_updated_at
    assert task.updated_at.tzinfo == cest


def test_reopen():
    """Test that reopen() transitions status back to PENDING."""
    task = Task(title="Test")
    task.status = TaskStatus.DONE
    task.reopen()
    assert task.status == TaskStatus.PENDING


def test_reopen_updates_timestamp():
    """Test that reopen() updates updated_at to CEST timezone."""
    cest = ZoneInfo("Europe/Paris")
    task = Task(title="Test")
    task.status = TaskStatus.DONE
    old_updated_at = task.updated_at
    task.reopen()
    assert task.updated_at != old_updated_at
    assert task.updated_at.tzinfo == cest


# Tests for query/predicate methods


def test_is_completed_true():
    """Test that is_completed() returns True when status is DONE."""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_false():
    """Test that is_completed() returns False when status is not DONE."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_completed() is False
    task.status = TaskStatus.IN_PROGRESS
    assert task.is_completed() is False


def test_is_pending_true():
    """Test that is_pending() returns True when status is PENDING."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True


def test_is_pending_false():
    """Test that is_pending() returns False when status is not PENDING."""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_pending() is False
    task.status = TaskStatus.IN_PROGRESS
    assert task.is_pending() is False


def test_is_in_progress_true():
    """Test that is_in_progress() returns True when status is IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


def test_is_in_progress_false():
    """Test that is_in_progress() returns False when status is not IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_in_progress() is False
    task.status = TaskStatus.DONE
    assert task.is_in_progress() is False


def test_is_overdue_with_past_due_date():
    """Test that is_overdue() returns True when due_date is in the past."""
    cest = ZoneInfo("Europe/Paris")
    past_date = datetime(2020, 1, 1, tzinfo=cest)
    task = Task(title="Test", due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_with_future_due_date():
    """Test that is_overdue() returns False when due_date is in the future."""
    cest = ZoneInfo("Europe/Paris")
    future_date = datetime(2050, 12, 31, tzinfo=cest)
    task = Task(title="Test", due_date=future_date)
    assert task.is_overdue() is False


def test_is_overdue_with_none_due_date():
    """Test that is_overdue() returns False when due_date is None."""
    task = Task(title="Test", due_date=None)
    assert task.is_overdue() is False


def test_query_methods_dont_modify_state():
    """Test that query methods don't modify task state."""
    cest = ZoneInfo("Europe/Paris")
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS, due_date=datetime(2020, 1, 1, tzinfo=cest))
    original_status = task.status
    original_updated_at = task.updated_at

    # Call all query methods
    _ = task.is_completed()
    _ = task.is_pending()
    _ = task.is_in_progress()
    _ = task.is_overdue()

    # Verify state hasn't changed
    assert task.status == original_status
    assert task.updated_at == original_updated_at
