import pytest
from datetime import datetime, timezone, timedelta
from src.models.task import Task
from src.models.task_comment import TaskComment
from src.models.task_status import TaskStatus


def test_task_defaults():
    task = Task(title="Buy milk")
    assert task.title == "Buy milk"
    assert task.status == TaskStatus.PENDING
    assert task.description is None
    assert task.id is not None


def test_task_unique_ids():
    a = Task(title="A")
    b = Task(title="B")
    assert a.id != b.id


def test_task_roundtrip():
    task = Task(title="Test", description="desc")
    restored = Task.from_dict(task.to_dict())
    assert restored.id == task.id
    assert restored.title == task.title
    assert restored.description == task.description
    assert restored.status == task.status
    assert restored.created_at == task.created_at
    assert restored.updated_at == task.updated_at


def test_task_status_serialisation():
    for status in TaskStatus:
        task = Task(title="x", status=status)
        restored = Task.from_dict(task.to_dict())
        assert restored.status == status


# mark_in_progress() tests
def test_mark_in_progress_from_pending():
    """Test transition PENDING -> IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > original_updated_at


def test_mark_in_progress_from_done():
    """Test transition DONE -> IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.DONE)
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > original_updated_at


def test_mark_in_progress_already_in_progress_is_noop():
    """Test that mark_in_progress is a no-op when already IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == original_updated_at


# mark_done() tests
def test_mark_done_from_in_progress():
    """Test transition IN_PROGRESS -> DONE."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    original_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at > original_updated_at


def test_mark_done_from_pending_is_noop():
    """Test that mark_done is a no-op when PENDING."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_status = task.status
    original_updated_at = task.updated_at
    task.mark_done()
    assert task.status == original_status
    assert task.updated_at == original_updated_at


def test_mark_done_already_done_is_noop():
    """Test that mark_done is a no-op when already DONE."""
    task = Task(title="Test", status=TaskStatus.DONE)
    original_updated_at = task.updated_at
    task.mark_done()
    assert task.status == TaskStatus.DONE
    assert task.updated_at == original_updated_at


# reopen() tests
def test_reopen_from_done():
    """Test transition DONE -> IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.DONE)
    original_updated_at = task.updated_at
    task.reopen()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > original_updated_at


def test_reopen_from_pending_is_noop():
    """Test that reopen is a no-op when PENDING."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_status = task.status
    original_updated_at = task.updated_at
    task.reopen()
    assert task.status == original_status
    assert task.updated_at == original_updated_at


def test_reopen_from_in_progress_is_noop():
    """Test that reopen is a no-op when IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    original_status = task.status
    original_updated_at = task.updated_at
    task.reopen()
    assert task.status == original_status
    assert task.updated_at == original_updated_at


# is_completed() tests
def test_is_completed_when_done():
    """Test is_completed returns True when status is DONE."""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() is True


def test_is_completed_when_pending():
    """Test is_completed returns False when status is PENDING."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_completed() is False


def test_is_completed_when_in_progress():
    """Test is_completed returns False when status is IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_completed() is False


# is_pending() tests
def test_is_pending_when_pending():
    """Test is_pending returns True when status is PENDING."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True


def test_is_pending_when_in_progress():
    """Test is_pending returns False when status is IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_pending() is False


def test_is_pending_when_done():
    """Test is_pending returns False when status is DONE."""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_pending() is False


# is_in_progress() tests
def test_is_in_progress_when_in_progress():
    """Test is_in_progress returns True when status is IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    assert task.is_in_progress() is True


def test_is_in_progress_when_pending():
    """Test is_in_progress returns False when status is PENDING."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_in_progress() is False


def test_is_in_progress_when_done():
    """Test is_in_progress returns False when status is DONE."""
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_in_progress() is False


# is_overdue() tests
def test_is_overdue_with_future_due_date():
    """Test is_overdue returns False when due_date is in the future."""
    future_date = datetime.now(timezone.utc) + timedelta(hours=1)
    task = Task(title="Test", status=TaskStatus.PENDING, due_date=future_date)
    assert task.is_overdue() is False


def test_is_overdue_with_past_due_date():
    """Test is_overdue returns True when due_date is in the past and not completed."""
    past_date = datetime.now(timezone.utc) - timedelta(hours=1)
    task = Task(title="Test", status=TaskStatus.PENDING, due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_with_past_due_date_in_progress():
    """Test is_overdue returns True for IN_PROGRESS task with past due_date."""
    past_date = datetime.now(timezone.utc) - timedelta(hours=1)
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS, due_date=past_date)
    assert task.is_overdue() is True


def test_is_overdue_when_no_due_date():
    """Test is_overdue returns False when due_date is None."""
    task = Task(title="Test", status=TaskStatus.PENDING, due_date=None)
    assert task.is_overdue() is False


def test_is_overdue_when_completed():
    """Test is_overdue returns False even with past due_date when task is DONE."""
    past_date = datetime.now(timezone.utc) - timedelta(hours=1)
    task = Task(title="Test", status=TaskStatus.DONE, due_date=past_date)
    assert task.is_overdue() is False


