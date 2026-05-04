"""Tests for GUI viewer and workflow runs display."""

import pytest
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from unittest.mock import MagicMock, patch, call

from src.gui.gui_viewer import WorkflowRunsGUIViewer, run_gui
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_attempt_service import WorkflowAttemptService


def _make_run(
    run_id: str = "run-1234567890abcdef",
    workflow_name: str = "CI",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion = WorkflowConclusion.SUCCESS,
    created_at: datetime = None,
    updated_at: datetime = None,
    duration_seconds: float = 10.0,
) -> WorkflowRun:
    if created_at is None:
        created_at = datetime(2026, 5, 3, 10, 0, 0)
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=created_at,
        updated_at=updated_at,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def mock_run_service():
    """Mock WorkflowRunService."""
    service = MagicMock(spec=WorkflowRunService)
    service.list_runs.return_value = []
    return service


@pytest.fixture
def mock_attempt_service():
    """Mock WorkflowAttemptService."""
    service = MagicMock(spec=WorkflowAttemptService)
    service.filter_by_run_id.return_value = []
    return service


@pytest.fixture
def mock_tk_root():
    """Create a mock tkinter root without displaying."""
    root = MagicMock(spec=tk.Tk)
    root.title = MagicMock()
    root.geometry = MagicMock()
    root.mainloop = MagicMock()
    return root


