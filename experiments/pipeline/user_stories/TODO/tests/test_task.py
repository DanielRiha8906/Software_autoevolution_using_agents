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


# ─── Group A: mark_in_progress() tests ──────────────────────────────────────

@pytest.fixture
def pending_task():
    """Fixture for a task in PENDING status"""
    return Task(title="Example task", status=TaskStatus.PENDING)


@pytest.fixture
def in_progress_task():
    """Fixture for a task in IN_PROGRESS status"""
    return Task(title="Example task", status=TaskStatus.IN_PROGRESS)


@pytest.fixture
def done_task():
    """Fixture for a task in DONE status"""
    return Task(title="Example task", status=TaskStatus.DONE)


def test_mark_in_progress_valid_transition(pending_task):
    """A1: mark_in_progress() transitions PENDING -> IN_PROGRESS"""
    original_updated_at = pending_task.updated_at

    result = pending_task.mark_in_progress()

    assert result is pending_task  # Returns self
    assert pending_task.is_in_progress()
    assert pending_task.status == TaskStatus.IN_PROGRESS
    assert pending_task.updated_at > original_updated_at


def test_mark_in_progress_invalid_from_in_progress(in_progress_task):
    """A2: mark_in_progress() raises ValueError from IN_PROGRESS"""
    with pytest.raises(ValueError, match="Cannot mark in_progress: task is already in in_progress"):
        in_progress_task.mark_in_progress()

    assert in_progress_task.is_in_progress()  # Status unchanged


def test_mark_in_progress_invalid_from_done(done_task):
    """A3: mark_in_progress() raises ValueError from DONE"""
    with pytest.raises(ValueError, match="Cannot mark in_progress: task is already in done"):
        done_task.mark_in_progress()

    assert done_task.is_completed()  # Status unchanged


# ─── Group B: mark_done() tests ─────────────────────────────────────────────

def test_mark_done_valid_transition(in_progress_task):
    """B1: mark_done() transitions IN_PROGRESS -> DONE"""
    original_updated_at = in_progress_task.updated_at

    result = in_progress_task.mark_done()

    assert result is in_progress_task  # Returns self
    assert in_progress_task.is_completed()
    assert in_progress_task.status == TaskStatus.DONE
    assert in_progress_task.updated_at > original_updated_at


def test_mark_done_invalid_from_pending(pending_task):
    """B2: mark_done() raises ValueError from PENDING"""
    with pytest.raises(ValueError, match="Cannot mark done: task is pending"):
        pending_task.mark_done()

    assert pending_task.is_pending()  # Status unchanged


def test_mark_done_invalid_from_done(done_task):
    """B3: mark_done() raises ValueError from DONE"""
    with pytest.raises(ValueError, match="Cannot mark done: task is done"):
        done_task.mark_done()

    assert done_task.is_completed()  # Status unchanged


# ─── Group C: reopen() tests ────────────────────────────────────────────────

def test_reopen_valid_transition(done_task):
    """C1: reopen() transitions DONE -> IN_PROGRESS"""
    original_updated_at = done_task.updated_at

    result = done_task.reopen()

    assert result is done_task  # Returns self
    assert done_task.is_in_progress()
    assert done_task.status == TaskStatus.IN_PROGRESS
    assert done_task.updated_at > original_updated_at


def test_reopen_invalid_from_pending(pending_task):
    """C2: reopen() raises ValueError from PENDING"""
    with pytest.raises(ValueError, match="Cannot reopen: task is pending"):
        pending_task.reopen()

    assert pending_task.is_pending()  # Status unchanged


def test_reopen_invalid_from_in_progress(in_progress_task):
    """C3: reopen() raises ValueError from IN_PROGRESS"""
    with pytest.raises(ValueError, match="Cannot reopen: task is in_progress"):
        in_progress_task.reopen()

    assert in_progress_task.is_in_progress()  # Status unchanged


# ─── Group D: updated_at timestamp tests ───────────────────────────────────

def test_mark_in_progress_updates_timestamp(pending_task):
    """D1: mark_in_progress() updates updated_at to current UTC time"""
    before = datetime.now(timezone.utc)
    pending_task.mark_in_progress()
    after = datetime.now(timezone.utc)

    assert before <= pending_task.updated_at <= after


def test_mark_done_updates_timestamp(in_progress_task):
    """D2: mark_done() updates updated_at to current UTC time"""
    before = datetime.now(timezone.utc)
    in_progress_task.mark_done()
    after = datetime.now(timezone.utc)

    assert before <= in_progress_task.updated_at <= after


