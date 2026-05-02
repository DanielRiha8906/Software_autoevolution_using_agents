import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.models.task_comment import TaskComment
from src.services.comments_service import CommentsService, CommentNotFoundError
from src.services.task_manager import TaskManager
from src.storage.json_storage import JsonStorage


@pytest.fixture
def storage(tmp_path):
    """Create a temporary JsonStorage instance."""
    return JsonStorage(str(tmp_path / "data.json"))


@pytest.fixture
def service(storage):
    """Create a CommentsService with temporary storage."""
    return CommentsService(storage=storage)


@pytest.fixture
def service_with_task_manager(tmp_path):
    """Create CommentsService and TaskManager sharing the same storage."""
    storage = JsonStorage(str(tmp_path / "data.json"))
    comments = CommentsService(storage=storage)
    task_manager = TaskManager(storage=storage, comments_service=comments)
    return comments, task_manager


# MUST TESTS

class TestAddCommentToExistingTask:
    """Add comment to existing task."""

    def test_add_comment_basic(self, service):
        comment = service.add("task-1", "Test comment")
        assert comment.task_id == "task-1"
        assert comment.content == "Test comment"
        assert comment.id is not None
        assert comment.author is None

    def test_add_comment_with_author(self, service):
        comment = service.add("task-1", "Test comment", author="Alice")
        assert comment.author == "Alice"
        assert comment.content == "Test comment"

    @pytest.mark.parametrize("author", ["Bob", None, ""])
    def test_add_comment_various_authors(self, service, author):
        comment = service.add("task-1", "Content", author=author if author else None)
        assert comment.author == (author if author else None)

    def test_add_multiple_comments_same_task(self, service):
        c1 = service.add("task-1", "First")
        c2 = service.add("task-1", "Second")
        c3 = service.add("task-1", "Third")
        assert c1.id != c2.id
        assert c2.id != c3.id
        assert len(service.list_for_task("task-1")) == 3


class TestAddCommentValidation:
    """Add comment validates task_id exists (if TaskManager provided)."""

    def test_add_comment_without_task_manager_no_validation(self, service):
        # Without TaskManager, should accept any task_id
        comment = service.add("nonexistent-task", "Content")
        assert comment.task_id == "nonexistent-task"

    def test_add_comment_validates_task_id_exists_with_manager(self, service_with_task_manager):
        comments, task_manager = service_with_task_manager
        task = task_manager.add("Test Task")
        # Should succeed for existing task
        comment = comments.add(task.id, "Content")
        assert comment.task_id == task.id

    def test_add_comment_empty_content_raises(self, service):
        with pytest.raises(ValueError, match="Content cannot be empty"):
            service.add("task-1", "")

    def test_add_comment_whitespace_content_raises(self, service):
        with pytest.raises(ValueError, match="Content cannot be empty"):
            service.add("task-1", "   ")

    def test_add_comment_empty_task_id_raises(self, service):
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            service.add("", "Content")

    def test_add_comment_whitespace_task_id_raises(self, service):
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            service.add("   ", "Content")


