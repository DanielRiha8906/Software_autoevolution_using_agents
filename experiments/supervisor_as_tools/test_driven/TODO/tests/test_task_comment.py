from datetime import datetime, timezone, timedelta
import uuid
import pytest
from src.models.task_comment import TaskComment, CEST


class TestTaskCommentInstantiation:
    """Test basic TaskComment instantiation and defaults."""

    def test_task_comment_creation_with_required_fields(self):
        """TaskComment can be created with task_id and content."""
        task_id = str(uuid.uuid4())
        content = "This is a test comment"
        comment = TaskComment(task_id=task_id, content=content)

        assert comment.task_id == task_id
        assert comment.content == content
        assert comment.id is not None
        assert isinstance(comment.id, str)
        assert comment.author is None
        assert comment.updated_at is None

    def test_task_comment_default_created_at(self):
        """TaskComment created_at defaults to current time in CEST."""
        before = datetime.now(CEST)
        comment = TaskComment(task_id="test-id", content="Test content")
        after = datetime.now(CEST)

        assert comment.created_at is not None
        assert comment.created_at.tzinfo is not None
        assert before <= comment.created_at <= after
        assert comment.created_at.tzinfo == CEST

    def test_task_comment_unique_ids(self):
        """Each TaskComment gets a unique UUID."""
        task_id = str(uuid.uuid4())
        comment1 = TaskComment(task_id=task_id, content="Comment 1")
        comment2 = TaskComment(task_id=task_id, content="Comment 2")

        assert comment1.id != comment2.id

    def test_task_comment_with_all_fields(self):
        """TaskComment can be created with all optional fields."""
        task_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        created_at = datetime.now(CEST)
        updated_at = datetime.now(CEST)
        author = "test_user"

        comment = TaskComment(
            task_id=task_id,
            content="Full comment",
            id=comment_id,
            created_at=created_at,
            author=author,
            updated_at=updated_at,
        )

        assert comment.id == comment_id
        assert comment.author == author
        assert comment.updated_at == updated_at


class TestTaskCommentValidation:
    """Test TaskComment field validation."""

    def test_empty_content_raises_value_error(self):
        """Creating TaskComment with empty content raises ValueError."""
        with pytest.raises(ValueError, match="Content must not be empty"):
            TaskComment(task_id="test-id", content="")

    def test_whitespace_only_content_raises_value_error(self):
        """Creating TaskComment with whitespace-only content raises ValueError."""
        with pytest.raises(ValueError, match="Content must not be empty"):
            TaskComment(task_id="test-id", content="   ")

    def test_whitespace_only_with_tabs_raises_value_error(self):
        """Creating TaskComment with tab-only content raises ValueError."""
        with pytest.raises(ValueError, match="Content must not be empty"):
            TaskComment(task_id="test-id", content="\t\t")

    def test_naive_datetime_updated_at_raises_value_error(self):
        """Creating TaskComment with naive datetime for updated_at raises ValueError."""
        task_id = str(uuid.uuid4())
        naive_dt = datetime(2025, 5, 2, 12, 0, 0)

        with pytest.raises(ValueError, match="Datetime must be timezone-aware"):
            TaskComment(
                task_id=task_id,
                content="Test",
                updated_at=naive_dt,
            )

    def test_timezone_aware_updated_at_is_valid(self):
        """Creating TaskComment with timezone-aware updated_at succeeds."""
        task_id = str(uuid.uuid4())
        tz_aware_dt = datetime(2025, 5, 2, 12, 0, 0, tzinfo=timezone.utc)

        comment = TaskComment(
            task_id=task_id,
            content="Test",
            updated_at=tz_aware_dt,
        )

        assert comment.updated_at == tz_aware_dt


