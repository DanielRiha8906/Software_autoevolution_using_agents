import pytest
from datetime import datetime, timezone
from src.services.comments_service import CommentsService, CommentNotFoundError
from src.models.task_comment import TaskComment
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    """Create a CommentsService with a temporary storage file."""
    return CommentsService(JsonStorage(str(tmp_path / "data.json")))


class TestCommentsServiceBasics:
    """Test basic comment operations."""

    def test_add_comment(self, service):
        """Test adding a comment to a task."""
        comment = service.add_comment("task-123", "This is a comment")
        assert comment.task_id == "task-123"
        assert comment.content == "This is a comment"
        assert comment.id is not None
        assert comment.author is None

    def test_add_comment_with_author(self, service):
        """Test adding a comment with an author."""
        comment = service.add_comment("task-123", "Test comment", author="Alice")
        assert comment.author == "Alice"

    def test_add_comment_strips_whitespace(self, service):
        """Test that comment content is stripped of leading/trailing whitespace."""
        comment = service.add_comment("task-123", "  padded content  ")
        assert comment.content == "padded content"

    def test_add_comment_empty_content_raises(self, service):
        """Test that adding a comment with empty content raises ValueError."""
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            service.add_comment("task-123", "")

    def test_add_comment_whitespace_only_raises(self, service):
        """Test that adding a comment with whitespace-only content raises ValueError."""
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            service.add_comment("task-123", "   ")


class TestCommentsServiceList:
    """Test listing comments."""

    def test_list_comments_empty(self, service):
        """Test listing comments when there are none."""
        comments = service.list_comments_by_task("task-123")
        assert comments == []

    def test_list_comments_single(self, service):
        """Test listing a single comment."""
        comment = service.add_comment("task-123", "First comment")
        comments = service.list_comments_by_task("task-123")
        assert len(comments) == 1
        assert comments[0].id == comment.id

    def test_list_comments_multiple(self, service):
        """Test listing multiple comments."""
        c1 = service.add_comment("task-123", "First")
        c2 = service.add_comment("task-123", "Second")
        c3 = service.add_comment("task-123", "Third")

        comments = service.list_comments_by_task("task-123")
        assert len(comments) == 3
        assert comments[0].id == c1.id
        assert comments[1].id == c2.id
        assert comments[2].id == c3.id

    def test_list_comments_ordered_by_created_at(self, service):
        """Test that comments are ordered by created_at ascending."""
        c1 = service.add_comment("task-123", "First")
        c2 = service.add_comment("task-123", "Second")
        c3 = service.add_comment("task-123", "Third")

        comments = service.list_comments_by_task("task-123")
        assert comments[0].created_at <= comments[1].created_at
        assert comments[1].created_at <= comments[2].created_at

    def test_list_comments_filters_by_task(self, service):
        """Test that listing only returns comments for the specified task."""
        service.add_comment("task-123", "For task 1")
        service.add_comment("task-456", "For task 2")
        service.add_comment("task-123", "Another for task 1")

        comments_123 = service.list_comments_by_task("task-123")
        comments_456 = service.list_comments_by_task("task-456")

        assert len(comments_123) == 2
        assert len(comments_456) == 1
        assert all(c.task_id == "task-123" for c in comments_123)
        assert all(c.task_id == "task-456" for c in comments_456)


class TestCommentsServiceGet:
    """Test getting a comment by ID."""

    def test_get_comment(self, service):
        """Test getting a comment by its ID."""
        comment = service.add_comment("task-123", "Test comment")
        retrieved = service.get_comment(comment.id)
        assert retrieved.id == comment.id
        assert retrieved.content == comment.content

    def test_get_comment_not_found(self, service):
        """Test that getting a non-existent comment raises CommentNotFoundError."""
        with pytest.raises(CommentNotFoundError, match="Comment.*not found"):
            service.get_comment("non-existent-id")


