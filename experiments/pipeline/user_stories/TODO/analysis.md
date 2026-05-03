# Task 06 Analysis: Summary Report of Task Counts and Completion Rates

## Task Understanding

**Objective:** Implement a TODO application feature that generates a structured summary report of task statistics, including:
- Total task count
- Count breakdown by status (pending, in_progress, done)
- Count of overdue tasks
- Count of tasks with due date set
- Completion rate as a percentage (done / total)
- Bonus: Average days from creation to completion for done tasks
- Output as a dataclass (not plain dict)
- Output format deterministic regardless of task ordering
- Accessible via both interactive menu and CLI flag (`python -m src report` or similar)

## Current Architecture Overview

### Codebase Structure

**Models** (`src/models/`):
- `Task` (dataclass): Contains `id`, `title`, `description`, `status` (TaskStatus enum), `created_at` (datetime), `updated_at` (datetime), `due_date` (Optional[datetime]), `comments` (list of TaskComment)
- `TaskStatus` (enum): PENDING, IN_PROGRESS, DONE (with values "pending", "in_progress", "done")
- `TaskComment` (dataclass): For comment management (not directly relevant to report)

**Services** (`src/services/`):
- `TaskManager`: Core CRUD operations, persistence via JsonStorage
  - `list_all()` returns all tasks
  - `list_by_status(status)` filters by status
  - Methods available: `add()`, `get()`, `list_all()`, `list_by_status()`, `list_by_due_date_range()`, `update()`, `set_status()`, `set_due_date()`, `delete()`
- `TodoService`: High-level service layer wrapping TaskManager
  - Delegates to TaskManager for most operations
  - Also supports: `add_task()`, `list_tasks()`, `get_task()`, `complete_task()`, `start_task()`, `reopen_task()`, `update_task()`, etc.

**Storage** (`src/storage/`):
- `JsonStorage`: Reads/writes to JSON file (default: ~/.todo_data.json)
- Provides `load()` and `save(tasks)` methods

**CLI** (`src/cli/`):
- `TodoCLI`: Argument parser with subcommands (add, list, show, start, done, reopen, update, delete, due-date, add-comment, list-comments, delete-comment, edit-comment)
- `InteractiveMenu`: Full-screen terminal menu with options 1-8 (and 0 for quit)
  - Current menu options: List/filter (1), Add (2), Show (3), Change status (4), Update (5), Set due date (6), Delete (7), Manage comments (8)

**Entry Point** (`src/__main__.py`):
- If `sys.argv` has length > 1: dispatches to `TodoCLI().run()`
- Otherwise: launches `InteractiveMenu().run()`

### Data Model Available Fields

On **Task** object:
- `id: str` (UUID)
- `title: str`
- `description: Optional[str]`
- `status: TaskStatus` (with `.is_completed()`, `.is_pending()`, `.is_in_progress()`, `.is_overdue()` methods)
- `created_at: datetime` (UTC timezone-aware)
- `updated_at: datetime` (UTC timezone-aware)
- `due_date: Optional[datetime]` (UTC timezone-aware or None)
- `comments: list[TaskComment]`
- Methods: `is_pending()`, `is_in_progress()`, `is_completed()`, `is_overdue()`

## Key Findings

### 1. Data Availability for Report

All required fields for the report are already available:
- **Total count**: `len(service.list_tasks())`
- **Status counts**: Available via `service.list_tasks(status=TaskStatus.PENDING)` etc.
- **Overdue count**: Can use `task.is_overdue()` on all tasks
- **Due date set**: Can count tasks where `task.due_date is not None`
- **Completion rate**: Done count / Total count (trivial math)
- **Bonus metric (avg days creation to completion)**: 
  - Available from tasks with `status == DONE` 
  - Calculate: `(task.updated_at - task.created_at).days` (Note: `updated_at` is set when status changes to DONE)
  - Assumption: `updated_at` is updated when task is marked done (confirmed in code via `task.mark_done()` sets `updated_at`)

### 2. Output Format Requirement

