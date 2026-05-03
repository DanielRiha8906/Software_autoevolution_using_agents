import pytest
from unittest.mock import patch, MagicMock
from src.cli.interactive_menu import InteractiveMenu


@pytest.fixture
def menu(tmp_path):
    """Create an InteractiveMenu with temporary storage."""
    return InteractiveMenu(str(tmp_path / "tasks.json"))


class TestCheckStatusMenu:
    """Test check status menu option 7."""

    def test_check_status_method_exists(self, menu):
        """Test that _do_check_status method exists."""
        assert hasattr(menu, '_do_check_status')
        assert callable(getattr(menu, '_do_check_status'))

    @patch('builtins.input')
    def test_check_status_displays_task_statuses(self, mock_input, menu, capsys):
        """Test that check_status displays status predicates."""
        # Setup
        task = menu._service.add_task("Test task")
        menu._service.mark_in_progress(task.id)

        tasks = [task]
        # First call to _pick returns choice 1 (select first task), second to continue
        mock_input.side_effect = ["1", "test"]

        # Execute
        menu._do_check_status(tasks)

        # Verify output contains status information
        captured = capsys.readouterr()
        assert "Pending" in captured.out
        assert "In progress" in captured.out
        assert "Completed" in captured.out
        assert "Overdue" in captured.out

    @patch('builtins.input')
    def test_check_status_no_tasks(self, mock_input, menu):
        """Test that check_status handles empty task list."""
        # Setup
        mock_input.return_value = "test"  # Simulate user pressing Enter

        # Execute
        menu._do_check_status([])

        # Should not raise an error
        mock_input.assert_called()
