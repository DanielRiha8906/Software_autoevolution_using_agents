# Progress Log

## Task 01: Add due date to tasks

### Summary

Successfully implemented due_date feature for Task model with full backward compatibility and comprehensive test coverage.

### Files Changed

**Source Code:**
- `src/models/task.py` — Added due_date field, updated to_dict()/from_dict(), added is_overdue() method

**Tests:**
- `tests/test_task.py` — Added 14 new tests covering due_date functionality
- `tests/test_task_manager.py` — Added 2 new persistence and backward compatibility tests

**Documentation:**
- `artifacts/class_diagram.puml` — Updated Task class diagram with new field and method

**Analysis & Design:**
- `analysis.md` — Documented current structure and requirements
- `design.md` — Detailed implementation plan

### Test Results

✅ All 57 tests passed
- New tests: 16 (14 in test_task.py + 2 in test_task_manager.py)
- Existing tests: 41 (all still passing)
- Backward compatibility verified

### Features Implemented

**Must (All Completed):**
- ✅ Add attribute `due_date: Optional[datetime]` to Task
- ✅ Allow tasks without a due date (None by default)
- ✅ Persist due_date through storage layer
- ✅ Update to_dict() and from_dict()
- ✅ Use CEST timezone-aware datetime (stored UTC, ready for display)

**Should (All Completed):**
- ✅ Backward compatibility with stored JSON (tasks without due_date load without error)
- ✅ Validate datetime values in parsing

**Could (Completed):**
- ✅ Added is_overdue() predicate returning True for past due_dates on non-DONE tasks

### Implementation Details

- Due dates stored as UTC timezone-aware datetime objects (consistent with created_at/updated_at)
- Serialization uses ISO 8601 format (+00:00 timezone suffix)
- to_dict() conditionally omits null due_date for clean JSON
- from_dict() safely parses using .get() for backward compatibility
- is_overdue() returns False for tasks without due_date, DONE status, or future dates

Duration: 358.9s | Cost: $0.528996 USD | Turns: 18

## Task 02: Add status and due date methods to Task

### Summary
Successfully implemented status transition and query methods on the Task class, including CLI and interactive menu exposure.

### Files Changed
- src/models/task.py — Added mark_in_progress(), mark_done(), reopen(), is_completed() methods
- src/cli/todo_cli.py — Added is-completed and check-overdue CLI commands
- src/cli/interactive_menu.py — Added menu options 7 and 8 for checking task status
- tests/test_task.py — Added 34 tests for Task class methods
- tests/test_todo_cli.py — Added 10 tests for CLI commands
- artifacts/class_diagram.puml — Updated Task class diagram with new methods
- artifacts/activity_diagram.puml — Updated activity diagram with menu options 7 and 8
- artifacts/use_case_diagram.puml — Updated use cases for new commands

### Test Result
✅ All 100 tests passed (57 pre-existing + 43 new)
- Task.is_completed() — 6 tests, all passing
- Task.mark_done() — 7 tests, all passing
- Task.mark_in_progress() — 6 tests, all passing
- Task.reopen() — 6 tests, all passing
- Status transitions — 4 tests, all passing
- is_overdue() after status changes — 4 tests, all passing
- CLI is-completed command — 5 tests, all passing
- CLI check-overdue command — 5 tests, all passing

### Implementation Details

**Methods Implemented:**
1. `Task.mark_in_progress() -> Task` — Sets status to IN_PROGRESS, updates updated_at timestamp, returns self
2. `Task.mark_done() -> Task` — Sets status to DONE, updates updated_at timestamp, returns self
3. `Task.reopen() -> Task` — Sets status to PENDING, updates updated_at timestamp, returns self
4. `Task.is_completed() -> bool` — Returns True if status is DONE, False otherwise

**CLI Commands Added:**
1. `python -m src is-completed <id>` — Check if task is completed
2. `python -m src check-overdue <id>` — Check if task is overdue

**Interactive Menu Options:**
- Option 7: Check if task is completed
- Option 8: Check if task is overdue

### Test Coverage
- ✅ All status transitions tested (PENDING ↔ IN_PROGRESS ↔ DONE)
- ✅ Timestamp updates verified (strictly increasing)
- ✅ Method chaining tested
- ✅ is_overdue() behavior after status changes
- ✅ CLI command integration
- ✅ Interactive menu functionality

Duration: 347.9s | Cost: $0.638082 USD | Turns: 15
