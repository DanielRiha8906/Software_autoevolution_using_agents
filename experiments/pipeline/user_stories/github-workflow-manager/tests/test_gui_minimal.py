"""
Minimal integration tests for GUI components.

Tests the core functionality of:
- WorkflowRunMainWindow initialization and service interactions
- Edit dialog integration with service
- Delete integration with service
- Filter integration with service
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService
from src.services.workflow_run_attempt_service import WorkflowRunAttemptService


@pytest.fixture
def sample_runs():
    return [
        WorkflowRun(
            id="1",
            workflow_name="build",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
            run_number=1,
            commit_sha="abc123",
            duration_seconds=30.5,
        ),
        WorkflowRun(
            id="2",
            workflow_name="test",
            branch="develop",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.FAILURE,
            created_at=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 2, 10, 30, 0, tzinfo=timezone.utc),
            run_number=2,
            commit_sha="def456",
            duration_seconds=45.0,
        ),
    ]


@pytest.fixture
def mock_service(sample_runs):
    service = Mock(spec=WorkflowRunService)
    service.list_runs.return_value = sample_runs
    service.query.return_value = sample_runs
    service.get_run_detail.side_effect = lambda run_id: next(
        (r for r in sample_runs if r.id == run_id), None
    )
    service.replace_run.return_value = None
    service.delete_run.return_value = True
    service._storage = Mock()
    return service


@pytest.fixture
def mock_attempt_service():
    service = Mock(spec=WorkflowRunAttemptService)
    service.get_attempts_for_run.return_value = []
    service._storage = Mock()
    return service


@pytest.fixture
def mock_tree():
    tree = Mock()
    tree.get_children.return_value = []
    tree.insert = Mock()
    tree.delete = Mock()
    tree.selection = Mock(return_value=[])
    # item() returns a dict with 'values' key, where values is a tuple
    def mock_item(item_id, key):
        if key == "values":
            return ('1', 'test', 'main', 'completed', 'success', '30.5')
        return {'values': ('1', 'test', 'main', 'completed', 'success', '30.5')}
    tree.item = Mock(side_effect=mock_item)
    tree.tag_configure = Mock()
    tree.column = Mock()
    tree.heading = Mock()
    tree.pack = Mock()
    tree.yview = Mock()
    return tree


def _create_window(mock_root, mock_service, mock_attempt_service, mock_tree):
    """Helper to create a WorkflowRunMainWindow with all tkinter mocked."""
    with patch('src.gui.workflow_gui.ttk.Frame', return_value=Mock(pack=Mock())):
        with patch('src.gui.workflow_gui.ttk.Label', return_value=Mock(pack=Mock(), cget=Mock(return_value=""))):
            with patch('src.gui.workflow_gui.ttk.LabelFrame', return_value=Mock(pack=Mock())):
                with patch('src.gui.workflow_gui.ttk.Combobox', return_value=Mock(pack=Mock())):
                    with patch('src.gui.workflow_gui.ttk.Button', return_value=Mock(pack=Mock())):
                        with patch('src.gui.workflow_gui.ttk.Treeview', return_value=mock_tree):
                            with patch('src.gui.workflow_gui.ttk.Scrollbar', return_value=Mock(pack=Mock(), config=Mock())):
                                with patch('src.gui.workflow_gui.tk.StringVar'):
                                    from src.gui.workflow_gui import WorkflowRunMainWindow
                                    return WorkflowRunMainWindow(mock_root, mock_service, mock_attempt_service)


class TestWindowInitialization:
    """Test window initialization and service setup."""

    def test_window_initializes_with_services(self, mock_service, mock_attempt_service, mock_tree):
        """Test that window correctly stores service references."""
        mock_root = Mock()

        window = _create_window(mock_root, mock_service, mock_attempt_service, mock_tree)

        assert window.service is mock_service
        assert window.attempt_service is mock_attempt_service


class TestAttemptCountHandling:
    """Test that attempt counts handle numeric IDs correctly."""

    def test_get_attempt_count_with_numeric_id(self, mock_service, mock_attempt_service, mock_tree):
        """Test attempt count retrieval with numeric ID."""
        mock_root = Mock()
        window = _create_window(mock_root, mock_service, mock_attempt_service, mock_tree)

        run = WorkflowRun(
            id="1",
            workflow_name="test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha=None,
            duration_seconds=0.0,
        )

        count = window._get_attempt_count(run)

        assert count == 0
        mock_attempt_service.get_attempts_for_run.assert_called_with(1)

    def test_get_attempt_count_with_non_numeric_id(self, mock_service, mock_attempt_service, mock_tree, sample_runs):
        """Test attempt count returns 0 for non-numeric IDs."""
        mock_root = Mock()
        window = _create_window(mock_root, mock_service, mock_attempt_service, mock_tree)

        run = WorkflowRun(
            id="uuid-123-abc",
            workflow_name="test",
            branch="main",
            status=WorkflowStatus.COMPLETED,
            conclusion=WorkflowConclusion.SUCCESS,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            run_number=1,
            commit_sha=None,
            duration_seconds=0.0,
        )

        # Reset the mock to clear any calls made during initialization
        mock_attempt_service.get_attempts_for_run.reset_mock()

        count = window._get_attempt_count(run)

        assert count == 0
        # Should not call the service for non-numeric IDs
        mock_attempt_service.get_attempts_for_run.assert_not_called()


class TestFilteringServiceCalls:
    """Test that filtering properly calls the service with correct parameters."""

    def test_filter_by_status(self, mock_service, mock_attempt_service, mock_tree, sample_runs):
        """Test filtering by status calls service.query with correct params."""
        mock_root = Mock()
        mock_service.query.return_value = [sample_runs[0]]
        mock_tree.get_children.return_value = []

        window = _create_window(mock_root, mock_service, mock_attempt_service, mock_tree)
        window._status_var = Mock(get=Mock(return_value="completed"))
        window._conclusion_var = Mock(get=Mock(return_value="(All)"))

        window._apply_filters()

        mock_service.query.assert_called_with(
            status=WorkflowStatus.COMPLETED,
            conclusion=None,
        )

    def test_filter_by_conclusion(self, mock_service, mock_attempt_service, mock_tree, sample_runs):
        """Test filtering by conclusion calls service.query with correct params."""
        mock_root = Mock()
        mock_service.query.return_value = [sample_runs[1]]
        mock_tree.get_children.return_value = []

        window = _create_window(mock_root, mock_service, mock_attempt_service, mock_tree)
        window._status_var = Mock(get=Mock(return_value="(All)"))
        window._conclusion_var = Mock(get=Mock(return_value="failure"))

        window._apply_filters()

        mock_service.query.assert_called_with(
            status=None,
            conclusion=WorkflowConclusion.FAILURE,
        )


class TestEditIntegration:
    """Test edit dialog integration with service."""

    def test_edit_persists_to_service(self, mock_service, mock_attempt_service, mock_tree, sample_runs):
        """Test that edited run is persisted via service.replace_run()."""
        mock_root = Mock()
        window = _create_window(mock_root, mock_service, mock_attempt_service, mock_tree)

        modified_run = WorkflowRun(
            id="1",
            workflow_name="modified",
            branch="main",
            status=sample_runs[0].status,
            conclusion=sample_runs[0].conclusion,
            created_at=sample_runs[0].created_at,
            updated_at=datetime.now(timezone.utc),
            run_number=sample_runs[0].run_number,
            commit_sha=sample_runs[0].commit_sha,
            duration_seconds=sample_runs[0].duration_seconds,
        )

        with patch('src.gui.workflow_gui.WorkflowRunEditDialog') as mock_dialog_class:
            with patch('tkinter.messagebox.showinfo'):
                mock_dialog = Mock()
                mock_dialog.result = modified_run
                mock_dialog.top = Mock()
                mock_dialog_class.return_value = mock_dialog

                mock_tree.selection.return_value = ["item1"]
                # Make item() return the values tuple directly when called with "values" key
                def mock_item(item_id, key):
                    if key == "values":
                        return (sample_runs[0].id, 'build', 'main', 'completed', 'success', '30.5')
                    return {}
                mock_tree.item = Mock(side_effect=mock_item)

                with patch.object(mock_root, 'wait_window'):
                    with patch.object(window, '_refresh'):
                        window._edit_run()

        mock_service.replace_run.assert_called_once_with(modified_run)


class TestDeleteIntegration:
    """Test delete integration with service."""

    def test_delete_calls_service(self, mock_service, mock_attempt_service, mock_tree, sample_runs):
        """Test that delete calls service.delete_run()."""
        mock_root = Mock()
        window = _create_window(mock_root, mock_service, mock_attempt_service, mock_tree)

        mock_tree.selection.return_value = ["item1"]
        # Make item() return the values tuple directly when called with "values" key
        def mock_item(item_id, key):
            if key == "values":
                return (sample_runs[0].id, 'build', 'main', 'completed', 'success', '30.5')
            return {}
        mock_tree.item = Mock(side_effect=mock_item)

        with patch('tkinter.messagebox.askyesno', return_value=True):
            with patch('tkinter.messagebox.showinfo'):
                with patch.object(window, '_refresh'):
                    window._delete_run()

        mock_service.delete_run.assert_called_once_with(sample_runs[0].id)