**Must be a dataclass, not a plain dict.** This means:
- Create a new dataclass `TaskSummaryReport` (or similar name) in `src/models/`
- Fields: `total_count`, `pending_count`, `in_progress_count`, `done_count`, `overdue_count`, `due_date_set_count`, `completion_rate` (as float or percentage), and optionally `avg_days_to_completion` (float)
- Must be deterministic: Order doesn't matter for counts (all are aggregations), so output is inherently deterministic

### 3. Deterministic Output

The requirement states "Output format is deterministic regardless of task ordering":
- All counts are aggregations, so the order of tasks doesn't affect the result
- Completion rate is a ratio, also deterministic
- Average calculation is also deterministic (sum/count)
- Dataclass with frozen=True could help ensure immutability, but not required

### 4. CLI and Menu Integration

**Current CLI pattern** (`src/cli/todo_cli.py`):
- Uses `argparse` with subcommands
- New subcommand needed: `report` with no arguments (or optional filters?)
- Should return formatted output (JSON-compatible or human-readable)

**Current Menu pattern** (`src/cli/interactive_menu.py`):
- Main menu has options 1-8 (and 0 for quit)
- New menu option needed: e.g., option "9" for "View summary report"
- Should display report in human-readable format

**Entry point** (`src/__main__.py`):
- Already dispatches correctly: if args present, go to CLI; otherwise go to menu
- No changes needed here

## What New Functionality Is Needed

### 1. New Dataclass: TaskSummaryReport

**Location:** `src/models/task_summary_report.py` (new file)

**Fields:**
```python
@dataclass
class TaskSummaryReport:
    total_count: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    due_date_set_count: int
    completion_rate: float  # 0.0 to 1.0 (or percentage 0-100)
    avg_days_to_completion: Optional[float] = None  # bonus
```

**Exports:** Add to `src/models/__init__.py`

### 2. Report Generation Method

**Location:** `src/services/todo_service.py` (or new file `src/services/report_service.py`)

**Method:** `generate_report()` that:
1. Gets all tasks via `self.list_tasks()`
2. Counts by status using existing `list_by_status()` or manual iteration
3. Counts overdue using `task.is_overdue()`
4. Counts due_date set using `task.due_date is not None`
5. Calculates completion_rate: done_count / total_count (handle division by zero)
6. Calculates avg_days_to_completion for bonus (only for DONE tasks)
7. Returns `TaskSummaryReport` instance

### 3. CLI Integration

**Location:** `src/cli/todo_cli.py`

**New subcommand:** `report` (no arguments required)
- Add parser section:
  ```python
  p_report = sub.add_parser("report", help="Generate task summary report")
  p_report.set_defaults(func=self._cmd_report)
  ```
- Add handler method:
  ```python
  def _cmd_report(self, args: argparse.Namespace) -> int:
      report = self._service.generate_report()
      print(f"Total tasks: {report.total_count}")
      print(f"  Pending: {report.pending_count}")
      print(f"  In progress: {report.in_progress_count}")
      print(f"  Done: {report.done_count}")
      # ... etc
      return 0
  ```

### 4. Interactive Menu Integration

**Location:** `src/cli/interactive_menu.py`

**New menu option:** Add option 9 (after Manage comments, before Quit)
- Update `_print_main_menu()` to include new option
- Add new handler method `_do_report()` that:
  1. Gets report via `self._service.generate_report()`
  2. Displays in formatted human-readable way
  3. Prompts to continue (or auto-returns)

## What Existing Code Needs Modification

### 1. `src/models/__init__.py`
- Add import and export of `TaskSummaryReport`

### 2. `src/services/todo_service.py`
- Add new method `generate_report()` that creates and returns `TaskSummaryReport`

### 3. `src/cli/todo_cli.py`
- Add `report` subcommand to argparse parser
- Add `_cmd_report()` handler method
- Format and print report output

### 4. `src/cli/interactive_menu.py`
- Update `_print_main_menu()` to show new option (9)
- Update main loop to handle choice "9"
- Add `_do_report()` method to generate and display report

### 5. `src/__main__.py` (no changes needed)
- Already routes correctly

## Data Model Summary