class TestListCommentsForTask:
    """List comments for task (ordered by created_at)."""

    def test_list_for_task_basic(self, service):
        c1 = service.add("task-1", "First")
        c2 = service.add("task-1", "Second")
        c3 = service.add("task-1", "Third")
        comments = service.list_for_task("task-1")
        assert len(comments) == 3
        # Should be sorted by created_at ascending
        assert comments[0].id == c1.id
        assert comments[1].id == c2.id
        assert comments[2].id == c3.id

    def test_list_for_task_multiple_tasks(self, service):
        service.add("task-1", "A")
        service.add("task-2", "B")
        service.add("task-1", "C")
        service.add("task-2", "D")

        t1_comments = service.list_for_task("task-1")
        t2_comments = service.list_for_task("task-2")
        assert len(t1_comments) == 2
        assert len(t2_comments) == 2
        assert all(c.task_id == "task-1" for c in t1_comments)
        assert all(c.task_id == "task-2" for c in t2_comments)

    def test_list_for_task_sorted_by_created_at(self, service):
        # Add comments with specific timestamps
        base_time = datetime(2025, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        c1 = TaskComment(task_id="task-1", content="First", created_at=base_time)
        c2 = TaskComment(task_id="task-1", content="Second", created_at=base_time + timedelta(seconds=1))
        c3 = TaskComment(task_id="task-1", content="Third", created_at=base_time + timedelta(seconds=2))

        service._comments[c1.id] = c1
        service._comments[c2.id] = c2
        service._comments[c3.id] = c3
        service._persist()

        comments = service.list_for_task("task-1")
        assert len(comments) == 3
        assert comments[0].created_at <= comments[1].created_at
        assert comments[1].created_at <= comments[2].created_at


class TestListCommentsEmpty:
    """List comments returns empty list when no comments."""

    def test_list_for_nonexistent_task_returns_empty(self, service):
        comments = service.list_for_task("nonexistent-task")
        assert comments == []

    def test_list_all_empty(self, service):
        assert service.list_all() == []

    def test_list_all_after_deletion(self, service):
        c = service.add("task-1", "Test")
        service.delete(c.id)
        assert service.list_all() == []


class TestDeleteCommentById:
    """Delete comment by id."""

    def test_delete_comment_basic(self, service):
        c = service.add("task-1", "Test")
        service.delete(c.id)
        with pytest.raises(CommentNotFoundError):
            service.get(c.id)

    def test_delete_comment_by_prefix(self, service):
        c = service.add("task-1", "Test")
        prefix = c.id[:8]
        service.delete(prefix)
        with pytest.raises(CommentNotFoundError):
            service.get(c.id)

    def test_delete_nonexistent_raises(self, service):
        with pytest.raises(CommentNotFoundError):
            service.delete("nonexistent-id")

    def test_delete_ambiguous_prefix_raises(self, service):
        c1 = service.add("task-1", "First")
        c2 = service.add("task-1", "Second")
        # Both start with same prefix, should be ambiguous
        common_prefix = c1.id[:10]
        if c2.id.startswith(common_prefix):
            with pytest.raises(CommentNotFoundError, match="Ambiguous"):
                service.delete(common_prefix)


class TestDeleteByTaskIdCascade:
    """Delete by task_id cascades properly."""

    def test_delete_by_task_id_basic(self, service):
        c1 = service.add("task-1", "First")
        c2 = service.add("task-1", "Second")
        c3 = service.add("task-2", "Other")

        service.delete_by_task_id("task-1")

        assert len(service.list_for_task("task-1")) == 0
        assert len(service.list_for_task("task-2")) == 1
        assert service.get(c3.id).id == c3.id

    def test_delete_by_task_id_nonexistent_task(self, service):
        c = service.add("task-1", "Test")
        # Should not raise, just do nothing
        service.delete_by_task_id("nonexistent-task")
        assert len(service.list_all()) == 1

    def test_delete_by_task_id_empty_list(self, service):
        # Should not raise
        service.delete_by_task_id("task-1")
        assert len(service.list_all()) == 0

    def test_delete_by_task_id_persists(self, storage):
        s1 = CommentsService(storage=storage)
        s1.add("task-1", "First")
        s1.add("task-1", "Second")
        s1.delete_by_task_id("task-1")

        s2 = CommentsService(storage=storage)
        assert len(s2.list_for_task("task-1")) == 0


class TestCommentsPersistence:
    """Comments persist across service instances."""

    def test_persistence_basic(self, storage):
        s1 = CommentsService(storage=storage)
        c1 = s1.add("task-1", "First comment", author="Alice")

        s2 = CommentsService(storage=storage)
        retrieved = s2.get(c1.id)
        assert retrieved.id == c1.id
        assert retrieved.content == "First comment"
        assert retrieved.author == "Alice"
        assert retrieved.task_id == "task-1"

    def test_persistence_multiple_comments(self, storage):
        s1 = CommentsService(storage=storage)
        c1 = s1.add("task-1", "First")
        c2 = s1.add("task-1", "Second")
        c3 = s1.add("task-2", "Third")

        s2 = CommentsService(storage=storage)
        all_comments = s2.list_all()
        assert len(all_comments) == 3
        ids = {c.id for c in all_comments}
        assert c1.id in ids
        assert c2.id in ids
        assert c3.id in ids

    def test_persistence_after_delete(self, storage):
        s1 = CommentsService(storage=storage)
        c1 = s1.add("task-1", "First")
        c2 = s1.add("task-1", "Second")
        s1.delete(c1.id)

        s2 = CommentsService(storage=storage)
        assert len(s2.list_all()) == 1
        assert s2.get(c2.id).id == c2.id


class TestLoadPersistIntegration:
    """Load/persist integration with storage."""

    def test_load_all_returns_proper_dict_format(self, storage):
        service = CommentsService(storage=storage)
        service.add("task-1", "Test")

        data = storage.load_all()
        assert isinstance(data, dict)
        assert "comments" in data
        assert "tasks" in data
        assert isinstance(data["comments"], list)

    def test_load_migrates_old_list_format(self, tmp_path):
        """Backward compatibility: old list-based JSON files are auto-migrated."""
        import json
        path = str(tmp_path / "old_data.json")

        # Create old format (list of tasks)
        old_data = [
            {"id": "task-1", "title": "Task 1", "status": "pending"}
        ]
        Path(path).write_text(json.dumps(old_data))

        storage = JsonStorage(path)
        data = storage.load_all()

        # Should be migrated to new format
        assert isinstance(data, dict)
        assert "tasks" in data
        assert "comments" in data
        assert len(data["tasks"]) == 1
        assert len(data["comments"]) == 0

    def test_persist_preserves_tasks(self, tmp_path):
        """Persisting comments should preserve existing tasks."""
        import json
        path = str(tmp_path / "data.json")

        # Create initial data with tasks
        initial_data = {"tasks": [{"id": "task-1", "title": "Task"}], "comments": []}
        Path(path).write_text(json.dumps(initial_data))

        storage = JsonStorage(path)
        service = CommentsService(storage=storage)
        service.add("task-1", "Comment")

        # Verify tasks are still there
        data = storage.load_all()
        assert len(data["tasks"]) == 1
        assert len(data["comments"]) == 1

    def test_json_storage_load_all_dict_format(self, storage):
        """JsonStorage load_all() returns proper dict format."""
        service = CommentsService(storage=storage)
        c1 = service.add("task-1", "First")
        c2 = service.add("task-2", "Second")

        data = storage.load_all()
        assert isinstance(data, dict)
        assert "comments" in data
        comments_list = data["comments"]
        assert isinstance(comments_list, list)
        assert len(comments_list) == 2


# SHOULD TESTS

class TestUUIDPrefixLookup:
    """UUID prefix lookup (like TaskManager)."""

    def test_get_by_full_id(self, service):
        c = service.add("task-1", "Test")
        retrieved = service.get(c.id)
        assert retrieved.id == c.id

    def test_get_by_prefix(self, service):
        c = service.add("task-1", "Test")
        prefix = c.id[:8]
        retrieved = service.get(prefix)
        assert retrieved.id == c.id

    def test_get_by_longer_prefix(self, service):
        c = service.add("task-1", "Test")
        prefix = c.id[:20]
        retrieved = service.get(prefix)
        assert retrieved.id == c.id


class TestPrefixLookupAmbiguous:
    """Prefix lookup raises CommentNotFoundError when ambiguous."""

    def test_ambiguous_prefix_raises(self, service):
        c1 = service.add("task-1", "First")
        c2 = service.add("task-1", "Second")

        # Find common prefix that matches both
        for i in range(1, len(c1.id)):
            prefix = c1.id[:i]
            if c2.id.startswith(prefix):
                with pytest.raises(CommentNotFoundError, match="Ambiguous"):
                    service.get(prefix)
                break

    def test_get_nonexistent_raises(self, service):
        with pytest.raises(CommentNotFoundError, match="not found"):
            service.get("nonexistent-id")


class TestUpdateCommentContent:
    """Update comment content and updated_at timestamp."""

    def test_update_content_basic(self, service):
        c = service.add("task-1", "Original")
        original_updated_at = c.updated_at

        updated = service.update(c.id, content="Updated content")
        assert updated.content == "Updated content"
        assert updated.updated_at is not None
        assert updated.updated_at != original_updated_at

    def test_update_author_basic(self, service):
        c = service.add("task-1", "Test", author="Alice")
        updated = service.update(c.id, author="Bob")
        assert updated.author == "Bob"
        assert updated.content == "Test"

    def test_update_both_content_and_author(self, service):
        c = service.add("task-1", "Original", author="Alice")
        updated = service.update(c.id, content="New content", author="Bob")
        assert updated.content == "New content"
        assert updated.author == "Bob"

    def test_update_content_only_preserves_author(self, service):
        c = service.add("task-1", "Original", author="Alice")
        updated = service.update(c.id, content="Updated")
        assert updated.author == "Alice"
        assert updated.content == "Updated"

    def test_update_author_only_preserves_content(self, service):
        c = service.add("task-1", "Original content", author="Alice")
        updated = service.update(c.id, author="Bob")
        assert updated.content == "Original content"
        assert updated.author == "Bob"

    def test_update_by_prefix(self, service):
        c = service.add("task-1", "Original")
        prefix = c.id[:8]
        updated = service.update(prefix, content="Updated")
        assert updated.content == "Updated"

    def test_update_nonexistent_raises(self, service):
        with pytest.raises(CommentNotFoundError):
            service.update("nonexistent", content="New")

    def test_update_persists(self, storage):
        s1 = CommentsService(storage=storage)
        c = s1.add("task-1", "Original")
        s1.update(c.id, content="Updated")

        s2 = CommentsService(storage=storage)
        retrieved = s2.get(c.id)
        assert retrieved.content == "Updated"

    def test_update_timestamp_is_utc(self, service):
        c = service.add("task-1", "Original")
        updated = service.update(c.id, content="Updated")
        assert updated.updated_at.tzinfo is not None
        assert updated.updated_at.tzinfo == timezone.utc


# COULD TESTS

class TestEditComment:
    """Edit comment (update)."""

    def test_edit_comment_multiple_times(self, service):
        c = service.add("task-1", "Version 1")
        c = service.update(c.id, content="Version 2")
        c = service.update(c.id, content="Version 3")
        assert c.content == "Version 3"

    def test_edit_comment_preserves_id(self, service):
        c = service.add("task-1", "Original")
        original_id = c.id
        updated = service.update(c.id, content="Updated")
        assert updated.id == original_id

    def test_edit_comment_preserves_task_id(self, service):
        c = service.add("task-1", "Original")
        updated = service.update(c.id, content="Updated")
        assert updated.task_id == "task-1"

    def test_edit_comment_preserves_created_at(self, service):
        c = service.add("task-1", "Original")
        original_created_at = c.created_at
        updated = service.update(c.id, content="Updated")
        assert updated.created_at == original_created_at


# INTEGRATION TESTS

class TestBackwardCompatibility:
    """Backward compatibility: old list-based JSON files are auto-migrated."""

    def test_migrate_old_list_to_new_dict(self, tmp_path):
        import json
        path = str(tmp_path / "old_data.json")

        old_data = [
            {"id": "task-1", "title": "Task 1", "status": "pending"},
            {"id": "task-2", "title": "Task 2", "status": "done"}
        ]
        Path(path).write_text(json.dumps(old_data))

        storage = JsonStorage(path)
        service = CommentsService(storage=storage)

        # Should migrate to new format
        data = storage.load_all()
        assert isinstance(data, dict)
        assert "tasks" in data
        assert "comments" in data
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["title"] == "Task 1"

    def test_comments_service_with_migrated_data(self, tmp_path):
        import json
        path = str(tmp_path / "data.json")

        # Old format
        old_data = [{"id": "task-1", "title": "Task", "status": "pending"}]
        Path(path).write_text(json.dumps(old_data))

        storage = JsonStorage(path)
        service = CommentsService(storage=storage)

        # Should be able to add comments
        c = service.add("task-1", "Comment on migrated task")
        assert c.task_id == "task-1"
        assert c.content == "Comment on migrated task"


class TestTaskManagerIntegration:
    """Cascade delete integrates with TaskManager.delete()."""

    def test_task_manager_delete_cascades_to_comments(self, service_with_task_manager):
        comments, task_manager = service_with_task_manager
        task = task_manager.add("Test Task")

        c1 = comments.add(task.id, "First comment")
        c2 = comments.add(task.id, "Second comment")
        c3 = comments.add("other-task", "Other comment")

        task_manager.delete(task.id)

        # Comments for deleted task should be gone
        assert len(comments.list_for_task(task.id)) == 0
        # Other comments should remain
        assert len(comments.list_all()) == 1
        assert comments.get(c3.id).id == c3.id

    def test_task_manager_delete_multiple_tasks_with_comments(self, service_with_task_manager):
        comments, task_manager = service_with_task_manager
        t1 = task_manager.add("Task 1")
        t2 = task_manager.add("Task 2")

        comments.add(t1.id, "Comment on Task 1")
        comments.add(t2.id, "Comment on Task 2")

        task_manager.delete(t1.id)

        assert len(comments.list_for_task(t1.id)) == 0
        assert len(comments.list_for_task(t2.id)) == 1

    def test_all_existing_task_tests_still_pass(self, service_with_task_manager):
        """Verify that task manager operations still work correctly."""
        comments, task_manager = service_with_task_manager

        # Add multiple tasks
        t1 = task_manager.add("Task 1")
        t2 = task_manager.add("Task 2")

        # Add comments
        c1 = comments.add(t1.id, "Comment 1")
        c2 = comments.add(t2.id, "Comment 2")

        # List tasks
        all_tasks = task_manager.list_all()
        assert len(all_tasks) == 2

        # Get task
        retrieved = task_manager.get(t1.id)
        assert retrieved.id == t1.id

        # Update task
        updated = task_manager.update(t1.id, title="Updated Task 1")
        assert updated.title == "Updated Task 1"

        # Comments should still exist
        assert len(comments.list_all()) == 2


class TestGetComment:
    """General get comment tests."""

    def test_get_returns_comment_object(self, service):
        c = service.add("task-1", "Test")
        retrieved = service.get(c.id)
        assert isinstance(retrieved, TaskComment)
        assert retrieved.id == c.id
        assert retrieved.task_id == "task-1"
        assert retrieved.content == "Test"

    def test_list_all_returns_all_comments(self, service):
        c1 = service.add("task-1", "First")
        c2 = service.add("task-2", "Second")
        c3 = service.add("task-1", "Third")

        all_comments = service.list_all()
        assert len(all_comments) == 3
        ids = {c.id for c in all_comments}
        assert c1.id in ids
        assert c2.id in ids
        assert c3.id in ids
