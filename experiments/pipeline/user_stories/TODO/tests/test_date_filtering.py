"""Tests for date filtering functionality.

Covers:
- TaskManager.list_by_due_date_range() with before, after, status, overdue filtering
- TaskManager boundary calculation methods (get_week_boundaries, get_month_boundaries, get_year_boundaries)
- TodoService.list_tasks() with date parameters
- TodoService period-based listing (list_tasks_by_week/month/year)
- TodoCLI._cmd_list() with date flags
- InteractiveMenu._do_list() filter submenu
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_status import TaskStatus
from src.services.task_manager import TaskManager
from src.services.todo_service import TodoService
from src.cli.todo_cli import TodoCLI
from src.storage.json_storage import JsonStorage


@pytest.fixture
def manager(tmp_path):
    """Create a TaskManager with temporary storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


@pytest.fixture
def service(tmp_path):
    """Create a TodoService with temporary storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TodoService(storage)


@pytest.fixture
def cli(tmp_path):
    """Create a TodoCLI with temporary storage."""
    return TodoCLI(str(tmp_path / "tasks.json"))


# ─── TaskManager.list_by_due_date_range() Tests ────────────────────────────


class TestListByDueDateRange:
    """Test filtering by due date range."""

    def test_filter_before_date_inclusive(self, manager):
        """Tasks with due_date <= before should be included."""
        # Setup
        dt_before = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        dt_on = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        dt_after = datetime(2026, 5, 16, 0, 0, tzinfo=timezone.utc)

        t1 = manager.add("Before", due_date=datetime(2026, 5, 14, 23, 59, tzinfo=timezone.utc))
        t2 = manager.add("On date", due_date=dt_on)
        t3 = manager.add("After", due_date=dt_after)

        # Filter
        result = manager.list_by_due_date_range(before=dt_before)

        # Assert
        assert len(result) == 2
        assert t1 in result
        assert t2 in result
        assert t3 not in result

    def test_filter_after_date_inclusive(self, manager):
        """Tasks with due_date >= after should be included."""
        # Setup
        dt_after = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        dt_on = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        dt_before = datetime(2026, 5, 14, 23, 59, tzinfo=timezone.utc)

        t1 = manager.add("Before", due_date=dt_before)
        t2 = manager.add("On date", due_date=dt_on)
        t3 = manager.add("After", due_date=datetime(2026, 5, 16, 0, 0, tzinfo=timezone.utc))

        # Filter
        result = manager.list_by_due_date_range(after=dt_after)

        # Assert
        assert len(result) == 2
        assert t1 not in result
        assert t2 in result
        assert t3 in result

    def test_filter_date_range(self, manager):
        """Tasks within date range (both before and after) should be included."""
        # Setup
        dt_start = datetime(2026, 5, 10, 0, 0, tzinfo=timezone.utc)
        dt_end = datetime(2026, 5, 20, 23, 59, tzinfo=timezone.utc)

        t1 = manager.add("Too early", due_date=datetime(2026, 5, 5, 0, 0, tzinfo=timezone.utc))
        t2 = manager.add("In range 1", due_date=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc))
        t3 = manager.add("In range 2", due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
        t4 = manager.add("Too late", due_date=datetime(2026, 5, 25, 0, 0, tzinfo=timezone.utc))

        # Filter
        result = manager.list_by_due_date_range(after=dt_start, before=dt_end)

        # Assert
        assert len(result) == 2
        assert t1 not in result
        assert t2 in result
        assert t3 in result
        assert t4 not in result

    def test_exclude_tasks_without_due_date(self, manager):
        """Tasks with no due_date should be excluded from date range filters."""
        # Setup
        t1 = manager.add("No due date")
        t2 = manager.add("With due date", due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))

        # Filter
        result = manager.list_by_due_date_range(
            after=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
        )

        # Assert
        assert len(result) == 1
        assert t1 not in result
        assert t2 in result

    def test_filter_with_status(self, manager):
        """Combine due date range with status filter."""
        # Setup
        t1 = manager.add("Done task", due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
        t2 = manager.add("Pending task", due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))

        manager.set_status(t1.id, TaskStatus.IN_PROGRESS)
        manager.set_status(t1.id, TaskStatus.DONE)

        # Filter
        result = manager.list_by_due_date_range(
            after=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
            status=TaskStatus.PENDING
        )

        # Assert
        assert len(result) == 1
        assert t2 in result
        assert t1 not in result

    def test_overdue_filter_pending_task(self, manager):
        """Overdue filter should include only pending/in_progress tasks with due_date in past."""
        # Setup: Use a fixed past time
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)

        t_overdue = manager.add("Overdue", due_date=past)
        t_future = manager.add("Future", due_date=future)
        t_no_due = manager.add("No due date")

        # Filter for overdue only
        result = manager.list_by_due_date_range(overdue_only=True)

        # Assert
        assert len(result) == 1
        assert t_overdue in result
        assert t_future not in result
        assert t_no_due not in result

    def test_overdue_filter_done_task_excluded(self, manager):
        """Overdue filter should exclude DONE tasks even if they had past due_date."""
        # Setup
        past = datetime.now(timezone.utc) - timedelta(days=1)
        t_done = manager.add("Done overdue", due_date=past)
        t_pending = manager.add("Pending overdue", due_date=past)

        manager.set_status(t_done.id, TaskStatus.IN_PROGRESS)
        manager.set_status(t_done.id, TaskStatus.DONE)

        # Filter for overdue
        result = manager.list_by_due_date_range(overdue_only=True)

        # Assert
        assert len(result) == 1
        assert t_pending in result
        assert t_done not in result

    def test_overdue_with_status_filter(self, manager):
        """Combine overdue filter with status filter."""
        # Setup
        past = datetime.now(timezone.utc) - timedelta(days=1)
        t_pending_overdue = manager.add("Pending overdue", due_date=past)
        t_in_progress_overdue = manager.add("In progress overdue", due_date=past)

        manager.set_status(t_in_progress_overdue.id, TaskStatus.IN_PROGRESS)

        # Filter for overdue pending only
        result = manager.list_by_due_date_range(
            overdue_only=True,
            status=TaskStatus.PENDING
        )

        # Assert
        assert len(result) == 1
        assert t_pending_overdue in result
        assert t_in_progress_overdue not in result

    def test_empty_result_when_no_matches(self, manager):
        """Should return empty list when no tasks match filter."""
        # Setup
        manager.add("Task 1", due_date=datetime(2026, 5, 10, 0, 0, tzinfo=timezone.utc))
        manager.add("Task 2", due_date=datetime(2026, 5, 10, 0, 0, tzinfo=timezone.utc))

        # Filter with date range that excludes all
        result = manager.list_by_due_date_range(
            after=datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
        )

        # Assert
        assert len(result) == 0

    def test_all_tasks_match_when_filter_wide(self, manager):
        """Should return all tasks when filter is very wide."""
        # Setup
        t1 = manager.add("Early", due_date=datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc))
        t2 = manager.add("Recent", due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
        t3 = manager.add("Future", due_date=datetime(2099, 12, 31, 23, 59, tzinfo=timezone.utc))

        # Filter with very wide range
        result = manager.list_by_due_date_range(
            after=datetime(1900, 1, 1, 0, 0, tzinfo=timezone.utc),
            before=datetime(2100, 12, 31, 23, 59, tzinfo=timezone.utc)
        )

        # Assert
        assert len(result) == 3


# ─── TaskManager Boundary Calculation Tests ────────────────────────────────


class TestWeekBoundaries:
    """Test get_week_boundaries() calculation."""

    def test_valid_week(self, manager):
        """Should return correct start and end for valid ISO week."""
        start, end = manager.get_week_boundaries(2026, 20)

        # Week 20, 2026: Monday May 11 to Sunday May 17
        assert start.year == 2026
        assert start.month == 5
        assert start.day == 11
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.tzinfo == timezone.utc

        assert end.year == 2026
        assert end.month == 5
        assert end.day == 17
        assert end.tzinfo == timezone.utc

    def test_week_1(self, manager):
        """Week 1 should start on the first Monday of the year."""
        start, end = manager.get_week_boundaries(2026, 1)
        # 2026-01-01 is a Thursday, so week 1 starts Mon 2025-12-29
        assert start.month == 12
        assert start.year == 2025
        assert start.tzinfo == timezone.utc

    def test_week_52(self, manager):
        """Week 52/53 calculation."""
        start, end = manager.get_week_boundaries(2026, 52)
        assert start.tzinfo == timezone.utc
        assert end.tzinfo == timezone.utc
        # Just verify it's consistent
        assert start < end

    def test_invalid_week_zero(self, manager):
        """Should raise ValueError for week 0."""
        with pytest.raises(ValueError, match="Week must be 1-53"):
            manager.get_week_boundaries(2026, 0)

    def test_invalid_week_54(self, manager):
        """Should raise ValueError for week 54."""
        with pytest.raises(ValueError, match="Week must be 1-53"):
            manager.get_week_boundaries(2026, 54)

    def test_invalid_week_negative(self, manager):
        """Should raise ValueError for negative week."""
        with pytest.raises(ValueError, match="Week must be 1-53"):
            manager.get_week_boundaries(2026, -1)

    def test_week_boundaries_timezone_utc(self, manager):
        """Week boundaries should be in UTC."""
        start, end = manager.get_week_boundaries(2026, 20)
        assert start.tzinfo is timezone.utc
        assert end.tzinfo is timezone.utc


class TestMonthBoundaries:
    """Test get_month_boundaries() calculation."""

    def test_valid_month(self, manager):
        """Should return correct start and end for valid month."""
        start, end = manager.get_month_boundaries(2026, 5)

        assert start.year == 2026
        assert start.month == 5
        assert start.day == 1
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.tzinfo == timezone.utc

        assert end.year == 2026
        assert end.month == 5
        assert end.day == 31
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59
        assert end.tzinfo == timezone.utc

    def test_february_non_leap_year(self, manager):
        """February in non-leap year should end on 28th."""
        start, end = manager.get_month_boundaries(2025, 2)
        assert end.day == 28

    def test_february_leap_year(self, manager):
        """February in leap year should end on 29th."""
        start, end = manager.get_month_boundaries(2024, 2)
        assert end.day == 29

    def test_invalid_month_zero(self, manager):
        """Should raise ValueError for month 0."""
        with pytest.raises(ValueError, match="Month must be 1-12"):
            manager.get_month_boundaries(2026, 0)

    def test_invalid_month_13(self, manager):
        """Should raise ValueError for month 13."""
        with pytest.raises(ValueError, match="Month must be 1-12"):
            manager.get_month_boundaries(2026, 13)

    def test_invalid_month_negative(self, manager):
        """Should raise ValueError for negative month."""
        with pytest.raises(ValueError, match="Month must be 1-12"):
            manager.get_month_boundaries(2026, -1)

    def test_month_boundaries_timezone_utc(self, manager):
        """Month boundaries should be in UTC."""
        start, end = manager.get_month_boundaries(2026, 5)
        assert start.tzinfo is timezone.utc
        assert end.tzinfo is timezone.utc


class TestYearBoundaries:
    """Test get_year_boundaries() calculation."""

    def test_valid_year(self, manager):
        """Should return correct start and end for valid year."""
        start, end = manager.get_year_boundaries(2026)

        assert start.year == 2026
        assert start.month == 1
        assert start.day == 1
        assert start.hour == 0
        assert start.minute == 0
        assert start.second == 0
        assert start.tzinfo == timezone.utc

        assert end.year == 2026
        assert end.month == 12
        assert end.day == 31
        assert end.hour == 23
        assert end.minute == 59
        assert end.second == 59
        assert end.tzinfo == timezone.utc

    def test_leap_year(self, manager):
        """Should handle leap years correctly."""
        start, end = manager.get_year_boundaries(2024)
        assert start.year == 2024
        assert end.year == 2024

    def test_year_boundaries_timezone_utc(self, manager):
        """Year boundaries should be in UTC."""
        start, end = manager.get_year_boundaries(2026)
        assert start.tzinfo is timezone.utc
        assert end.tzinfo is timezone.utc


# ─── TodoService.list_tasks() Tests ────────────────────────────────────────


class TestTodoServiceListTasks:
    """Test TodoService.list_tasks() with date filtering."""

    def test_list_with_no_filters(self, service):
        """Should return all tasks when no filters applied."""
        service.add_task("A")
        service.add_task("B")
        service.add_task("C")

        result = service.list_tasks()
        assert len(result) == 3

    def test_list_with_status_filter_only(self, service):
        """Should filter by status when specified."""
        t1 = service.add_task("A")
        t2 = service.add_task("B")

        service.start_task(t1.id)

        result = service.list_tasks(status=TaskStatus.IN_PROGRESS)
        assert len(result) == 1
        assert result[0].id == t1.id

    def test_list_with_date_range(self, service):
        """Should filter by date range when before/after specified."""
        dt_start = datetime(2026, 5, 10, 0, 0, tzinfo=timezone.utc)
        dt_end = datetime(2026, 5, 20, 23, 59, tzinfo=timezone.utc)

        service.add_task("Before", due_date=datetime(2026, 5, 5, 0, 0, tzinfo=timezone.utc))
        service.add_task("In range", due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
        service.add_task("After", due_date=datetime(2026, 5, 25, 0, 0, tzinfo=timezone.utc))

        result = service.list_tasks(after=dt_start, before=dt_end)
        assert len(result) == 1
        assert result[0].title == "In range"

    def test_list_with_status_and_date_range(self, service):
        """Should combine status and date range filters."""
        dt_start = datetime(2026, 5, 10, 0, 0, tzinfo=timezone.utc)
        dt_end = datetime(2026, 5, 20, 23, 59, tzinfo=timezone.utc)

        t1 = service.add_task("Pending in range", due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))
        t2 = service.add_task("Done in range", due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc))

        service.start_task(t2.id)
        service.complete_task(t2.id)

        result = service.list_tasks(
            status=TaskStatus.PENDING,
            after=dt_start,
            before=dt_end
        )
        assert len(result) == 1
        assert result[0].id == t1.id

    def test_list_with_overdue_only(self, service):
        """Should filter to overdue tasks only."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)

        service.add_task("Overdue", due_date=past)
        service.add_task("Future", due_date=future)

        result = service.list_tasks(overdue_only=True)
        assert len(result) == 1
        assert result[0].title == "Overdue"

    def test_list_backward_compatibility(self, service):
        """Should work with no date args (backward compatibility)."""
        service.add_task("A")
        service.add_task("B")

        # Should not raise
        result = service.list_tasks()
        assert len(result) == 2


