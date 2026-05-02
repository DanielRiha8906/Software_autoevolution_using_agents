import pytest
from datetime import datetime, timezone, timedelta
from src.models.task_comment import TaskComment, CEST


def test_task_comment_creation():
    """Test that TaskComment can be created with required fields."""
    comment = TaskComment(task_id="task-123", content="This is a comment")
    assert comment.task_id == "task-123"
    assert comment.content == "This is a comment"
    assert comment.id is not None
    assert comment.author is None
    assert comment.created_at is not None
    assert comment.updated_at is not None


def test_task_comment_with_author():
    """Test that TaskComment can be created with an author."""
    comment = TaskComment(task_id="task-123", content="Comment", author="Alice")
    assert comment.author == "Alice"


def test_task_comment_unique_ids():
    """Test that each TaskComment gets a unique ID."""
    comment1 = TaskComment(task_id="task-123", content="Comment 1")
    comment2 = TaskComment(task_id="task-123", content="Comment 2")
    assert comment1.id != comment2.id


def test_task_comment_empty_content_raises_error():
    """Test that TaskComment raises ValueError if content is empty."""
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        TaskComment(task_id="task-123", content="")


def test_task_comment_whitespace_only_content_raises_error():
    """Test that TaskComment raises ValueError if content is only whitespace."""
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        TaskComment(task_id="task-123", content="   ")


def test_task_comment_whitespace_only_content_tab_raises_error():
    """Test that TaskComment raises ValueError if content is only tabs."""
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        TaskComment(task_id="task-123", content="\t\t\t")


def test_task_comment_whitespace_only_content_newline_raises_error():
    """Test that TaskComment raises ValueError if content is only newlines."""
    with pytest.raises(ValueError, match="Comment content cannot be empty"):
        TaskComment(task_id="task-123", content="\n\n\n")


def test_task_comment_to_dict():
    """Test that TaskComment serializes to dictionary correctly."""
    comment = TaskComment(
        task_id="task-123",
        content="Test comment",
        author="Alice"
    )
    d = comment.to_dict()
    assert d["id"] == comment.id
    assert d["task_id"] == "task-123"
    assert d["content"] == "Test comment"
    assert d["author"] == "Alice"
    assert d["created_at"] == comment.created_at.isoformat()
    assert d["updated_at"] == comment.updated_at.isoformat()


def test_task_comment_to_dict_no_author():
    """Test that TaskComment serializes with None author."""
    comment = TaskComment(task_id="task-123", content="Test comment")
    d = comment.to_dict()
    assert d["author"] is None


def test_task_comment_from_dict():
    """Test that TaskComment deserializes from dictionary correctly."""
    data = {
        "id": "comment-123",
        "task_id": "task-456",
        "content": "Test comment",
        "author": "Bob",
        "created_at": "2025-05-02T12:00:00+02:00",
        "updated_at": "2025-05-02T13:00:00+02:00",
    }
    comment = TaskComment.from_dict(data)
    assert comment.id == "comment-123"
    assert comment.task_id == "task-456"
    assert comment.content == "Test comment"
    assert comment.author == "Bob"
    assert comment.created_at == datetime.fromisoformat("2025-05-02T12:00:00+02:00")
    assert comment.updated_at == datetime.fromisoformat("2025-05-02T13:00:00+02:00")


def test_task_comment_from_dict_no_author():
    """Test that TaskComment deserializes with None author."""
    data = {
        "id": "comment-123",
        "task_id": "task-456",
        "content": "Test comment",
        "created_at": "2025-05-02T12:00:00+02:00",
        "updated_at": "2025-05-02T13:00:00+02:00",
    }
    comment = TaskComment.from_dict(data)
    assert comment.author is None


def test_task_comment_roundtrip():
    """Test that TaskComment survives to_dict() and from_dict() roundtrip."""
    original = TaskComment(
        task_id="task-123",
        content="Test comment",
        author="Charlie"
    )
    restored = TaskComment.from_dict(original.to_dict())
    assert restored.id == original.id
    assert restored.task_id == original.task_id
    assert restored.content == original.content
    assert restored.author == original.author
    assert restored.created_at == original.created_at
    assert restored.updated_at == original.updated_at


def test_task_comment_task_id_references_parent():
    """Test that task_id correctly references the parent Task."""
    parent_task_id = "task-abc123"
    comment = TaskComment(task_id=parent_task_id, content="Comment about task")
    assert comment.task_id == parent_task_id


def test_task_comment_created_at_defaults_to_cest():
    """Test that created_at defaults to current CEST time."""
    before = datetime.now(CEST)
    comment = TaskComment(task_id="task-123", content="Comment")
    after = datetime.now(CEST)
    assert before <= comment.created_at <= after


def test_task_comment_updated_at_defaults_to_cest():
    """Test that updated_at defaults to current CEST time."""
    before = datetime.now(CEST)
    comment = TaskComment(task_id="task-123", content="Comment")
    after = datetime.now(CEST)
    assert before <= comment.updated_at <= after


def test_task_comment_with_explicit_timestamps():
    """Test that TaskComment can be created with explicit timestamps."""
    created = datetime(2025, 5, 2, 10, 0, 0, tzinfo=CEST)
    updated = datetime(2025, 5, 2, 11, 0, 0, tzinfo=CEST)
    comment = TaskComment(
        task_id="task-123",
        content="Comment",
        created_at=created,
        updated_at=updated
    )
    assert comment.created_at == created
    assert comment.updated_at == updated


def test_task_comment_content_with_special_characters():
    """Test that TaskComment handles content with special characters."""
    content = "This is a comment with special chars: @#$%^&*()"
    comment = TaskComment(task_id="task-123", content=content)
    assert comment.content == content


def test_task_comment_content_with_newlines():
    """Test that TaskComment handles multi-line content."""
    content = "Line 1\nLine 2\nLine 3"
    comment = TaskComment(task_id="task-123", content=content)
    assert comment.content == content


def test_task_comment_long_content():
    """Test that TaskComment handles long content."""
    content = "A" * 10000
    comment = TaskComment(task_id="task-123", content=content)
    assert comment.content == content
    assert len(comment.content) == 10000