def test_reopen_updates_timestamp(done_task):
    """D3: reopen() updates updated_at to current UTC time"""
    before = datetime.now(timezone.utc)
    done_task.reopen()
    after = datetime.now(timezone.utc)

    assert before <= done_task.updated_at <= after


# ─── Group E: is_pending() tests ────────────────────────────────────────────

def test_is_pending_true_when_pending():
    """E1: is_pending() returns True for PENDING status"""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True


def test_is_pending_false_when_in_progress():
    """E2: is_pending() returns False for IN_PROGRESS status"""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_pending() is False


def test_is_pending_false_when_done():
    """E3: is_pending() returns False for DONE status"""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_pending() is False


# ─── Group F: is_in_progress() tests ────────────────────────────────────────

def test_is_in_progress_true_when_in_progress():
    """F1: is_in_progress() returns True for IN_PROGRESS status"""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


def test_is_in_progress_false_when_pending():
    """F2: is_in_progress() returns False for PENDING status"""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_in_progress() is False


def test_is_in_progress_false_when_done():
    """F3: is_in_progress() returns False for DONE status"""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_in_progress() is False


# ─── Group G: is_completed() tests ──────────────────────────────────────────

def test_is_completed_true_when_done():
    """G1: is_completed() returns True for DONE status"""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_false_when_pending():
    """G2: is_completed() returns False for PENDING status"""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_completed() is False


def test_is_completed_false_when_in_progress():
    """G3: is_completed() returns False for IN_PROGRESS status"""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_completed() is False


# ─── Group H: is_overdue() tests ────────────────────────────────────────────

def test_is_overdue_false_when_no_due_date():
    """H1: is_overdue() returns False when due_date is None"""
    task = Task(title="Test", status=TaskStatus.PENDING, due_date=None)
    assert task.is_overdue() is False


def test_is_overdue_false_when_future_date_and_pending():
    """H2: is_overdue() returns False when due_date is in future and status is PENDING"""
    future_date = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.PENDING, due_date=future_date)
    assert task.is_overdue() is False


def test_is_overdue_true_when_past_date_and_pending():
    """H3: is_overdue() returns True when due_date is in past and status is PENDING"""
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.PENDING, due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_true_when_past_date_and_in_progress():
    """H4: is_overdue() returns True when due_date is in past and status is IN_PROGRESS"""
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS, due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_false_when_past_date_and_done():
    """H5: is_overdue() returns False when status is DONE (regardless of due_date)"""
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.DONE, due_date=past_date)
    assert task.is_overdue() is False


def test_is_overdue_false_when_future_date_and_done():
    """H6: is_overdue() returns False when status is DONE even with future due_date"""
    future_date = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(title="Test", status=TaskStatus.DONE, due_date=future_date)
    assert task.is_overdue() is False


# ─── Group I: Integration with TaskManager ─────────────────────────────────

def test_task_manager_set_status_pending_to_in_progress(tmp_path):
    """I1: TaskManager.set_status() calls mark_in_progress() and persists"""
    from src.services.task_manager import TaskManager
    from src.storage.json_storage import JsonStorage

    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    task = manager.add("Test task")

    result = manager.set_status(task.id, TaskStatus.IN_PROGRESS)

    assert result.is_in_progress()
    # Verify persistence by reloading
    reloaded = manager.get(task.id)
    assert reloaded.is_in_progress()


def test_task_manager_set_status_in_progress_to_done(tmp_path):
    """I2: TaskManager.set_status() calls mark_done() and persists"""
    from src.services.task_manager import TaskManager
    from src.storage.json_storage import JsonStorage

    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    task = manager.add("Test task")
    manager.set_status(task.id, TaskStatus.IN_PROGRESS)

    result = manager.set_status(task.id, TaskStatus.DONE)

    assert result.is_completed()
    # Verify persistence
    reloaded = manager.get(task.id)
    assert reloaded.is_completed()


def test_task_manager_set_status_done_to_in_progress_via_reopen(tmp_path):
    """I3: TaskManager.set_status() calls reopen() for DONE->IN_PROGRESS"""
    from src.services.task_manager import TaskManager
    from src.storage.json_storage import JsonStorage

    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    task = manager.add("Test task")
    manager.set_status(task.id, TaskStatus.IN_PROGRESS)
    manager.set_status(task.id, TaskStatus.DONE)

    result = manager.set_status(task.id, TaskStatus.IN_PROGRESS)

    assert result.is_in_progress()
    # Verify persistence
    reloaded = manager.get(task.id)
    assert reloaded.is_in_progress()


