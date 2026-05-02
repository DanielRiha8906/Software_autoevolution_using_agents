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


# ─── Due date tests ─────────────────────────────────────────────────────────

def test_task_default_due_date_is_none():
    """Test that due_date defaults to None"""
    task = Task(title="No deadline")
    assert task.due_date is None


def test_task_with_timezone_aware_datetime():
    """Test Task accepts timezone-aware datetime"""
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    task = Task(title="Deadline", due_date=dt)
    assert task.due_date == dt
    assert task.due_date.tzinfo is not None


def test_task_with_timezone_aware_datetime_different_tz():
    """Test Task accepts timezone-aware datetime with different timezone"""
    tz_plus_2 = timezone(timedelta(hours=2))
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=tz_plus_2)
    task = Task(title="Deadline", due_date=dt)
    assert task.due_date == dt
    assert task.due_date.tzinfo is not None


def test_task_rejects_naive_datetime():
    """Test Task raises ValueError for naive datetime"""
    dt_naive = datetime(2026, 5, 15, 14, 30)  # no tzinfo
    with pytest.raises(ValueError, match="due_date must be timezone-aware"):
        Task(title="Deadline", due_date=dt_naive)


def test_task_roundtrip_with_due_date():
    """Test to_dict/from_dict preserves due_date with timezone"""
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    task = Task(title="Task with deadline", due_date=dt)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == task.due_date
    assert restored.due_date.tzinfo is not None


def test_task_roundtrip_without_due_date():
    """Test to_dict/from_dict with None due_date"""
    task = Task(title="No deadline")
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date is None


