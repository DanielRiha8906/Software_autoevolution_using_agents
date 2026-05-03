import pytest
from datetime import datetime, timezone, timedelta
from src.models.task import Task
from src.models.task_comment import TaskComment
from src.models.task_status import TaskStatus
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


# ─── TaskComment Model Tests ────────────────────────────────────────────────

class TestTaskCommentCreation:
    """Test TaskComment creation and initialization."""

    def test_create_comment_with_minimal_fields(self):
        """Test creating a comment with only required fields."""
        comment = TaskComment(content="Hello", task_id="task-123")
        assert comment.content == "Hello"
        assert comment.task_id == "task-123"
        assert comment.id is not None
        assert comment.author is None
        assert comment.created_at is not None
        assert comment.updated_at is None

    def test_comment_has_unique_ids(self):
        """Test that multiple comments have unique IDs."""
        c1 = TaskComment(content="First", task_id="task-1")
        c2 = TaskComment(content="Second", task_id="task-1")
        assert c1.id != c2.id

    def test_create_comment_with_author(self):
        """Test creating a comment with an author."""
        comment = TaskComment(
            content="Great work!",
            task_id="task-456",
            author="Alice"
        )
        assert comment.author == "Alice"
        assert comment.content == "Great work!"

    def test_create_comment_with_explicit_datetime(self):
        """Test creating a comment with an explicit timezone-aware datetime."""
        dt = datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc)
        comment = TaskComment(
            content="Test",
            task_id="task-1",
            created_at=dt
        )
        assert comment.created_at == dt

    def test_comment_created_at_is_timezone_aware(self):
        """Test that created_at defaults to UTC timezone-aware datetime."""
        comment = TaskComment(content="Test", task_id="task-1")
        assert comment.created_at.tzinfo is not None
        assert comment.created_at.tzinfo == timezone.utc

    def test_comment_defaults_created_at_to_now(self):
        """Test that created_at defaults to approximately now."""
        before = datetime.now(timezone.utc)
        comment = TaskComment(content="Test", task_id="task-1")
        after = datetime.now(timezone.utc)
        assert before <= comment.created_at <= after


class TestTaskCommentValidation:
    """Test TaskComment validation in __post_init__."""

    def test_reject_empty_content(self):
        """Test that empty content is rejected."""
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            TaskComment(content="", task_id="task-1")

    def test_reject_whitespace_only_content(self):
        """Test that whitespace-only content is rejected."""
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            TaskComment(content="   ", task_id="task-1")

    def test_reject_tabs_and_newlines_only(self):
        """Test that tabs and newlines only are rejected."""
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            TaskComment(content="\t\n  \t", task_id="task-1")

    @pytest.mark.parametrize("content", [
        "a",
        "Single character",
        "  padded  ",
        "With\nnewlines\ninside",
        "Content with special chars: !@#$%^&*()",
    ])
    def test_accept_valid_content(self, content):
        """Test that valid content is accepted."""
        comment = TaskComment(content=content, task_id="task-1")
        assert comment.content == content


class TestTaskCommentDatetimeValidation:
    """Test TaskComment datetime handling."""

    def test_created_at_accepts_naive_datetime(self):
        """Test that TaskComment accepts naive datetime for created_at (no validation)."""
        dt_naive = datetime(2026, 5, 3, 12, 0)  # No tzinfo
        comment = TaskComment(
            content="Test",
            task_id="task-1",
            created_at=dt_naive
        )
        assert comment.created_at == dt_naive

    def test_created_at_naive_datetime_is_accepted(self):
        """Test that naive datetime IS accepted for created_at (no validation)."""
        dt_naive = datetime(2026, 5, 3, 12, 0)
        comment = TaskComment(
            content="Test",
            task_id="task-1",
            created_at=dt_naive
        )
        assert comment.created_at == dt_naive

    def test_updated_at_can_be_none(self):
        """Test that updated_at can be None."""
        comment = TaskComment(content="Test", task_id="task-1", updated_at=None)
        assert comment.updated_at is None

    def test_updated_at_can_be_timezone_aware_datetime(self):
        """Test that updated_at can be a timezone-aware datetime."""
        dt = datetime(2026, 5, 3, 14, 0, tzinfo=timezone.utc)
        comment = TaskComment(
            content="Test",
            task_id="task-1",
            updated_at=dt
        )
        assert comment.updated_at == dt


