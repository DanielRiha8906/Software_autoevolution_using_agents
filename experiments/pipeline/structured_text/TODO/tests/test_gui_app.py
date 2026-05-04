"""Tests for GUIApp main window class - testing business logic without UI rendering."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from src.container import Container
from src.models.task_status import TaskStatus
from src.exceptions import TaskNotFoundError


class TestGUIAppIntegration:
    """Integration tests for GUIApp business logic using mocked tkinter."""

    @pytest.fixture
    def mock_gui_app(self, tmp_path):
        """Create a mocked GUIApp instance."""
        from src.gui.app import GUIApp

        with patch('tkinter.Tk.__init__', return_value=None):
            with patch('tkinter.Tk.title'):
                with patch('tkinter.Tk.geometry'):
                    with patch.object(GUIApp, '_create_widgets'):
                        with patch.object(GUIApp, '_refresh_tasks'):
                            app = GUIApp(storage_path=str(tmp_path / "tasks.json"))
                            # Manually set up attributes that would be created normally
                            app.container = Container(storage_path=str(tmp_path / "tasks.json"))
                            app.service = app.container.get_todo_service()
                            app.action_bar = MagicMock()
                            app.filter_bar = MagicMock()
                            app.filter_bar.get_status_filter = MagicMock(return_value=None)
                            app.task_list = MagicMock()
                            app.task_list.clear = MagicMock()
                            app.task_list.add_task = MagicMock()
                            app.status_label = MagicMock()
                            app._selected_task_id = None
                            yield app

    def test_gui_app_has_container(self, mock_gui_app):
        """Test that GUIApp initializes a Container."""
        assert hasattr(mock_gui_app, 'container')
        assert isinstance(mock_gui_app.container, Container)

    def test_gui_app_has_service(self, mock_gui_app):
        """Test that GUIApp initializes TodoService."""
        assert hasattr(mock_gui_app, 'service')
        assert mock_gui_app.service is not None

    def test_on_task_select_sets_selected_id(self, mock_gui_app):
        """Test that selecting a task sets the selected ID."""
        task = mock_gui_app.service.add_task("Test Task")
        mock_gui_app._on_task_select(task.id)
        assert mock_gui_app._selected_task_id == task.id

    def test_on_task_select_updates_status_label(self, mock_gui_app):
        """Test that selecting a task updates status label."""
        task = mock_gui_app.service.add_task("Test Task")
        mock_gui_app._on_task_select(task.id)
        # Should call config on status label
        mock_gui_app.status_label.config.assert_called()

    def test_on_task_select_nonexistent_task(self, mock_gui_app):
        """Test selecting a nonexistent task."""
        mock_gui_app._on_task_select("nonexistent-id")
        # Should still call config, but with error message
        mock_gui_app.status_label.config.assert_called()

    def test_on_task_double_click_initiates_edit(self, mock_gui_app):
        """Test that double-click sets ID and triggers edit."""
        task = mock_gui_app.service.add_task("Task to Edit")
        with patch.object(mock_gui_app, '_on_edit_task') as mock_edit:
            mock_gui_app._on_task_double_click(task.id)
            assert mock_gui_app._selected_task_id == task.id
            mock_edit.assert_called_once()

    def test_on_filter_change_calls_refresh(self, mock_gui_app):
        """Test that filter change triggers refresh."""
        with patch.object(mock_gui_app, '_refresh_tasks') as mock_refresh:
            mock_gui_app._on_filter_change()
            mock_refresh.assert_called_once()

    def test_on_edit_task_no_selection_shows_warning(self, mock_gui_app):
        """Test that edit without selection shows warning."""
        mock_gui_app._selected_task_id = None
        with patch('tkinter.messagebox.showwarning') as mock_warn:
            mock_gui_app._on_edit_task()
            mock_warn.assert_called()

    def test_on_delete_task_no_selection_shows_warning(self, mock_gui_app):
        """Test that delete without selection shows warning."""
        mock_gui_app._selected_task_id = None
        with patch('tkinter.messagebox.showwarning') as mock_warn:
            mock_gui_app._on_delete_task()
            mock_warn.assert_called()

    def test_on_filter_change_causes_refresh(self, mock_gui_app):
        """Test that _on_filter_change calls _refresh_tasks."""
        with patch.object(mock_gui_app, '_refresh_tasks') as mock_refresh:
            mock_gui_app._on_filter_change()
            mock_refresh.assert_called_once()

    def test_service_list_tasks_no_filter(self, mock_gui_app):
        """Test service list_tasks without filter."""
        task = mock_gui_app.service.add_task("Test Task")
        tasks = mock_gui_app.service.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Test Task"

    def test_service_list_tasks_with_status_filter(self, mock_gui_app):
        """Test service list_tasks with status filter."""
        task1 = mock_gui_app.service.add_task("Pending Task")
        task2 = mock_gui_app.service.add_task("Done Task")
        mock_gui_app.service.complete_task(task2.id)

        # Filter by done status
        done_tasks = mock_gui_app.service.list_tasks(status=TaskStatus.DONE)
        assert len(done_tasks) == 1
        assert done_tasks[0].status == TaskStatus.DONE


class TestGUIAppAddTaskLogic:
    """Tests for add task functionality."""

    @pytest.fixture
    def mock_gui_app_for_add(self, tmp_path):
        """Create a mocked GUIApp for add task tests."""
        from src.gui.app import GUIApp

        with patch('tkinter.Tk.__init__', return_value=None):
            with patch('tkinter.Tk.title'):
                with patch('tkinter.Tk.geometry'):
                    with patch.object(GUIApp, '_create_widgets'):
                        with patch.object(GUIApp, '_refresh_tasks'):
                            app = GUIApp(storage_path=str(tmp_path / "tasks.json"))
                            app.container = Container(storage_path=str(tmp_path / "tasks.json"))
                            app.service = app.container.get_todo_service()
                            app.status_label = MagicMock()
                            app._selected_task_id = None
                            yield app

    @patch('src.gui.app.AddTaskDialog')
    def test_on_add_task_shows_dialog(self, mock_dialog_class, mock_gui_app_for_add):
        """Test that add task shows the dialog."""
        mock_dialog = MagicMock()
        mock_dialog.result = None
        mock_dialog_class.return_value = mock_dialog

        mock_gui_app_for_add.service.list_projects = MagicMock(return_value=[])
        mock_gui_app_for_add.wait_window = MagicMock()

        mock_gui_app_for_add._on_add_task()
        mock_dialog_class.assert_called_once()

    @patch('src.gui.app.AddTaskDialog')
    def test_on_add_task_creates_task(self, mock_dialog_class, mock_gui_app_for_add):
        """Test that confirmed add dialog creates a task."""
        mock_dialog = MagicMock()
        mock_dialog.result = {
            "title": "New Task",
            "description": "Task description",
            "due_date": None,
            "project_id": None
        }
        mock_dialog_class.return_value = mock_dialog
        mock_gui_app_for_add.service.list_projects = MagicMock(return_value=[])
        mock_gui_app_for_add.wait_window = MagicMock()

        with patch.object(mock_gui_app_for_add, '_refresh_tasks'):
            mock_gui_app_for_add._on_add_task()

            # Verify task was created
            tasks = mock_gui_app_for_add.service.list_tasks()
            assert len(tasks) == 1
            assert tasks[0].title == "New Task"

    @patch('src.gui.app.AddTaskDialog')
    def test_on_add_task_cancelled(self, mock_dialog_class, mock_gui_app_for_add):
        """Test that cancelled add dialog doesn't create task."""
        mock_dialog = MagicMock()
        mock_dialog.result = None
        mock_dialog_class.return_value = mock_dialog
        mock_gui_app_for_add.service.list_projects = MagicMock(return_value=[])
        mock_gui_app_for_add.wait_window = MagicMock()

        initial_count = len(mock_gui_app_for_add.service.list_tasks())
        mock_gui_app_for_add._on_add_task()
        final_count = len(mock_gui_app_for_add.service.list_tasks())

        assert initial_count == final_count


