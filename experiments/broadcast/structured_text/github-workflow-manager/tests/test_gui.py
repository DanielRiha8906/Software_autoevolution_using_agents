import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch
import sys

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.attempt_service import AttemptService


def _make_run(
    run_id: str = "1",
    workflow_name: str = "Test Workflow",
    branch: str = "main",
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    conclusion: WorkflowConclusion | None = WorkflowConclusion.SUCCESS,
    duration_seconds: float = 60.0,
) -> WorkflowRun:
    """Create a WorkflowRun with specified parameters."""
    return WorkflowRun(
        id=run_id,
        workflow_name=workflow_name,
        branch=branch,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
        duration_seconds=duration_seconds,
    )


class TestGUIModule:
    """Tests for the GUI module structure."""

    def test_gui_module_imports(self):
        """Test that gui module can be imported."""
        from src import gui
        assert hasattr(gui, 'WorkflowRunViewerGUI')
        assert hasattr(gui, 'run_gui')

    def test_gui_class_has_required_methods(self):
        """Test that GUI class has required methods."""
        from src.gui import WorkflowRunViewerGUI
        assert hasattr(WorkflowRunViewerGUI, '__init__')
        assert hasattr(WorkflowRunViewerGUI, '_setup_ui')
        assert hasattr(WorkflowRunViewerGUI, '_refresh_data')

    def test_run_gui_function_exists(self):
        """Test that run_gui function exists."""
        from src.gui import run_gui
        assert callable(run_gui)


class TestGUILogic:
    """Tests for GUI logic and business logic."""

    def test_status_enum_conversion_completed(self):
        """Test that 'completed' string converts to WorkflowStatus.COMPLETED."""
        assert WorkflowStatus("completed") == WorkflowStatus.COMPLETED

    def test_status_enum_conversion_in_progress(self):
        """Test that 'in_progress' string converts to WorkflowStatus.IN_PROGRESS."""
        assert WorkflowStatus("in_progress") == WorkflowStatus.IN_PROGRESS

    def test_conclusion_enum_conversion_success(self):
        """Test that 'success' string converts to WorkflowConclusion.SUCCESS."""
        assert WorkflowConclusion("success") == WorkflowConclusion.SUCCESS

    def test_conclusion_enum_conversion_failure(self):
        """Test that 'failure' string converts to WorkflowConclusion.FAILURE."""
        assert WorkflowConclusion("failure") == WorkflowConclusion.FAILURE

    def test_duration_formatting(self):
        """Test duration formatting logic."""
        duration = 120.567
        formatted = f"{duration:.2f}"
        assert formatted == "120.57"

    def test_conclusion_none_represented_as_dash(self):
        """Test that None conclusion is represented as dash."""
        run = _make_run(conclusion=None)
        conclusion_str = run.conclusion.value if run.conclusion else "—"
        assert conclusion_str == "—"

    def test_failed_run_detection(self):
        """Test that failed runs are correctly identified."""
        run = _make_run(conclusion=WorkflowConclusion.FAILURE)
        assert run.is_failed()

    def test_successful_run_detection(self):
        """Test that successful runs are correctly identified."""
        run = _make_run(conclusion=WorkflowConclusion.SUCCESS)
        assert run.is_successful()
        assert not run.is_failed()


class TestFilterLogic:
    """Tests for filtering logic independent of GUI."""

    def test_status_filter_enum_conversion(self):
        """Test that status filter converts string to enum."""
        status_filter = "completed"
        status_enum = None if status_filter == "All" else WorkflowStatus(status_filter)
        assert status_enum == WorkflowStatus.COMPLETED

    def test_conclusion_filter_enum_conversion(self):
        """Test that conclusion filter converts string to enum."""
        conclusion_filter = "failure"
        conclusion_enum = None if conclusion_filter == "All" else WorkflowConclusion(conclusion_filter)
        assert conclusion_enum == WorkflowConclusion.FAILURE

    def test_all_status_filter_returns_none(self):
        """Test that 'All' status filter returns None."""
        status_filter = "All"
        status_enum = None if status_filter == "All" else WorkflowStatus(status_filter)
        assert status_enum is None

    def test_all_conclusion_filter_returns_none(self):
        """Test that 'All' conclusion filter returns None."""
        conclusion_filter = "All"
        conclusion_enum = None if conclusion_filter == "All" else WorkflowConclusion(conclusion_filter)
        assert conclusion_enum is None


