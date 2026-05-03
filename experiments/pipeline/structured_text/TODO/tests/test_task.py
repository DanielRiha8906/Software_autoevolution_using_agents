import pytest
from datetime import datetime, timezone, timedelta
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


# ===== Due Date Feature Tests =====

def test_task_due_date_default_none():
    """Verify due_date defaults to None when not provided."""
    task = Task(title="Test Task")
    assert task.due_date is None


def test_task_due_date_set():
    """Verify due_date can be set explicitly."""
    due_date = datetime(2025, 12, 25, 10, 0, 0, tzinfo=timezone.utc)
    task = Task(title="Test Task", due_date=due_date)
    assert task.due_date == due_date


def test_task_due_date_roundtrip():
    """Create → to_dict() → from_dict() → verify due_date matches."""
    due_date = datetime(2025, 12, 25, 15, 30, 45, tzinfo=timezone.utc)
    task = Task(title="Test Task", due_date=due_date)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == due_date
    assert restored.due_date.tzinfo is not None


def test_task_to_dict_omits_null_due_date():
    """Verify 'due_date' key is not in dict when due_date is None."""
    task = Task(title="Test Task")
    task_dict = task.to_dict()
    assert "due_date" not in task_dict


def test_task_to_dict_includes_due_date():
    """Verify 'due_date' key is in dict when due_date is set."""
    due_date = datetime(2025, 12, 25, 10, 0, 0, tzinfo=timezone.utc)
    task = Task(title="Test Task", due_date=due_date)
    task_dict = task.to_dict()
    assert "due_date" in task_dict
    assert task_dict["due_date"] == due_date.isoformat()


def test_task_from_dict_without_due_date():
    """Simulate old JSON without due_date key, verify loads with None."""
    old_data = {
        "id": "test-id",
        "title": "Old Task",
        "description": None,
        "status": "pending",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00"
    }
    task = Task.from_dict(old_data)
    assert task.due_date is None
    assert task.title == "Old Task"


def test_task_from_dict_with_due_date():
    """Test from_dict with due_date present."""
    data = {
        "id": "test-id",
        "title": "Task with due date",
        "description": None,
        "status": "pending",
        "due_date": "2025-12-25T10:00:00+00:00",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00"
    }
    task = Task.from_dict(data)
    assert task.due_date is not None
    assert task.due_date == datetime(2025, 12, 25, 10, 0, 0, tzinfo=timezone.utc)