class TestGUIAppEditTaskLogic:
    """Tests for edit task functionality."""

    @pytest.fixture
    def mock_gui_app_for_edit(self, tmp_path):
        """Create a mocked GUIApp for edit task tests."""
        from src.gui.app import GUIApp

        with patch('tkinter.Tk.__init__', return_value=None):
            with patch('tkinter.Tk.title'):
                with patch('tkinter.Tk.geometry'):
                    with patch.object(GUIApp, '_create_widgets'):
                        with patch.object(GUIApp, '_refresh_tasks'):
                            app = GUIApp(storage_path=str(tmp_path / "tasks.json"))
                            app.container = Container(storage_path=str(tmp_path / "tasks.json"))
                            app.service = app.container.get_todo_service()
                            app.status_label = MagicMock()
                            app._selected_task_id = None
                            yield app

    @patch('src.gui.app.EditTaskDialog')
    def test_on_edit_task_shows_dialog(self, mock_dialog_class, mock_gui_app_for_edit):
        """Test that edit task shows the dialog."""
        task = mock_gui_app_for_edit.service.add_task("Task to Edit")
        mock_gui_app_for_edit._selected_task_id = task.id

        mock_dialog = MagicMock()
        mock_dialog.result = None
        mock_dialog_class.return_value = mock_dialog
        mock_gui_app_for_edit.service.list_projects = MagicMock(return_value=[])
        mock_gui_app_for_edit.wait_window = MagicMock()

        mock_gui_app_for_edit._on_edit_task()
        mock_dialog_class.assert_called_once()

    def test_on_edit_task_nonexistent(self, mock_gui_app_for_edit):
        """Test editing a nonexistent task."""
        mock_gui_app_for_edit._selected_task_id = "nonexistent-id"

        with patch('tkinter.messagebox.showerror') as mock_error:
            mock_gui_app_for_edit._on_edit_task()
            mock_error.assert_called()