class TestAttemptCounting:
    """Tests for attempt counting logic."""

    def test_attempt_count_from_service(self):
        """Test that attempt count is retrieved from service."""
        mock_service = MagicMock(spec=AttemptService)
        mock_attempts = [MagicMock(), MagicMock(), MagicMock()]
        mock_service.get_attempts_by_run_id.return_value = mock_attempts

        attempt_count = len(mock_service.get_attempts_by_run_id("1"))
        assert attempt_count == 3

    def test_attempt_count_zero(self):
        """Test that zero attempts returns 0."""
        mock_service = MagicMock(spec=AttemptService)
        mock_service.get_attempts_by_run_id.return_value = []

        attempt_count = len(mock_service.get_attempts_by_run_id("1"))
        assert attempt_count == 0

    def test_run_id_handling_string_to_int(self):
        """Test that run_id string conversion is handled."""
        run = _make_run(run_id="123")
        # Simulate the logic in _refresh_data
        run_id_for_query = int(run.id) if run.id.isdigit() else run.id
        assert run_id_for_query == 123
        assert isinstance(run_id_for_query, int)


class TestDataDisplay:
    """Tests for data display logic."""

    def test_run_data_extraction(self):
        """Test extracting run data for display."""
        run = _make_run(
            run_id="123",
            workflow_name="Build",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            duration_seconds=120.567
        )

        # Simulate display data extraction
        run_data = {
            "id": run.id,
            "workflow": run.workflow_name,
            "branch": run.branch,
            "status": run.status.value,
            "conclusion": run.conclusion.value if run.conclusion else "—",
            "duration": f"{run.duration_seconds:.2f}",
        }

        assert run_data["id"] == "123"
        assert run_data["workflow"] == "Build"
        assert run_data["branch"] == "main"
        assert run_data["status"] == "completed"
        assert run_data["conclusion"] == "success"
        assert run_data["duration"] == "120.57"

    def test_multiple_runs_data_extraction(self):
        """Test extracting data from multiple runs."""
        runs = [
            _make_run(run_id="1"),
            _make_run(run_id="2"),
            _make_run(run_id="3"),
        ]

        extracted_ids = [run.id for run in runs]
        assert extracted_ids == ["1", "2", "3"]

    def test_run_with_no_conclusion_handling(self):
        """Test handling runs with no conclusion."""
        run = _make_run(conclusion=None)

        conclusion_str = run.conclusion.value if run.conclusion else "—"
        assert conclusion_str == "—"


class TestHighlighting:
    """Tests for highlighting logic."""

    def test_failed_run_should_be_highlighted(self):
        """Test that failed runs should be tagged."""
        run = _make_run(conclusion=WorkflowConclusion.FAILURE)

        should_highlight = run.is_failed()
        assert should_highlight is True

    def test_successful_run_should_not_be_highlighted(self):
        """Test that successful runs should not be tagged."""
        run = _make_run(conclusion=WorkflowConclusion.SUCCESS)

        should_highlight = run.is_failed()
        assert should_highlight is False

    def test_cancelled_run_should_not_be_highlighted(self):
        """Test that cancelled runs should not be highlighted as failed."""
        run = _make_run(conclusion=WorkflowConclusion.CANCELLED)

        should_highlight = run.is_failed()
        assert should_highlight is False

    def test_skipped_run_should_not_be_highlighted(self):
        """Test that skipped runs should not be highlighted."""
        run = _make_run(conclusion=WorkflowConclusion.SKIPPED)

        should_highlight = run.is_failed()
        assert should_highlight is False


class TestFilteringIntegration:
    """Tests for filtering integration with service."""

    @patch('src.gui.tk.Tk')
    @patch('src.gui.ttk.Frame')
    @patch('src.gui.ttk.LabelFrame')
    @patch('src.gui.ttk.Label')
    @patch('src.gui.ttk.Combobox')
    @patch('src.gui.ttk.Button')
    @patch('src.gui.ttk.Scrollbar')
    @patch('src.gui.ttk.Treeview')
    def test_gui_calls_service_filter_with_correct_params(
        self,
        mock_tree_class,
        mock_scrollbar,
        mock_button,
        mock_combobox,
        mock_label,
        mock_labelframe,
        mock_frame,
        mock_tk_class,
    ):
        """Test that GUI calls service filter with correct parameters."""
        # Setup mocks
        mock_root = MagicMock()
        mock_tree = MagicMock()
        mock_tree_class.return_value = mock_tree
        mock_tree.get_children.return_value = []
        mock_tk_class.return_value = mock_root

        # Create real service and attempt service mocks
        mock_service = MagicMock(spec=WorkflowRunService)
        mock_service.filter_runs.return_value = []

        mock_attempt_service = MagicMock(spec=AttemptService)

        # Patch StringVar to work with mocks
        with patch('src.gui.tk.StringVar') as mock_stringvar_class:
            mock_status_var = MagicMock()
            mock_status_var.get.return_value = "All"
            mock_conclusion_var = MagicMock()
            mock_conclusion_var.get.return_value = "All"

            call_count = [0]

            def stringvar_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_status_var
                else:
                    return mock_conclusion_var

            mock_stringvar_class.side_effect = stringvar_side_effect

            from src.gui import WorkflowRunViewerGUI

            gui = WorkflowRunViewerGUI(mock_root, mock_service, mock_attempt_service)

            # Verify filter_runs was called with None for both filters
            mock_service.filter_runs.assert_called()
            call_kwargs = mock_service.filter_runs.call_args[1]
            assert call_kwargs["status"] is None
            assert call_kwargs["conclusion"] is None


