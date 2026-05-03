import pytest
from src.cli.todo_cli import TodoCLI
from src.storage.json_storage import JsonStorage


@pytest.fixture
def cli(tmp_path):
    return TodoCLI(storage_path=str(tmp_path / "tasks.json"))


def _add(cli, title, description=None, due_date=None):
    args = ["add", title]
    if description:
        args += ["-d", description]
    if due_date:
        args += ["--due-date", due_date]
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
    assert "in_progress" in out


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


# ─── Due date tests ─────────────────────────────────────────────────────────

def test_add_with_due_date(cli, capsys):
    """Test add command with --due-date option"""
    rc = _add(cli, "Task with deadline", due_date="2026-05-15T14:30:00+00:00")
    assert rc == 0
    assert "Task with deadline" in capsys.readouterr().out


def test_add_invalid_due_date_format(cli, capsys):
    """Test add command rejects invalid date format"""
    rc = cli.run(["add", "Task", "--due-date", "not-a-date"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Invalid date format" in err


def test_add_with_valid_iso_8601_formats(cli, capsys):
    """Test add with various valid ISO 8601 formats"""
    valid_formats = [
        "2026-05-15T14:30:00+00:00",
        "2026-05-15T14:30:00Z",
        "2026-05-15T14:30:00+02:00",
        "2026-05-15T14:30:00-05:00",
    ]
    for fmt in valid_formats:
        rc = _add(cli, "Task", due_date=fmt)
        assert rc == 0, f"Failed with format: {fmt}"


def test_update_with_due_date(cli, capsys):
    """Test update command with --due-date option"""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["update", task_id, "--due-date", "2026-05-15T14:30:00+00:00"])
    assert rc == 0
    assert "Updated" in capsys.readouterr().out


def test_update_invalid_due_date_format(cli, capsys):
    """Test update command rejects invalid date format"""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["update", task_id, "--due-date", "invalid-date"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Invalid date format" in err


def test_due_date_command_set(cli, capsys):
    """Test due-date subcommand to set a due date"""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["due-date", task_id, "--date", "2026-05-15T14:30:00+00:00"])
    assert rc == 0
    output = capsys.readouterr().out
    assert "Set due date" in output
    assert "2026-05-15T14:30:00+00:00" in output


def test_due_date_command_clear(cli, capsys):
    """Test due-date subcommand to clear a due date"""
    _add(cli, "Task", due_date="2026-05-15T14:30:00+00:00")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    # Clear by not providing --date
    rc = cli.run(["due-date", task_id])
    assert rc == 0
    output = capsys.readouterr().out
    assert "—" in output  # Display shows — for cleared/None due_date


def test_due_date_command_invalid_format(cli, capsys):
    """Test due-date command rejects invalid date format"""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["due-date", task_id, "--date", "invalid"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Invalid date format" in err


def test_show_displays_due_date(cli, capsys):
    """Test show command displays due_date when present"""
    _add(cli, "Task with deadline", due_date="2026-05-15T14:30:00+00:00")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["show", task_id])
    out = capsys.readouterr().out
    assert "Due date:" in out
    assert "2026-05-15T14:30:00+00:00" in out


def test_show_displays_dash_when_no_due_date(cli, capsys):
    """Test show command displays — when due_date is None"""
    _add(cli, "Task without deadline")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["show", task_id])
    out = capsys.readouterr().out
    assert "Due date:" in out
    assert "—" in out


def test_add_with_description_and_due_date(cli, capsys):
    """Test add command with both description and due-date"""
    rc = cli.run(["add", "Complete task", "-d", "Task description", "--due-date", "2026-05-15T14:30:00+00:00"])
    assert rc == 0

    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["show", task_id])
    out = capsys.readouterr().out
    assert "Complete task" in out
    assert "Task description" in out
    assert "2026-05-15T14:30:00+00:00" in out


# ─── Comment CLI command tests ──────────────────────────────────────────────────

def test_add_comment_success(cli, capsys):
    """Test add-comment command successfully adds a comment."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["add-comment", task_id, "Great work!"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Added comment" in out
    assert "Great work!" in out


def test_add_comment_with_author(cli, capsys):
    """Test add-comment command with --author option."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["add-comment", task_id, "Nice job!", "-a", "Alice"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "by Alice" in out


def test_add_comment_empty_content_fails(cli, capsys):
    """Test add-comment fails with empty content."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["add-comment", task_id, "   "])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error" in err


def test_add_comment_missing_task_fails(cli, capsys):
    """Test add-comment fails when task doesn't exist."""
    rc = cli.run(["add-comment", "00000000", "Comment"])
    assert rc == 1


