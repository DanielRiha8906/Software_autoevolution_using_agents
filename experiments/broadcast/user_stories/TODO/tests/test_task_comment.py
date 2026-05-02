import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_comment import TaskComment, CEST


class TestTaskCommentCreation:
    def test_create_with_required_fields(self):
        comment = TaskComment(
            task_id="task-123",
            content="This is a comment"
        )
        assert comment.task_id == "task-123"
        assert comment.content == "This is a comment"
        assert comment.id is not None
        assert comment.author is None
        assert comment.updated_at is None
        assert comment.created_at is not None

    def test_create_with_all_fields(self):
        now = datetime.now(CEST)
        later = now + timedelta(hours=1)
        comment = TaskComment(
            task_id="task-456",
            content="Updated comment",
            author="John",
            created_at=now,
            updated_at=later
        )
        assert comment.task_id == "task-456"
        assert comment.content == "Updated comment"
        assert comment.author == "John"
        assert comment.created_at == now
        assert comment.updated_at == later

    def test_create_with_explicit_id(self):
        comment = TaskComment(
            id="custom-id",
            task_id="task-789",
            content="Test content"
        )
        assert comment.id == "custom-id"

    def test_created_at_defaults_to_cest(self):
        comment = TaskComment(
            task_id="task-123",
            content="Comment text"
        )
        assert comment.created_at.tzinfo == CEST

    def test_unique_ids_for_different_comments(self):
        comment1 = TaskComment(task_id="task-1", content="Comment 1")
        comment2 = TaskComment(task_id="task-2", content="Comment 2")
        assert comment1.id != comment2.id

    def test_reject_empty_content(self):
        with pytest.raises(ValueError, match="content cannot be empty"):
            TaskComment(task_id="task-123", content="")

    def test_reject_whitespace_only_content(self):
        with pytest.raises(ValueError, match="content cannot be empty"):
            TaskComment(task_id="task-123", content="   ")

    def test_reject_empty_task_id(self):
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            TaskComment(task_id="", content="Some content")

    def test_reject_whitespace_only_task_id(self):
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            TaskComment(task_id="   ", content="Some content")


class TestTaskCommentSerialization:
    def test_to_dict(self):
        comment = TaskComment(
            id="comment-123",
            task_id="task-456",
            content="Test content",
            author="Alice"
        )
        data = comment.to_dict()
        assert data["id"] == "comment-123"
        assert data["task_id"] == "task-456"
        assert data["content"] == "Test content"
        assert data["author"] == "Alice"
        assert data["created_at"] is not None
        assert data["updated_at"] is None

    def test_to_dict_with_updated_at(self):
        now = datetime.now(CEST)
        comment = TaskComment(
            task_id="task-123",
            content="Comment",
            updated_at=now
        )
        data = comment.to_dict()
        assert data["updated_at"] == now.isoformat()

    def test_from_dict(self):
        original_data = {
            "id": "comment-123",
            "task_id": "task-456",
            "content": "Test content",
            "author": "Bob",
            "created_at": datetime.now(CEST).isoformat(),
            "updated_at": None
        }
        comment = TaskComment.from_dict(original_data)
        assert comment.id == "comment-123"
        assert comment.task_id == "task-456"
        assert comment.content == "Test content"
        assert comment.author == "Bob"
        assert comment.updated_at is None

    def test_roundtrip_serialization(self):
        comment = TaskComment(
            task_id="task-789",
            content="Round trip test",
            author="Charlie"
        )
        restored = TaskComment.from_dict(comment.to_dict())
        assert restored.id == comment.id
        assert restored.task_id == comment.task_id
        assert restored.content == comment.content
        assert restored.author == comment.author
        assert restored.created_at == comment.created_at
        assert restored.updated_at == comment.updated_at

    def test_roundtrip_with_updated_at(self):
        now = datetime.now(CEST)
        later = now + timedelta(minutes=30)
        comment = TaskComment(
            task_id="task-999",
            content="Updated content",
            author="Dave",
            created_at=now,
            updated_at=later
        )
        restored = TaskComment.from_dict(comment.to_dict())
        assert restored.id == comment.id
        assert restored.task_id == comment.task_id
        assert restored.content == comment.content
        assert restored.author == comment.author
        assert restored.created_at == comment.created_at
        assert restored.updated_at == comment.updated_at

    def test_from_dict_without_author(self):
        data = {
            "id": "comment-123",
            "task_id": "task-456",
            "content": "No author",
            "created_at": datetime.now(CEST).isoformat(),
        }
        comment = TaskComment.from_dict(data)
        assert comment.author is None

    def test_from_dict_with_invalid_updated_at(self):
        data = {
            "id": "comment-123",
            "task_id": "task-456",
            "content": "Test",
            "created_at": datetime.now(CEST).isoformat(),
            "updated_at": "invalid-date"
        }
        with pytest.raises(ValueError, match="Invalid updated_at format"):
            TaskComment.from_dict(data)


class TestTaskCommentTimezone:
    def test_cest_timezone_on_creation(self):
        comment = TaskComment(task_id="task-123", content="Test")
        assert comment.created_at.tzinfo == CEST

    def test_cest_offset(self):
        # CEST is UTC+2
        expected_offset = timedelta(hours=2)
        assert CEST.utcoffset(None) == expected_offset

    def test_custom_created_at_preserved(self):
        custom_time = datetime(2024, 5, 1, 12, 0, 0, tzinfo=CEST)
        comment = TaskComment(
            task_id="task-123",
            content="Test",
            created_at=custom_time
        )
        assert comment.created_at == custom_time

    def test_optional_author_field(self):
        comment_without_author = TaskComment(
            task_id="task-123",
            content="No author"
        )
        assert comment_without_author.author is None

        comment_with_author = TaskComment(
            task_id="task-123",
            content="Has author",
            author="Eve"
        )
        assert comment_with_author.author == "Eve"

    def test_optional_updated_at_field(self):
        comment_no_update = TaskComment(
            task_id="task-123",
            content="Never updated"
        )
        assert comment_no_update.updated_at is None

        updated_time = datetime.now(CEST) + timedelta(hours=2)
        comment_with_update = TaskComment(
            task_id="task-123",
            content="Updated content",
            updated_at=updated_time
        )
        assert comment_with_update.updated_at == updated_time