class TestWorkflowRunsGUIViewerInit:
    """Tests for WorkflowRunsGUIViewer.__init__()"""

    def test_gui_viewer_initialization_with_mock_services(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test creating viewer with mock services."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)

        assert viewer._run_service is mock_run_service
        assert viewer._attempt_service is mock_attempt_service
        assert viewer._root is mock_tk_root
        assert viewer._treeview is None
        assert viewer._status_filter is None
        assert viewer._conclusion_filter is None
        assert viewer._current_runs == []

    def test_gui_viewer_initialization_with_provided_root(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test creating viewer with a provided root window."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)

        assert viewer._root is mock_tk_root
        assert viewer._run_service is mock_run_service
        assert viewer._attempt_service is mock_attempt_service


class TestGetAttemptCount:
    """Tests for WorkflowRunsGUIViewer._get_attempt_count()"""

    def test_get_attempt_count_with_multiple_attempts(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test getting attempt count for a run with 3 attempts."""
        attempts = [MagicMock(), MagicMock(), MagicMock()]
        mock_attempt_service.filter_by_run_id.return_value = attempts

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        count = viewer._get_attempt_count("run-123")

        assert count == 3
        mock_attempt_service.filter_by_run_id.assert_called_once_with("run-123")

    def test_get_attempt_count_with_zero_attempts(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test getting attempt count for a run with no attempts."""
        mock_attempt_service.filter_by_run_id.return_value = []

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        count = viewer._get_attempt_count("run-456")

        assert count == 0
        mock_attempt_service.filter_by_run_id.assert_called_once_with("run-456")

    def test_get_attempt_count_with_single_attempt(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test getting attempt count for a run with 1 attempt."""
        attempts = [MagicMock()]
        mock_attempt_service.filter_by_run_id.return_value = attempts

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        count = viewer._get_attempt_count("run-789")

        assert count == 1


class TestFormatDuration:
    """Tests for WorkflowRunsGUIViewer._format_duration()"""

    def test_format_duration_with_decimal_places(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting duration 123.456 → "123.46s"."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_duration(123.456)

        assert result == "123.46s"

    def test_format_duration_zero_seconds(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting zero duration."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_duration(0.0)

        assert result == "0.00s"

    def test_format_duration_whole_number(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting whole number duration."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_duration(42.0)

        assert result == "42.00s"

    def test_format_duration_very_small(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting very small duration."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_duration(0.001)

        assert result == "0.00s"

    def test_format_duration_large_number(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting large duration."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_duration(3661.234)

        assert result == "3661.23s"

    @pytest.mark.parametrize("seconds,expected", [
        (1.234, "1.23s"),
        (10.005, "10.01s"),
        (99.999, "100.00s"),
    ])
    def test_format_duration_parametrized(self, mock_run_service, mock_attempt_service, mock_tk_root, seconds, expected):
        """Test formatting various durations."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_duration(seconds)

        assert result == expected


class TestFormatConclusion:
    """Tests for WorkflowRunsGUIViewer._format_conclusion()"""

    def test_format_conclusion_with_success(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting SUCCESS conclusion."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_conclusion(WorkflowConclusion.SUCCESS)

        assert result == "success"

    def test_format_conclusion_with_failure(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting FAILURE conclusion."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_conclusion(WorkflowConclusion.FAILURE)

        assert result == "failure"

    def test_format_conclusion_with_cancelled(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting CANCELLED conclusion."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_conclusion(WorkflowConclusion.CANCELLED)

        assert result == "cancelled"

    def test_format_conclusion_none(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting None conclusion returns dash."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_conclusion(None)

        assert result == "—"

    @pytest.mark.parametrize("conclusion,expected", [
        (WorkflowConclusion.TIMED_OUT, "timed_out"),
        (WorkflowConclusion.ACTION_REQUIRED, "action_required"),
        (WorkflowConclusion.SKIPPED, "skipped"),
        (WorkflowConclusion.NEUTRAL, "neutral"),
        (WorkflowConclusion.STALE, "stale"),
    ])
    def test_format_conclusion_all_types(self, mock_run_service, mock_attempt_service, mock_tk_root, conclusion, expected):
        """Test formatting all conclusion types."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_conclusion(conclusion)

        assert result == expected


class TestFormatTimestamp:
    """Tests for WorkflowRunsGUIViewer._format_timestamp()"""

    def test_format_timestamp_iso_format(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting datetime to ISO format."""
        dt = datetime(2026, 5, 3, 10, 30, 45, 123456)
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_timestamp(dt)

        assert result == "2026-05-03T10:30:45.123456"

    def test_format_timestamp_midnight(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting datetime at midnight."""
        dt = datetime(2026, 1, 1, 0, 0, 0)
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_timestamp(dt)

        assert result == "2026-01-01T00:00:00"

    def test_format_timestamp_end_of_day(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test formatting datetime at end of day."""
        dt = datetime(2026, 12, 31, 23, 59, 59)
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        result = viewer._format_timestamp(dt)

        assert result == "2026-12-31T23:59:59"


class TestPopulateTreeview:
    """Tests for WorkflowRunsGUIViewer._populate_treeview()"""

    def test_populate_treeview_with_two_runs(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test populating treeview with 2 runs."""
        mock_attempt_service.filter_by_run_id.return_value = []

        run1 = _make_run("run-1234567890abcdef", duration_seconds=10.0)
        run2 = _make_run("run-2234567890abcdef", duration_seconds=20.0)
        runs = [run1, run2]

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        # Mock treeview
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []
        viewer._treeview.delete = MagicMock()
        viewer._treeview.insert = MagicMock()

        viewer._populate_treeview(runs)

        # Verify current_runs was set
        assert viewer._current_runs == runs
        # Verify insert was called twice
        assert viewer._treeview.insert.call_count == 2

    def test_populate_treeview_with_empty_list(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test populating treeview with empty list."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []

        viewer._populate_treeview([])

        assert viewer._current_runs == []
        # insert should not be called for empty list
        assert viewer._treeview.insert.call_count == 0

    def test_populate_treeview_clears_existing_items(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that populate treeview clears existing items."""
        mock_attempt_service.filter_by_run_id.return_value = []

        run1 = _make_run("run-1111111111111111")
        run2 = _make_run("run-2222222222222222")

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = ["item1"]
        viewer._treeview.delete = MagicMock()
        viewer._treeview.insert = MagicMock()

        # First populate
        viewer._populate_treeview([run1])
        first_call_count = viewer._treeview.delete.call_count

        # Second populate should clear first
        viewer._treeview.get_children.return_value = ["item2"]
        viewer._populate_treeview([run2])

        # delete should have been called twice (once per populate)
        assert viewer._treeview.delete.call_count > first_call_count

    def test_populate_treeview_when_treeview_is_none(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that populate returns early if treeview is None."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = None

        run = _make_run()
        viewer._populate_treeview([run])

        # Should not crash, just return
        assert viewer._current_runs == []


class TestFailedRunsTag:
    """Tests for failed runs highlighting."""

    def test_failed_runs_receive_failed_row_tag(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that failed runs get the failed_run tag."""
        mock_attempt_service.filter_by_run_id.return_value = []

        # Create a successful and a failed run
        success_run = _make_run(
            "run-success1234567",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS
        )
        failed_run = _make_run(
            "run-failed1234567",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE
        )

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []

        viewer._populate_treeview([success_run, failed_run])

        # Check that insert was called with appropriate tags
        calls = viewer._treeview.insert.call_args_list
        assert len(calls) == 2

        # Check first call (success) - tags should be empty tuple
        first_call_tags = calls[0][1]["tags"]
        assert first_call_tags == ()

        # Check second call (failed) - tags should include "failed_run"
        second_call_tags = calls[1][1]["tags"]
        assert "failed_run" in second_call_tags

    def test_timed_out_runs_receive_failed_row_tag(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that timed-out runs get the failed_run tag."""
        mock_attempt_service.filter_by_run_id.return_value = []

        timed_out_run = _make_run(
            "run-timeout1234567",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.TIMED_OUT
        )

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []

        viewer._populate_treeview([timed_out_run])

        # Check that insert was called with failed_run tag
        calls = viewer._treeview.insert.call_args_list
        assert len(calls) == 1
        tags = calls[0][1]["tags"]
        assert "failed_run" in tags


class TestApplyFilters:
    """Tests for WorkflowRunsGUIViewer._apply_filters()"""

    def test_apply_filters_with_status_only(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test filtering by status only."""
        runs = [
            _make_run("run-1111", status=WorkflowStatus.COMPLETED),
            _make_run("run-2222", status=WorkflowStatus.QUEUED),
            _make_run("run-3333", status=WorkflowStatus.COMPLETED),
        ]
        mock_run_service.list_runs.return_value = runs
        mock_attempt_service.filter_by_run_id.return_value = []

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []
        viewer._status_filter = MagicMock()
        viewer._status_filter.get.return_value = "completed"
        viewer._conclusion_filter = MagicMock()
        viewer._conclusion_filter.get.return_value = "All"

        with patch.object(viewer, '_populate_treeview') as mock_populate:
            viewer._apply_filters()
            mock_populate.assert_called_once()

    def test_apply_filters_with_conclusion_only(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test filtering by conclusion only."""
        runs = [
            _make_run("run-1111", conclusion=WorkflowConclusion.SUCCESS),
            _make_run("run-2222", conclusion=WorkflowConclusion.FAILURE),
            _make_run("run-3333", conclusion=WorkflowConclusion.SUCCESS),
        ]
        mock_run_service.list_runs.return_value = runs
        mock_attempt_service.filter_by_run_id.return_value = []

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []
        viewer._status_filter = MagicMock()
        viewer._status_filter.get.return_value = "All"
        viewer._conclusion_filter = MagicMock()
        viewer._conclusion_filter.get.return_value = "success"

        with patch.object(viewer, '_populate_treeview') as mock_populate:
            viewer._apply_filters()
            mock_populate.assert_called_once()

    def test_apply_filters_with_both_status_and_conclusion(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test filtering by both status and conclusion."""
        runs = [
            _make_run("run-1111", status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.SUCCESS),
            _make_run("run-2222", status=WorkflowStatus.COMPLETED, conclusion=WorkflowConclusion.FAILURE),
            _make_run("run-3333", status=WorkflowStatus.QUEUED, conclusion=WorkflowConclusion.SUCCESS),
        ]
        mock_run_service.list_runs.return_value = runs
        mock_attempt_service.filter_by_run_id.return_value = []

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []
        viewer._status_filter = MagicMock()
        viewer._status_filter.get.return_value = "completed"
        viewer._conclusion_filter = MagicMock()
        viewer._conclusion_filter.get.return_value = "success"

        with patch.object(viewer, '_populate_treeview') as mock_populate:
            viewer._apply_filters()
            mock_populate.assert_called_once()

    def test_apply_filters_returns_early_if_filters_none(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that apply filters returns early if filters are None."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._status_filter = None
        viewer._conclusion_filter = None

        # Should not crash
        viewer._apply_filters()


class TestClearFilters:
    """Tests for WorkflowRunsGUIViewer._clear_filters()"""

    def test_clear_filters_resets_dropdowns(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that clearing filters resets dropdowns to 'All'."""
        mock_run_service.list_runs.return_value = []
        mock_attempt_service.filter_by_run_id.return_value = []

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []
        viewer._status_filter = MagicMock()
        viewer._status_filter.set = MagicMock()
        viewer._conclusion_filter = MagicMock()
        viewer._conclusion_filter.set = MagicMock()

        viewer._clear_filters()

        viewer._status_filter.set.assert_called_once_with("All")
        viewer._conclusion_filter.set.assert_called_once_with("All")

    def test_clear_filters_repopulates_treeview(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that clearing filters repopulates treeview with all runs."""
        runs = [
            _make_run("run-1111"),
            _make_run("run-2222"),
        ]
        mock_run_service.list_runs.return_value = runs
        mock_attempt_service.filter_by_run_id.return_value = []

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = MagicMock()
        viewer._treeview.get_children.return_value = []
        viewer._status_filter = MagicMock()
        viewer._conclusion_filter = MagicMock()

        with patch.object(viewer, '_populate_treeview') as mock_populate:
            viewer._clear_filters()
            mock_populate.assert_called_once_with(runs)


class TestOnFilterChanged:
    """Tests for WorkflowRunsGUIViewer._on_filter_changed()"""

    def test_on_filter_changed_calls_apply_filters(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that filter changed callback calls apply_filters."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)

        with patch.object(viewer, '_apply_filters') as mock_apply:
            viewer._on_filter_changed()
            mock_apply.assert_called_once()

    def test_on_filter_changed_accepts_event_parameter(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that filter changed accepts event parameter."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        event = MagicMock()

        with patch.object(viewer, '_apply_filters'):
            # Should not raise
            viewer._on_filter_changed(event)


class TestRun:
    """Tests for WorkflowRunsGUIViewer.run()"""

    def test_run_creates_window_and_populates_data(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that run() sets up window and starts GUI."""
        runs = [_make_run("run-1111")]
        mock_run_service.list_runs.return_value = runs
        mock_attempt_service.filter_by_run_id.return_value = []

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)

        with patch.object(viewer, '_setup_window') as mock_setup, \
             patch.object(viewer, '_create_widgets') as mock_create, \
             patch.object(viewer, '_populate_treeview') as mock_populate:

            viewer.run()

            mock_setup.assert_called_once()
            mock_create.assert_called_once()
            mock_populate.assert_called_once_with(runs)
            mock_tk_root.mainloop.assert_called_once()


class TestHighlightFailedRows:
    """Tests for WorkflowRunsGUIViewer._highlight_failed_rows()"""

    def test_highlight_failed_rows_marks_failed_runs(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test that highlight failed rows marks failed runs."""
        mock_attempt_service.filter_by_run_id.return_value = []

        success_run = _make_run(
            "run-success1111111",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS
        )
        failed_run = _make_run(
            "run-failed1111111",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE
        )

        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._current_runs = [success_run, failed_run]

        # Mock treeview
        viewer._treeview = MagicMock()
        item1 = "item1"
        item2 = "item2"
        viewer._treeview.get_children.return_value = [item1, item2]

        # Mock item method to return values tuple
        def item_side_effect(x, key=None, tags=None):
            if key == "values":
                if x == item1:
                    return (success_run.id[:8],)
                else:
                    return (failed_run.id[:8],)
            return {}

        viewer._treeview.item.side_effect = item_side_effect

        viewer._highlight_failed_rows()

        # Verify item() was called for both items
        assert viewer._treeview.item.call_count >= 2

    def test_highlight_failed_rows_when_treeview_none(self, mock_run_service, mock_attempt_service, mock_tk_root):
        """Test highlight failed rows handles None treeview."""
        viewer = WorkflowRunsGUIViewer(mock_run_service, mock_attempt_service, root=mock_tk_root)
        viewer._treeview = None

        # Should not crash
        viewer._highlight_failed_rows()


class TestRunGUIEntryPoint:
    """Tests for run_gui() entry point."""

    def test_run_gui_creates_viewer_and_calls_run(self, mock_run_service, mock_attempt_service):
        """Test that run_gui entry point creates viewer and calls run."""
        with patch('src.gui.gui_viewer.WorkflowRunsGUIViewer') as mock_viewer_class:
            mock_viewer_instance = MagicMock()
            mock_viewer_class.return_value = mock_viewer_instance

            run_gui(mock_run_service, mock_attempt_service)

            mock_viewer_class.assert_called_once_with(mock_run_service, mock_attempt_service)
            mock_viewer_instance.run.assert_called_once()

    def test_run_gui_passes_services_to_viewer(self, mock_run_service, mock_attempt_service):
        """Test that run_gui passes services correctly."""
        with patch('src.gui.gui_viewer.WorkflowRunsGUIViewer') as mock_viewer_class:
            mock_viewer_instance = MagicMock()
            mock_viewer_class.return_value = mock_viewer_instance

            run_gui(mock_run_service, mock_attempt_service)

            call_args = mock_viewer_class.call_args
            assert call_args[0][0] is mock_run_service
            assert call_args[0][1] is mock_attempt_service