class TestTaskCommentSerialization:
    """Test TaskComment to_dict() and from_dict() methods."""

    def test_to_dict_minimal(self):
        """Test to_dict() with minimal comment."""
        comment = TaskComment(content="Hello", task_id="task-123")
        d = comment.to_dict()
        assert d["id"] == comment.id
        assert d["task_id"] == "task-123"
        assert d["content"] == "Hello"
        assert d["author"] is None
        assert isinstance(d["created_at"], str)
        assert d["updated_at"] is None

    def test_to_dict_with_author(self):
        """Test to_dict() with author."""
        comment = TaskComment(
            content="Comment",
            task_id="task-123",
            author="Bob"
        )
        d = comment.to_dict()
        assert d["author"] == "Bob"

    def test_to_dict_with_updated_at(self):
        """Test to_dict() with updated_at."""
        dt = datetime(2026, 5, 3, 14, 0, tzinfo=timezone.utc)
        comment = TaskComment(
            content="Updated",
            task_id="task-123",
            updated_at=dt
        )
        d = comment.to_dict()
        assert d["updated_at"] == dt.isoformat()

    def test_to_dict_datetime_is_isoformat(self):
        """Test that datetime fields in to_dict() are ISO format strings."""
        comment = TaskComment(content="Test", task_id="task-1")
        d = comment.to_dict()
        # Should be able to parse back as ISO format
        datetime.fromisoformat(d["created_at"])

    def test_from_dict_minimal(self):
        """Test from_dict() with minimal data."""
        data = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Hello",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        comment = TaskComment.from_dict(data)
        assert comment.id == "comment-1"
        assert comment.task_id == "task-1"
        assert comment.content == "Hello"
        assert comment.author is None
        assert comment.updated_at is None

    def test_from_dict_with_author(self):
        """Test from_dict() with author."""
        data = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Hello",
            "author": "Charlie",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        comment = TaskComment.from_dict(data)
        assert comment.author == "Charlie"

    def test_from_dict_with_updated_at(self):
        """Test from_dict() with updated_at."""
        dt = datetime(2026, 5, 3, 14, 0, tzinfo=timezone.utc)
        data = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Updated",
            "author": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": dt.isoformat(),
        }
        comment = TaskComment.from_dict(data)
        assert comment.updated_at == dt

    def test_from_dict_null_updated_at(self):
        """Test from_dict() with null updated_at."""
        data = {
            "id": "comment-1",
            "task_id": "task-1",
            "content": "Test",
            "author": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None,
        }
        comment = TaskComment.from_dict(data)
        assert comment.updated_at is None

    def test_roundtrip_minimal(self):
        """Test roundtrip: create -> to_dict -> from_dict."""
        original = TaskComment(content="Test", task_id="task-1")
        restored = TaskComment.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.content == original.content
        assert restored.author == original.author
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at

    def test_roundtrip_with_all_fields(self):
        """Test roundtrip with all fields populated."""
        dt_created = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)
        dt_updated = datetime(2026, 5, 3, 14, 0, tzinfo=timezone.utc)
        original = TaskComment(
            id="comment-xyz",
            task_id="task-abc",
            content="Full comment",
            author="Diana",
            created_at=dt_created,
            updated_at=dt_updated,
        )
        restored = TaskComment.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.task_id == original.task_id
        assert restored.content == original.content
        assert restored.author == original.author
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at


# ─── Task Integration Tests ─────────────────────────────────────────────────

