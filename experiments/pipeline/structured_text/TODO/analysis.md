# Task Statistics Functionality Analysis

## Task Summary

Add task statistics functionality to compute aggregate metrics about the TODO application's task population. The statistics must be:
- Exposed via `python -m src stats` as a CLI one-shot command
- Exposed via interactive menu as a numbered menu option
- Returned as a dataclass-structured report object
- Computable from all tasks in storage without external dependencies

**Required metrics:**
- Total task count
- Count per status (pending, in_progress, done)
- Count of overdue tasks
- Count of tasks with a due date set

---

## Current Architecture

### Overall Structure

The application follows a layered architecture:

1. **Entry Point** (`src/__main__.py`): Routes to `InteractiveMenu` (no args) or `TodoCLI` (with args)
2. **CLI Layer** (`src/cli/`):
   - `TodoCLI`: Argparse-based command dispatch; each command is a `_cmd_*` method
   - `InteractiveMenu`: Menu-driven UI with numbered options; each action is a `_do_*` method
3. **Service Layer** (`src/services/`):
   - `TodoService`: High-level business logic (public API for CLI/UI)
   - `TaskManager`: Task CRUD and filtering
   - `CommentManager`: Comment CRUD
4. **Domain Model** (`src/models/`):
   - `Task`: Dataclass with task fields
   - `TaskStatus`: Enum (PENDING, IN_PROGRESS, DONE)
   - `TaskComment`: Dataclass for comments
5. **Persistence** (`src/storage/`):
   - `JsonStorage`: Loads/saves task and comment JSON
6. **Utilities** (`src/utils/`):
   - `TimezoneUtils`: CEST/UTC timezone conversion

### Current Entry Point Logic

**File:** `src/__main__.py` (21 lines)

```python
def main() -> None:
    if len(sys.argv) > 1:
        sys.exit(TodoCLI().run())  # CLI mode

    menu = InteractiveMenu()
    try:
        menu.run()                 # Interactive mode
    except KeyboardInterrupt:
        print()
        sys.exit(0)
```

**Behavior:** If command-line arguments are present, use `TodoCLI.run()` (which parses argv). Otherwise, start `InteractiveMenu.run()`.

---

## Task Storage Mechanism

### Task Data Model

**File:** `src/models/task.py` (90 lines)

```python
@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING  # enum: PENDING, IN_PROGRESS, DONE
    due_date: Optional[datetime] = None      # nullable, ISO 8601 format when persisted
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

**Key methods:**
- `is_overdue() -> bool`: Returns True if due_date is set, status != DONE, and current UTC time > due_date
- `is_completed() -> bool`: Returns True if status == DONE

### Task Storage

**File:** `src/services/task_manager.py` (124 lines)

```python
class TaskManager:
    def __init__(self, storage: Optional[JsonStorage] = None):
        self._storage = storage or JsonStorage()
        self._tasks: dict[str, Task] = {}  # in-memory dict keyed by task.id
        self._load()

    def list_all(self) -> list[Task]:
        return list(self._tasks.values())
```

**Access pattern:** All tasks are held in `self._tasks` dict. Method `list_all()` returns all tasks as a list. No filtering needed at storage layer — all data is already in memory.

---

## Current CLI/Menu Structure

### CLI Mode (TodoCLI)

**File:** `src/cli/todo_cli.py` (277 lines)

**Command structure:**
```
todo add [title] [-d description]
todo list [--status pending|in_progress|done] [--due-after DATE] [--due-before DATE] [--overdue|--not-overdue]
todo show [id]
todo start [id]
todo done [id]
todo reopen [id]
todo update [id] [-t title] [-d description]
todo delete [id]
todo is-completed [id]
todo check-overdue [id]
todo add-comment [task_id] [content] [-a author]
todo show-comments [task_id]
todo delete-comment [comment_id]
```

**Argparse structure:**
- Main parser with subparsers for each command
- Each subcommand gets `set_defaults(func=self._cmd_*)` callback
- `run(argv)` method handles parsing and dispatch

**Example command handler:**
```python
def _cmd_list(self, args: argparse.Namespace) -> int:
    # Parse filters, call self._service.list_tasks(), print results
    return 0
```

### Interactive Menu Mode

**File:** `src/cli/interactive_menu.py` (448 lines)

**Main menu (from `_print_main_menu()`):**
```
  1. List / filter tasks
  2. Add task
  3. Show task details
  4. Change status  (start / done / reopen)
  5. Update task    (title / description)
  6. Delete task
  7. Check if task is completed
  8. Check if task is overdue
  9. Manage comments
  0. Quit
```

**Pattern:** Each menu option maps to a `_do_*` method via the main loop:
```python
def run(self) -> None:
    while True:
        # ...display menu, get choice...
        if choice == "1":
            self._do_list()
        elif choice == "2":
            self._do_add()
        # etc.
```

---

## Required Changes

### 1. Create TaskStatistics Dataclass

**File to create:** `src/models/task_statistics.py`

```python
from dataclasses import dataclass

@dataclass
class TaskStatistics:
    total_count: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    with_due_date_count: int
