import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.models.task_comment import TaskComment, CEST
from src.services.comments_service import CommentsService, CommentNotFoundError
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.storage.json_storage import JsonStorage


class TestCommentsServiceAddComment:
    def test_add_comment_to_existing_task(self, tmp_path):
        """Add a comment to a task that exists."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment = service.add_comment(task.id, "Great task!")
        assert comment.task_id == task.id
        assert comment.content == "Great task!"
        assert comment.author is None
        assert comment.id is not None

    def test_add_comment_with_author(self, tmp_path):
        """Add a comment with an author."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment = service.add_comment(task.id, "Good work!", author="Alice")
        assert comment.author == "Alice"

    def test_add_comment_to_nonexistent_task_raises(self, tmp_path):
        """Adding a comment to a nonexistent task raises TaskNotFoundError."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        with pytest.raises(TaskNotFoundError):
            service.add_comment("nonexistent-id", "This should fail")

    def test_add_comment_with_empty_content_raises(self, tmp_path):
        """Adding a comment with empty content raises ValueError."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        with pytest.raises(ValueError, match="content cannot be empty"):
            service.add_comment(task.id, "")

    def test_add_multiple_comments_to_same_task(self, tmp_path):
        """Add multiple comments to the same task."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment1 = service.add_comment(task.id, "First comment")
        comment2 = service.add_comment(task.id, "Second comment")

        assert comment1.id != comment2.id
        assert comment1.task_id == task.id
        assert comment2.task_id == task.id

    def test_add_comments_to_different_tasks(self, tmp_path):
        """Add comments to different tasks."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task1 = task_manager.add("Task 1")
        task2 = task_manager.add("Task 2")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment1 = service.add_comment(task1.id, "Comment on task 1")
        comment2 = service.add_comment(task2.id, "Comment on task 2")

        assert comment1.task_id == task1.id
        assert comment2.task_id == task2.id


