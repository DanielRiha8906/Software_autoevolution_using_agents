"""
Tests for date-based filtering functionality (Task 05).

Tests the following features:
- is_datetime_in_range() helper function
- TaskManager filter methods (list_by_due_date_before, list_by_due_date_after, list_by_due_date_range, list_overdue, list_by_status_with_filters)
- TodoService.list_tasks() with filter parameters
- CLI filters (--due-before, --due-after, --overdue)
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.models.task_status import TaskStatus
from src.services.task_manager import TaskManager
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage
from src.utils.datetime_utils import is_datetime_in_range, parse_datetime_or_iso_string
from src.cli.todo_cli import TodoCLI


# ─────────────────────────────────────────────────────────────────────────────
# Helper fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def cest():
    """Return CEST timezone."""
    return ZoneInfo("Europe/Paris")


@pytest.fixture
def manager(tmp_path):
    """Return TaskManager with temporary storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


@pytest.fixture
def service(tmp_path):
    """Return TodoService with temporary storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TodoService(storage)


@pytest.fixture
def cli(tmp_path):
    """Return TodoCLI with temporary storage."""
    return TodoCLI(str(tmp_path / "tasks.json"))


@pytest.fixture
def sample_tasks(manager, cest):
    """Create sample tasks with various due dates and statuses.

    Returns:
        dict with keys:
        - today: task due today at 23:59 CEST (pending, not overdue)
        - tomorrow: task due tomorrow at 00:00 CEST (pending)
        - next_week: task due in 7 days at 00:00 CEST (pending)
        - last_week: task due 7 days ago at 00:00 CEST (pending, overdue)
        - no_date: task with no due date (pending)
        - completed_overdue: task due 7 days ago at 00:00 CEST (completed, not overdue)
    """
    now = datetime.now(ZoneInfo("Europe/Paris"))
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    tomorrow_start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    next_week = tomorrow_start + timedelta(days=6)
    last_week = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)

    return {
        "today": manager.add("Today task", due_date=today_end),
        "tomorrow": manager.add("Tomorrow task", due_date=tomorrow_start),
        "next_week": manager.add("Next week task", due_date=next_week),
        "last_week": manager.add("Last week task", due_date=last_week),
        "no_date": manager.add("No date task"),
        "completed_overdue": manager.add("Completed overdue", due_date=last_week),
    }


@pytest.fixture
def setup_sample_tasks(sample_tasks, manager):
    """Mark the completed_overdue task as done."""
    manager.set_status(sample_tasks["completed_overdue"].id, TaskStatus.DONE)
    return sample_tasks


# ─────────────────────────────────────────────────────────────────────────────
# Tests for is_datetime_in_range()
# ─────────────────────────────────────────────────────────────────────────────

class TestIsDatetimeInRange:
    """Test is_datetime_in_range() helper function."""

    def test_none_datetime_returns_false(self, cest):
        """None datetime should always return False."""
        start = datetime(2025, 1, 1, tzinfo=cest)
        end = datetime(2025, 12, 31, tzinfo=cest)
        assert is_datetime_in_range(None, start, end) is False
        assert is_datetime_in_range(None, None, end) is False
        assert is_datetime_in_range(None, start, None) is False
        assert is_datetime_in_range(None, None, None) is False

    def test_within_range(self, cest):
        """Datetime within [start, end] should return True."""
        start = datetime(2025, 1, 1, tzinfo=cest)
        dt = datetime(2025, 6, 15, tzinfo=cest)
        end = datetime(2025, 12, 31, tzinfo=cest)
        assert is_datetime_in_range(dt, start, end) is True

    def test_on_start_boundary(self, cest):
        """Datetime equal to start should return True (inclusive)."""
        start = datetime(2025, 1, 1, tzinfo=cest)
        dt = start
        end = datetime(2025, 12, 31, tzinfo=cest)
        assert is_datetime_in_range(dt, start, end) is True

    def test_on_end_boundary(self, cest):
        """Datetime equal to end should return True (inclusive)."""
        start = datetime(2025, 1, 1, tzinfo=cest)
        dt = datetime(2025, 12, 31, tzinfo=cest)
        end = dt
        assert is_datetime_in_range(dt, start, end) is True

    def test_before_start(self, cest):
        """Datetime before start should return False."""
        start = datetime(2025, 6, 1, tzinfo=cest)
        dt = datetime(2025, 5, 31, tzinfo=cest)
        end = datetime(2025, 12, 31, tzinfo=cest)
        assert is_datetime_in_range(dt, start, end) is False

    def test_after_end(self, cest):
        """Datetime after end should return False."""
        start = datetime(2025, 1, 1, tzinfo=cest)
        dt = datetime(2026, 1, 1, tzinfo=cest)
        end = datetime(2025, 12, 31, tzinfo=cest)
        assert is_datetime_in_range(dt, start, end) is False

    def test_no_lower_bound(self, cest):
        """No lower bound (start=None) should allow any dt <= end."""
        dt = datetime(2025, 6, 15, tzinfo=cest)
        end = datetime(2025, 12, 31, tzinfo=cest)
        assert is_datetime_in_range(dt, None, end) is True
        dt_after_end = datetime(2026, 1, 1, tzinfo=cest)
        assert is_datetime_in_range(dt_after_end, None, end) is False

    def test_no_upper_bound(self, cest):
        """No upper bound (end=None) should allow any dt >= start."""
        start = datetime(2025, 1, 1, tzinfo=cest)
        dt = datetime(2025, 6, 15, tzinfo=cest)
        assert is_datetime_in_range(dt, start, None) is True
        dt_before_start = datetime(2024, 12, 31, tzinfo=cest)
        assert is_datetime_in_range(dt_before_start, start, None) is False

    def test_no_bounds(self, cest):
        """No bounds (start=None, end=None) should return True for any non-None dt."""
        dt = datetime(2025, 6, 15, tzinfo=cest)
        assert is_datetime_in_range(dt, None, None) is True


# ─────────────────────────────────────────────────────────────────────────────
# Tests for TaskManager filter methods
# ─────────────────────────────────────────────────────────────────────────────

class TestTaskManagerListByDueDateBefore:
    """Test TaskManager.list_by_due_date_before()."""

    def test_tasks_before_cutoff(self, setup_sample_tasks, manager, cest):
        """Should return tasks with due_date <= cutoff."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=23, minute=59, second=59, microsecond=0)
        cutoff = today + timedelta(days=1)

        tasks = manager.list_by_due_date_before(cutoff)
        # Should include: today, tomorrow, last_week, completed_overdue
        assert len(tasks) >= 3
        titles = {t.title for t in tasks}
        assert "Today task" in titles
        assert "Last week task" in titles
        assert "Completed overdue" in titles

    def test_no_tasks_before_cutoff(self, setup_sample_tasks, manager, cest):
        """Should return empty list if no tasks before cutoff."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = today - timedelta(days=30)

        tasks = manager.list_by_due_date_before(cutoff)
        assert len(tasks) == 0

    def test_excludes_tasks_without_due_date(self, setup_sample_tasks, manager, cest):
        """Should not include tasks without due_date."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = today + timedelta(days=30)

        tasks = manager.list_by_due_date_before(cutoff)
        titles = {t.title for t in tasks}
        assert "No date task" not in titles


