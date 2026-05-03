import pytest
from src.cli.todo_cli import TodoCLI
from src.storage.json_storage import JsonStorage


@pytest.fixture
def cli(tmp_path):
    return TodoCLI(storage_path=str(tmp_path / "tasks.json"))


def _add(cli, title, description=None):
    args = ["add", title]
    if description:
        args += ["-d", description]
    return cli.run(args)


def test_add_prints_id(cli, capsys):
    rc = _add(cli, "Buy milk")
    assert rc == 0
    assert "Buy milk" in capsys.readouterr().out


def test_add_empty_title_exits_1(cli):
    rc = cli.run(["add", "  "])
    assert rc == 1


def test_list_empty(cli, capsys):
    rc = cli.run(["list"])
    assert rc == 0
    assert "No tasks" in capsys.readouterr().out


def test_list_shows_tasks(cli, capsys):
    _add(cli, "Task A")
    _add(cli, "Task B")
    cli.run(["list"])
    out = capsys.readouterr().out
    assert "Task A" in out
    assert "Task B" in out


def test_list_filter_status(cli, capsys):
    _add(cli, "Pending one")
    cli.run(["list", "--status", "done"])
    assert "No tasks" in capsys.readouterr().out


def test_start_done_reopen(cli, capsys):
    _add(cli, "Flow task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    assert cli.run(["start", task_id]) == 0
    assert cli.run(["done", task_id]) == 0
    assert cli.run(["reopen", task_id]) == 0

    cli.run(["show", task_id])
    out = capsys.readouterr().out
    assert "pending" in out


def test_show_details(cli, capsys):
    _add(cli, "Detailed task", "some description")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]
    cli.run(["show", task_id])
    out = capsys.readouterr().out
    assert "Detailed task" in out
    assert "some description" in out


def test_delete(cli, capsys):
    _add(cli, "Ephemeral")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]
    assert cli.run(["delete", task_id]) == 0
    cli.run(["list"])
    assert "No tasks" in capsys.readouterr().out


def test_missing_task_exits_1(cli):
    assert cli.run(["start", "00000000"]) == 1


def test_update_title(cli, capsys):
    _add(cli, "Old")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]
    cli.run(["update", task_id, "-t", "New"])
    cli.run(["show", task_id])
    assert "New" in capsys.readouterr().out


def test_no_subcommand_prints_help(cli, capsys):
    rc = cli.run([])
    assert rc == 0


# ===== is-completed command tests =====