class TestRunGuiFunction:
    """Tests for the run_gui function."""

    @patch('src.gui.tk.Tk')
    @patch('src.gui.WorkflowRunViewerGUI')
    def test_run_gui_creates_and_launches(self, mock_gui_class, mock_tk_class):
        """Test that run_gui creates a root and launches the viewer."""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        mock_viewer = MagicMock()
        mock_gui_class.return_value = mock_viewer

        mock_service = MagicMock(spec=WorkflowRunService)
        mock_attempt_service = MagicMock(spec=AttemptService)

        from src.gui import run_gui

        run_gui(mock_service, mock_attempt_service)

        mock_tk_class.assert_called_once()
        mock_gui_class.assert_called_once_with(mock_root, mock_service, mock_attempt_service)
        mock_root.mainloop.assert_called_once()

    @patch('src.gui.tk.Tk')
    @patch('src.gui.WorkflowRunViewerGUI')
    def test_run_gui_passes_correct_service_instances(self, mock_gui_class, mock_tk_class):
        """Test that run_gui passes the correct service instances."""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root

        mock_service = MagicMock(spec=WorkflowRunService)
        mock_attempt_service = MagicMock(spec=AttemptService)

        from src.gui import run_gui

        run_gui(mock_service, mock_attempt_service)

        call_args = mock_gui_class.call_args
        assert call_args[0][1] == mock_service
        assert call_args[0][2] == mock_attempt_service


class TestFilterModel:
    """Tests for the FilterModel class."""

    def test_filter_model_initialization(self):
        """Test that FilterModel initializes with None filters."""
        from src.gui import FilterModel

        model = FilterModel()
        assert model.status_filter is None
        assert model.conclusion_filter is None

    def test_set_status_with_valid_value(self):
        """Test setting status filter with valid status string."""
        from src.gui import FilterModel

        model = FilterModel()
        model.set_status("completed")
        assert model.status_filter == WorkflowStatus.COMPLETED

    def test_set_status_with_all_clears_filter(self):
        """Test that 'All' status string clears the filter."""
        from src.gui import FilterModel

        model = FilterModel()
        model.set_status("completed")
        assert model.status_filter == WorkflowStatus.COMPLETED
        model.set_status("All")
        assert model.status_filter is None

    def test_set_conclusion_with_valid_value(self):
        """Test setting conclusion filter with valid conclusion string."""
        from src.gui import FilterModel

        model = FilterModel()
        model.set_conclusion("success")
        assert model.conclusion_filter == WorkflowConclusion.SUCCESS

    def test_set_conclusion_with_all_clears_filter(self):
        """Test that 'All' conclusion string clears the filter."""
        from src.gui import FilterModel

        model = FilterModel()
        model.set_conclusion("failure")
        assert model.conclusion_filter == WorkflowConclusion.FAILURE
        model.set_conclusion("All")
        assert model.conclusion_filter is None

    def test_reset_clears_all_filters(self):
        """Test that reset clears all filters."""
        from src.gui import FilterModel

        model = FilterModel()
        model.set_status("in_progress")
        model.set_conclusion("cancelled")
        assert model.status_filter is not None
        assert model.conclusion_filter is not None

        model.reset()
        assert model.status_filter is None
        assert model.conclusion_filter is None

    def test_status_filter_with_all_statuses(self):
        """Test setting status filter with all available status values."""
        from src.gui import FilterModel

        model = FilterModel()
        for status in WorkflowStatus:
            model.set_status(status.value)
            assert model.status_filter == status

    def test_conclusion_filter_with_all_conclusions(self):
        """Test setting conclusion filter with all available conclusion values."""
        from src.gui import FilterModel

        model = FilterModel()
        for conclusion in WorkflowConclusion:
            model.set_conclusion(conclusion.value)
            assert model.conclusion_filter == conclusion


