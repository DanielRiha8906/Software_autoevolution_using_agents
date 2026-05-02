import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_comment import TaskComment

CEST = timezone(timedelta(hours=2))


def test_task_comment_creation():
    """TaskComment(task_id="abc", content="Hello") creates an instance"""
    comment = TaskComment(task_id="abc", content="Hello")
    assert comment.task_id == "abc"
    assert comment.content == "Hello"


def test_task_comment_has_unique_id():
    """Each instance gets a unique UUID id"""
    comment1 = TaskComment(task_id="abc", content="Hello")
    comment2 = TaskComment(task_id="abc", content="Hello")
    assert comment1.id != comment2.id


def test_task_comment_id_is_string():
    """id is a UUID string"""
    comment = TaskComment(task_id="abc", content="Hello")
    assert isinstance(comment.id, str)
    # Verify it's a valid UUID string
    import uuid
    uuid.UUID(comment.id)


def test_task_comment_created_at_is_datetime():
    """created_at is a datetime object using CEST timezone"""
    comment = TaskComment(task_id="abc", content="Hello")
    assert isinstance(comment.created_at, datetime)
    assert comment.created_at.tzinfo == CEST


def test_task_comment_empty_content_raises():
    """Empty content raises an Exception"""
    with pytest.raises(Exception):
        TaskComment(task_id="abc", content="")

    with pytest.raises(Exception):
        TaskComment(task_id="abc", content="   ")


def test_task_comment_to_dict():
    """to_dict() serializes all fields, with created_at as ISO 8601 string"""
    comment = TaskComment(task_id="abc", content="Hello")
    d = comment.to_dict()
    assert d["task_id"] == "abc"
    assert d["content"] == "Hello"
    assert d["id"] == comment.id
    assert d["created_at"] == comment.created_at.isoformat()
    assert isinstance(d["created_at"], str)


def test_task_comment_from_dict():
    """from_dict() deserializes and restores the object (round-trip)"""
    comment = TaskComment(task_id="abc", content="Hello")
    d = comment.to_dict()
    restored = TaskComment.from_dict(d)
    assert restored.id == comment.id
    assert restored.task_id == comment.task_id
    assert restored.content == comment.content
    assert restored.created_at == comment.created_at


def test_task_comment_optional_author():
    """Optional author field"""
    comment_without_author = TaskComment(task_id="abc", content="Hello")
    assert comment_without_author.author is None

    comment_with_author = TaskComment(task_id="abc", content="Hello", author="John")
    assert comment_with_author.author == "John"


def test_task_comment_has_updated_at():
    """Has updated_at attribute (optional, but must use CEST if present)"""
    # Without updated_at
    comment = TaskComment(task_id="abc", content="Hello")
    assert hasattr(comment, "updated_at")
    assert comment.updated_at is None

    # With updated_at
    now = datetime.now(CEST)
    comment_with_update = TaskComment(task_id="abc", content="Hello", updated_at=now)
    assert comment_with_update.updated_at == now
    assert comment_with_update.updated_at.tzinfo == CEST


def test_task_comment_updated_at_in_dict():
    """updated_at is included in to_dict() when present"""
    updated = datetime.now(CEST)
    comment = TaskComment(task_id="abc", content="Hello", updated_at=updated)
    d = comment.to_dict()
    assert "updated_at" in d
    assert d["updated_at"] == updated.isoformat()


def test_task_comment_roundtrip_with_all_fields():
    """Round-trip serialization with all fields"""
    updated = datetime.now(CEST)
    comment = TaskComment(
        task_id="task-123",
        content="Test comment",
        author="Alice",
        updated_at=updated
    )
    d = comment.to_dict()
    restored = TaskComment.from_dict(d)
    assert restored.id == comment.id
    assert restored.task_id == comment.task_id
    assert restored.content == comment.content
    assert restored.author == comment.author
    assert restored.created_at == comment.created_at
    assert restored.updated_at == comment.updated_at
