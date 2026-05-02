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


# ===== Status Transition Tests (9 combinations) =====

@pytest.mark.parametrize(
    "initial_status,method,expected_status",
    [
        # PENDING transitions
        (TaskStatus.PENDING, "mark_in_progress", TaskStatus.IN_PROGRESS),
        (TaskStatus.PENDING, "mark_done", TaskStatus.DONE),
        (TaskStatus.PENDING, "reopen", TaskStatus.PENDING),
        # IN_PROGRESS transitions
        (TaskStatus.IN_PROGRESS, "mark_in_progress", TaskStatus.IN_PROGRESS),
        (TaskStatus.IN_PROGRESS, "mark_done", TaskStatus.DONE),
        (TaskStatus.IN_PROGRESS, "reopen", TaskStatus.PENDING),
        # DONE transitions
        (TaskStatus.DONE, "mark_in_progress", TaskStatus.IN_PROGRESS),
        (TaskStatus.DONE, "mark_done", TaskStatus.DONE),
        (TaskStatus.DONE, "reopen", TaskStatus.PENDING),
    ],
    ids=[
        "PENDING->IN_PROGRESS",
        "PENDING->DONE",
        "PENDING->PENDING_noop",
        "IN_PROGRESS->IN_PROGRESS_noop",
        "IN_PROGRESS->DONE",
        "IN_PROGRESS->PENDING",
        "DONE->IN_PROGRESS",
        "DONE->DONE_noop",
        "DONE->PENDING",
    ]
)
def test_status_transitions(initial_status, method, expected_status):
    """Test all 9 status transition combinations."""
    task = Task(title="Test", status=initial_status)
    getattr(task, method)()
    assert task.status == expected_status


# ===== Timestamp Update Tests (6 tests) =====

def test_mark_in_progress_updates_timestamp_on_transition():
    """Verify updated_at changes when marking PENDING task as IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_timestamp = task.updated_at
    task.mark_in_progress()
    assert task.updated_at > old_timestamp


def test_mark_in_progress_skips_timestamp_on_noop():
    """Verify updated_at unchanged when calling mark_in_progress on IN_PROGRESS task."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_timestamp = task.updated_at
    task.mark_in_progress()
    assert task.updated_at == old_timestamp


def test_mark_done_updates_timestamp_on_transition():
    """Verify updated_at changes when marking IN_PROGRESS task as DONE."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    old_timestamp = task.updated_at
    task.mark_done()
    assert task.updated_at > old_timestamp


def test_mark_done_skips_timestamp_on_noop():
    """Verify updated_at unchanged when calling mark_done on DONE task."""
    task = Task(title="Test", status=TaskStatus.DONE)
    old_timestamp = task.updated_at
    task.mark_done()
    assert task.updated_at == old_timestamp


def test_reopen_updates_timestamp_on_transition():
    """Verify updated_at changes when reopening DONE task."""
    task = Task(title="Test", status=TaskStatus.DONE)
    old_timestamp = task.updated_at
    task.reopen()
    assert task.updated_at > old_timestamp


def test_reopen_skips_timestamp_on_noop():
    """Verify updated_at unchanged when calling reopen on PENDING task."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    old_timestamp = task.updated_at
    task.reopen()
    assert task.updated_at == old_timestamp


# ===== Query Method Tests (3 tests) =====

def test_is_completed_returns_true_for_done():
    """Verify is_completed returns True when status is DONE."""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_returns_false_for_pending():
    """Verify is_completed returns False when status is PENDING."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_completed() is False


def test_is_completed_returns_false_for_in_progress():
    """Verify is_completed returns False when status is IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_completed() is False


# ===== Edge Case Tests =====

def test_chained_mutations_with_timestamp_updates():
    """Test PENDING → IN_PROGRESS → DONE → PENDING with timestamp verification."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    ts1 = task.updated_at

    task.mark_in_progress()
    ts2 = task.updated_at
    assert ts2 > ts1
    assert task.status == TaskStatus.IN_PROGRESS

    task.mark_done()
    ts3 = task.updated_at
    assert ts3 > ts2
    assert task.status == TaskStatus.DONE

    task.reopen()
    ts4 = task.updated_at
    assert ts4 > ts3
    assert task.status == TaskStatus.PENDING


def test_multiple_noop_calls_do_not_change_timestamp():
    """Verify timestamp stays unchanged across multiple no-op calls."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    original_timestamp = task.updated_at

    task.mark_in_progress()
    assert task.updated_at == original_timestamp

    task.mark_in_progress()
    assert task.updated_at == original_timestamp

    task.mark_in_progress()
    assert task.updated_at == original_timestamp


def test_mark_done_from_pending_skips_intermediate_in_progress():
    """Verify can transition directly from PENDING to DONE without intermediate IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.is_completed() is True
