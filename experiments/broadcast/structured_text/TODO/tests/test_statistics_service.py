import pytest
from datetime import datetime, timezone, timedelta

from src.models.task_statistics import TaskStatistics
from src.models.task_status import TaskStatus
from src.services.statistics_service import StatisticsService
from src.services.task_manager import TaskManager
from src.storage.json_storage import JsonStorage


@pytest.fixture
def stats_service(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return StatisticsService(storage)


def test_empty_task_list(stats_service):
    """Statistics for empty task list."""
    stats = stats_service.compute_statistics()
    assert stats.total_task_count == 0
    assert stats.pending_count == 0
    assert stats.in_progress_count == 0
    assert stats.done_count == 0
    assert stats.overdue_count == 0
    assert stats.tasks_with_due_date_count == 0
    assert stats.completion_rate == 0.0


def test_all_pending_tasks(tmp_path):
    """Statistics with all pending tasks."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    manager.add("Task 1")
    manager.add("Task 2")
    manager.add("Task 3")

    stats_service = StatisticsService(storage)
    stats = stats_service.compute_statistics()
    assert stats.total_task_count == 3
    assert stats.pending_count == 3
    assert stats.in_progress_count == 0
    assert stats.done_count == 0
    assert stats.completion_rate == 0.0


def test_mixed_status_tasks(tmp_path):
    """Statistics with mixed task statuses."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    t1 = manager.add("Pending")
    t2 = manager.add("In Progress")
    t3 = manager.add("Done")

    manager.set_status(t2.id, TaskStatus.IN_PROGRESS)
    manager.set_status(t3.id, TaskStatus.DONE)

    stats_service = StatisticsService(storage)
    stats = stats_service.compute_statistics()
    assert stats.total_task_count == 3
    assert stats.pending_count == 1
    assert stats.in_progress_count == 1
    assert stats.done_count == 1
    assert stats.completion_rate == 1.0 / 3


def test_completion_rate(tmp_path):
    """Test completion rate calculation."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    t1 = manager.add("Task 1")
    t2 = manager.add("Task 2")
    t3 = manager.add("Task 3")
    t4 = manager.add("Task 4")

    manager.set_status(t1.id, TaskStatus.DONE)
    manager.set_status(t2.id, TaskStatus.DONE)

    stats_service = StatisticsService(storage)
    stats = stats_service.compute_statistics()
    assert stats.total_task_count == 4
    assert stats.done_count == 2
    assert stats.completion_rate == 0.5


def test_tasks_with_due_date(tmp_path):
    """Count tasks with due dates."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=1)

    manager.add("No due date")
    manager.add("With due date", due_date=future)
    manager.add("Another without due date")
    manager.add("Another with due date", due_date=future)

    stats_service = StatisticsService(storage)
    stats = stats_service.compute_statistics()
    assert stats.total_task_count == 4
    assert stats.tasks_with_due_date_count == 2


def test_overdue_tasks(tmp_path):
    """Count overdue tasks."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=1)
    future = now + timedelta(days=1)

    manager.add("Overdue task", due_date=past)
    manager.add("On time task", due_date=future)
    manager.add("No due date")
    manager.add("Another overdue", due_date=past)

    stats_service = StatisticsService(storage)
    stats = stats_service.compute_statistics()
    assert stats.total_task_count == 4
    assert stats.overdue_count == 2


def test_completion_rate_100_percent(tmp_path):
    """Test 100% completion rate."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    t1 = manager.add("Task 1")
    t2 = manager.add("Task 2")

    manager.set_status(t1.id, TaskStatus.DONE)
    manager.set_status(t2.id, TaskStatus.DONE)

    stats_service = StatisticsService(storage)
    stats = stats_service.compute_statistics()
    assert stats.completion_rate == 1.0


def test_deterministic_output(tmp_path):
    """Statistics output should be deterministic regardless of task ordering."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)

    # Add tasks in one order
    tasks = []
    for i in range(5):
        tasks.append(manager.add(f"Task {i}"))

    manager.set_status(tasks[0].id, TaskStatus.DONE)
    manager.set_status(tasks[1].id, TaskStatus.IN_PROGRESS)

    stats_service1 = StatisticsService(storage)
    stats1 = stats_service1.compute_statistics()

    # Create another service instance (simulating a fresh load)
    stats_service2 = StatisticsService(storage)
    stats2 = stats_service2.compute_statistics()

    # Both should have identical results
    assert stats1.total_task_count == stats2.total_task_count
    assert stats1.pending_count == stats2.pending_count
    assert stats1.in_progress_count == stats2.in_progress_count
    assert stats1.done_count == stats2.done_count
    assert stats1.completion_rate == stats2.completion_rate


def test_completion_rate_precision(tmp_path):
    """Test completion rate is calculated correctly with various ratios."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)

    # 1 out of 3 = 0.333...
    for i in range(3):
        task = manager.add(f"Task {i}")
        if i == 0:
            manager.set_status(task.id, TaskStatus.DONE)

    stats_service = StatisticsService(storage)
    stats = stats_service.compute_statistics()
    assert abs(stats.completion_rate - (1.0 / 3.0)) < 0.0001


@pytest.fixture
def task_statistics_dataclass():
    """Test TaskStatistics dataclass instantiation and validation."""
    stats = TaskStatistics(
        total_task_count=10,
        pending_count=3,
        in_progress_count=2,
        done_count=5,
        overdue_count=1,
        tasks_with_due_date_count=4,
        completion_rate=0.5,
    )
    return stats


def test_task_statistics_creation(task_statistics_dataclass):
    """Test creating a valid TaskStatistics instance."""
    assert task_statistics_dataclass.total_task_count == 10
    assert task_statistics_dataclass.pending_count == 3
    assert task_statistics_dataclass.in_progress_count == 2
    assert task_statistics_dataclass.done_count == 5
    assert task_statistics_dataclass.overdue_count == 1
    assert task_statistics_dataclass.tasks_with_due_date_count == 4
    assert task_statistics_dataclass.completion_rate == 0.5


def test_task_statistics_negative_values():
    """Test TaskStatistics rejects negative counts."""
    with pytest.raises(ValueError, match="total_task_count cannot be negative"):
        TaskStatistics(
            total_task_count=-1,
            pending_count=0,
            in_progress_count=0,
            done_count=0,
            overdue_count=0,
            tasks_with_due_date_count=0,
            completion_rate=0.0,
        )

    with pytest.raises(ValueError, match="pending_count cannot be negative"):
        TaskStatistics(
            total_task_count=1,
            pending_count=-1,
            in_progress_count=0,
            done_count=0,
            overdue_count=0,
            tasks_with_due_date_count=0,
            completion_rate=0.0,
        )


def test_task_statistics_invalid_completion_rate():
    """Test TaskStatistics rejects invalid completion rates."""
    with pytest.raises(ValueError, match="completion_rate must be between 0.0 and 1.0"):
        TaskStatistics(
            total_task_count=10,
            pending_count=3,
            in_progress_count=2,
            done_count=5,
            overdue_count=0,
            tasks_with_due_date_count=0,
            completion_rate=1.5,
        )

    with pytest.raises(ValueError, match="completion_rate must be between 0.0 and 1.0"):
        TaskStatistics(
            total_task_count=10,
            pending_count=3,
            in_progress_count=2,
            done_count=5,
            overdue_count=0,
            tasks_with_due_date_count=0,
            completion_rate=-0.1,
        )
