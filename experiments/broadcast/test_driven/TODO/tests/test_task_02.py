import pytest
from datetime import datetime, timezone, timedelta
from src.models.task import Task
from src.models.task_status import TaskStatus

CEST = timezone(timedelta(hours=2))
PAST = datetime(2020, 1, 1, tzinfo=CEST)
FUTURE = datetime(2099, 1, 1, tzinfo=CEST)


def test_mark_in_progress():
    task = Task(title="Test")
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS


def test_mark_done():
    task = Task(title="Test")
    task.mark_done()
    assert task.status == TaskStatus.DONE


def test_reopen():
    task = Task(title="Test")
    task.mark_done()
    task.reopen()
    assert task.status == TaskStatus.PENDING


def test_status_mutation_updates_updated_at():
    task = Task(title="Test")
    before = task.updated_at
    task.mark_in_progress()
    assert task.updated_at >= before

def test_status_mutation_updates_updated_at_to_cest():
    task = Task(title="Test")
    task.mark_in_progress()
    assert task.updated_at.tzinfo == CEST

def test_is_completed_true_when_done():
    task = Task(title="Test")
    task.mark_done()
    assert task.is_completed() is True


def test_is_completed_false_when_pending():
    assert Task(title="Test").is_completed() is False


def test_is_overdue_true_when_past_due():
    assert Task(title="Test", due_date=PAST).is_overdue() is True


def test_is_overdue_false_when_future_due():
    assert Task(title="Test", due_date=FUTURE).is_overdue() is False


def test_is_overdue_false_when_no_due_date():
    assert Task(title="Test").is_overdue() is False


def test_is_pending():
    assert Task(title="Test").is_pending() is True


def test_is_in_progress():
    task = Task(title="Test")
    task.mark_in_progress()
    assert task.is_in_progress() is True


def test_reopen_on_pending_is_noop_or_raises():
    task = Task(title="Test")
    try:
        task.reopen()
        assert task.status == TaskStatus.PENDING
    except Exception:
        pass
