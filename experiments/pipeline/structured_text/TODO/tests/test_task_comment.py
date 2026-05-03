import pytest
from datetime import datetime, timezone
from src.models.task_comment import TaskComment


class TestTaskCommentDefaults:
    """Tests for TaskComment default field initialization."""

    def test_comment_requires_task_id_and_content(self):
        """TaskComment requires task_id and content; other fields have defaults."""
        comment = TaskComment(task_id="task-123", content="Great job!")
        assert comment.task_id == "task-123"
        assert comment.content == "Great job!"
        assert comment.id is not None
        assert comment.author is None
        assert comment.created_at is not None
        assert comment.updated_at is None

    def test_comment_unique_ids(self):
        """Each comment gets a unique UUID."""
        c1 = TaskComment(task_id="t1", content="first")
        c2 = TaskComment(task_id="t1", content="second")
        assert c1.id != c2.id

    def test_comment_created_at_is_utc(self):
        """created_at uses UTC timezone."""
        comment = TaskComment(task_id="t1", content="test")
        assert comment.created_at.tzinfo is not None
        assert comment.created_at.tzinfo == timezone.utc

    def test_comment_with_author(self):
        """TaskComment can have an optional author."""
        comment = TaskComment(task_id="t1", content="comment", author="Alice")
        assert comment.author == "Alice"

    def test_comment_updated_at_default_none(self):
        """updated_at defaults to None."""
        comment = TaskComment(task_id="t1", content="test")
        assert comment.updated_at is None

    def test_comment_updated_at_can_be_set(self):
        """updated_at can be explicitly set."""
        now = datetime.now(timezone.utc)
        comment = TaskComment(task_id="t1", content="test", updated_at=now)
        assert comment.updated_at == now


