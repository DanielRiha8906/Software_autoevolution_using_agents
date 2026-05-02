import pytest
from datetime import datetime, timezone, timedelta
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


def test_task_due_date_defaults_to_none():
    task = Task(title="Buy milk")
    assert task.due_date is None


def test_task_due_date_roundtrip():
    future = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", due_date=future)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == future


def test_task_backward_compatibility_without_due_date():
    """Test that tasks without due_date in dict still load correctly."""
    data = {
        "id": "test-id",
        "title": "Old task",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    task = Task.from_dict(data)
    assert task.due_date is None


def test_task_is_overdue_false_when_none():
    task = Task(title="No due date")
    assert task.is_overdue() is False


def test_task_is_overdue_false_when_future():
    future = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Future task", due_date=future)
    assert task.is_overdue() is False


def test_task_is_overdue_true_when_past():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    task = Task(title="Past task", due_date=past)
    assert task.is_overdue() is True


# Status transition tests: mark_in_progress()
def test_mark_in_progress_from_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > original_updated_at


def test_mark_in_progress_from_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > original_updated_at


def test_mark_in_progress_noop_when_already_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    original_status = task.status
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == original_status
    assert task.updated_at == original_updated_at


# Status transition tests: mark_done()
def test_mark_done_from_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at > original_updated_at


def test_mark_done_from_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    original_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at > original_updated_at


def test_mark_done_noop_when_already_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    original_status = task.status
    original_updated_at = task.updated_at
    task.mark_done()
    assert task.status == original_status
    assert task.updated_at == original_updated_at


# Status transition tests: reopen()
def test_reopen_from_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    original_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at > original_updated_at


def test_reopen_from_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    original_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at > original_updated_at


def test_reopen_noop_when_already_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_status = task.status
    original_updated_at = task.updated_at
    task.reopen()
    assert task.status == original_status
    assert task.updated_at == original_updated_at


# Predicate tests: is_completed()
def test_is_completed_true_when_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_false_when_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_completed() is False


def test_is_completed_false_when_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_completed() is False


# Predicate tests: is_pending()
def test_is_pending_true_when_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True


def test_is_pending_false_when_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_pending() is False


def test_is_pending_false_when_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_pending() is False


# Predicate tests: is_in_progress()
def test_is_in_progress_true_when_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


def test_is_in_progress_false_when_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_in_progress() is False


def test_is_in_progress_false_when_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_in_progress() is False
