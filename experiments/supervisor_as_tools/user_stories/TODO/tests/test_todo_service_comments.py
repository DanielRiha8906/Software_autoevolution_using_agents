import pytest
from src.models.task_comment import TaskComment
from src.services.comment_manager import CommentNotFoundError
from src.services.task_manager import TaskNotFoundError
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TodoService(storage)


def test_add_comment_creates_comment(service):
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Great!")
    assert comment.task_id == task.id
    assert comment.content == "Great!"


def test_add_comment_returns_task_comment(service):
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Comment")
    assert isinstance(comment, TaskComment)


def test_add_comment_raises_task_not_found(service):
    with pytest.raises(TaskNotFoundError):
        service.add_comment("nonexistent-task", "Comment")


def test_add_comment_raises_empty_content(service):
    task = service.add_task("Task")
    with pytest.raises(ValueError):
        service.add_comment(task.id, "")


def test_get_comment_retrieves_comment(service):
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Test")
    retrieved = service.get_comment(comment.id)
    assert retrieved.id == comment.id
    assert retrieved.content == "Test"


def test_get_comment_raises_not_found(service):
    with pytest.raises(CommentNotFoundError):
        service.get_comment("nonexistent-id")


def test_list_task_comments_returns_comments(service):
    task = service.add_task("Task")
    c1 = service.add_comment(task.id, "Comment 1")
    c2 = service.add_comment(task.id, "Comment 2")
    comments = service.list_task_comments(task.id)
    assert len(comments) == 2
    assert c1 in comments
    assert c2 in comments


def test_list_task_comments_empty_for_task_without_comments(service):
    task = service.add_task("Task")
    comments = service.list_task_comments(task.id)
    assert comments == []


def test_update_comment_modifies_content(service):
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Original")
    updated = service.update_comment(comment.id, "Modified")
    assert updated.content == "Modified"


def test_update_comment_raises_not_found(service):
    with pytest.raises(CommentNotFoundError):
        service.update_comment("nonexistent-id", "New")


def test_delete_comment_removes_comment(service):
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "To delete")
    service.delete_comment(comment.id)
    with pytest.raises(CommentNotFoundError):
        service.get_comment(comment.id)


def test_delete_comment_raises_not_found(service):
    with pytest.raises(CommentNotFoundError):
        service.delete_comment("nonexistent-id")


def test_comment_error_propagation_task_not_found(service):
    with pytest.raises(TaskNotFoundError):
        service.add_comment("invalid-task-id", "Comment")


def test_comment_error_propagation_not_found(service):
    with pytest.raises(CommentNotFoundError):
        service.get_comment("invalid-comment-id")


def test_comment_error_propagation_empty_content(service):
    task = service.add_task("Task")
    with pytest.raises(ValueError):
        service.add_comment(task.id, "")
