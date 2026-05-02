import pytest
from datetime import datetime, timedelta, timezone
from src.models.task_comment import TaskComment


def test_task_comment_instantiation_with_defaults():
    comment = TaskComment(task_id="task-123", content="This is a comment")
    assert comment.task_id == "task-123"
    assert comment.content == "This is a comment"
    assert comment.id is not None
    assert comment.created_at is not None
    assert comment.author is None
    assert comment.updated_at is None


def test_task_comment_uuid_uniqueness():
    comment1 = TaskComment(task_id="task-1", content="Comment 1")
    comment2 = TaskComment(task_id="task-2", content="Comment 2")
    assert comment1.id != comment2.id


def test_task_comment_content_validation_empty():
    with pytest.raises(ValueError, match="Content cannot be empty"):
        TaskComment(task_id="task-123", content="")


def test_task_comment_content_validation_whitespace_only():
    with pytest.raises(ValueError, match="Content cannot be empty"):
        TaskComment(task_id="task-123", content="   ")


def test_task_comment_task_id_validation_empty():
    with pytest.raises(ValueError, match="task_id cannot be empty"):
        TaskComment(task_id="", content="Some content")


def test_task_comment_to_dict_serialization():
    comment = TaskComment(task_id="task-123", content="Test comment", author="John")
    comment_dict = comment.to_dict()
    assert comment_dict["task_id"] == "task-123"
    assert comment_dict["content"] == "Test comment"
    assert comment_dict["id"] == comment.id
    assert comment_dict["author"] == "John"
    assert comment_dict["updated_at"] is None
    assert isinstance(comment_dict["created_at"], str)


def test_task_comment_to_dict_with_timezone_preservation():
    cest = timezone(timedelta(hours=2))
    created = datetime(2025, 5, 2, 14, 30, 45, tzinfo=cest)
    comment = TaskComment(task_id="task-123", content="Test", created_at=created)
    comment_dict = comment.to_dict()
    # ISO format should preserve the timezone offset
    assert "+02:00" in comment_dict["created_at"]


def test_task_comment_to_dict_with_updated_at():
    created = datetime(2025, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2025, 5, 2, 14, 30, 0, tzinfo=timezone.utc)
    comment = TaskComment(task_id="task-123", content="Test", created_at=created, updated_at=updated)
    comment_dict = comment.to_dict()
    assert comment_dict["updated_at"] is not None
    assert isinstance(comment_dict["updated_at"], str)


def test_task_comment_from_dict_deserialization():
    data = {
        "id": "comment-1",
        "task_id": "task-123",
        "content": "Deserialized comment",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": "Alice",
        "updated_at": None,
    }
    comment = TaskComment.from_dict(data)
    assert comment.id == "comment-1"
    assert comment.task_id == "task-123"
    assert comment.content == "Deserialized comment"
    assert comment.author == "Alice"
    assert comment.updated_at is None


def test_task_comment_from_dict_with_updated_at():
    created_iso = datetime(2025, 5, 2, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    updated_iso = datetime(2025, 5, 2, 14, 30, 0, tzinfo=timezone.utc).isoformat()
    data = {
        "id": "comment-1",
        "task_id": "task-123",
        "content": "Test",
        "created_at": created_iso,
        "author": None,
        "updated_at": updated_iso,
    }
    comment = TaskComment.from_dict(data)
    assert comment.updated_at is not None
    assert comment.updated_at == datetime.fromisoformat(updated_iso)


def test_task_comment_roundtrip_serialization():
    original = TaskComment(task_id="task-123", content="Round trip test", author="Bob")
    restored = TaskComment.from_dict(original.to_dict())
    assert restored.id == original.id
    assert restored.task_id == original.task_id
    assert restored.content == original.content
    assert restored.author == original.author
    assert restored.created_at == original.created_at
    assert restored.updated_at == original.updated_at


def test_task_comment_roundtrip_with_updated_at():
    updated = datetime.now(timezone.utc)
    original = TaskComment(
        task_id="task-123",
        content="With update",
        author="Charlie",
        updated_at=updated,
    )
    restored = TaskComment.from_dict(original.to_dict())
    assert restored.updated_at == original.updated_at


def test_task_comment_optional_author_field():
    comment_with_author = TaskComment(task_id="task-1", content="With author", author="Dave")
    comment_without_author = TaskComment(task_id="task-2", content="Without author")
    assert comment_with_author.author == "Dave"
    assert comment_without_author.author is None


def test_task_comment_optional_updated_at_field():
    comment = TaskComment(task_id="task-1", content="Test")
    assert comment.updated_at is None
    comment_dict = comment.to_dict()
    assert comment_dict["updated_at"] is None


def test_task_comment_cest_timezone_handling():
    cest = timezone(timedelta(hours=2))
    created = datetime(2025, 5, 2, 14, 30, 45, tzinfo=cest)
    updated = datetime(2025, 5, 2, 16, 45, 30, tzinfo=cest)
    comment = TaskComment(
        task_id="task-123",
        content="CEST test",
        created_at=created,
        updated_at=updated,
    )
    restored = TaskComment.from_dict(comment.to_dict())
    assert restored.created_at == created
    assert restored.updated_at == updated
    assert restored.created_at.tzinfo == cest
    assert restored.updated_at.tzinfo == cest