def test_task_from_dict_missing_due_date_key():
    """Test backward compatibility: missing due_date key → None"""
    data = {
        "id": "test-id",
        "title": "Legacy task",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    # Note: no "due_date" key
    task = Task.from_dict(data)
    assert task.due_date is None


def test_task_from_dict_null_due_date():
    """Test from_dict with null due_date → None"""
    data = {
        "id": "test-id",
        "title": "Task with null due_date",
        "description": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "due_date": None,
    }
    task = Task.from_dict(data)
    assert task.due_date is None


@pytest.mark.parametrize("tz_offset", [0, 1, 2, -5, 12])
def test_task_roundtrip_preserves_timezone(tz_offset):
    """Test that timezone info is preserved through roundtrip with various timezones"""
    tz = timezone(timedelta(hours=tz_offset))
    dt = datetime(2026, 5, 15, 14, 30, tzinfo=tz)
    task = Task(title="TZ test", due_date=dt)
    restored = Task.from_dict(task.to_dict())
    assert restored.due_date == dt
    assert restored.due_date.tzinfo.utcoffset(None) == tz.utcoffset(None)


# ─── mark_in_progress() tests ──────────────────────────────────────────────

def test_mark_in_progress_valid_transition_pending_to_in_progress():
    """Test valid transition from PENDING to IN_PROGRESS"""
    task = Task(title="Task", status=TaskStatus.PENDING)
    result = task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert result is task  # method chaining


def test_mark_in_progress_idempotent_from_in_progress():
    """Test mark_in_progress is idempotent when already IN_PROGRESS"""
    task = Task(title="Task", status=TaskStatus.IN_PROGRESS)
    result = task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert result is task


def test_mark_in_progress_invalid_from_done():
    """Test mark_in_progress raises ValueError when task is DONE"""
    task = Task(title="Task", status=TaskStatus.DONE)
    with pytest.raises(ValueError, match="Cannot mark a DONE task as IN_PROGRESS"):
        task.mark_in_progress()


def test_mark_in_progress_timezone_correctness():
    """Test mark_in_progress updates updated_at with CEST (UTC+2) timezone"""
    task = Task(title="Task", status=TaskStatus.PENDING)
    before = datetime.now(timezone.utc)
    task.mark_in_progress()
    after = datetime.now(timezone.utc)

    # Verify updated_at has CEST timezone
    assert task.updated_at.tzinfo is not None
    assert task.updated_at.tzinfo.utcoffset(None) == timedelta(hours=2)

    # Verify updated_at is within expected range (allow some tolerance)
    assert before <= task.updated_at.astimezone(timezone.utc) <= after + timedelta(seconds=1)


# ─── mark_done() tests ─────────────────────────────────────────────────────

def test_mark_done_valid_transition_in_progress_to_done():
    """Test valid transition from IN_PROGRESS to DONE"""
    task = Task(title="Task", status=TaskStatus.IN_PROGRESS)
    result = task.mark_done()
    assert task.status == TaskStatus.DONE
    assert result is task  # method chaining


def test_mark_done_invalid_from_pending():
    """Test mark_done raises ValueError when task is PENDING"""
    task = Task(title="Task", status=TaskStatus.PENDING)
    with pytest.raises(ValueError, match="Can only mark IN_PROGRESS tasks as DONE"):
        task.mark_done()


def test_mark_done_invalid_from_done():
    """Test mark_done raises ValueError when task is already DONE"""
    task = Task(title="Task", status=TaskStatus.DONE)
    with pytest.raises(ValueError, match="Can only mark IN_PROGRESS tasks as DONE"):
        task.mark_done()


def test_mark_done_timezone_correctness():
    """Test mark_done updates updated_at with CEST (UTC+2) timezone"""
    task = Task(title="Task", status=TaskStatus.IN_PROGRESS)
    before = datetime.now(timezone.utc)
    task.mark_done()
    after = datetime.now(timezone.utc)

    # Verify updated_at has CEST timezone
    assert task.updated_at.tzinfo is not None
    assert task.updated_at.tzinfo.utcoffset(None) == timedelta(hours=2)

    # Verify updated_at is within expected range
    assert before <= task.updated_at.astimezone(timezone.utc) <= after + timedelta(seconds=1)


# ─── reopen() tests ────────────────────────────────────────────────────────

def test_reopen_valid_transition_done_to_in_progress():
    """Test valid transition from DONE to IN_PROGRESS"""
    task = Task(title="Task", status=TaskStatus.DONE)
    result = task.reopen()
    assert task.status == TaskStatus.IN_PROGRESS
    assert result is task  # method chaining


def test_reopen_invalid_from_pending():
    """Test reopen raises ValueError when task is PENDING"""
    task = Task(title="Task", status=TaskStatus.PENDING)
    with pytest.raises(ValueError, match="Can only reopen DONE tasks"):
        task.reopen()


def test_reopen_invalid_from_in_progress():
    """Test reopen raises ValueError when task is IN_PROGRESS"""
    task = Task(title="Task", status=TaskStatus.IN_PROGRESS)
    with pytest.raises(ValueError, match="Can only reopen DONE tasks"):
        task.reopen()


def test_reopen_timezone_correctness():
    """Test reopen updates updated_at with CEST (UTC+2) timezone"""
    task = Task(title="Task", status=TaskStatus.DONE)
    before = datetime.now(timezone.utc)
    task.reopen()
    after = datetime.now(timezone.utc)

    # Verify updated_at has CEST timezone
    assert task.updated_at.tzinfo is not None
    assert task.updated_at.tzinfo.utcoffset(None) == timedelta(hours=2)

    # Verify updated_at is within expected range
    assert before <= task.updated_at.astimezone(timezone.utc) <= after + timedelta(seconds=1)


# ─── is_completed() tests ──────────────────────────────────────────────────

@pytest.mark.parametrize("status", [TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
def test_is_completed_returns_false(status):
    """Test is_completed returns False for PENDING and IN_PROGRESS"""
    task = Task(title="Task", status=status)
    assert task.is_completed() is False


def test_is_completed_returns_true_for_done():
    """Test is_completed returns True when status is DONE"""
    task = Task(title="Task", status=TaskStatus.DONE)
    assert task.is_completed() is True


# ─── is_pending() tests ────────────────────────────────────────────────────

@pytest.mark.parametrize("status", [TaskStatus.IN_PROGRESS, TaskStatus.DONE])
def test_is_pending_returns_false(status):
    """Test is_pending returns False for IN_PROGRESS and DONE"""
    task = Task(title="Task", status=status)
    assert task.is_pending() is False


def test_is_pending_returns_true_for_pending():
    """Test is_pending returns True when status is PENDING"""
    task = Task(title="Task", status=TaskStatus.PENDING)
    assert task.is_pending() is True


# ─── is_in_progress() tests ────────────────────────────────────────────────

@pytest.mark.parametrize("status", [TaskStatus.PENDING, TaskStatus.DONE])
def test_is_in_progress_returns_false(status):
    """Test is_in_progress returns False for PENDING and DONE"""
    task = Task(title="Task", status=status)
    assert task.is_in_progress() is False


def test_is_in_progress_returns_true_for_in_progress():
    """Test is_in_progress returns True when status is IN_PROGRESS"""
    task = Task(title="Task", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


# ─── is_overdue() tests ────────────────────────────────────────────────────

def test_is_overdue_returns_false_when_due_date_is_none():
    """Test is_overdue returns False when due_date is None"""
    task = Task(title="Task with no deadline")
    assert task.is_overdue() is False


def test_is_overdue_returns_false_with_future_due_date():
    """Test is_overdue returns False when due_date is in the future"""
    # Use CEST timezone and add a large buffer to ensure it's in the future
    future_date = datetime.now(timezone.utc) + timedelta(days=365)
    task = Task(title="Future task", due_date=future_date)
    assert task.is_overdue() is False


def test_is_overdue_returns_true_with_past_due_date():
    """Test is_overdue returns True when due_date is in the past"""
    # Use CEST timezone and subtract time to ensure it's in the past
    past_date = datetime.now(timezone.utc) - timedelta(days=365)
    task = Task(title="Past task", due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_timezone_conversion_utc_to_cest():
    """Test is_overdue handles timezone conversion correctly from UTC to CEST"""
    # Create a datetime in UTC that is 2 hours in the future
    # When converted to CEST, it should be now (same absolute time)
    # Create a datetime explicitly in the past in CEST
    cest_tz = timezone(timedelta(hours=2))
    past_in_cest = datetime.now(cest_tz) - timedelta(hours=1)

    # Convert to UTC for the task
    past_in_utc = past_in_cest.astimezone(timezone.utc)
    task = Task(title="Past task", due_date=past_in_utc)
    assert task.is_overdue() is True


@pytest.mark.parametrize("tz_offset_hours", [0, 1, 2, -5, 12])
def test_is_overdue_handles_various_timezone_offsets(tz_offset_hours):
    """Test is_overdue handles due_date with various timezone offsets"""
    tz = timezone(timedelta(hours=tz_offset_hours))
    # Create a datetime in the past with this timezone
    past_time = datetime(2020, 1, 1, 12, 0, tzinfo=tz)
    task = Task(title="Task", due_date=past_time)
    assert task.is_overdue() is True

    # Create a datetime in the future with this timezone
    future_time = datetime(2099, 1, 1, 12, 0, tzinfo=tz)
    task2 = Task(title="Task", due_date=future_time)
    assert task2.is_overdue() is False
