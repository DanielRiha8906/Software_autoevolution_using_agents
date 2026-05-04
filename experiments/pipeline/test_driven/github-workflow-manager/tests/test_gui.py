"""Tests for WorkflowGUI module."""

import pytest
import subprocess
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.gui.workflow_gui import WorkflowGUI
from src.models.workflow_run import WorkflowRun
from src.models.workflow_status import WorkflowStatus
from src.models.workflow_conclusion import WorkflowConclusion
from src.services.workflow_run_service import WorkflowRunService


def _make_run(run_id: str = "run-1", branch: str = "main") -> WorkflowRun:
    """Create a test workflow run."""
    return WorkflowRun(
        id=run_id,
        workflow_name="CI",
        branch=branch,
        status=WorkflowStatus.COMPLETED,
        conclusion=WorkflowConclusion.SUCCESS,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        run_number=1,
        commit_sha="abc123",
    )


@pytest.fixture
def mock_service():
    """Create a mock WorkflowRunService."""
    service = MagicMock(spec=WorkflowRunService)
    service.list_runs.return_value = []
    return service


def test_workflow_gui_module_exists():
    """Test that WorkflowGUI module can be imported."""
    from src.gui import workflow_gui
    assert hasattr(workflow_gui, 'WorkflowGUI')


def test_workflow_gui_accepts_service_constructor(mock_service):
    """Test that WorkflowGUI accepts a service via constructor."""
    gui = WorkflowGUI(service=mock_service)
    assert gui.service is mock_service


def test_workflow_gui_stores_service_reference(mock_service):
    """Test that GUI stores and uses the injected service."""
    gui = WorkflowGUI(service=mock_service)
    assert gui.service == mock_service


def test_workflow_gui_does_not_instantiate_service_internally(mock_service):
    """Test that GUI does not create its own service instance."""
    # GUI should use the provided service, not create one
    gui = WorkflowGUI(service=mock_service)

    # Service should be the mock, not a real instance
    assert isinstance(gui.service, MagicMock)

    # The provided service should be stored as-is
    assert gui.service is mock_service


def test_workflow_gui_accepts_optional_attempt_service(mock_service):
    """Test that GUI accepts optional AttemptService."""
    attempt_service = MagicMock()
    gui = WorkflowGUI(service=mock_service, attempt_service=attempt_service)
    assert gui.attempt_service is attempt_service


def test_workflow_gui_attempt_service_optional(mock_service):
    """Test that AttemptService is optional."""
    gui = WorkflowGUI(service=mock_service)
    assert gui.attempt_service is None


def test_workflow_gui_source_does_not_use_subprocess():
    """Test that WorkflowGUI does not directly use subprocess."""
    gui_file = Path(__file__).parent.parent / "src" / "gui" / "workflow_gui.py"
    content = gui_file.read_text()

    # Check that subprocess is not imported in the GUI module
    assert "import subprocess" not in content
    assert "from subprocess" not in content


def test_workflow_gui_does_not_use_github_cli():
    """Test that WorkflowGUI does not invoke GitHub CLI directly."""
    gui_file = Path(__file__).parent.parent / "src" / "gui" / "workflow_gui.py"
    content = gui_file.read_text()

    # Check that subprocess calls to gh or git CLI are not made
    assert "subprocess.run" not in content or "gh" not in content
    assert "subprocess.call" not in content or "gh" not in content


def test_workflow_gui_references_service_in_code(mock_service):
    """Test that GUI code references the injected service."""
    gui_file = Path(__file__).parent.parent / "src" / "gui" / "workflow_gui.py"
    content = gui_file.read_text()

    # Service should be used in methods, not subprocess
    assert "self.service" in content
    assert "self.service.list_runs()" in content
    assert "self.service.get_run_detail" in content


def test_workflow_gui_handles_failed_runs_visually():
    """Test that GUI defines visual handling for failed runs."""
    gui_file = Path(__file__).parent.parent / "src" / "gui" / "workflow_gui.py"
    content = gui_file.read_text()

    # GUI should configure tags for visual differentiation
    assert "tag_configure" in content
    assert "failed" in content
    assert "success" in content
    assert "background=" in content or "foreground=" in content


def test_workflow_gui_uses_tag_for_failed_runs(mock_service):
    """Test that failed runs are tagged with 'failed' tag."""
    gui_file = Path(__file__).parent.parent / "src" / "gui" / "workflow_gui.py"
    content = gui_file.read_text()

    # Should check run.is_failed() and apply tag
    assert "is_failed()" in content
    assert 'tag = "failed"' in content


def test_workflow_gui_uses_tag_for_successful_runs(mock_service):
    """Test that successful runs are tagged with 'success' tag."""
    gui_file = Path(__file__).parent.parent / "src" / "gui" / "workflow_gui.py"
    content = gui_file.read_text()

    # Should check run.is_successful() and apply tag
    assert "is_successful()" in content
    assert 'tag = "success"' in content


def test_workflow_gui_uses_tag_for_in_progress_runs(mock_service):
    """Test that in-progress runs are tagged with 'in_progress' tag."""
    gui_file = Path(__file__).parent.parent / "src" / "gui" / "workflow_gui.py"
    content = gui_file.read_text()

    # Should check run.is_running() and apply tag
    assert "is_running()" in content
    assert 'tag = "in_progress"' in content


def test_workflow_gui_initializes_gui_widgets(mock_service):
    """Test that GUI initializes with placeholder widget attributes."""
    gui = WorkflowGUI(service=mock_service)

    # GUI should have attributes for widgets that will be created on run()
    assert hasattr(gui, 'root')
    assert hasattr(gui, 'tree')
    assert hasattr(gui, 'branch_var')
    assert hasattr(gui, 'status_var')
    assert hasattr(gui, 'conclusion_var')


def test_workflow_gui_has_run_method(mock_service):
    """Test that GUI has a run() method to start the application."""
    gui = WorkflowGUI(service=mock_service)
    assert callable(gui.run)
