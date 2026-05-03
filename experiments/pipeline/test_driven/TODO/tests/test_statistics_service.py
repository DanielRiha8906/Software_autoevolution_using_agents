import dataclasses
import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_status import TaskStatus
from src.services.todo_service import TodoService
from src.services.statistics_service import TaskStatisticsService
from src.storage.json_storage import JsonStorage

CEST = timezone(timedelta(hours=2))
PAST = datetime(2020, 1, 1, tzinfo=CEST)
FUTURE = datetime(2099, 1, 1, tzinfo=CEST)


@pytest.fixture
def stats_svc(tmp_path):
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    todo.add_task("Pending")
    t2 = todo.add_task("Done task")
    todo.complete_task(t2.id)
    todo.add_task("Overdue", due_date=PAST)
    todo.add_task("Future", due_date=FUTURE)
    return TaskStatisticsService(todo)


def test_report_is_dataclass(stats_svc):
    assert dataclasses.is_dataclass(stats_svc.compute())


def test_total_count(stats_svc):
    assert stats_svc.compute().total == 4


def test_count_per_status(stats_svc):
    report = stats_svc.compute()
    assert report.count_per_status[TaskStatus.DONE] == 1
    assert report.count_per_status[TaskStatus.PENDING] == 3


def test_overdue_count(stats_svc):
    assert stats_svc.compute().overdue_count == 1


def test_with_due_date_count(stats_svc):
    assert stats_svc.compute().with_due_date_count == 2


def test_completion_rate(stats_svc):
    assert stats_svc.compute().completion_rate == pytest.approx(25.0)

def test_empty_task_list_statistics(tmp_path):
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    report = TaskStatisticsService(todo).compute()
    assert report.total == 0
    assert report.completion_rate == 0
    assert report.overdue_count == 0

def test_output_is_deterministic(stats_svc):
    assert stats_svc.compute().total == stats_svc.compute().total


# Additional comprehensive tests

def test_all_tasks_done(tmp_path):
    """Test when all tasks are marked as done."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    t1 = todo.add_task("Task 1")
    t2 = todo.add_task("Task 2")
    t3 = todo.add_task("Task 3")
    todo.complete_task(t1.id)
    todo.complete_task(t2.id)
    todo.complete_task(t3.id)

    report = TaskStatisticsService(todo).compute()
    assert report.total == 3
    assert report.count_per_status[TaskStatus.DONE] == 3
    assert report.count_per_status[TaskStatus.PENDING] == 0
    assert report.count_per_status[TaskStatus.IN_PROGRESS] == 0
    assert report.completion_rate == pytest.approx(100.0)


def test_all_tasks_in_progress(tmp_path):
    """Test when all tasks are in progress."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    t1 = todo.add_task("Task 1")
    t2 = todo.add_task("Task 2")
    todo.start_task(t1.id)
    todo.start_task(t2.id)

    report = TaskStatisticsService(todo).compute()
    assert report.total == 2
    assert report.count_per_status[TaskStatus.IN_PROGRESS] == 2
    assert report.count_per_status[TaskStatus.PENDING] == 0
    assert report.count_per_status[TaskStatus.DONE] == 0
    assert report.completion_rate == pytest.approx(0.0)


def test_mixed_due_dates(tmp_path):
    """Test tasks with various due date combinations."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    todo.add_task("No due date 1")
    todo.add_task("With past date", due_date=PAST)
    todo.add_task("No due date 2")
    todo.add_task("With future date", due_date=FUTURE)
    todo.add_task("With past date 2", due_date=PAST)

    report = TaskStatisticsService(todo).compute()
    assert report.total == 5
    assert report.with_due_date_count == 3
    assert report.overdue_count == 2


def test_completion_rate_one_third(tmp_path):
    """Test completion rate with one task done out of three."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    t1 = todo.add_task("Task 1")
    todo.add_task("Task 2")
    todo.add_task("Task 3")
    todo.complete_task(t1.id)

    report = TaskStatisticsService(todo).compute()
    assert report.completion_rate == pytest.approx(33.33, rel=0.01)


def test_completion_rate_two_thirds(tmp_path):
    """Test completion rate with two tasks done out of three."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    t1 = todo.add_task("Task 1")
    t2 = todo.add_task("Task 2")
    todo.add_task("Task 3")
    todo.complete_task(t1.id)
    todo.complete_task(t2.id)

    report = TaskStatisticsService(todo).compute()
    assert report.completion_rate == pytest.approx(66.67, rel=0.01)


def test_count_per_status_keys_always_present(tmp_path):
    """Ensure all TaskStatus keys are present in count_per_status dict."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    todo.add_task("Task 1")
    todo.add_task("Task 2")

    report = TaskStatisticsService(todo).compute()
    assert TaskStatus.PENDING in report.count_per_status
    assert TaskStatus.IN_PROGRESS in report.count_per_status
    assert TaskStatus.DONE in report.count_per_status


