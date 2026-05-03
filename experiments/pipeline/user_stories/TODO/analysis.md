# TODO Application: Due Date Filtering Analysis

## Task Overview

Implement task filtering by due date and overdue status, enabling users to query tasks by:
- Due date range (before/after datetime)
- Time period filters (week, month, year)
- Overdue status
- Combined with existing status filtering
- Access via CLI and interactive menu

---

## Current Task Data Structure

### Task Model
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/models/task.py`

**Key attributes:**
- `id: str` — UUID, supports prefix lookup
- `title: str` — required
- `description: Optional[str]`
- `status: TaskStatus` — enum (PENDING, IN_PROGRESS, DONE)
- `created_at: datetime` — UTC timezone-aware, auto-set
- `updated_at: datetime` — UTC timezone-aware, auto-set
- `due_date: Optional[datetime]` — UTC timezone-aware, nullable
- `comments: list[TaskComment]`

**Existing query methods on Task:**
- `is_pending() -> bool`
- `is_in_progress() -> bool`
- `is_completed() -> bool`
- `is_overdue() -> bool` — **already implemented** (checks if `due_date < now` and not DONE)

**Serialization:**
- `to_dict()` — serializes as ISO 8601 strings
- `from_dict(data)` — deserializes from dicts

**Validation:**
- Enforces timezone-aware datetimes on initialization (raises ValueError if `due_date.tzinfo is None`)

---

## Current Filtering Implementation

### TodoService.list_tasks() [Main filtering entry point]
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/services/todo_service.py` (lines 25-28)

```python
def list_tasks(self, status: Optional[TaskStatus] = None) -> list[Task]:
    if status is not None:
        return self._manager.list_by_status(status)
    return self._manager.list_all()
```

**Current behavior:**
- Accepts single optional `status` parameter (TaskStatus enum)
- Returns all tasks if status is None
- Delegates to TaskManager for actual filtering

### TaskManager filtering methods
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/services/task_manager.py`

- `list_all()` (line 44) — returns all tasks as list
- `list_by_status(status: TaskStatus)` (lines 47-48) — filters by status via list comprehension

**Pattern:** Simple list comprehensions on `self._tasks.values()`, no composition/chaining support

---

## Where list_tasks() is Called

### From CLI
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/cli/todo_cli.py`

- `_cmd_list()` (lines 143-153) — parses `--status` flag, calls `list_tasks(status)`
  - Currently supports: `--status [pending|in_progress|done]`
  - Displays results with status symbols and descriptions

### From Interactive Menu
**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/cli/interactive_menu.py`

- `run()` (line 62) — calls `list_tasks()` with no args to display all tasks in header
- `_do_list()` (lines 120-142) — interactive status filter menu
  - Prompts user to select status (pending/in_progress/done/all)
  - Calls `list_tasks(status)`
  - Displays with line format: `[status_symbol] [id_prefix] [title] [description]`

---

## How Status Filtering Currently Works

### In CLI (todo_cli.py)
```python
def _cmd_list(self, args: argparse.Namespace) -> int:
    status = TaskStatus(args.status) if args.status else None  # Convert string to enum
    tasks = self._service.list_tasks(status)  # Pass enum or None
    # ... display logic
```

### In Interactive Menu (interactive_menu.py)
```python
status_map = {"1": TaskStatus.PENDING, "2": TaskStatus.IN_PROGRESS, "3": TaskStatus.DONE}
status = status_map.get(raw)  # Lookup enum or None
tasks = self._service.list_tasks(status)  # Pass enum or None
```

**Pattern:**
1. User input (string or numeric choice) → enum conversion
2. Pass enum or None to service
3. Service delegates to manager's `list_by_status()`
4. Manager uses list comprehension to filter

---

## Required Changes for Due Date Filtering

### 1. Service Layer (TodoService)

**Extend `list_tasks()` signature:**

Currently:
```python
def list_tasks(self, status: Optional[TaskStatus] = None) -> list[Task]
```

Should become:
```python
def list_tasks(
    self,
    status: Optional[TaskStatus] = None,
    before: Optional[datetime] = None,
    after: Optional[datetime] = None,
    overdue_only: bool = False
) -> list[Task]
```

**Add helper methods for time period filtering:**
- `list_tasks_by_week(year: int, week: int, status: Optional[TaskStatus] = None) -> list[Task]`
- `list_tasks_by_month(year: int, month: int, status: Optional[TaskStatus] = None) -> list[Task]`
- `list_tasks_by_year(year: int, status: Optional[TaskStatus] = None) -> list[Task]`

**Or a more flexible approach:**
```python
def list_tasks_by_due_date_range(
    self,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    status: Optional[TaskStatus] = None,
    overdue_only: bool = False
) -> list[Task]
```

### 2. Manager Layer (TaskManager)

**Add filtering methods:**

```python
def list_by_due_date_range(
    self,
    before: Optional[datetime] = None,
    after: Optional[datetime] = None,
    status: Optional[TaskStatus] = None,
    overdue_only: bool = False
) -> list[Task]:
    """Filter tasks by due date range and optional status/overdue."""
