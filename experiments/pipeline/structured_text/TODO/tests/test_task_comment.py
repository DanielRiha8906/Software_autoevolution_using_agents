import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_comment import TaskComment


def test_task_comment_creation():
    """Test that TaskComment can be created with required fields."""
    comment = TaskComment(task_id="task-123", content="This is a comment")
    assert comment.task_id == "task-123"
    assert comment.content == "This is a comment"
    assert comment.id is not None
    assert comment.created_at is not None


def test_task_comment_auto_generated_id():
    """Test that TaskComment has an auto-generated UUID id."""
    comment = TaskComment(task_id="task-123", content="Comment")
    assert comment.id is not None
    assert isinstance(comment.id, str)
    assert len(comment.id) > 0


def test_task_comment_auto_generated_created_at():
    """Test that TaskComment has an auto-generated created_at timestamp."""
    before = datetime.now(timezone(timedelta(hours=2)))
    comment = TaskComment(task_id="task-123", content="Comment")
    after = datetime.now(timezone(timedelta(hours=2)))

    assert comment.created_at is not None
    assert isinstance(comment.created_at, datetime)
    assert before <= comment.created_at <= after


def test_task_comment_created_at_uses_cest_timezone():
    """Test that created_at uses CEST (UTC+2) timezone."""
    comment = TaskComment(task_id="task-123", content="Comment")
    cest = timezone(timedelta(hours=2))
    assert comment.created_at.tzinfo == cest


def test_task_comment_unique_ids():
    """Test that different TaskComment instances have unique ids."""
    comment1 = TaskComment(task_id="task-123", content="Comment 1")
    comment2 = TaskComment(task_id="task-123", content="Comment 2")
    assert comment1.id != comment2.id


def test_task_comment_to_dict():
    """Test that TaskComment can be serialized to dict."""
    comment = TaskComment(
        task_id="task-123",
        content="This is a test comment",
        id="comment-id-456",
        created_at=datetime(2026, 5, 2, 10, 30, 0, tzinfo=timezone(timedelta(hours=2)))
    )
    result = comment.to_dict()

    assert result["id"] == "comment-id-456"
    assert result["task_id"] == "task-123"
    assert result["content"] == "This is a test comment"
    assert result["created_at"] == "2026-05-02T10:30:00+02:00"


def test_task_comment_from_dict():
    """Test that TaskComment can be deserialized from dict."""
    data = {
        "id": "comment-id-456",
        "task_id": "task-123",
        "content": "This is a test comment",
        "created_at": "2026-05-02T10:30:00+02:00"
    }
    comment = TaskComment.from_dict(data)

    assert comment.id == "comment-id-456"
    assert comment.task_id == "task-123"
    assert comment.content == "This is a test comment"
    assert comment.created_at == datetime(2026, 5, 2, 10, 30, 0, tzinfo=timezone(timedelta(hours=2)))


def test_task_comment_serialization_roundtrip():
    """Test that TaskComment survives serialization and deserialization."""
    original = TaskComment(
        task_id="task-789",
        content="Round trip test"
    )
    restored = TaskComment.from_dict(original.to_dict())

    assert restored.id == original.id
    assert restored.task_id == original.task_id
    assert restored.content == original.content
    assert restored.created_at == original.created_at


def test_task_comment_datetime_iso_format():
    """Test that created_at is serialized in ISO 8601 format."""
    created_at = datetime(2026, 5, 2, 14, 45, 30, tzinfo=timezone(timedelta(hours=2)))
    comment = TaskComment(
        task_id="task-123",
        content="Test",
        created_at=created_at
    )
    result = comment.to_dict()

    assert result["created_at"] == "2026-05-02T14:45:30+02:00"


def test_task_comment_empty_content_validation():
    """Test that empty content raises ValueError."""
    data = {
        "id": "comment-id",
        "task_id": "task-123",
        "content": "",
        "created_at": "2026-05-02T10:30:00+02:00"
    }
    with pytest.raises(ValueError, match="Content cannot be empty"):
        TaskComment.from_dict(data)


def test_task_comment_whitespace_content_validation():
    """Test that whitespace-only content raises ValueError."""
    data = {
        "id": "comment-id",
        "task_id": "task-123",
        "content": "   ",
        "created_at": "2026-05-02T10:30:00+02:00"
    }
    with pytest.raises(ValueError, match="Content cannot be empty"):
        TaskComment.from_dict(data)


def test_task_comment_missing_id():
    """Test that missing id field raises ValueError."""
    data = {
        "task_id": "task-123",
        "content": "Test comment",
        "created_at": "2026-05-02T10:30:00+02:00"
    }
    with pytest.raises(ValueError, match="Missing required field: id"):
        TaskComment.from_dict(data)


def test_task_comment_missing_task_id():
    """Test that missing task_id field raises ValueError."""
    data = {
        "id": "comment-id",
        "content": "Test comment",
        "created_at": "2026-05-02T10:30:00+02:00"
    }
    with pytest.raises(ValueError, match="Missing required field: task_id"):
        TaskComment.from_dict(data)


def test_task_comment_missing_content():
    """Test that missing content field raises ValueError."""
    data = {
        "id": "comment-id",
        "task_id": "task-123",
        "created_at": "2026-05-02T10:30:00+02:00"
    }
    with pytest.raises(ValueError, match="Missing required field: content"):
        TaskComment.from_dict(data)


def test_task_comment_missing_created_at():
    """Test that missing created_at field raises ValueError."""
    data = {
        "id": "comment-id",
        "task_id": "task-123",
        "content": "Test comment"
    }
    with pytest.raises(ValueError, match="Missing required field: created_at"):
        TaskComment.from_dict(data)


def test_task_comment_invalid_created_at_format():
    """Test that invalid created_at format raises ValueError."""
    data = {
        "id": "comment-id",
        "task_id": "task-123",
        "content": "Test comment",
        "created_at": "not-a-date"
    }
    with pytest.raises(ValueError, match="Invalid created_at format"):
        TaskComment.from_dict(data)


def test_task_comment_with_explicit_id():
    """Test that TaskComment can be created with explicit id."""
    comment = TaskComment(
        task_id="task-123",
        content="Test",
        id="custom-id-789"
    )
    assert comment.id == "custom-id-789"


def test_task_comment_with_explicit_created_at():
    """Test that TaskComment can be created with explicit created_at."""
    created_at = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    comment = TaskComment(
        task_id="task-123",
        content="Test",
        created_at=created_at
    )
    assert comment.created_at == created_at
