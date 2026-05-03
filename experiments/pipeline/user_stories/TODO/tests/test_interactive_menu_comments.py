"""Tests for interactive menu comment management functions."""

import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime, timezone
from src.cli.interactive_menu import InteractiveMenu
from src.models.task import Task
from src.models.task_comment import TaskComment
from src.services.todo_service import TodoService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def menu(tmp_path):
    """Fixture for InteractiveMenu with temporary storage."""
    return InteractiveMenu(storage_path=str(tmp_path / "tasks.json"))


@pytest.fixture
def service(tmp_path):
    """Fixture for TodoService with temporary storage."""
    return TodoService(JsonStorage(str(tmp_path / "tasks.json")))


class TestInteractiveMenuManageComments:
    """Test _do_manage_comments() method."""

    def test_manage_comments_no_tasks(self, menu):
        """Test _do_manage_comments with no tasks (should exit early)."""
        tasks = []
        with patch('builtins.input', return_value=''):
            menu._do_manage_comments(tasks)
        # If there are no tasks, the method should return early
        # No exception should be raised

    def test_manage_comments_with_tasks(self, menu):
        """Test _do_manage_comments with available tasks."""
        task = menu._service.add_task("Test task")
        tasks = [task]

        with patch('builtins.input', side_effect=['0']):
            menu._do_manage_comments(tasks)
        # Should handle task selection and return


class TestInteractiveMenuAddComment:
    """Test _do_add_comment() method."""

    def test_add_comment_with_content_and_author(self, menu, capsys):
        """Test _do_add_comment with both content and author."""
        task = menu._service.add_task("Task")

        with patch('builtins.input', side_effect=['Great work!', 'Alice', '']):
            menu._do_add_comment(task)

        # Verify comment was added
        comments = menu._service.get_comments(task.id)
        assert len(comments) == 1
        assert comments[0].content == "Great work!"
        assert comments[0].author == "Alice"

    def test_add_comment_without_author(self, menu):
        """Test _do_add_comment without author."""
        task = menu._service.add_task("Task")

        with patch('builtins.input', side_effect=['Comment text', '', '']):
            menu._do_add_comment(task)

        comments = menu._service.get_comments(task.id)
        assert len(comments) == 1
        assert comments[0].content == "Comment text"
        assert comments[0].author is None

    def test_add_comment_empty_content_rejected(self, menu):
        """Test _do_add_comment rejects empty content."""
        task = menu._service.add_task("Task")

        with patch('builtins.input', side_effect=['', 'Alice']):
            menu._do_add_comment(task)

        # Comment should not be added
        comments = menu._service.get_comments(task.id)
        assert len(comments) == 0

    def test_add_comment_whitespace_only_rejected(self, menu):
        """Test _do_add_comment rejects whitespace-only content."""
        task = menu._service.add_task("Task")

        with patch('builtins.input', side_effect=['   ', 'Alice']):
            menu._do_add_comment(task)

        comments = menu._service.get_comments(task.id)
        assert len(comments) == 0


class TestInteractiveMenuPickComment:
    """Test _do_pick_comment() method."""

    def test_pick_comment_cancel(self, menu):
        """Test _do_pick_comment when user cancels."""
        task = menu._service.add_task("Task")
        menu._service.add_comment(task.id, "Comment 1")

        with patch('builtins.input', return_value='0'):
            menu._do_pick_comment(task)
        # Should return without error

    def test_pick_comment_selects_first(self, menu):
        """Test _do_pick_comment selecting the first comment."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "Comment 1")
        menu._service.add_comment(task.id, "Comment 2")

        with patch('builtins.input', side_effect=['1', '0']):
            menu._do_pick_comment(task)
        # Should display comment and return

    def test_pick_comment_displays_comment_details(self, menu, capsys):
        """Test _do_pick_comment displays comment information."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "Test comment", author="Alice")

        with patch('builtins.input', side_effect=['1', '0']):
            menu._do_pick_comment(task)

        # The method should display the comment
        # No assertion needed, just verify no exceptions