def test_list_comments_empty(cli, capsys):
    """Test list-comments on task with no comments."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["list-comments", task_id])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(no comments)" in out


def test_list_comments_with_comments(cli, capsys):
    """Test list-comments displays all comments."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "First comment", "-a", "Alice"])
    cli.run(["add-comment", task_id, "Second comment", "-a", "Bob"])

    rc = cli.run(["list-comments", task_id])
    assert rc == 0
    out = capsys.readouterr().out
    assert "First comment" in out
    assert "Second comment" in out
    assert "Alice" in out
    assert "Bob" in out


def test_list_comments_shows_timestamps(cli, capsys):
    """Test list-comments displays creation and update timestamps."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "Comment"])

    rc = cli.run(["list-comments", task_id])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Created:" in out


def test_list_comments_missing_task_fails(cli, capsys):
    """Test list-comments fails when task doesn't exist."""
    rc = cli.run(["list-comments", "00000000"])
    assert rc == 1


def test_delete_comment_success(cli, capsys):
    """Test delete-comment successfully removes a comment."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "To delete"])
    cli.run(["list-comments", task_id])
    output = capsys.readouterr().out
    # Extract comment ID from "  287a4899 — (no author)" line format
    # Split by newlines and find the line with the comment ID
    lines = output.split('\n')
    comment_id = None
    for line in lines:
        if line.strip() and '—' in line:
            comment_id = line.strip().split()[0]
            break

    assert comment_id is not None, "Could not extract comment ID from output"
    rc = cli.run(["delete-comment", task_id, comment_id])
    assert rc == 0
    output = capsys.readouterr().out
    assert "Deleted comment" in output


def test_delete_comment_nonexistent_fails(cli, capsys):
    """Test delete-comment fails when comment doesn't exist."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["delete-comment", task_id, "00000000"])
    assert rc == 1


def test_delete_comment_missing_task_fails(cli, capsys):
    """Test delete-comment fails when task doesn't exist."""
    rc = cli.run(["delete-comment", "00000000", "comment-id"])
    assert rc == 1


def test_edit_comment_success(cli, capsys):
    """Test edit-comment successfully updates a comment."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "Original"])
    cli.run(["list-comments", task_id])
    output = capsys.readouterr().out
    # Extract comment ID from "  287a4899 — (no author)" line format
    lines = output.split('\n')
    comment_id = None
    for line in lines:
        if line.strip() and '—' in line:
            comment_id = line.strip().split()[0]
            break

    assert comment_id is not None, "Could not extract comment ID from output"
    rc = cli.run(["edit-comment", task_id, comment_id, "Updated content"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Edited comment" in out
    assert "Updated content" in out


def test_edit_comment_empty_content_fails(cli, capsys):
    """Test edit-comment fails with empty content."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "Original"])
    cli.run(["list-comments", task_id])
    output = capsys.readouterr().out
    comment_id = output.split()[1]

    rc = cli.run(["edit-comment", task_id, comment_id, "   "])
    assert rc == 1


def test_edit_comment_nonexistent_fails(cli, capsys):
    """Test edit-comment fails when comment doesn't exist."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    rc = cli.run(["edit-comment", task_id, "00000000", "New content"])
    assert rc == 1


def test_edit_comment_missing_task_fails(cli, capsys):
    """Test edit-comment fails when task doesn't exist."""
    rc = cli.run(["edit-comment", "00000000", "comment-id", "Content"])
    assert rc == 1


def test_comment_prefix_matching_in_delete(cli, capsys):
    """Test delete-comment works with comment ID prefix (first 8 chars)."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "To delete"])
    cli.run(["list-comments", task_id])
    output = capsys.readouterr().out
    # Extract comment ID
    lines = output.split('\n')
    comment_id = None
    for line in lines:
        if line.strip() and '—' in line:
            comment_id = line.strip().split()[0]
            break

    assert comment_id is not None
    # Use only first 8 chars as prefix
    rc = cli.run(["delete-comment", task_id, comment_id[:8]])
    assert rc == 0


def test_comment_prefix_matching_in_edit(cli, capsys):
    """Test edit-comment works with comment ID prefix (first 8 chars)."""
    _add(cli, "Task")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    cli.run(["add-comment", task_id, "Original"])
    cli.run(["list-comments", task_id])
    output = capsys.readouterr().out
    # Extract comment ID
    lines = output.split('\n')
    comment_id = None
    for line in lines:
        if line.strip() and '—' in line:
            comment_id = line.strip().split()[0]
            break

    assert comment_id is not None
    # Use only first 8 chars as prefix
    rc = cli.run(["edit-comment", task_id, comment_id[:8], "Updated"])
    assert rc == 0
