# Task 05: Extend list_tasks with Due Date Filtering

## Summary

Extended `TodoService.list_tasks()` to support filtering by due date range and overdue status, combining cleanly with the existing status filter without breaking its behavior.

## Files Changed

- `src/services/todo_service.py` — Extended list_tasks() signature and implemented filtering logic with timezone validation
- `src/cli/todo_cli.py` — Added --due-before, --due-after, --overdue flags to list subparser
- `src/cli/interactive_menu.py` — Added menu option 7 for due date filtering
- `tests/test_task_05_due_date_filtering.py` — Created new test file with 7 test functions
- `artifacts/class_diagram.puml` — Updated TodoService signatures
- `artifacts/use_case_diagram.puml` — Added new use cases for due date filtering
- `artifacts/activity_diagram.puml` — Added activity for menu option 7

## Test Results

All tests pass:
- **7 new tests** (test_task_05_due_date_filtering.py): PASS
  - test_filter_overdue
  - test_filter_due_before
  - test_filter_due_after
  - test_combined_status_and_overdue
  - test_existing_status_filter_unchanged
  - test_due_date_filters_use_cest
  - test_results_are_task_objects

- **87 total tests**: ALL PASS
- **80 existing tests**: PASS (no regressions)

## Implementation Details

### Core Features
1. **Timezone Validation**: All due_date filters validate CEST timezone; non-CEST raises ValueError
2. **Filter Logic**: 
   - `overdue=True` — returns tasks where is_overdue() == True
   - `due_before=dt` — returns tasks where due_date is None or due_date < dt
   - `due_after=dt` — returns tasks where due_date is None or due_date > dt
3. **Combined Filters**: All filters use AND logic; can be combined with status filter
4. **Backward Compatibility**: All new parameters have defaults; existing calls work unchanged

### CLI Integration
- `python -m src list --overdue` — show overdue tasks
- `python -m src list --due-before "2026-05-31T18:00:00+02:00"` — tasks before cutoff
- `python -m src list --status pending --overdue` — pending tasks that are overdue

### Interactive Menu
- New menu option 7: "Filter by due date"
- Submenu with 3 filtering options:
  1. Overdue tasks
  2. Due before date (YYYY-MM-DD HH:MM in CEST)
  3. Due after date (YYYY-MM-DD HH:MM in CEST)

## Constraints Met
✅ All provided tests pass
✅ Existing tests still pass (no regressions)
✅ Code compiles without syntax errors
✅ `list_tasks()` with no arguments returns all tasks
✅ Functionality accessible via `python -m src` (CLI flags + interactive menu)
✅ Timezone validation enforces CEST only
✅ Status filter logic unchanged
✅ No database query engine used (in-memory filtering)

Duration: 452.6s | Cost: $0.830710 USD | Turns: 23

---

# Task 06: Implement TaskStatisticsService

## Summary

Implemented `TaskStatisticsService` that computes aggregate statistics from stored tasks, including total count, per-status breakdown, overdue count, tasks with due dates, and completion rate as a percentage.

## Files Changed

- `src/services/task_statistics_service.py` — Created new service with TaskStatistics dataclass and TaskStatisticsService class
- `src/services/statistics_service.py` — Created alias module for test imports (re-exports from task_statistics_service)
- `src/services/__init__.py` — Added TaskStatisticsService and TaskStatistics exports
- `src/cli/todo_cli.py` — Added statistics subcommand (python -m src statistics)
- `src/cli/interactive_menu.py` — Added menu option 8 for "View statistics"
- `tests/test_statistics_service.py` — Created comprehensive test suite (22 tests)
- `artifacts/class_diagram.puml` — Added TaskStatistics and TaskStatisticsService classes
- `artifacts/component_diagram.puml` — Added Task Statistics Service component

## Test Results

All tests pass:
- **8 required tests**: PASS (test_report_is_dataclass, test_total_count, test_count_per_status, test_overdue_count, test_with_due_date_count, test_completion_rate, test_empty_task_list_statistics, test_output_is_deterministic)
- **14 additional comprehensive tests**: PASS (edge cases, invariants, integration)
- **109 total tests**: ALL PASS
- **87 existing tests**: PASS (no regressions)

## Implementation Details

### Core Features
1. **TaskStatistics Dataclass**: Contains 5 fields:
   - `total: int` — total number of tasks
   - `count_per_status: dict[TaskStatus, int]` — count per status (PENDING, IN_PROGRESS, DONE)
   - `overdue_count: int` — tasks with due_date in the past
   - `with_due_date_count: int` — tasks with non-None due_date
   - `completion_rate: float` — percentage of completed tasks (0-100)

2. **TaskStatisticsService.compute()**: Computes all statistics in one call:
   - Gets all tasks via `TodoService.list_tasks()`
   - Counts tasks per status
   - Uses `list_tasks(overdue=True)` for overdue count
   - Filters tasks with `due_date is not None` for due date count
   - Calculates completion_rate: `(done_count / total * 100) if total > 0 else 0.0`

3. **CLI Integration**:
   - Command: `python -m src statistics`
   - Displays formatted report with aligned output

4. **Interactive Menu**:
   - Menu option 8: "View statistics"
   - Displays statistics in formatted box with aligned columns

### Edge Cases Handled
- Empty task list: completion_rate = 0.0 (not NaN or exception)
- No tasks with due dates: with_due_date_count = 0
- All tasks completed: completion_rate = 100.0
- No overdue tasks: overdue_count = 0
- Division by zero: Protected by `if total > 0` check

## Constraints Met
✅ All provided tests pass (8/8)
✅ Existing tests still pass (87/87, no regressions)
✅ Code compiles without syntax errors
✅ TaskStatistics is a @dataclass (not dict, not custom class)
✅ Completion rate expressed as 0-100 percentage
✅ Empty task lists handled safely
✅ All functionality accessible via `python -m src`
✅ Return type is deterministic dataclass

Duration: 414.9s | Cost: $0.732374 USD | Turns: 15
