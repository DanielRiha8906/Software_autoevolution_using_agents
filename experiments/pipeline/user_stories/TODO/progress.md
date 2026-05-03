# TODO Application Progress — Pipeline / User Stories

## Task 01: Add Due Date Support

**Status:** COMPLETE ✓

### Changes Made
- **Task Model:** Added optional `due_date: Optional[datetime] = None` field with timezone-aware validation in `__post_init__()`
- **Serialization:** Updated `to_dict()` and `from_dict()` for ISO 8601 support with backward compatibility
- **TaskManager:** Added `due_date` parameter to `add()` and `update()` methods; added new `set_due_date()` method
- **TodoService:** Added `due_date` parameter to `add_task()` and `update_task()` with validation; added new `set_due_date()` method
- **TodoCLI:** Added `--due-date` flag to `add` and `update` subcommands; added new `due-date` subcommand; updated `show` to display due_date
- **InteractiveMenu:** Updated menu to include "Set due date" option; added prompts for due_date in add/update; added `_do_set_due_date()` method
- **Diagrams:** Updated class_diagram.puml, activity_diagram.puml, use_case_diagram.puml to reflect new due_date field and methods

### Files Changed
- src/models/task.py
- src/services/task_manager.py
- src/services/todo_service.py
- src/cli/todo_cli.py
- src/cli/interactive_menu.py
- artifacts/class_diagram.puml
- artifacts/activity_diagram.puml
- artifacts/use_case_diagram.puml

### Test Results
**89 tests total: ALL PASSED**
- 13 new tests for Task class (validation, serialization, backward compatibility)
- 8 new tests for TaskManager (due_date operations, persistence)
- 12 new tests for TodoService (validation, method operations)
- 2 new tests for backward compatibility (loading legacy tasks)
- 13 new tests for TodoCLI (command handling, display)

### Acceptance Criteria Verification
✓ Task has optional `due_date` attribute (None by default)
✓ Tasks without due_date load and behave correctly
✓ `due_date` is stored and loaded through storage layer
✓ Dates use timezone-aware ISO 8601 representation
✓ Invalid datetime values rejected before save
✓ Existing stored tasks without `due_date` field load without error

Duration: 614.7s | Cost: $1.099172 USD | Turns: 14

---

## Task 02: Task Status Transition Methods

**Status:** COMPLETE ✓

### Changes Made
- **Task Model:** Added 7 new methods for state management:
  - Query methods: `is_pending()`, `is_in_progress()`, `is_completed()`, `is_overdue()`
  - Mutation methods: `mark_in_progress()`, `mark_done()`, `reopen()`
  - All mutations update `updated_at` to current UTC timestamp
  - All mutations validate state transitions and raise ValueError on invalid transitions
  - Mutation methods return self for method chaining
- **TaskManager:** Refactored `set_status()` to call Task transition methods, enforcing state machine rules
- **TodoService:** Updated `reopen_task()` to transition to IN_PROGRESS (not PENDING), aligning with spec
- **Diagrams:** Updated class_diagram.puml to show all 7 new methods with proper signatures

### Files Changed
- src/models/task.py (7 new methods)
- src/services/task_manager.py (refactored set_status())
- src/services/todo_service.py (fixed reopen_task())
- artifacts/class_diagram.puml (added method signatures)

### Test Results
**131 tests total: ALL PASSED**
- 42 new tests for Task methods (valid transitions, invalid transitions, error messages)
- 3 tests for mark_in_progress() (valid + 2 invalid states)
- 3 tests for mark_done() (valid + 2 invalid states)
- 3 tests for reopen() (valid + 2 invalid states, goes to IN_PROGRESS not PENDING)
- 3 tests for updated_at timestamp verification on all mutations
- 3 tests each for is_pending(), is_in_progress(), is_completed()
- 6 tests for is_overdue() (None due_date, past/future dates, status override)
- 5 tests for TaskManager.set_status() integration
- 3 tests for TodoService integration (start, complete, reopen)
- 4 tests for error handling and method chaining

### Acceptance Criteria Verification
✓ Task provides clear methods: `mark_in_progress()`, `mark_done()`, `reopen()`, `is_completed()`, `is_overdue()`
✓ Additional symmetry methods: `is_pending()`, `is_in_progress()`
✓ Each status-mutating method updates `updated_at` to current UTC time
✓ Methods derive state strictly from existing Task attributes (no external input)
✓ Invalid transitions raise ValueError with descriptive messages (fail-fast)
✓ All functionality accessible via `python -m src` (interactive menu option 4 + CLI flags start/done/reopen)

Duration: PENDING | Cost: PENDING | Turns: PENDING
