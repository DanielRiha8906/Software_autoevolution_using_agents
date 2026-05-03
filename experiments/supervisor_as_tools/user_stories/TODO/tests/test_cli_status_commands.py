import pytest
from datetime import datetime, timezone, timedelta
from src.cli.todo_cli import TodoCLI


@pytest.fixture
def cli(tmp_path):
    """Create a TodoCLI with temporary storage."""
    return TodoCLI(str(tmp_path / "tasks.json"))


class TestMarkInProgressCommand:
    """Test mark-in-progress CLI command."""

    def test_mark_in_progress_command(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Mark as in-progress
        result = cli.run(["mark-in-progress", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "Started" in captured.out

        # Verify status
        cli.run(["show", task_id])
        captured = capsys.readouterr()
        assert "in_progress" in captured.out


class TestMarkDoneCommand:
    """Test mark-done CLI command."""

    def test_mark_done_command(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Mark as done
        result = cli.run(["mark-done", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "Completed" in captured.out

        # Verify status
        cli.run(["show", task_id])
        captured = capsys.readouterr()
        assert "done" in captured.out


class TestIsPendingCommand:
    """Test is-pending CLI command."""

    def test_is_pending_true(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Check is-pending
        result = cli.run(["is-pending", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "true" in captured.out

    def test_is_pending_false(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Mark as done
        cli.run(["mark-done", task_id])

        # Check is-pending
        result = cli.run(["is-pending", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "false" in captured.out


class TestIsInProgressCommand:
    """Test is-in-progress CLI command."""

    def test_is_in_progress_true(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Mark as in-progress
        cli.run(["mark-in-progress", task_id])

        # Check is-in-progress
        result = cli.run(["is-in-progress", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "true" in captured.out

    def test_is_in_progress_false(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Check is-in-progress
        result = cli.run(["is-in-progress", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "false" in captured.out


class TestIsCompletedCommand:
    """Test is-completed CLI command."""

    def test_is_completed_true(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Mark as done
        cli.run(["mark-done", task_id])

        # Check is-completed
        result = cli.run(["is-completed", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "true" in captured.out

    def test_is_completed_false(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Check is-completed
        result = cli.run(["is-completed", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "false" in captured.out


class TestIsOverdueCommand:
    """Test is-overdue CLI command."""

    def test_is_overdue_true(self, cli, capsys):
        # Add a task with past due date
        past = datetime.now(timezone.utc) - timedelta(days=1)
        cli.run(["add", "Test task", "--due-date", past.isoformat()])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Check is-overdue
        result = cli.run(["is-overdue", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "true" in captured.out

    def test_is_overdue_false(self, cli, capsys):
        # Add a task
        cli.run(["add", "Test task"])

        # List to get the ID
        cli.run(["list"])
        captured = capsys.readouterr()
        task_id = captured.out.split()[2]

        # Check is-overdue
        result = cli.run(["is-overdue", task_id])
        assert result == 0
        captured = capsys.readouterr()
        assert "false" in captured.out