def test_is_overdue_no_due_date():
    """No due_date → returns False."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_overdue() is False


def test_is_overdue_future_date():
    """Future due_date → returns False."""
    future = datetime.now(timezone.utc) + timedelta(days=10)
    task = Task(title="Test", due_date=future, status=TaskStatus.PENDING)
    assert task.is_overdue() is False


def test_is_overdue_past_date():
    """Past due_date → returns True."""
    past = datetime.now(timezone.utc) - timedelta(days=10)
    task = Task(title="Test", due_date=past, status=TaskStatus.PENDING)
    assert task.is_overdue() is True


def test_is_overdue_past_date_in_progress():
    """Past due_date with IN_PROGRESS status → returns True."""
    past = datetime.now(timezone.utc) - timedelta(days=10)
    task = Task(title="Test", due_date=past, status=TaskStatus.IN_PROGRESS)
    assert task.is_overdue() is True


def test_is_overdue_completed_task():
    """Past due_date but DONE status → returns False."""
    past = datetime.now(timezone.utc) - timedelta(days=10)
    task = Task(title="Test", due_date=past, status=TaskStatus.DONE)
    assert task.is_overdue() is False


def test_is_overdue_edge_case_very_recent_past():
    """Due date just now (or very recently) → returns True."""
    just_past = datetime.now(timezone.utc) - timedelta(seconds=1)
    task = Task(title="Test", due_date=just_past, status=TaskStatus.PENDING)
    assert task.is_overdue() is True


def test_task_roundtrip_with_due_date():
    """Comprehensive roundtrip test including due_date."""
    due_date = datetime(2025, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
    task = Task(
        title="Complete project",
        description="Finish the implementation",
        due_date=due_date,
        status=TaskStatus.IN_PROGRESS
    )
    restored = Task.from_dict(task.to_dict())
    assert restored.id == task.id
    assert restored.title == task.title
    assert restored.description == task.description
    assert restored.due_date == due_date
    assert restored.status == task.status
    assert restored.created_at == task.created_at
    assert restored.updated_at == task.updated_at


# ===== Task Status Change Methods (Task 02) =====

class TestIsCompleted:
    """Tests for Task.is_completed() method."""

    @pytest.mark.parametrize("status,expected", [
        (TaskStatus.PENDING, False),
        (TaskStatus.IN_PROGRESS, False),
        (TaskStatus.DONE, True),
    ])
    def test_is_completed_returns_correct_boolean(self, status, expected):
        """is_completed() returns True only when status is DONE, False otherwise."""
        task = Task(title="Test", status=status)
        assert task.is_completed() is expected

    def test_is_completed_pending_task(self):
        """Newly created tasks are PENDING and not completed."""
        task = Task(title="New task")
        assert task.is_completed() is False

    def test_is_completed_after_mark_done(self):
        """After mark_done(), is_completed() returns True."""
        task = Task(title="Test")
        task.mark_done()
        assert task.is_completed() is True

    def test_is_completed_after_mark_in_progress(self):
        """IN_PROGRESS status yields is_completed() False."""
        task = Task(title="Test")
        task.mark_in_progress()
        assert task.is_completed() is False


class TestMarkDone:
    """Tests for Task.mark_done() method."""

    def test_mark_done_sets_status_to_done(self):
        """mark_done() sets status to DONE."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_done()
        assert task.status == TaskStatus.DONE

    def test_mark_done_updates_timestamp(self):
        """mark_done() updates updated_at to a later time."""
        task = Task(title="Test")
        original_updated = task.updated_at
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        task.mark_done()
        assert task.updated_at > original_updated

    def test_mark_done_returns_self(self):
        """mark_done() returns self for method chaining."""
        task = Task(title="Test")
        result = task.mark_done()
        assert result is task

    def test_mark_done_from_in_progress(self):
        """mark_done() works from IN_PROGRESS status."""
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        task.mark_done()
        assert task.status == TaskStatus.DONE

    def test_mark_done_from_done_already(self):
        """mark_done() on already DONE task idempotent."""
        task = Task(title="Test", status=TaskStatus.DONE)
        first_done_time = task.updated_at
        import time
        time.sleep(0.01)
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at > first_done_time

    def test_mark_done_method_chaining(self):
        """mark_done() can be chained with other methods."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        result = task.mark_done()
        assert result.is_completed() is True

    def test_mark_done_created_at_unchanged(self):
        """mark_done() does not change created_at."""
        task = Task(title="Test")
        original_created = task.created_at
        task.mark_done()
        assert task.created_at == original_created


class TestMarkInProgress:
    """Tests for Task.mark_in_progress() method."""

    def test_mark_in_progress_sets_status(self):
        """mark_in_progress() sets status to IN_PROGRESS."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_mark_in_progress_updates_timestamp(self):
        """mark_in_progress() updates updated_at to a later time."""
        task = Task(title="Test")
        original_updated = task.updated_at
        import time
        time.sleep(0.01)
        task.mark_in_progress()
        assert task.updated_at > original_updated

    def test_mark_in_progress_returns_self(self):
        """mark_in_progress() returns self for method chaining."""
        task = Task(title="Test")
        result = task.mark_in_progress()
        assert result is task

    def test_mark_in_progress_from_pending(self):
        """mark_in_progress() works from PENDING status."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_mark_in_progress_from_done(self):
        """mark_in_progress() can set a DONE task back to IN_PROGRESS."""
        task = Task(title="Test", status=TaskStatus.DONE)
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_mark_in_progress_method_chaining(self):
        """mark_in_progress() can be chained with other methods."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        result = task.mark_in_progress()
        assert result.status == TaskStatus.IN_PROGRESS
        assert result.is_completed() is False


