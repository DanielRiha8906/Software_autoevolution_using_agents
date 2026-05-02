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
