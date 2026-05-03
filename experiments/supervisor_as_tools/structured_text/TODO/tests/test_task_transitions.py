import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from src.models.task import Task
from src.models.task_status import TaskStatus


class TestMarkInProgress:
    def test_mark_in_progress_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_updated_at = task.updated_at
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at > original_updated_at

    def test_mark_in_progress_from_in_progress_is_noop(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated_at = task.updated_at
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at == original_updated_at

    def test_mark_in_progress_from_done_is_noop(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated_at = task.updated_at
        task.mark_in_progress()
        assert task.status == TaskStatus.DONE
        assert task.updated_at == original_updated_at

    def test_mark_in_progress_updates_to_utc(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        before = datetime.now(timezone.utc)
        task.mark_in_progress()
        after = datetime.now(timezone.utc)
        assert before <= task.updated_at <= after
        assert task.updated_at.tzinfo == timezone.utc


class TestMarkDone:
    def test_mark_done_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_updated_at = task.updated_at
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at > original_updated_at

    def test_mark_done_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated_at = task.updated_at
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at > original_updated_at

    def test_mark_done_from_done_is_noop(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated_at = task.updated_at
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at == original_updated_at

    def test_mark_done_updates_to_utc(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        before = datetime.now(timezone.utc)
        task.mark_done()
        after = datetime.now(timezone.utc)
        assert before <= task.updated_at <= after
        assert task.updated_at.tzinfo == timezone.utc


class TestReopen:
    def test_reopen_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated_at = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated_at

    def test_reopen_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated_at = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated_at

    def test_reopen_from_pending_is_noop(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_updated_at = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at == original_updated_at

    def test_reopen_updates_to_utc(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        before = datetime.now(timezone.utc)
        task.reopen()
        after = datetime.now(timezone.utc)
        assert before <= task.updated_at <= after
        assert task.updated_at.tzinfo == timezone.utc


class TestIsCompleted:
    def test_is_completed_true_when_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.is_completed() is True

    def test_is_completed_false_when_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_completed() is False

    def test_is_completed_false_when_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert task.is_completed() is False


class TestTimezoneHandling:
    def test_mark_in_progress_converts_cest_to_utc(self):
        """Verify that mark_in_progress uses CEST as intermediate timezone before converting to UTC."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        cest = ZoneInfo("Europe/Paris")
        before_cest = datetime.now(cest)
        task.mark_in_progress()
        after_cest = datetime.now(cest)
        # Convert task.updated_at to CEST for comparison
        updated_cest = task.updated_at.astimezone(cest)
        assert before_cest <= updated_cest <= after_cest
        assert task.updated_at.tzinfo == timezone.utc

    def test_mark_done_converts_cest_to_utc(self):
        """Verify that mark_done uses CEST as intermediate timezone before converting to UTC."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        cest = ZoneInfo("Europe/Paris")
        before_cest = datetime.now(cest)
        task.mark_done()
        after_cest = datetime.now(cest)
        updated_cest = task.updated_at.astimezone(cest)
        assert before_cest <= updated_cest <= after_cest
        assert task.updated_at.tzinfo == timezone.utc

    def test_reopen_converts_cest_to_utc(self):
        """Verify that reopen uses CEST as intermediate timezone before converting to UTC."""
        task = Task(title="Test", status=TaskStatus.DONE)
        cest = ZoneInfo("Europe/Paris")
        before_cest = datetime.now(cest)
        task.reopen()
        after_cest = datetime.now(cest)
        updated_cest = task.updated_at.astimezone(cest)
        assert before_cest <= updated_cest <= after_cest
        assert task.updated_at.tzinfo == timezone.utc


class TestIsOverdueWithCompletedTasks:
    def test_is_overdue_on_completed_task_with_past_due_date(self):
        """Completed tasks should still report as overdue if due_date is in the past."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        task = Task(title="Test", status=TaskStatus.DONE, due_date=past)
        assert task.is_overdue() is True
        assert task.is_completed() is True

    def test_is_overdue_on_pending_task_with_future_due_date(self):
        """Non-completed tasks should not be overdue if due_date is in the future."""
        future = datetime.now(timezone.utc) + timedelta(days=1)
        task = Task(title="Test", status=TaskStatus.PENDING, due_date=future)
        assert task.is_overdue() is False
        assert task.is_completed() is False

    def test_is_overdue_on_in_progress_task_with_past_due_date(self):
        """In-progress tasks should still report as overdue if due_date is in the past."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS, due_date=past)
        assert task.is_overdue() is True
        assert task.is_completed() is False


class TestTransitionChains:
    def test_full_workflow_pending_to_done(self):
        task = Task(title="Complete workflow", status=TaskStatus.PENDING)
        assert task.status == TaskStatus.PENDING
        assert not task.is_completed()

        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert not task.is_completed()

        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.is_completed()

    def test_full_workflow_with_reopen(self):
        task = Task(title="Reopen workflow", status=TaskStatus.PENDING)

        task.mark_in_progress()
        task.mark_done()
        assert task.is_completed()

        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert not task.is_completed()

        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_updated_at_only_changes_on_actual_transitions(self):
        """Verify that updated_at is only updated when status actually changes."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        updated_at_1 = task.updated_at

        # No-op transition
        task.reopen()
        assert task.updated_at == updated_at_1

        # Real transition
        task.mark_in_progress()
        updated_at_2 = task.updated_at
        assert updated_at_2 > updated_at_1

        # No-op transition
        task.mark_in_progress()
        assert task.updated_at == updated_at_2


class TestPersistence:
    def test_transitions_persist_in_to_dict(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        d = task.to_dict()
        assert d["status"] == "in_progress"

    def test_transitions_survive_roundtrip(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_done()
        original_status = task.status
        original_updated_at = task.updated_at

        restored = Task.from_dict(task.to_dict())
        assert restored.status == original_status
        assert restored.updated_at == original_updated_at
        assert restored.is_completed() is True

    def test_multiple_transitions_persist_final_state(self):
        task = Task(title="Test")
        task.mark_in_progress()
        task.mark_done()
        task.reopen()
        task.mark_in_progress()

        restored = Task.from_dict(task.to_dict())
        assert restored.status == TaskStatus.IN_PROGRESS
        assert restored.is_completed() is False
