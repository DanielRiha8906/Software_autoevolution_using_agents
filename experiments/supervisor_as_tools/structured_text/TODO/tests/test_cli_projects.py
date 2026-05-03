import pytest
import tempfile
from pathlib import Path

from src.cli.todo_cli import TodoCLI


@pytest.fixture
def temp_storage():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_cli_project_add(temp_storage, capsys):
    """Test project-add command."""
    cli = TodoCLI(temp_storage)
    ret = cli.run(["project-add", "My Project"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Added project" in captured.out
    assert "My Project" in captured.out


def test_cli_project_list(temp_storage, capsys):
    """Test project-list command."""
    cli = TodoCLI(temp_storage)
    cli.run(["project-add", "Project 1"])
    cli.run(["project-add", "Project 2"])

    ret = cli.run(["project-list"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Project 1" in captured.out
    assert "Project 2" in captured.out


def test_cli_project_list_empty(temp_storage, capsys):
    """Test project-list when no projects exist."""
    cli = TodoCLI(temp_storage)
    ret = cli.run(["project-list"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "No projects found" in captured.out


def test_cli_add_task_with_project(temp_storage, capsys):
    """Test adding a task with --project flag."""
    cli = TodoCLI(temp_storage)
    result = cli.run(["project-add", "My Project"])
    assert result == 0
    captured = capsys.readouterr()
    # Extract project ID from output
    output_lines = captured.out.split("\n")
    project_id = output_lines[0].split()[2]  # Extract first 8 chars after "Added project"

    ret = cli.run(["add", "Task", "--project", project_id])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Added task" in captured.out
    assert "to project" in captured.out


def test_cli_list_tasks_by_project(temp_storage, capsys):
    """Test listing tasks with --project filter."""
    cli = TodoCLI(temp_storage)
    result = cli.run(["project-add", "Project 1"])
    assert result == 0
    captured = capsys.readouterr()
    project_id = captured.out.split()[2]

    capsys.readouterr()  # Clear the buffer
    cli.run(["add", "Task in Project", "--project", project_id])
    capsys.readouterr()  # Clear the buffer
    cli.run(["add", "Task without Project"])
    capsys.readouterr()  # Clear the buffer

    ret = cli.run(["list", "--project", project_id])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Task in Project" in captured.out
    assert "Task without Project" not in captured.out


def test_cli_project_delete(temp_storage, capsys):
    """Test project-delete command."""
    cli = TodoCLI(temp_storage)
    result = cli.run(["project-add", "To Delete"])
    assert result == 0
    captured = capsys.readouterr()
    # Extract project ID - it should be the first 8 characters after "Added project "
    lines = captured.out.strip().split()
    project_id = lines[2]  # Skip "Added" and "project", get ID

    ret = cli.run(["project-delete", project_id])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Deleted project" in captured.out


def test_cli_project_delete_missing(temp_storage, capsys):
    """Test project-delete with missing project."""
    cli = TodoCLI(temp_storage)
    ret = cli.run(["project-delete", "missing"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_cli_project_add_empty_name(temp_storage, capsys):
    """Test project-add with empty name."""
    cli = TodoCLI(temp_storage)
    ret = cli.run(["project-add", ""])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err
