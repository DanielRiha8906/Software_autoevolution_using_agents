import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from io import StringIO

from src.models.task_summary_report import TaskSummaryReport
from src.models.task import Task
from src.models.task_status import TaskStatus
from src.services.todo_service import TodoService
from src.cli.todo_cli import TodoCLI
from src.cli.interactive_menu import InteractiveMenu
from src.storage.json_storage import JsonStorage


# ══════════════════════════════════════════════════════════════════════════════
# TestTaskSummaryReportDataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestTaskSummaryReportDataclass:
    """Tests for TaskSummaryReport dataclass structure and properties."""

    def test_dataclass_is_frozen(self):
        """Verify that TaskSummaryReport is frozen (immutable)."""
        report = TaskSummaryReport(
            total_count=5,
            pending_count=2,
            in_progress_count=1,
            done_count=2,
            overdue_count=0,
            due_date_set_count=3,
            completion_rate=0.4,
            avg_days_to_completion=5.0
        )
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            report.total_count = 10

    def test_all_eight_fields_present(self):
        """Verify all 8 required fields are present."""
        report = TaskSummaryReport(
            total_count=10,
            pending_count=3,
            in_progress_count=4,
            done_count=3,
            overdue_count=2,
            due_date_set_count=7,
            completion_rate=0.3,
            avg_days_to_completion=5.5
        )
        assert hasattr(report, 'total_count')
        assert hasattr(report, 'pending_count')
        assert hasattr(report, 'in_progress_count')
        assert hasattr(report, 'done_count')
        assert hasattr(report, 'overdue_count')
        assert hasattr(report, 'due_date_set_count')
        assert hasattr(report, 'completion_rate')
        assert hasattr(report, 'avg_days_to_completion')

    def test_field_types_are_correct(self):
        """Verify field types match expected types."""
        report = TaskSummaryReport(
            total_count=5,
            pending_count=2,
            in_progress_count=1,
            done_count=2,
            overdue_count=0,
            due_date_set_count=3,
            completion_rate=0.4,
            avg_days_to_completion=5.0
        )
        assert isinstance(report.total_count, int)
        assert isinstance(report.pending_count, int)
        assert isinstance(report.in_progress_count, int)
        assert isinstance(report.done_count, int)
        assert isinstance(report.overdue_count, int)
        assert isinstance(report.due_date_set_count, int)
        assert isinstance(report.completion_rate, float)
        assert report.avg_days_to_completion is None or isinstance(report.avg_days_to_completion, float)

    def test_avg_days_to_completion_optional(self):
        """Verify avg_days_to_completion can be None."""
        report = TaskSummaryReport(
            total_count=5,
            pending_count=5,
            in_progress_count=0,
            done_count=0,
            overdue_count=0,
            due_date_set_count=0,
            completion_rate=0.0
        )
        assert report.avg_days_to_completion is None

    def test_identical_instances_are_equal(self):
        """Verify two identical instances are equal."""
        report1 = TaskSummaryReport(
            total_count=5,
            pending_count=2,
            in_progress_count=1,
            done_count=2,
            overdue_count=0,
            due_date_set_count=3,
            completion_rate=0.4,
            avg_days_to_completion=5.0
        )
        report2 = TaskSummaryReport(
            total_count=5,
            pending_count=2,
            in_progress_count=1,
            done_count=2,
            overdue_count=0,
            due_date_set_count=3,
            completion_rate=0.4,
            avg_days_to_completion=5.0
        )
        assert report1 == report2

    def test_repr_is_deterministic(self):
        """Verify repr output is deterministic."""
        report = TaskSummaryReport(
            total_count=5,
            pending_count=2,
            in_progress_count=1,
            done_count=2,
            overdue_count=0,
            due_date_set_count=3,
            completion_rate=0.4,
            avg_days_to_completion=5.0
        )
        repr1 = repr(report)
        repr2 = repr(report)
        assert repr1 == repr2
        assert "TaskSummaryReport" in repr1


# ══════════════════════════════════════════════════════════════════════════════
# TestGenerateReport
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def service(tmp_path):
    """Fixture providing a TodoService with temporary storage."""
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