class TestTaskCommentsField:
    """Test Task.comments field and integration with comments."""

    def test_task_comments_defaults_to_empty_list(self):
        """Test that Task.comments defaults to an empty list."""
        task = Task(title="No comments")
        assert task.comments == []
        assert isinstance(task.comments, list)

    def test_task_comments_can_be_populated(self):
        """Test that comments can be added to a task."""
        task = Task(title="With comments")
        comment = TaskComment(content="First comment", task_id=task.id)
        task.comments.append(comment)
        assert len(task.comments) == 1
        assert task.comments[0] == comment

    def test_task_to_dict_includes_comments(self):
        """Test that Task.to_dict() includes comments."""
        task = Task(title="Task")
        comment = TaskComment(content="Comment", task_id=task.id)
        task.comments.append(comment)
        d = task.to_dict()
        assert "comments" in d
        assert len(d["comments"]) == 1
        assert d["comments"][0]["content"] == "Comment"

    def test_task_to_dict_empty_comments(self):
        """Test that Task.to_dict() includes empty comments list."""
        task = Task(title="No comments")
        d = task.to_dict()
        assert "comments" in d
        assert d["comments"] == []

    def test_task_from_dict_deserializes_comments(self):
        """Test that Task.from_dict() deserializes comments."""
        dt = datetime.now(timezone.utc)
        data = {
            "id": "task-1",
            "title": "Task",
            "description": None,
            "status": "pending",
            "created_at": dt.isoformat(),
            "updated_at": dt.isoformat(),
            "due_date": None,
            "comments": [
                {
                    "id": "comment-1",
                    "task_id": "task-1",
                    "content": "First",
                    "author": None,
                    "created_at": dt.isoformat(),
                    "updated_at": None,
                }
            ],
        }
        task = Task.from_dict(data)
        assert len(task.comments) == 1
        assert task.comments[0].content == "First"

    def test_task_from_dict_backward_compat_missing_comments_key(self):
        """Test backward compatibility when comments key is missing."""
        dt = datetime.now(timezone.utc)
        data = {
            "id": "task-1",
            "title": "Legacy task",
            "description": None,
            "status": "pending",
            "created_at": dt.isoformat(),
            "updated_at": dt.isoformat(),
            "due_date": None,
            # Note: no "comments" key
        }
        task = Task.from_dict(data)
        assert task.comments == []

    def test_task_from_dict_with_empty_comments_list(self):
        """Test Task.from_dict() with empty comments list."""
        dt = datetime.now(timezone.utc)
        data = {
            "id": "task-1",
            "title": "Task",
            "description": None,
            "status": "pending",
            "created_at": dt.isoformat(),
            "updated_at": dt.isoformat(),
            "due_date": None,
            "comments": [],
        }
        task = Task.from_dict(data)
        assert task.comments == []

    def test_task_roundtrip_preserves_comments(self):
        """Test that Task roundtrip preserves comments."""
        task = Task(title="Task")
        comment1 = TaskComment(content="Comment 1", task_id=task.id)
        comment2 = TaskComment(content="Comment 2", task_id=task.id)
        task.comments.extend([comment1, comment2])

        restored = Task.from_dict(task.to_dict())
        assert len(restored.comments) == 2
        assert restored.comments[0].content == "Comment 1"
        assert restored.comments[1].content == "Comment 2"


# ─── TaskManager Comment Tests ──────────────────────────────────────────────

@pytest.fixture
def manager(tmp_path):
    """Fixture for TaskManager with temporary storage."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


class TestTaskManagerAddComment:
    """Test TaskManager.add_comment() method."""

    def test_add_comment_creates_comment(self, manager):
        """Test that add_comment() creates a comment."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Great work!")
        assert comment.content == "Great work!"
        assert comment.task_id == task.id

    def test_add_comment_persists(self, manager):
        """Test that added comment is persisted."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Comment")
        retrieved_task = manager.get(task.id)
        assert len(retrieved_task.comments) == 1
        assert retrieved_task.comments[0].content == "Comment"

    def test_add_comment_with_author(self, manager):
        """Test add_comment() with author parameter."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Comment", author="Eve")
        assert comment.author == "Eve"

    def test_add_comment_without_author(self, manager):
        """Test add_comment() without author defaults to None."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Comment")
        assert comment.author is None

    def test_add_comment_to_nonexistent_task_raises(self, manager):
        """Test that add_comment() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            manager.add_comment("nonexistent-id", "Comment")

    def test_add_comment_validates_empty_content(self, manager):
        """Test that add_comment() validates empty content."""
        task = manager.add("Task")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            manager.add_comment(task.id, "")

    def test_add_comment_validates_whitespace_only(self, manager):
        """Test that add_comment() rejects whitespace-only content."""
        task = manager.add("Task")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            manager.add_comment(task.id, "   ")

    def test_add_multiple_comments(self, manager):
        """Test adding multiple comments to same task."""
        task = manager.add("Task")
        comment1 = manager.add_comment(task.id, "First")
        comment2 = manager.add_comment(task.id, "Second")
        retrieved = manager.get(task.id)
        assert len(retrieved.comments) == 2
        assert retrieved.comments[0].id == comment1.id
        assert retrieved.comments[1].id == comment2.id

    def test_add_comment_returns_task_comment(self, manager):
        """Test that add_comment() returns a TaskComment instance."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Test")
        assert isinstance(comment, TaskComment)


class TestTaskManagerGetComments:
    """Test TaskManager.get_comments() method."""

    def test_get_comments_empty_task(self, manager):
        """Test get_comments() on task with no comments."""
        task = manager.add("Task")
        comments = manager.get_comments(task.id)
        assert comments == []

    def test_get_comments_returns_all(self, manager):
        """Test get_comments() returns all comments."""
        task = manager.add("Task")
        manager.add_comment(task.id, "First")
        manager.add_comment(task.id, "Second")
        manager.add_comment(task.id, "Third")
        comments = manager.get_comments(task.id)
        assert len(comments) == 3

    def test_get_comments_preserves_order(self, manager):
        """Test that get_comments() preserves comment order."""
        task = manager.add("Task")
        c1 = manager.add_comment(task.id, "First")
        c2 = manager.add_comment(task.id, "Second")
        comments = manager.get_comments(task.id)
        assert comments[0].id == c1.id
        assert comments[1].id == c2.id

    def test_get_comments_nonexistent_task_raises(self, manager):
        """Test that get_comments() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            manager.get_comments("nonexistent-id")

    def test_get_comments_returns_list(self, manager):
        """Test that get_comments() returns a list."""
        task = manager.add("Task")
        comments = manager.get_comments(task.id)
        assert isinstance(comments, list)


