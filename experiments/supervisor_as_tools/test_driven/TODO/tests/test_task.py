import pytest
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


class TestTaskStatusTransitions:
    """Test status transition methods: mark_in_progress, mark_done, reopen"""

    def test_mark_in_progress_changes_status(self):
        task = Task(title="Work")
        assert task.status == TaskStatus.PENDING
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_mark_in_progress_updates_timestamp(self):
        from datetime import datetime
        from src.models.task import CEST

        task = Task(title="Work")
        original_updated_at = task.updated_at
        task.mark_in_progress()
        assert task.updated_at > original_updated_at
        assert task.updated_at.tzinfo == CEST

    def test_mark_done_changes_status(self):
        task = Task(title="Work")
        task.mark_done()
        assert task.status == TaskStatus.DONE

    def test_mark_done_updates_timestamp(self):
        from datetime import datetime
        from src.models.task import CEST

        task = Task(title="Work")
        original_updated_at = task.updated_at
        task.mark_done()
        assert task.updated_at > original_updated_at
        assert task.updated_at.tzinfo == CEST

    def test_reopen_changes_status_back_to_pending(self):
        task = Task(title="Work", status=TaskStatus.DONE)
        task.reopen()
        assert task.status == TaskStatus.PENDING

    def test_reopen_from_in_progress_to_pending(self):
        task = Task(title="Work", status=TaskStatus.IN_PROGRESS)
        task.reopen()
        assert task.status == TaskStatus.PENDING

    def test_reopen_updates_timestamp(self):
        from datetime import datetime
        from src.models.task import CEST

        task = Task(title="Work", status=TaskStatus.DONE)
        original_updated_at = task.updated_at
        task.reopen()
        assert task.updated_at > original_updated_at
        assert task.updated_at.tzinfo == CEST

    def test_status_transitions_chain(self):
        task = Task(title="Work")
        assert task.status == TaskStatus.PENDING

        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

        task.mark_done()
        assert task.status == TaskStatus.DONE

        task.reopen()
        assert task.status == TaskStatus.PENDING


class TestTaskStatusChecks:
    """Test status checking methods: is_completed, is_pending, is_in_progress"""

    @pytest.mark.parametrize("status,expected_completed", [
        (TaskStatus.PENDING, False),
        (TaskStatus.IN_PROGRESS, False),
        (TaskStatus.DONE, True),
    ])
    def test_is_completed(self, status, expected_completed):
        task = Task(title="Test", status=status)
        assert task.is_completed() == expected_completed

    @pytest.mark.parametrize("status,expected_pending", [
        (TaskStatus.PENDING, True),
        (TaskStatus.IN_PROGRESS, False),
        (TaskStatus.DONE, False),
    ])
    def test_is_pending(self, status, expected_pending):
        task = Task(title="Test", status=status)
        assert task.is_pending() == expected_pending

    @pytest.mark.parametrize("status,expected_in_progress", [
        (TaskStatus.PENDING, False),
        (TaskStatus.IN_PROGRESS, True),
        (TaskStatus.DONE, False),
    ])
    def test_is_in_progress(self, status, expected_in_progress):
        task = Task(title="Test", status=status)
        assert task.is_in_progress() == expected_in_progress

    def test_status_checks_mutually_exclusive(self):
        """Ensure only one status check is true at a time"""
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_pending()
        assert not task.is_in_progress()
        assert not task.is_completed()

        task.mark_in_progress()
        assert not task.is_pending()
        assert task.is_in_progress()
        assert not task.is_completed()

        task.mark_done()
        assert not task.is_pending()
        assert not task.is_in_progress()
        assert task.is_completed()


class TestTaskOverdue:
    """Test is_overdue method for due date checking"""

    def test_is_overdue_returns_false_when_no_due_date(self):
        task = Task(title="No deadline")
        assert task.due_date is None
        assert task.is_overdue() is False

    def test_is_overdue_returns_false_when_future_due_date(self):
        from datetime import datetime, timedelta
        from src.models.task import CEST

        future = datetime.now(tz=CEST) + timedelta(days=1)
        task = Task(title="Future due", due_date=future)
        assert task.is_overdue() is False

    def test_is_overdue_returns_true_when_past_due_date(self):
        from datetime import datetime, timedelta
        from src.models.task import CEST

        past = datetime.now(tz=CEST) - timedelta(days=1)
        task = Task(title="Overdue", due_date=past)
        assert task.is_overdue() is True

    def test_is_overdue_with_due_date_exactly_now(self):
        from datetime import datetime, timedelta
        from src.models.task import CEST

        # This is a boundary test - if due_date is now, should it be overdue?
        # Based on the implementation: return datetime.now(tz=CEST) > self.due_date
        # We use future instead to avoid race conditions
        future = datetime.now(tz=CEST) + timedelta(seconds=1)
        task = Task(title="Due in future", due_date=future)
        assert task.is_overdue() is False

    def test_is_overdue_one_second_past(self):
        from datetime import datetime, timedelta
        from src.models.task import CEST

        just_past = datetime.now(tz=CEST) - timedelta(seconds=1)
        task = Task(title="Just overdue", due_date=just_past)
        assert task.is_overdue() is True

    def test_is_overdue_with_status_independent(self):
        """Due date overdue status should be independent of task status"""
        from datetime import datetime, timedelta
        from src.models.task import CEST

        past = datetime.now(tz=CEST) - timedelta(days=1)

        task_pending = Task(title="Overdue pending", due_date=past, status=TaskStatus.PENDING)
        assert task_pending.is_overdue()

        task_in_progress = Task(title="Overdue in progress", due_date=past, status=TaskStatus.IN_PROGRESS)
        assert task_in_progress.is_overdue()

        task_done = Task(title="Overdue done", due_date=past, status=TaskStatus.DONE)
        assert task_done.is_overdue()


class TestTaskDueDateValidation:
    """Test that due_date validation works correctly"""

    def test_due_date_must_be_timezone_aware(self):
        from datetime import datetime

        naive_datetime = datetime(2025, 12, 31, 23, 59, 59)
        with pytest.raises(ValueError, match="must be timezone-aware"):
            Task(title="Test", due_date=naive_datetime)

    def test_due_date_must_be_cest(self):
        from datetime import datetime, timezone, timedelta

        utc = timezone.utc
        utc_datetime = datetime(2025, 12, 31, 23, 59, 59, tzinfo=utc)
        with pytest.raises(ValueError, match="must be in CEST timezone"):
            Task(title="Test", due_date=utc_datetime)

    def test_due_date_cest_accepted(self):
        from datetime import datetime
        from src.models.task import CEST

        cest_datetime = datetime(2025, 12, 31, 23, 59, 59, tzinfo=CEST)
        task = Task(title="Test", due_date=cest_datetime)
        assert task.due_date == cest_datetime
