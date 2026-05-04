"""Tests for GUI dialog classes - testing business logic without UI rendering."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from src.gui.dialogs.add_task import AddTaskDialog
from src.gui.dialogs.edit_task import EditTaskDialog
from src.gui.dialogs.delete_confirm import DeleteConfirmDialog


class TestAddTaskDialogLogic:
    """Tests for AddTaskDialog business logic."""

    def test_get_task_data_minimal(self):
        """Test getting minimal task data (title only)."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Buy milk"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        data = dialog.get_task_data()
        assert data["title"] == "Buy milk"
        assert data["description"] is None
        assert data["due_date"] is None
        assert data["project_id"] is None

    def test_get_task_data_with_description(self):
        """Test getting task data with description."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Task"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = "This is a description"
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        data = dialog.get_task_data()
        assert data["title"] == "Task"
        assert data["description"] == "This is a description"

    def test_get_task_data_with_valid_due_date(self):
        """Test getting task data with valid due date."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Task"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = "2025-12-25"
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        data = dialog.get_task_data()
        assert data["title"] == "Task"
        assert data["due_date"] is not None
        assert data["due_date"].year == 2025
        assert data["due_date"].month == 12
        assert data["due_date"].day == 25
        assert data["due_date"].tzinfo == timezone.utc

    def test_get_task_data_invalid_due_date_format_raises(self):
        """Test that invalid date format raises ValueError."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Task"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = "25/12/2025"  # Wrong format
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        with pytest.raises(ValueError) as exc_info:
            dialog.get_task_data()
        assert "Invalid date format" in str(exc_info.value)

    def test_get_task_data_whitespace_trimmed(self):
        """Test that whitespace is trimmed from title and description."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "  Task Title  "
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = "  Description  "
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        data = dialog.get_task_data()
        assert data["title"] == "Task Title"
        assert data["description"] == "Description"

    def test_get_task_data_empty_description_becomes_none(self):
        """Test that empty description becomes None."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Task"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = "   "  # Whitespace only
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        data = dialog.get_task_data()
        assert data["description"] is None

    def test_get_task_data_with_project_id(self):
        """Test getting task data with project ID."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Task"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = "proj1"

        data = dialog.get_task_data()
        assert data["project_id"] == "proj1"

    def test_set_projects(self):
        """Test setting available projects."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.project_combo = MagicMock()

        projects = [("proj1", "Project One"), ("proj2", "Project Two")]
        dialog.set_projects(projects)

        # Check that combobox values were set
        expected_values = ["Project One", "Project Two"]
        dialog.project_combo.__setitem__.assert_called_with("values", expected_values)

    def test_on_ok_valid_data(self):
        """Test _on_ok with valid data sets result."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Valid Title"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""
        dialog.destroy = MagicMock()

        dialog._on_ok()
        assert dialog.result is not None
        assert dialog.result["title"] == "Valid Title"
        dialog.destroy.assert_called_once()

    def test_on_ok_empty_title_shows_error(self):
        """Test that empty title shows error and doesn't destroy."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.result = None  # Initialize result
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "   "
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""
        dialog.destroy = MagicMock()

        with patch('tkinter.messagebox.showerror'):
            dialog._on_ok()
            assert dialog.result is None
            dialog.destroy.assert_not_called()

    def test_on_ok_invalid_date_shows_error(self):
        """Test that invalid date shows error."""
        dialog = AddTaskDialog.__new__(AddTaskDialog)
        dialog.result = None  # Initialize result
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Valid Title"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = "invalid-date"
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""
        dialog.destroy = MagicMock()

        with patch('tkinter.messagebox.showerror'):
            dialog._on_ok()
            assert dialog.result is None
            dialog.destroy.assert_not_called()


class TestEditTaskDialogLogic:
    """Tests for EditTaskDialog business logic."""

    def test_get_task_data_modified(self):
        """Test getting modified task data."""
        task = {
            "id": "task1",
            "title": "Original Title",
            "description": None,
            "due_date": None,
            "project_id": None,
            "project_name": ""
        }
        dialog = EditTaskDialog.__new__(EditTaskDialog)
        dialog.task = task
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Modified Title"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        data = dialog.get_task_data()
        assert data["title"] == "Modified Title"

    def test_get_task_data_preserves_description(self):
        """Test that description is properly retrieved."""
        task = {
            "id": "task1",
            "title": "Task",
            "description": "Original description",
            "due_date": None,
            "project_id": None,
            "project_name": ""
        }
        dialog = EditTaskDialog.__new__(EditTaskDialog)
        dialog.task = task
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Task"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = "Updated description"
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        data = dialog.get_task_data()
        assert data["description"] == "Updated description"

    def test_get_task_data_with_new_due_date(self):
        """Test adding a due date to a task that didn't have one."""
        task = {
            "id": "task1",
            "title": "Task",
            "description": None,
            "due_date": None,
            "project_id": None,
            "project_name": ""
        }
        dialog = EditTaskDialog.__new__(EditTaskDialog)
        dialog.task = task
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Task"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = "2025-05-20"
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""

        data = dialog.get_task_data()
        assert data["due_date"] is not None
        assert data["due_date"].year == 2025
        assert data["due_date"].month == 5

    def test_set_projects_for_edit(self):
        """Test setting projects in edit dialog."""
        task = {
            "id": "task1",
            "title": "Task",
            "description": None,
            "due_date": None,
            "project_id": None,
            "project_name": ""
        }
        dialog = EditTaskDialog.__new__(EditTaskDialog)
        dialog.task = task
        dialog.project_combo = MagicMock()

        projects = [("proj1", "Project One"), ("proj2", "Project Two")]
        dialog.set_projects(projects)

        expected_values = ["Project One", "Project Two"]
        dialog.project_combo.__setitem__.assert_called_with("values", expected_values)

    def test_on_ok_empty_title_shows_error(self):
        """Test that empty title in edit shows error."""
        task = {
            "id": "task1",
            "title": "Task",
            "description": None,
            "due_date": None,
            "project_id": None,
            "project_name": ""
        }
        dialog = EditTaskDialog.__new__(EditTaskDialog)
        dialog.result = None  # Initialize result
        dialog.task = task
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = ""
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""
        dialog.destroy = MagicMock()

        with patch('tkinter.messagebox.showerror'):
            dialog._on_ok()
            assert dialog.result is None

    def test_on_ok_valid_edit(self):
        """Test valid edit operation."""
        task = {
            "id": "task1",
            "title": "Original",
            "description": None,
            "due_date": None,
            "project_id": None,
            "project_name": ""
        }
        dialog = EditTaskDialog.__new__(EditTaskDialog)
        dialog.task = task
        dialog.title_entry = MagicMock()
        dialog.title_entry.get.return_value = "Updated Title"
        dialog.desc_text = MagicMock()
        dialog.desc_text.get.return_value = ""
        dialog.due_date_entry = MagicMock()
        dialog.due_date_entry.get.return_value = ""
        dialog.project_var = MagicMock()
        dialog.project_var.get.return_value = ""
        dialog.destroy = MagicMock()

        dialog._on_ok()
        assert dialog.result is not None
        assert dialog.result["title"] == "Updated Title"