class TestTaskManagerDeleteComment:
    """Test TaskManager.delete_comment() method."""

    def test_delete_comment_removes_comment(self, manager):
        """Test that delete_comment() removes the comment."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "To delete")
        manager.delete_comment(task.id, comment.id)
        comments = manager.get_comments(task.id)
        assert len(comments) == 0

    def test_delete_comment_persists_deletion(self, manager):
        """Test that comment deletion is persisted."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Comment")
        manager.delete_comment(task.id, comment.id)
        retrieved = manager.get(task.id)
        assert len(retrieved.comments) == 0

    def test_delete_comment_nonexistent_comment_raises(self, manager):
        """Test delete_comment() raises ValueError for missing comment."""
        task = manager.add("Task")
        with pytest.raises(ValueError, match="Comment .* not found"):
            manager.delete_comment(task.id, "nonexistent-id")

    def test_delete_comment_nonexistent_task_raises(self, manager):
        """Test delete_comment() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            manager.delete_comment("nonexistent-id", "comment-id")

    def test_delete_one_comment_keeps_others(self, manager):
        """Test that deleting one comment keeps others."""
        task = manager.add("Task")
        c1 = manager.add_comment(task.id, "Keep this")
        c2 = manager.add_comment(task.id, "Delete this")
        c3 = manager.add_comment(task.id, "Keep this too")
        manager.delete_comment(task.id, c2.id)
        comments = manager.get_comments(task.id)
        assert len(comments) == 2
        assert comments[0].id == c1.id
        assert comments[1].id == c3.id


# ─── TodoService Comment Tests ──────────────────────────────────────────────

@pytest.fixture
def service(tmp_path):
    """Fixture for TodoService with temporary storage."""
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


class TestTodoServiceAddComment:
    """Test TodoService.add_comment() method."""

    def test_add_comment_creates_comment(self, service):
        """Test that add_comment() creates a comment."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Nice work!")
        assert comment.content == "Nice work!"
        assert comment.task_id == task.id

    def test_add_comment_with_author(self, service):
        """Test add_comment() with author parameter."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Comment", author="Frank")
        assert comment.author == "Frank"

    def test_add_comment_without_author(self, service):
        """Test add_comment() without author defaults to None."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Comment")
        assert comment.author is None

    def test_add_comment_validates_empty_content(self, service):
        """Test that add_comment() validates empty content."""
        task = service.add_task("Task")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            service.add_comment(task.id, "")

    def test_add_comment_validates_whitespace_only(self, service):
        """Test that add_comment() rejects whitespace-only content."""
        task = service.add_task("Task")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            service.add_comment(task.id, "   ")

    def test_add_comment_strips_whitespace(self, service):
        """Test that add_comment() strips whitespace from content."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "  padded content  ")
        assert comment.content == "padded content"

    def test_add_comment_nonexistent_task_raises(self, service):
        """Test that add_comment() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            service.add_comment("nonexistent-id", "Comment")

    @pytest.mark.parametrize("content", [
        "Single line",
        "  Whitespace trimmed  ",
        "Multi\nline\ncomment",
    ])
    def test_add_comment_with_various_content(self, service, content):
        """Test add_comment() with various content formats."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, content)
        assert comment is not None


class TestTodoServiceGetComments:
    """Test TodoService.get_comments() method."""

    def test_get_comments_empty_task(self, service):
        """Test get_comments() on task with no comments."""
        task = service.add_task("Task")
        comments = service.get_comments(task.id)
        assert comments == []

    def test_get_comments_returns_all(self, service):
        """Test get_comments() returns all comments."""
        task = service.add_task("Task")
        service.add_comment(task.id, "First")
        service.add_comment(task.id, "Second")
        comments = service.get_comments(task.id)
        assert len(comments) == 2

    def test_get_comments_nonexistent_task_raises(self, service):
        """Test that get_comments() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            service.get_comments("nonexistent-id")

    def test_get_comments_returns_list(self, service):
        """Test that get_comments() returns a list."""
        task = service.add_task("Task")
        comments = service.get_comments(task.id)
        assert isinstance(comments, list)


