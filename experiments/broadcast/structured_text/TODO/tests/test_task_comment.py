import pytest
from datetime import datetime, timezone
from src.models.task_comment import TaskComment


def test_task_comment_defaults():
    """Test TaskComment with minimal required fields."""
    comment = TaskComment(task_id="task-123", content="This is a comment")
    assert comment.task_id == "task-123"
    assert comment.content == "This is a comment"
    assert comment.id is not None
    assert comment.created_at is not None
    assert comment.author is None
    assert comment.updated_at is None


def test_task_comment_unique_ids():
    """Test that each TaskComment gets a unique ID."""
    comment1 = TaskComment(task_id="task-123", content="Comment 1")
    comment2 = TaskComment(task_id="task-123", content="Comment 2")
    assert comment1.id != comment2.id


def test_task_comment_with_author():
    """Test TaskComment with optional author field."""
    comment = TaskComment(
        task_id="task-123",
        content="A comment",
        author="John Doe"
    )
    assert comment.author == "John Doe"


def test_task_comment_with_updated_at():
    """Test TaskComment with optional updated_at field."""
    now = datetime.now(timezone.utc)
    comment = TaskComment(
        task_id="task-123",
        content="A comment",
        updated_at=now
    )
    assert comment.updated_at == now


def test_task_comment_empty_content_validation():
    """Test that empty content raises ValueError."""
    with pytest.raises(ValueError, match="content cannot be empty"):
        TaskComment(task_id="task-123", content="")


def test_task_comment_whitespace_content_validation():
    """Test that whitespace-only content raises ValueError."""
    with pytest.raises(ValueError, match="content cannot be empty"):
        TaskComment(task_id="task-123", content="   ")


def test_task_comment_empty_task_id_validation():
    """Test that empty task_id raises ValueError."""
    with pytest.raises(ValueError, match="task_id cannot be empty"):
        TaskComment(task_id="", content="A comment")


def test_task_comment_whitespace_task_id_validation():
    """Test that whitespace-only task_id raises ValueError."""
    with pytest.raises(ValueError, match="task_id cannot be empty"):
        TaskComment(task_id="   ", content="A comment")


def test_task_comment_to_dict_minimal():
    """Test serialization with minimal fields."""
    comment = TaskComment(task_id="task-123", content="Test comment")
    data = comment.to_dict()

    assert data["id"] == comment.id
    assert data["task_id"] == "task-123"
    assert data["content"] == "Test comment"
    assert data["created_at"] == comment.created_at.isoformat()
    assert "author" not in data
    assert "updated_at" not in data


def test_task_comment_to_dict_with_author():
    """Test serialization with author field."""
    comment = TaskComment(
        task_id="task-123",
        content="Test comment",
        author="Alice"
    )
    data = comment.to_dict()

    assert data["author"] == "Alice"


def test_task_comment_to_dict_with_updated_at():
    """Test serialization with updated_at field."""
    now = datetime.now(timezone.utc)
    comment = TaskComment(
        task_id="task-123",
        content="Test comment",
        updated_at=now
    )
    data = comment.to_dict()

    assert data["updated_at"] == now.isoformat()


def test_task_comment_roundtrip_minimal():
    """Test serialization and deserialization (minimal fields)."""
    original = TaskComment(task_id="task-123", content="Test comment")
    restored = TaskComment.from_dict(original.to_dict())

    assert restored.id == original.id
    assert restored.task_id == original.task_id
    assert restored.content == original.content
    assert restored.created_at == original.created_at
    assert restored.author == original.author
    assert restored.updated_at == original.updated_at


def test_task_comment_roundtrip_full():
    """Test serialization and deserialization (all fields)."""
    now = datetime.now(timezone.utc)
    original = TaskComment(
        task_id="task-456",
        content="Detailed comment",
        author="Bob",
        updated_at=now
    )
    restored = TaskComment.from_dict(original.to_dict())

    assert restored.id == original.id
    assert restored.task_id == original.task_id
    assert restored.content == original.content
    assert restored.created_at == original.created_at
    assert restored.author == original.author
    assert restored.updated_at == original.updated_at


def test_task_comment_from_dict_with_id():
    """Test that from_dict preserves the provided ID."""
    data = {
        "id": "comment-789",
        "task_id": "task-123",
        "content": "Restored comment",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    comment = TaskComment.from_dict(data)

    assert comment.id == "comment-789"


def test_task_comment_from_dict_minimal():
    """Test deserialization with minimal fields."""
    created_at = datetime.now(timezone.utc)
    data = {
        "id": "comment-123",
        "task_id": "task-456",
        "content": "A comment",
        "created_at": created_at.isoformat(),
    }
    comment = TaskComment.from_dict(data)

    assert comment.id == "comment-123"
    assert comment.task_id == "task-456"
    assert comment.content == "A comment"
    assert comment.created_at == created_at
    assert comment.author is None
    assert comment.updated_at is None


def test_task_comment_from_dict_full():
    """Test deserialization with all fields."""
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)
    data = {
        "id": "comment-123",
        "task_id": "task-456",
        "content": "A comment",
        "created_at": created_at.isoformat(),
        "author": "Charlie",
        "updated_at": updated_at.isoformat(),
    }
    comment = TaskComment.from_dict(data)

    assert comment.id == "comment-123"
    assert comment.task_id == "task-456"
    assert comment.content == "A comment"
    assert comment.created_at == created_at
    assert comment.author == "Charlie"
    assert comment.updated_at == updated_at