class TestTaskCommentSerialization:
    """Tests for TaskComment.to_dict() and from_dict()."""

    def test_to_dict_minimal(self):
        """to_dict() with minimal fields (no author, no updated_at)."""
        comment = TaskComment(task_id="task-1", content="Hello", id="c-123",
                              created_at=datetime(2025, 5, 3, 12, 0, 0, tzinfo=timezone.utc))
        result = comment.to_dict()
        assert result["id"] == "c-123"
        assert result["task_id"] == "task-1"
        assert result["content"] == "Hello"
        assert result["author"] is None
        assert "created_at" in result
        assert "updated_at" not in result

    def test_to_dict_with_author(self):
        """to_dict() includes author when present."""
        comment = TaskComment(task_id="t1", content="test", author="Bob", id="c-1",
                              created_at=datetime(2025, 5, 3, 12, 0, 0, tzinfo=timezone.utc))
        result = comment.to_dict()
        assert result["author"] == "Bob"

    def test_to_dict_with_updated_at(self):
        """to_dict() includes updated_at when present."""
        created = datetime(2025, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        updated = datetime(2025, 5, 4, 14, 30, 0, tzinfo=timezone.utc)
        comment = TaskComment(task_id="t1", content="test", id="c-1",
                              created_at=created, updated_at=updated)
        result = comment.to_dict()
        assert "updated_at" in result
        assert result["updated_at"] == updated.isoformat()

    def test_to_dict_created_at_isoformat(self):
        """created_at is converted to ISO format string."""
        created = datetime(2025, 5, 3, 12, 30, 45, tzinfo=timezone.utc)
        comment = TaskComment(task_id="t1", content="test", id="c-1", created_at=created)
        result = comment.to_dict()
        assert result["created_at"] == "2025-05-03T12:30:45+00:00"

    def test_from_dict_minimal(self):
        """from_dict() with required fields only."""
        data = {
            "id": "c-123",
            "task_id": "t-456",
            "content": "Test comment",
            "created_at": "2025-05-03T12:00:00+00:00"
        }
        comment = TaskComment.from_dict(data)
        assert comment.id == "c-123"
        assert comment.task_id == "t-456"
        assert comment.content == "Test comment"
        assert comment.author is None
        assert comment.updated_at is None
        assert comment.created_at == datetime(2025, 5, 3, 12, 0, 0, tzinfo=timezone.utc)

    def test_from_dict_with_author(self):
        """from_dict() includes author when present."""
        data = {
            "id": "c-1",
            "task_id": "t-1",
            "content": "comment",
            "author": "Charlie",
            "created_at": "2025-05-03T12:00:00+00:00"
        }
        comment = TaskComment.from_dict(data)
        assert comment.author == "Charlie"

    def test_from_dict_with_updated_at(self):
        """from_dict() includes updated_at when present."""
        data = {
            "id": "c-1",
            "task_id": "t-1",
            "content": "comment",
            "author": None,
            "created_at": "2025-05-03T12:00:00+00:00",
            "updated_at": "2025-05-04T14:30:00+00:00"
        }
        comment = TaskComment.from_dict(data)
        assert comment.updated_at == datetime(2025, 5, 4, 14, 30, 0, tzinfo=timezone.utc)

    def test_from_dict_missing_id_raises(self):
        """from_dict() raises KeyError if 'id' is missing."""
        data = {
            "task_id": "t-1",
            "content": "comment",
            "created_at": "2025-05-03T12:00:00+00:00"
        }
        with pytest.raises(KeyError):
            TaskComment.from_dict(data)

    def test_from_dict_missing_task_id_raises(self):
        """from_dict() raises KeyError if 'task_id' is missing."""
        data = {
            "id": "c-1",
            "content": "comment",
            "created_at": "2025-05-03T12:00:00+00:00"
        }
        with pytest.raises(KeyError):
            TaskComment.from_dict(data)

    def test_from_dict_missing_content_raises(self):
        """from_dict() raises KeyError if 'content' is missing."""
        data = {
            "id": "c-1",
            "task_id": "t-1",
            "created_at": "2025-05-03T12:00:00+00:00"
        }
        with pytest.raises(KeyError):
            TaskComment.from_dict(data)

    def test_from_dict_missing_created_at_raises(self):
        """from_dict() raises KeyError if 'created_at' is missing."""
        data = {
            "id": "c-1",
            "task_id": "t-1",
            "content": "comment"
        }
        with pytest.raises(KeyError):
            TaskComment.from_dict(data)


class TestTaskCommentRoundtrip:
    """Tests for to_dict() → from_dict() round-trip consistency."""

    def test_roundtrip_minimal(self):
        """Round-trip with minimal fields."""
        original = TaskComment(task_id="t-1", content="hello")
        restored = TaskComment.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.content == original.content
        assert restored.author == original.author
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at

    def test_roundtrip_with_author(self):
        """Round-trip with author."""
        original = TaskComment(task_id="t-1", content="comment", author="Diana")
        restored = TaskComment.from_dict(original.to_dict())
        assert restored.author == "Diana"

    def test_roundtrip_with_updated_at(self):
        """Round-trip with updated_at."""
        now = datetime.now(timezone.utc)
        original = TaskComment(task_id="t-1", content="edited", updated_at=now)
        restored = TaskComment.from_dict(original.to_dict())
        assert restored.updated_at == original.updated_at

    def test_roundtrip_complete(self):
        """Full round-trip with all fields."""
        created = datetime(2025, 5, 3, 10, 0, 0, tzinfo=timezone.utc)
        updated = datetime(2025, 5, 3, 11, 0, 0, tzinfo=timezone.utc)
        original = TaskComment(
            id="c-abc123",
            task_id="t-xyz789",
            content="Detailed comment",
            author="Eve",
            created_at=created,
            updated_at=updated
        )
        restored = TaskComment.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.content == original.content
        assert restored.author == original.author
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at


class TestTaskCommentBackwardCompatibility:
    """Tests for loading legacy data without new fields."""

    def test_from_dict_old_format_without_author(self):
        """Load comment data that has no author field."""
        old_data = {
            "id": "c-old",
            "task_id": "t-1",
            "content": "old comment",
            "created_at": "2025-01-01T00:00:00+00:00"
        }
        comment = TaskComment.from_dict(old_data)
        assert comment.author is None
        assert comment.updated_at is None

    def test_from_dict_old_format_without_updated_at(self):
        """Load comment data that has no updated_at field."""
        old_data = {
            "id": "c-old",
            "task_id": "t-1",
            "content": "old comment",
            "author": "Frank",
            "created_at": "2025-01-01T00:00:00+00:00"
        }
        comment = TaskComment.from_dict(old_data)
        assert comment.updated_at is None


class TestTaskCommentTimezoneHandling:
    """Tests for timezone-aware datetime handling."""

    def test_created_at_preserves_timezone_on_roundtrip(self):
        """Timezone info is preserved through serialization."""
        utc_now = datetime.now(timezone.utc)
        comment = TaskComment(task_id="t-1", content="test", id="c-1", created_at=utc_now)
        restored = TaskComment.from_dict(comment.to_dict())
        assert restored.created_at.tzinfo is not None
        assert restored.created_at == utc_now

    def test_updated_at_preserves_timezone_on_roundtrip(self):
        """updated_at timezone is preserved through serialization."""
        utc_now = datetime.now(timezone.utc)
        comment = TaskComment(task_id="t-1", content="test", id="c-1", updated_at=utc_now)
        restored = TaskComment.from_dict(comment.to_dict())
        assert restored.updated_at.tzinfo is not None
        assert restored.updated_at == utc_now

    def test_created_at_is_always_utc(self):
        """created_at default is always UTC."""
        comment = TaskComment(task_id="t-1", content="test")
        assert comment.created_at.tzinfo == timezone.utc
