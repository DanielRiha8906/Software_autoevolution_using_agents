# TODO Application - Task Progress

## Task 01: Add optional `due_date` attribute to Task

### Status: Completed ✓

**Task number:** 01

**Files changed:**
- src/models/task.py
- src/services/task_manager.py
- src/services/todo_service.py
- artifacts/class_diagram.puml

**Test result:** ✓ All 41 tests passed (0 failures)

**Summary:**
- Added optional `due_date: Optional[datetime] = None` field to Task dataclass
- Implemented timezone validation in Task.__post_init__() to ensure due_date is timezone-aware
- Updated Task.to_dict() to conditionally include due_date (only when not None)
- Updated Task.from_dict() to gracefully handle missing due_date field (backward compatible)
- Extended TaskManager.update() to accept optional due_date parameter
- Extended TodoService.add_task() and update_task() to accept optional due_date parameter with validation
- Updated class_diagram.puml to reflect the new due_date field and updated method signatures
- All existing 41 tests pass, confirming full backward compatibility

**Acceptance Criteria Met:**
- ✓ Task has optional due_date attribute (None by default)
- ✓ Tasks without due_date load and behave correctly
- ✓ due_date is stored and loaded through storage layer
- ✓ Dates use timezone-aware datetime objects (timezone info preserved in ISO 8601 format)
- ✓ Invalid datetime values (non-datetime or naive datetime) are rejected in Task.__post_init__()
- ✓ Existing stored tasks lacking due_date field load without error (uses .get() in from_dict())

Duration: 278.1s | Cost: $0.497082 USD | Turns: 21

## Task 02: Add status transition and state-checking methods

### Status: Completed ✓

**Task number:** 02

**Files changed:**
- src/models/task.py
- tests/test_task.py
- artifacts/class_diagram.puml
- artifacts/state_diagram.puml

**Test result:** ✓ All 60 tests passed (0 failures)

**Summary:**
- Added CEST timezone constant to task.py: `CEST = timezone(timedelta(hours=2))` (UTC+2, fixed)
- Implemented 3 status-mutation methods with silent no-op on invalid transitions:
  - `mark_in_progress()`: Transitions PENDING → IN_PROGRESS, updates `updated_at` to CEST
  - `mark_done()`: Transitions IN_PROGRESS → DONE, updates `updated_at` to CEST
  - `reopen()`: Transitions DONE → PENDING, updates `updated_at` to CEST
- Implemented 4 predicate methods (read-only, no side effects):
  - `is_completed()`: Returns True if status is DONE
  - `is_pending()`: Returns True if status is PENDING
  - `is_in_progress()`: Returns True if status is IN_PROGRESS
  - `is_overdue()`: Returns False if due_date is None, else compares against current CEST time
- Added 19 new tests to test_task.py covering all transitions, predicates, and timestamp behavior
- Updated class_diagram.puml to show the 7 new methods in the Task class
- Updated state_diagram.puml to clarify transition method names and state-checking predicates

**Acceptance Criteria Met:**
- ✓ Task provides all required methods: mark_in_progress, mark_done, reopen, is_completed, is_overdue
- ✓ Each status-mutating method updates updated_at to current CEST time (UTC+2)
- ✓ Methods derive state strictly from existing Task attributes (no external input required)
- ✓ Invalid transitions are silent no-ops (do not update updated_at or state)
- ✓ Symmetry predicates provided: is_pending() and is_in_progress()
- ✓ All 60 tests pass (4 original + 23 from Task class + tests from other modules)
- ✓ No regression in existing functionality

**State Machine Enforced:**
- PENDING ↔ IN_PROGRESS ↔ DONE (linear forward)
- DONE ↔ PENDING (reopen transition)
- All invalid transitions silently ignored (no-op)

Duration: 300.2s | Cost: $0.497598 USD | Turns: 26
