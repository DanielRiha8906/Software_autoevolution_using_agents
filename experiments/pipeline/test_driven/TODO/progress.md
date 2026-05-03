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

Duration: PENDING | Cost: PENDING | Turns: PENDING
