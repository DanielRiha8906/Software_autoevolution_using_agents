"""
Comprehensive tests for Task 05 features:
- TaskRepository.list_by_filter() with all filter combinations
- TodoService.list_tasks() backward compatibility and new parameters
- Timezone utility functions (now_in_cest, is_overdue_cest, utc_to_cest)
- CLI argument parsing for new flags (--due-after, --due-before, --overdue, --not-overdue)
"""

import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from src.models.task_status import TaskStatus
from src.repositories.task_repository import TaskRepository
from src.repositories.comment_repository import CommentRepository
from src.repositories.project_repository import ProjectRepository
from src.services.todo_service import TodoService
from src.exceptions import TaskNotFoundError
from src.cli.todo_cli import TodoCLI
from src.utils.timezone_utils import now_in_cest, is_overdue_cest, utc_to_cest


# ========== Fixtures ==========

@pytest.fixture
def manager(tmp_path):
    """TaskRepository with temporary storage."""
    return TaskRepository(tmp_path / "tasks.json")


@pytest.fixture
def service(tmp_path):
    """TodoService with temporary storage."""
    return TodoService(
        TaskRepository(tmp_path / "tasks.json"),
        CommentRepository(tmp_path / "comments.json"),
        ProjectRepository(tmp_path / "projects.json"),
    )


@pytest.fixture
def cli(tmp_path):
    """TodoCLI with temporary storage."""
    return TodoCLI(storage_path=str(tmp_path / "tasks.json"))


@pytest.fixture
def sample_tasks(manager):
    """Create tasks with varying statuses and due dates for filtering tests.

    Returns:
        dict mapping task descriptions to Task objects.
    """
    # All datetimes in UTC
    now_utc = datetime.now(timezone.utc)
    yesterday = now_utc - timedelta(days=1)
    tomorrow = now_utc + timedelta(days=1)
    next_week = now_utc + timedelta(days=7)

    tasks = {}

    # Pending tasks
    t1 = manager.add("Pending with no due date")
    tasks["pending_no_due"] = t1

    # Pending task - overdue
    t2 = manager.add("Pending overdue")
    t2.due_date = yesterday
    manager._persist()
    tasks["pending_overdue"] = t2

    # Pending task - future due date
    t3 = manager.add("Pending with future due")
    t3.due_date = tomorrow
    manager._persist()
    tasks["pending_future"] = t3

    # In-progress task
    t4 = manager.add("In progress no due")
    manager.set_status(t4.id, TaskStatus.IN_PROGRESS)
    tasks["in_progress_no_due"] = t4

    # In-progress overdue
    t5 = manager.add("In progress overdue")
    t5.due_date = yesterday
    manager.set_status(t5.id, TaskStatus.IN_PROGRESS)
    manager._persist()
    tasks["in_progress_overdue"] = t5

    # Done task - overdue (should not be overdue)
    t6 = manager.add("Done overdue")
    t6.due_date = yesterday
    manager.set_status(t6.id, TaskStatus.DONE)
    manager._persist()
    tasks["done_overdue"] = t6

    # Done task - future due
    t7 = manager.add("Done with future")
    t7.due_date = tomorrow
    manager.set_status(t7.id, TaskStatus.DONE)
    manager._persist()
    tasks["done_future"] = t7

    # Task with far future due
    t8 = manager.add("Far future")
    t8.due_date = next_week
    manager._persist()
    tasks["pending_far_future"] = t8

    return tasks


# ========== Tests for TaskManager.list_by_filter() ==========