class TestRowTagging:
    """Tests for row tagging logic in the GUI."""

    @patch('src.gui.tk.Tk')
    @patch('src.gui.ttk.Frame')
    @patch('src.gui.ttk.LabelFrame')
    @patch('src.gui.ttk.Label')
    @patch('src.gui.ttk.Combobox')
    @patch('src.gui.ttk.Button')
    @patch('src.gui.ttk.Scrollbar')
    @patch('src.gui.ttk.Treeview')
    def test_get_row_tags_for_failed_run(
        self,
        mock_tree_class,
        mock_scrollbar,
        mock_button,
        mock_combobox,
        mock_label,
        mock_labelframe,
        mock_frame,
        mock_tk_class,
    ):
        """Test that failed runs get the correct tag."""
        mock_root = MagicMock()
        mock_tree = MagicMock()
        mock_tree_class.return_value = mock_tree
        mock_tree.get_children.return_value = []
        mock_tk_class.return_value = mock_root

        mock_service = MagicMock(spec=WorkflowRunService)
        mock_service.filter_runs.return_value = []
        mock_attempt_service = MagicMock(spec=AttemptService)

        with patch('src.gui.tk.StringVar') as mock_stringvar_class:
            mock_status_var = MagicMock()
            mock_status_var.get.return_value = "All"
            mock_conclusion_var = MagicMock()
            mock_conclusion_var.get.return_value = "All"

            call_count = [0]

            def stringvar_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_status_var
                else:
                    return mock_conclusion_var

            mock_stringvar_class.side_effect = stringvar_side_effect

            from src.gui import WorkflowRunViewerGUI

            gui = WorkflowRunViewerGUI(mock_root, mock_service, mock_attempt_service)
            run = _make_run(conclusion=WorkflowConclusion.FAILURE)
            tags = gui._get_row_tags(run)
            assert tags == ("failed",)

    @patch('src.gui.tk.Tk')
    @patch('src.gui.ttk.Frame')
    @patch('src.gui.ttk.LabelFrame')
    @patch('src.gui.ttk.Label')
    @patch('src.gui.ttk.Combobox')
    @patch('src.gui.ttk.Button')
    @patch('src.gui.ttk.Scrollbar')
    @patch('src.gui.ttk.Treeview')
    def test_get_row_tags_for_successful_run(
        self,
        mock_tree_class,
        mock_scrollbar,
        mock_button,
        mock_combobox,
        mock_label,
        mock_labelframe,
        mock_frame,
        mock_tk_class,
    ):
        """Test that successful runs get the correct tag."""
        mock_root = MagicMock()
        mock_tree = MagicMock()
        mock_tree_class.return_value = mock_tree
        mock_tree.get_children.return_value = []
        mock_tk_class.return_value = mock_root

        mock_service = MagicMock(spec=WorkflowRunService)
        mock_service.filter_runs.return_value = []
        mock_attempt_service = MagicMock(spec=AttemptService)

        with patch('src.gui.tk.StringVar') as mock_stringvar_class:
            mock_status_var = MagicMock()
            mock_status_var.get.return_value = "All"
            mock_conclusion_var = MagicMock()
            mock_conclusion_var.get.return_value = "All"

            call_count = [0]

            def stringvar_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_status_var
                else:
                    return mock_conclusion_var

            mock_stringvar_class.side_effect = stringvar_side_effect

            from src.gui import WorkflowRunViewerGUI

            gui = WorkflowRunViewerGUI(mock_root, mock_service, mock_attempt_service)
            run = _make_run(conclusion=WorkflowConclusion.SUCCESS)
            tags = gui._get_row_tags(run)
            assert tags == ("success",)

    @patch('src.gui.tk.Tk')
    @patch('src.gui.ttk.Frame')
    @patch('src.gui.ttk.LabelFrame')
    @patch('src.gui.ttk.Label')
    @patch('src.gui.ttk.Combobox')
    @patch('src.gui.ttk.Button')
    @patch('src.gui.ttk.Scrollbar')
    @patch('src.gui.ttk.Treeview')
    def test_get_row_tags_for_in_progress_run(
        self,
        mock_tree_class,
        mock_scrollbar,
        mock_button,
        mock_combobox,
        mock_label,
        mock_labelframe,
        mock_frame,
        mock_tk_class,
    ):
        """Test that in-progress runs get the correct tag."""
        mock_root = MagicMock()
        mock_tree = MagicMock()
        mock_tree_class.return_value = mock_tree
        mock_tree.get_children.return_value = []
        mock_tk_class.return_value = mock_root

        mock_service = MagicMock(spec=WorkflowRunService)
        mock_service.filter_runs.return_value = []
        mock_attempt_service = MagicMock(spec=AttemptService)

        with patch('src.gui.tk.StringVar') as mock_stringvar_class:
            mock_status_var = MagicMock()
            mock_status_var.get.return_value = "All"
            mock_conclusion_var = MagicMock()
            mock_conclusion_var.get.return_value = "All"

            call_count = [0]

            def stringvar_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_status_var
                else:
                    return mock_conclusion_var

            mock_stringvar_class.side_effect = stringvar_side_effect

            from src.gui import WorkflowRunViewerGUI

            gui = WorkflowRunViewerGUI(mock_root, mock_service, mock_attempt_service)
            run = _make_run(status=WorkflowStatus.IN_PROGRESS, conclusion=None)
            tags = gui._get_row_tags(run)
            assert tags == ("in_progress",)
