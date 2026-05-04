import inspect
from unittest.mock import MagicMock


def test_workflow_gui_module_exists():
    from src.gui.workflow_gui import WorkflowGUI
    assert WorkflowGUI is not None


def test_workflow_gui_accepts_service():
    from src.gui.workflow_gui import WorkflowGUI
    gui = WorkflowGUI(MagicMock())
    assert gui is not None


def test_gui_does_not_instantiate_services():
    from src.gui import workflow_gui
    source = inspect.getsource(workflow_gui)

    assert "WorkflowRunService(" not in source
    assert "AttemptService(" not in source


def test_gui_does_not_use_github_cli():
    from src.gui import workflow_gui
    source = inspect.getsource(workflow_gui)

    assert "subprocess" not in source
    assert "gh " not in source


def test_gui_references_service():
    from src.gui import workflow_gui
    source = inspect.getsource(workflow_gui)

    assert "service" in source.lower()


def test_gui_handles_failed_runs_visually():
    from src.gui import workflow_gui
    source = inspect.getsource(workflow_gui)

    assert "fail" in source.lower() or "error" in source.lower()
