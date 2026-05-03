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
