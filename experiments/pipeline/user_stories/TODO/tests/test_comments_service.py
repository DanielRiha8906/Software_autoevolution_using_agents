import pytest

from src.services.comments_service import CommentsService
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def task_manager(tmp_path):
    """Fixture providing TaskManager with isolated JSON storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


@pytest.fixture
def comments_service(task_manager):
    """Fixture providing CommentsService sharing the task_manager."""
    return CommentsService(task_manager)


# ============================================================================
# add_comment tests (8 tests)
# ============================================================================

def test_add_comment_creates_and_persists(comments_service, task_manager):
    """Test that add_comment creates a comment and persists it."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "Great task!", author="Alice")
    assert comment.content == "Great task!"
    assert comment.author == "Alice"
    assert comment.task_id == task.id
    assert comment.id is not None
    assert comment.created_at is not None


def test_add_comment_empty_content_raises(comments_service, task_manager):
    """Test that add_comment rejects empty content."""
    task = task_manager.add("Test Task")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        comments_service.add_comment(task.id, "")


def test_add_comment_whitespace_only_raises(comments_service, task_manager):
    """Test that add_comment rejects whitespace-only content."""
    task = task_manager.add("Test Task")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        comments_service.add_comment(task.id, "   ")


def test_add_comment_nonexistent_task_raises(comments_service):
    """Test that add_comment raises TaskNotFoundError for nonexistent task."""
    with pytest.raises(TaskNotFoundError):
        comments_service.add_comment("nonexistent-id", "Comment text")


def test_add_comment_strips_whitespace(comments_service, task_manager):
    """Test that add_comment strips whitespace from content."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "  padded content  ")
    assert comment.content == "padded content"


def test_add_comment_without_author(comments_service, task_manager):
    """Test adding a comment without specifying author."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "No author")
    assert comment.author is None


def test_add_multiple_comments_to_task(comments_service, task_manager):
    """Test adding multiple comments to the same task."""
    task = task_manager.add("Test Task")
    comment1 = comments_service.add_comment(task.id, "First comment", author="Alice")
    comment2 = comments_service.add_comment(task.id, "Second comment", author="Bob")
    retrieved_task = task_manager.get(task.id)
    assert len(retrieved_task.comments) == 2
    assert retrieved_task.comments[0].id == comment1.id
    assert retrieved_task.comments[1].id == comment2.id


def test_add_comment_persists_across_retrieval(comments_service, task_manager):
    """Test that comments persist after being added and task is re-retrieved."""
    task = task_manager.add("Test Task")
    comments_service.add_comment(task.id, "Persistent comment", author="Alice")
    retrieved = task_manager.get(task.id)
    assert len(retrieved.comments) == 1
    assert retrieved.comments[0].content == "Persistent comment"
    assert retrieved.comments[0].author == "Alice"


def test_add_comment_generates_unique_ids(comments_service, task_manager):
    """Test that each comment gets a unique ID."""
    task = task_manager.add("Test Task")
    c1 = comments_service.add_comment(task.id, "Comment 1")
    c2 = comments_service.add_comment(task.id, "Comment 2")
    c3 = comments_service.add_comment(task.id, "Comment 3")
    ids = {c1.id, c2.id, c3.id}
    assert len(ids) == 3  # All IDs are unique


# ============================================================================
# list_comments tests (4 tests)
# ============================================================================

def test_list_comments_returns_all(comments_service, task_manager):
    """Test list_comments returns all comments for a task."""
    task = task_manager.add("Test Task")
    comments_service.add_comment(task.id, "Comment 1", author="Alice")
    comments_service.add_comment(task.id, "Comment 2", author="Bob")
    comments_service.add_comment(task.id, "Comment 3", author="Charlie")
    comments = comments_service.list_comments(task.id)
    assert len(comments) == 3
    assert comments[0].content == "Comment 1"
    assert comments[1].content == "Comment 2"
    assert comments[2].content == "Comment 3"


def test_list_comments_empty_for_new_task(comments_service, task_manager):
    """Test list_comments returns empty list for task with no comments."""
    task = task_manager.add("Test Task")
    comments = comments_service.list_comments(task.id)
    assert comments == []


def test_list_comments_preserves_order(comments_service, task_manager):
    """Test list_comments preserves creation order."""
    task = task_manager.add("Test Task")
    ids = []
    for i in range(5):
        comment = comments_service.add_comment(task.id, f"Comment {i}")
        ids.append(comment.id)
    comments = comments_service.list_comments(task.id)
    assert [c.id for c in comments] == ids


def test_list_comments_nonexistent_task_raises(comments_service):
    """Test list_comments raises TaskNotFoundError for nonexistent task."""
    with pytest.raises(TaskNotFoundError):
        comments_service.list_comments("nonexistent-id")


# ============================================================================
# delete_comment tests (5 tests)
# ============================================================================

