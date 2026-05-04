"""Unit tests for WorkflowRunGUI and FilterState."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch
import tkinter as tk

from src.models.workflow_run import WorkflowRun
from src.models.workflow_run_attempt import WorkflowRunAttempt
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.gui.filters import FilterState
from src.gui.workflow_run_gui import WorkflowRunGUI


def _make_run(
    run_id: str = "run-1",
    workflow_name: str = "CI",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    duration_seconds: float = 10.5,
) -> WorkflowRun:
    """Helper to create a test WorkflowRun."""
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


def _make_attempt(
    id: int = 1,
    run_id: int = 1,
    attempt_number: int = 1,
    status: str = "completed",
    conclusion: str = "success",
    duration_seconds: float = 5.0,
) -> WorkflowRunAttempt:
    """Helper to create a test WorkflowRunAttempt."""
    return WorkflowRunAttempt(
        id=id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )


class TestFilterState:
    """Tests for FilterState class."""

    def test_filter_state_init_empty(self):
        """Test FilterState initialization with no filters."""
        fs = FilterState()
        assert fs.status is None
        assert fs.conclusion is None
        assert not fs.is_active()

    def test_filter_state_init_with_values(self):
        """Test FilterState initialization with status and conclusion."""
        fs = FilterState(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )
        assert fs.status == WorkflowStatus.COMPLETED
        assert fs.conclusion == WorkflowConclusion.SUCCESS
        assert fs.is_active()

    def test_filter_state_is_active_with_status(self):
        """Test is_active returns True when status is set."""
        fs = FilterState(status=WorkflowStatus.COMPLETED)
        assert fs.is_active()

    def test_filter_state_is_active_with_conclusion(self):
        """Test is_active returns True when conclusion is set."""
        fs = FilterState(conclusion=WorkflowConclusion.FAILURE)
        assert fs.is_active()

    def test_filter_state_to_filter_params(self):
        """Test to_filter_params returns dict with status and conclusion."""
        fs = FilterState(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
        )
        params = fs.to_filter_params()
        assert params["status"] == WorkflowStatus.COMPLETED
        assert params["conclusion"] == WorkflowConclusion.FAILURE

    def test_filter_state_reset(self):
        """Test reset clears filters."""
        fs = FilterState(
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
        )
        fs.reset()
        assert fs.status is None
        assert fs.conclusion is None
        assert not fs.is_active()


class TestWorkflowRunGUIInitialization:
    """Tests for WorkflowRunGUI initialization."""

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_gui_init(self, mock_tk, mock_stringvar):
        """Test GUI initialization."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        service = MagicMock()
        service.list_runs.return_value = []
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)

        assert gui.service is service
        assert gui.attempt_service is attempt_service
        assert gui.statistics_service is statistics_service
        assert gui.root is mock_root
        assert gui.all_runs == []

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_gui_populate_table_with_runs(self, mock_tk, mock_stringvar):
        """Test populate_table loads runs from service."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        run1 = _make_run("r1")
        run2 = _make_run("r2", conclusion=WorkflowConclusion.FAILURE)

        service = MagicMock()
        service.list_runs.return_value = [run1, run2]
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)

        assert len(gui.all_runs) == 2
        assert gui.all_runs[0] == run1
        assert gui.all_runs[1] == run2

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_gui_populate_table_empty(self, mock_tk, mock_stringvar):
        """Test populate_table with no runs."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        service = MagicMock()
        service.list_runs.return_value = []
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)

        assert gui.all_runs == []


