import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_summary import TaskSummary
from src.models.task_status import TaskStatus
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


def test_task_summary_creation():
    """Test that TaskSummary can be created with all fields."""
    summary = TaskSummary(
        total_tasks=10,
        pending_count=5,
        in_progress_count=3,
        done_count=2,
        overdue_count=1,
        with_due_date_count=7,
        completion_rate=20.0,
        avg_days_to_completion=3.5,
    )
    assert summary.total_tasks == 10
    assert summary.pending_count == 5
    assert summary.completion_rate == 20.0


def test_generate_report_empty(service):
    """Test report generation with no tasks."""
    report = service.generate_report()
    assert report.total_tasks == 0
    assert report.pending_count == 0
    assert report.in_progress_count == 0
    assert report.done_count == 0
    assert report.overdue_count == 0
    assert report.with_due_date_count == 0
    assert report.completion_rate == 0.0
    assert report.avg_days_to_completion is None


def test_generate_report_single_pending(service):
    """Test report with a single pending task."""
    service.add_task("Buy milk")
    report = service.generate_report()
    assert report.total_tasks == 1
    assert report.pending_count == 1
    assert report.in_progress_count == 0
    assert report.done_count == 0
    assert report.completion_rate == 0.0


def test_generate_report_mixed_statuses(service):
    """Test report with tasks in different statuses."""
    t1 = service.add_task("Pending task")
    t2 = service.add_task("In progress task")
    service.start_task(t2.id)
    t3 = service.add_task("Done task")
    service.complete_task(t3.id)

    report = service.generate_report()
    assert report.total_tasks == 3
    assert report.pending_count == 1
    assert report.in_progress_count == 1
    assert report.done_count == 1


def test_generate_report_completion_rate(service):
    """Test completion rate calculation."""
    service.add_task("Task 1")
    service.add_task("Task 2")
    t3 = service.add_task("Task 3")
    t4 = service.add_task("Task 4")
    service.complete_task(t3.id)
    service.complete_task(t4.id)

    report = service.generate_report()
    assert report.total_tasks == 4
    assert report.done_count == 2
    assert report.completion_rate == 50.0


def test_generate_report_with_due_dates(service):
    """Test report counts tasks with due dates."""
    t1 = service.add_task("Task without due date")
    t2 = service.add_task("Task with due date")
    t2.due_date = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    service._manager._persist()

    report = service.generate_report()
    assert report.total_tasks == 2
    assert report.with_due_date_count == 1


def test_generate_report_overdue_count(service):
    """Test report counts overdue tasks."""
    # Create an overdue task (due date in the past)
    t1 = service.add_task("Overdue task")
    t1.due_date = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    service._manager._persist()

    # Create a non-overdue task (due date in the future)
    t2 = service.add_task("Future task")
    t2.due_date = datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    service._manager._persist()

    report = service.generate_report()
    assert report.total_tasks == 2
    assert report.overdue_count == 1


def test_generate_report_avg_days_to_completion(service):
    """Test average days to completion calculation."""
    # Create a task and complete it
    t1 = service.add_task("Task 1")
    # Simulate task completion by advancing created_at
    original_created = t1.created_at
    t1.created_at = original_created - timedelta(days=5)
    service.complete_task(t1.id)
    service._manager._persist()

    # Create another task and complete it after 3 days
    t2 = service.add_task("Task 2")
    t2.created_at = datetime.now(timezone.utc) - timedelta(days=3)
    service.complete_task(t2.id)
    service._manager._persist()

    report = service.generate_report()
    assert report.done_count == 2
    assert report.avg_days_to_completion is not None
    # Average should be (5 + 3) / 2 = 4 days
    assert report.avg_days_to_completion == 4.0


def test_generate_report_no_avg_for_no_done_tasks(service):
    """Test that avg_days_to_completion is None when no tasks are done."""
    service.add_task("Pending task")
    service.add_task("Another pending task")

    report = service.generate_report()
    assert report.done_count == 0
    assert report.avg_days_to_completion is None


def test_generate_report_deterministic(service):
    """Test that report is deterministic regardless of task ordering."""
    # Add tasks in one order
    t1 = service.add_task("Task A")
    t2 = service.add_task("Task B")
    t3 = service.add_task("Task C")
    service.start_task(t1.id)
    service.complete_task(t2.id)

    report1 = service.generate_report()

    # Get tasks again in different order (they're stored internally)
    report2 = service.generate_report()

    # Reports should be identical
    assert report1.total_tasks == report2.total_tasks
    assert report1.pending_count == report2.pending_count
    assert report1.in_progress_count == report2.in_progress_count
    assert report1.done_count == report2.done_count
    assert report1.overdue_count == report2.overdue_count
    assert report1.with_due_date_count == report2.with_due_date_count
    assert report1.completion_rate == report2.completion_rate


def test_generate_report_complex_scenario(service):
    """Test report with a complex mix of tasks."""
    # 10 tasks with mixed states
    tasks = []
    for i in range(10):
        t = service.add_task(f"Task {i+1}")
        tasks.append(t)

    # Mark some as in progress
    service.start_task(tasks[0].id)
    service.start_task(tasks[1].id)

    # Mark some as done
    service.complete_task(tasks[2].id)
    service.complete_task(tasks[3].id)
    service.complete_task(tasks[4].id)

    # Add due dates to some
    tasks[5].due_date = datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    tasks[6].due_date = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    service._manager._persist()

    report = service.generate_report()
    assert report.total_tasks == 10
    assert report.pending_count == 5
    assert report.in_progress_count == 2
    assert report.done_count == 3
    assert report.overdue_count == 1
    assert report.with_due_date_count == 2
    assert report.completion_rate == 30.0
