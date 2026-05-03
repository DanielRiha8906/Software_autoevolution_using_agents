import pytest
from src.models.task_comment import TaskComment
from src.services.comment_manager import CommentManager, CommentNotFoundError
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def task_manager(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


@pytest.fixture
def comment_manager(task_manager, tmp_path):
    storage = JsonStorage(str(tmp_path / "comments.json"))
    return CommentManager(task_manager, storage)


def test_add_creates_comment(task_manager, comment_manager):
    task = task_manager.add("Test Task")
    comment = comment_manager.add(task.id, "Great task!")
    assert comment.task_id == task.id
    assert comment.content == "Great task!"
    assert comment.id is not None


def test_add_returns_task_comment_object(task_manager, comment_manager):
    task = task_manager.add("Task")
    comment = comment_manager.add(task.id, "Comment")
    assert isinstance(comment, TaskComment)


def test_add_persists_to_storage(task_manager, tmp_path):
    storage_path = str(tmp_path / "comments.json")
    m1 = CommentManager(task_manager, JsonStorage(storage_path))
    task = task_manager.add("Task")
    comment = m1.add(task.id, "Persisted")

    # Create new manager instance from same storage
    m2 = CommentManager(task_manager, JsonStorage(storage_path))
    retrieved = m2.get(comment.id)
    assert retrieved.content == "Persisted"


def test_add_raises_task_not_found(comment_manager):
    with pytest.raises(TaskNotFoundError):
        comment_manager.add("nonexistent-task-id", "Comment")


def test_add_raises_empty_content(task_manager, comment_manager):
    task = task_manager.add("Task")
    with pytest.raises(ValueError):
        comment_manager.add(task.id, "")


def test_add_raises_whitespace_content(task_manager, comment_manager):
    task = task_manager.add("Task")
    with pytest.raises(ValueError):
        comment_manager.add(task.id, "   ")


def test_get_by_exact_id(task_manager, comment_manager):
    task = task_manager.add("Task")
    comment = comment_manager.add(task.id, "Comment")
    retrieved = comment_manager.get(comment.id)
    assert retrieved.id == comment.id
    assert retrieved.content == "Comment"


def test_get_by_prefix_match(task_manager, comment_manager):
    task = task_manager.add("Task")
    comment = comment_manager.add(task.id, "First")
    # Use first 8 chars of ID
    prefix = comment.id[:8]
    retrieved = comment_manager.get(prefix)
    assert retrieved.id == comment.id


def test_get_raises_not_found(comment_manager):
    with pytest.raises(CommentNotFoundError):
        comment_manager.get("nonexistent-id")


def test_get_raises_ambiguous_prefix(task_manager, comment_manager):
    task = task_manager.add("Task")
    c1 = comment_manager.add(task.id, "Comment 1")
    c2 = comment_manager.add(task.id, "Comment 2")
    # Use a prefix that matches both (single char from a shared prefix)
    prefix = c1.id[0]
    # If both comments happen to start with same char, this should be ambiguous
    if c2.id[0] == prefix:
        with pytest.raises(CommentNotFoundError) as exc:
            comment_manager.get(prefix)
        assert "Ambiguous" in str(exc.value)


def test_list_by_task(task_manager, comment_manager):
    task1 = task_manager.add("Task 1")
    task2 = task_manager.add("Task 2")
    c1 = comment_manager.add(task1.id, "Comment 1")
    c2 = comment_manager.add(task1.id, "Comment 2")
    c3 = comment_manager.add(task2.id, "Comment 3")

    task1_comments = comment_manager.list_by_task(task1.id)
    assert len(task1_comments) == 2
    assert c1 in task1_comments
    assert c2 in task1_comments
    assert c3 not in task1_comments


def test_list_by_task_empty(task_manager, comment_manager):
    task = task_manager.add("Task")
    comments = comment_manager.list_by_task(task.id)
    assert comments == []


def test_update_modifies_content(task_manager, comment_manager):
    task = task_manager.add("Task")
    comment = comment_manager.add(task.id, "Original")
    updated = comment_manager.update(comment.id, "Modified")
    assert updated.content == "Modified"


def test_update_sets_updated_at(task_manager, comment_manager):
    task = task_manager.add("Task")
    comment = comment_manager.add(task.id, "Original")
    original_updated = comment.updated_at
    import time
    time.sleep(0.01)  # Small delay to ensure timestamp difference
    updated = comment_manager.update(comment.id, "Modified")
    assert updated.updated_at > original_updated


def test_update_raises_not_found(comment_manager):
    with pytest.raises(CommentNotFoundError):
        comment_manager.update("nonexistent-id", "New content")


def test_update_raises_empty_content(task_manager, comment_manager):
    task = task_manager.add("Task")
    comment = comment_manager.add(task.id, "Content")
    with pytest.raises(ValueError):
        comment_manager.update(comment.id, "")


def test_delete_removes_comment(task_manager, comment_manager):
    task = task_manager.add("Task")
    comment = comment_manager.add(task.id, "Comment")
    comment_manager.delete(comment.id)
    with pytest.raises(CommentNotFoundError):
        comment_manager.get(comment.id)


def test_delete_raises_not_found(comment_manager):
    with pytest.raises(CommentNotFoundError):
        comment_manager.delete("nonexistent-id")


def test_delete_persists(task_manager, tmp_path):
    storage_path = str(tmp_path / "comments.json")
    m1 = CommentManager(task_manager, JsonStorage(storage_path))
    task = task_manager.add("Task")
    comment = m1.add(task.id, "To delete")
    m1.delete(comment.id)

    # Verify deletion persists
    m2 = CommentManager(task_manager, JsonStorage(storage_path))
    with pytest.raises(CommentNotFoundError):
        m2.get(comment.id)