class TestDeleteConfirmDialogLogic:
    """Tests for DeleteConfirmDialog business logic."""

    def test_on_delete_sets_result_true(self):
        """Test that delete button sets result to True."""
        dialog = DeleteConfirmDialog.__new__(DeleteConfirmDialog)
        dialog.task_title = "Task to Delete"
        dialog.result = None
        dialog.destroy = MagicMock()

        dialog._on_delete()
        assert dialog.result is True
        dialog.destroy.assert_called_once()

    def test_on_cancel_sets_result_none(self):
        """Test that cancel button sets result to None."""
        dialog = DeleteConfirmDialog.__new__(DeleteConfirmDialog)
        dialog.task_title = "Task"
        dialog.result = None
        dialog.destroy = MagicMock()

        dialog._on_cancel()
        assert dialog.result is None
        dialog.destroy.assert_called_once()

    def test_task_title_stored(self):
        """Test that task title is stored correctly."""
        dialog = DeleteConfirmDialog.__new__(DeleteConfirmDialog)
        dialog.task_title = "My Task"
        assert dialog.task_title == "My Task"

    def test_with_long_task_title(self):
        """Test handling of very long task titles."""
        dialog = DeleteConfirmDialog.__new__(DeleteConfirmDialog)
        long_title = "A" * 100
        dialog.task_title = long_title
        assert dialog.task_title == long_title

    def test_with_special_characters_in_title(self):
        """Test handling of special characters in task title."""
        dialog = DeleteConfirmDialog.__new__(DeleteConfirmDialog)
        special_title = 'Task with "quotes" and \'apostrophes\''
        dialog.task_title = special_title
        assert dialog.task_title == special_title

    def test_initial_result_none(self):
        """Test that initial result is None."""
        dialog = DeleteConfirmDialog.__new__(DeleteConfirmDialog)
        dialog.result = None
        assert dialog.result is None
