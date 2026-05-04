# Design Document: TodoGUI Implementation with tkinter

## Test Specifications

All five required tests must pass:

1. **test_todo_gui_module_exists**
   - Module: `src/gui/todo_gui.py`
   - Test: Import `TodoGUI` class directly from the module
   - Expected: Class `TodoGUI` exists and can be imported without error

2. **test_todo_gui_accepts_service**
   - Method: `TodoGUI.__init__(service)`
   - Inputs: `service` parameter (mock object or real TodoService instance)
   - Expected: Instance created successfully with `TodoGUI(MagicMock())`
   - Behavior: Constructor must accept a pre-injected service instance

3. **test_gui_does_not_duplicate_task_logic**
   - Location: Source code of `src/gui/todo_gui.py`
   - Negative checks: Source must NOT contain literal strings:
     - `"def add_task("`
     - `"TaskStatus("`
   - Rationale: All task logic delegated to service; no enum redefinition

4. **test_gui_references_service**
   - Location: Source code of `src/gui/todo_gui.py`
   - Positive check: Source must contain word "service" (case-insensitive)
   - Rationale: Ensures service is referenced in the implementation

5. **test_gui_handles_overdue**
   - Location: Source code of `src/gui/todo_gui.py`
   - Positive check: Source must contain either:
     - `"overdue"` (case-insensitive), OR
     - `"is_overdue"` (case-insensitive)
   - Rationale: Ensures overdue detection logic is present

## Source Changes

### File: `src/gui/__init__.py` (NEW)

**Purpose:** Module initialization to export public interface

**Content structure:**
```python
from .todo_gui import TodoGUI

__all__ = ["TodoGUI"]
```

### File: `src/gui/todo_gui.py` (NEW)

**Purpose:** Tkinter-based GUI for task management

**Class Structure:**

`TodoGUI` class with the following design:

**Constructor:**
- Signature: `def __init__(self, service: TodoService) -> None:`
- Parameter: `service` — pre-instantiated `TodoService` (injected, not created)
- Instance variables to maintain:
  - `self.service` — the injected TodoService instance
  - `self.root` — tkinter.Tk() main window
  - `self.task_widgets` — dict mapping task IDs to widget references for updates
  - `self.current_filter` — dict storing current filtering state

**Window Structure (tkinter layout):**

1. **Top Control Frame**
   - Title label: "Todo Manager"
   - Refresh button to reload task list

2. **Input/Action Frame**
   - Text entry for new task title
   - Button to add task
   - Quick status filter buttons (All, Pending, In Progress, Done)

3. **Task List Frame (main area)**
   - Scrollable text widget or frame with task items
   - Each task displayed with:
     - Status symbol (using TaskFormatter.get_status_symbol)
     - Task ID
     - Task title
     - Due date (if present, formatted)
     - Project ID (if present)
   - Overdue visual distinction:
     - Red text for tasks where `task.is_overdue()` is True
     - Normal text for other tasks

4. **Task Details Frame**
   - Show when task is selected
   - Display: full description, timestamps, IDs
   - Action buttons:
     - Start Task (calls `service.start_task()`)
     - Complete Task (calls `service.complete_task()`)
     - Reopen Task (calls `service.reopen_task()`)
     - Delete Task (calls `service.delete_task()`)
     - Update (calls `service.update_task()`)

**Key Methods:**

- `_create_widgets()` — Initialize all tkinter widgets and layout
- `_refresh_task_list()` — Reload tasks from service and update display
- `_add_task(title_text)` — Add new task via service
- `_display_task_line(task)` — Render a single task with overdue highlighting
- `_on_task_select(task_id)` — Handle task selection
- `_start_task(task_id)` — Start a task
- `_complete_task(task_id)` — Mark task done
- `_reopen_task(task_id)` — Reopen a task
- `_delete_task(task_id)` — Delete a task with confirmation
- `_update_task(task_id, **kwargs)` — Update task fields
- `run()` — Start the GUI event loop

**Imports and Dependencies:**

```python
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone, timedelta

from ..models.task import CEST
from ..formatters.task_formatter import TaskFormatter
from ..services.todo_service import TodoService
```

**Visual Distinction for Overdue Tasks:**

- Use `Text` widget tags or direct foreground coloring
- Apply red color when `task.is_overdue()` is True
- Use `TaskFormatter.get_status_symbol()` for consistent status display

**Exception Handling Pattern:**

For all service calls:
```python
try:
    result = self.service.method(args)
    self._refresh_task_list()
except Exception as e:
    messagebox.showerror("Error", str(e))
```

**Service Integration Pattern:**

Every GUI action follows this flow:
1. User triggers action (button click, Enter key, menu selection)
2. Validate input locally if needed
3. Call `self.service.method(args)`
4. On success: refresh display with `self._refresh_task_list()`
5. On failure: show error dialog and do NOT refresh

## Backward Compatibility

- No existing files are modified
- Service layer is unchanged
- GUI is purely additive

## Files to Create

1. `src/gui/__init__.py`
2. `src/gui/todo_gui.py`