def test_delete_comment_removes_from_task(comments_service, task_manager):
    """Test delete_comment removes a comment from a task."""
    task = task_manager.add("Test Task")
    comment1 = comments_service.add_comment(task.id, "Keep this", author="Alice")
    comment2 = comments_service.add_comment(task.id, "Delete this", author="Bob")
    comments_service.delete_comment(task.id, comment2.id)
    comments = comments_service.list_comments(task.id)
    assert len(comments) == 1
    assert comments[0].id == comment1.id


def test_delete_comment_nonexistent_comment_raises(comments_service, task_manager):
    """Test delete_comment raises ValueError for nonexistent comment."""
    task = task_manager.add("Test Task")
    with pytest.raises(ValueError, match="Comment .* not found"):
        comments_service.delete_comment(task.id, "nonexistent-comment")


def test_delete_comment_nonexistent_task_raises(comments_service):
    """Test delete_comment raises TaskNotFoundError for nonexistent task."""
    with pytest.raises(TaskNotFoundError):
        comments_service.delete_comment("nonexistent-task", "some-comment")


def test_delete_comment_persists(comments_service, task_manager):
    """Test that deleted comment stays deleted after retrieval."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "Temporary")
    comments_service.delete_comment(task.id, comment.id)
    retrieved = task_manager.get(task.id)
    assert len(retrieved.comments) == 0


# ============================================================================
# edit_comment tests (8 tests)
# ============================================================================

def test_edit_comment_updates_content(comments_service, task_manager):
    """Test edit_comment updates comment content."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "Original content")
    updated = comments_service.edit_comment(task.id, comment.id, "New content")
    assert updated.content == "New content"
    assert updated.id == comment.id


def test_edit_comment_empty_content_raises(comments_service, task_manager):
    """Test edit_comment rejects empty content."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "Original")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        comments_service.edit_comment(task.id, comment.id, "")


def test_edit_comment_whitespace_only_raises(comments_service, task_manager):
    """Test edit_comment rejects whitespace-only content."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "Original")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        comments_service.edit_comment(task.id, comment.id, "   ")


def test_edit_comment_nonexistent_comment_raises(comments_service, task_manager):
    """Test edit_comment raises ValueError for nonexistent comment."""
    task = task_manager.add("Test Task")
    with pytest.raises(ValueError, match="Comment .* not found"):
        comments_service.edit_comment(task.id, "nonexistent-id", "New content")


def test_edit_comment_nonexistent_task_raises(comments_service):
    """Test edit_comment raises TaskNotFoundError for nonexistent task."""
    with pytest.raises(TaskNotFoundError):
        comments_service.edit_comment("nonexistent-task", "some-comment", "content")


def test_edit_comment_strips_whitespace(comments_service, task_manager):
    """Test edit_comment strips whitespace from new content."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "Original")
    updated = comments_service.edit_comment(task.id, comment.id, "  trimmed  ")
    assert updated.content == "trimmed"


def test_edit_comment_updates_timestamp(comments_service, task_manager):
    """Test edit_comment updates the updated_at timestamp."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "Original")
    # New comments have updated_at = None initially
    assert comment.updated_at is None
    updated = comments_service.edit_comment(task.id, comment.id, "Modified")
    # After edit, updated_at should be set
    assert updated.updated_at is not None


def test_edit_comment_persists(comments_service, task_manager):
    """Test that edited comment changes persist after retrieval."""
    task = task_manager.add("Test Task")
    comment = comments_service.add_comment(task.id, "Original")
    comments_service.edit_comment(task.id, comment.id, "Changed")
    retrieved = task_manager.get(task.id)
    assert len(retrieved.comments) == 1
    assert retrieved.comments[0].content == "Changed"


# ============================================================================
# cascade delete tests (2 tests)
# ============================================================================

def test_cascade_delete_removes_comments_on_task_delete(comments_service, task_manager):
    """Test that comments are removed when task is deleted (implicit cascade)."""
    task = task_manager.add("Task with comments")
    comments_service.add_comment(task.id, "Comment 1")
    comments_service.add_comment(task.id, "Comment 2")
    comments_service.add_comment(task.id, "Comment 3")

    # Verify comments exist
    assert len(comments_service.list_comments(task.id)) == 3

    # Delete the task
    task_manager.delete(task.id)

    # Verify task is gone (and implicitly, comments are gone)
    with pytest.raises(TaskNotFoundError):
        task_manager.get(task.id)


def test_cascade_delete_comments_not_in_other_tasks(comments_service, task_manager):
    """Test that deleting one task doesn't affect comments on other tasks."""
    task1 = task_manager.add("Task 1")
    task2 = task_manager.add("Task 2")

    c1 = comments_service.add_comment(task1.id, "Comment on task 1")
    c2 = comments_service.add_comment(task2.id, "Comment on task 2")

    # Delete task1
    task_manager.delete(task1.id)

    # Verify task2's comment still exists
    comments = comments_service.list_comments(task2.id)
    assert len(comments) == 1
    assert comments[0].id == c2.id
