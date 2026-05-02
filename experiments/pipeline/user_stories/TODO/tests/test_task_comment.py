import pytest
from datetime import datetime, timezone
from src.models.task_comment import TaskComment


class TestTaskCommentInstantiation:
    """Test TaskComment creation and default values."""

    def test_create_with_minimal_fields(self):
        """Test creating TaskComment with only required fields."""
        comment = TaskComment(task_id="task-123", content="Great work!")
        assert comment.task_id == "task-123"
        assert comment.content == "Great work!"
        assert comment.id is not None
        assert comment.author is None
        assert comment.updated_at is None

    def test_auto_generated_id(self):
        """Test that id is auto-generated."""
        comment1 = TaskComment(task_id="task-1", content="Comment 1")
        comment2 = TaskComment(task_id="task-1", content="Comment 2")
        assert comment1.id != comment2.id

    def test_auto_generated_created_at(self):
        """Test that created_at is auto-generated."""
        before = datetime.now(timezone.utc)
        comment = TaskComment(task_id="task-1", content="Test")
        after = datetime.now(timezone.utc)
        assert before <= comment.created_at <= after

    def test_create_with_author(self):
        """Test creating TaskComment with author."""
        comment = TaskComment(task_id="task-1", content="Good", author="Alice")
        assert comment.author == "Alice"

    def test_create_with_all_fields(self):
        """Test creating TaskComment with all fields."""
        now = datetime.now(timezone.utc)
        comment = TaskComment(
            id="comment-123",
            task_id="task-456",
            content="Comprehensive comment",
            created_at=now,
            author="Bob",
            updated_at=now,
        )
        assert comment.id == "comment-123"
        assert comment.task_id == "task-456"
        assert comment.content == "Comprehensive comment"
        assert comment.created_at == now
        assert comment.author == "Bob"
        assert comment.updated_at == now


class TestTaskCommentSerialization:
    """Test TaskComment to_dict and from_dict methods."""

    def test_to_dict_with_all_fields(self):
        """Test serialization with all fields populated."""
        now = datetime.now(timezone.utc)
        comment = TaskComment(
            id="comment-1",
            task_id="task-1",
            content="Test comment",
            created_at=now,
            author="Alice",
            updated_at=now,
        )
        result = comment.to_dict()
        assert result["id"] == "comment-1"
        assert result["task_id"] == "task-1"
        assert result["content"] == "Test comment"
        assert result["created_at"] == now.isoformat()
        assert result["author"] == "Alice"
        assert result["updated_at"] == now.isoformat()

    def test_to_dict_with_none_fields(self):
        """Test serialization with optional None fields."""
        comment = TaskComment(task_id="task-1", content="Minimal")
        result = comment.to_dict()
        assert result["author"] is None
        assert result["updated_at"] is None

    def test_from_dict_with_all_fields(self):
        """Test deserialization with all fields."""
        now = datetime.now(timezone.utc)
        data = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Test",
            "created_at": now.isoformat(),
            "author": "Alice",
            "updated_at": now.isoformat(),
        }
        comment = TaskComment.from_dict(data)
        assert comment.id == "comment-1"
        assert comment.task_id == "task-1"
        assert comment.content == "Test"
        assert comment.created_at == now
        assert comment.author == "Alice"
        assert comment.updated_at == now

    def test_from_dict_with_none_fields(self):
        """Test deserialization with None optional fields."""
        now = datetime.now(timezone.utc)
        data = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Test",
            "created_at": now.isoformat(),
            "author": None,
            "updated_at": None,
        }
        comment = TaskComment.from_dict(data)
        assert comment.author is None
        assert comment.updated_at is None

    def test_from_dict_missing_optional_fields(self):
        """Test deserialization handles missing optional fields."""
        now = datetime.now(timezone.utc)
        data = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Test",
            "created_at": now.isoformat(),
        }
        comment = TaskComment.from_dict(data)
        assert comment.author is None
        assert comment.updated_at is None

    def test_roundtrip_serialization(self):
        """Test that to_dict -> from_dict preserves all data."""
        original = TaskComment(
            task_id="task-1",
            content="Roundtrip test",
            author="TestAuthor",
        )
        data = original.to_dict()
        restored = TaskComment.from_dict(data)
        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.content == original.content
        assert restored.created_at == original.created_at
        assert restored.author == original.author
        assert restored.updated_at == original.updated_at

    def test_roundtrip_with_updated_at(self):
        """Test roundtrip with updated_at field set."""
        now = datetime.now(timezone.utc)
        original = TaskComment(
            task_id="task-1",
            content="Updated",
            author="Editor",
            updated_at=now,
        )
        data = original.to_dict()
        restored = TaskComment.from_dict(data)
        assert restored.updated_at == now


class TestTaskCommentValidation:
    """Test TaskComment validation at model and initialization level."""

    def test_accepts_any_task_id(self):
        """Test that from_dict accepts any task_id without validation."""
        data = {
            "id": "comment-1",
            "task_id": "nonexistent-task",
            "content": "Test",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        comment = TaskComment.from_dict(data)
        assert comment.task_id == "nonexistent-task"

    def test_accepts_empty_content_at_model_level(self):
        """Test that model level allows empty content (validation at service)."""
        comment = TaskComment(task_id="task-1", content="")
        assert comment.content == ""

    def test_created_at_is_utc(self):
        """Test that created_at uses UTC timezone."""
        comment = TaskComment(task_id="task-1", content="Test")
        assert comment.created_at.tzinfo is not None
        assert comment.created_at.tzinfo == timezone.utc

    def test_id_is_string(self):
        """Test that id is a string (UUID)."""
        comment = TaskComment(task_id="task-1", content="Test")
        assert isinstance(comment.id, str)
        assert len(comment.id) == 36  # Standard UUID string length with hyphens