def test_task_manager_set_status_invalid_transition_raises(tmp_path):
    """I4: TaskManager.set_status() raises ValueError for invalid transitions"""
    from src.services.task_manager import TaskManager
    from src.storage.json_storage import JsonStorage

    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    task = manager.add("Test task")

    # Try to transition PENDING -> DONE (invalid)
    with pytest.raises(ValueError, match="Cannot transition"):
        manager.set_status(task.id, TaskStatus.DONE)


def test_task_manager_set_status_already_in_status_raises(tmp_path):
    """I5: TaskManager.set_status() raises ValueError when already in target status"""
    from src.services.task_manager import TaskManager
    from src.storage.json_storage import JsonStorage

    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    task = manager.add("Test task")

    # Try to set PENDING when already PENDING
    with pytest.raises(ValueError, match="Task is already pending"):
        manager.set_status(task.id, TaskStatus.PENDING)


# ─── Group J: Integration with TodoService ─────────────────────────────────

def test_todo_service_start_task(tmp_path):
    """J1: TodoService.start_task() transitions PENDING -> IN_PROGRESS"""
    from src.services.todo_service import TodoService
    from src.storage.json_storage import JsonStorage

    storage = JsonStorage(str(tmp_path / "tasks.json"))
    service = TodoService(storage)
    task = service.add_task("Test task")

    result = service.start_task(task.id)

    assert result.is_in_progress()


def test_todo_service_complete_task(tmp_path):
    """J2: TodoService.complete_task() transitions to DONE"""
    from src.services.todo_service import TodoService
    from src.storage.json_storage import JsonStorage

    storage = JsonStorage(str(tmp_path / "tasks.json"))
    service = TodoService(storage)
    task = service.add_task("Test task")
    service.start_task(task.id)

    result = service.complete_task(task.id)

    assert result.is_completed()


def test_todo_service_reopen_task_uses_in_progress(tmp_path):
    """J3: TodoService.reopen_task() transitions DONE -> IN_PROGRESS (not PENDING)"""
    from src.services.todo_service import TodoService
    from src.storage.json_storage import JsonStorage

    storage = JsonStorage(str(tmp_path / "tasks.json"))
    service = TodoService(storage)
    task = service.add_task("Test task")
    service.start_task(task.id)
    service.complete_task(task.id)

    result = service.reopen_task(task.id)

    # The crucial assertion: reopen should set to IN_PROGRESS, not PENDING
    assert result.is_in_progress()
    assert not result.is_pending()


# ─── Group K: Error handling and message verification ──────────────────────

def test_mark_in_progress_error_message_contains_status(in_progress_task):
    """K1: mark_in_progress() error message includes current status"""
    try:
        in_progress_task.mark_in_progress()
        pytest.fail("Should have raised ValueError")
    except ValueError as e:
        assert "in_progress" in str(e)
        assert "Cannot mark in_progress" in str(e)


def test_mark_done_error_message_contains_status(pending_task):
    """K2: mark_done() error message includes current status"""
    try:
        pending_task.mark_done()
        pytest.fail("Should have raised ValueError")
    except ValueError as e:
        assert "pending" in str(e)
        assert "Cannot mark done" in str(e)


def test_reopen_error_message_contains_status(pending_task):
    """K3: reopen() error message includes current status"""
    try:
        pending_task.reopen()
        pytest.fail("Should have raised ValueError")
    except ValueError as e:
        assert "pending" in str(e)
        assert "Cannot reopen" in str(e)


# ─── Group L: Method chaining and return value tests ──────────────────────

def test_mark_in_progress_returns_self(pending_task):
    """L1: mark_in_progress() returns self for method chaining"""
    result = pending_task.mark_in_progress()
    assert result is pending_task


def test_mark_done_returns_self(in_progress_task):
    """L2: mark_done() returns self for method chaining"""
    result = in_progress_task.mark_done()
    assert result is in_progress_task


def test_reopen_returns_self(done_task):
    """L3: reopen() returns self for method chaining"""
    result = done_task.reopen()
    assert result is done_task


def test_method_chaining_multiple_transitions():
    """L4: Multiple method calls can be chained together"""
    task = Task(title="Test")
    result = task.mark_in_progress().mark_done()
    assert result is task
    assert task.is_completed()
