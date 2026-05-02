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


class TestStatusTransitions:
    def test_mark_in_progress_from_pending(self):
        task = Task(title="Test")
        assert task.status == TaskStatus.PENDING
        old_updated_at = task.updated_at
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at > old_updated_at
        assert task.updated_at.tzinfo == CEST

    def test_mark_done_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        old_updated_at = task.updated_at
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at > old_updated_at
        assert task.updated_at.tzinfo == CEST

    def test_mark_done_from_pending(self):
        task = Task(title="Test")
        old_updated_at = task.updated_at
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at > old_updated_at
        assert task.updated_at.tzinfo == CEST

    def test_reopen_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        old_updated_at = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at > old_updated_at
        assert task.updated_at.tzinfo == CEST

    def test_reopen_from_pending_is_noop(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        old_updated_at = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at == old_updated_at

    def test_reopen_from_in_progress_is_noop(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        old_updated_at = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at == old_updated_at

    def test_full_workflow(self):
        task = Task(title="Test")
        assert task.is_pending()
        task.mark_in_progress()
        assert task.is_in_progress()
        task.mark_done()
        assert task.is_completed()
        task.reopen()
        assert task.is_pending()


class TestStatusPredicates:
    def test_is_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_pending()
        assert not task.is_in_progress()
        assert not task.is_completed()

    def test_is_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert not task.is_pending()
        assert task.is_in_progress()
        assert not task.is_completed()

    def test_is_completed(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert not task.is_pending()
        assert not task.is_in_progress()
        assert task.is_completed()


class TestOverdue:
    def test_no_due_date_not_overdue(self):
        task = Task(title="Test")
        assert not task.is_overdue()

    def test_future_due_date_not_overdue(self):
        future = datetime.now(CEST) + timedelta(days=1)
        task = Task(title="Test", due_date=future)
        assert not task.is_overdue()

    def test_past_due_date_is_overdue(self):
        past = datetime.now(CEST) - timedelta(days=1)
        task = Task(title="Test", due_date=past, status=TaskStatus.IN_PROGRESS)
        assert task.is_overdue()

    def test_completed_task_not_overdue(self):
        past = datetime.now(CEST) - timedelta(days=1)
        task = Task(title="Test", due_date=past, status=TaskStatus.DONE)
        assert not task.is_overdue()

    def test_just_past_due_date_is_overdue(self):
        past = datetime.now(CEST) - timedelta(seconds=1)
        task = Task(title="Test", due_date=past, status=TaskStatus.PENDING)
        assert task.is_overdue()
