import pytest
from src.services.comments_service import CommentsService, CommentNotFoundError
from src.services.task_manager import TaskManager, TaskNotFoundError
from src.storage.json_storage import JsonStorage


@pytest.fixture
def task_manager(tmp_path):
    """Create a TaskManager instance for testing."""
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    return TaskManager(storage)


@pytest.fixture
def service(tmp_path, task_manager):
    """Create a CommentsService instance for testing."""
    storage = JsonStorage(str(tmp_path / "comments.json"))
    return CommentsService(storage=storage, task_manager=task_manager)


class TestAddComment:
    """Tests for add_comment() method."""

    def test_add_comment_to_existing_task(self, task_manager, service):
        """Test adding a comment to an existing task."""
        task = task_manager.add("Buy milk")
        comment = service.add_comment(task.id, "Need to buy 2L carton")
        assert comment.task_id == task.id
        assert comment.content == "Need to buy 2L carton"
        assert comment.id is not None

    def test_add_comment_to_nonexistent_task_raises(self, service):
        """Test that adding a comment to a nonexistent task raises TaskNotFoundError."""
        with pytest.raises(TaskNotFoundError):
            service.add_comment("nonexistent-task-id", "This should fail")

    def test_add_comment_with_empty_content_raises(self, task_manager, service):
        """Test that empty content raises ValueError."""
        task = task_manager.add("Task")
        with pytest.raises(ValueError):
            service.add_comment(task.id, "")

    def test_add_comment_with_whitespace_only_content_raises(self, task_manager, service):
        """Test that whitespace-only content raises ValueError."""
        task = task_manager.add("Task")
        with pytest.raises(ValueError):
            service.add_comment(task.id, "   \t\n  ")

    def test_add_comment_strips_whitespace_from_content(self, task_manager, service):
        """Test that content is stripped of leading/trailing whitespace."""
        task = task_manager.add("Task")
        comment = service.add_comment(task.id, "  padded content  ")
        assert comment.content == "padded content"

    def test_add_multiple_comments_to_same_task(self, task_manager, service):
        """Test adding multiple comments to the same task."""
        task = task_manager.add("Task")
        c1 = service.add_comment(task.id, "First comment")
        c2 = service.add_comment(task.id, "Second comment")
        assert c1.id != c2.id
        assert len(service.list_comments(task.id)) == 2


class TestListComments:
    """Tests for list_comments() method."""

    def test_list_comments_for_task_with_comments(self, task_manager, service):
        """Test listing comments for a task with existing comments."""
        task = task_manager.add("Task")
        service.add_comment(task.id, "First")
        service.add_comment(task.id, "Second")
        comments = service.list_comments(task.id)
        assert len(comments) == 2

    def test_list_comments_for_task_with_no_comments(self, task_manager, service):
        """Test listing comments for a task with no comments returns empty list."""
        task = task_manager.add("Task")
        comments = service.list_comments(task.id)
        assert comments == []

    def test_list_comments_for_nonexistent_task_returns_empty(self, service):
        """Test listing comments for nonexistent task returns empty list (no validation)."""
        comments = service.list_comments("nonexistent-task-id")
        assert comments == []

    def test_list_comments_sorted_by_created_at(self, task_manager, service):
        """Test that comments are sorted by created_at ascending."""
        task = task_manager.add("Task")
        c1 = service.add_comment(task.id, "First")
        c2 = service.add_comment(task.id, "Second")
        c3 = service.add_comment(task.id, "Third")

        comments = service.list_comments(task.id)
        assert comments[0].id == c1.id
        assert comments[1].id == c2.id
        assert comments[2].id == c3.id

    def test_list_comments_only_returns_comments_for_task(self, task_manager, service):
        """Test that list_comments only returns comments for the specified task."""
        task1 = task_manager.add("Task 1")
        task2 = task_manager.add("Task 2")
        service.add_comment(task1.id, "Comment for task 1")
        service.add_comment(task2.id, "Comment for task 2")
        service.add_comment(task2.id, "Another comment for task 2")

        task1_comments = service.list_comments(task1.id)
        task2_comments = service.list_comments(task2.id)

        assert len(task1_comments) == 1
        assert len(task2_comments) == 2
        assert task1_comments[0].task_id == task1.id
        assert all(c.task_id == task2.id for c in task2_comments)


