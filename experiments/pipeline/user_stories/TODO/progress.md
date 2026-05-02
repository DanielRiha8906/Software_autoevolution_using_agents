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

## Task 02: Task Status Transition Methods

**Status:** COMPLETE ✓

### Changes Made
- **Task Model:** Added 7 new methods for status transitions and state queries:
  - `mark_in_progress()` — transitions PENDING → IN_PROGRESS (idempotent from IN_PROGRESS)
  - `mark_done()` — transitions IN_PROGRESS → DONE with validation
  - `reopen()` — transitions DONE → IN_PROGRESS with validation
  - `is_completed()`, `is_pending()`, `is_in_progress()` — status predicates
  - `is_overdue()` — checks due_date against current CEST time
- **Timezone handling:** All status-mutating methods update `updated_at` to current CEST (UTC+2) time
- **Validation:** Invalid transitions raise ValueError with descriptive messages
- **Diagrams:** Updated class_diagram.puml to include 7 new public methods

### Files Changed
- src/models/task.py
- tests/test_task.py
- artifacts/class_diagram.puml
- analysis.md (working document)
- design.md (working document)

### Test Results
**119 tests total: ALL PASSED**
- 30 new tests for Task status methods (4 mark_in_progress, 4 mark_done, 4 reopen, 3 is_completed, 3 is_pending, 3 is_in_progress, 6 is_overdue with timezone handling)
- All existing tests continue to pass

### Acceptance Criteria Verification
✓ Task provides `mark_in_progress()`, `mark_done()`, `reopen()` status transition methods
✓ Task provides `is_completed()`, `is_overdue()` state check methods
✓ Task provides `is_pending()`, `is_in_progress()` symmetry predicates
✓ All status-mutating methods update `updated_at` to current CEST time
✓ Methods derive state strictly from existing Task attributes
✓ Invalid transitions (e.g., reopen() on PENDING) raise ValueError
✓ Method chaining supported (all mutating methods return self)

Duration: 240.4s | Cost: $0.399010 USD | Turns: 14
