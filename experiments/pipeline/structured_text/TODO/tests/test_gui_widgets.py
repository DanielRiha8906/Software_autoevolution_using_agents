"""Tests for GUI widget classes - testing business logic without UI rendering."""

import pytest
from unittest.mock import Mock, MagicMock, call
from src.gui.widgets.task_list import TaskListWidget
from src.gui.widgets.filter_bar import FilterBar
from src.gui.widgets.action_bar import ActionBar


class TestTaskListWidgetLogic:
    """Tests for TaskListWidget business logic."""

    def test_get_status_symbol_pending(self):
        """Test status symbol for pending status."""
        widget = TaskListWidget.__new__(TaskListWidget)
        assert widget._get_status_symbol("pending") == "[ ]"

    def test_get_status_symbol_in_progress(self):
        """Test status symbol for in_progress status."""
        widget = TaskListWidget.__new__(TaskListWidget)
        assert widget._get_status_symbol("in_progress") == "[~]"

    def test_get_status_symbol_done(self):
        """Test status symbol for done status."""
        widget = TaskListWidget.__new__(TaskListWidget)
        assert widget._get_status_symbol("done") == "[x]"

    def test_get_status_symbol_unknown(self):
        """Test status symbol for unknown status."""
        widget = TaskListWidget.__new__(TaskListWidget)
        assert widget._get_status_symbol("unknown") == "?"

    def test_add_task_basic(self):
        """Test adding a basic task to the widget."""
        widget = TaskListWidget.__new__(TaskListWidget)
        widget._task_id_map = {}
        widget.tree = MagicMock()
        widget.tree.insert = MagicMock(return_value="item1")

        task = {
            "id": "task1",
            "title": "Test Task",
            "status": "pending",
            "due_date": None,
            "project_name": "My Project"
        }
        widget.add_task(task, is_overdue=False)

        # Verify task was mapped
        assert "item1" in widget._task_id_map
        assert widget._task_id_map["item1"] == "task1"
        widget.tree.insert.assert_called_once()

    def test_add_task_with_overdue(self):
        """Test adding an overdue task."""
        from datetime import datetime, timezone
        widget = TaskListWidget.__new__(TaskListWidget)
        widget._task_id_map = {}
        widget.tree = MagicMock()
        widget.tree.insert = MagicMock(return_value="item1")
        widget.tree.tag_configure = MagicMock()

        task = {
            "id": "task1",
            "title": "Overdue Task",
            "status": "pending",
            "due_date": datetime(2020, 1, 1, tzinfo=timezone.utc),
            "project_name": ""
        }
        widget.add_task(task, is_overdue=True)

        # Verify overdue tag configuration was called
        widget.tree.tag_configure.assert_called()

    def test_clear_tasks(self):
        """Test clearing all tasks."""
        widget = TaskListWidget.__new__(TaskListWidget)
        widget._task_id_map = {"item1": "task1", "item2": "task2"}
        widget.tree = MagicMock()
        widget.tree.get_children = MagicMock(return_value=["item1", "item2"])

        widget.clear()

        # Verify delete was called for each item
        assert widget.tree.delete.call_count == 2
        assert widget._task_id_map == {}

    def test_clear_empty_list(self):
        """Test clearing an empty list."""
        widget = TaskListWidget.__new__(TaskListWidget)
        widget._task_id_map = {}
        widget.tree = MagicMock()
        widget.tree.get_children = MagicMock(return_value=[])

        widget.clear()

        assert widget._task_id_map == {}
        widget.tree.delete.assert_not_called()

    def test_get_selected_task_id_when_selected(self):
        """Test getting selected task ID when a task is selected."""
        widget = TaskListWidget.__new__(TaskListWidget)
        widget._task_id_map = {"item1": "task1"}
        widget.tree = MagicMock()
        widget.tree.selection = MagicMock(return_value=("item1",))

        result = widget.get_selected_task_id()
        assert result == "task1"

    def test_get_selected_task_id_when_none_selected(self):
        """Test getting selected task ID when nothing is selected."""
        widget = TaskListWidget.__new__(TaskListWidget)
        widget._task_id_map = {}
        widget.tree = MagicMock()
        widget.tree.selection = MagicMock(return_value=())

        result = widget.get_selected_task_id()
        assert result is None

    def test_get_selected_task_id_unmapped_item(self):
        """Test getting selected task ID for unmapped item."""
        widget = TaskListWidget.__new__(TaskListWidget)
        widget._task_id_map = {}
        widget.tree = MagicMock()
        widget.tree.selection = MagicMock(return_value=("item1",))

        result = widget.get_selected_task_id()
        assert result is None

    def test_widget_callbacks(self):
        """Test widget callbacks are stored."""
        on_select = Mock()
        on_double_click = Mock()
        widget = TaskListWidget.__new__(TaskListWidget)
        widget.on_select = on_select
        widget.on_double_click = on_double_click

        assert widget.on_select == on_select
        assert widget.on_double_click == on_double_click

    def test_on_select_with_callback(self):
        """Test selection event with callback."""
        on_select = Mock()
        widget = TaskListWidget.__new__(TaskListWidget)
        widget.on_select = on_select
        widget._task_id_map = {"item1": "task1"}
        widget.tree = MagicMock()
        widget.tree.selection = MagicMock(return_value=("item1",))

        widget._on_select(MagicMock())
        on_select.assert_called_once_with("task1")

    def test_on_select_without_callback(self):
        """Test selection event without callback doesn't error."""
        widget = TaskListWidget.__new__(TaskListWidget)
        widget.on_select = None
        widget._task_id_map = {}
        widget.tree = MagicMock()

        # Should not raise
        widget._on_select(MagicMock())

    def test_on_double_click_with_callback(self):
        """Test double-click event with callback."""
        on_double_click = Mock()
        widget = TaskListWidget.__new__(TaskListWidget)
        widget.on_double_click = on_double_click
        widget._task_id_map = {"item1": "task1"}
        widget.tree = MagicMock()
        widget.tree.identify = MagicMock(return_value="item1")

        event = MagicMock()
        event.x = 100
        event.y = 100
        widget._on_double_click(event)

        on_double_click.assert_called_once_with("task1")

    def test_on_double_click_without_item(self):
        """Test double-click on empty area."""
        on_double_click = Mock()
        widget = TaskListWidget.__new__(TaskListWidget)
        widget.on_double_click = on_double_click
        widget._task_id_map = {}
        widget.tree = MagicMock()
        widget.tree.identify = MagicMock(return_value="")

        event = MagicMock()
        widget._on_double_click(event)

        on_double_click.assert_not_called()


