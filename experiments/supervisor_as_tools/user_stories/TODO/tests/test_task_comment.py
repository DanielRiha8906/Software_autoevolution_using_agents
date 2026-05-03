import pytest
from datetime import datetime
from src.models.task_comment import TaskComment


def test_task_comment_defaults():
    comment = TaskComment(task_id="task-123", content="This is a comment")
    assert comment.task_id == "task-123"
    assert comment.content == "This is a comment"
    assert comment.id is not None
    assert comment.author is None


def test_task_comment_unique_ids():
    c1 = TaskComment(task_id="task-1", content="Comment 1")
    c2 = TaskComment(task_id="task-1", content="Comment 2")
    assert c1.id != c2.id


def test_task_comment_with_author():
    comment = TaskComment(task_id="task-1", content="My comment", author="Alice")
    assert comment.author == "Alice"


def test_task_comment_created_at_set():
    comment = TaskComment(task_id="task-1", content="Content")
    assert comment.created_at is not None
    assert isinstance(comment.created_at, datetime)


def test_task_comment_updated_at_set():
    comment = TaskComment(task_id="task-1", content="Content")
    assert comment.updated_at is not None
    assert isinstance(comment.updated_at, datetime)


def test_task_comment_to_dict():
    comment = TaskComment(task_id="task-123", content="Test", author="Bob")
    data = comment.to_dict()
    assert data["id"] == comment.id
    assert data["task_id"] == "task-123"
    assert data["content"] == "Test"
    assert data["author"] == "Bob"
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)


def test_task_comment_to_dict_iso_timestamps():
    comment = TaskComment(task_id="task-1", content="Test")
    data = comment.to_dict()
    # ISO format should contain 'T' and '+' or 'Z' for UTC
    assert "T" in data["created_at"]
    assert "+" in data["created_at"] or "Z" in data["created_at"]
    assert "T" in data["updated_at"]
    assert "+" in data["updated_at"] or "Z" in data["updated_at"]


def test_task_comment_from_dict():
    original = TaskComment(task_id="task-1", content="Hello", author="Charlie")
    restored = TaskComment.from_dict(original.to_dict())
    assert restored.id == original.id
    assert restored.task_id == original.task_id
    assert restored.content == original.content
    assert restored.author == original.author
    assert restored.created_at == original.created_at
    assert restored.updated_at == original.updated_at


def test_task_comment_roundtrip():
    comment = TaskComment(task_id="task-xyz", content="Round trip test", author="David")
    restored = TaskComment.from_dict(comment.to_dict())
    assert restored.id == comment.id
    assert restored.task_id == comment.task_id
    assert restored.content == comment.content
    assert restored.author == comment.author
    assert restored.created_at == comment.created_at
    assert restored.updated_at == comment.updated_at


def test_task_comment_empty_content_raises():
    with pytest.raises(ValueError):
        TaskComment(task_id="task-1", content="")


def test_task_comment_whitespace_content_raises():
    with pytest.raises(ValueError):
        TaskComment(task_id="task-1", content="   ")


def test_task_comment_whitespace_with_newline_raises():
    with pytest.raises(ValueError):
        TaskComment(task_id="task-1", content="\n\t  ")


def test_task_comment_from_dict_without_author():
    data = {
        "id": "comment-1",
        "task_id": "task-1",
        "content": "Test",
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
    }
    comment = TaskComment.from_dict(data)
    assert comment.author is None