class TestGUIAppDeleteTaskLogic:
    """Tests for delete task functionality."""

    @pytest.fixture
    def mock_gui_app_for_delete(self, tmp_path):
        """Create a mocked GUIApp for delete task tests."""
        from src.gui.app import GUIApp

        with patch('tkinter.Tk.__init__', return_value=None):
            with patch('tkinter.Tk.title'):
                with patch('tkinter.Tk.geometry'):
                    with patch.object(GUIApp, '_create_widgets'):
                        with patch.object(GUIApp, '_refresh_tasks'):
                            app = GUIApp(storage_path=str(tmp_path / "tasks.json"))
                            app.container = Container(storage_path=str(tmp_path / "tasks.json"))
                            app.service = app.container.get_todo_service()
                            app.status_label = MagicMock()
                            app._selected_task_id = None
                            yield app

    @patch('src.gui.app.DeleteConfirmDialog')
    def test_on_delete_task_shows_confirmation(self, mock_dialog_class, mock_gui_app_for_delete):
        """Test that delete task shows confirmation dialog."""
        task = mock_gui_app_for_delete.service.add_task("Task to Delete")
        mock_gui_app_for_delete._selected_task_id = task.id

        mock_dialog = MagicMock()
        mock_dialog.result = None
        mock_dialog_class.return_value = mock_dialog
        mock_gui_app_for_delete.wait_window = MagicMock()

        mock_gui_app_for_delete._on_delete_task()
        mock_dialog_class.assert_called_once()

    @patch('src.gui.app.DeleteConfirmDialog')
    def test_on_delete_task_confirmed(self, mock_dialog_class, mock_gui_app_for_delete):
        """Test that confirmed delete removes the task."""
        task = mock_gui_app_for_delete.service.add_task("Task to Delete")
        mock_gui_app_for_delete._selected_task_id = task.id

        mock_dialog = MagicMock()
        mock_dialog.result = True
        mock_dialog_class.return_value = mock_dialog
        mock_gui_app_for_delete.wait_window = MagicMock()

        with patch.object(mock_gui_app_for_delete, '_refresh_tasks'):
            mock_gui_app_for_delete._on_delete_task()

            # Verify task was deleted
            assert mock_gui_app_for_delete._selected_task_id is None
            tasks = mock_gui_app_for_delete.service.list_tasks()
            assert len(tasks) == 0

    @patch('src.gui.app.DeleteConfirmDialog')
    def test_on_delete_task_cancelled(self, mock_dialog_class, mock_gui_app_for_delete):
        """Test that cancelled delete keeps the task."""
        task = mock_gui_app_for_delete.service.add_task("Task Not to Delete")
        mock_gui_app_for_delete._selected_task_id = task.id

        mock_dialog = MagicMock()
        mock_dialog.result = None
        mock_dialog_class.return_value = mock_dialog
        mock_gui_app_for_delete.wait_window = MagicMock()

        initial_count = len(mock_gui_app_for_delete.service.list_tasks())
        mock_gui_app_for_delete._on_delete_task()
        final_count = len(mock_gui_app_for_delete.service.list_tasks())

        assert initial_count == final_count

    def test_on_delete_task_nonexistent(self, mock_gui_app_for_delete):
        """Test deleting a nonexistent task."""
        mock_gui_app_for_delete._selected_task_id = "nonexistent-id"

        with patch('tkinter.messagebox.showerror') as mock_error:
            mock_gui_app_for_delete._on_delete_task()
            mock_error.assert_called()
