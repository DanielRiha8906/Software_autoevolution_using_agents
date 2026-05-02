# Task 02: Add Status and Due Date Methods to Task — Design

**Date:** 2026-05-02  
**Status:** Design complete

---

## Overview

Add four methods to the Task class that encapsulate status transitions with automatic `updated_at` timestamp updates in CEST timezone. All methods validate state transitions to prevent invalid workflow states.

## Method Signatures

### mark_in_progress()
```python
def mark_in_progress(self) -> None:
    """
    Transition task status to IN_PROGRESS.
    
    Valid transition: PENDING → IN_PROGRESS
    Updates updated_at to current CEST time.
    
    Raises:
        ValueError: If current status is not PENDING
    """
```

### mark_done()
```python
def mark_done(self) -> None:
    """
    Transition task status to DONE.
    
    Valid transition: IN_PROGRESS → DONE
    Updates updated_at to current CEST time.
    
    Raises:
        ValueError: If current status is not IN_PROGRESS
    """
```

### reopen()
```python
def reopen(self) -> None:
    """
    Transition task status back to PENDING.
    
    Valid transition: DONE → PENDING
    Updates updated_at to current CEST time.
    
    Raises:
        ValueError: If current status is not DONE
    """
```

### is_completed()
```python
def is_completed(self) -> bool:
    """
    Check if task is completed.
    
    Returns:
        True if status is DONE, False otherwise
    """
```

## Implementation Details

### State Transitions
Valid transitions (enforced by methods):
- PENDING → IN_PROGRESS (via `mark_in_progress()`)
- IN_PROGRESS → DONE (via `mark_done()`)
- DONE → PENDING (via `reopen()`)

All other transitions raise `ValueError` with message format:
```
"Cannot transition from {current_status} to {target_status}"
```

### CEST Timezone
All mutation methods update `updated_at` to:
```python
cest = timezone(timedelta(hours=2))
self.updated_at = datetime.now(cest)
```

This is consistent with the existing `is_overdue()` method.

### Error Handling
- Raise `ValueError` when invalid transitions are attempted
- Use enum.value to display status strings (e.g., "pending", "in_progress", "done")

## Files to Modify

### 1. src/models/task.py
Add four methods to the Task class (after existing methods).

**Changes:**
- Add `mark_in_progress()` method with PENDING→IN_PROGRESS validation
- Add `mark_done()` method with IN_PROGRESS→DONE validation
- Add `reopen()` method with DONE→PENDING validation
- Add `is_completed()` method returning bool

### 2. tests/test_task.py
Add 19 test functions covering:

**mark_in_progress() tests:**
- test_mark_in_progress_from_pending() — Valid transition
- test_mark_in_progress_from_in_progress_raises_error() — Invalid
- test_mark_in_progress_from_done_raises_error() — Invalid
- test_mark_in_progress_updates_timestamp_to_cest() — Timezone check

**mark_done() tests:**
- test_mark_done_from_in_progress() — Valid transition
- test_mark_done_from_pending_raises_error() — Invalid
- test_mark_done_from_done_raises_error() — Invalid
- test_mark_done_updates_timestamp_to_cest() — Timezone check

**reopen() tests:**
- test_reopen_from_done() — Valid transition
- test_reopen_from_pending_raises_error() — Invalid
- test_reopen_from_in_progress_raises_error() — Invalid
- test_reopen_updates_timestamp_to_cest() — Timezone check

**is_completed() tests:**
- test_is_completed_when_done() — Returns True
- test_is_completed_when_pending() — Returns False
- test_is_completed_when_in_progress() — Returns False

**Integration tests:**
- test_full_transition_cycle_pending_to_done() — PENDING→IN_PROGRESS→DONE
- test_full_transition_cycle_with_reopen() — Full cycle including reopen

**Serialization tests:**
- test_status_preserved_through_serialization_after_mark_in_progress()
- test_timestamp_preserved_through_serialization_after_mark_done()

### 3. artifacts/class_diagram.puml
Update Task class definition to include four new methods:
- `markInProgress() : void`
- `markDone() : void`
- `reopen() : void`
- `isCompleted() : Boolean`

Note: PlantUML uses camelCase; Python uses snake_case.

## Design Decisions

### State Validation at Model Layer
Enforce valid transitions in methods rather than service layer. Prevents invalid states at the source. Provides immediate feedback to callers.

### CEST for updated_at Only
Set `updated_at` to CEST (UTC+2) in mutation methods. Keep `created_at` in UTC (immutable creation timestamp). This follows the existing `is_overdue()` pattern and aligns with requirement specifications.

### None Return Type
Mutation methods return None; they mutate the task in-place. This is standard Python pattern for side-effecting operations. Service layer can handle any return values if needed.

### ValueError for Invalid Transitions
Use standard Python `ValueError` exception. No custom exception needed. Error messages include both current and target status for clarity.

## Test Strategy

### Coverage
- Happy path: each valid transition tested
- Invalid transitions: each invalid transition raises ValueError
- Timezone: CEST offset verified after each mutation
- Integration: multi-step transitions in sequence
- Serialization: status and timestamps survive roundtrip

### Edge Cases
- Attempting to mark already-done task as done
- Attempting to reopen already-pending task
- Chained transitions validating each step

## Implementation Order

1. Add methods to src/models/task.py
2. Add tests to tests/test_task.py
3. Update artifacts/class_diagram.puml
4. Run pytest to verify all tests pass
