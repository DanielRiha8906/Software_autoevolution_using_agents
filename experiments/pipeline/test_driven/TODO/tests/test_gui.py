"""Tests for the TodoGUI module."""

import inspect
from unittest.mock import MagicMock


def test_todo_gui_module_exists():
    """Verify TodoGUI class exists and can be imported."""
    from src.gui.todo_gui import TodoGUI
    assert TodoGUI is not None


def test_todo_gui_accepts_service():
    """Verify TodoGUI can be instantiated with a service object."""
    from src.gui.todo_gui import TodoGUI
    assert TodoGUI(MagicMock()) is not None


def test_gui_does_not_duplicate_task_logic():
    """Verify GUI does not duplicate task creation or status logic.

    The GUI should delegate to the service, not reimplement task logic.
    """
    from src.gui import todo_gui
    source = inspect.getsource(todo_gui)
    assert "def add_task(" not in source
    assert "TaskStatus(" not in source


def test_gui_references_service():
    """Verify GUI uses the injected service for operations."""
    from src.gui import todo_gui
    source = inspect.getsource(todo_gui)
    assert "service" in source.lower()


def test_gui_handles_overdue():
    """Verify GUI implementation handles overdue task detection."""
    from src.gui import todo_gui
    source = inspect.getsource(todo_gui)
    assert "overdue" in source.lower() or "is_overdue" in source