class TestFilterBarLogic:
    """Tests for FilterBar business logic."""

    def test_get_status_filter_all(self):
        """Test getting status filter when set to 'all'."""
        widget = FilterBar.__new__(FilterBar)
        widget.status_var = MagicMock()
        widget.status_var.get.return_value = "all"

        result = widget.get_status_filter()
        assert result is None

    def test_get_status_filter_pending(self):
        """Test getting status filter for 'pending'."""
        widget = FilterBar.__new__(FilterBar)
        widget.status_var = MagicMock()
        widget.status_var.get.return_value = "pending"

        result = widget.get_status_filter()
        assert result == "pending"

    def test_get_status_filter_in_progress(self):
        """Test getting status filter for 'in_progress'."""
        widget = FilterBar.__new__(FilterBar)
        widget.status_var = MagicMock()
        widget.status_var.get.return_value = "in_progress"

        result = widget.get_status_filter()
        assert result == "in_progress"

    def test_get_status_filter_done(self):
        """Test getting status filter for 'done'."""
        widget = FilterBar.__new__(FilterBar)
        widget.status_var = MagicMock()
        widget.status_var.get.return_value = "done"

        result = widget.get_status_filter()
        assert result == "done"

    def test_get_project_filter_all(self):
        """Test getting project filter when set to 'all'."""
        widget = FilterBar.__new__(FilterBar)
        widget.project_var = MagicMock()
        widget.project_var.get.return_value = "all"

        result = widget.get_project_filter()
        assert result is None

    def test_get_project_filter_specific(self):
        """Test getting project filter for specific project."""
        widget = FilterBar.__new__(FilterBar)
        widget.project_var = MagicMock()
        widget.project_var.get.return_value = "proj1"

        result = widget.get_project_filter()
        assert result == "proj1"

    def test_set_projects_basic(self):
        """Test setting available projects."""
        widget = FilterBar.__new__(FilterBar)
        widget.project_combo = MagicMock()

        projects = [("proj1", "Project One"), ("proj2", "Project Two")]
        widget.set_projects(projects)

        # Should set combobox values to include project names
        expected_values = ["all", "Project One", "Project Two"]
        widget.project_combo.__setitem__.assert_called_with("values", expected_values)

    def test_set_projects_empty(self):
        """Test setting empty projects list."""
        widget = FilterBar.__new__(FilterBar)
        widget.project_combo = MagicMock()

        widget.set_projects([])

        # Should only have "all" option
        expected_values = ["all"]
        widget.project_combo.__setitem__.assert_called_with("values", expected_values)

    def test_set_projects_creates_id_map(self):
        """Test that set_projects creates project ID map."""
        widget = FilterBar.__new__(FilterBar)
        widget.project_combo = MagicMock()

        projects = [("proj1", "Project One"), ("proj2", "Project Two")]
        widget.set_projects(projects)

        assert widget._project_id_map["Project One"] == "proj1"
        assert widget._project_id_map["Project Two"] == "proj2"

    def test_reset_filters(self):
        """Test resetting filters to default."""
        widget = FilterBar.__new__(FilterBar)
        widget.status_var = MagicMock()
        widget.project_var = MagicMock()

        widget.reset_filters()

        widget.status_var.set.assert_called_with("all")
        widget.project_var.set.assert_called_with("all")

    def test_on_change_calls_callback(self):
        """Test that _on_change calls the callback."""
        on_filter_change = Mock()
        widget = FilterBar.__new__(FilterBar)
        widget.on_filter_change = on_filter_change

        widget._on_change()

        on_filter_change.assert_called_once()

    def test_on_change_without_callback(self):
        """Test that _on_change works without callback."""
        widget = FilterBar.__new__(FilterBar)
        widget.on_filter_change = None

        # Should not raise
        widget._on_change()


