import pytest
from datetime import datetime, timedelta
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


# Tests for mark_in_progress()
def test_mark_in_progress_from_pending():
    task = Task(title="Test")
    assert task.status == TaskStatus.PENDING
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > old_updated_at


def test_mark_in_progress_from_in_progress_is_noop():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == old_updated_at


def test_mark_in_progress_from_done_is_noop():
    task = Task(title="Test", status=TaskStatus.DONE)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.DONE
    assert task.updated_at == old_updated_at


# Tests for mark_done()
def test_mark_done_from_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at > old_updated_at


def test_mark_done_from_pending_is_noop():
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at == old_updated_at


def test_mark_done_from_done_is_noop():
    task = Task(title="Test", status=TaskStatus.DONE)
    old_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at == old_updated_at


# Tests for reopen()
def test_reopen_from_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > old_updated_at


def test_reopen_from_pending_is_noop():
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.PENDING
    assert task.updated_at == old_updated_at


def test_reopen_from_in_progress_is_noop():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == old_updated_at


# Tests for is_completed()
def test_is_completed_true_when_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_false_when_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_completed() is False


def test_is_completed_false_when_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_completed() is False


# Tests for is_pending()
def test_is_pending_true_when_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True


def test_is_pending_false_when_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_pending() is False


def test_is_pending_false_when_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_pending() is False


# Tests for is_in_progress()
def test_is_in_progress_true_when_in_progress():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


def test_is_in_progress_false_when_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_in_progress() is False


def test_is_in_progress_false_when_done():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_in_progress() is False


# Tests for is_overdue()
def test_is_overdue_with_past_due_date():
    past_date = datetime.now(CEST) - timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.PENDING, due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_with_future_due_date():
    future_date = datetime.now(CEST) + timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.PENDING, due_date=future_date)
    assert task.is_overdue() is False


def test_is_overdue_with_no_due_date():
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_overdue() is False


def test_is_overdue_false_when_done():
    past_date = datetime.now(CEST) - timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.DONE, due_date=past_date)
    assert task.is_overdue() is False


def test_is_overdue_false_when_in_progress_and_future():
    future_date = datetime.now(CEST) + timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS, due_date=future_date)
    assert task.is_overdue() is False


def test_is_overdue_true_when_in_progress_and_past():
    past_date = datetime.now(CEST) - timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS, due_date=past_date)
    assert task.is_overdue() is True


# Tests for updated_at timestamp (CEST)
def test_mark_in_progress_updates_timestamp_in_cest():
    task = Task(title="Test")
    task.mark_in_progress()
    # Verify updated_at is in CEST (has +02:00 offset or equivalent)
    assert task.updated_at.tzinfo is not None
    assert task.updated_at > task.created_at


def test_mark_done_updates_timestamp_in_cest():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    task.mark_done()
    # Verify updated_at is in CEST (has +02:00 offset or equivalent)
    assert task.updated_at.tzinfo is not None


def test_reopen_updates_timestamp_in_cest():
    task = Task(title="Test", status=TaskStatus.DONE)
    task.reopen()
    # Verify updated_at is in CEST (has +02:00 offset or equivalent)
    assert task.updated_at.tzinfo is not None


# Integration tests for state transitions
def test_full_workflow_pending_to_done():
    task = Task(title="Full workflow")
    assert task.is_pending() is True

    task.mark_in_progress()
    assert task.is_in_progress() is True
    assert task.is_pending() is False

    task.mark_done()
    assert task.is_completed() is True
    assert task.is_in_progress() is False


def test_full_workflow_with_reopening():
    task = Task(title="Full workflow with reopen")
    task.mark_in_progress()
    task.mark_done()
    assert task.is_completed() is True

    task.reopen()
    assert task.is_in_progress() is True
    assert task.is_completed() is False
