"""Tests for filtering functionality (due date range, overdue status)."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.models.task_status import TaskStatus
from src.models.filter_options import FilterOptions
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage

CEST = ZoneInfo("Europe/Paris")


@pytest.fixture
def service(tmp_path):
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


class TestFilterOptions:
    """Test FilterOptions dataclass."""

    def test_filter_options_status_only(self):
        opts = FilterOptions(status=TaskStatus.PENDING)
        assert opts.status == TaskStatus.PENDING
        assert opts.due_before is None
        assert opts.due_after is None
        assert opts.overdue_only is False

    def test_filter_options_due_before(self):
        now = datetime.now(CEST)
        opts = FilterOptions(due_before=now)
        assert opts.due_before == now

    def test_filter_options_due_after(self):
        now = datetime.now(CEST)
        opts = FilterOptions(due_after=now)
        assert opts.due_after == now

    def test_filter_options_overdue_only(self):
        opts = FilterOptions(overdue_only=True)
        assert opts.overdue_only is True

    def test_filter_options_rejects_naive_due_before(self):
        naive_dt = datetime.now()
        with pytest.raises(ValueError, match="timezone-aware"):
            FilterOptions(due_before=naive_dt)

    def test_filter_options_rejects_naive_due_after(self):
        naive_dt = datetime.now()
        with pytest.raises(ValueError, match="timezone-aware"):
            FilterOptions(due_after=naive_dt)

    def test_filter_options_rejects_non_datetime_due_before(self):
        with pytest.raises(ValueError, match="due_before must be a datetime"):
            FilterOptions(due_before="2024-01-01")

    def test_filter_options_rejects_non_datetime_due_after(self):
        with pytest.raises(ValueError, match="due_after must be a datetime"):
            FilterOptions(due_after="2024-01-01")


class TestListTasksWithDueDateFiltering:
    """Test list_tasks with due date filtering."""

    def test_list_tasks_due_before(self, service):
        """Filter tasks with due date before a given datetime."""
        # Create a task due in the past
        task_past = service.add_task("Past task")
        past_date = datetime.now(CEST) - timedelta(days=1)
        task_past.due_date = past_date
        service._manager._persist()

        # Create a task due in the future
        task_future = service.add_task("Future task")
        future_date = datetime.now(CEST) + timedelta(days=1)
        task_future.due_date = future_date
        service._manager._persist()

        # Create a task with no due date
        task_no_date = service.add_task("No date task")

        # Filter tasks due before now
        cutoff = datetime.now(CEST)
        results = service.list_tasks(due_before=cutoff)

        # Should only include the past task (tasks without due dates are excluded)
        assert len(results) == 1
        assert results[0].id == task_past.id

    def test_list_tasks_due_after(self, service):
        """Filter tasks with due date after a given datetime."""
        # Create a task due in the past
        task_past = service.add_task("Past task")
        past_date = datetime.now(CEST) - timedelta(days=1)
        task_past.due_date = past_date
        service._manager._persist()

        # Create a task due in the future
        task_future = service.add_task("Future task")
        future_date = datetime.now(CEST) + timedelta(days=1)
        task_future.due_date = future_date
        service._manager._persist()

        # Create a task with no due date
        task_no_date = service.add_task("No date task")

        # Filter tasks due after now
        cutoff = datetime.now(CEST)
        results = service.list_tasks(due_after=cutoff)

        # Should only include the future task
        assert len(results) == 1
        assert results[0].id == task_future.id

    def test_list_tasks_due_between(self, service):
        """Filter tasks due between two dates."""
        # Create tasks with various due dates
        task1 = service.add_task("Task 1")
        task1.due_date = datetime.now(CEST) - timedelta(days=10)
        service._manager._persist()

        task2 = service.add_task("Task 2")
        task2.due_date = datetime.now(CEST) - timedelta(days=5)
        service._manager._persist()

        task3 = service.add_task("Task 3")
        task3.due_date = datetime.now(CEST) + timedelta(days=5)
        service._manager._persist()

        # Filter between -6 and +1 days
        before = datetime.now(CEST) + timedelta(days=1)
        after = datetime.now(CEST) - timedelta(days=6)
        results = service.list_tasks(due_after=after, due_before=before)

        # Should only include task2
        assert len(results) == 1
        assert results[0].id == task2.id

    def test_list_tasks_due_filters_exclude_no_due_date(self, service):
        """Tasks without due date are excluded when filtering by due date."""
        task_no_date = service.add_task("No date")
        task_with_date = service.add_task("With date")
        task_with_date.due_date = datetime.now(CEST)
        service._manager._persist()

        # Filter by due before future date
        future = datetime.now(CEST) + timedelta(days=1)
        results = service.list_tasks(due_before=future)

        # Should only include the task with a due date
        assert len(results) == 1
        assert results[0].id == task_with_date.id


class TestListTasksWithOverdueFiltering:
    """Test list_tasks with overdue status filtering."""

    def test_list_tasks_overdue_true(self, service):
        """Filter to get only overdue tasks."""
        # Create an overdue task
        task_overdue = service.add_task("Overdue task")
        past_date = datetime.now(CEST) - timedelta(days=1)
        task_overdue.due_date = past_date
        service._manager._persist()

        # Create a non-overdue task
        task_future = service.add_task("Future task")
        future_date = datetime.now(CEST) + timedelta(days=1)
        task_future.due_date = future_date
        service._manager._persist()

        # Create a task with no due date
        task_no_date = service.add_task("No date task")

        # Filter for overdue tasks
        results = service.list_tasks(overdue=True)

        # Should only include the overdue task
        assert len(results) == 1
        assert results[0].id == task_overdue.id

    def test_list_tasks_overdue_false(self, service):
        """Filter to get only non-overdue tasks."""
        # Create an overdue task
        task_overdue = service.add_task("Overdue task")
        past_date = datetime.now(CEST) - timedelta(days=1)
        task_overdue.due_date = past_date
        service._manager._persist()

        # Create a non-overdue task
        task_future = service.add_task("Future task")
        future_date = datetime.now(CEST) + timedelta(days=1)
        task_future.due_date = future_date
        service._manager._persist()

        # Create a task with no due date
        task_no_date = service.add_task("No date task")

        # Filter for non-overdue tasks
        results = service.list_tasks(overdue=False)

        # Should include future task and no-date task
        assert len(results) == 2
        result_ids = {r.id for r in results}
        assert task_future.id in result_ids
        assert task_no_date.id in result_ids

    def test_list_tasks_overdue_with_done_status(self, service):
        """Overdue filtering works even if task is marked done."""
        # Create an overdue task
        task = service.add_task("Overdue task")
        task.due_date = datetime.now(CEST) - timedelta(days=1)
        task.status = TaskStatus.DONE
        service._manager._persist()

        # Even if marked done, it's still overdue
        results = service.list_tasks(overdue=True)
        assert len(results) == 1
        assert results[0].id == task.id


class TestListTasksCombinedFilters:
    """Test list_tasks with multiple filters applied together."""

    def test_list_tasks_status_and_overdue(self, service):
        """Filter by both status and overdue."""
        # Overdue pending task
        t1 = service.add_task("Overdue pending")
        t1.status = TaskStatus.PENDING
        t1.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        # Overdue completed task
        t2 = service.add_task("Overdue done")
        t2.status = TaskStatus.DONE
        t2.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        # Non-overdue pending task
        t3 = service.add_task("Future pending")
        t3.status = TaskStatus.PENDING
        t3.due_date = datetime.now(CEST) + timedelta(days=1)
        service._manager._persist()

        # Filter for pending overdue tasks
        results = service.list_tasks(status=TaskStatus.PENDING, overdue=True)

        assert len(results) == 1
        assert results[0].id == t1.id

    def test_list_tasks_status_and_due_before(self, service):
        """Filter by both status and due before date."""
        # Pending task due in past
        t1 = service.add_task("Pending past")
        t1.status = TaskStatus.PENDING
        t1.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        # Pending task due in future
        t2 = service.add_task("Pending future")
        t2.status = TaskStatus.PENDING
        t2.due_date = datetime.now(CEST) + timedelta(days=1)
        service._manager._persist()

        # Done task due in past
        t3 = service.add_task("Done past")
        t3.status = TaskStatus.DONE
        t3.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        # Filter for pending tasks due before now
        cutoff = datetime.now(CEST)
        results = service.list_tasks(status=TaskStatus.PENDING, due_before=cutoff)

        assert len(results) == 1
        assert results[0].id == t1.id

    def test_list_tasks_all_filters_combined(self, service):
        """Filter by status, due date range, and overdue."""
        # Create multiple tasks
        t1 = service.add_task("Pending overdue")
        t1.status = TaskStatus.PENDING
        t1.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        t2 = service.add_task("In progress overdue")
        t2.status = TaskStatus.IN_PROGRESS
        t2.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        t3 = service.add_task("Pending future")
        t3.status = TaskStatus.PENDING
        t3.due_date = datetime.now(CEST) + timedelta(days=1)
        service._manager._persist()

        # Filter: pending, overdue, and due before tomorrow
        tomorrow = datetime.now(CEST) + timedelta(days=1)
        results = service.list_tasks(
            status=TaskStatus.PENDING,
            overdue=True,
            before=tomorrow
        )

        assert len(results) == 1
        assert results[0].id == t1.id

    def test_list_tasks_preserves_existing_behavior(self, service):
        """Filtering with no parameters returns all tasks."""
        t1 = service.add_task("Task 1")
        t2 = service.add_task("Task 2")
        t3 = service.add_task("Task 3")

        results = service.list_tasks()
        assert len(results) == 3

    def test_list_tasks_status_filter_unchanged(self, service):
        """Status-only filtering behavior is unchanged."""
        t1 = service.add_task("Pending 1")
        t1.status = TaskStatus.PENDING
        service._manager._persist()

        t2 = service.add_task("Done 1")
        t2.status = TaskStatus.DONE
        service._manager._persist()

        results = service.list_tasks(status=TaskStatus.PENDING)
        assert len(results) == 1
        assert results[0].id == t1.id


class TestApplyFilters:
    """Test TaskManager.apply_filters method directly."""

    def test_apply_filters_status_only(self, service):
        """apply_filters respects status filter."""
        t1 = service.add_task("Pending")
        t1.status = TaskStatus.PENDING
        service._manager._persist()

        t2 = service.add_task("Done")
        t2.status = TaskStatus.DONE
        service._manager._persist()

        opts = FilterOptions(status=TaskStatus.PENDING)
        results = service._manager.apply_filters(opts)

        assert len(results) == 1
        assert results[0].id == t1.id

    def test_apply_filters_due_before(self, service):
        """apply_filters respects due_before."""
        t1 = service.add_task("Past")
        t1.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        t2 = service.add_task("Future")
        t2.due_date = datetime.now(CEST) + timedelta(days=1)
        service._manager._persist()

        cutoff = datetime.now(CEST)
        opts = FilterOptions(due_before=cutoff)
        results = service._manager.apply_filters(opts)

        assert len(results) == 1
        assert results[0].id == t1.id

    def test_apply_filters_due_after(self, service):
        """apply_filters respects due_after."""
        t1 = service.add_task("Past")
        t1.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        t2 = service.add_task("Future")
        t2.due_date = datetime.now(CEST) + timedelta(days=1)
        service._manager._persist()

        cutoff = datetime.now(CEST)
        opts = FilterOptions(due_after=cutoff)
        results = service._manager.apply_filters(opts)

        assert len(results) == 1
        assert results[0].id == t2.id

    def test_apply_filters_overdue_only(self, service):
        """apply_filters respects overdue_only."""
        t1 = service.add_task("Overdue")
        t1.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        t2 = service.add_task("Future")
        t2.due_date = datetime.now(CEST) + timedelta(days=1)
        service._manager._persist()

        opts = FilterOptions(overdue_only=True)
        results = service._manager.apply_filters(opts)

        assert len(results) == 1
        assert results[0].id == t1.id

    def test_apply_filters_combined(self, service):
        """apply_filters respects multiple filters together."""
        t1 = service.add_task("Pending overdue")
        t1.status = TaskStatus.PENDING
        t1.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        t2 = service.add_task("Done overdue")
        t2.status = TaskStatus.DONE
        t2.due_date = datetime.now(CEST) - timedelta(days=1)
        service._manager._persist()

        opts = FilterOptions(status=TaskStatus.PENDING, overdue_only=True)
        results = service._manager.apply_filters(opts)

        assert len(results) == 1
        assert results[0].id == t1.id

    def test_apply_filters_empty_result(self, service):
        """apply_filters returns empty list when no tasks match."""
        service.add_task("Task")

        opts = FilterOptions(status=TaskStatus.DONE)
        results = service._manager.apply_filters(opts)

        assert len(results) == 0
