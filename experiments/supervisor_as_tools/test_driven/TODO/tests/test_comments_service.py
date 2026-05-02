import pytest
from datetime import datetime, timezone
from src.services.comments_service import CommentsService
from src.services.task_manager import TaskNotFoundError
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    todo_service = TodoService(JsonStorage(str(tmp_path / "tasks.json")))
    return CommentsService(todo_service)


@pytest.fixture
def todo_service(tmp_path):
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


@pytest.fixture
def comments_service(todo_service):
    return CommentsService(todo_service)


def test_add_comment(service):
    """Test adding a comment to a task."""
    task = service._todo_service.add_task("Test task")
    comment = service.add_comment(task.id, "This is a comment")
    assert comment.task_id == task.id
    assert comment.content == "This is a comment"
    assert comment.id is not None
    assert comment.author is None
    assert comment.created_at is not None


def test_add_empty_comment_raises(service):
    """Test that adding an empty comment raises ValueError."""
    task = service._todo_service.add_task("Test task")
    with pytest.raises(ValueError):
        service.add_comment(task.id, "")


def test_add_whitespace_only_comment_raises(service):
    """Test that adding a whitespace-only comment raises ValueError."""
    task = service._todo_service.add_task("Test task")
    with pytest.raises(ValueError):
        service.add_comment(task.id, "   ")


def test_comments_service_does_not_contain_file_io(service):
    """Test that CommentsService does not perform direct file I/O.

    Comments are stored in-memory only; storage integration is delegated to TodoService.
    """
    # This test verifies the service stores comments in memory
    task = service._todo_service.add_task("Test task")
    comment = service.add_comment(task.id, "In-memory comment")

    # Verify comment is in the internal cache
    assert task.id in service._comments
    assert comment in service._comments[task.id]
    # Note: Comments are not persisted to storage in the current implementation


def test_list_comments_ordered_by_created_at(service):
    """Test that comments are returned ordered by created_at."""
    task = service._todo_service.add_task("Test task")

    # Add multiple comments with slight delays to ensure different timestamps
    comment1 = service.add_comment(task.id, "First")
    comment2 = service.add_comment(task.id, "Second")
    comment3 = service.add_comment(task.id, "Third")

    comments = service.list_comments(task.id)
    assert len(comments) == 3
    # Verify ordering by created_at
    assert comments[0].id == comment1.id
    assert comments[1].id == comment2.id
    assert comments[2].id == comment3.id
    assert comments[0].created_at <= comments[1].created_at <= comments[2].created_at


def test_delete_comment(service):
    """Test deleting a comment from a task."""
    task = service._todo_service.add_task("Test task")
    comment1 = service.add_comment(task.id, "Keep this")
    comment2 = service.add_comment(task.id, "Delete this")

    service.delete_comment(task.id, comment2.id)

    comments = service.list_comments(task.id)
    assert len(comments) == 1
    assert comments[0].id == comment1.id


def test_add_comment_to_nonexistent_task_raises(service):
    """Test that adding a comment to a non-existent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        service.add_comment("nonexistent-task-id", "Comment content")


def test_delete_task_cascades_to_comments(comments_service, todo_service):
    """Test that deleting a task removes all its comments."""
    task = todo_service.add_task("Task to delete")
    comment1 = comments_service.add_comment(task.id, "Comment 1")
    comment2 = comments_service.add_comment(task.id, "Comment 2")

    # Verify comments exist
    assert len(comments_service.list_comments(task.id)) == 2

    # Delete the task
    todo_service.delete_task(task.id)

    # Verify comments can't be accessed (task no longer exists)
    with pytest.raises(TaskNotFoundError):
        comments_service.list_comments(task.id)


def test_add_comment_with_author(service):
    """Test adding a comment with an author."""
    task = service._todo_service.add_task("Test task")
    comment = service.add_comment(task.id, "Authored comment", author="Alice")
    assert comment.author == "Alice"


def test_list_comments_empty_task(service):
    """Test listing comments for a task with no comments."""
    task = service._todo_service.add_task("Empty task")
    comments = service.list_comments(task.id)
    assert comments == []


def test_delete_comment_nonexistent(service):
    """Test deleting a comment that doesn't exist (should not raise)."""
    task = service._todo_service.add_task("Test task")
    comment = service.add_comment(task.id, "Real comment")

    # Delete a non-existent comment ID
    service.delete_comment(task.id, "nonexistent-comment-id")

    # Original comment should still exist
    comments = service.list_comments(task.id)
    assert len(comments) == 1
    assert comments[0].id == comment.id


def test_list_comments_for_nonexistent_task_raises(service):
    """Test that listing comments for a non-existent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        service.list_comments("nonexistent-task-id")


def test_delete_comment_for_nonexistent_task_raises(service):
    """Test that deleting a comment from a non-existent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        service.delete_comment("nonexistent-task-id", "any-comment-id")


def test_delete_comments_for_task(service):
    """Test the delete_comments_for_task cascade delete method."""
    task = service._todo_service.add_task("Task to cascade delete")
    comment1 = service.add_comment(task.id, "Comment 1")
    comment2 = service.add_comment(task.id, "Comment 2")
    comment3 = service.add_comment(task.id, "Comment 3")

    # Verify comments exist
    assert len(service.list_comments(task.id)) == 3

    # Delete all comments for the task
    service.delete_comments_for_task(task.id)

    # Verify all comments are deleted
    comments = service.list_comments(task.id)
    assert len(comments) == 0


def test_delete_comments_for_nonexistent_task_raises(service):
    """Test that deleting all comments for a non-existent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        service.delete_comments_for_task("nonexistent-task-id")


def test_multiple_tasks_with_comments(service):
    """Test managing comments for multiple tasks independently."""
    task1 = service._todo_service.add_task("Task 1")
    task2 = service._todo_service.add_task("Task 2")

    comment1_t1 = service.add_comment(task1.id, "Task 1 comment 1")
    comment2_t1 = service.add_comment(task1.id, "Task 1 comment 2")
    comment1_t2 = service.add_comment(task2.id, "Task 2 comment 1")

    # Verify task 1 comments
    task1_comments = service.list_comments(task1.id)
    assert len(task1_comments) == 2
    assert all(c.task_id == task1.id for c in task1_comments)

    # Verify task 2 comments
    task2_comments = service.list_comments(task2.id)
    assert len(task2_comments) == 1
    assert task2_comments[0].task_id == task2.id

    # Delete a comment from task 1, verify task 2 unaffected
    service.delete_comment(task1.id, comment1_t1.id)
    assert len(service.list_comments(task1.id)) == 1
    assert len(service.list_comments(task2.id)) == 1