class TestTodoServiceDeleteComment:
    """Test TodoService.delete_comment() method."""

    def test_delete_comment_removes_comment(self, service):
        """Test that delete_comment() removes the comment."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "To delete")
        service.delete_comment(task.id, comment.id)
        comments = service.get_comments(task.id)
        assert len(comments) == 0

    def test_delete_comment_nonexistent_comment_raises(self, service):
        """Test delete_comment() raises ValueError for missing comment."""
        task = service.add_task("Task")
        with pytest.raises(ValueError, match="Comment .* not found"):
            service.delete_comment(task.id, "nonexistent-id")

    def test_delete_comment_nonexistent_task_raises(self, service):
        """Test delete_comment() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            service.delete_comment("nonexistent-id", "comment-id")

    def test_delete_one_keeps_others(self, service):
        """Test that deleting one comment keeps others."""
        task = service.add_task("Task")
        c1 = service.add_comment(task.id, "Keep")
        c2 = service.add_comment(task.id, "Delete")
        service.delete_comment(task.id, c2.id)
        comments = service.get_comments(task.id)
        assert len(comments) == 1
        assert comments[0].id == c1.id


class TestTaskManagerEditComment:
    """Test TaskManager.edit_comment() method."""

    def test_edit_comment_updates_content(self, manager):
        """Test that edit_comment() updates the comment content."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Old content")
        updated = manager.edit_comment(task.id, comment.id, "New content")
        assert updated.content == "New content"

    def test_edit_comment_sets_updated_at(self, manager):
        """Test that edit_comment() sets updated_at timestamp."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Original")
        before = datetime.now(timezone.utc)
        updated = manager.edit_comment(task.id, comment.id, "Modified")
        after = datetime.now(timezone.utc)
        assert updated.updated_at is not None
        assert before <= updated.updated_at <= after

    def test_edit_comment_persists(self, manager):
        """Test that edited comment is persisted."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Original")
        manager.edit_comment(task.id, comment.id, "Updated")
        retrieved = manager.get(task.id)
        assert retrieved.comments[0].content == "Updated"

    def test_edit_comment_nonexistent_task_raises(self, manager):
        """Test edit_comment() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            manager.edit_comment("nonexistent-id", "comment-id", "New content")

    def test_edit_comment_nonexistent_comment_raises(self, manager):
        """Test edit_comment() raises ValueError for missing comment."""
        task = manager.add("Task")
        with pytest.raises(ValueError, match="Comment .* not found"):
            manager.edit_comment(task.id, "nonexistent-id", "New content")

    def test_edit_comment_empty_content_raises(self, manager):
        """Test edit_comment() rejects empty content."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Original")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            manager.edit_comment(task.id, comment.id, "")

    def test_edit_comment_whitespace_only_raises(self, manager):
        """Test edit_comment() rejects whitespace-only content."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Original")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            manager.edit_comment(task.id, comment.id, "   ")

    def test_edit_comment_strips_whitespace(self, manager):
        """Test that edit_comment() strips whitespace from content."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Original")
        updated = manager.edit_comment(task.id, comment.id, "  Trimmed  ")
        assert updated.content == "Trimmed"

    def test_edit_comment_preserves_other_fields(self, manager):
        """Test that edit_comment() preserves id, task_id, author, created_at."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Original", author="Alice")
        original_id = comment.id
        original_author = comment.author
        original_created_at = comment.created_at

        updated = manager.edit_comment(task.id, comment.id, "Modified")
        assert updated.id == original_id
        assert updated.author == original_author
        assert updated.created_at == original_created_at

    def test_edit_comment_multiple_times(self, manager):
        """Test editing a comment multiple times."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Version 1")
        manager.edit_comment(task.id, comment.id, "Version 2")
        manager.edit_comment(task.id, comment.id, "Version 3")
        retrieved = manager.get_comments(task.id)
        assert len(retrieved) == 1
        assert retrieved[0].content == "Version 3"


class TestTodoServiceEditComment:
    """Test TodoService.edit_comment() method."""

    def test_edit_comment_updates_content(self, service):
        """Test that edit_comment() updates the comment content."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Old")
        updated = service.edit_comment(task.id, comment.id, "New")
        assert updated.content == "New"

    def test_edit_comment_sets_updated_at(self, service):
        """Test that edit_comment() sets updated_at timestamp."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Original")
        before = datetime.now(timezone.utc)
        updated = service.edit_comment(task.id, comment.id, "Modified")
        after = datetime.now(timezone.utc)
        assert updated.updated_at is not None
        assert before <= updated.updated_at <= after

    def test_edit_comment_empty_content_raises(self, service):
        """Test edit_comment() rejects empty content."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Original")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            service.edit_comment(task.id, comment.id, "")

    def test_edit_comment_whitespace_only_raises(self, service):
        """Test edit_comment() rejects whitespace-only content."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Original")
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            service.edit_comment(task.id, comment.id, "   ")

    def test_edit_comment_strips_whitespace(self, service):
        """Test that edit_comment() strips whitespace from content."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Original")
        updated = service.edit_comment(task.id, comment.id, "  Trimmed  ")
        assert updated.content == "Trimmed"

    def test_edit_comment_nonexistent_task_raises(self, service):
        """Test edit_comment() raises TaskNotFoundError for missing task."""
        with pytest.raises(TaskNotFoundError):
            service.edit_comment("nonexistent-id", "comment-id", "New")

    def test_edit_comment_nonexistent_comment_raises(self, service):
        """Test edit_comment() raises ValueError for missing comment."""
        task = service.add_task("Task")
        with pytest.raises(ValueError, match="Comment .* not found"):
            service.edit_comment(task.id, "nonexistent-id", "New")


