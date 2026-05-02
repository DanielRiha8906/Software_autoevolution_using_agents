import pytest
from datetime import datetime, timedelta, timezone
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


def test_task_due_date_default():
    task = Task(title="Test")
    assert task.due_date is None


def test_task_due_date_set():
    due = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    task = Task(title="Test", due_date=due)
    assert task.due_date == due


def test_task_due_date_roundtrip():
    due = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    task = Task(title="Test", due_date=due)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due


def test_task_due_date_none_roundtrip():
    task = Task(title="Test", due_date=None)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date is None


def test_task_due_date_backward_compatibility():
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


def test_task_due_date_with_cest_timezone():
    from datetime import timezone as tz
    cest = tz(timedelta(hours=2))
    due = datetime(2025, 12, 31, 23, 59, 59, tzinfo=cest)
    task = Task(title="Test", due_date=due)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due


def test_task_is_overdue_true():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    task = Task(title="Test", due_date=past)
    assert task.is_overdue() is True


def test_task_is_overdue_false_future():
    future = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", due_date=future)
    assert task.is_overdue() is False


def test_task_is_overdue_none():
    task = Task(title="Test", due_date=None)
    assert task.is_overdue() is False


# Tests for mark_in_progress()
def test_mark_in_progress_from_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > original_updated_at


def test_mark_in_progress_from_in_progress_raises():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    with pytest.raises(ValueError, match="already in progress"):
        task.mark_in_progress()


def test_mark_in_progress_from_done_raises():
    task = Task(title="Test", status=TaskStatus.DONE)
    with pytest.raises(ValueError, match="completed task"):
        task.mark_in_progress()


# Tests for mark_done()
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


def test_mark_done_from_done_raises():
    task = Task(title="Test", status=TaskStatus.DONE)
    with pytest.raises(ValueError, match="already done"):
        task.mark_done()


# Tests for reopen()
def test_reopen_from_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    original_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at > original_updated_at


def test_reopen_from_pending_raises():
    task = Task(title="Test", status=TaskStatus.PENDING)
    with pytest.raises(ValueError, match="completed tasks"):
        task.reopen()


def test_reopen_from_in_progress_raises():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    with pytest.raises(ValueError, match="completed tasks"):
        task.reopen()


# Tests for is_completed()
def test_is_completed_true():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_false_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_completed() is False


def test_is_completed_false_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_completed() is False


# Tests for is_pending()
def test_is_pending_true():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True


def test_is_pending_false_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_pending() is False


def test_is_pending_false_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_pending() is False


# Tests for is_in_progress()
def test_is_in_progress_true():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


def test_is_in_progress_false_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_in_progress() is False


def test_is_in_progress_false_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_in_progress() is False


# Tests for valid transition chains
def test_transition_pending_to_in_progress_to_done():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True

    task.mark_in_progress()
    assert task.is_in_progress() is True

    task.mark_done()
    assert task.is_completed() is True


def test_transition_pending_to_done_direct():
    task = Task(title="Test", status=TaskStatus.PENDING)
    task.mark_done()
    assert task.is_completed() is True


def test_transition_done_to_pending_via_reopen():
    task = Task(title="Test", status=TaskStatus.DONE)
    task.reopen()
    assert task.is_pending() is True


def test_transition_complex_flow():
    """Test a complex transition flow: PENDING -> IN_PROGRESS -> DONE -> PENDING -> IN_PROGRESS -> DONE"""
    task = Task(title="Test")

    # PENDING -> IN_PROGRESS
    task.mark_in_progress()
    assert task.is_in_progress() is True

    # IN_PROGRESS -> DONE
    task.mark_done()
    assert task.is_completed() is True

    # DONE -> PENDING (reopen)
    task.reopen()
    assert task.is_pending() is True

    # PENDING -> IN_PROGRESS
    task.mark_in_progress()
    assert task.is_in_progress() is True

    # IN_PROGRESS -> DONE
    task.mark_done()
    assert task.is_completed() is True


# Tests for updated_at timestamp
def test_mark_in_progress_updates_timestamp():
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_updated_at = task.updated_at
    # Small delay to ensure timestamp difference
    import time
    time.sleep(0.01)
    task.mark_in_progress()
    assert task.updated_at > original_updated_at
    assert task.updated_at.tzinfo == timezone.utc


def test_mark_done_updates_timestamp():
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_updated_at = task.updated_at
    import time
    time.sleep(0.01)
    task.mark_done()
    assert task.updated_at > original_updated_at
    assert task.updated_at.tzinfo == timezone.utc


def test_reopen_updates_timestamp():
    task = Task(title="Test", status=TaskStatus.DONE)
    original_updated_at = task.updated_at
    import time
    time.sleep(0.01)
    task.reopen()
    assert task.updated_at > original_updated_at
    assert task.updated_at.tzinfo == timezone.utc


# Tests ensuring is_overdue still works correctly with status transitions
def test_is_overdue_with_status_transitions():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    task = Task(title="Test", due_date=past, status=TaskStatus.PENDING)
    assert task.is_overdue() is True

    task.mark_in_progress()
    assert task.is_overdue() is True

    task.mark_done()
    assert task.is_overdue() is True


def test_is_overdue_with_reopen():
    future = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", due_date=future, status=TaskStatus.DONE)
    assert task.is_overdue() is False

    task.reopen()
    assert task.is_overdue() is False
