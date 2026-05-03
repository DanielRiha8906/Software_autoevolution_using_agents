import dataclasses
import pytest
import tempfile
import os
from datetime import datetime, timezone, timedelta

from src.models.task import Task, CEST
from src.models.task_status import TaskStatus
from src.models.task_statistics import TaskStatistics
from src.services.todo_service import TodoService
from src.services.statistics_service import TaskStatisticsService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def empty_service():
    """Create a TodoService with no tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "tasks.json")
        storage = JsonStorage(storage_path)
        yield TodoService(storage)


@pytest.fixture
def service_with_tasks():
    """Create a TodoService with 4 tasks: 1 done, 3 pending, 1 overdue, 2 with due date."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "tasks.json")
        storage = JsonStorage(storage_path)
        service = TodoService(storage)

        # Task 1: DONE, no due date
        task1 = service.add_task("Task 1 - Completed")
        service.complete_task(task1.id)

        # Task 2: PENDING, no due date
        service.add_task("Task 2 - Pending")

        # Task 3: PENDING, past due date (overdue)
        past_date = datetime.now(tz=CEST) - timedelta(hours=1)
        task3 = service.add_task("Task 3 - Overdue")
        # Directly set due_date (bypass validation for testing)
        tasks = service._manager.list_all()
        for t in tasks:
            if t.id == task3.id:
                t.due_date = past_date
                service._manager._persist()
                break

        # Task 4: PENDING, future due date
        future_date = datetime.now(tz=CEST) + timedelta(days=1)
        task4 = service.add_task("Task 4 - Future due")
        tasks = service._manager.list_all()
        for t in tasks:
            if t.id == task4.id:
                t.due_date = future_date
                service._manager._persist()
                break

        yield service


def test_report_is_dataclass(empty_service):
    """TaskStatistics must be a dataclass."""
    stats_svc = TaskStatisticsService(empty_service)
    report = stats_svc.compute()
    assert dataclasses.is_dataclass(report)


def test_total_count(service_with_tasks):
    """Total count should be 4."""
    stats_svc = TaskStatisticsService(service_with_tasks)
    assert stats_svc.compute().total == 4


def test_count_per_status(service_with_tasks):
    """Count per status: 1 DONE, 3 PENDING."""
    stats_svc = TaskStatisticsService(service_with_tasks)
    report = stats_svc.compute()
    assert report.count_per_status[TaskStatus.DONE] == 1
    assert report.count_per_status[TaskStatus.PENDING] == 3
    assert report.count_per_status[TaskStatus.IN_PROGRESS] == 0


def test_overdue_count(service_with_tasks):
    """Overdue count should be 1."""
    stats_svc = TaskStatisticsService(service_with_tasks)
    assert stats_svc.compute().overdue_count == 1


def test_with_due_date_count(service_with_tasks):
    """With due date count should be 2."""
    stats_svc = TaskStatisticsService(service_with_tasks)
    assert stats_svc.compute().with_due_date_count == 2


def test_completion_rate(service_with_tasks):
    """Completion rate should be 25% (1 done / 4 total)."""
    stats_svc = TaskStatisticsService(service_with_tasks)
    report = stats_svc.compute()
    assert report.completion_rate == pytest.approx(25.0)


def test_empty_task_list_statistics(empty_service):
    """Empty task list should return total=0, completion_rate=0, overdue_count=0."""
    stats_svc = TaskStatisticsService(empty_service)
    report = stats_svc.compute()
    assert report.total == 0
    assert report.completion_rate == 0.0
    assert report.overdue_count == 0
    assert report.count_per_status[TaskStatus.DONE] == 0
    assert report.count_per_status[TaskStatus.PENDING] == 0
    assert report.count_per_status[TaskStatus.IN_PROGRESS] == 0


def test_output_is_deterministic(service_with_tasks):
    """Calling compute() twice should return the same values."""
    stats_svc = TaskStatisticsService(service_with_tasks)
    report1 = stats_svc.compute()
    report2 = stats_svc.compute()

    assert report1.total == report2.total
    assert report1.count_per_status == report2.count_per_status
    assert report1.overdue_count == report2.overdue_count
    assert report1.with_due_date_count == report2.with_due_date_count
    assert report1.completion_rate == report2.completion_rate


def test_all_status_values_present_in_count_per_status(empty_service):
    """count_per_status dict must include all TaskStatus enum values."""
    stats_svc = TaskStatisticsService(empty_service)
    report = stats_svc.compute()
    assert TaskStatus.PENDING in report.count_per_status
    assert TaskStatus.IN_PROGRESS in report.count_per_status
    assert TaskStatus.DONE in report.count_per_status


def test_completion_rate_is_float():
    """completion_rate must be a float, not an int."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "tasks.json")
        storage = JsonStorage(storage_path)
        service = TodoService(storage)
        task = service.add_task("Test")
        service.complete_task(task.id)

        stats_svc = TaskStatisticsService(service)
        report = stats_svc.compute()
        assert isinstance(report.completion_rate, float)
        assert report.completion_rate == pytest.approx(100.0)
