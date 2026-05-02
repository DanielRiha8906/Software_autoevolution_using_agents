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

Duration: PENDING | Cost: PENDING | Turns: PENDING
