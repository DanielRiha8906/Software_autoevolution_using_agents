import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_comment import TaskComment

CEST = timezone(timedelta(hours=2))


def test_task_comment_requires_task_id():
    """task_id is required."""
    comment = TaskComment(task_id="123", content="Hello")
    assert comment.task_id == "123"


def test_task_comment_requires_content():
    """content is required."""
    comment = TaskComment(task_id="123", content="Hello")
    assert comment.content == "Hello"


def test_task_comment_empty_content_raises():
    """Empty content raises ValueError."""
    with pytest.raises(ValueError, match="content must be non-empty"):
        TaskComment(task_id="123", content="")


def test_task_comment_whitespace_only_content_raises():
    """Whitespace-only content raises ValueError."""
    with pytest.raises(ValueError, match="content must be non-empty"):
        TaskComment(task_id="123", content="   ")


def test_task_comment_auto_generates_id():
    """id is auto-generated as UUID string."""
    comment = TaskComment(task_id="123", content="Hello")
    assert comment.id is not None
    assert isinstance(comment.id, str)
    assert len(comment.id) == 36  # UUID4 string format


def test_task_comment_unique_ids():
    """Each comment gets a unique id."""
    c1 = TaskComment(task_id="123", content="A")
    c2 = TaskComment(task_id="123", content="B")
    assert c1.id != c2.id


def test_task_comment_created_at_auto_set():
    """created_at is auto-set to current time in CEST."""
    before = datetime.now(CEST)
    comment = TaskComment(task_id="123", content="Hello")
    after = datetime.now(CEST)
    assert before <= comment.created_at <= after


def test_task_comment_created_at_is_cest():
    """created_at must use CEST timezone."""
    comment = TaskComment(task_id="123", content="Hello")
    assert comment.created_at.tzinfo == CEST


def test_task_comment_created_at_serialize_iso8601():
    """created_at serializes to ISO 8601 string."""
    comment = TaskComment(task_id="123", content="Hello")
    iso_str = comment.created_at.isoformat()
    assert isinstance(iso_str, str)
    assert "T" in iso_str  # ISO 8601 format


def test_task_comment_author_optional():
    """author is optional."""
    c1 = TaskComment(task_id="123", content="Hello")
    assert c1.author is None
    c2 = TaskComment(task_id="123", content="Hello", author="Alice")
    assert c2.author == "Alice"


def test_task_comment_updated_at_optional():
    """updated_at is optional."""
    comment = TaskComment(task_id="123", content="Hello")
    assert comment.updated_at is None


def test_task_comment_updated_at_can_be_set():
    """updated_at can be set to a CEST datetime."""
    updated = datetime(2026, 5, 3, 10, 30, tzinfo=CEST)
    comment = TaskComment(task_id="123", content="Hello", updated_at=updated)
    assert comment.updated_at == updated


def test_task_comment_updated_at_must_be_cest():
    """updated_at must use CEST timezone."""
    utc_time = datetime(2026, 5, 3, 10, 30, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="CEST"):
        TaskComment(task_id="123", content="Hello", updated_at=utc_time)


def test_task_comment_to_dict():
    """to_dict serializes TaskComment."""
    comment = TaskComment(task_id="123", content="Hello", author="Alice")
    d = comment.to_dict()
    assert d["id"] == comment.id
    assert d["task_id"] == "123"
    assert d["content"] == "Hello"
    assert d["created_at"] == comment.created_at.isoformat()
    assert d["author"] == "Alice"
    assert "updated_at" not in d


def test_task_comment_to_dict_with_updated_at():
    """to_dict includes updated_at if set."""
    updated = datetime(2026, 5, 3, 10, 30, tzinfo=CEST)
    comment = TaskComment(task_id="123", content="Hello", updated_at=updated)
    d = comment.to_dict()
    assert d["updated_at"] == updated.isoformat()


def test_task_comment_to_dict_without_author():
    """to_dict excludes author if None."""
    comment = TaskComment(task_id="123", content="Hello")
    d = comment.to_dict()
    assert "author" not in d


def test_task_comment_from_dict():
    """from_dict deserializes TaskComment."""
    d = {
        "id": "abc-123",
        "task_id": "456",
        "content": "Hello",
        "created_at": datetime(2026, 5, 3, 10, 0, tzinfo=CEST).isoformat(),
    }
    comment = TaskComment.from_dict(d)
    assert comment.id == "abc-123"
    assert comment.task_id == "456"
    assert comment.content == "Hello"
    assert comment.author is None
    assert comment.updated_at is None


def test_task_comment_from_dict_with_all_fields():
    """from_dict handles all fields."""
    d = {
        "id": "abc-123",
        "task_id": "456",
        "content": "Hello",
        "author": "Alice",
        "created_at": datetime(2026, 5, 3, 10, 0, tzinfo=CEST).isoformat(),
        "updated_at": datetime(2026, 5, 3, 11, 0, tzinfo=CEST).isoformat(),
    }
    comment = TaskComment.from_dict(d)
    assert comment.id == "abc-123"
    assert comment.task_id == "456"
    assert comment.content == "Hello"
    assert comment.author == "Alice"
    assert comment.updated_at == datetime(2026, 5, 3, 11, 0, tzinfo=CEST)


def test_task_comment_roundtrip():
    """TaskComment serializes and deserializes correctly."""
    original = TaskComment(
        task_id="456",
        content="Test comment",
        author="Bob",
        updated_at=datetime(2026, 5, 3, 12, 30, tzinfo=CEST)
    )
    d = original.to_dict()
    restored = TaskComment.from_dict(d)
    assert restored.id == original.id
    assert restored.task_id == original.task_id
    assert restored.content == original.content
    assert restored.author == original.author
    assert restored.created_at == original.created_at
    assert restored.updated_at == original.updated_at
