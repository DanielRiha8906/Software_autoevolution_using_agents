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


# Comment operation tests
def test_add_comment_creates_and_persists(service):
    """Test that add_comment creates a comment and persists it."""
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Great task!", author="Alice")
    assert comment.content == "Great task!"
    assert comment.author == "Alice"
    assert comment.task_id == task.id


def test_add_comment_empty_content_raises(service):
    """Test that add_comment rejects empty content."""
    task = service.add_task("Task")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        service.add_comment(task.id, "")


def test_add_comment_whitespace_only_raises(service):
    """Test that add_comment rejects whitespace-only content."""
    task = service.add_task("Task")
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        service.add_comment(task.id, "   ")


def test_add_comment_nonexistent_task_raises(service):
    """Test that add_comment raises for nonexistent task."""
    with pytest.raises(TaskNotFoundError):
        service.add_comment("nonexistent-id", "Comment text")


def test_add_comment_strips_whitespace(service):
    """Test that add_comment strips whitespace from content."""
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "  padded content  ")
    assert comment.content == "padded content"


def test_add_comment_without_author(service):
    """Test adding a comment without specifying author."""
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "No author")
    assert comment.author is None


def test_add_multiple_comments_to_task(service):
    """Test adding multiple comments to the same task."""
    task = service.add_task("Task")
    comment1 = service.add_comment(task.id, "First comment", author="Alice")
    comment2 = service.add_comment(task.id, "Second comment", author="Bob")
    retrieved_task = service.get_task(task.id)
    assert len(retrieved_task.comments) == 2
    assert retrieved_task.comments[0].id == comment1.id
    assert retrieved_task.comments[1].id == comment2.id


def test_comment_persists_across_retrieval(service):
    """Test that comments persist after being added and task is re-retrieved."""
    task = service.add_task("Task")
    service.add_comment(task.id, "Persistent comment", author="Alice")
    retrieved = service.get_task(task.id)
    assert len(retrieved.comments) == 1
    assert retrieved.comments[0].content == "Persistent comment"
    assert retrieved.comments[0].author == "Alice"


def test_get_task_comments_returns_all(service):
    """Test get_task_comments returns all comments for a task."""
    task = service.add_task("Task")
    service.add_comment(task.id, "Comment 1", author="Alice")
    service.add_comment(task.id, "Comment 2", author="Bob")
    service.add_comment(task.id, "Comment 3", author="Charlie")
    comments = service.get_task_comments(task.id)
    assert len(comments) == 3
    assert comments[0].content == "Comment 1"
    assert comments[1].content == "Comment 2"
    assert comments[2].content == "Comment 3"


def test_get_task_comments_empty_for_new_task(service):
    """Test get_task_comments returns empty list for task with no comments."""
    task = service.add_task("Task")
    comments = service.get_task_comments(task.id)
    assert comments == []


def test_get_task_comments_nonexistent_task_raises(service):
    """Test get_task_comments raises for nonexistent task."""
    with pytest.raises(TaskNotFoundError):
        service.get_task_comments("nonexistent-id")


def test_delete_comment_removes_from_task(service):
    """Test delete_comment removes a comment from a task."""
    task = service.add_task("Task")
    comment1 = service.add_comment(task.id, "Keep this", author="Alice")
    comment2 = service.add_comment(task.id, "Delete this", author="Bob")
    service.delete_comment(task.id, comment2.id)
    comments = service.get_task_comments(task.id)
    assert len(comments) == 1
    assert comments[0].id == comment1.id


def test_delete_comment_nonexistent_comment_raises(service):
    """Test delete_comment raises for nonexistent comment."""
    task = service.add_task("Task")
    with pytest.raises(ValueError, match="Comment .* not found"):
        service.delete_comment(task.id, "nonexistent-comment")


def test_delete_comment_nonexistent_task_raises(service):
    """Test delete_comment raises for nonexistent task."""
    with pytest.raises(TaskNotFoundError):
        service.delete_comment("nonexistent-task", "some-comment")


def test_delete_comment_persists(service):
    """Test that deleted comment stays deleted after retrieval."""
    task = service.add_task("Task")
    comment = service.add_comment(task.id, "Temporary")
    service.delete_comment(task.id, comment.id)
    retrieved = service.get_task(task.id)
    assert len(retrieved.comments) == 0