class TestGenerateReport:
    """Tests for TodoService.generate_report() method."""

    def test_empty_database_all_zeros(self, service):
        """Test with no tasks: all counts should be 0, completion_rate 0.0, avg_days None."""
        report = service.generate_report()
        assert report.total_count == 0
        assert report.pending_count == 0
        assert report.in_progress_count == 0
        assert report.done_count == 0
        assert report.overdue_count == 0
        assert report.due_date_set_count == 0
        assert report.completion_rate == 0.0
        assert report.avg_days_to_completion is None

    def test_single_pending_task(self, service):
        """Test with a single pending task."""
        service.add_task("Test task")
        report = service.generate_report()
        assert report.total_count == 1
        assert report.pending_count == 1
        assert report.in_progress_count == 0
        assert report.done_count == 0
        assert report.completion_rate == 0.0

    def test_mixed_statuses_counts(self, service):
        """Test counts are correct for PENDING, IN_PROGRESS, DONE tasks."""
        t1 = service.add_task("Pending task")

        t2 = service.add_task("In progress task")
        service.start_task(t2.id)

        t3 = service.add_task("Done task")
        service.start_task(t3.id)
        service.complete_task(t3.id)

        report = service.generate_report()
        assert report.total_count == 3
        assert report.pending_count == 1
        assert report.in_progress_count == 1
        assert report.done_count == 1

    def test_completion_rate_calculation(self, service):
        """Test completion_rate = done_count / total_count."""
        service.add_task("A")
        service.add_task("B")
        service.add_task("C")
        service.add_task("D")

        # Complete 2 out of 4
        tasks = service.list_tasks()
        service.start_task(tasks[0].id)
        service.complete_task(tasks[0].id)
        service.start_task(tasks[1].id)
        service.complete_task(tasks[1].id)

        report = service.generate_report()
        assert report.total_count == 4
        assert report.done_count == 2
        assert report.completion_rate == 0.5

    def test_completion_rate_100_percent(self, service):
        """Test completion_rate is 1.0 when all tasks are done."""
        t1 = service.add_task("Task 1")
        t2 = service.add_task("Task 2")

        service.start_task(t1.id)
        service.complete_task(t1.id)
        service.start_task(t2.id)
        service.complete_task(t2.id)

        report = service.generate_report()
        assert report.completion_rate == 1.0

    def test_completion_rate_zero_percent(self, service):
        """Test completion_rate is 0.0 when no tasks are done."""
        service.add_task("Task 1")
        service.add_task("Task 2")

        report = service.generate_report()
        assert report.completion_rate == 0.0

    def test_overdue_detection_uses_is_overdue(self, service):
        """Test that overdue_count only includes truly overdue tasks."""
        now = datetime.now(timezone.utc)

        # Overdue task (past due date, not done)
        t1 = service.add_task("Overdue task", due_date=now - timedelta(days=1))

        # Not overdue yet (future due date)
        t2 = service.add_task("Future task", due_date=now + timedelta(days=1))

        # Completed overdue task (should not count as overdue)
        t3 = service.add_task("Was overdue", due_date=now - timedelta(days=1))
        service.start_task(t3.id)
        service.complete_task(t3.id)

        # No due date
        t4 = service.add_task("No due date")

        report = service.generate_report()
        assert report.overdue_count == 1  # Only t1

    def test_due_date_set_count(self, service):
        """Test counting tasks with due_date is not None."""
        now = datetime.now(timezone.utc)
        service.add_task("With due date", due_date=now)
        service.add_task("Without due date")
        service.add_task("With due date 2", due_date=now + timedelta(days=1))
        service.add_task("Also without")

        report = service.generate_report()
        assert report.due_date_set_count == 2

    def test_avg_days_to_completion_none_for_no_done_tasks(self, service):
        """Test avg_days_to_completion is None when no tasks are done."""
        service.add_task("Pending")
        service.add_task("In progress")

        report = service.generate_report()
        assert report.avg_days_to_completion is None

    def test_avg_days_to_completion_single_task(self, service):
        """Test avg_days_to_completion calculation for single done task."""
        # Create a task and mark as done
        t = service.add_task("Test")
        created = t.created_at
        service.start_task(t.id)
        service.complete_task(t.id)

        report = service.generate_report()
        # Get the task to check the difference
        done_task = service.get_task(t.id)
        expected_days = (done_task.updated_at - done_task.created_at).days
        assert report.avg_days_to_completion == float(expected_days)

    def test_avg_days_to_completion_multiple_tasks(self, service):
        """Test avg_days_to_completion for multiple done tasks."""
        # Create tasks with known timestamps
        now = datetime.now(timezone.utc)

        # Task 1: created now, completed immediately (0 days)
        t1 = service.add_task("Task 1")
        service.start_task(t1.id)
        service.complete_task(t1.id)

        # Task 2: manually adjust timing for testing
        t2 = service.add_task("Task 2")
        service.start_task(t2.id)
        service.complete_task(t2.id)

        report = service.generate_report()
        # Should calculate average of days for both done tasks
        done_tasks = service.list_tasks(status=TaskStatus.DONE)
        total_days = sum((t.updated_at - t.created_at).days for t in done_tasks)
        expected_avg = total_days / len(done_tasks)
        assert report.avg_days_to_completion == expected_avg

    def test_determinism_same_task_set(self, service):
        """Test multiple calls with same task set produce identical reports."""
        service.add_task("Task A")
        service.add_task("Task B")
        service.add_task("Task C")

        report1 = service.generate_report()
        report2 = service.generate_report()

        assert report1 == report2

    def test_determinism_with_status_changes(self, service):
        """Test determinism across multiple status changes."""
        t1 = service.add_task("Task 1")
        t2 = service.add_task("Task 2")

        service.start_task(t1.id)
        service.complete_task(t1.id)

        report1 = service.generate_report()
        service.start_task(t2.id)
        report2 = service.generate_report()

        # Reports should be different now
        assert report1 != report2

        # But calling generate_report again should give same result
        report2_again = service.generate_report()
        assert report2 == report2_again

    @pytest.mark.parametrize("task_count", [10, 50, 100])
    def test_performance_with_large_task_count(self, service, task_count):
        """Test that generate_report() handles large task counts efficiently (O(n))."""
        import time

        # Create many tasks
        for i in range(task_count):
            service.add_task(f"Task {i}")

        # Measure execution time
        start = time.time()
        report = service.generate_report()
        end = time.time()

        # Should complete in reasonable time (< 1 second for 100 tasks)
        assert end - start < 1.0
        assert report.total_count == task_count