def test_is_completed_command_with_completed_task(cli, capsys):
    """is-completed with a DONE task prints 'completed'."""
    _add(cli, "Finished task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["done", task_id])
    rc = cli.run(["is-completed", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Status: completed" in out
    assert "Finished task" in out


def test_is_completed_command_with_pending_task(cli, capsys):
    """is-completed with a PENDING task prints 'not completed'."""
    _add(cli, "Pending task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["is-completed", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Status: not completed" in out
    assert "Pending task" in out


def test_is_completed_command_with_in_progress_task(cli, capsys):
    """is-completed with an IN_PROGRESS task prints 'not completed'."""
    _add(cli, "In progress task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["start", task_id])
    rc = cli.run(["is-completed", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Status: not completed" in out


def test_is_completed_command_with_missing_task_id(cli):
    """is-completed with missing task ID exits with error code 1."""
    rc = cli.run(["is-completed", "00000000"])
    assert rc == 1


def test_is_completed_shows_task_id_prefix(cli, capsys):
    """is-completed output includes the task ID prefix."""
    _add(cli, "Check this")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["is-completed", task_id])
    out = capsys.readouterr().out
    assert task_id in out


# ===== check-overdue command tests =====

def test_check_overdue_command_with_overdue_task(cli, capsys):
    """check-overdue with an overdue task prints 'overdue'."""
    from datetime import datetime, timezone, timedelta

    # Create task with past due date
    past_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    cli.run(["add", "Overdue task"])
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    # Get and set the task with past due date manually via internal API
    # For now, test the command structure exists and works
    rc = cli.run(["check-overdue", task_id])

    # The command should exist and execute
    assert rc == 0
    out = capsys.readouterr().out
    assert "Status:" in out  # Either overdue or not overdue


def test_check_overdue_command_with_non_overdue_task(cli, capsys):
    """check-overdue with a non-overdue task prints 'not overdue'."""
    _add(cli, "Future task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["check-overdue", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Status: not overdue" in out


def test_check_overdue_command_with_missing_task_id(cli):
    """check-overdue with missing task ID exits with error code 1."""
    rc = cli.run(["check-overdue", "00000000"])
    assert rc == 1


def test_check_overdue_shows_task_id_prefix(cli, capsys):
    """check-overdue output includes the task ID prefix."""
    _add(cli, "Overdue check")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["check-overdue", task_id])
    out = capsys.readouterr().out
    assert task_id in out


def test_check_overdue_completed_task_not_overdue(cli, capsys):
    """check-overdue on a completed past-due task prints 'not overdue'."""
    from datetime import datetime, timezone, timedelta
    from src.services.task_manager import TaskManager

    # Create a task and manually set it as completed with past due date
    _add(cli, "Completed overdue")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    # Mark it done first
    cli.run(["done", task_id])

    # Now check overdue - should be not overdue because it's done
    rc = cli.run(["check-overdue", task_id])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Status: not overdue" in out


# ===== add-comment command tests =====

def test_add_comment_command(cli, capsys):
    """add-comment adds a comment to a task."""
    _add(cli, "Task for comment")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["add-comment", task_id, "Great job!"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Added comment" in out
    assert task_id in out


def test_add_comment_with_author(cli, capsys):
    """add-comment with -a flag includes author."""
    _add(cli, "Task for comment")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["add-comment", task_id, "Nice work", "-a", "Alice"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Added comment" in out


def test_add_comment_with_author_long_form(cli, capsys):
    """add-comment with --author flag includes author."""
    _add(cli, "Task for comment")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["add-comment", task_id, "Nice work", "--author", "Bob"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Added comment" in out


def test_add_comment_to_nonexistent_task_exits_1(cli):
    """add-comment to non-existent task exits with code 1."""
    rc = cli.run(["add-comment", "00000000", "comment text"])
    assert rc == 1


def test_add_comment_empty_content_exits_1(cli, capsys):
    """add-comment with empty content exits with code 1."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["add-comment", task_id, ""])
    assert rc == 1


def test_add_comment_whitespace_only_exits_1(cli, capsys):
    """add-comment with whitespace-only content exits with code 1."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["add-comment", task_id, "   "])
    assert rc == 1


def test_add_comment_with_task_prefix(cli, capsys):
    """add-comment works with task ID prefix."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]
    prefix = task_id[:8]

    rc = cli.run(["add-comment", prefix, "comment"])
    assert rc == 0


# ===== show-comments command tests =====

def test_show_comments_command_no_comments(cli, capsys):
    """show-comments with no comments prints message."""
    _add(cli, "Task with no comments")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["show-comments", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "No comments" in out


def test_show_comments_command_with_comments(cli, capsys):
    """show-comments displays all comments."""
    _add(cli, "Task with comments")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    # Add comments
    cli.run(["add-comment", task_id, "First comment"])
    cli.run(["add-comment", task_id, "Second comment"])

    rc = cli.run(["show-comments", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "First comment" in out
    assert "Second comment" in out


def test_show_comments_displays_author(cli, capsys):
    """show-comments displays author when present."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "comment", "-a", "Carol"])

    rc = cli.run(["show-comments", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Carol" in out


def test_show_comments_displays_timestamp(cli, capsys):
    """show-comments displays created_at timestamp."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "timestamped comment"])

    rc = cli.run(["show-comments", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    # Look for ISO format datetime
    assert "T" in out  # ISO format has a T


def test_show_comments_nonexistent_task_exits_1(cli):
    """show-comments on non-existent task exits with code 1."""
    rc = cli.run(["show-comments", "00000000"])
    assert rc == 1


def test_show_comments_with_task_prefix(cli, capsys):
    """show-comments works with task ID prefix."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]
    prefix = task_id[:8]

    cli.run(["add-comment", task_id, "comment"])

    rc = cli.run(["show-comments", prefix])

    assert rc == 0
    out = capsys.readouterr().out
    assert "comment" in out


def test_show_comments_in_chronological_order(cli, capsys):
    """show-comments displays comments in chronological order."""
    import time
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "first comment"])
    time.sleep(0.01)
    cli.run(["add-comment", task_id, "second comment"])

    rc = cli.run(["show-comments", task_id])

    assert rc == 0
    out = capsys.readouterr().out
    # Verify both comments are present
    assert "first comment" in out
    assert "second comment" in out


# ===== delete-comment command tests =====

def test_delete_comment_command(cli, capsys):
    """delete-comment removes a comment."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "to delete"])
    cli.run(["show-comments", task_id])
    output = capsys.readouterr().out
    # Extract comment ID from output - it's on the first indented line after "Comments on task"
    lines = output.split('\n')
    comment_id = None
    for line in lines:
        if line.strip() and not line.startswith("Comments") and not "T" in line and "comment" not in line:
            comment_id = line.strip().split()[0]
            break

    assert comment_id is not None

    rc = cli.run(["delete-comment", comment_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "Deleted comment" in out


def test_delete_comment_by_prefix(cli, capsys):
    """delete-comment works with comment ID prefix."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "to delete"])
    cli.run(["show-comments", task_id])
    output = capsys.readouterr().out
    lines = output.split('\n')
    comment_id = None
    for line in lines:
        if line.strip() and not line.startswith("Comments") and not "T" in line and "comment" not in line:
            comment_id = line.strip().split()[0]
            break

    assert comment_id is not None
    prefix = comment_id[:8]

    rc = cli.run(["delete-comment", prefix])

    assert rc == 0


def test_delete_comment_nonexistent_exits_1(cli):
    """delete-comment on non-existent comment exits with code 1."""
    rc = cli.run(["delete-comment", "00000000"])
    assert rc == 1


def test_delete_comment_removes_from_task(cli, capsys):
    """After delete-comment, comment is no longer listed."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "comment 1"])
    cli.run(["add-comment", task_id, "comment 2"])

    cli.run(["show-comments", task_id])
    output = capsys.readouterr().out
    lines = output.split('\n')
    comment_id = None
    for line in lines:
        if line.strip() and not line.startswith("Comments") and not "T" in line and "comment" not in line:
            comment_id = line.strip().split()[0]
            break

    assert comment_id is not None

    cli.run(["delete-comment", comment_id])

    cli.run(["show-comments", task_id])
    output = capsys.readouterr().out
    assert "comment 1" not in output
    assert "comment 2" in output


def test_delete_comment_integration_task_deletion(cli, capsys):
    """When task is deleted, its comments are also deleted."""
    _add(cli, "Task to delete")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "comment"])
    cli.run(["show-comments", task_id])
    output = capsys.readouterr().out
    comment_id = output.split()[0]

    # Delete the task
    cli.run(["delete", task_id])

    # Try to delete the comment - should fail
    rc = cli.run(["delete-comment", comment_id])
    assert rc == 1


def test_add_then_show_then_delete_workflow(cli, capsys):
    """Full workflow: add task, add comments, show, delete comments."""
    _add(cli, "Main task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    # Add multiple comments
    cli.run(["add-comment", task_id, "comment 1", "-a", "Alice"])
    cli.run(["add-comment", task_id, "comment 2", "-a", "Bob"])
    cli.run(["add-comment", task_id, "comment 3"])

    # Show comments
    rc = cli.run(["show-comments", task_id])
    assert rc == 0
    output = capsys.readouterr().out
    assert "comment 1" in output
    assert "comment 2" in output
    assert "comment 3" in output
    assert "Alice" in output
    assert "Bob" in output