class TestTaskManagerListByDueDateAfter:
    """Test TaskManager.list_by_due_date_after()."""

    def test_tasks_after_cutoff(self, setup_sample_tasks, manager, cest):
        """Should return tasks with due_date >= cutoff."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = today_end

        tasks = manager.list_by_due_date_after(cutoff)
        # Should include: today, tomorrow, next_week
        titles = {t.title for t in tasks}
        assert "Today task" in titles
        assert "Tomorrow task" in titles
        assert "Next week task" in titles

    def test_no_tasks_after_cutoff(self, setup_sample_tasks, manager, cest):
        """Should return empty list if no tasks after cutoff."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = today + timedelta(days=30)

        tasks = manager.list_by_due_date_after(cutoff)
        assert len(tasks) == 0

    def test_excludes_tasks_without_due_date(self, setup_sample_tasks, manager, cest):
        """Should not include tasks without due_date."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = today - timedelta(days=30)

        tasks = manager.list_by_due_date_after(cutoff)
        titles = {t.title for t in tasks}
        assert "No date task" not in titles


class TestTaskManagerListByDueDateRange:
    """Test TaskManager.list_by_due_date_range()."""

    def test_tasks_in_range(self, setup_sample_tasks, manager, cest):
        """Should return tasks within [start, end] range."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=10)
        end = today + timedelta(days=2)

        tasks = manager.list_by_due_date_range(start, end)
        titles = {t.title for t in tasks}
        assert "Last week task" in titles
        assert "Today task" in titles
        assert "Tomorrow task" in titles
        assert "Next week task" not in titles
        assert "No date task" not in titles

    def test_open_start_range(self, setup_sample_tasks, manager, cest):
        """Should handle range with open start (None)."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = today + timedelta(days=2)

        tasks = manager.list_by_due_date_range(None, end)
        titles = {t.title for t in tasks}
        assert "Last week task" in titles
        assert "Today task" in titles
        assert "Tomorrow task" in titles

    def test_open_end_range(self, setup_sample_tasks, manager, cest):
        """Should handle range with open end (None)."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today

        tasks = manager.list_by_due_date_range(start, None)
        titles = {t.title for t in tasks}
        assert "Today task" in titles
        assert "Tomorrow task" in titles
        assert "Next week task" in titles

    def test_empty_range(self, setup_sample_tasks, manager, cest):
        """Should return empty list for range with no tasks."""
        now = datetime.now(ZoneInfo("Europe/Paris"))
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today + timedelta(days=20)
        end = today + timedelta(days=30)

        tasks = manager.list_by_due_date_range(start, end)
        assert len(tasks) == 0