```

**Rationale:** Dataclass provides structured output, matches pattern already used for Task and TaskComment. Can be serialized to dict or JSON if needed.

### 2. Add Statistics Method to TodoService

**File to modify:** `src/services/todo_service.py`

Add method to `TodoService` class:
```python
def get_statistics(self) -> TaskStatistics:
    """Compute aggregate statistics over all tasks."""
    tasks = self._manager.list_all()
    
    total_count = len(tasks)
    pending_count = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    in_progress_count = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    done_count = sum(1 for t in tasks if t.status == TaskStatus.DONE)
    overdue_count = sum(1 for t in tasks if t.is_overdue())
    with_due_date_count = sum(1 for t in tasks if t.due_date is not None)
    
    return TaskStatistics(
        total_count=total_count,
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        done_count=done_count,
        overdue_count=overdue_count,
        with_due_date_count=with_due_date_count,
    )
```

**Location:** Add after `get_comments()` method, before class end.

### 3. Add CLI Command (`stats` subcommand)

**File to modify:** `src/cli/todo_cli.py`

In `_build_parser()`, add new subparser (after the `delete-comment` subparser):
```python
p_stats = sub.add_parser("stats", help="Show task statistics")
p_stats.set_defaults(func=self._cmd_stats)
```

Add handler method:
```python
def _cmd_stats(self, args: argparse.Namespace) -> int:
    stats = self._service.get_statistics()
    print(f"Task Statistics:")
    print(f"  Total:           {stats.total_count}")
    print(f"  Pending:         {stats.pending_count}")
    print(f"  In Progress:     {stats.in_progress_count}")
    print(f"  Done:            {stats.done_count}")
    print(f"  Overdue:         {stats.overdue_count}")
    print(f"  With due date:   {stats.with_due_date_count}")
    return 0
```

### 4. Add Interactive Menu Option

**File to modify:** `src/cli/interactive_menu.py`

In `_print_main_menu()`, change the last displayed line before "0. Quit":
```python
def _print_main_menu(self) -> None:
    print("  1. List / filter tasks")
    print("  2. Add task")
    print("  3. Show task details")
    print("  4. Change status  (start / done / reopen)")
    print("  5. Update task    (title / description)")
    print("  6. Delete task")
    print("  7. Check if task is completed")
    print("  8. Check if task is overdue")
    print("  9. Manage comments")
    print("  10. View statistics")        # ADD THIS
    print("  0. Quit")
    print()
```

In `run()` method, in the main loop after the comments handler, add:
```python
elif choice == "10":
    self._do_statistics()
```

Add handler method:
```python
def _do_statistics(self) -> None:
    _clear()
    stats = self._service.get_statistics()
    print("  Task Statistics\n")
    print(f"  Total tasks:           {stats.total_count}")
    print(f"  Pending:               {stats.pending_count}")
    print(f"  In Progress:           {stats.in_progress_count}")
    print(f"  Done:                  {stats.done_count}")
    print(f"  Overdue (active):      {stats.overdue_count}")
    print(f"  With due date:         {stats.with_due_date_count}")
    print()
    input("  Press Enter to continue...")
```

---

## Implementation Notes

### Metric Definitions

**total_count:** Length of all tasks. Computed once with `len(tasks)`.

**pending_count, in_progress_count, done_count:** Sum of tasks matching each `TaskStatus` enum value. Uses single pass over all tasks.

**overdue_count:** Sum of tasks where `task.is_overdue()` returns True. This delegates to Task's existing method which checks:
- due_date is not None
- status != DONE
- current UTC time > due_date

**with_due_date_count:** Sum of tasks where `task.due_date is not None`. Does not check completion status.

### Code Reuse & Consistency

1. **No new dependencies:** TaskStatistics uses only dataclass (already imported in models)
2. **Existing patterns:** Follows existing CLI command pattern (argparse handler + print output) and menu pattern (helper method in class)
3. **Service layer:** Statistics method lives in TodoService, not in TaskManager, to follow existing layering (TodoService is the public facade)
4. **Storage layer:** No changes needed; `list_all()` already returns all tasks in memory

### Testing Surface

Implementation is testable at three levels:
1. **Unit:** `TodoService.get_statistics()` with mocked task lists
2. **Integration:** CLI command `python -m src stats`
3. **Integration:** Interactive menu option 10

### Edge Cases Handled by Existing Code

- **Empty task list:** `total_count` will be 0, all counts will be 0 — valid output
- **Tasks without due_date:** `with_due_date_count` correctly excludes them; `overdue_count` also excludes them (by Task.is_overdue())
- **Completed overdue tasks:** Task.is_overdue() returns False if status == DONE, so they won't be counted in `overdue_count` but will be in `done_count`

---

## Scope & Boundaries

### In Scope
- Computing statistics from in-memory task list
- Returning structured dataclass
- CLI exposure via `stats` subcommand
- Interactive menu option

### Out of Scope
- Statistics persistence or history (not requested)
- Filtering statistics by date range or other criteria (not requested)
- Graphical charts or visualizations (would be menu-only, no CLI flag needed)
- Export to CSV/JSON format (not requested)

### Borderline / Working Assumptions

**Q: Should statistics include cascading impact of comment counts?**
A: Not requested. Task.* does not mention comments, so statistics are task-only.

**Q: Should overdue status respect timezone?**
A: Use existing Task.is_overdue() method, which uses UTC. Consistent with application's timezone handling.

**Q: Should the menu option be numbered 10 or should other options be renumbered?**
A: Adding as 10 avoids breaking any existing scripts/tests that reference "9" as manage comments. The next free number is safe and least disruptive.

