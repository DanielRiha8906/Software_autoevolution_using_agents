import uuid
import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_comment import TaskComment


CEST = timezone(timedelta(hours=2))


def test_task_comment_can_be_created():
    assert TaskComment(task_id="abc", content="Hello") is not None


def test_task_comment_has_unique_uuid_id():
    a = TaskComment(task_id="abc", content="Hello")
    b = TaskComment(task_id="abc", content="Hello")
    assert a.id != b.id


def test_task_comment_id_is_uuid_string():
    comment = TaskComment(task_id="abc", content="Hello")
    parsed = uuid.UUID(comment.id)
    assert str(parsed) == comment.id


def test_task_comment_has_created_at():
    assert isinstance(TaskComment(task_id="abc", content="Hello").created_at, datetime)


def test_task_comment_created_at_uses_cest():
    comment = TaskComment(task_id="abc", content="Hello")
    assert comment.created_at.tzinfo == CEST


def test_empty_content_raises():
    with pytest.raises(Exception):
        TaskComment(task_id="abc", content="")


def test_serializes_to_dict():
    comment = TaskComment(task_id="abc", content="Hello")
    d = comment.to_dict()
    assert d["task_id"] == "abc"
    assert d["content"] == "Hello"
    assert "id" in d
    assert "created_at" in d


def test_created_at_serializes_as_string():
    comment = TaskComment(task_id="abc", content="Hello")
    d = comment.to_dict()
    assert isinstance(d["created_at"], str)


def test_round_trips_via_dict():
    comment = TaskComment(task_id="abc", content="Hello")
    restored = TaskComment.from_dict(comment.to_dict())
    assert restored.id == comment.id
    assert restored.content == comment.content
    assert restored.created_at == comment.created_at


def test_optional_author():
    assert TaskComment(task_id="abc", content="Hi", author="Alice").author == "Alice"


def test_has_updated_at_attribute():
    assert hasattr(TaskComment(task_id="abc", content="Hi"), "updated_at")


def test_updated_at_uses_cest_when_present():
    comment = TaskComment(task_id="abc", content="Hi")
    if comment.updated_at is not None:
        assert comment.updated_at.tzinfo == CEST
