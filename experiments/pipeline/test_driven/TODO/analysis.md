# Task 10 Analysis: Implementing TodoGUI with tkinter

## Task Summary

Implement a tkinter-based GUI class (`TodoGUI`) that:
- Accepts a `TodoService` instance (not creating its own)
- Displays tasks with status, due date, and project information
- Supports basic task operations via the service layer (no duplicating business logic)
- Highlights overdue tasks visually
- Integrates entirely with the existing service architecture

## Current Project Structure

### Models (src/models/)
- **task.py**: `Task` dataclass with fields: `id`, `title`, `description`, `status`, `created_at`, `updated_at`, `due_date`, `project_id`
  - Methods: `is_overdue()`, `mark_in_progress()`, `mark_done()`, `reopen()`, `to_dict()`, `from_dict()`
- **task_status.py**: `TaskStatus` enum (PENDING, IN_PROGRESS, DONE)
- **project.py**: `Project` dataclass with fields: `id`, `name`, `description`, `created_at`
- **task_comment.py**: `TaskComment` dataclass for task comments

### Services (src/services/)
The service layer is fully initialized and provides these core APIs:
- **TodoService**:
  - `add_task(title, description=None, due_date=None, project_id=None) -> Task`
  - `get_task(task_id) -> Task`
  - `list_tasks(status=None, due_before=None, due_after=None, overdue=False, project_id=None) -> List[Task]`
  - `start_task(task_id) -> Task` (status → IN_PROGRESS)
  - `complete_task(task_id) -> Task` (status → DONE)
  - `reopen_task(task_id) -> Task` (status → PENDING)
  - `update_task(task_id, title=None, description=None, project_id=None) -> Task`
  - `delete_task(task_id) -> None`

- **ProjectService**:
  - `create(name, description=None) -> Project`
  - `get(project_id) -> Project`
  - `list_all() -> List[Project]`
  - `update(project_id, name=None, description=None) -> Project`
  - `delete(project_id) -> None`

- **CommentsService**:
  - `add_comment(task_id, content) -> TaskComment`
  - `list_comments(task_id) -> List[TaskComment]`
  - `delete_comment(comment_id) -> None`

- **TaskStatisticsService**:
  - `compute() -> TaskStatistics` (returns: total, count_per_status, overdue_count, with_due_date_count, completion_rate)

### Formatters (src/formatters/)
- **TaskFormatter**: Provides:
  - `get_status_symbol(status: TaskStatus) -> str` (returns "[ ]", "[~]", or "[x]")
  - `get_status_name(status: TaskStatus) -> str` (returns "pending", "in progress", "done")
  - `format_task_line(task, show_project=False) -> str` (pre-formatted task display line)

## Exact Changes Needed

### New Directory Structure Required
```
src/gui/
├── __init__.py          (module initialization)
└── todo_gui.py          (TodoGUI class implementation)
```

### File: src/gui/todo_gui.py
**Must implement:**
- `TodoGUI` class with constructor signature: `__init__(self, service: TodoService)`
- GUI must display:
  - Task status (using TaskFormatter symbols)
  - Task title
  - Task due date (if present)
  - Task project (if present)
  - Overdue highlighting (visual distinction for `task.is_overdue() == True`)
- GUI must support operations:
  - Add task (delegating to `service.add_task()`)
  - List tasks (delegating to `service.list_tasks()`)
  - Mark task status changes (delegating to `service.start_task()`, `complete_task()`, `reopen_task()`)
  - Update task (delegating to `service.update_task()`)
  - Delete task (delegating to `service.delete_task()`)
  - View task details
- GUI must NOT:
  - Define TaskStatus enum or duplicate it
  - Define add_task() logic (must delegate entirely to service)
  - Create its own TodoService instance
  - Include storage/persistence logic (all via service)

### File: src/gui/__init__.py
Must export the `TodoGUI` class for external imports.

## Key Test Requirements

1. `test_todo_gui_module_exists`: `from src.gui.todo_gui import TodoGUI` must work
2. `test_todo_gui_accepts_service`: `TodoGUI(MagicMock())` must instantiate successfully
3. `test_gui_does_not_duplicate_task_logic`: Source code must NOT contain "def add_task(" or "TaskStatus("
4. `test_gui_references_service`: Source code must reference "service" (case-insensitive)
5. `test_gui_handles_overdue`: Source code must reference "overdue" or "is_overdue"

## Key Constraints

1. **Service Injection**: Constructor must accept pre-instantiated `TodoService` instance, not create its own
2. **No Logic Duplication**: All task logic stays in TodoService. GUI is purely presentational.
3. **Overdue Detection**: Must use `task.is_overdue()` method from Task model
4. **Use tkinter**: Standard library only, no external GUI libraries
5. **Visual Distinction**: Overdue tasks must be highlighted/distinguished visually
6. **Backward Compatibility**: Must not break existing CLI or tests

## Files to Create

- `src/gui/__init__.py`
- `src/gui/todo_gui.py`