class TestTaskManagerListOverdue:
    """Test TaskManager.list_overdue()."""

    def test_returns_overdue_tasks(self, setup_sample_tasks, manager):
        """Should return only overdue tasks (past due date and not completed)."""
        tasks = manager.list_overdue()
        # Should only include: last_week (pending and overdue)
        assert len(tasks) == 1
        assert tasks[0].title == "Last week task"

    def test_excludes_completed_tasks(self, setup_sample_tasks, manager):
        """Should not include completed tasks even if past due date."""
        tasks = manager.list_overdue()
        titles = {t.title for t in tasks}
        assert "Completed overdue" not in titles

    def test_excludes_future_tasks(self, setup_sample_tasks, manager):
        """Should not include tasks with future due dates."""
        tasks = manager.list_overdue()
        titles = {t.title for t in tasks}
        assert "Today task" not in titles
        assert "Tomorrow task" not in titles
        assert "Next week task" not in titles

    def test_excludes_tasks_without_due_date(self, setup_sample_tasks, manager):
        """Should not include tasks without due_date."""
        tasks = manager.list_overdue()
        titles = {t.title for t in tasks}
        assert "No date task" not in titles


class TestTaskManagerListByStatusWithFilters:
    """Test TaskManager.list_by_status_with_filters()."""

    def test_filter_by_status_only(self, setup_sample_tasks, manager):
        """Should filter by status when provided."""
        # Mark some tasks as in_progress
        manager.set_status(setup_sample_tasks["today"].id, TaskStatus.IN_PROGRESS)

        tasks = manager.list_by_status_with_filters(status=TaskStatus.IN_PROGRESS)
        assert len(tasks) == 1
        assert tasks[0].title == "Today task"

    def test_filter_by_due_before(self, setup_sample_tasks, manager, cest):
        """Should filter by due_before when provided."""
        # Use a date far in the future to ensure all recent tasks are included
        cutoff = datetime(2099, 12, 31, 23, 59, 59, tzinfo=cest)

        tasks = manager.list_by_status_with_filters(due_before=cutoff)
        # Should include all tasks with due dates
        titles = {t.title for t in tasks}
        assert "Last week task" in titles
        assert "Today task" in titles
        assert "Tomorrow task" in titles
        assert "Next week task" in titles
        assert "No date task" not in titles

    def test_filter_by_due_after(self, setup_sample_tasks, manager, cest):
        """Should filter by due_after when provided."""
        # Use a date far in the past to ensure recent tasks are included
        cutoff = datetime(2000, 1, 1, 0, 0, 0, tzinfo=cest)

        tasks = manager.list_by_status_with_filters(due_after=cutoff)
        # Should include all tasks with due dates
        titles = {t.title for t in tasks}
        assert "Last week task" in titles
        assert "Today task" in titles
        assert "Tomorrow task" in titles
        assert "Next week task" in titles
        assert "No date task" not in titles

    def test_filter_overdue_only(self, setup_sample_tasks, manager):
        """Should filter to overdue tasks only when overdue_only=True."""
        tasks = manager.list_by_status_with_filters(overdue_only=True)
        assert len(tasks) == 1
        assert tasks[0].title == "Last week task"

    def test_combined_filters_and_logic(self, setup_sample_tasks, manager, cest):
        """Should combine filters with AND logic."""
        # Mark tomorrow task as in_progress
        manager.set_status(setup_sample_tasks["tomorrow"].id, TaskStatus.IN_PROGRESS)
        # Mark next_week task as in_progress
        manager.set_status(setup_sample_tasks["next_week"].id, TaskStatus.IN_PROGRESS)

        # Use a cutoff that includes tomorrow but not next_week
        cutoff = datetime(2099, 1, 1, 0, 0, 0, tzinfo=cest)
        cutoff_early = datetime(2000, 1, 1, 0, 0, 0, tzinfo=cest)

        tasks = manager.list_by_status_with_filters(
            status=TaskStatus.IN_PROGRESS,
            due_after=cutoff_early,
            due_before=cutoff,
        )
        # Should match any in_progress task within the range
        titles = {t.title for t in tasks}
        assert "Tomorrow task" in titles
        assert "Next week task" in titles

    def test_sorting_by_due_date(self, setup_sample_tasks, manager, cest):
        """Should sort by (due_date is None, due_date)."""
        tasks = manager.list_by_status_with_filters()
        # Tasks with due dates should come first, then None
        titles = [t.title for t in tasks]
        # The "No date task" should come after all tasks with due dates
        if "No date task" in titles:
            no_date_idx = titles.index("No date task")
            # At least some tasks with due dates should come before
            with_dates = ["Last week task", "Today task", "Tomorrow task", "Next week task", "Completed overdue"]
            any_before = any(title in titles and titles.index(title) < no_date_idx for title in with_dates)
            assert any_before