class TestReopen:
    """Tests for Task.reopen() method."""

    def test_reopen_sets_status_to_pending(self):
        """reopen() sets status to PENDING."""
        task = Task(title="Test", status=TaskStatus.DONE)
        task.reopen()
        assert task.status == TaskStatus.PENDING

    def test_reopen_updates_timestamp(self):
        """reopen() updates updated_at to a later time."""
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated = task.updated_at
        import time
        time.sleep(0.01)
        task.reopen()
        assert task.updated_at > original_updated

    def test_reopen_returns_self(self):
        """reopen() returns self for method chaining."""
        task = Task(title="Test", status=TaskStatus.DONE)
        result = task.reopen()
        assert result is task

    def test_reopen_from_done(self):
        """reopen() works from DONE status."""
        task = Task(title="Test", status=TaskStatus.DONE)
        task.reopen()
        assert task.status == TaskStatus.PENDING

    def test_reopen_from_in_progress(self):
        """reopen() can set an IN_PROGRESS task back to PENDING."""
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        task.reopen()
        assert task.status == TaskStatus.PENDING

    def test_reopen_method_chaining(self):
        """reopen() can be chained with other methods."""
        task = Task(title="Test", status=TaskStatus.DONE)
        result = task.reopen()
        assert result.status == TaskStatus.PENDING
        assert result.is_completed() is False


class TestStatusTransitions:
    """Tests for combined status transition scenarios."""

    def test_pending_to_in_progress_to_done(self):
        """Transitions: PENDING → IN_PROGRESS → DONE."""
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_completed() is False

        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.is_completed() is False

        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.is_completed() is True

    def test_done_to_pending_to_in_progress(self):
        """Transitions: DONE → PENDING (reopen) → IN_PROGRESS."""
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.is_completed() is True

        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.is_completed() is False

        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.is_completed() is False

    def test_done_back_to_in_progress_directly(self):
        """Transitions: DONE → IN_PROGRESS (without reopen)."""
        task = Task(title="Test", status=TaskStatus.DONE)
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.is_completed() is False

    def test_timestamps_strictly_increasing_across_transitions(self):
        """Timestamps increase strictly with each status change."""
        import time
        task = Task(title="Test")
        t1 = task.updated_at

        time.sleep(0.01)
        task.mark_in_progress()
        t2 = task.updated_at
        assert t2 > t1

        time.sleep(0.01)
        task.mark_done()
        t3 = task.updated_at
        assert t3 > t2

        time.sleep(0.01)
        task.reopen()
        t4 = task.updated_at
        assert t4 > t3


class TestIsOverdueAfterStatusChanges:
    """Tests for is_overdue() behavior after status changes."""

    def test_is_overdue_remains_true_after_mark_in_progress(self):
        """is_overdue() stays True after mark_in_progress()."""
        past = datetime.now(timezone.utc) - timedelta(days=10)
        task = Task(title="Test", due_date=past, status=TaskStatus.PENDING)
        assert task.is_overdue() is True

        task.mark_in_progress()
        assert task.is_overdue() is True

    def test_is_overdue_becomes_false_after_mark_done(self):
        """is_overdue() becomes False after mark_done()."""
        past = datetime.now(timezone.utc) - timedelta(days=10)
        task = Task(title="Test", due_date=past, status=TaskStatus.PENDING)
        assert task.is_overdue() is True

        task.mark_done()
        assert task.is_overdue() is False

    def test_is_overdue_becomes_true_after_reopen(self):
        """is_overdue() becomes True again after reopen() from DONE."""
        past = datetime.now(timezone.utc) - timedelta(days=10)
        task = Task(title="Test", due_date=past, status=TaskStatus.DONE)
        assert task.is_overdue() is False

        task.reopen()
        assert task.is_overdue() is True

    def test_completed_task_not_overdue_regardless_of_transitions(self):
        """A DONE task is never overdue, even after transitions."""
        past = datetime.now(timezone.utc) - timedelta(days=10)
        task = Task(title="Test", due_date=past)

        task.mark_in_progress()
        task.mark_done()
        assert task.is_overdue() is False

        # Reopen and complete again
        task.reopen()
        task.mark_in_progress()
        task.mark_done()
        assert task.is_overdue() is False