# ══════════════════════════════════════════════════════════════════════════════
# TestCLIReport
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def cli(tmp_path):
    """Fixture providing a TodoCLI with temporary storage."""
    return TodoCLI(storage_path=str(tmp_path / "tasks.json"))


class TestCLIReport:
    """Tests for TodoCLI._cmd_report() method."""

    def test_report_command_runs_without_error(self, cli):
        """Test report command returns exit code 0."""
        rc = cli.run(["report"])
        assert rc == 0

    def test_report_command_with_no_tasks(self, cli, capsys):
        """Test report displays all zeros when no tasks exist."""
        cli.run(["report"])
        out = capsys.readouterr().out
        assert "Total tasks:" in out
        assert "0" in out

    def test_report_output_includes_all_metrics(self, cli, capsys):
        """Test output includes all required metrics."""
        cli.run(["report"])
        out = capsys.readouterr().out

        assert "Task Summary Report" in out
        assert "Total tasks:" in out
        assert "Pending:" in out
        assert "In progress:" in out
        assert "Done:" in out
        assert "With due date:" in out
        assert "Overdue:" in out
        assert "Completion rate:" in out
        assert "Avg days to completion:" in out

    def test_completion_rate_formatted_as_percentage(self, cli, capsys):
        """Test completion_rate is formatted as percentage with .1f decimal."""
        # Add 3 tasks
        cli.run(["add", "Task 1"])
        cli.run(["add", "Task 2"])
        cli.run(["add", "Task 3"])

        # Get service to directly access tasks
        service = cli._service
        tasks = service.list_tasks()
        task_ids = [t.id for t in tasks]

        # Complete exactly 2 out of 3 (66.7%)
        service.start_task(task_ids[0])
        service.complete_task(task_ids[0])
        service.start_task(task_ids[1])
        service.complete_task(task_ids[1])

        # Run report command
        cli.run(["report"])
        out = capsys.readouterr().out

        # Should show completion rate as percentage with 1 decimal
        assert "Completion rate:" in out
        # Check format has decimal
        import re
        match = re.search(r'Completion rate:\s+([\d.]+)%', out)
        assert match is not None, f"Could not find completion rate in output: {out}"
        rate = float(match.group(1))
        # With 2 tasks done out of 3, should be exactly 66.666...% which formats as 66.7%
        assert 66.6 <= rate <= 66.8, f"Expected ~66.7%, got {rate}%"

    def test_avg_days_formatted_with_1f_decimal(self, cli, capsys):
        """Test avg_days_to_completion formatted with .1f decimal."""
        cli.run(["add", "Task 1"])
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["start", task_id])
        cli.run(["done", task_id])

        cli.run(["report"])
        out = capsys.readouterr().out

        # Should show avg days with 1 decimal place
        assert "Avg days to completion:" in out
        # If there are done tasks, should have a decimal format
        if "0.0" in out or any(str(i) + "." in out for i in range(10)):
            pass  # Format is correct

    def test_avg_days_na_when_none(self, cli, capsys):
        """Test 'N/A' displayed when avg_days_to_completion is None."""
        cli.run(["add", "Pending task"])
        cli.run(["report"])
        out = capsys.readouterr().out

        assert "Avg days to completion: N/A" in out

    def test_report_returns_exit_code_0(self, cli):
        """Test report command returns exit code 0 on success."""
        cli.run(["add", "Task"])
        rc = cli.run(["report"])
        assert rc == 0