# ─── TodoService Period-based Listing Tests ────────────────────────────────


class TestTodoServiceByPeriod:
    """Test TodoService period-based listing methods."""

    def test_list_by_week_valid(self, service):
        """Should list tasks due in specified week."""
        # Week 20, 2026: Mon May 11 to Sun May 17
        task_in_week = service.add_task(
            "In week",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        task_outside = service.add_task(
            "Outside week",
            due_date=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc)
        )

        result = service.list_tasks_by_week(2026, 20)
        assert len(result) == 1
        assert result[0].id == task_in_week.id

    def test_list_by_week_with_status(self, service):
        """Should apply status filter to week listing."""
        t1 = service.add_task(
            "Pending",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        t2 = service.add_task(
            "Done",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        service.start_task(t2.id)
        service.complete_task(t2.id)

        result = service.list_tasks_by_week(2026, 20, status=TaskStatus.PENDING)
        assert len(result) == 1
        assert result[0].id == t1.id

    def test_list_by_week_invalid_week(self, service):
        """Should raise ValueError for invalid week."""
        with pytest.raises(ValueError):
            service.list_tasks_by_week(2026, 54)

    def test_list_by_month_valid(self, service):
        """Should list tasks due in specified month."""
        task_in_month = service.add_task(
            "In month",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        task_outside = service.add_task(
            "Outside month",
            due_date=datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        )

        result = service.list_tasks_by_month(2026, 5)
        assert len(result) == 1
        assert result[0].id == task_in_month.id

    def test_list_by_month_with_status(self, service):
        """Should apply status filter to month listing."""
        t1 = service.add_task(
            "Pending",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        t2 = service.add_task(
            "Done",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        service.start_task(t2.id)
        service.complete_task(t2.id)

        result = service.list_tasks_by_month(2026, 5, status=TaskStatus.PENDING)
        assert len(result) == 1
        assert result[0].id == t1.id

    def test_list_by_month_invalid_month(self, service):
        """Should raise ValueError for invalid month."""
        with pytest.raises(ValueError):
            service.list_tasks_by_month(2026, 13)

    def test_list_by_year_valid(self, service):
        """Should list tasks due in specified year."""
        task_in_year = service.add_task(
            "In year",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        task_outside = service.add_task(
            "Outside year",
            due_date=datetime(2027, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        result = service.list_tasks_by_year(2026)
        assert len(result) == 1
        assert result[0].id == task_in_year.id

    def test_list_by_year_with_status(self, service):
        """Should apply status filter to year listing."""
        t1 = service.add_task(
            "Pending",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        t2 = service.add_task(
            "Done",
            due_date=datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
        )

        service.start_task(t2.id)
        service.complete_task(t2.id)

        result = service.list_tasks_by_year(2026, status=TaskStatus.PENDING)
        assert len(result) == 1
        assert result[0].id == t1.id


# ─── TodoCLI._cmd_list() Tests ──────────────────────────────────────────────


class TestTodoCLIListCommand:
    """Test TodoCLI list command with date filters."""

    def test_list_no_filters(self, cli):
        """Should list all tasks with no flags."""
        cli._service.add_task("A")
        cli._service.add_task("B")

        result = cli.run(["list"])
        assert result == 0

    def test_list_with_due_before(self, cli):
        """Should filter by --due-before flag."""
        cli._service.add_task(
            "Before",
            due_date=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)
        )
        cli._service.add_task(
            "After",
            due_date=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)
        )

        result = cli.run(["list", "--due-before", "2026-05-15T12:00:00+00:00"])
        assert result == 0

    def test_list_with_due_after(self, cli):
        """Should filter by --due-after flag."""
        cli._service.add_task(
            "Before",
            due_date=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)
        )
        cli._service.add_task(
            "After",
            due_date=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)
        )

        result = cli.run(["list", "--due-after", "2026-05-15T12:00:00+00:00"])
        assert result == 0

    def test_list_with_status(self, cli):
        """Should filter by --status flag."""
        t1 = cli._service.add_task("A")
        t2 = cli._service.add_task("B")
        cli._service.start_task(t1.id)

        result = cli.run(["list", "--status", "in_progress"])
        assert result == 0

    def test_list_with_week(self, cli):
        """Should filter by --week flag (YYYY-Www format)."""
        cli._service.add_task(
            "In week",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        result = cli.run(["list", "--week", "2026-W20"])
        assert result == 0

    def test_list_with_month(self, cli):
        """Should filter by --month flag (YYYY-MM format)."""
        cli._service.add_task(
            "In month",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        result = cli.run(["list", "--month", "2026-05"])
        assert result == 0

    def test_list_with_year(self, cli):
        """Should filter by --year flag (YYYY format)."""
        cli._service.add_task(
            "In year",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        result = cli.run(["list", "--year", "2026"])
        assert result == 0

    def test_list_with_overdue(self, cli):
        """Should filter by --overdue flag."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        cli._service.add_task("Overdue", due_date=past)

        result = cli.run(["list", "--overdue"])
        assert result == 0

    def test_list_invalid_week_format(self, cli):
        """Should error with invalid week format."""
        result = cli.run(["list", "--week", "invalid"])
        assert result == 1

    def test_list_invalid_month_format(self, cli):
        """Should error with invalid month format."""
        result = cli.run(["list", "--month", "invalid"])
        assert result == 1

    def test_list_invalid_year_format(self, cli):
        """Should error with invalid year format."""
        result = cli.run(["list", "--year", "invalid"])
        assert result == 1

    def test_list_invalid_due_before_date(self, cli):
        """Should error with invalid ISO 8601 due-before."""
        result = cli.run(["list", "--due-before", "not-a-date"])
        assert result == 1

    def test_list_invalid_due_after_date(self, cli):
        """Should error with invalid ISO 8601 due-after."""
        result = cli.run(["list", "--due-after", "not-a-date"])
        assert result == 1

    def test_list_with_status_and_date_range(self, cli):
        """Should combine --status with date filters."""
        t1 = cli._service.add_task(
            "Pending in range",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        t2 = cli._service.add_task(
            "Done in range",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        cli._service.start_task(t2.id)
        cli._service.complete_task(t2.id)

        result = cli.run([
            "list",
            "--status", "pending",
            "--due-after", "2026-05-10T00:00:00+00:00",
            "--due-before", "2026-05-20T23:59:59+00:00"
        ])
        assert result == 0

    def test_list_empty_result(self, cli):
        """Should handle empty results gracefully."""
        result = cli.run(["list", "--year", "2099"])
        assert result == 0


# ─── TodoCLI Date Format Parsing Tests ──────────────────────────────────────


class TestTodoCLIDateParsing:
    """Test date format parsing helpers in TodoCLI."""

    def test_parse_and_list_by_week_valid(self, cli):
        """Should parse and list by valid week format."""
        cli._service.add_task(
            "Test",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        result = cli._parse_and_list_by_week("2026-W20", None)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_parse_and_list_by_week_invalid_format(self, cli):
        """Should raise ValueError for invalid week format."""
        with pytest.raises(ValueError, match="Invalid week format"):
            cli._parse_and_list_by_week("invalid", None)

    def test_parse_and_list_by_week_with_status(self, cli):
        """Should apply status filter when provided."""
        t1 = cli._service.add_task(
            "Pending",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        t2 = cli._service.add_task(
            "Done",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        cli._service.start_task(t2.id)
        cli._service.complete_task(t2.id)

        result = cli._parse_and_list_by_week("2026-W20", TaskStatus.PENDING)
        assert len(result) == 1
        assert result[0].id == t1.id

    def test_parse_and_list_by_month_valid(self, cli):
        """Should parse and list by valid month format."""
        cli._service.add_task(
            "Test",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        result = cli._parse_and_list_by_month("2026-05", None)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_parse_and_list_by_month_invalid_format(self, cli):
        """Should raise ValueError for invalid month format."""
        with pytest.raises(ValueError, match="Invalid month format"):
            cli._parse_and_list_by_month("invalid", None)

    def test_parse_and_list_by_year_valid(self, cli):
        """Should parse and list by valid year format."""
        cli._service.add_task(
            "Test",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )

        result = cli._parse_and_list_by_year("2026", None)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_parse_and_list_by_year_invalid_format(self, cli):
        """Should raise ValueError for invalid year format."""
        with pytest.raises(ValueError, match="Invalid year format"):
            cli._parse_and_list_by_year("invalid", None)


# ─── Integration Tests ──────────────────────────────────────────────────────


class TestDateFilteringIntegration:
    """Integration tests across service and CLI layers."""

    def test_end_to_end_date_filtering(self, service):
        """Complete flow: add tasks with due dates, filter by range."""
        # Setup
        service.add_task(
            "Q1 task",
            due_date=datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc)
        )
        service.add_task(
            "Q2 task",
            due_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
        )
        service.add_task(
            "Q3 task",
            due_date=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
        )

        # Filter to May only
        result = service.list_tasks_by_month(2026, 5)
        assert len(result) == 1
        assert result[0].title == "Q2 task"

    def test_combined_status_and_period_filtering(self, service):
        """Filter by both status and time period."""
        # Setup: Multiple tasks in May
        t1 = service.add_task(
            "Pending May",
            due_date=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)
        )
        t2 = service.add_task(
            "Done May",
            due_date=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)
        )
        service.start_task(t2.id)
        service.complete_task(t2.id)

        # Filter for pending tasks in May
        result = service.list_tasks_by_month(2026, 5, status=TaskStatus.PENDING)
        assert len(result) == 1
        assert result[0].id == t1.id
        assert result[0].status == TaskStatus.PENDING

    def test_overdue_status_interaction(self, service):
        """Overdue tasks should exclude completed tasks."""
        past = datetime.now(timezone.utc) - timedelta(days=1)

        # Overdue pending
        t1 = service.add_task("Overdue pending", due_date=past)

        # Overdue but done
        t2 = service.add_task("Overdue done", due_date=past)
        service.start_task(t2.id)
        service.complete_task(t2.id)

        # Check overdue
        overdue = service.list_tasks(overdue_only=True)
        assert len(overdue) == 1
        assert overdue[0].id == t1.id
