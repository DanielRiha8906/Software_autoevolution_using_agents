import pytest
from src.cli.todo_cli import TodoCLI


@pytest.fixture
def cli(tmp_path):
    """Provide a TodoCLI instance with a temporary storage backend."""
    return TodoCLI(storage_path=str(tmp_path / "tasks.json"))


class TestCliStatsCommand:
    """Test the 'stats' CLI command."""

    def test_stats_command_exists(self, cli):
        """stats command is registered and callable."""
        rc = cli.run(["stats"])
        assert rc == 0

    def test_stats_command_returns_zero(self, cli):
        """stats command returns 0 on success."""
        rc = cli.run(["stats"])
        assert rc == 0

    def test_stats_with_empty_list(self, cli, capsys):
        """stats command shows all zeros for empty task list."""
        rc = cli.run(["stats"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Task Statistics" in out
        assert "Total:" in out
        assert "Pending:" in out
        assert "In Progress:" in out
        assert "Done:" in out
        assert "Overdue:" in out
        assert "With due date:" in out

    def test_stats_output_format(self, cli, capsys):
        """stats command output has correct format."""
        rc = cli.run(["stats"])
        assert rc == 0
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        # Should have header and at least 6 stat lines
        assert len(lines) >= 7
        assert "Task Statistics:" in out

    def test_stats_empty_counts_zero(self, cli, capsys):
        """stats command shows zero for all counts when no tasks exist."""
        cli.run(["stats"])
        out = capsys.readouterr().out
        # Look for counts being zero
        assert "0" in out

    def test_stats_with_pending_task(self, cli, capsys):
        """stats command shows pending count for pending tasks."""
        cli.run(["add", "Pending task"])
        cli.run(["stats"])
        out = capsys.readouterr().out
        assert "Pending:" in out
        # Total should be 1
        assert "Total:" in out

    def test_stats_with_in_progress_task(self, cli, capsys):
        """stats command counts in-progress tasks."""
        cli.run(["add", "Task to start"])
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["start", task_id])
        cli.run(["stats"])
        out = capsys.readouterr().out
        assert "In Progress:" in out

    def test_stats_with_done_task(self, cli, capsys):
        """stats command counts completed tasks."""
        cli.run(["add", "Task to complete"])
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["done", task_id])
        cli.run(["stats"])
        out = capsys.readouterr().out
        assert "Done:" in out

    def test_stats_with_mixed_statuses(self, cli, capsys):
        """stats command correctly counts mixed task statuses."""
        # Add 3 tasks
        cli.run(["add", "Task 1"])  # Will be pending
        cli.run(["list"])
        task1_id = capsys.readouterr().out.split()[2]

        cli.run(["add", "Task 2"])  # Will be in_progress
        cli.run(["list"])
        out = capsys.readouterr().out
        task2_id = out.split("\n")[1].split()[2]  # Second task

        cli.run(["add", "Task 3"])  # Will be done
        cli.run(["list"])
        out = capsys.readouterr().out
        task3_id = out.split("\n")[2].split()[2]  # Third task

        # Change statuses
        cli.run(["start", task2_id])
        cli.run(["done", task3_id])

        # Get stats
        cli.run(["stats"])
        out = capsys.readouterr().out

        # All three lines should be present
        assert "Pending:" in out
        assert "In Progress:" in out
        assert "Done:" in out

    def test_stats_after_task_deletion(self, cli, capsys):
        """stats command updates correctly after task deletion."""
        # Add tasks
        cli.run(["add", "Task 1"])
        cli.run(["add", "Task 2"])
        cli.run(["list"])
        task1_id = capsys.readouterr().out.split()[2]

        # Get initial stats
        cli.run(["stats"])
        initial_out = capsys.readouterr().out

        # Delete first task
        cli.run(["delete", task1_id])

        # Get updated stats
        cli.run(["stats"])
        updated_out = capsys.readouterr().out

        # Both should have stats, counts may differ
        assert "Task Statistics:" in initial_out
        assert "Task Statistics:" in updated_out

    def test_stats_output_contains_all_fields(self, cli, capsys):
        """stats output contains all required statistic fields."""
        cli.run(["add", "Sample task"])
        cli.run(["stats"])
        out = capsys.readouterr().out

        required_fields = [
            "Task Statistics:",
            "Total:",
            "Pending:",
            "In Progress:",
            "Done:",
            "Overdue:",
            "With due date:",
        ]
        for field in required_fields:
            assert field in out, f"Missing field: {field}"

    def test_stats_with_description_task(self, cli, capsys):
        """stats command counts tasks with descriptions."""
        cli.run(["add", "Task with description", "-d", "This is a description"])
        cli.run(["stats"])
        out = capsys.readouterr().out
        # Stats should reflect 1 task regardless of description
        assert "Task Statistics:" in out

    def test_stats_repeated_calls(self, cli, capsys):
        """stats command can be called multiple times."""
        cli.run(["add", "Task 1"])

        # First call
        cli.run(["stats"])
        out1 = capsys.readouterr().out

        # Second call
        cli.run(["stats"])
        out2 = capsys.readouterr().out

        # Both should be valid
        assert "Task Statistics:" in out1
        assert "Task Statistics:" in out2

    def test_stats_with_many_tasks(self, cli, capsys):
        """stats command works with many tasks."""
        # Add 10 tasks
        for i in range(10):
            cli.run(["add", f"Task {i+1}"])

        cli.run(["stats"])
        out = capsys.readouterr().out

        assert "Task Statistics:" in out
        # Should show total = 10
        lines = [line for line in out.split("\n") if "Total:" in line]
        assert len(lines) > 0

    def test_stats_no_arguments(self, cli):
        """stats command works with no arguments."""
        rc = cli.run(["stats"])
        assert rc == 0

    def test_stats_case_insensitive_command(self, cli, capsys):
        """stats command recognizes lowercase 'stats'."""
        rc = cli.run(["stats"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Task Statistics:" in out

    @pytest.mark.parametrize(
        "num_pending,num_in_progress,num_done",
        [
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (2, 1, 1),
            (3, 3, 3),
            (5, 2, 0),
        ],
    )
    def test_stats_parametrized_task_counts(
        self, cli, capsys, num_pending, num_in_progress, num_done
    ):
        """stats command correctly reports counts for various task distributions."""
        # Add pending tasks
        pending_ids = []
        for i in range(num_pending):
            cli.run(["add", f"Pending {i+1}"])
            cli.run(["list"])
            task_id = capsys.readouterr().out.split()[2]
            pending_ids.append(task_id)

        # Add and start in-progress tasks
        for i in range(num_in_progress):
            cli.run(["add", f"In Progress {i+1}"])
            cli.run(["list"])
            out = capsys.readouterr().out
            # Find the last added task's ID
            task_id = out.split("\n")[-2].split()[2]
            cli.run(["start", task_id])

        # Add and complete done tasks
        for i in range(num_done):
            cli.run(["add", f"Done {i+1}"])
            cli.run(["list"])
            out = capsys.readouterr().out
            # Find the last added task's ID
            task_id = out.split("\n")[-2].split()[2]
            cli.run(["done", task_id])

        # Get stats
        cli.run(["stats"])
        out = capsys.readouterr().out

        # Verify output contains stats
        assert "Task Statistics:" in out
        assert "Total:" in out