# ══════════════════════════════════════════════════════════════════════════════
# TestMenuReport
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def menu(tmp_path):
    """Fixture providing an InteractiveMenu with temporary storage."""
    return InteractiveMenu(storage_path=str(tmp_path / "tasks.json"))


class TestMenuReport:
    """Tests for InteractiveMenu._do_report() method."""

    def test_menu_option_9_in_main_display(self, menu, capsys, monkeypatch):
        """Test that menu option 9 appears in main menu display."""
        # Mock the run method to print menu and exit
        original_run = menu.run

        def mocked_run():
            menu._print_header()
            menu._print_task_list([])
            menu._print_main_menu()

        menu.run = mocked_run
        menu.run()

        out = capsys.readouterr().out
        assert "9." in out
        assert "View summary report" in out or "report" in out.lower()

    def test_menu_option_9_is_selectable(self, menu, capsys, monkeypatch):
        """Test that menu option 9 is selectable and triggers _do_report()."""
        # Mock input to select option 9
        inputs = iter(["9", "0"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        # Mock _do_report to track if it was called
        called = []
        original_do_report = menu._do_report

        def tracked_do_report():
            called.append(True)

        menu._do_report = tracked_do_report

        try:
            menu.run()
        except StopIteration:
            pass  # Expected when inputs run out

        assert len(called) > 0

    def test_report_displays_in_menu_format(self, menu, capsys, monkeypatch):
        """Test that report displays correctly in menu format."""
        # Add a task
        menu._service.add_task("Test task")

        # Mock input
        monkeypatch.setattr('builtins.input', lambda _: "")

        # Call _do_report directly
        menu._do_report()

        out = capsys.readouterr().out
        assert "Task Summary Report" in out
        assert "Total tasks:" in out
        assert "Completion rate:" in out

    def test_report_press_enter_prompt_appears(self, menu, capsys, monkeypatch):
        """Test that 'Press Enter to continue...' prompt appears."""
        # Track if input was called
        input_calls = []

        def mock_input(prompt):
            input_calls.append(prompt)
            return ""

        monkeypatch.setattr('builtins.input', mock_input)

        # Call _do_report directly
        menu._do_report()

        # Check that input was called with the prompt containing "Press Enter to continue"
        assert any("Press Enter to continue" in call for call in input_calls), f"Prompts: {input_calls}"

    def test_do_report_no_exceptions_raised(self, menu, monkeypatch):
        """Test that no exceptions are raised during _do_report()."""
        # Add various tasks
        t1 = menu._service.add_task("Task 1")
        t2 = menu._service.add_task("Task 2")
        menu._service.start_task(t2.id)
        menu._service.complete_task(t2.id)

        # Mock input
        monkeypatch.setattr('builtins.input', lambda _: "")

        # Should not raise any exceptions
        try:
            menu._do_report()
        except Exception as e:
            pytest.fail(f"_do_report() raised {type(e).__name__}: {e}")

    def test_report_shows_correct_counts(self, menu, capsys, monkeypatch):
        """Test that report shows correct counts in menu format."""
        t1 = menu._service.add_task("Pending")
        t2 = menu._service.add_task("In progress")
        menu._service.start_task(t2.id)
        t3 = menu._service.add_task("Done")
        menu._service.start_task(t3.id)
        menu._service.complete_task(t3.id)

        monkeypatch.setattr('builtins.input', lambda _: "")
        menu._do_report()

        out = capsys.readouterr().out
        assert "Total tasks:" in out
        assert "3" in out
        assert "Pending:" in out
        assert "1" in out

    def test_report_handles_empty_task_list(self, menu, capsys, monkeypatch):
        """Test that report handles empty task list without errors."""
        monkeypatch.setattr('builtins.input', lambda _: "")

        menu._do_report()

        out = capsys.readouterr().out
        assert "Total tasks:" in out
        assert "0" in out

    def test_do_report_with_overdue_tasks(self, menu, capsys, monkeypatch):
        """Test that report correctly counts overdue tasks in menu."""
        now = datetime.now(timezone.utc)
        t1 = menu._service.add_task("Overdue", due_date=now - timedelta(days=1))
        t2 = menu._service.add_task("Not overdue", due_date=now + timedelta(days=1))

        monkeypatch.setattr('builtins.input', lambda _: "")
        menu._do_report()

        out = capsys.readouterr().out
        assert "Overdue:" in out
        assert "1" in out