class TestTaskManagerGetCommentsSorted:
    """Test TaskManager.get_comments() sorting by created_at."""

    def test_get_comments_sorted_empty_list(self, manager):
        """Test get_comments() returns empty list for task with no comments."""
        task = manager.add("Task")
        comments = manager.get_comments(task.id)
        assert comments == []

    def test_get_comments_sorted_single_comment(self, manager):
        """Test get_comments() with single comment."""
        task = manager.add("Task")
        comment = manager.add_comment(task.id, "Only comment")
        comments = manager.get_comments(task.id)
        assert len(comments) == 1
        assert comments[0].id == comment.id

    def test_get_comments_sorted_by_created_at_ascending(self, manager):
        """Test that get_comments() returns comments sorted by created_at ascending (oldest first)."""
        task = manager.add("Task")

        # Create comments with explicit timestamps
        dt1 = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)
        dt2 = datetime(2026, 5, 2, 10, 0, tzinfo=timezone.utc)
        dt3 = datetime(2026, 5, 3, 10, 0, tzinfo=timezone.utc)

        c3 = TaskComment(content="Third", task_id=task.id, created_at=dt3)
        c1 = TaskComment(content="First", task_id=task.id, created_at=dt1)
        c2 = TaskComment(content="Second", task_id=task.id, created_at=dt2)

        # Add in non-sequential order
        task.comments.extend([c3, c1, c2])
        manager._persist()

        # Get comments should return sorted (oldest first)
        comments = manager.get_comments(task.id)
        assert len(comments) == 3
        assert comments[0].content == "First"
        assert comments[1].content == "Second"
        assert comments[2].content == "Third"

    def test_get_comments_preserves_insertion_order_when_same_timestamp(self, manager):
        """Test get_comments() with comments created at same timestamp."""
        task = manager.add("Task")
        dt = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)

        c1 = TaskComment(content="First", task_id=task.id, created_at=dt)
        c2 = TaskComment(content="Second", task_id=task.id, created_at=dt)

        task.comments.extend([c1, c2])
        manager._persist()

        comments = manager.get_comments(task.id)
        assert len(comments) == 2
        # When timestamps are equal, sort is stable, preserving order
        assert comments[0].id == c1.id
        assert comments[1].id == c2.id


