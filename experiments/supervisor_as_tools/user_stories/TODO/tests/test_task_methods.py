import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from src.models.task import Task
from src.models.task_status import TaskStatus


class TestTaskStatusChecks:
    """Test status checking methods: is_pending, is_in_progress, is_completed, is_overdue."""

    def test_is_pending_true(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_pending() is True

    def test_is_pending_false_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert task.is_pending() is False

    def test_is_pending_false_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.is_pending() is False

    def test_is_in_progress_true(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert task.is_in_progress() is True

    def test_is_in_progress_false_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_in_progress() is False

    def test_is_in_progress_false_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.is_in_progress() is False

    def test_is_completed_true(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.is_completed() is True

    def test_is_completed_false_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_completed() is False

    def test_is_completed_false_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert task.is_completed() is False

    def test_is_overdue_no_due_date(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_overdue() is False

    def test_is_overdue_completed_task(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        task = Task(title="Test", status=TaskStatus.DONE, due_date=past)
        assert task.is_overdue() is False

    def test_is_overdue_true(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        task = Task(title="Test", status=TaskStatus.PENDING, due_date=past)
        assert task.is_overdue() is True

    def test_is_overdue_future_due_date(self):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        task = Task(title="Test", status=TaskStatus.PENDING, due_date=future)
        assert task.is_overdue() is False


class TestTaskMutations:
    """Test status mutation methods: mark_in_progress, mark_done, reopen."""

    def test_mark_in_progress_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_updated = task.updated_at
        result = task.mark_in_progress()
        assert result is task  # returns self for chaining
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at > original_updated

    def test_mark_in_progress_idempotent(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated = task.updated_at
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at == original_updated  # no change

    def test_mark_in_progress_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated = task.updated_at
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at > original_updated

    def test_mark_done_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_updated = task.updated_at
        result = task.mark_done()
        assert result is task  # returns self for chaining
        assert task.status == TaskStatus.DONE
        assert task.updated_at > original_updated

    def test_mark_done_idempotent(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated = task.updated_at
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at == original_updated  # no change

    def test_mark_done_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated = task.updated_at
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at > original_updated

    def test_reopen_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated = task.updated_at
        result = task.reopen()
        assert result is task  # returns self for chaining
        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated

    def test_reopen_idempotent(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_updated = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at == original_updated  # no change

    def test_reopen_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated


class TestChaining:
    """Test method chaining capabilities."""

    def test_chain_mark_in_progress_then_done(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        result = task.mark_in_progress().mark_done()
        assert result is task
        assert task.status == TaskStatus.DONE

    def test_chain_mark_done_then_reopen(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        result = task.mark_in_progress().mark_done().reopen()
        assert result is task
        assert task.status == TaskStatus.PENDING


class TestSerialization:
    """Test serialization roundtrips with new methods."""

    def test_roundtrip_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        restored = Task.from_dict(task.to_dict())
        assert restored.is_pending() is True
        assert restored.is_in_progress() is False
        assert restored.is_completed() is False

    def test_roundtrip_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        restored = Task.from_dict(task.to_dict())
        assert restored.is_pending() is False
        assert restored.is_in_progress() is True
        assert restored.is_completed() is False

    def test_roundtrip_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        restored = Task.from_dict(task.to_dict())
        assert restored.is_pending() is False
        assert restored.is_in_progress() is False
        assert restored.is_completed() is True

    def test_roundtrip_after_mutation(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        restored = Task.from_dict(task.to_dict())
        assert restored.status == TaskStatus.IN_PROGRESS
        assert restored.is_in_progress() is True
