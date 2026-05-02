# Progress Report

## Task 01: Due Date Support for Tasks

### Summary
Implemented optional due_date attribute for tasks with full support for creation, update, storage, and display.

### Files Changed
- src/models/task.py — Added due_date field, updated serialization
- src/services/todo_service.py — Added validation, extended method signatures
- src/services/task_manager.py — Updated add() and update() signatures
- src/cli/todo_cli.py — Added --due-date options and display
- src/cli/interactive_menu.py — Added prompts and CEST display
- tests/ — All 41 tests pass (backward compatible, no test modifications needed)
- artifacts/class_diagram.puml — Updated class signatures
- artifacts/activity_diagram.puml — Updated activity flows

### Test Result
✓ All 41 tests passed

### Acceptance Criteria Met
- ✓ Task has optional due_date attribute (None by default)
- ✓ Tasks without due_date load and behave correctly
- ✓ due_date stored and loaded through storage layer
- ✓ Dates use timezone-aware ISO 8601 representation in CEST (UTC+2)
- ✓ Invalid datetime values rejected before save
- ✓ Existing tasks without due_date field load without error

### Implementation Details
- Stores dates as UTC internally, displays as CEST (UTC+2)
- Validates ISO 8601 format in TodoService before save
- Supports loading legacy tasks without due_date field
- Added --due-date CLI options for add/update commands
- Interactive menu prompts for optional due_date and converts for display

Duration: 372.3s | Cost: $0.624776 USD | Turns: 14

## Task 02: Status Transition Methods

### Summary
Implemented explicit status transition methods on the Task class with validation, timestamp updates, and comprehensive predicates for cleaner state management.

### Files Changed
- src/models/task.py — Added 7 new methods (is_pending, is_in_progress, is_done, mark_in_progress, mark_done, reopen, _transition_to)
- tests/test_task.py — Added 41 comprehensive test cases covering all transitions, errors, and edge cases
- artifacts/state_diagram.puml — Updated transition labels to show method names (mark_in_progress, mark_done, reopen)
- artifacts/class_diagram.puml — Added all 7 new methods to Task class structure

### Test Result
✓ All 45 tests passed (4 original + 41 new)

### Acceptance Criteria Met
- ✓ Task provides: mark_in_progress(), mark_done(), reopen(), is_completed(), is_overdue(), is_pending(), is_in_progress()
- ✓ Each status-mutating method updates updated_at to current UTC time
- ✓ Methods derive state strictly from existing Task attributes
- ✓ Invalid transitions raise ValueError with descriptive error messages
- ✓ Predicate methods available for all states (is_pending, is_in_progress, is_done)

### Implementation Details
- Transition validation: strict (raises ValueError on invalid transitions, not idempotent)
- Valid transitions: PENDING → IN_PROGRESS → DONE, DONE/IN_PROGRESS → PENDING (via reopen)
- Timestamp updates: Always uses datetime.now(timezone.utc) on successful transitions
- Error messages match specification exactly
- All 41 new tests verify valid transitions, invalid transitions, timestamp updates, and serialization

Duration: 247.1s | Cost: $0.395894 USD | Turns: 15