class TestTaskManagerListByFilter:
    """Tests for TaskManager.list_by_filter() with all filter combinations."""

    # --- Test status filter alone ---

    def test_list_by_filter_status_pending(self, manager, sample_tasks):
        """Filter by PENDING status only."""
        result = manager.list_by_filter(status=TaskStatus.PENDING)
        assert len(result) == 4  # pending_no_due, pending_overdue, pending_future, pending_far_future
        assert all(t.status == TaskStatus.PENDING for t in result)

    def test_list_by_filter_status_in_progress(self, manager, sample_tasks):
        """Filter by IN_PROGRESS status only."""
        result = manager.list_by_filter(status=TaskStatus.IN_PROGRESS)
        assert len(result) == 2  # in_progress_no_due, in_progress_overdue
        assert all(t.status == TaskStatus.IN_PROGRESS for t in result)

    def test_list_by_filter_status_done(self, manager, sample_tasks):
        """Filter by DONE status only."""
        result = manager.list_by_filter(status=TaskStatus.DONE)
        assert len(result) == 2  # done_overdue, done_future
        assert all(t.status == TaskStatus.DONE for t in result)

    # --- Test due_after filter ---

    def test_list_by_filter_due_after_excludes_tasks_without_due_date(self, manager, sample_tasks):
        """Tasks without due_date are excluded from due_after filtering."""
        now_utc = datetime.now(timezone.utc)
        result = manager.list_by_filter(due_after=now_utc - timedelta(days=2))
        # Should exclude tasks without due_date
        assert all(t.due_date is not None for t in result)

    def test_list_by_filter_due_after_includes_matching_dates(self, manager, sample_tasks):
        """due_after includes tasks with due_date >= cutoff."""
        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc - timedelta(hours=1)
        result = manager.list_by_filter(due_after=cutoff)
        # Should include pending_future, done_future, pending_far_future
        # (tasks with due_dates >= cutoff)
        assert len(result) >= 1
        assert all(t.due_date >= cutoff for t in result)

    def test_list_by_filter_due_after_excludes_before_cutoff(self, manager, sample_tasks):
        """due_after excludes tasks with due_date < cutoff."""
        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc  # Exclude tasks before now
        result = manager.list_by_filter(due_after=cutoff)
        assert all(t.due_date >= cutoff for t in result)

    # --- Test due_before filter ---

    def test_list_by_filter_due_before_includes_past_dates(self, manager, sample_tasks):
        """due_before includes tasks with due_date <= cutoff."""
        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc - timedelta(hours=1)
        result = manager.list_by_filter(due_before=cutoff)
        # Should include tasks with past due dates
        assert len(result) >= 1
        assert all(t.due_date <= cutoff for t in result)

    def test_list_by_filter_due_before_excludes_future_dates(self, manager, sample_tasks):
        """due_before excludes tasks with due_date > cutoff."""
        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc - timedelta(hours=1)
        result = manager.list_by_filter(due_before=cutoff)
        assert all(t.due_date <= cutoff for t in result)

    # --- Test date range (due_after AND due_before) ---

    def test_list_by_filter_date_range(self, manager, sample_tasks):
        """Filter by date range (both due_after and due_before)."""
        now_utc = datetime.now(timezone.utc)
        start = now_utc - timedelta(days=2)
        end = now_utc + timedelta(hours=1)
        result = manager.list_by_filter(due_after=start, due_before=end)
        # Should return tasks with due_date in [start, end]
        assert all(t.due_date is not None for t in result)
        assert all(start <= t.due_date <= end for t in result)

    def test_list_by_filter_date_range_validation(self, manager, sample_tasks):
        """Raises ValueError if due_after > due_before."""
        now_utc = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="due_after cannot be after due_before"):
            manager.list_by_filter(
                due_after=now_utc,
                due_before=now_utc - timedelta(days=1)
            )

    # --- Test overdue filter ---

    def test_list_by_filter_overdue_true(self, manager, sample_tasks):
        """Filter overdue=True returns only overdue tasks."""
        result = manager.list_by_filter(overdue=True)
        assert len(result) >= 1
        assert all(t.is_overdue() for t in result)

    def test_list_by_filter_overdue_false(self, manager, sample_tasks):
        """Filter overdue=False returns only non-overdue tasks."""
        result = manager.list_by_filter(overdue=False)
        # Should include tasks with no due date or future due dates (but not done tasks with past dates)
        assert all(not t.is_overdue() for t in result)

    def test_list_by_filter_overdue_respects_done_status(self, manager, sample_tasks):
        """Done tasks are never overdue, even with past due_date."""
        # Verify that done task with past due_date is not returned by overdue=True
        result = manager.list_by_filter(overdue=True)
        done_tasks = [t for t in result if t.status == TaskStatus.DONE]
        assert len(done_tasks) == 0  # No done tasks should be overdue

    # --- Test combined filters ---

    def test_list_by_filter_status_and_overdue(self, manager, sample_tasks):
        """Filter by both status and overdue."""
        result = manager.list_by_filter(status=TaskStatus.PENDING, overdue=True)
        assert all(t.status == TaskStatus.PENDING and t.is_overdue() for t in result)

    def test_list_by_filter_status_and_date_range(self, manager, sample_tasks):
        """Filter by status and date range."""
        now_utc = datetime.now(timezone.utc)
        start = now_utc - timedelta(days=2)
        end = now_utc + timedelta(hours=1)
        result = manager.list_by_filter(
            status=TaskStatus.PENDING,
            due_after=start,
            due_before=end
        )
        assert all(t.status == TaskStatus.PENDING for t in result)
        assert all(t.due_date is not None for t in result)
        assert all(start <= t.due_date <= end for t in result)

    def test_list_by_filter_overdue_and_date_range(self, manager, sample_tasks):
        """Filter by overdue and date range."""
        now_utc = datetime.now(timezone.utc)
        start = now_utc - timedelta(days=2)
        end = now_utc + timedelta(hours=1)
        result = manager.list_by_filter(
            overdue=True,
            due_after=start,
            due_before=end
        )
        assert all(t.is_overdue() for t in result)
        assert all(start <= t.due_date <= end for t in result)

    def test_list_by_filter_status_overdue_date_range(self, manager, sample_tasks):
        """Filter by status, overdue, and date range."""
        now_utc = datetime.now(timezone.utc)
        start = now_utc - timedelta(days=2)
        end = now_utc + timedelta(hours=1)
        result = manager.list_by_filter(
            status=TaskStatus.IN_PROGRESS,
            overdue=True,
            due_after=start,
            due_before=end
        )
        assert all(t.status == TaskStatus.IN_PROGRESS for t in result)
        assert all(t.is_overdue() for t in result)
        assert all(start <= t.due_date <= end for t in result)

    # --- Test no filters (backward compatibility) ---

    def test_list_by_filter_no_filters_returns_all(self, manager, sample_tasks):
        """Calling with no filters returns all tasks (like list_all)."""
        result = manager.list_by_filter()
        assert len(result) == len(sample_tasks)

    def test_list_by_filter_empty_manager(self, manager):
        """list_by_filter on empty manager returns empty list."""
        result = manager.list_by_filter(status=TaskStatus.PENDING)
        assert result == []

    def test_list_by_filter_tasks_without_due_date_excluded_from_date_filters(self, manager):
        """Tasks without due_date are excluded from all date-based filters."""
        t1 = manager.add("No due date")
        t2 = manager.add("Has due date")
        t2.due_date = datetime.now(timezone.utc) + timedelta(days=1)
        manager._persist()

        # Any date filter should exclude t1
        now = datetime.now(timezone.utc)
        result = manager.list_by_filter(due_after=now - timedelta(days=1))
        assert all(t.id != t1.id for t in result)