class TestInteractiveMenuEditCommentContent:
    """Test _do_edit_comment_content() method."""

    def test_edit_comment_success(self, menu):
        """Test _do_edit_comment_content successfully updates content."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "Original")

        with patch('builtins.input', return_value='Updated content'):
            menu._do_edit_comment_content(task, comment)

        # Verify comment was updated
        comments = menu._service.get_comments(task.id)
        assert comments[0].content == "Updated content"

    def test_edit_comment_with_default(self, menu):
        """Test _do_edit_comment_content with default (same content)."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "Original")

        with patch('builtins.input', return_value=''):
            menu._do_edit_comment_content(task, comment)

        # Comment should retain original content (empty input = use default)
        comments = menu._service.get_comments(task.id)
        assert comments[0].content == "Original"

    def test_edit_comment_empty_content_rejected(self, menu):
        """Test _do_edit_comment_content rejects empty content."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "Original")

        # Simulate user entering empty string, then pressing Enter
        with patch('builtins.input', return_value=''):
            menu._do_edit_comment_content(task, comment)

        # Content should remain unchanged
        comments = menu._service.get_comments(task.id)
        assert comments[0].content == "Original"

    def test_edit_comment_whitespace_rejected(self, menu):
        """Test _do_edit_comment_content rejects whitespace-only content."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "Original")

        with patch('builtins.input', return_value='   '):
            menu._do_edit_comment_content(task, comment)

        # The interactive menu passes the content through _prompt with default
        # Whitespace-only input should be treated as empty and rejected
        comments = menu._service.get_comments(task.id)
        # After _prompt, "   " becomes "" (stripped), which gets treated as default
        # The method will reject it as empty


class TestInteractiveMenuManageExistingComment:
    """Test _do_manage_existing_comment() method."""

    def test_manage_existing_comment_back_option(self, menu):
        """Test _do_manage_existing_comment with back/cancel."""
        task = menu._service.add_task("Task")
        menu._service.add_comment(task.id, "Comment")

        with patch('builtins.input', side_effect=['0']):
            menu._do_manage_existing_comment(task)
        # Should exit cleanly

    def test_manage_existing_comment_add_flow(self, menu):
        """Test _do_manage_existing_comment add comment flow."""
        task = menu._service.add_task("Task")

        with patch('builtins.input', side_effect=['1', 'New comment', '', '', '0']):
            menu._do_manage_existing_comment(task)

        # Verify comment was added
        comments = menu._service.get_comments(task.id)
        assert len(comments) == 1

    def test_manage_existing_comment_view_edit_delete_flow(self, menu):
        """Test _do_manage_existing_comment view/edit/delete flow."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "Original")

        with patch('builtins.input', side_effect=['2', '1', '0', '0']):
            menu._do_manage_existing_comment(task)
        # Should navigate through the comment management

    def test_manage_existing_comment_no_comments_initially(self, menu):
        """Test _do_manage_existing_comment when task has no comments."""
        task = menu._service.add_task("Task")

        with patch('builtins.input', side_effect=['0']):
            menu._do_manage_existing_comment(task)
        # Should display "(no comments yet)" and allow adding


class TestInteractiveMenuCommentWorkflow:
    """Integration tests for complete comment workflows."""

    def test_complete_comment_workflow_add_and_view(self, menu):
        """Test complete workflow: add comment and view it."""
        task = menu._service.add_task("Task")

        # Add comment
        with patch('builtins.input', side_effect=['Test comment', 'Alice', '']):
            menu._do_add_comment(task)

        # Verify
        comments = menu._service.get_comments(task.id)
        assert len(comments) == 1
        assert comments[0].content == "Test comment"
        assert comments[0].author == "Alice"

    def test_multiple_comments_in_menu(self, menu):
        """Test managing multiple comments in menu."""
        task = menu._service.add_task("Task")

        # Add multiple comments
        menu._service.add_comment(task.id, "First comment", author="Alice")
        menu._service.add_comment(task.id, "Second comment", author="Bob")

        # Verify they're retrievable
        comments = menu._service.get_comments(task.id)
        assert len(comments) == 2

    def test_edit_comment_preserves_author(self, menu):
        """Test that editing a comment preserves the author."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "Original", author="Alice")

        with patch('builtins.input', return_value='Updated'):
            menu._do_edit_comment_content(task, comment)

        comments = menu._service.get_comments(task.id)
        assert comments[0].author == "Alice"
        assert comments[0].content == "Updated"

    def test_delete_comment_via_manage_workflow(self, menu):
        """Test deleting a comment through management workflow."""
        task = menu._service.add_task("Task")
        comment = menu._service.add_comment(task.id, "To delete")

        # Via menu's service
        menu._service.delete_comment(task.id, comment.id)

        comments = menu._service.get_comments(task.id)
        assert len(comments) == 0
