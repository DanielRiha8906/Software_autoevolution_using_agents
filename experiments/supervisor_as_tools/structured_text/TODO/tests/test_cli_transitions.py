import pytest
from src.cli.todo_cli import TodoCLI


@pytest.fixture
def cli(tmp_path):
    return TodoCLI(storage_path=str(tmp_path / "tasks.json"))


def _add(cli, title, description=None):
    """Helper to add a task and return success code."""
    args = ["add", title]
    if description:
        args += ["-d", description]
    return cli.run(args)


def _extract_task_id(output):
    """Helper to extract task ID from output (first 8 chars are shown)."""
    # Output format: "Added task <id[:8]>  <title>"
    parts = output.split()
    if len(parts) >= 3:
        return parts[2]  # This is the short ID
    return None


class TestCLIStartCommand:
    def test_start_transitions_pending_to_in_progress(self, cli, capsys):
        """Verify that 'start' command transitions task to IN_PROGRESS."""
        _add(cli, "Start me")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        assert cli.run(["start", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "in_progress" in output

    def test_start_idempotent(self, cli, capsys):
        """Verify that 'start' on an already in-progress task succeeds."""
        _add(cli, "Already started")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        assert cli.run(["start", task_id]) == 0
        assert cli.run(["start", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "in_progress" in output

    def test_start_cannot_move_back_from_done(self, cli, capsys):
        """Verify that 'start' on a DONE task does not transition it back."""
        _add(cli, "Already done")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["start", task_id])
        cli.run(["done", task_id])
        cli.run(["start", task_id])  # Should be no-op
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "done" in output  # Should still be DONE

    def test_start_missing_task_exits_1(self, cli):
        """Verify that 'start' on missing task exits with code 1."""
        assert cli.run(["start", "nonexistent"]) == 1


class TestCLIDoneCommand:
    def test_done_transitions_pending_to_done(self, cli, capsys):
        """Verify that 'done' command transitions task to DONE."""
        _add(cli, "Complete me")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        assert cli.run(["done", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "done" in output

    def test_done_from_in_progress(self, cli, capsys):
        """Verify that 'done' transitions from IN_PROGRESS to DONE."""
        _add(cli, "In progress to done")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["start", task_id])
        assert cli.run(["done", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "done" in output

    def test_done_idempotent(self, cli, capsys):
        """Verify that 'done' on an already done task succeeds."""
        _add(cli, "Already done")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        assert cli.run(["done", task_id]) == 0
        assert cli.run(["done", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "done" in output

    def test_done_missing_task_exits_1(self, cli):
        """Verify that 'done' on missing task exits with code 1."""
        assert cli.run(["done", "nonexistent"]) == 1


class TestCLIReopenCommand:
    def test_reopen_transitions_done_to_pending(self, cli, capsys):
        """Verify that 'reopen' command transitions task to PENDING."""
        _add(cli, "Reopen me")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["done", task_id])
        assert cli.run(["reopen", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "pending" in output

    def test_reopen_from_in_progress(self, cli, capsys):
        """Verify that 'reopen' transitions from IN_PROGRESS to PENDING."""
        _add(cli, "In progress to pending")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["start", task_id])
        assert cli.run(["reopen", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "pending" in output

    def test_reopen_idempotent(self, cli, capsys):
        """Verify that 'reopen' on an already pending task succeeds."""
        _add(cli, "Already pending")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        assert cli.run(["reopen", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "pending" in output

    def test_reopen_missing_task_exits_1(self, cli):
        """Verify that 'reopen' on missing task exits with code 1."""
        assert cli.run(["reopen", "nonexistent"]) == 1


class TestCLIWorkflow:
    def test_full_cli_workflow(self, cli, capsys):
        """Test a complete CLI workflow: add -> start -> done -> reopen."""
        _add(cli, "Workflow task")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        # Verify initial state
        cli.run(["show", task_id])
        assert "pending" in capsys.readouterr().out

        # Start
        assert cli.run(["start", task_id]) == 0
        cli.run(["show", task_id])
        assert "in_progress" in capsys.readouterr().out

        # Complete
        assert cli.run(["done", task_id]) == 0
        cli.run(["show", task_id])
        assert "done" in capsys.readouterr().out

        # Reopen
        assert cli.run(["reopen", task_id]) == 0
        cli.run(["show", task_id])
        assert "pending" in capsys.readouterr().out

    def test_multiple_task_workflow(self, cli, capsys):
        """Test CLI workflow with multiple tasks."""
        _add(cli, "Task 1")
        _add(cli, "Task 2")
        _add(cli, "Task 3")

        cli.run(["list"])
        lines = capsys.readouterr().out.split("\n")
        task_ids = []
        for line in lines:
            if "[ ]" in line:  # Pending task
                task_ids.append(line.split()[2])
        assert len(task_ids) == 3

        # Transition tasks to different states
        cli.run(["start", task_ids[0]])
        cli.run(["done", task_ids[1]])

        # Check list filtering
        cli.run(["list"])
        output = capsys.readouterr().out
        # Output should contain all 3 tasks with different symbols
        assert "[ ]" in output  # pending (task 3)
        assert "[~]" in output  # in_progress (task 1)
        assert "[x]" in output  # done (task 2)

    def test_status_symbols_in_list_after_transitions(self, cli, capsys):
        """Verify that list output shows correct status symbols after transitions."""
        _add(cli, "Symbol test")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        # Pending
        cli.run(["list"])
        output = capsys.readouterr().out
        assert "[ ]" in output

        # In progress
        cli.run(["start", task_id])
        cli.run(["list"])
        output = capsys.readouterr().out
        assert "[~]" in output
        assert "[ ]" not in output

        # Done
        cli.run(["done", task_id])
        cli.run(["list"])
        output = capsys.readouterr().out
        assert "[x]" in output
        assert "[~]" not in output


class TestCLITransitionMessages:
    def test_start_prints_started_message(self, cli, capsys):
        """Verify that 'start' prints a success message."""
        _add(cli, "Message test")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["start", task_id])
        output = capsys.readouterr().out
        assert "Started" in output

    def test_done_prints_completed_message(self, cli, capsys):
        """Verify that 'done' prints a success message."""
        _add(cli, "Message test")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["done", task_id])
        output = capsys.readouterr().out
        assert "Completed" in output

    def test_reopen_prints_reopened_message(self, cli, capsys):
        """Verify that 'reopen' prints a success message."""
        _add(cli, "Message test")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["done", task_id])
        capsys.readouterr()  # Clear output
        cli.run(["reopen", task_id])
        output = capsys.readouterr().out
        assert "Reopened" in output


class TestCLIPrefixMatching:
    def test_start_with_task_id_prefix(self, cli, capsys):
        """Verify that 'start' works with task ID prefix (unique matching)."""
        _add(cli, "Prefix test")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]  # 8-char prefix

        # Should work with the prefix
        assert cli.run(["start", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "in_progress" in output

    def test_done_with_task_id_prefix(self, cli, capsys):
        """Verify that 'done' works with task ID prefix."""
        _add(cli, "Prefix test")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        assert cli.run(["done", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "done" in output

    def test_reopen_with_task_id_prefix(self, cli, capsys):
        """Verify that 'reopen' works with task ID prefix."""
        _add(cli, "Prefix test")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        cli.run(["done", task_id])
        assert cli.run(["reopen", task_id]) == 0
        cli.run(["show", task_id])
        output = capsys.readouterr().out
        assert "pending" in output


class TestCLIPersistence:
    def test_transitions_persist_across_cli_instances(self, cli, capsys, tmp_path):
        """Verify that transitions persist across different CLI instances."""
        _add(cli, "Persistence test")
        cli.run(["list"])
        task_id = capsys.readouterr().out.split()[2]

        # Transition in first instance
        cli.run(["start", task_id])
        cli.run(["done", task_id])

        # Create new CLI instance using same storage
        cli2 = TodoCLI(storage_path=str(tmp_path / "tasks.json"))
        cli2.run(["show", task_id])
        output = capsys.readouterr().out
        assert "done" in output
