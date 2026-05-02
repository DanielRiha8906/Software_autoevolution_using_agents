import pytest
from datetime import datetime, timedelta, timezone

from src.models.task import Task, CEST
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


# Status Transition Tests

def test_mark_in_progress_from_pending():
    """Task transitions PENDING -> IN_PROGRESS."""
    task = Task(title="Test")
    assert task.status == TaskStatus.PENDING
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS


def test_mark_in_progress_idempotent():
    """Calling mark_in_progress() on IN_PROGRESS task is no-op."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == old_updated_at


def test_mark_done_from_in_progress():
    """Task transitions IN_PROGRESS -> DONE."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.status == TaskStatus.IN_PROGRESS
    task.mark_done()
    assert task.status == TaskStatus.DONE


def test_mark_done_from_pending_noop():
    """Calling mark_done() on PENDING task is no-op."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at == old_updated_at


def test_reopen_from_done():
    """Task transitions DONE -> PENDING."""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.status == TaskStatus.DONE
    task.reopen()
    assert task.status == TaskStatus.PENDING


def test_reopen_from_pending_noop():
    """Calling reopen() on PENDING task is no-op."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at == old_updated_at


def test_reopen_from_in_progress_noop():
    """Calling reopen() on IN_PROGRESS task is no-op."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == old_updated_at


# Predicate Tests

def test_is_completed_on_done():
    """Returns True for DONE status."""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_on_other():
    """Returns False for non-DONE statuses."""
    for status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
        task = Task(title="Test", status=status)
        assert task.is_completed() is False


def test_is_pending_on_pending():
    """Returns True for PENDING status."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True


def test_is_pending_on_other():
    """Returns False for non-PENDING statuses."""
    for status in [TaskStatus.IN_PROGRESS, TaskStatus.DONE]:
        task = Task(title="Test", status=status)
        assert task.is_pending() is False


def test_is_in_progress_on_in_progress():
    """Returns True for IN_PROGRESS status."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


def test_is_in_progress_on_other():
    """Returns False for non-IN_PROGRESS statuses."""
    for status in [TaskStatus.PENDING, TaskStatus.DONE]:
        task = Task(title="Test", status=status)
        assert task.is_in_progress() is False


# Timestamp Tests

def test_updated_at_changed_on_valid_transition():
    """Verify updated_at is updated to CEST on valid transitions."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at

    # Mark in progress
    task.mark_in_progress()
    assert task.updated_at > old_updated_at
    assert task.updated_at.tzinfo == CEST

    # Mark done
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.updated_at > old_updated_at
    assert task.updated_at.tzinfo == CEST

    # Reopen
    old_updated_at = task.updated_at
    task.reopen()
    assert task.updated_at > old_updated_at
    assert task.updated_at.tzinfo == CEST


def test_updated_at_unchanged_on_noop_transition():
    """Verify updated_at is NOT updated on no-ops."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at

    task.mark_in_progress()
    assert task.updated_at == old_updated_at

    task.mark_done()
    old_updated_at = task.updated_at

    task.mark_done()
    assert task.updated_at == old_updated_at


# Overdue Tests

def test_is_overdue_with_future_due_date():
    """Returns False when due_date is in the future."""
    future_date = datetime.now(CEST) + timedelta(days=1)
    task = Task(title="Test", due_date=future_date)
    assert task.is_overdue() is False


def test_is_overdue_with_past_due_date():
    """Returns True when due_date is in the past."""
    past_date = datetime.now(CEST) - timedelta(days=1)
    task = Task(title="Test", due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_with_none_due_date():
    """Returns False when due_date is None."""
    task = Task(title="Test", due_date=None)
    assert task.is_overdue() is False


# Lifecycle Tests

def test_full_lifecycle():
    """PENDING -> IN_PROGRESS -> DONE -> PENDING with all state changes verified."""
    task = Task(title="Test")

    # Initial state
    assert task.is_pending() is True
    assert task.is_in_progress() is False
    assert task.is_completed() is False

    # Transition to IN_PROGRESS
    task.mark_in_progress()
    assert task.is_pending() is False
    assert task.is_in_progress() is True
    assert task.is_completed() is False

    # Transition to DONE
    task.mark_done()
    assert task.is_pending() is False
    assert task.is_in_progress() is False
    assert task.is_completed() is True

    # Transition back to PENDING
    task.reopen()
    assert task.is_pending() is True
    assert task.is_in_progress() is False
    assert task.is_completed() is False