```

**Filtering logic needed:**
- If `before` is set: include only tasks where `due_date <= before` or `due_date is None` (decision needed)
- If `after` is set: include only tasks where `due_date >= after`
- If `overdue_only=True`: include only tasks where `task.is_overdue()`
- If `status` is set: include only matching status
- Combine all conditions with AND logic

**Note:** The `is_overdue()` method already exists on Task, so can be leveraged

### 3. CLI Layer (TodoCLI)

**Extend `_cmd_list()` argument parser:**

Current:
```python
p_list.add_argument("--status", choices=["pending", "in_progress", "done"], help="Filter by status")
```

Add:
```python
p_list.add_argument("--due-before", help="Due date before (ISO 8601, e.g., 2026-05-15T23:59:59+00:00)")
p_list.add_argument("--due-after", help="Due date after (ISO 8601)")
p_list.add_argument("--week", help="Due in week YYYY-Www (e.g., 2026-W20)")
p_list.add_argument("--month", help="Due in month YYYY-MM (e.g., 2026-05)")
p_list.add_argument("--year", help="Due in year YYYY (e.g., 2026)")
p_list.add_argument("--overdue", action="store_true", help="Show only overdue tasks")
```

**Implement `_cmd_list()` logic:**
1. Parse date arguments (ISO 8601 strings → datetime objects)
2. Convert week/month/year to date ranges
3. Call appropriate service method
4. Display results (extend current display to show due date if present)

### 4. Interactive Menu Layer (InteractiveMenu)

**Extend `_do_list()` menu:**

Current flow:
1. Prompt for status filter (4 options: pending/in_progress/done/all)
2. Display filtered tasks

New flow:
1. Show filter submenu:
   - Filter by status
   - Filter by due date range
   - Filter by time period (week/month/year)
   - Filter by overdue only
   - Combine filters
2. Collect filter parameters via prompts
3. Call service with combined filters
4. Display results with due date column

---

## Key Implementation Details

### Date Range Calculation

For week/month/year filters, need to calculate boundaries:

**Week (ISO 8601):** Week starts Monday
- Input: "2026-W20" (week 20 of 2026)
- Start: first day of that week (Monday)
- End: last day of that week (Sunday at 23:59:59)

**Month:**
- Input: "2026-05"
- Start: 2026-05-01 00:00:00
- End: 2026-05-31 23:59:59

**Year:**
- Input: "2026"
- Start: 2026-01-01 00:00:00
- End: 2026-12-31 23:59:59

Recommendation: Use `datetime.date.fromisocalendar()` for weeks, `calendar` module for month boundaries

### Combining Filters

All filters should be combinable (AND logic):
- status + due_before
- status + due_after + overdue
- week + status
- etc.

Current implementation (`list_by_status`) is incompatible with combining filters. Need unified filtering strategy.

### Display Considerations

**Current output:** `[status_symbol] [id_prefix] [title] [description]`

**Consider adding due date info:**
- Show due date inline? `[status] [id] [title] (due: 2026-05-15)`
- Show overdue warning? Flag overdue tasks with `*` or color
- Show count in header? "Tasks: 12 (3 overdue)"

### Timezone Handling

- All `due_date` fields are UTC timezone-aware
- User input (CLI/menu) should be parsed as ISO 8601, preserving timezone
- Comparisons (`before`, `after`, `overdue`) all use UTC `datetime.now(timezone.utc)`
- **Already handled correctly in existing code**

---

## Files to Modify

1. **src/services/todo_service.py** — extend `list_tasks()` signature and add time-period methods
2. **src/services/task_manager.py** — add `list_by_due_date_range()` and helper methods
3. **src/cli/todo_cli.py** — extend `list` subcommand args, implement `_cmd_list()` date parsing logic
4. **src/cli/interactive_menu.py** — extend `_do_list()` with date filter menu options
5. **src/__main__.py** — no changes needed (CLI/menu wiring already in place)

No model, storage, or test infrastructure changes required initially (Task and JsonStorage already support due_date).

---

## Ambiguities & Decisions

1. **Null due_date handling in range filters:**
   - Should tasks with `due_date=None` be included when filtering by date range?
   - Assumption: No, exclude them. They are not "due" at all.
   - Alternative: Add `include_no_due_date: bool` flag if needed later.

2. **Filter combination order:**
   - Should all filters be AND-ed? Yes.
   - Example: `--status pending --overdue` → pending AND overdue
   - Assumption: All filters are AND-ed together.

3. **Week/month/year boundary precision:**
   - Should period end at 00:00:00 or 23:59:59?
   - Assumption: End at 23:59:59 to be inclusive of whole day/month/year.

4. **CLI flag vs menu option naming:**
   - CLI flags: `--due-before`, `--due-after`, `--week`, `--month`, `--year`, `--overdue`
   - Menu: numbered or lettered options for filter type, then sub-prompts for values
   - Assumption: Follow existing pattern (status filter is option 1 in menu).

5. **Combined filter semantics in interactive menu:**
   - Should user be able to stack multiple filters in one session?
   - Assumption: Yes, show a "filter summary" before displaying results.

---

## Integration Points

### Test Coverage Implications
- Current tests focus on status filtering (test_task_manager.py, test_todo_service.py)
- New tests needed for:
  - Due date range filtering
  - Week/month/year parsing and boundary calculation
  - Overdue detection in filter context
  - Combined filters (status + due_date)
  - CLI date parsing and validation
  - Interactive menu date input

### Backward Compatibility
- Existing `list_tasks()` calls with `status=None` will still work (default behavior unchanged)
- New parameters are optional with sensible defaults
- CLI: existing `list` command without filters still works

---

## Summary

The TODO application has a clean separation of concerns (models → services → CLI/menu). The Task model already includes `due_date` and `is_overdue()` logic. The filtering infrastructure in TodoService and TaskManager is currently single-purpose (status only) but follows a simple pattern that can be extended.

**Primary work:**
1. Extend service/manager filtering to accept date ranges and combine with status
2. Add CLI arguments for date filtering and parse ISO 8601 input
3. Add interactive menu options for date-based filtering
4. Display results with due date information where relevant

**No structural changes needed** — just extend existing filtering patterns to include date-based predicates.
