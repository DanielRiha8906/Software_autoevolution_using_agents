import pytest
from src.models.task_status import TaskStatus
from src.services.task_manager import TaskNotFoundError
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


def test_add_task(service):
    task = service.add_task("Hello")
    assert task.title == "Hello"


def test_add_task_strips_whitespace(service):
    task = service.add_task("  padded  ")
    assert task.title == "padded"


def test_add_empty_title_raises(service):
    with pytest.raises(ValueError):
        service.add_task("   ")


def test_start_task(service):
    task = service.add_task("Do it")
    started = service.start_task(task.id)
    assert started.status == TaskStatus.IN_PROGRESS


def test_complete_task(service):
    task = service.add_task("Do it")
    done = service.complete_task(task.id)
    assert done.status == TaskStatus.DONE


def test_reopen_task(service):
    task = service.add_task("Redo")
    service.complete_task(task.id)
    reopened = service.reopen_task(task.id)
    assert reopened.status == TaskStatus.PENDING


def test_list_tasks_all(service):
    service.add_task("A")
    service.add_task("B")
    assert len(service.list_tasks()) == 2


def test_list_tasks_filtered(service):
    t = service.add_task("A")
    service.add_task("B")
    service.complete_task(t.id)
    assert len(service.list_tasks(TaskStatus.DONE)) == 1
    assert len(service.list_tasks(TaskStatus.PENDING)) == 1


def test_update_task(service):
    task = service.add_task("Old title")
    updated = service.update_task(task.id, title="New title")
    assert updated.title == "New title"


def test_update_task_empty_title_raises(service):
    task = service.add_task("Valid")
    with pytest.raises(ValueError):
        service.update_task(task.id, title="")


def test_delete_task(service):
    task = service.add_task("Bye")
    service.delete_task(task.id)
    with pytest.raises(TaskNotFoundError):
        service.get_task(task.id)


# ===== Comment Tests =====

def test_add_comment(service):
    """add_comment() creates a comment on a task."""
    task = service.add_task("Task with comment")
    comment = service.add_comment(task.id, "Great task!")
    assert comment.task_id == task.id
    assert comment.content == "Great task!"
    assert comment.author is None


def test_add_comment_with_author(service):
    """add_comment() can include an author."""
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "comment", author="Alice")
    assert comment.author == "Alice"


def test_add_comment_strips_whitespace(service):
    """add_comment() strips whitespace from content."""
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "  spaced  ")
    assert comment.content == "spaced"


def test_add_comment_empty_content_raises(service):
    """add_comment() raises ValueError for empty content."""
    task = service.add_task("Task")
    with pytest.raises(ValueError):
        service.add_comment(task.id, "")


def test_add_comment_whitespace_only_raises(service):
    """add_comment() raises ValueError for whitespace-only content."""
    task = service.add_task("Task")
    with pytest.raises(ValueError):
        service.add_comment(task.id, "   ")


def test_add_comment_nonexistent_task_raises(service):
    """add_comment() raises TaskNotFoundError if task doesn't exist."""
    with pytest.raises(TaskNotFoundError):
        service.add_comment("nonexistent-id", "comment")


def test_add_comment_with_task_prefix(service):
    """add_comment() works with task ID prefix."""
    task = service.add_task("Task")
    prefix = task.id[:8]
    comment = service.add_comment(prefix, "comment text")
    assert comment.task_id == task.id


def test_get_comments_empty(service):
    """get_comments() returns empty list for task with no comments."""
    task = service.add_task("Task")
    comments = service.get_comments(task.id)
    assert comments == []


def test_get_comments_returns_all(service):
    """get_comments() returns all comments for a task."""
    task = service.add_task("Task")
    c1 = service.add_comment(task.id, "first")
    c2 = service.add_comment(task.id, "second")

    comments = service.get_comments(task.id)
    assert len(comments) == 2
    ids = {c.id for c in comments}
    assert c1.id in ids
    assert c2.id in ids