class TestWorkflowRunGUIFiltering:
    """Tests for filtering functionality in WorkflowRunGUI."""

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_apply_status_filter(self, mock_tk, mock_stringvar):
        """Test applying status filter."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_status_var = MagicMock()
        mock_status_var.get.return_value = "completed"
        mock_stringvar.return_value = mock_status_var

        run1 = _make_run("r1", status=WorkflowStatus.COMPLETED)
        run2 = _make_run("r2", status=WorkflowStatus.QUEUED)

        service = MagicMock()
        service.list_runs.return_value = [run1, run2]
        service.filter_runs.return_value = [run1]
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"), \
             patch.object(WorkflowRunGUI, "_refresh_table"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.status_var = mock_status_var
            gui.conclusion_var = MagicMock()
            gui.conclusion_var.get.return_value = ""
            gui._apply_filters()

        assert gui.filter_state.status == WorkflowStatus.COMPLETED
        assert gui.all_runs == [run1]

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_apply_conclusion_filter(self, mock_tk, mock_stringvar):
        """Test applying conclusion filter."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_conclusion_var = MagicMock()
        mock_conclusion_var.get.return_value = "failure"
        mock_stringvar.return_value = mock_conclusion_var

        run1 = _make_run("r1", conclusion=WorkflowConclusion.SUCCESS)
        run2 = _make_run("r2", conclusion=WorkflowConclusion.FAILURE)

        service = MagicMock()
        service.list_runs.return_value = [run1, run2]
        service.filter_runs.return_value = [run2]
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"), \
             patch.object(WorkflowRunGUI, "_refresh_table"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.status_var = MagicMock()
            gui.status_var.get.return_value = ""
            gui.conclusion_var = mock_conclusion_var
            gui._apply_filters()

        assert gui.filter_state.conclusion == WorkflowConclusion.FAILURE
        assert gui.all_runs == [run2]

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_apply_combined_filters(self, mock_tk, mock_stringvar):
        """Test applying both status and conclusion filters (AND logic)."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        run1 = _make_run("r1", status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS)
        run2 = _make_run("r2", status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE)

        service = MagicMock()
        service.list_runs.return_value = [run1, run2]
        service.filter_runs.return_value = [run2]
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"), \
             patch.object(WorkflowRunGUI, "_refresh_table"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.status_var = MagicMock()
            gui.status_var.get.return_value = "completed"
            gui.conclusion_var = MagicMock()
            gui.conclusion_var.get.return_value = "failure"
            gui._apply_filters()

        assert gui.filter_state.status == WorkflowStatus.COMPLETED
        assert gui.filter_state.conclusion == WorkflowConclusion.FAILURE
        service.filter_runs.assert_called()

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_reset_filters(self, mock_tk, mock_stringvar):
        """Test resetting filters."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        run1 = _make_run("r1")
        run2 = _make_run("r2")

        service = MagicMock()
        service.list_runs.return_value = [run1, run2]
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"), \
             patch.object(WorkflowRunGUI, "_refresh_table"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.filter_state.status = WorkflowStatus.COMPLETED
            gui.filter_state.conclusion = WorkflowConclusion.FAILURE
            gui.status_var = MagicMock()
            gui.conclusion_var = MagicMock()

            gui._reset_filters()

        assert gui.filter_state.status is None
        assert gui.filter_state.conclusion is None
        gui.status_var.set.assert_called_with("")
        gui.conclusion_var.set.assert_called_with("")
        assert gui.all_runs == [run1, run2]


class TestWorkflowRunGUIRowColoring:
    """Tests for row coloring in WorkflowRunGUI."""

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_failed_run_highlighting(self, mock_tk, mock_stringvar):
        """Test that failed runs are highlighted in light red."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        run_success = _make_run("r1", conclusion=WorkflowConclusion.SUCCESS)
        run_failure = _make_run("r2", conclusion=WorkflowConclusion.FAILURE)

        service = MagicMock()
        service.list_runs.return_value = [run_success, run_failure]
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.all_runs = [run_success, run_failure]
            gui.treeview = MagicMock()
            gui.treeview.get_children.return_value = []

        # Manually call _refresh_table to test coloring logic
        gui._refresh_table()
        gui.treeview.tag_configure.assert_called_with("failed", background="#ffcccc")


class TestWorkflowRunGUIDetailView:
    """Tests for detail view in WorkflowRunGUI."""

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_show_detail(self, mock_tk, mock_stringvar):
        """Test showing detail for selected run."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        run = _make_run("run-123", workflow_name="Deploy", branch="develop")

        service = MagicMock()
        service.list_runs.return_value = [run]
        service.get_run_detail.return_value = run
        attempt_service = MagicMock()
        attempt_service.get_attempts_by_run_id.return_value = []
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.treeview = MagicMock()
            # Mock the treeview.item() call to return values as a tuple
            gui.treeview.item = MagicMock(return_value={"values": ("run-123", "Deploy", "completed", "success", "10.5", "1", "2025-01-01")})
            gui.treeview.item.side_effect = lambda item_id, key: ("run-123", "Deploy", "completed", "success", "10.5", "1", "2025-01-01") if key == "values" else {}
            gui.detail_labels = {
                "id": MagicMock(),
                "workflow": MagicMock(),
                "branch": MagicMock(),
                "status": MagicMock(),
                "conclusion": MagicMock(),
                "created_at": MagicMock(),
                "updated_at": MagicMock(),
                "duration": MagicMock(),
            }
            gui.attempts_treeview = MagicMock()
            gui.attempts_treeview.get_children.return_value = []
            gui._show_detail("mock_item_id")

        # Verify detail labels were updated
        gui.detail_labels["id"].config.assert_called_with(text="run-123")
        gui.detail_labels["workflow"].config.assert_called_with(text="Deploy")
        gui.detail_labels["branch"].config.assert_called_with(text="develop")

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_show_attempts(self, mock_tk, mock_stringvar):
        """Test showing attempts for a run."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        run = _make_run("1")

        attempt1 = _make_attempt(id=1, run_id=1, attempt_number=1, conclusion="success")
        attempt2 = _make_attempt(id=2, run_id=1, attempt_number=2, conclusion="failure")

        service = MagicMock()
        service.list_runs.return_value = [run]
        attempt_service = MagicMock()
        attempt_service.get_attempts_by_run_id.return_value = [attempt1, attempt2]
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.attempts_treeview = MagicMock()
            gui.attempts_treeview.get_children.return_value = []
            gui._show_attempts(run)

        attempt_service.get_attempts_by_run_id.assert_called_with(1)

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_show_detail_not_found(self, mock_tk, mock_stringvar):
        """Test showing detail when run is not found."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        service = MagicMock()
        service.list_runs.return_value = []
        service.get_run_detail.return_value = None
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"), \
             patch.object(WorkflowRunGUI, "_show_error") as mock_error:
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.treeview = MagicMock()
            # Mock the treeview.item() call to return values as a tuple
            gui.treeview.item.side_effect = lambda item_id, key: ("unknown-id", "CI", "completed", "success", "10.5", "1", "2025-01-01") if key == "values" else {}
            gui._show_detail("mock_item_id")

        mock_error.assert_called()