class TestCommentsServiceListComments:
    def test_list_comments_for_task_ordered_by_created_at(self, tmp_path):
        """List comments for a task, ordered by created_at ascending."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        # Add comments with controlled timestamps
        now = datetime.now(CEST)
        comment1 = TaskComment(
            task_id=task.id, content="First", created_at=now - timedelta(minutes=2)
        )
        comment2 = TaskComment(
            task_id=task.id, content="Second", created_at=now - timedelta(minutes=1)
        )
        comment3 = TaskComment(task_id=task.id, content="Third", created_at=now)

        service._comments[comment1.id] = comment1
        service._comments[comment2.id] = comment2
        service._comments[comment3.id] = comment3
        service._persist()

        comments = service.list_comments(task.id)
        assert len(comments) == 3
        assert comments[0].content == "First"
        assert comments[1].content == "Second"
        assert comments[2].content == "Third"

    def test_list_comments_empty_for_task_with_no_comments(self, tmp_path):
        """List comments returns empty list for task with no comments."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comments = service.list_comments(task.id)
        assert comments == []

    def test_list_comments_filters_by_task_id(self, tmp_path):
        """List comments only returns comments for the specified task."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task1 = task_manager.add("Task 1")
        task2 = task_manager.add("Task 2")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        service.add_comment(task1.id, "Comment on task 1")
        service.add_comment(task2.id, "Comment on task 2")
        service.add_comment(task1.id, "Another comment on task 1")

        task1_comments = service.list_comments(task1.id)
        task2_comments = service.list_comments(task2.id)

        assert len(task1_comments) == 2
        assert len(task2_comments) == 1
        assert all(c.task_id == task1.id for c in task1_comments)
        assert all(c.task_id == task2.id for c in task2_comments)


class TestCommentsServiceDeleteComment:
    def test_delete_comment_by_id(self, tmp_path):
        """Delete a comment by its ID."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment = service.add_comment(task.id, "Comment to delete")
        assert len(service.list_comments(task.id)) == 1

        service.delete_comment(comment.id)
        assert len(service.list_comments(task.id)) == 0

    def test_delete_nonexistent_comment_raises(self, tmp_path):
        """Delete a nonexistent comment raises CommentNotFoundError."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        with pytest.raises(CommentNotFoundError, match="Comment"):
            service.delete_comment("nonexistent-id")

    def test_delete_comment_persists_to_storage(self, tmp_path):
        """Deleting a comment persists the deletion to storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service1 = CommentsService(task_manager, comments_storage)
        comment = service1.add_comment(task.id, "Comment to delete")

        # Delete and verify it's gone
        service1.delete_comment(comment.id)

        # Create a new service instance to verify persistence
        service2 = CommentsService(task_manager, comments_storage)
        assert len(service2.list_comments(task.id)) == 0

    def test_delete_one_of_multiple_comments(self, tmp_path):
        """Delete one comment while keeping others."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment1 = service.add_comment(task.id, "Keep this")
        comment2 = service.add_comment(task.id, "Delete this")
        comment3 = service.add_comment(task.id, "Keep this too")

        service.delete_comment(comment2.id)

        remaining = service.list_comments(task.id)
        assert len(remaining) == 2
        assert comment1.id in [c.id for c in remaining]
        assert comment3.id in [c.id for c in remaining]
        assert comment2.id not in [c.id for c in remaining]


class TestCommentsServiceDeleteCommentsForTask:
    def test_delete_all_comments_for_task(self, tmp_path):
        """Delete all comments for a task."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        service.add_comment(task.id, "Comment 1")
        service.add_comment(task.id, "Comment 2")
        service.add_comment(task.id, "Comment 3")
        assert len(service.list_comments(task.id)) == 3

        service.delete_comments_for_task(task.id)
        assert len(service.list_comments(task.id)) == 0

    def test_delete_comments_for_task_with_no_comments(self, tmp_path):
        """Delete comments for a task that has no comments (should not raise)."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        # Should not raise
        service.delete_comments_for_task(task.id)
        assert len(service.list_comments(task.id)) == 0

    def test_delete_comments_does_not_affect_other_tasks(self, tmp_path):
        """Deleting comments for one task doesn't affect comments on other tasks."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task1 = task_manager.add("Task 1")
        task2 = task_manager.add("Task 2")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        service.add_comment(task1.id, "Task 1 comment 1")
        service.add_comment(task1.id, "Task 1 comment 2")
        service.add_comment(task2.id, "Task 2 comment 1")

        service.delete_comments_for_task(task1.id)

        assert len(service.list_comments(task1.id)) == 0
        assert len(service.list_comments(task2.id)) == 1

    def test_delete_comments_for_task_persists(self, tmp_path):
        """Deleting comments for a task persists to storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service1 = CommentsService(task_manager, comments_storage)
        service1.add_comment(task.id, "Comment 1")
        service1.add_comment(task.id, "Comment 2")

        service1.delete_comments_for_task(task.id)

        # Create a new service instance to verify persistence
        service2 = CommentsService(task_manager, comments_storage)
        assert len(service2.list_comments(task.id)) == 0


class TestCommentsServiceEditComment:
    def test_edit_comment_content(self, tmp_path):
        """Edit a comment's content."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment = service.add_comment(task.id, "Original content")
        assert comment.content == "Original content"
        assert comment.updated_at is None

        updated = service.edit_comment(comment.id, "Updated content")
        assert updated.content == "Updated content"
        assert updated.updated_at is not None

    def test_edit_comment_updates_timestamp(self, tmp_path):
        """Editing a comment updates the updated_at timestamp."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment = service.add_comment(task.id, "Original")
        original_created = comment.created_at

        updated = service.edit_comment(comment.id, "Modified")
        assert updated.updated_at is not None
        assert updated.created_at == original_created

    def test_edit_nonexistent_comment_raises(self, tmp_path):
        """Editing a nonexistent comment raises CommentNotFoundError."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        with pytest.raises(CommentNotFoundError):
            service.edit_comment("nonexistent-id", "New content")

    def test_edit_comment_with_empty_content_raises(self, tmp_path):
        """Editing a comment with empty content raises ValueError."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        comment = service.add_comment(task.id, "Original")

        with pytest.raises(ValueError, match="content cannot be empty"):
            service.edit_comment(comment.id, "")

    def test_edit_comment_persists_to_storage(self, tmp_path):
        """Editing a comment persists to storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service1 = CommentsService(task_manager, comments_storage)
        comment = service1.add_comment(task.id, "Original")

        service1.edit_comment(comment.id, "Modified")

        # Create a new service instance to verify persistence
        service2 = CommentsService(task_manager, comments_storage)
        comments = service2.list_comments(task.id)
        assert len(comments) == 1
        assert comments[0].content == "Modified"
        assert comments[0].updated_at is not None


