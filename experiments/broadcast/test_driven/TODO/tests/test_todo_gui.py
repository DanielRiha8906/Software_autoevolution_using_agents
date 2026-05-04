import inspect
from unittest.mock import MagicMock


def test_todo_gui_module_exists():
    from src.gui.todo_gui import TodoGUI
    assert TodoGUI is not None


def test_todo_gui_accepts_service():
    from src.gui.todo_gui import TodoGUI
    assert TodoGUI(MagicMock()) is not None


def test_gui_does_not_duplicate_task_logic():
    from src.gui import todo_gui
    source = inspect.getsource(todo_gui)
    assert "def add_task(" not in source
    assert "TaskStatus(" not in source


def test_gui_references_service():
    from src.gui import todo_gui
    source = inspect.getsource(todo_gui)
    assert "service" in source.lower()


def test_gui_handles_overdue():
    from src.gui import todo_gui
    source = inspect.getsource(todo_gui)
    assert "overdue" in source.lower() or "is_overdue" in source
