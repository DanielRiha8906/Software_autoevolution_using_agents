import pytest
from src.models.task_comment import TaskComment
from src.services.comments_service import CommentsService, CommentNotFoundError
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def comments_storage(tmp_path):
    return JsonStorage(str(tmp_path / "comments.json"))


@pytest.fixture
def task_storage(tmp_path):
    return JsonStorage(str(tmp_path / "tasks.json"))


@pytest.fixture
def task_manager(task_storage):
    return TaskManager(task_storage)


@pytest.fixture
def comments_service(comments_storage, task_manager):
    return CommentsService(comments_storage, task_manager)


def test_add_comment_creates_comment(comments_service, task_manager):
    """Test that add_comment creates a new comment."""
    task = task_manager.add("Test task")
    comment = comments_service.add_comment(task.id, "Great task!")
    assert comment.task_id == task.id
    assert comment.content == "Great task!"
    assert comment.author is None


def test_add_comment_with_author(comments_service, task_manager):
    """Test that add_comment creates a comment with author."""
    task = task_manager.add("Test task")
    comment = comments_service.add_comment(task.id, "Nice work", author="Alice")
    assert comment.author == "Alice"


def test_add_comment_validates_task_exists(comments_service):
    """Test that add_comment raises error if task doesn't exist."""
    with pytest.raises(TaskNotFoundError):
        comments_service.add_comment("nonexistent-task-id", "Comment")


def test_add_comment_without_task_manager(comments_storage):
    """Test that add_comment works without task_manager (no validation)."""
    service = CommentsService(comments_storage, task_manager=None)
    comment = service.add_comment("any-task-id", "Comment without validation")
    assert comment.task_id == "any-task-id"
    assert comment.content == "Comment without validation"


def test_list_comments_empty(comments_service, task_manager):
    """Test that list_comments returns empty list when no comments exist."""
    task = task_manager.add("Test task")
    comments = comments_service.list_comments(task.id)
    assert comments == []


def test_list_comments_single(comments_service, task_manager):
    """Test that list_comments returns single comment."""
    task = task_manager.add("Test task")
    comment = comments_service.add_comment(task.id, "Only comment")
    comments = comments_service.list_comments(task.id)
    assert len(comments) == 1
    assert comments[0].id == comment.id


def test_list_comments_multiple_ordered_by_created_at(comments_service, task_manager):
    """Test that list_comments returns multiple comments ordered by created_at."""
    task = task_manager.add("Test task")
    comment1 = comments_service.add_comment(task.id, "First comment")
    comment2 = comments_service.add_comment(task.id, "Second comment")
    comment3 = comments_service.add_comment(task.id, "Third comment")

    comments = comments_service.list_comments(task.id)
    assert len(comments) == 3
    assert comments[0].id == comment1.id
    assert comments[1].id == comment2.id
    assert comments[2].id == comment3.id


def test_list_comments_only_for_task(comments_service, task_manager):
    """Test that list_comments only returns comments for the specified task."""
    task1 = task_manager.add("Task 1")
    task2 = task_manager.add("Task 2")

    comment1 = comments_service.add_comment(task1.id, "Comment on task 1")
    comment2 = comments_service.add_comment(task2.id, "Comment on task 2")
    comment3 = comments_service.add_comment(task1.id, "Another comment on task 1")

    task1_comments = comments_service.list_comments(task1.id)
    task2_comments = comments_service.list_comments(task2.id)

    assert len(task1_comments) == 2
    assert len(task2_comments) == 1
    assert comment1 in task1_comments
    assert comment3 in task1_comments
    assert comment2 in task2_comments


def test_delete_comment(comments_service, task_manager):
    """Test that delete_comment removes a comment."""
    task = task_manager.add("Test task")
    comment = comments_service.add_comment(task.id, "Comment to delete")
    comments_service.delete_comment(comment.id)

    comments = comments_service.list_comments(task.id)
    assert len(comments) == 0


def test_delete_comment_not_found(comments_service):
    """Test that delete_comment raises error if comment doesn't exist."""
    with pytest.raises(CommentNotFoundError):
        comments_service.delete_comment("nonexistent-comment-id")