class TestTaskCommentSerialization:
    """Test TaskComment serialization to dict."""

    def test_to_dict_basic(self):
        """to_dict returns all required fields."""
        task_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        content = "Test comment"
        created_at = datetime(2025, 5, 2, 10, 0, 0, tzinfo=CEST)

        comment = TaskComment(
            task_id=task_id,
            content=content,
            id=comment_id,
            created_at=created_at,
            author="user1",
        )

        result = comment.to_dict()

        assert result["id"] == comment_id
        assert result["task_id"] == task_id
        assert result["content"] == content
        assert result["author"] == "user1"
        assert result["created_at"] == created_at.isoformat()
        assert result["updated_at"] is None

    def test_to_dict_with_updated_at(self):
        """to_dict includes updated_at when it is set."""
        task_id = str(uuid.uuid4())
        created_at = datetime(2025, 5, 1, 10, 0, 0, tzinfo=CEST)
        updated_at = datetime(2025, 5, 2, 15, 0, 0, tzinfo=CEST)

        comment = TaskComment(
            task_id=task_id,
            content="Updated comment",
            created_at=created_at,
            updated_at=updated_at,
        )

        result = comment.to_dict()

        assert result["updated_at"] == updated_at.isoformat()

    def test_to_dict_with_none_author(self):
        """to_dict returns None for author when not set."""
        comment = TaskComment(task_id="task-1", content="Test")
        result = comment.to_dict()
        assert result["author"] is None


class TestTaskCommentDeserialization:
    """Test TaskComment deserialization from dict."""

    def test_from_dict_basic(self):
        """from_dict creates TaskComment from dict with required fields."""
        data = {
            "id": "comment-123",
            "task_id": "task-456",
            "content": "Test comment",
            "author": "user1",
            "created_at": "2025-05-02T10:00:00+02:00",
            "updated_at": None,
        }

        comment = TaskComment.from_dict(data)

        assert comment.id == "comment-123"
        assert comment.task_id == "task-456"
        assert comment.content == "Test comment"
        assert comment.author == "user1"
        assert comment.updated_at is None
        assert comment.created_at.tzinfo is not None

    def test_from_dict_with_updated_at(self):
        """from_dict handles updated_at datetime."""
        data = {
            "id": "comment-123",
            "task_id": "task-456",
            "content": "Updated comment",
            "author": "user1",
            "created_at": "2025-05-01T10:00:00+02:00",
            "updated_at": "2025-05-02T15:00:00+02:00",
        }

        comment = TaskComment.from_dict(data)

        assert comment.updated_at is not None
        assert comment.updated_at.tzinfo is not None

    def test_from_dict_without_author(self):
        """from_dict handles missing author field."""
        data = {
            "id": "comment-123",
            "task_id": "task-456",
            "content": "Test comment",
            "created_at": "2025-05-02T10:00:00+02:00",
            "updated_at": None,
        }

        comment = TaskComment.from_dict(data)

        assert comment.author is None

    def test_from_dict_naive_created_at_raises(self):
        """from_dict raises ValueError for naive created_at datetime."""
        data = {
            "id": "comment-123",
            "task_id": "task-456",
            "content": "Test comment",
            "created_at": "2025-05-02T10:00:00",
            "updated_at": None,
        }

        with pytest.raises(ValueError, match="Datetime must be timezone-aware"):
            TaskComment.from_dict(data)

    def test_from_dict_naive_updated_at_raises(self):
        """from_dict raises ValueError for naive updated_at datetime."""
        data = {
            "id": "comment-123",
            "task_id": "task-456",
            "content": "Test comment",
            "created_at": "2025-05-02T10:00:00+02:00",
            "updated_at": "2025-05-02T15:00:00",
        }

        with pytest.raises(ValueError, match="Datetime must be timezone-aware"):
            TaskComment.from_dict(data)


class TestTaskCommentRoundTrip:
    """Test TaskComment serialization and deserialization round trips."""

    def test_roundtrip_basic_comment(self):
        """TaskComment survives to_dict and from_dict round trip."""
        task_id = str(uuid.uuid4())
        original = TaskComment(
            task_id=task_id,
            content="Round trip test",
            author="test_user",
        )

        data = original.to_dict()
        restored = TaskComment.from_dict(data)

        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.content == original.content
        assert restored.author == original.author
        assert restored.created_at == original.created_at

    def test_roundtrip_comment_with_updated_at(self):
        """TaskComment with updated_at survives round trip."""
        created_at = datetime(2025, 5, 1, 10, 0, 0, tzinfo=CEST)
        updated_at = datetime(2025, 5, 2, 15, 0, 0, tzinfo=CEST)

        original = TaskComment(
            task_id="task-id",
            content="Updated comment",
            created_at=created_at,
            updated_at=updated_at,
            author="editor",
        )

        data = original.to_dict()
        restored = TaskComment.from_dict(data)

        assert restored.updated_at == original.updated_at
        assert restored.content == original.content
        assert restored.author == original.author
