import pytest
from datetime import datetime, timezone
from src.models.task import Task
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


# Status predicate tests
class TestStatusPredicates:
    """Test is_pending(), is_in_progress(), is_done() methods."""

    def test_is_pending_when_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_pending() is True

    def test_is_pending_when_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert task.is_pending() is False

    def test_is_pending_when_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.is_pending() is False

    def test_is_in_progress_when_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_in_progress() is False

    def test_is_in_progress_when_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert task.is_in_progress() is True

    def test_is_in_progress_when_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.is_in_progress() is False

    def test_is_done_when_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert task.is_done() is False

    def test_is_done_when_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert task.is_done() is False

    def test_is_done_when_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert task.is_done() is True


# Valid transition tests
class TestValidTransitions:
    """Test valid state transitions."""

    def test_mark_in_progress_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_updated_at = task.updated_at
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at > original_updated_at

    def test_mark_done_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated_at = task.updated_at
        task.mark_done()
        assert task.status == TaskStatus.DONE
        assert task.updated_at > original_updated_at

    def test_reopen_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated_at = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated_at

    def test_reopen_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated_at = task.updated_at
        task.reopen()
        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated_at

    def test_full_lifecycle_pending_to_done(self):
        task = Task(title="Full lifecycle", status=TaskStatus.PENDING)
        assert task.is_pending()
        task.mark_in_progress()
        assert task.is_in_progress()
        task.mark_done()
        assert task.is_done()

    def test_full_lifecycle_with_reopen(self):
        task = Task(title="With reopen", status=TaskStatus.PENDING)
        task.mark_in_progress()
        task.mark_done()
        task.reopen()
        assert task.is_pending()


# Invalid transition tests
class TestInvalidTransitions:
    """Test invalid state transitions."""

    def test_mark_in_progress_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        with pytest.raises(ValueError) as exc_info:
            task.mark_in_progress()
        assert str(exc_info.value) == "Cannot mark in_progress task as in progress. Task must be pending."

    def test_mark_in_progress_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        with pytest.raises(ValueError) as exc_info:
            task.mark_in_progress()
        assert str(exc_info.value) == "Cannot mark done task as in progress. Task must be pending."

    def test_mark_done_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        with pytest.raises(ValueError) as exc_info:
            task.mark_done()
        assert str(exc_info.value) == "Cannot mark pending task as done. Task must be in progress."

    def test_mark_done_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        with pytest.raises(ValueError) as exc_info:
            task.mark_done()
        assert str(exc_info.value) == "Cannot mark done task as done. Task must be in progress."

    def test_reopen_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        with pytest.raises(ValueError) as exc_info:
            task.reopen()
        assert str(exc_info.value) == "Cannot reopen a pending task. Task must be in progress or done."


# Non-idempotency tests
class TestNonIdempotency:
    """Test that transitions are not idempotent (calling twice raises error)."""

    def test_mark_in_progress_twice_raises_error(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        with pytest.raises(ValueError):
            task.mark_in_progress()

    def test_mark_done_twice_raises_error(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        task.mark_done()
        with pytest.raises(ValueError):
            task.mark_done()

    def test_reopen_twice_raises_error(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        task.reopen()
        with pytest.raises(ValueError):
            task.reopen()


# Timestamp update tests
class TestTimestampUpdates:
    """Test that updated_at is correctly updated during transitions."""

    def test_mark_in_progress_updates_timestamp(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_updated_at = task.updated_at
        task.mark_in_progress()
        assert task.updated_at > original_updated_at
        assert task.updated_at.tzinfo == timezone.utc

    def test_mark_done_updates_timestamp(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        original_updated_at = task.updated_at
        task.mark_done()
        assert task.updated_at > original_updated_at
        assert task.updated_at.tzinfo == timezone.utc

    def test_reopen_updates_timestamp(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        original_updated_at = task.updated_at
        task.reopen()
        assert task.updated_at > original_updated_at
        assert task.updated_at.tzinfo == timezone.utc

    def test_created_at_not_modified_during_transitions(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_created_at = task.created_at
        task.mark_in_progress()
        assert task.created_at == original_created_at

    def test_multiple_transitions_update_timestamp_each_time(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        timestamps = [task.updated_at]

        task.mark_in_progress()
        timestamps.append(task.updated_at)

        task.mark_done()
        timestamps.append(task.updated_at)

        # Each timestamp should be strictly greater than the previous
        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i - 1]


# Predicate idempotency tests
class TestPredicateIdempotency:
    """Test that predicate methods have no side effects."""

    def test_predicates_have_no_side_effects(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        original_status = task.status
        original_updated_at = task.updated_at

        # Call predicates multiple times
        for _ in range(5):
            task.is_pending()
            task.is_in_progress()
            task.is_done()

        assert task.status == original_status
        assert task.updated_at == original_updated_at

    def test_is_pending_returns_bool(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        assert isinstance(task.is_pending(), bool)

    def test_is_in_progress_returns_bool(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        assert isinstance(task.is_in_progress(), bool)

    def test_is_done_returns_bool(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        assert isinstance(task.is_done(), bool)


# Error message tests
class TestErrorMessages:
    """Test that error messages match the specification."""

    def test_mark_in_progress_error_message_from_in_progress(self):
        task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
        with pytest.raises(ValueError) as exc_info:
            task.mark_in_progress()
        assert "Cannot mark in_progress task as in progress" in str(exc_info.value)
        assert "Task must be pending" in str(exc_info.value)

    def test_mark_in_progress_error_message_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        with pytest.raises(ValueError) as exc_info:
            task.mark_in_progress()
        assert "Cannot mark done task as in progress" in str(exc_info.value)
        assert "Task must be pending" in str(exc_info.value)

    def test_mark_done_error_message_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        with pytest.raises(ValueError) as exc_info:
            task.mark_done()
        assert "Cannot mark pending task as done" in str(exc_info.value)
        assert "Task must be in progress" in str(exc_info.value)

    def test_mark_done_error_message_from_done(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        with pytest.raises(ValueError) as exc_info:
            task.mark_done()
        assert "Cannot mark done task as done" in str(exc_info.value)
        assert "Task must be in progress" in str(exc_info.value)

    def test_reopen_error_message_from_pending(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        with pytest.raises(ValueError) as exc_info:
            task.reopen()
        assert str(exc_info.value) == "Cannot reopen a pending task. Task must be in progress or done."


# Serialization tests for transition methods
class TestSerializationAfterTransitions:
    """Test that tasks with different statuses serialize/deserialize correctly."""

    def test_serialization_after_mark_in_progress(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        restored = Task.from_dict(task.to_dict())
        assert restored.status == TaskStatus.IN_PROGRESS
        assert restored.is_in_progress()

    def test_serialization_after_mark_done(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        task.mark_done()
        restored = Task.from_dict(task.to_dict())
        assert restored.status == TaskStatus.DONE
        assert restored.is_done()

    def test_serialization_after_reopen(self):
        task = Task(title="Test", status=TaskStatus.DONE)
        task.reopen()
        restored = Task.from_dict(task.to_dict())
        assert restored.status == TaskStatus.PENDING
        assert restored.is_pending()

    def test_timestamp_preserved_after_transition_roundtrip(self):
        task = Task(title="Test", status=TaskStatus.PENDING)
        task.mark_in_progress()
        updated_at_before = task.updated_at
        restored = Task.from_dict(task.to_dict())
        assert restored.updated_at == updated_at_before
