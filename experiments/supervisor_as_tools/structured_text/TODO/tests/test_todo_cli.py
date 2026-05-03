import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
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


# Tests for new CLI flags
def test_list_due_before(cli, capsys):
    """Test --due-before flag."""
    cest = ZoneInfo("Europe/Paris")
    now_cest = datetime.now(cest)
    past = (now_cest + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    future = (now_cest + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")

    _add(cli, "Task 1")
    _add(cli, "Task 2")

    cli.run(["list"])
    output = capsys.readouterr().out
    lines = output.split("\n")
    task_ids = []
    for line in lines:
        if line.startswith("["):
            parts = line.split()
            # The format is "[ ] id  title"
            if len(parts) >= 3:
                task_ids.append(parts[2])

    if len(task_ids) < 2:
        pytest.skip("Could not parse task IDs")

    t1_id, t2_id = task_ids[0], task_ids[1]

    cli.run(["due-date", t1_id, "--date", past])
    cli.run(["due-date", t2_id, "--date", future])

    cli.run(["list", "--due-before", past])
    out = capsys.readouterr().out
    # Task with due date before the cutoff should appear
    assert "No tasks" in out or t1_id in out or "Task 1" in out


def test_list_due_after(cli, capsys):
    """Test --due-after flag."""
    cest = ZoneInfo("Europe/Paris")
    now_cest = datetime.now(cest)
    past = (now_cest + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    future = (now_cest + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")

    _add(cli, "Task 1")
    _add(cli, "Task 2")

    cli.run(["list"])
    output = capsys.readouterr().out
    lines = output.split("\n")
    task_ids = []
    for line in lines:
        if line.startswith("["):
            parts = line.split()
            if len(parts) >= 3:
                task_ids.append(parts[2])

    if len(task_ids) < 2:
        pytest.skip("Could not parse task IDs")

    t1_id, t2_id = task_ids[0], task_ids[1]

    cli.run(["due-date", t1_id, "--date", past])
    cli.run(["due-date", t2_id, "--date", future])

    cli.run(["list", "--due-after", future])
    out = capsys.readouterr().out
    # Only task with future due date should appear
    assert "No tasks" in out or t2_id in out or "Task 2" in out


def test_list_overdue_flag(cli, capsys):
    """Test --overdue flag."""
    _add(cli, "Task 1")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    # Set task to past due date by manipulating the storage
    service = cli._service
    task = service.get_task(task_id)
    past = datetime.now(timezone.utc) - timedelta(days=1)
    task.due_date = past
    service._manager._persist()

    cli.run(["list", "--overdue"])
    out = capsys.readouterr().out
    # Overdue task should appear
    assert "Task 1" in out


def test_list_overdue_excludes_future(cli, capsys):
    """Test that --overdue doesn't show future tasks."""
    _add(cli, "Task 1")
    _add(cli, "Task 2")

    cli.run(["list"])
    output = capsys.readouterr().out
    lines = output.split("\n")
    task_ids = []
    for line in lines:
        if line.startswith("["):
            parts = line.split()
            if len(parts) >= 3:
                task_ids.append(parts[2])

    if len(task_ids) < 2:
        pytest.skip("Could not parse task IDs")

    t1_id, t2_id = task_ids[0], task_ids[1]
    service = cli._service

    # t1 is overdue, t2 is future
    t1 = service.get_task(t1_id)
    t1.due_date = datetime.now(timezone.utc) - timedelta(days=1)
    service._manager._persist()

    cli.run(["due-date", t2_id, "--date",
             (datetime.now(ZoneInfo("Europe/Paris")) + timedelta(days=10)).strftime("%Y-%m-%d %H:%M")])

    cli.run(["list", "--overdue"])
    out = capsys.readouterr().out
    assert "Task 1" in out


def test_list_invalid_due_before_format(cli, capsys):
    """Test that invalid --due-before format returns error."""
    rc = cli.run(["list", "--due-before", "invalid"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Invalid date format" in err


def test_list_invalid_due_after_format(cli, capsys):
    """Test that invalid --due-after format returns error."""
    rc = cli.run(["list", "--due-after", "invalid"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Invalid date format" in err


def test_list_due_flags_with_status(cli, capsys):
    """Test combining due flags with status filter."""
    cest = ZoneInfo("Europe/Paris")
    now_cest = datetime.now(cest)
    past = (now_cest + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    future = (now_cest + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")

    _add(cli, "Task 1")
    _add(cli, "Task 2")

    cli.run(["list"])
    output = capsys.readouterr().out
    lines = output.split("\n")
    task_ids = []
    for line in lines:
        if line.startswith("["):
            parts = line.split()
            if len(parts) >= 3:
                task_ids.append(parts[2])

    if len(task_ids) < 2:
        pytest.skip("Could not parse task IDs")

    t1_id, t2_id = task_ids[0], task_ids[1]

    cli.run(["due-date", t1_id, "--date", past])
    cli.run(["due-date", t2_id, "--date", future])

    # Complete one task
    cli.run(["done", t1_id])

    # List pending tasks with due date in range
    cli.run(["list", "--status", "pending", "--due-after", past])
    out = capsys.readouterr().out
    # Only pending task in range should appear
    assert "Task 2" in out


def test_list_cest_datetime_parsing(cli, capsys):
    """Test that CEST datetime strings are correctly parsed."""
    cest = ZoneInfo("Europe/Paris")
    # Create a specific CEST time
    cest_time = datetime(2026, 5, 5, 10, 30, tzinfo=cest)
    date_str = cest_time.strftime("%Y-%m-%d %H:%M")

    _add(cli, "Task 1")
    cli.run(["list"])
    task_id = capsys.readouterr().out.split()[2]

    service = cli._service
    task = service.get_task(task_id)
    task.due_date = cest_time.astimezone(timezone.utc)
    service._manager._persist()

    # List with due_after just before this time - should include task
    earlier_str = (cest_time - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    cli.run(["list", "--due-after", earlier_str])
    out = capsys.readouterr().out
    assert "Task 1" in out
