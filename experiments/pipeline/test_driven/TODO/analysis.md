# Task 02 Analysis: Status Methods on Task Model

## Current State

### Task Model Structure (src/models/task.py)
- Dataclass with fields: title, id, description, status, created_at, updated_at, due_date
- CEST timezone constant defined at module level (UTC+2)
- Current defaults use UTC for created_at and updated_at
- Due date validation enforces CEST timezone if set

### TaskStatus Enum (src/models/task_status.py)
- Simple enum: PENDING, IN_PROGRESS, DONE

### Existing Test Coverage
- 40 tests in test_task.py covering Task defaults, serialization, and due_date handling

## Task 02 Requirements

### Mutation Methods (must update status and updated_at to CEST now)
1. `mark_in_progress()` - transitions status to IN_PROGRESS
2. `mark_done()` - transitions status to DONE
3. `reopen()` - transitions status back to PENDING

### Query Methods (read-only state checks)
1. `is_completed()` - returns True if status == DONE
2. `is_overdue()` - returns True if due_date is set AND due_date < now (CEST) AND task not completed
3. `is_pending()` - returns True if status == PENDING
4. `is_in_progress()` - returns True if status == IN_PROGRESS

## Test Suite (test_task_02.py) - 17 tests

Key test requirements:
- `mark_in_progress()`, `mark_done()`, `reopen()` change status appropriately
- Status mutations must update `updated_at` timestamp
- Status mutations must set `updated_at` timezone to CEST (UTC+2)
- `is_overdue()` returns False when no due_date
- `is_overdue()` returns True for past due_date, False for future due_date
- `reopen()` on PENDING task either no-ops or raises (test accepts both)

## Implementation Notes

### Key Constraints
1. All state must derive strictly from existing Task attributes
2. Mutations must set `updated_at` to current CEST time (not UTC)
3. `updated_at` must remain timezone-aware after mutations
4. `is_overdue()` uses CEST for current time comparison
5. `is_overdue()` returns False when due_date is None
6. Do not modify Task dataclass structure or existing fields
7. Do not modify TaskStatus enum

### State Machine (implied by tests)
- PENDING → IN_PROGRESS (via mark_in_progress)
- IN_PROGRESS → DONE (via mark_done)
- PENDING → DONE (via mark_done)
- DONE → PENDING (via reopen)
- IN_PROGRESS → PENDING (via reopen)
- No validation - transitions are permissive

### Timezone Handling
- Current implementation initializes updated_at to UTC now
- Mutations must convert updated_at to CEST now
- Comparison in is_overdue() must use CEST timezone
- Use `datetime.now(tz=CEST)` to get current CEST time

## Files to Modify
- `src/models/task.py` - add 7 new methods to Task class

## Files to Keep Unchanged
- `src/models/task_status.py` - no changes needed
- `src/models/task_manager.py` - status logic moves from here to Task, but TaskManager doesn't need changes yet
- Test files - no changes except running them

## Existing Tests Impact
All 40 existing tests should continue to pass after these changes since:
- No dataclass fields are changed
- No existing methods are modified
- Only new methods are added