class TestActionBarLogic:
    """Tests for ActionBar business logic."""

    def test_on_add_click_calls_callback(self):
        """Test add button click invokes callback."""
        on_add = Mock()
        widget = ActionBar.__new__(ActionBar)
        widget.on_add = on_add

        widget._on_add_click()

        on_add.assert_called_once()

    def test_on_edit_click_calls_callback(self):
        """Test edit button click invokes callback."""
        on_edit = Mock()
        widget = ActionBar.__new__(ActionBar)
        widget.on_edit = on_edit

        widget._on_edit_click()

        on_edit.assert_called_once()

    def test_on_delete_click_calls_callback(self):
        """Test delete button click invokes callback."""
        on_delete = Mock()
        widget = ActionBar.__new__(ActionBar)
        widget.on_delete = on_delete

        widget._on_delete_click()

        on_delete.assert_called_once()

    def test_on_refresh_click_calls_callback(self):
        """Test refresh button click invokes callback."""
        on_refresh = Mock()
        widget = ActionBar.__new__(ActionBar)
        widget.on_refresh = on_refresh

        widget._on_refresh_click()

        on_refresh.assert_called_once()

    def test_add_click_without_callback(self):
        """Test add button click without callback doesn't error."""
        widget = ActionBar.__new__(ActionBar)
        widget.on_add = None

        # Should not raise
        widget._on_add_click()

    def test_edit_click_without_callback(self):
        """Test edit button click without callback doesn't error."""
        widget = ActionBar.__new__(ActionBar)
        widget.on_edit = None

        # Should not raise
        widget._on_edit_click()

    def test_delete_click_without_callback(self):
        """Test delete button click without callback doesn't error."""
        widget = ActionBar.__new__(ActionBar)
        widget.on_delete = None

        # Should not raise
        widget._on_delete_click()

    def test_refresh_click_without_callback(self):
        """Test refresh button click without callback doesn't error."""
        widget = ActionBar.__new__(ActionBar)
        widget.on_refresh = None

        # Should not raise
        widget._on_refresh_click()

    def test_multiple_callbacks(self):
        """Test ActionBar with multiple callbacks."""
        on_add = Mock()
        on_edit = Mock()
        on_delete = Mock()
        on_refresh = Mock()

        widget = ActionBar.__new__(ActionBar)
        widget.on_add = on_add
        widget.on_edit = on_edit
        widget.on_delete = on_delete
        widget.on_refresh = on_refresh

        widget._on_add_click()
        widget._on_edit_click()
        widget._on_delete_click()
        widget._on_refresh_click()

        on_add.assert_called_once()
        on_edit.assert_called_once()
        on_delete.assert_called_once()
        on_refresh.assert_called_once()

    def test_partial_callbacks(self):
        """Test ActionBar with some callbacks set."""
        on_add = Mock()
        on_refresh = Mock()

        widget = ActionBar.__new__(ActionBar)
        widget.on_add = on_add
        widget.on_edit = None
        widget.on_delete = None
        widget.on_refresh = on_refresh

        widget._on_add_click()
        widget._on_refresh_click()

        on_add.assert_called_once()
        on_refresh.assert_called_once()
