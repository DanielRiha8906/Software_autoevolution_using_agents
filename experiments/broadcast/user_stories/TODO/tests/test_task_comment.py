import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.models.task_comment import TaskComment, CEST


def test_task_comment_defaults():
    """Test that a TaskComment is created with valid defaults."""
    task_id = "task-123"
    content = "This is a comment"
    comment = TaskComment(task_id=task_id, content=content)

    assert comment.task_id == task_id
    assert comment.content == content
    assert comment.id is not None
    assert comment.author is None
    assert comment.updated_at is None
    assert comment.created_at is not None


def test_task_comment_unique_ids():
    """Test that each TaskComment gets a unique id."""
    comment1 = TaskComment(task_id="task-1", content="First comment")
    comment2 = TaskComment(task_id="task-1", content="Second comment")
    assert comment1.id != comment2.id


def test_task_comment_with_author():
    """Test that TaskComment can include an author."""
    comment = TaskComment(
        task_id="task-123",
        content="A comment",
        author="Alice"
    )
    assert comment.author == "Alice"


def test_task_comment_with_updated_at():
    """Test that TaskComment can include an updated_at timestamp."""
    updated_time = datetime(2026, 5, 3, 12, 0, 0, tzinfo=CEST)
    comment = TaskComment(
        task_id="task-123",
        content="A comment",
        updated_at=updated_time
    )
    assert comment.updated_at == updated_time


def test_task_comment_rejects_empty_content():
    """Test that empty content is rejected."""
    with pytest.raises(ValueError, match="content cannot be empty"):
        TaskComment(task_id="task-123", content="")


def test_task_comment_rejects_whitespace_only_content():
    """Test that whitespace-only content is rejected."""
    with pytest.raises(ValueError, match="content cannot be empty"):
        TaskComment(task_id="task-123", content="   ")


def test_task_comment_rejects_empty_task_id():
    """Test that empty task_id is rejected."""
    with pytest.raises(ValueError, match="task_id must be a non-empty string"):
        TaskComment(task_id="", content="A comment")


def test_task_comment_rejects_whitespace_task_id():
    """Test that whitespace-only task_id is rejected."""
    with pytest.raises(ValueError, match="task_id must be a non-empty string"):
        TaskComment(task_id="   ", content="A comment")


def test_task_comment_roundtrip():
    """Test that TaskComment survives serialization/deserialization."""
    comment = TaskComment(
        task_id="task-123",
        content="A detailed comment about the task",
        author="Bob"
    )
    restored = TaskComment.from_dict(comment.to_dict())

    assert restored.id == comment.id
    assert restored.task_id == comment.task_id
    assert restored.content == comment.content
    assert restored.author == comment.author
    assert restored.created_at == comment.created_at
    assert restored.updated_at == comment.updated_at


def test_task_comment_to_dict():
    """Test that to_dict returns the expected structure."""
    comment = TaskComment(
        id="comment-123",
        task_id="task-456",
        content="Test comment",
        author="Test User"
    )
    result = comment.to_dict()

    assert result["id"] == "comment-123"
    assert result["task_id"] == "task-456"
    assert result["content"] == "Test comment"
    assert result["author"] == "Test User"
    assert "created_at" in result
    assert "updated_at" not in result


def test_task_comment_to_dict_includes_updated_at():
    """Test that to_dict includes updated_at when present."""
    updated_time = datetime(2026, 5, 3, 14, 30, 0, tzinfo=CEST)
    comment = TaskComment(
        task_id="task-123",
        content="Updated comment",
        updated_at=updated_time
    )
    result = comment.to_dict()

    assert "updated_at" in result
    assert result["updated_at"] == updated_time.isoformat()


def test_task_comment_to_dict_omits_none_author():
    """Test that to_dict omits author when it's None."""
    comment = TaskComment(
        task_id="task-123",
        content="A comment"
    )
    result = comment.to_dict()

    assert "author" not in result


def test_task_comment_from_dict():
    """Test that from_dict reconstructs a TaskComment correctly."""
    data = {
        "id": "comment-789",
        "task_id": "task-123",
        "content": "A reconstructed comment",
        "created_at": "2026-05-03T10:00:00+02:00",
        "author": "Charlie"
    }
    comment = TaskComment.from_dict(data)

    assert comment.id == "comment-789"
    assert comment.task_id == "task-123"
    assert comment.content == "A reconstructed comment"
    assert comment.author == "Charlie"
    assert comment.updated_at is None


def test_task_comment_from_dict_with_updated_at():
    """Test that from_dict includes updated_at when present."""
    data = {
        "id": "comment-789",
        "task_id": "task-123",
        "content": "A comment",
        "created_at": "2026-05-03T10:00:00+02:00",
        "updated_at": "2026-05-03T12:00:00+02:00"
    }
    comment = TaskComment.from_dict(data)

    assert comment.updated_at is not None
    assert comment.updated_at == datetime.fromisoformat("2026-05-03T12:00:00+02:00")


def test_task_comment_from_dict_without_optional_fields():
    """Test that from_dict handles missing optional fields gracefully."""
    data = {
        "id": "comment-101",
        "task_id": "task-202",
        "content": "Minimal comment",
        "created_at": "2026-05-03T09:00:00+02:00"
    }
    comment = TaskComment.from_dict(data)

    assert comment.author is None
    assert comment.updated_at is None


def test_task_comment_serialization_roundtrip_with_all_fields():
    """Test full roundtrip with all optional fields."""
    original = TaskComment(
        id="comment-999",
        task_id="task-888",
        content="A comprehensive comment",
        author="Diana",
        updated_at=datetime(2026, 5, 3, 15, 30, 0, tzinfo=CEST)
    )

    data = original.to_dict()
    restored = TaskComment.from_dict(data)

    assert restored.id == original.id
    assert restored.task_id == original.task_id
    assert restored.content == original.content
    assert restored.author == original.author
    assert restored.created_at == original.created_at
    assert restored.updated_at == original.updated_at


def test_task_comment_created_at_is_cest():
    """Test that created_at defaults to CEST timezone."""
    comment = TaskComment(task_id="task-123", content="Test")
    # Verify the timezone is set to CEST
    assert comment.created_at.tzinfo is not None
    assert comment.created_at.tzname() == "CEST" or comment.created_at.tzname() == "CET"