def test_delete_comment_removes_only_specified(comments_service, task_manager):
    """Test that delete_comment only removes the specified comment."""
    task = task_manager.add("Test task")
    comment1 = comments_service.add_comment(task.id, "Keep this")
    comment2 = comments_service.add_comment(task.id, "Delete this")

    comments_service.delete_comment(comment2.id)

    comments = comments_service.list_comments(task.id)
    assert len(comments) == 1
    assert comments[0].id == comment1.id


def test_delete_comments_for_task_cascade(comments_service, task_manager):
    """Test that delete_comments_for_task removes all comments for a task."""
    task1 = task_manager.add("Task 1")
    task2 = task_manager.add("Task 2")

    comment1 = comments_service.add_comment(task1.id, "Comment 1 on task 1")
    comment2 = comments_service.add_comment(task1.id, "Comment 2 on task 1")
    comment3 = comments_service.add_comment(task2.id, "Comment on task 2")

    comments_service.delete_comments_for_task(task1.id)

    task1_comments = comments_service.list_comments(task1.id)
    task2_comments = comments_service.list_comments(task2.id)

    assert len(task1_comments) == 0
    assert len(task2_comments) == 1
    assert task2_comments[0].id == comment3.id


def test_delete_comments_for_task_no_comments(comments_service, task_manager):
    """Test that delete_comments_for_task works even if task has no comments."""
    task = task_manager.add("Task without comments")
    # Should not raise any error
    comments_service.delete_comments_for_task(task.id)
    assert len(comments_service.list_comments(task.id)) == 0


def test_get_comment(comments_service, task_manager):
    """Test that get_comment returns the correct comment."""
    task = task_manager.add("Test task")
    comment = comments_service.add_comment(task.id, "Test comment")

    retrieved = comments_service.get_comment(comment.id)
    assert retrieved.id == comment.id
    assert retrieved.content == "Test comment"


def test_get_comment_not_found(comments_service):
    """Test that get_comment raises error if comment doesn't exist."""
    with pytest.raises(CommentNotFoundError):
        comments_service.get_comment("nonexistent-comment-id")


def test_update_comment(comments_service, task_manager):
    """Test that update_comment updates the content and updated_at."""
    task = task_manager.add("Test task")
    comment = comments_service.add_comment(task.id, "Original content")
    original_updated_at = comment.updated_at

    updated = comments_service.update_comment(comment.id, "Updated content")
    assert updated.content == "Updated content"
    assert updated.updated_at >= original_updated_at


def test_update_comment_not_found(comments_service):
    """Test that update_comment raises error if comment doesn't exist."""
    with pytest.raises(CommentNotFoundError):
        comments_service.update_comment("nonexistent-comment-id", "New content")


def test_persistence(tmp_path):
    """Test that comments are persisted to storage."""
    path = str(tmp_path / "comments.json")
    task_path = str(tmp_path / "tasks.json")

    # Create first service instance and add comment
    task_manager1 = TaskManager(JsonStorage(task_path))
    task = task_manager1.add("Test task")
    service1 = CommentsService(JsonStorage(path), task_manager1)
    comment1 = service1.add_comment(task.id, "Persisted comment")

    # Create second service instance and load from storage
    task_manager2 = TaskManager(JsonStorage(task_path))
    service2 = CommentsService(JsonStorage(path), task_manager2)
    comments = service2.list_comments(task.id)

    assert len(comments) == 1
    assert comments[0].id == comment1.id
    assert comments[0].content == "Persisted comment"


def test_empty_content_raises_error(comments_service, task_manager):
    """Test that adding a comment with empty content raises ValueError."""
    task = task_manager.add("Test task")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        comments_service.add_comment(task.id, "")


def test_add_comment_returns_task_comment(comments_service, task_manager):
    """Test that add_comment returns a TaskComment instance."""
    task = task_manager.add("Test task")
    comment = comments_service.add_comment(task.id, "Comment")
    assert isinstance(comment, TaskComment)


def test_list_comments_returns_list_of_task_comments(comments_service, task_manager):
    """Test that list_comments returns a list of TaskComment instances."""
    task = task_manager.add("Test task")
    comments_service.add_comment(task.id, "Comment 1")
    comments_service.add_comment(task.id, "Comment 2")

    comments = comments_service.list_comments(task.id)
    assert isinstance(comments, list)
    assert all(isinstance(c, TaskComment) for c in comments)