class TestCommentsServicePersistence:
    def test_comments_persist_across_service_instances(self, tmp_path):
        """Comments are persisted and reloaded correctly."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))

        # Add comments with first service
        service1 = CommentsService(task_manager, comments_storage)
        comment1 = service1.add_comment(task.id, "First comment", author="Alice")
        comment2 = service1.add_comment(task.id, "Second comment", author="Bob")

        # Create new service and verify comments are loaded
        service2 = CommentsService(task_manager, comments_storage)
        comments = service2.list_comments(task.id)
        assert len(comments) == 2
        assert comments[0].content == "First comment"
        assert comments[0].author == "Alice"
        assert comments[1].content == "Second comment"
        assert comments[1].author == "Bob"

    def test_comments_ordered_by_created_at_in_storage(self, tmp_path):
        """Comments are ordered by created_at when saved to storage."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Test Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        # Add comments with controlled timestamps
        now = datetime.now(CEST)
        comment1 = TaskComment(
            task_id=task.id, content="First", created_at=now - timedelta(minutes=2)
        )
        comment2 = TaskComment(
            task_id=task.id, content="Second", created_at=now - timedelta(minutes=1)
        )
        comment3 = TaskComment(task_id=task.id, content="Third", created_at=now)

        service._comments[comment1.id] = comment1
        service._comments[comment2.id] = comment2
        service._comments[comment3.id] = comment3
        service._persist()

        # Reload and verify order
        service2 = CommentsService(task_manager, comments_storage)
        raw_data = comments_storage.load()
        assert len(raw_data) == 3
        # Verify they're in order
        assert raw_data[0]["content"] == "First"
        assert raw_data[1]["content"] == "Second"
        assert raw_data[2]["content"] == "Third"


class TestCommentsServiceIntegration:
    def test_task_manager_validation_prevents_orphan_comments(self, tmp_path):
        """Cannot add a comment to a task that doesn't exist."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        # Try to add comment to non-existent task
        with pytest.raises(TaskNotFoundError):
            service.add_comment("fake-task-id", "This should fail")

    def test_full_workflow(self, tmp_path):
        """Test a complete workflow: add task, add comments, edit, delete some."""
        storage = JsonStorage(str(tmp_path / "tasks.json"))
        task_manager = TaskManager(storage)
        task = task_manager.add("Important Task")

        comments_storage = JsonStorage(str(tmp_path / "comments.json"))
        service = CommentsService(task_manager, comments_storage)

        # Add initial comments
        c1 = service.add_comment(task.id, "This looks good", author="Alice")
        c2 = service.add_comment(task.id, "Needs revision", author="Bob")
        c3 = service.add_comment(task.id, "Ready to merge", author="Charlie")

        # Verify all comments exist
        all_comments = service.list_comments(task.id)
        assert len(all_comments) == 3

        # Edit one comment
        service.edit_comment(c2.id, "Actually, this is ready!")
        updated_comments = service.list_comments(task.id)
        assert updated_comments[1].content == "Actually, this is ready!"

        # Delete one comment
        service.delete_comment(c1.id)
        remaining = service.list_comments(task.id)
        assert len(remaining) == 2

        # Delete all remaining comments
        service.delete_comments_for_task(task.id)
        final = service.list_comments(task.id)
        assert len(final) == 0