class TestCommentsServiceDelete:
    """Test deleting comments."""

    def test_delete_comment(self, service):
        """Test deleting a comment."""
        comment = service.add_comment("task-123", "To be deleted")
        service.delete_comment(comment.id)

        with pytest.raises(CommentNotFoundError):
            service.get_comment(comment.id)

    def test_delete_comment_not_found(self, service):
        """Test that deleting a non-existent comment raises CommentNotFoundError."""
        with pytest.raises(CommentNotFoundError, match="Comment.*not found"):
            service.delete_comment("non-existent-id")

    def test_delete_comments_by_task(self, service):
        """Test cascade delete: deleting all comments for a task."""
        service.add_comment("task-123", "Comment 1")
        service.add_comment("task-123", "Comment 2")
        service.add_comment("task-456", "Comment on different task")

        service.delete_comments_by_task("task-123")

        assert len(service.list_comments_by_task("task-123")) == 0
        assert len(service.list_comments_by_task("task-456")) == 1

    def test_delete_comments_by_task_no_comments(self, service):
        """Test cascade delete when a task has no comments."""
        # Should not raise
        service.delete_comments_by_task("task-with-no-comments")


class TestCommentsServiceUpdate:
    """Test updating comments."""

    def test_update_comment(self, service):
        """Test updating a comment's content."""
        comment = service.add_comment("task-123", "Original content")
        updated = service.update_comment(comment.id, "Updated content")

        assert updated.content == "Updated content"
        assert updated.updated_at is not None

    def test_update_comment_sets_updated_at(self, service):
        """Test that updating a comment sets the updated_at field."""
        comment = service.add_comment("task-123", "Original")
        original_updated_at = comment.updated_at

        updated = service.update_comment(comment.id, "Updated")
        assert updated.updated_at is not None
        # updated_at should be more recent than before (or at least equal)
        assert updated.updated_at >= comment.created_at

    def test_update_comment_strips_whitespace(self, service):
        """Test that updating a comment strips whitespace."""
        comment = service.add_comment("task-123", "Original")
        updated = service.update_comment(comment.id, "  New content  ")
        assert updated.content == "New content"

    def test_update_comment_empty_content_raises(self, service):
        """Test that updating with empty content raises ValueError."""
        comment = service.add_comment("task-123", "Original")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            service.update_comment(comment.id, "")

    def test_update_comment_not_found(self, service):
        """Test that updating a non-existent comment raises CommentNotFoundError."""
        with pytest.raises(CommentNotFoundError, match="Comment.*not found"):
            service.update_comment("non-existent-id", "New content")


class TestCommentsServicePersistence:
    """Test that comments are persisted to storage."""

    def test_comments_persisted_to_storage(self, tmp_path):
        """Test that comments are saved to storage and can be reloaded."""
        path = str(tmp_path / "data.json")
        service1 = CommentsService(JsonStorage(path))
        comment = service1.add_comment("task-123", "Persisted comment", author="Alice")
        comment_id = comment.id

        # Create a new service instance with the same storage
        service2 = CommentsService(JsonStorage(path))
        retrieved = service2.get_comment(comment_id)

        assert retrieved.id == comment_id
        assert retrieved.content == "Persisted comment"
        assert retrieved.author == "Alice"

    def test_multiple_comments_persisted(self, tmp_path):
        """Test that multiple comments are persisted correctly."""
        path = str(tmp_path / "data.json")
        service1 = CommentsService(JsonStorage(path))
        c1 = service1.add_comment("task-123", "First")
        c2 = service1.add_comment("task-123", "Second")
        c3 = service1.add_comment("task-456", "For other task")

        service2 = CommentsService(JsonStorage(path))
        comments_123 = service2.list_comments_by_task("task-123")
        comments_456 = service2.list_comments_by_task("task-456")

        assert len(comments_123) == 2
        assert len(comments_456) == 1

    def test_deleted_comments_not_persisted(self, tmp_path):
        """Test that deleted comments don't appear after reload."""
        path = str(tmp_path / "data.json")
        service1 = CommentsService(JsonStorage(path))
        comment = service1.add_comment("task-123", "To be deleted")
        comment_id = comment.id
        service1.delete_comment(comment_id)

        service2 = CommentsService(JsonStorage(path))
        with pytest.raises(CommentNotFoundError):
            service2.get_comment(comment_id)
