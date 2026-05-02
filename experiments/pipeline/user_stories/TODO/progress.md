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

## Task 02: Task Status Transition Methods

### Summary
Implemented status transition and state query methods on Task domain model to provide clear, consistent state management with automatic timestamp updates.

### Files Changed
- src/models/task.py — Added 7 new methods: mark_in_progress(), mark_done(), reopen(), is_completed(), is_pending(), is_in_progress(), is_overdue()
- tests/test_task.py — Added 26 comprehensive tests for all methods, transitions, and edge cases
- artifacts/class_diagram.puml — Updated Task class diagram with method signatures

### Test Result
✓ All 67 tests passed (30 new tests + 37 existing tests)

### Acceptance Criteria Met
- ✓ Task provides mark_in_progress(), mark_done(), reopen() with automatic updated_at updates
- ✓ Task provides is_completed(), is_pending(), is_in_progress(), is_overdue() predicates
- ✓ Each status-mutating method updates updated_at to current UTC time
- ✓ Methods derive state strictly from existing Task attributes
- ✓ Invalid transitions are silent no-ops (no exceptions)
- ✓ All state transition rules enforced: PENDING→IN_PROGRESS, IN_PROGRESS→DONE, DONE→IN_PROGRESS

### Implementation Details
- Status transitions: PENDING↔IN_PROGRESS, IN_PROGRESS→DONE, DONE→IN_PROGRESS
- Invalid transitions silently ignored (method returns None, does nothing)
- Timestamps stored as UTC (consistent with existing created_at behavior)
- is_overdue() returns False if: due_date is None, task is completed, or due_date is in future
- All predicates are read-only with no side effects

Duration: 227.6s | Cost: $0.402283 USD | Turns: 18