def test_get_comments_chronological_order(service):
    """get_comments() returns comments in chronological order (oldest first)."""
    import time
    task = service.add_task("Task")
    c1 = service.add_comment(task.id, "first")
    time.sleep(0.01)
    c2 = service.add_comment(task.id, "second")
    time.sleep(0.01)
    c3 = service.add_comment(task.id, "third")

    comments = service.get_comments(task.id)
    assert comments[0].id == c1.id
    assert comments[1].id == c2.id
    assert comments[2].id == c3.id


def test_get_comments_nonexistent_task_raises(service):
    """get_comments() raises TaskNotFoundError if task doesn't exist."""
    with pytest.raises(TaskNotFoundError):
        service.get_comments("nonexistent-id")


def test_get_comments_with_task_prefix(service):
    """get_comments() works with task ID prefix."""
    task = service.add_task("Task")
    c1 = service.add_comment(task.id, "comment")
    prefix = task.id[:8]

    comments = service.get_comments(prefix)
    assert len(comments) == 1
    assert comments[0].id == c1.id


def test_delete_comment(service):
    """delete_comment() removes a comment."""
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "to delete")
    service.delete_comment(comment.id)

    comments = service.get_comments(task.id)
    assert len(comments) == 0


def test_delete_comment_by_prefix(service):
    """delete_comment() works with comment ID prefix."""
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "to delete")
    prefix = comment.id[:8]

    service.delete_comment(prefix)
    comments = service.get_comments(task.id)
    assert len(comments) == 0


def test_delete_comment_nonexistent_raises(service):
    """delete_comment() raises CommentNotFoundError if comment doesn't exist."""
    from src.services.comment_manager import CommentNotFoundError
    with pytest.raises(CommentNotFoundError):
        service.delete_comment("nonexistent-id")


def test_delete_comment_does_not_affect_other_comments(service):
    """delete_comment() only removes the specified comment."""
    task = service.add_task("Task")
    c1 = service.add_comment(task.id, "keep")
    c2 = service.add_comment(task.id, "delete")

    service.delete_comment(c2.id)

    comments = service.get_comments(task.id)
    assert len(comments) == 1
    assert comments[0].id == c1.id


def test_delete_task_cascades_comments(service):
    """delete_task() removes all comments for that task."""
    task = service.add_task("Task to delete")
    c1 = service.add_comment(task.id, "comment 1")
    c2 = service.add_comment(task.id, "comment 2")

    service.delete_task(task.id)

    # Task is gone
    with pytest.raises(TaskNotFoundError):
        service.get_task(task.id)

    # Comments are also gone (cascade delete)
    # Verify by attempting to get a non-existent comment
    from src.services.comment_manager import CommentNotFoundError
    with pytest.raises(CommentNotFoundError):
        service.delete_comment(c1.id)


def test_delete_task_preserves_other_tasks_comments(service):
    """delete_task() only removes comments for that task."""
    task1 = service.add_task("Task 1")
    task2 = service.add_task("Task 2")

    c1 = service.add_comment(task1.id, "on task 1")
    c2 = service.add_comment(task2.id, "on task 2")

    service.delete_task(task1.id)

    # Task 2 and its comment still exist
    assert service.get_task(task2.id) is not None
    comments = service.get_comments(task2.id)
    assert len(comments) == 1
    assert comments[0].id == c2.id


def test_comment_integration_workflow(service):
    """Integration: add task, add multiple comments, delete some comments."""
    task = service.add_task("Main task")

    c1 = service.add_comment(task.id, "comment 1", author="Alice")
    c2 = service.add_comment(task.id, "comment 2", author="Bob")
    c3 = service.add_comment(task.id, "comment 3")

    # Verify all comments are there
    comments = service.get_comments(task.id)
    assert len(comments) == 3

    # Delete middle comment
    service.delete_comment(c2.id)

    # Verify 2 comments remain, in order
    comments = service.get_comments(task.id)
    assert len(comments) == 2
    assert comments[0].id == c1.id
    assert comments[1].id == c3.id