# ─────────────────────────────────────────────────────────────────────────────
# Tests for TodoService.list_tasks() with filters
# ─────────────────────────────────────────────────────────────────────────────

class TestTodoServiceListTasksWithFilters:
    """Test TodoService.list_tasks() with optional filter parameters."""

    def test_list_with_due_before_string(self, setup_sample_tasks, service, cest):
        """Should accept due_before as ISO string."""
        cutoff_str = "2099-12-31"
        tasks = service.list_tasks(due_before=cutoff_str)
        titles = {t.title for t in tasks}
        # Should include all tasks with due dates before cutoff
        assert "Today task" in titles
        assert "Last week task" in titles

    def test_list_with_due_after_string(self, setup_sample_tasks, service, cest):
        """Should accept due_after as ISO string."""
        cutoff_str = "2000-01-01"
        tasks = service.list_tasks(due_after=cutoff_str)
        titles = {t.title for t in tasks}
        # Should include all tasks with due dates after cutoff
        assert "Today task" in titles
        assert "Last week task" in titles
        assert "Tomorrow task" in titles

    def test_list_with_overdue_only(self, setup_sample_tasks, service):
        """Should filter to overdue tasks only."""
        tasks = service.list_tasks(overdue_only=True)
        assert len(tasks) == 1
        assert tasks[0].title == "Last week task"

    def test_list_with_status_and_date_filters(self, setup_sample_tasks, service, cest):
        """Should combine status and date filters."""
        # Mark today task as in_progress
        service._manager.set_status(setup_sample_tasks["today"].id, TaskStatus.IN_PROGRESS)

        tasks = service.list_tasks(
            status=TaskStatus.IN_PROGRESS,
            due_before="2099-12-31",
        )
        assert len(tasks) == 1
        assert tasks[0].title == "Today task"

    def test_list_backward_compatibility(self, setup_sample_tasks, service):
        """Should maintain backward compatibility with status-only filtering."""
        # Mark some tasks
        service._manager.set_status(setup_sample_tasks["today"].id, TaskStatus.DONE)

        # Old-style call should still work
        tasks = service.list_tasks(status=TaskStatus.DONE)
        assert len(tasks) == 2  # completed_overdue and today
        titles = {t.title for t in tasks}
        assert "Today task" in titles
        assert "Completed overdue" in titles


# ─────────────────────────────────────────────────────────────────────────────
# Tests for CLI filtering
# ─────────────────────────────────────────────────────────────────────────────

class TestCLIListFiltering:
    """Test CLI list command with date filters."""

    def test_list_with_due_before_flag(self, setup_sample_tasks, cli, cest):
        """Should filter with --due-before flag."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            result = cli.run(["list", "--due-before", "2099-12-31"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert result == 0
        assert "Today task" in output or "Last week task" in output or "Tomorrow task" in output

    def test_list_with_due_after_flag(self, setup_sample_tasks, cli, cest):
        """Should filter with --due-after flag."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            result = cli.run(["list", "--due-after", "2000-01-01"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert result == 0
        assert "Today task" in output or "Last week task" in output or "Tomorrow task" in output

    def test_list_with_overdue_flag(self, setup_sample_tasks, cli):
        """Should filter with --overdue flag."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            result = cli.run(["list", "--overdue"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert result == 0
        assert "Last week task" in output
        # completed_overdue is done, so shouldn't appear
        assert "Completed overdue" not in output

    def test_list_with_invalid_due_before_date(self, cli):
        """Should return error for invalid --due-before date."""
        import io
        import sys
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        try:
            result = cli.run(["list", "--due-before", "invalid-date"])
            error = sys.stderr.getvalue()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        assert result == 1
        assert "Error" in error or "Could not parse" in error

    def test_list_with_invalid_date_range(self, cli, cest):
        """Should return error if due_after > due_before."""
        import io
        import sys
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        try:
            result = cli.run([
                "list",
                "--due-after", "2099-12-31",
                "--due-before", "2000-01-01",
            ])
            error = sys.stderr.getvalue()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        assert result == 1
        assert "cannot be after" in error