# Lifecycle tests
def test_full_lifecycle_pending_to_done():
    """Test full lifecycle: PENDING -> IN_PROGRESS -> DONE."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    assert task.is_pending() is True
    assert task.is_completed() is False

    task.mark_in_progress()
    assert task.is_in_progress() is True
    assert task.is_pending() is False

    task.mark_done()
    assert task.is_completed() is True
    assert task.is_in_progress() is False


def test_full_lifecycle_with_reopen():
    """Test lifecycle: PENDING -> IN_PROGRESS -> DONE -> IN_PROGRESS."""
    task = Task(title="Test", status=TaskStatus.PENDING)

    task.mark_in_progress()
    task.mark_done()
    assert task.is_completed() is True

    task.reopen()
    assert task.is_in_progress() is True
    assert task.is_completed() is False

    task.mark_done()
    assert task.is_completed() is True


def test_updated_at_changes_with_status_transitions():
    """Test that updated_at changes with each status transition."""
    task = Task(title="Test", status=TaskStatus.PENDING)
    updated_at_1 = task.updated_at

    task.mark_in_progress()
    updated_at_2 = task.updated_at
    assert updated_at_2 > updated_at_1

    task.mark_done()
    updated_at_3 = task.updated_at
    assert updated_at_3 > updated_at_2

    task.reopen()
    updated_at_4 = task.updated_at
    assert updated_at_4 > updated_at_3


# Comments field tests
def test_comments_default_to_empty_list():
    """Test that new tasks have empty comments list."""
    task = Task(title="Test")
    assert task.comments == []
    assert isinstance(task.comments, list)


def test_add_comment_creates_and_appends():
    """Test that add_comment creates a TaskComment and appends it."""
    task = Task(title="Test")
    comment = task.add_comment("Great task!", author="Alice")
    assert isinstance(comment, TaskComment)
    assert comment.task_id == task.id
    assert comment.content == "Great task!"
    assert comment.author == "Alice"
    assert len(task.comments) == 1
    assert task.comments[0] == comment


def test_add_comment_without_author():
    """Test adding a comment without author."""
    task = Task(title="Test")
    comment = task.add_comment("No author comment")
    assert comment.author is None
    assert len(task.comments) == 1


def test_add_multiple_comments():
    """Test adding multiple comments to a task."""
    task = Task(title="Test")
    comment1 = task.add_comment("First", author="Alice")
    comment2 = task.add_comment("Second", author="Bob")
    assert len(task.comments) == 2
    assert task.comments[0] == comment1
    assert task.comments[1] == comment2


def test_task_to_dict_includes_comments():
    """Test that to_dict includes comments array."""
    task = Task(title="Test")
    task.add_comment("Comment 1", author="Alice")
    task.add_comment("Comment 2", author="Bob")
    data = task.to_dict()
    assert "comments" in data
    assert len(data["comments"]) == 2
    assert data["comments"][0]["content"] == "Comment 1"
    assert data["comments"][1]["content"] == "Comment 2"


def test_task_from_dict_deserializes_comments():
    """Test that from_dict reconstructs comments."""
    now = datetime.now(timezone.utc)
    data = {
        "id": "task-1",
        "title": "Test",
        "description": None,
        "status": "pending",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "due_date": None,
        "comments": [
            {
                "id": "comment-1",
                "task_id": "task-1",
                "content": "Good work",
                "created_at": now.isoformat(),
                "author": "Alice",
                "updated_at": None,
            }
        ],
    }
    task = Task.from_dict(data)
    assert len(task.comments) == 1
    assert task.comments[0].content == "Good work"
    assert task.comments[0].author == "Alice"


def test_task_from_dict_backward_compatible_missing_comments():
    """Test that from_dict handles missing comments field (backward compatibility)."""
    now = datetime.now(timezone.utc)
    data = {
        "id": "task-1",
        "title": "Old task",
        "description": None,
        "status": "pending",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "due_date": None,
    }
    task = Task.from_dict(data)
    assert task.comments == []


def test_task_roundtrip_with_comments():
    """Test full roundtrip: Task -> to_dict -> from_dict preserves comments."""
    original = Task(title="Test")
    original.add_comment("Comment 1", author="Alice")
    original.add_comment("Comment 2", author="Bob")
    data = original.to_dict()
    restored = Task.from_dict(data)
    assert len(restored.comments) == 2
    assert restored.comments[0].content == "Comment 1"
    assert restored.comments[0].author == "Alice"
    assert restored.comments[1].content == "Comment 2"
    assert restored.comments[1].author == "Bob"


def test_comments_preserve_ids_in_roundtrip():
    """Test that comment IDs are preserved during roundtrip."""
    original = Task(title="Test")
    comment1 = original.add_comment("Comment 1")
    comment2 = original.add_comment("Comment 2")
    data = original.to_dict()
    restored = Task.from_dict(data)
    assert restored.comments[0].id == comment1.id
    assert restored.comments[1].id == comment2.id