class TestWorkflowRunGUIErrorHandling:
    """Tests for error handling in WorkflowRunGUI."""

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_filter_error_handling(self, mock_tk, mock_stringvar):
        """Test error handling when filter_runs raises ValueError."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        service = MagicMock()
        service.list_runs.return_value = []
        service.filter_runs.side_effect = ValueError("Invalid filter")
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"), \
             patch.object(WorkflowRunGUI, "_show_error") as mock_error:
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.status_var = MagicMock()
            gui.status_var.get.return_value = "completed"
            gui.conclusion_var = MagicMock()
            gui.conclusion_var.get.return_value = ""
            gui._apply_filters()

        mock_error.assert_called()

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_populate_table_error(self, mock_tk, mock_stringvar):
        """Test error handling during populate_table."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        service = MagicMock()
        service.list_runs.side_effect = Exception("Storage error")
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"), \
             patch.object(WorkflowRunGUI, "_show_error") as mock_error:
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)

        mock_error.assert_called()


class TestWorkflowRunGUIRowSelection:
    """Tests for row selection in WorkflowRunGUI."""

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_on_row_selected(self, mock_tk, mock_stringvar):
        """Test row selection event handler."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        run = _make_run("run-1")

        service = MagicMock()
        service.list_runs.return_value = [run]
        service.get_run_detail.return_value = run
        attempt_service = MagicMock()
        attempt_service.get_attempts_by_run_id.return_value = []
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)

            # Mock treeview selection
            gui.treeview = MagicMock()
            gui.treeview.selection.return_value = ["item1"]

            with patch.object(gui, "_show_detail") as mock_show:
                gui._on_row_selected(Mock())

            mock_show.assert_called()


class TestWorkflowRunGUIEmptyTable:
    """Tests for empty table handling in WorkflowRunGUI."""

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_empty_table(self, mock_tk, mock_stringvar):
        """Test GUI with no runs."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        service = MagicMock()
        service.list_runs.return_value = []
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)

        assert gui.all_runs == []

    @patch("src.gui.workflow_run_gui.tk.StringVar")
    @patch("src.gui.workflow_run_gui.tk.Tk")
    def test_refresh_empty_table(self, mock_tk, mock_stringvar):
        """Test refreshing with no runs."""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_stringvar.return_value = MagicMock()

        service = MagicMock()
        service.list_runs.return_value = []
        attempt_service = MagicMock()
        statistics_service = MagicMock()

        with patch.object(WorkflowRunGUI, "_setup_ui"):
            gui = WorkflowRunGUI(service, attempt_service, statistics_service)
            gui.all_runs = []
            gui.treeview = MagicMock()
            gui.treeview.get_children.return_value = []

            # This should not raise
            gui._refresh_table()