# ========== Tests for TodoService.list_tasks() ==========

class TestTodoServiceListTasks:
    """Tests for TodoService.list_tasks() with backward compatibility and new parameters."""

    def test_list_tasks_no_args_backward_compatible(self, service):
        """list_tasks() with no args returns all tasks (backward compatible)."""
        service.add_task("A")
        service.add_task("B")
        result = service.list_tasks()
        assert len(result) == 2

    def test_list_tasks_status_only_backward_compatible(self, service):
        """list_tasks(status=X) works as before (backward compatible)."""
        t1 = service.add_task("Pending")
        t2 = service.add_task("Done")
        service.complete_task(t2.id)

        pending = service.list_tasks(status=TaskStatus.PENDING)
        done = service.list_tasks(status=TaskStatus.DONE)

        assert len(pending) == 1
        assert len(done) == 1

    def test_list_tasks_with_due_after(self, service):
        """list_tasks(due_after=X) filters by due_after."""
        now = datetime.now(timezone.utc)
        t1 = service.add_task("Past")
        t1.due_date = now - timedelta(days=1)

        result = service.list_tasks(due_after=now - timedelta(hours=1))
        assert all(t.due_date >= now - timedelta(hours=1) for t in result)

    def test_list_tasks_with_due_before(self, service):
        """list_tasks(due_before=X) filters by due_before."""
        now = datetime.now(timezone.utc)
        t1 = service.add_task("Future")
        t1.due_date = now + timedelta(days=1)

        result = service.list_tasks(due_before=now)
        assert all(t.due_date <= now for t in result)

    def test_list_tasks_with_overdue_true(self, service):
        """list_tasks(overdue=True) filters overdue tasks."""
        now = datetime.now(timezone.utc)
        t1 = service.add_task("Overdue")
        t1.due_date = now - timedelta(days=1)

        result = service.list_tasks(overdue=True)
        assert all(t.is_overdue() for t in result)

    def test_list_tasks_with_overdue_false(self, service):
        """list_tasks(overdue=False) filters non-overdue tasks."""
        now = datetime.now(timezone.utc)
        t1 = service.add_task("Not overdue")
        t1.due_date = now + timedelta(days=1)

        result = service.list_tasks(overdue=False)
        assert all(not t.is_overdue() for t in result)

    def test_list_tasks_validation_due_after_before(self, service):
        """list_tasks raises ValueError if due_after > due_before."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="due_after cannot be after due_before"):
            service.list_tasks(
                due_after=now,
                due_before=now - timedelta(days=1)
            )

    def test_list_tasks_combined_filters(self, service):
        """list_tasks with multiple filters applied together."""
        now = datetime.now(timezone.utc)

        t1 = service.add_task("Pending overdue")
        t1.due_date = now - timedelta(days=1)

        t2 = service.add_task("Done overdue")
        t2.due_date = now - timedelta(days=1)
        service.complete_task(t2.id)

        # Filter: pending, overdue
        result = service.list_tasks(status=TaskStatus.PENDING, overdue=True)
        assert len(result) == 1
        assert result[0].id == t1.id


# ========== Tests for Timezone Utilities ==========

class TestTimezoneUtils:
    """Tests for timezone utility functions."""

    def test_now_in_cest_returns_datetime(self):
        """now_in_cest() returns a datetime object."""
        result = now_in_cest()
        assert isinstance(result, datetime)

    def test_now_in_cest_is_timezone_aware(self):
        """now_in_cest() returns timezone-aware datetime."""
        result = now_in_cest()
        assert result.tzinfo is not None

    def test_now_in_cest_is_paris_timezone(self):
        """now_in_cest() is in Europe/Paris timezone."""
        result = now_in_cest()
        paris_tz = ZoneInfo("Europe/Paris")
        assert result.tzinfo == paris_tz

    def test_now_in_cest_current_time(self):
        """now_in_cest() returns approximately current time."""
        before = datetime.now(ZoneInfo("Europe/Paris"))
        result = now_in_cest()
        after = datetime.now(ZoneInfo("Europe/Paris"))

        assert before <= result <= after or before <= after < result

    def test_is_overdue_cest_with_past_utc_datetime(self):
        """is_overdue_cest returns True for past UTC datetime."""
        past = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert is_overdue_cest(past) is True

    def test_is_overdue_cest_with_future_utc_datetime(self):
        """is_overdue_cest returns False for future UTC datetime."""
        future = datetime(2099, 12, 31, 12, 0, 0, tzinfo=timezone.utc)
        assert is_overdue_cest(future) is False

    def test_is_overdue_cest_with_naive_datetime_assumed_utc(self):
        """is_overdue_cest treats naive datetime as UTC."""
        past = datetime(2020, 1, 1, 12, 0, 0)  # naive, assumed UTC
        assert is_overdue_cest(past) is True

    def test_is_overdue_cest_with_timezone_aware_datetime(self):
        """is_overdue_cest converts timezone-aware datetime correctly."""
        past_cest = datetime(2020, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
        assert is_overdue_cest(past_cest) is True

    def test_is_overdue_cest_boundary_past_second(self):
        """is_overdue_cest returns True just after cutoff."""
        # Very close to current time but definitely in past
        just_past = now_in_cest() - timedelta(seconds=1)
        assert is_overdue_cest(just_past) is True

    def test_is_overdue_cest_boundary_future_second(self):
        """is_overdue_cest returns False just before cutoff."""
        # Very close to current time but definitely in future
        just_future = now_in_cest() + timedelta(seconds=10)
        assert is_overdue_cest(just_future) is False

    def test_utc_to_cest_converts_utc_datetime(self):
        """utc_to_cest converts UTC datetime to CEST."""
        utc_dt = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        result = utc_to_cest(utc_dt)

        assert result.tzinfo == ZoneInfo("Europe/Paris")
        # Same instant in time, just different timezone representation
        assert utc_dt.astimezone(ZoneInfo("Europe/Paris")) == result

    def test_utc_to_cest_with_naive_datetime_assumed_utc(self):
        """utc_to_cest treats naive datetime as UTC."""
        naive_dt = datetime(2026, 5, 3, 12, 0, 0)  # naive, assumed UTC
        result = utc_to_cest(naive_dt)

        assert result.tzinfo == ZoneInfo("Europe/Paris")

    def test_utc_to_cest_with_timezone_aware_datetime(self):
        """utc_to_cest converts timezone-aware datetime from any timezone."""
        paris_tz = ZoneInfo("Europe/Paris")
        paris_dt = datetime(2026, 5, 3, 12, 0, 0, tzinfo=paris_tz)
        result = utc_to_cest(paris_dt)

        assert result.tzinfo == ZoneInfo("Europe/Paris")
        assert result == paris_dt

    def test_utc_to_cest_preserves_instant(self):
        """utc_to_cest preserves the same instant in time."""
        utc_dt = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)
        cest_dt = utc_to_cest(utc_dt)

        # Convert both to UTC and compare
        utc_equiv = cest_dt.astimezone(timezone.utc)
        assert utc_dt == utc_equiv

    def test_utc_to_cest_may_offset_by_one_or_two_hours(self):
        """utc_to_cest offset from UTC is +1 or +2 depending on DST."""
        # May 3 is during CEST (UTC+2)
        utc_dt = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        cest_dt = utc_to_cest(utc_dt)

        # Should be UTC+2 in May (summer)
        offset = cest_dt.utcoffset()
        assert offset in (timedelta(hours=1), timedelta(hours=2))


# ========== Tests for CLI Argument Parsing ==========

class TestCLIArgumentParsing:
    """Tests for CLI argument parsing with new filtering flags."""

    def test_cli_list_with_status_flag(self, cli, capsys):
        """CLI parses --status flag."""
        cli.run(["add", "Task A"])
        cli.run(["list", "--status", "pending"])
        out = capsys.readouterr().out
        assert "Task A" in out

    def test_cli_list_with_due_after_flag(self, cli, capsys):
        """CLI parses --due-after flag."""
        cli.run(["add", "Task A"])
        cli.run(["add", "Task B"])

        # List with due_after in past (should show no tasks with due dates)
        cli.run(["list", "--due-after", "2020-01-01T00:00:00"])
        out = capsys.readouterr().out
        # Should show "No tasks" because tasks have no due_date
        assert "No tasks" in out

    def test_cli_list_with_due_before_flag(self, cli, capsys):
        """CLI parses --due-before flag."""
        cli.run(["add", "Task A"])
        cli.run(["list", "--due-before", "2099-12-31T23:59:59"])
        out = capsys.readouterr().out
        # Should show "No tasks" because tasks have no due_date
        assert "No tasks" in out

    def test_cli_list_with_overdue_flag(self, cli, capsys):
        """CLI parses --overdue flag."""
        cli.run(["add", "Task"])
        cli.run(["list", "--overdue"])
        out = capsys.readouterr().out
        # Should show "No tasks" because task has no due date
        assert "No tasks" in out

    def test_cli_list_with_not_overdue_flag(self, cli, capsys):
        """CLI parses --not-overdue flag."""
        cli.run(["add", "Task"])
        cli.run(["list", "--not-overdue"])
        out = capsys.readouterr().out
        # Should show the task
        assert "Task" in out

    def test_cli_list_overdue_and_not_overdue_mutually_exclusive(self, cli, capsys):
        """CLI rejects both --overdue and --not-overdue together."""
        cli.run(["add", "Task"])
        rc = cli.run(["list", "--overdue", "--not-overdue"])
        out = capsys.readouterr().err
        assert rc == 1
        assert "Cannot use both" in out or "both" in out.lower()

    def test_cli_list_due_after_invalid_format(self, cli, capsys):
        """CLI rejects invalid date format in --due-after."""
        rc = cli.run(["list", "--due-after", "invalid-date"])
        assert rc == 1
        assert "Invalid" in capsys.readouterr().err or "Error" in capsys.readouterr().err

    def test_cli_list_due_before_invalid_format(self, cli, capsys):
        """CLI rejects invalid date format in --due-before."""
        rc = cli.run(["list", "--due-before", "not-a-date"])
        assert rc == 1
        assert "Invalid" in capsys.readouterr().err or "Error" in capsys.readouterr().err

    def test_cli_list_combined_status_and_due_after(self, cli, capsys):
        """CLI handles combined --status and --due-after flags."""
        cli.run(["add", "Task A"])
        cli.run(["add", "Task B"])
        cli.run(["list", "--status", "pending", "--due-after", "2020-01-01T00:00:00"])
        out = capsys.readouterr().out
        # No tasks have due dates, so should show "No tasks"
        assert "No tasks" in out


# ========== Integration Tests ==========

class TestIntegration:
    """Integration tests for full filtering workflow."""

    def test_full_workflow_filter_overdue_pending_tasks(self, service, capsys):
        """Full workflow: add tasks, filter overdue pending tasks."""
        now = datetime.now(timezone.utc)

        # Add tasks
        t1 = service.add_task("Overdue pending")
        t1.due_date = now - timedelta(days=1)

        t2 = service.add_task("Overdue done")
        t2.due_date = now - timedelta(days=1)
        service.complete_task(t2.id)

        t3 = service.add_task("Not overdue")
        t3.due_date = now + timedelta(days=1)

        # Filter: pending + overdue
        result = service.list_tasks(status=TaskStatus.PENDING, overdue=True)

        assert len(result) == 1
        assert result[0].id == t1.id

    def test_full_workflow_cli_with_timezone_aware_dates(self, cli, capsys):
        """Full CLI workflow with timezone-aware ISO8601 dates."""
        # Add task
        cli.run(["add", "Future task"])

        # List with future due_after (should find no tasks)
        future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        cli.run(["list", "--due-after", future_date])
        out = capsys.readouterr().out
        assert "No tasks" in out

    def test_full_workflow_timezone_conversions(self):
        """Verify timezone conversions are consistent."""
        # Create a UTC datetime in the future
        utc_dt = datetime.now(timezone.utc) + timedelta(days=30)

        # Convert to CEST
        cest_dt = utc_to_cest(utc_dt)

        # Check overdue status (should be False for future date)
        is_due = is_overdue_cest(utc_dt)
        assert is_due is False

        # Verify conversion consistency
        assert utc_dt.astimezone(ZoneInfo("Europe/Paris")) == cest_dt


# ========== Edge Cases and Boundary Tests ==========

class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_list_by_filter_tasks_at_exact_boundary_times(self, manager):
        """Test filtering at exact boundary times."""
        now = datetime.now(timezone.utc)

        t1 = manager.add("At boundary")
        t1.due_date = now
        manager._persist()

        # Both due_after and due_before at exact time should include task
        result = manager.list_by_filter(due_after=now, due_before=now)
        assert len(result) == 1

    def test_timezone_conversion_handles_leap_seconds(self):
        """Timezone utilities handle edge case datetime values."""
        # Not a real test of leap seconds, but verifies no crash
        near_midnight = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        result = utc_to_cest(near_midnight)
        assert isinstance(result, datetime)

    def test_list_by_filter_with_empty_string_filters(self, manager):
        """Verify that None filters don't act like empty string filters."""
        manager.add("Task")

        # All None filters should return all tasks
        result = manager.list_by_filter(
            status=None,
            due_after=None,
            due_before=None,
            overdue=None
        )
        assert len(result) == 1

    def test_overdue_check_with_microseconds(self, manager):
        """is_overdue() correctly handles datetimes with microseconds."""
        now = datetime.now(timezone.utc)
        past_micro = now - timedelta(microseconds=1)

        task = manager.add("Micro overdue")
        task.due_date = past_micro
        manager._persist()

        assert task.is_overdue() is True