### Task Fields Relevant to Report
| Field | Type | Used For | Notes |
|-------|------|----------|-------|
| `status` | TaskStatus | Counting by status | PENDING, IN_PROGRESS, DONE |
| `due_date` | Optional[datetime] | Overdue check, due_date_set count | None if not set |
| `created_at` | datetime | Bonus: avg days to completion | UTC timezone-aware |
| `updated_at` | datetime | Bonus: avg days to completion | Updated when status changes |

### Task Methods Relevant to Report
| Method | Returns | Use |
|--------|---------|-----|
| `is_overdue()` | bool | Determine if task is overdue |
| `is_completed()` | bool | Filter done tasks (alternative to status check) |

## Integration Points

### Service Layer Access
- `TodoService.list_tasks()` — Get all tasks
- `TodoService._manager.list_by_status(status)` — Get tasks by status (or iterate manually)
- Individual task methods: `task.is_overdue()`, `task.is_completed()`

### CLI Integration
- `src/cli/todo_cli.py`: Add `report` subcommand
- `argparse` parser already setup with subcommands pattern
- Error handling via existing `TaskNotFoundError`, `ValueError` patterns

### Menu Integration
- `src/cli/interactive_menu.py`: Add menu option 9
- Menu already has pattern for task listing and formatting
- Existing helper functions: `_clear()`, `_prompt()`, `_pick()`, etc.

## Ambiguities and Assumptions

### 1. Completion Rate Format
**Assumption:** Return as float 0.0-1.0 (not percentage 0-100). This is more programmatic and can be formatted as needed by CLI/menu.

### 2. Division by Zero
**Assumption:** If no tasks exist, completion_rate = 0.0 (or could be NaN, but 0.0 is safer for dataclass)

### 3. Average Days Calculation
**Assumption:** Use `(task.updated_at - task.created_at).days` for done tasks.
- This assumes `updated_at` is set correctly when task is marked done (confirmed in code).
- If no done tasks, average = None (optional field)

### 4. Overdue Definition
**Assumption:** Use `task.is_overdue()` which returns False if:
- `due_date` is None
- Status is DONE
Otherwise checks if `due_date < now(UTC)`

### 5. Menu Option Number
**Assumption:** New option is "9" (adds before "0. Quit"). Could be other number, but 9 is next logical.

### 6. Report Accessibility
**Assumption:** 
- CLI: `python -m src report` (no additional flags)
- Menu: Option 9 on main menu
- Both required per task statement

## Scope Signals

### In Scope
- Generate aggregate counts (total, by status, overdue, with due_date)
- Calculate completion rate (done / total)
- Return as dataclass
- Bonus: average days from creation to completion
- Accessible via CLI flag and menu option
- Deterministic output

### Explicitly Out of Scope
- Charts or visualization (stated: "No charts/visualization")
- Filters by date range or other criteria (report is global)
- Custom report templates
- Export to CSV, PDF, etc.

### Borderline/Clarification Needed
- Is `completion_rate` a float (0.0-1.0) or percentage (0-100)? → Assuming float
- Is it possible to customize which fields are included? → No, all required fields are fixed
- Can report be exported? → Not required, output only

## Suggested Implementation Priority

1. **Create `TaskSummaryReport` dataclass** (src/models/task_summary_report.py)
   - Define all required fields
   - Simple dataclass, no methods needed
   - Add to models/__init__.py

2. **Implement report generation** (src/services/todo_service.py)
   - Add `generate_report()` method
   - Implement all count logic
   - Test with various task scenarios (empty, all pending, mixed, overdue)

3. **Add CLI integration** (src/cli/todo_cli.py)
   - Add `report` subcommand to argparse
   - Add `_cmd_report()` handler
   - Format output for readability

4. **Add menu integration** (src/cli/interactive_menu.py)
   - Update main menu to include option 9
   - Implement `_do_report()` method
   - Format output for terminal display

5. **Write comprehensive tests**
   - Test report generation with various task scenarios
   - Test CLI command
   - Test menu option
   - Edge cases: no tasks, all done, no due dates, etc.

6. **Update diagrams** (artifacts/*.puml)
   - class_diagram.puml: Add TaskSummaryReport class
   - component_diagram.puml: Add Report component
   - use_case_diagram.puml: Add "Generate report" use case