def test_single_task_pending(tmp_path):
    """Test with a single pending task."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    todo.add_task("Only task")

    report = TaskStatisticsService(todo).compute()
    assert report.total == 1
    assert report.count_per_status[TaskStatus.PENDING] == 1
    assert report.completion_rate == pytest.approx(0.0)
    assert report.overdue_count == 0
    assert report.with_due_date_count == 0


def test_single_task_done(tmp_path):
    """Test with a single done task."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    t = todo.add_task("Only task")
    todo.complete_task(t.id)

    report = TaskStatisticsService(todo).compute()
    assert report.total == 1
    assert report.count_per_status[TaskStatus.DONE] == 1
    assert report.completion_rate == pytest.approx(100.0)


def test_statistics_consistency_across_calls(tmp_path):
    """Verify statistics remain consistent across multiple calls."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    t1 = todo.add_task("Task 1")
    todo.add_task("Task 2", due_date=PAST)
    todo.complete_task(t1.id)

    stats_svc = TaskStatisticsService(todo)
    report1 = stats_svc.compute()
    report2 = stats_svc.compute()
    report3 = stats_svc.compute()

    assert report1.total == report2.total == report3.total
    assert report1.completion_rate == report2.completion_rate == report3.completion_rate
    assert report1.overdue_count == report2.overdue_count == report3.overdue_count
    assert report1.with_due_date_count == report2.with_due_date_count == report3.with_due_date_count


def test_completion_rate_precision(tmp_path):
    """Test completion rate is computed as floating point."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    todo.add_task("Task 1")
    t2 = todo.add_task("Task 2")
    todo.add_task("Task 3")
    todo.complete_task(t2.id)

    report = TaskStatisticsService(todo).compute()
    # 1 done out of 3 = 33.333...%
    assert isinstance(report.completion_rate, float)
    assert 33.0 < report.completion_rate < 34.0


def test_sum_of_counts_equals_total(tmp_path):
    """Verify sum of count_per_status equals total count."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    todo.add_task("Task 1")
    t2 = todo.add_task("Task 2")
    t3 = todo.add_task("Task 3")
    todo.start_task(t2.id)
    todo.complete_task(t3.id)

    report = TaskStatisticsService(todo).compute()
    status_sum = (
        report.count_per_status[TaskStatus.PENDING] +
        report.count_per_status[TaskStatus.IN_PROGRESS] +
        report.count_per_status[TaskStatus.DONE]
    )
    assert status_sum == report.total


def test_statistics_with_all_statuses(tmp_path):
    """Test with tasks in all three status states."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    t1 = todo.add_task("Pending")
    t2 = todo.add_task("In Progress")
    t3 = todo.add_task("Done")

    todo.start_task(t2.id)
    todo.complete_task(t3.id)

    report = TaskStatisticsService(todo).compute()
    assert report.total == 3
    assert report.count_per_status[TaskStatus.PENDING] == 1
    assert report.count_per_status[TaskStatus.IN_PROGRESS] == 1
    assert report.count_per_status[TaskStatus.DONE] == 1
    assert report.completion_rate == pytest.approx(33.33, rel=0.01)


def test_large_task_count(tmp_path):
    """Test with a large number of tasks."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    task_ids = []
    for i in range(100):
        t = todo.add_task(f"Task {i}")
        task_ids.append(t.id)

    # Complete 25 tasks
    for i in range(25):
        todo.complete_task(task_ids[i])

    report = TaskStatisticsService(todo).compute()
    assert report.total == 100
    assert report.count_per_status[TaskStatus.DONE] == 25
    assert report.count_per_status[TaskStatus.PENDING] == 75
    assert report.completion_rate == pytest.approx(25.0)


def test_overdue_task_not_done_still_overdue(tmp_path):
    """Verify that overdue count includes overdue tasks regardless of status."""
    todo = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    t1 = todo.add_task("Overdue pending", due_date=PAST)
    t2 = todo.add_task("Overdue in progress", due_date=PAST)

    todo.start_task(t2.id)

    report = TaskStatisticsService(todo).compute()
    assert report.overdue_count == 2
    assert report.count_per_status[TaskStatus.PENDING] == 1
    assert report.count_per_status[TaskStatus.IN_PROGRESS] == 1
