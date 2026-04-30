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