# ─── Integration Tests ──────────────────────────────────────────────────────

class TestCommentIntegration:
    """Integration tests for comments across components."""

    def test_comments_persist_across_manager_reload(self, tmp_path):
        """Test that comments persist when manager is reloaded."""
        path = str(tmp_path / "tasks.json")

        # Create manager, add task with comment
        m1 = TaskManager(JsonStorage(path))
        task = m1.add("Task")
        m1.add_comment(task.id, "Persisted comment")
        task_id = task.id

        # Reload manager and verify comment exists
        m2 = TaskManager(JsonStorage(path))
        reloaded = m2.get(task_id)
        assert len(reloaded.comments) == 1
        assert reloaded.comments[0].content == "Persisted comment"

    def test_todo_service_comments_persist_across_reload(self, tmp_path):
        """Test that TodoService comments persist across reload."""
        path = str(tmp_path / "tasks.json")

        # Create service, add task with comment
        s1 = TodoService(JsonStorage(path))
        task = s1.add_task("Task")
        s1.add_comment(task.id, "Comment")
        task_id = task.id

        # Reload service and verify comment exists
        s2 = TodoService(JsonStorage(path))
        comments = s2.get_comments(task_id)
        assert len(comments) == 1
        assert comments[0].content == "Comment"

    def test_comments_survive_task_update(self, manager):
        """Test that comments persist when task is updated."""
        task = manager.add("Original title")
        comment = manager.add_comment(task.id, "Comment")
        manager.update(task.id, title="Updated title")
        updated = manager.get(task.id)
        assert len(updated.comments) == 1
        assert updated.comments[0].id == comment.id

    def test_comments_deleted_with_task(self, manager):
        """Test that comments are deleted when task is deleted."""
        task = manager.add("Task")
        manager.add_comment(task.id, "Comment")
        manager.delete(task.id)
        with pytest.raises(TaskNotFoundError):
            manager.get(task.id)

    def test_multiple_tasks_with_separate_comments(self, manager):
        """Test that comments are properly separated per task."""
        t1 = manager.add("Task 1")
        t2 = manager.add("Task 2")
        manager.add_comment(t1.id, "Comment on task 1")
        manager.add_comment(t2.id, "Comment on task 2")
        c1 = manager.get_comments(t1.id)
        c2 = manager.get_comments(t2.id)
        assert len(c1) == 1
        assert len(c2) == 1
        assert c1[0].content == "Comment on task 1"
        assert c2[0].content == "Comment on task 2"

    def test_comment_lifecycle_complete(self, service):
        """Test complete comment lifecycle: create, read, update (indirectly), delete."""
        # Create task
        task = service.add_task("Task")

        # Add comments
        c1 = service.add_comment(task.id, "First comment", author="User1")
        c2 = service.add_comment(task.id, "Second comment", author="User2")

        # Read comments
        comments = service.get_comments(task.id)
        assert len(comments) == 2

        # Delete one comment
        service.delete_comment(task.id, c1.id)

        # Verify deletion
        remaining = service.get_comments(task.id)
        assert len(remaining) == 1
        assert remaining[0].id == c2.id

    def test_comment_edit_lifecycle(self, service):
        """Test comment edit lifecycle: create, edit, verify."""
        task = service.add_task("Task")
        comment = service.add_comment(task.id, "Original", author="User1")

        # Edit the comment
        updated = service.edit_comment(task.id, comment.id, "Modified")
        assert updated.content == "Modified"
        assert updated.author == "User1"
        assert updated.updated_at is not None

        # Verify persistence
        comments = service.get_comments(task.id)
        assert len(comments) == 1
        assert comments[0].content == "Modified"
