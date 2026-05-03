import pytest
from io import StringIO
import sys
from src.cli.todo_cli import TodoCLI
from src.storage.json_storage import JsonStorage


@pytest.fixture
def cli(tmp_path):
    storage_path = str(tmp_path / "tasks.json")
    return TodoCLI(storage_path)


def test_add_comment_creates_comment(cli, capsys):
    # First add a task
    cli.run(["add", "Test Task"])

    # Get the task to find its ID
    service = cli._service
    tasks = service.list_tasks()
    task_id = tasks[0].id

    # Add a comment
    result = cli.run(["add-comment", task_id, "--content", "Great task!"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Added comment" in captured.out or "created" in captured.out.lower()


def test_add_comment_with_invalid_task_id(cli, capsys):
    result = cli.run(["add-comment", "invalid-task-id", "--content", "Comment"])
    assert result == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err or "not found" in captured.err.lower()


def test_add_comment_without_content_flag(cli, capsys):
    service = cli._service
    task = service.add_task("Task")
    # argparse.error() calls sys.exit(2) for argument errors
    with pytest.raises(SystemExit) as exc:
        cli.run(["add-comment", task.id])
    assert exc.value.code == 2


def test_list_comments_for_task(cli, capsys):
    service = cli._service
    task = service.add_task("Task")
    service.add_comment(task.id, "Comment 1")
    service.add_comment(task.id, "Comment 2")

    result = cli.run(["list-comments", task.id])
    assert result == 0
    captured = capsys.readouterr()
    # Should show comments
    assert "Comment 1" in captured.out or "comment" in captured.out.lower()


def test_list_comments_empty_task(cli, capsys):
    service = cli._service
    task = service.add_task("Task with no comments")

    result = cli.run(["list-comments", task.id])
    assert result == 0
    captured = capsys.readouterr()
    # Should show empty or message
    assert "No comments" in captured.out or "none" in captured.out.lower() or len(captured.out) < 50


def test_show_comment_displays_details(cli, capsys):
    service = cli._service
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Test comment")

    result = cli.run(["show-comment", comment.id])
    assert result == 0
    captured = capsys.readouterr()
    assert "Test comment" in captured.out


def test_show_comment_with_invalid_id(cli, capsys):
    result = cli.run(["show-comment", "invalid-comment-id"])
    assert result == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err or "not found" in captured.err.lower()


def test_update_comment_modifies_content(cli, capsys):
    service = cli._service
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Original")

    result = cli.run(["update-comment", comment.id, "--content", "Modified"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Updated" in captured.out or "modified" in captured.out.lower()


def test_update_comment_with_invalid_id(cli, capsys):
    result = cli.run(["update-comment", "invalid-id", "--content", "New"])
    assert result == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err or "not found" in captured.err.lower()


def test_delete_comment_removes_comment(cli, capsys):
    service = cli._service
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "To delete")

    result = cli.run(["delete-comment", comment.id])
    assert result == 0
    captured = capsys.readouterr()
    assert "Deleted" in captured.out or "removed" in captured.out.lower()

    # Verify it's actually deleted
    from src.services.comments_service import CommentNotFoundError
    with pytest.raises(CommentNotFoundError):
        service.get_comment(comment.id)


def test_delete_comment_with_invalid_id(cli, capsys):
    result = cli.run(["delete-comment", "invalid-id"])
    assert result == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err or "not found" in captured.err.lower()


def test_comment_commands_with_prefix_id(cli, capsys):
    service = cli._service
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Test")

    # Use first 8 chars
    prefix = comment.id[:8]
    result = cli.run(["show-comment", prefix])
    assert result == 0
    captured = capsys.readouterr()
    assert "Test" in captured.out
