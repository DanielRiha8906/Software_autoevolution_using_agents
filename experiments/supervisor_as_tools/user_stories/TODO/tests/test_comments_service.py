import pytest
from datetime import datetime, timezone, timedelta

from src.services.comments_service import CommentsService, CommentNotFoundError
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def manager(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


@pytest.fixture
def service(manager):
    return CommentsService(manager)


@pytest.fixture
def task(manager):
    return manager.add("Test task")


# Group 1: add_comment() - 9 tests

def test_add_comment_valid(service, task):
    """Test adding a valid comment."""
    comment = service.add_comment(task.id, "This is a comment")
    assert comment.content == "This is a comment"
    assert comment.author is None
    assert comment.task_id == task.id
    assert comment.id is not None
    assert comment.created_at is not None


def test_add_comment_strips_whitespace(service, task):
    """Test that comment content is stripped of whitespace."""
    comment = service.add_comment(task.id, "  padded content  ")
    assert comment.content == "padded content"


def test_add_comment_empty_content_raises(service, task):
    """Test that empty content raises ValueError."""
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        service.add_comment(task.id, "")


def test_add_comment_whitespace_only_raises(service, task):
    """Test that whitespace-only content raises ValueError."""
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        service.add_comment(task.id, "   ")


def test_add_comment_nonexistent_task_raises(service):
    """Test that adding comment to nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        service.add_comment("nonexistent-id", "content")


def test_add_comment_with_author(service, task):
    """Test adding a comment with an author."""
    comment = service.add_comment(task.id, "Great work!", author="Alice")
    assert comment.author == "Alice"
    assert comment.content == "Great work!"


def test_add_comment_without_author(service, task):
    """Test adding a comment without an author defaults to None."""
    comment = service.add_comment(task.id, "No author here")
    assert comment.author is None


def test_add_comment_persists(manager, tmp_path):
    """Test that added comments persist to storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    service1 = CommentsService(TaskManager(storage))
    task = service1._manager.add("Persistence test")
    comment = service1.add_comment(task.id, "Persisted comment")

    # Create new service with same storage
    service2 = CommentsService(TaskManager(JsonStorage(str(tmp_path / "tasks.json"))))
    fetched_task = service2._manager.get(task.id)
    assert len(fetched_task.comments) == 1
    assert fetched_task.comments[0].content == "Persisted comment"


def test_add_multiple_comments(service, task):
    """Test adding multiple comments to a task."""
    c1 = service.add_comment(task.id, "First")
    c2 = service.add_comment(task.id, "Second")
    c3 = service.add_comment(task.id, "Third")

    comments = service.list_comments(task.id)
    assert len(comments) == 3
    assert comments[0].content == "First"
    assert comments[1].content == "Second"
    assert comments[2].content == "Third"


# Group 2: list_comments() - 5 tests

def test_list_comments_empty(service, task):
    """Test listing comments when none exist."""
    comments = service.list_comments(task.id)
    assert comments == []


def test_list_comments_single(service, task):
    """Test listing a single comment."""
    comment = service.add_comment(task.id, "Only comment")
    comments = service.list_comments(task.id)
    assert len(comments) == 1
    assert comments[0].id == comment.id


def test_list_comments_multiple(service, task):
    """Test listing multiple comments."""
    service.add_comment(task.id, "First")
    service.add_comment(task.id, "Second")
    service.add_comment(task.id, "Third")
    comments = service.list_comments(task.id)
    assert len(comments) == 3


def test_list_comments_sorted_by_created_at(manager):
    """Test that listed comments are sorted by created_at."""
    task = manager.add("Task for sorting")
    service = CommentsService(manager)

    # Add comments with slight delays
    c1 = service.add_comment(task.id, "First")
    # Manually set an older created_at to ensure ordering
    c1_created = c1.created_at - timedelta(seconds=2)
    task.comments[0].created_at = c1_created

    c2 = service.add_comment(task.id, "Second")
    c3 = service.add_comment(task.id, "Third")

    # Re-persist to ensure changes are saved
    manager._persist()

    comments = service.list_comments(task.id)
    assert comments[0].content == "First"
    assert comments[1].content == "Second"
    assert comments[2].content == "Third"


def test_list_comments_nonexistent_task_raises(service):
    """Test that listing comments for nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        service.list_comments("nonexistent-id")


# Group 3: delete_comment() - 5 tests

def test_delete_comment_valid(service, task):
    """Test deleting an existing comment."""
    comment = service.add_comment(task.id, "To be deleted")
    service.delete_comment(task.id, comment.id)
    comments = service.list_comments(task.id)
    assert len(comments) == 0


def test_delete_comment_nonexistent_comment_raises(service, task):
    """Test that deleting nonexistent comment raises CommentNotFoundError."""
    with pytest.raises(CommentNotFoundError, match="Comment .* not found"):
        service.delete_comment(task.id, "nonexistent-comment-id")


def test_delete_comment_nonexistent_task_raises(service):
    """Test that deleting comment from nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        service.delete_comment("nonexistent-task", "some-comment-id")


def test_delete_comment_removes_only_matching(service, task):
    """Test that only the matching comment is removed."""
    c1 = service.add_comment(task.id, "Keep this")
    c2 = service.add_comment(task.id, "Delete this")
    c3 = service.add_comment(task.id, "Keep this too")

    service.delete_comment(task.id, c2.id)
    comments = service.list_comments(task.id)
    assert len(comments) == 2
    assert comments[0].id == c1.id
    assert comments[1].id == c3.id


def test_delete_comment_persists(manager, tmp_path):
    """Test that deleted comments persist to storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    service1 = CommentsService(TaskManager(storage))
    task = service1._manager.add("Delete test")
    comment = service1.add_comment(task.id, "To delete")

    service1.delete_comment(task.id, comment.id)

    # Create new service with same storage
    service2 = CommentsService(TaskManager(JsonStorage(str(tmp_path / "tasks.json"))))
    fetched_task = service2._manager.get(task.id)
    assert len(fetched_task.comments) == 0


# Group 4: edit_comment() - 7 tests

def test_edit_comment_valid(service, task):
    """Test editing an existing comment."""
    comment = service.add_comment(task.id, "Original")
    edited = service.edit_comment(task.id, comment.id, "Updated")
    assert edited.content == "Updated"
    assert edited.id == comment.id


def test_edit_comment_strips_whitespace(service, task):
    """Test that edited content is stripped of whitespace."""
    comment = service.add_comment(task.id, "Original")
    edited = service.edit_comment(task.id, comment.id, "  padded  ")
    assert edited.content == "padded"


def test_edit_comment_empty_new_content_raises(service, task):
    """Test that empty new content raises ValueError."""
    comment = service.add_comment(task.id, "Original")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        service.edit_comment(task.id, comment.id, "")


def test_edit_comment_whitespace_only_raises(service, task):
    """Test that whitespace-only new content raises ValueError."""
    comment = service.add_comment(task.id, "Original")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        service.edit_comment(task.id, comment.id, "   ")


def test_edit_comment_nonexistent_comment_raises(service, task):
    """Test that editing nonexistent comment raises CommentNotFoundError."""
    with pytest.raises(CommentNotFoundError, match="Comment .* not found"):
        service.edit_comment(task.id, "nonexistent-comment-id", "new content")


def test_edit_comment_nonexistent_task_raises(service):
    """Test that editing comment in nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        service.edit_comment("nonexistent-task", "some-comment-id", "new content")


def test_edit_comment_updates_timestamp(service, task):
    """Test that editing a comment updates the updated_at timestamp."""
    comment = service.add_comment(task.id, "Original")
    original_updated_at = comment.updated_at

    # Wait a tiny bit to ensure timestamp changes
    import time
    time.sleep(0.01)

    edited = service.edit_comment(task.id, comment.id, "Updated")
    assert edited.updated_at is not None
    # The updated_at should be set (even if original was None)
    assert edited.updated_at > comment.created_at


# Group 5: Integration - 3 tests

def test_cascade_delete_removes_comments(manager):
    """Test that deleting a task removes all its comments."""
    service = CommentsService(manager)
    task = manager.add("Task to delete")
    service.add_comment(task.id, "Comment 1")
    service.add_comment(task.id, "Comment 2")

    manager.delete(task.id)
    with pytest.raises(TaskNotFoundError):
        service.list_comments(task.id)


def test_task_serialization_preserves_comments(manager, tmp_path):
    """Test that task serialization/deserialization preserves comments."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    service = CommentsService(TaskManager(storage))
    task = service._manager.add("Serialization test")
    service.add_comment(task.id, "Comment 1", author="Alice")
    service.add_comment(task.id, "Comment 2", author="Bob")

    # Load from fresh storage
    service2 = CommentsService(TaskManager(JsonStorage(str(tmp_path / "tasks.json"))))
    fetched_task = service2._manager.get(task.id)
    comments = service2.list_comments(fetched_task.id)

    assert len(comments) == 2
    assert comments[0].content == "Comment 1"
    assert comments[0].author == "Alice"
    assert comments[1].content == "Comment 2"
    assert comments[1].author == "Bob"


def test_multiple_tasks_have_independent_comments(service, manager):
    """Test that comments on different tasks are independent."""
    task1 = manager.add("Task 1")
    task2 = manager.add("Task 2")

    service.add_comment(task1.id, "Comment on task 1")
    service.add_comment(task2.id, "Comment on task 2")

    comments1 = service.list_comments(task1.id)
    comments2 = service.list_comments(task2.id)

    assert len(comments1) == 1
    assert len(comments2) == 1
    assert comments1[0].content == "Comment on task 1"
    assert comments2[0].content == "Comment on task 2"