class TestDeleteComment:
    """Tests for delete_comment() method."""

    def test_delete_existing_comment(self, task_manager, service):
        """Test deleting an existing comment."""
        task = task_manager.add("Task")
        comment = service.add_comment(task.id, "To delete")
        service.delete_comment(comment.id)
        comments = service.list_comments(task.id)
        assert len(comments) == 0

    def test_delete_nonexistent_comment_raises(self, service):
        """Test that deleting a nonexistent comment raises CommentNotFoundError."""
        with pytest.raises(CommentNotFoundError):
            service.delete_comment("nonexistent-comment-id")

    def test_delete_comment_leaves_other_comments(self, task_manager, service):
        """Test that deleting a comment doesn't affect other comments."""
        task = task_manager.add("Task")
        c1 = service.add_comment(task.id, "Keep this")
        c2 = service.add_comment(task.id, "Delete this")

        service.delete_comment(c2.id)
        comments = service.list_comments(task.id)

        assert len(comments) == 1
        assert comments[0].id == c1.id


class TestDeleteTaskComments:
    """Tests for delete_task_comments() method."""

    def test_delete_all_comments_for_task(self, task_manager, service):
        """Test deleting all comments for a task."""
        task = task_manager.add("Task")
        service.add_comment(task.id, "Comment 1")
        service.add_comment(task.id, "Comment 2")

        service.delete_task_comments(task.id)
        comments = service.list_comments(task.id)

        assert len(comments) == 0

    def test_delete_task_comments_is_idempotent(self, task_manager, service):
        """Test that delete_task_comments is idempotent (no error on empty task)."""
        task = task_manager.add("Task")
        # First call deletes no comments
        service.delete_task_comments(task.id)
        # Second call should not raise
        service.delete_task_comments(task.id)
        assert len(service.list_comments(task.id)) == 0

    def test_delete_task_comments_for_nonexistent_task(self, service):
        """Test that delete_task_comments for nonexistent task doesn't raise."""
        # Should not raise
        service.delete_task_comments("nonexistent-task-id")

    def test_delete_task_comments_only_deletes_for_specified_task(self, task_manager, service):
        """Test that delete_task_comments only deletes comments for the specified task."""
        task1 = task_manager.add("Task 1")
        task2 = task_manager.add("Task 2")
        service.add_comment(task1.id, "Comment 1")
        service.add_comment(task2.id, "Comment 2")

        service.delete_task_comments(task1.id)

        assert len(service.list_comments(task1.id)) == 0
        assert len(service.list_comments(task2.id)) == 1


class TestPersistence:
    """Tests for persistence of comments to storage."""

    def test_comments_persist_across_instances(self, tmp_path, task_manager):
        """Test that comments persist when loading a new CommentsService instance."""
        comments_path = str(tmp_path / "comments.json")

        # Create service and add comment
        service1 = CommentsService(
            storage=JsonStorage(comments_path),
            task_manager=task_manager
        )
        task = task_manager.add("Task")
        comment = service1.add_comment(task.id, "Persisted comment")

        # Create new service instance and verify comment still exists
        service2 = CommentsService(
            storage=JsonStorage(comments_path),
            task_manager=task_manager
        )
        comments = service2.list_comments(task.id)

        assert len(comments) == 1
        assert comments[0].id == comment.id
        assert comments[0].content == "Persisted comment"

    def test_comment_data_persists_correctly(self, tmp_path, task_manager):
        """Test that all comment fields persist correctly."""
        comments_path = str(tmp_path / "comments.json")

        service1 = CommentsService(
            storage=JsonStorage(comments_path),
            task_manager=task_manager
        )
        task = task_manager.add("Task")
        comment = service1.add_comment(task.id, "Test content")

        service2 = CommentsService(
            storage=JsonStorage(comments_path),
            task_manager=task_manager
        )
        fetched = service2.list_comments(task.id)[0]

        assert fetched.id == comment.id
        assert fetched.task_id == comment.task_id
        assert fetched.content == comment.content
        assert fetched.created_at == comment.created_at


class TestCascadeDelete:
    """Tests for cascade delete integration with TodoService."""

    def test_cascade_delete_via_todo_service(self, tmp_path):
        """Test that TodoService.delete_task() cascades to delete comments."""
        from src.services.todo_service import TodoService

        tasks_path = str(tmp_path / "tasks.json")
        service = TodoService(JsonStorage(tasks_path))

        task = service.add_task("Task")
        service._comments_service.add_comment(task.id, "Comment 1")
        service._comments_service.add_comment(task.id, "Comment 2")

        # Delete task (should cascade to comments)
        service.delete_task(task.id)

        # Comments should be gone
        assert len(service._comments_service.list_comments(task.id)) == 0
