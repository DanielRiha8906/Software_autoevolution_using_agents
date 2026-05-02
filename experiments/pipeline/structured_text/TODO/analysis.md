# Task 02: Implement Task Status Predicates and State Transitions — Analysis Report

**Date:** 2026-05-02  
**Status:** Analysis complete

---

## What the Task is Asking For

Implement five new methods on the Task class that manage status transitions and state queries:
1. **`mark_in_progress()`** — transition status from any state to IN_PROGRESS
2. **`mark_done()`** — transition status to DONE
3. **`reopen()`** — transition status back to PENDING
4. **`is_completed()`** — query whether status is DONE
5. **`is_overdue()`** — query whether due_date is set and in the past (already exists)

Each status-mutating method must update `updated_at` to the current CEST time. Methods must derive their behavior strictly from existing Task attributes (status, due_date, updated_at). The implementation should prevent invalid status transitions (SHOULD requirement), add comprehensive unit tests (SHOULD requirement), and optionally add symmetrical predicates for PENDING and IN_PROGRESS states (COULD requirement).

---

## Current Task Class Structure

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task.py`

### Current Attributes
```
task.id: str (UUID, auto-generated)
task.title: str (required)
task.description: Optional[str] (defaults to None)
task.status: TaskStatus (enum: PENDING, IN_PROGRESS, DONE)
task.created_at: datetime (UTC, auto-generated at creation)
task.updated_at: datetime (UTC, auto-generated at creation, updated on mutations)
task.due_date: Optional[datetime] (CEST timezone-aware, defaults to None, added in Task 01)
```

### Current Methods
- `to_dict() -> dict` — serializes Task to JSON-compatible dict
- `from_dict(data: dict) -> Task` — reconstructs Task from dict
- `is_overdue() -> bool` — returns True if due_date is set and earlier than current CEST time

---

## Status Enum Definition

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task_status.py`

```python
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
```

---

## Current Due Date Handling

Task 01 already implemented `due_date` as `Optional[datetime]` with CEST (UTC+2) timezone support. The `is_overdue()` method is implemented:

```python
def is_overdue(self) -> bool:
    """Check if task is overdue (due_date is in the past in CEST timezone)."""
    if self.due_date is None:
        return False
    cest = timezone(timedelta(hours=2))
    now = datetime.now(cest)
    return self.due_date < now
```

---

## State Transition Model

Per the state diagram in `artifacts/state_diagram.puml`:

```
[*] --> PENDING
PENDING --> IN_PROGRESS (via mark_in_progress or start)
IN_PROGRESS --> DONE (via mark_done or complete)
DONE --> IN_PROGRESS (not directly reachable via reopen, which goes to PENDING)
PENDING --> PENDING (reopen on PENDING is a no-op or error)
IN_PROGRESS --> IN_PROGRESS (mark_in_progress on IN_PROGRESS is a no-op)
DONE --> DONE (mark_done on DONE is a no-op)
```

Note: The state diagram shows `reopen` transitions DONE → IN_PROGRESS, but the task requirements state `reopen()` should transition to PENDING. This is a discrepancy that must be resolved by the next agent.

---

## Methods to Implement on Task Class

### 1. `mark_in_progress() -> None`
- **Purpose:** Transition task status to IN_PROGRESS
- **Signature:** `def mark_in_progress(self) -> None:`
- **Behavior:**
  - Set `self.status = TaskStatus.IN_PROGRESS`
  - Update `self.updated_at = datetime.now(timezone(timedelta(hours=2)))` (CEST)
  - If already IN_PROGRESS, should be a no-op (or raise, per SHOULD requirement)
- **Preconditions:** None (any status can transition to IN_PROGRESS)
- **Side effects:** Mutates self; persists via caller

### 2. `mark_done() -> None`
- **Purpose:** Transition task status to DONE
- **Signature:** `def mark_done(self) -> None:`
- **Behavior:**
  - Set `self.status = TaskStatus.DONE`
  - Update `self.updated_at = datetime.now(timezone(timedelta(hours=2)))` (CEST)
  - If already DONE, should be a no-op (or raise)
- **Preconditions:** None (any status can transition to DONE)
- **Side effects:** Mutates self; persists via caller

### 3. `reopen() -> None`
- **Purpose:** Transition task status to PENDING (reopen a closed or in-progress task)
- **Signature:** `def reopen(self) -> None:`
- **Behavior:**
  - Set `self.status = TaskStatus.PENDING`
  - Update `self.updated_at = datetime.now(timezone(timedelta(hours=2)))` (CEST)
  - If already PENDING, should be a no-op (or raise)
- **Preconditions:** None (any status can reopen to PENDING)
- **Side effects:** Mutates self; persists via caller

### 4. `is_completed() -> bool`
- **Purpose:** Check if task is in DONE state
- **Signature:** `def is_completed(self) -> bool:`
- **Behavior:**
  - Return `True` if `self.status == TaskStatus.DONE`
  - Return `False` otherwise
- **Pure function:** No side effects

### 5. `is_overdue() -> bool` (Already exists)
- **Purpose:** Check if task is overdue
- **Current implementation** is correct per Task 01
- **No changes needed** for Task 02

---

## CEST Timezone Handling

All datetime updates must use CEST (UTC+2 fixed offset), not UTC:

```python
from datetime import datetime, timezone, timedelta

cest = timezone(timedelta(hours=2))
now = datetime.now(cest)
```

Currently, `updated_at` is set to UTC in TaskManager (`datetime.now(timezone.utc)`). The Task methods should use CEST directly when they update `updated_at`.

---

## Validation & Invalid Transitions (SHOULD Requirement)

Methods should prevent or warn about invalid transitions:

1. **No-op transitions:** 
   - `mark_in_progress()` on an already IN_PROGRESS task
   - `mark_done()` on an already DONE task
   - `reopen()` on an already PENDING task

2. **Options for handling:**
   - **Option A (Silent no-op):** Silently return without changing status or updated_at
   - **Option B (Raise):** Raise a custom exception (e.g., `InvalidStatusTransition`) with a clear message
   - **Option C (Conditional update):** Only update `updated_at` if status actually changed

3. **Recommendation:** Option A (silent no-op) is idempotent and user-friendly. Implement it unless tests specify otherwise.

---

## Test Requirements

### Unit Tests to Add (test_task.py)

Must cover:
1. **Status transitions from each initial state:**
   - `test_mark_in_progress_from_pending()`
   - `test_mark_in_progress_from_done()`
   - `test_mark_in_progress_idempotent()` (SHOULD: no-op when already IN_PROGRESS)
   - `test_mark_done_from_pending()`
   - `test_mark_done_from_in_progress()`
   - `test_mark_done_idempotent()` (SHOULD: no-op when already DONE)
   - `test_reopen_from_in_progress()`
   - `test_reopen_from_done()`
   - `test_reopen_idempotent()` (SHOULD: no-op when already PENDING)

2. **Predicate methods:**
   - `test_is_completed_returns_true_when_done()`
   - `test_is_completed_returns_false_when_pending()`
   - `test_is_completed_returns_false_when_in_progress()`

3. **`updated_at` timestamp behavior:**
   - `test_mark_in_progress_updates_timestamp()`
   - `test_mark_done_updates_timestamp()`
   - `test_reopen_updates_timestamp()`
   - Verify new `updated_at` > old `updated_at`

4. **Timezone correctness (CEST):**
   - Verify `updated_at` is set with correct offset (+02:00 or equivalent)
   - Or test that CEST comparison works correctly

5. **Idempotence (SHOULD):**
   - Calling a transition method twice should not change `updated_at` the second time (or should be a no-op)

### Test Patterns

Tests should follow the existing pattern in `test_task.py`:
- Import `pytest`, `datetime`, `timezone`, `timedelta`, `Task`, `TaskStatus`
- Create tasks with default or explicit status
- Call method
- Assert status changed and `updated_at` was updated
- For predicates, assert boolean return value

Example pattern:
```python
def test_mark_in_progress_from_pending():
    task = Task(title="Do work", status=TaskStatus.PENDING)
    old_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > old_updated_at
```

---

## Integration Points (Service Layer)

The Task methods are **on the Task class itself** (instance methods), not on TaskManager or TodoService. However, the service layer may use them:

**Current service patterns:**
- `TaskManager.set_status()` directly mutates `task.status` and `task.updated_at`
- `TodoService.start_task()`, `complete_task()`, `reopen_task()` call `TaskManager.set_status()`

**Post-Task-02 integration:**
- Service methods may call Task instance methods instead of direct mutation
- Or Task methods may be used in tests to verify service behavior indirectly
- No changes to service signatures are required by this task

---

## Special Handling Required

### 1. Timezone: CEST vs UTC
- **Current state:** Task creation and updates in TaskManager use UTC (`timezone.utc`)
- **Task 02 requirement:** Status-mutating methods use CEST (`timezone(timedelta(hours=2))`)
- **Implication:** After `mark_in_progress()`, `updated_at` will have a +02:00 offset; subsequent updates may differ
- **Decision:** This is intentional; Task methods are independent of the service layer

### 2. Immutability vs Mutability
- Task is a mutable dataclass, not frozen
- These methods mutate `self.status` and `self.updated_at` in-place
- Callers (TaskManager, tests) are responsible for persisting changes

### 3. Return Type Convention
- All three transition methods (`mark_in_progress`, `mark_done`, `reopen`) should return `None` (not `self`)
- This follows Python conventions and prevents accidental chaining
- The predicates (`is_completed`, `is_overdue`) return `bool`

---

## Potential Ambiguities

### 1. Idempotence vs Exception Raising
**Ambiguity:** Should a no-op transition raise an exception or silently return?

**Evidence:**
- SHOULD requirement says "prevent invalid status transitions"
- "prevent" could mean raise, or could mean make a no-op
- Current service layer uses `set_status()` which performs no validation

**Assumption:** Implement silent no-ops (idempotent). If tests require exceptions, that will be caught in the pytest-tester step.

### 2. CEST Offset vs Daylight Saving
**Ambiguity:** CEST is Central European **Summer** Time (UTC+2). Winter is CET (UTC+1).

**Current evidence:**
- Task 01 used a fixed +2 offset (`timezone(timedelta(hours=2))`)
- UML diagram shows DateTime without specifying DST handling
- Requirement says "CEST timezone-aware datetime"

**Assumption:** Use the same fixed +2 offset as Task 01. A full DST-aware solution would require `zoneinfo` (Python 3.9+) and is out of scope.

### 3. State Diagram Inconsistency
**Ambiguity:** The state diagram in artifacts/state_diagram.puml shows:
```
DONE --> IN_PROGRESS : reopen
```

But the task requirement says `reopen()` transitions to PENDING.

**Evidence:**
- Task requirements explicitly state: "reopen() — transitions status to PENDING"
- State diagram shows reopen → IN_PROGRESS
- Current TodoService.reopen_task() calls `set_status(..., TaskStatus.PENDING)`

**Assumption:** Follow the task requirement: `reopen()` transitions to PENDING, not IN_PROGRESS. The diagram is outdated and will be corrected in the UML-designer step.

---

## Scope Summary

### In Scope
- Implement five methods on Task: `mark_in_progress()`, `mark_done()`, `reopen()`, `is_completed()`, and verify `is_overdue()`
- Each status-mutating method updates `updated_at` to CEST time
- Idempotent behavior: no-op transitions don't change state or timestamp
- Comprehensive unit tests covering all transitions, predicates, and edge cases
- CEST timezone handling (fixed +2 offset)

### Out of Scope
- Changes to TaskManager or TodoService (they already exist and work)
- Daylight saving time auto-detection
- Workflow approval framework or state machine library
- Persistence changes (handled by caller via TaskManager)
- CLI or interactive menu updates (not required by this task)

### Borderline (COULD-Have)
- Add `is_pending()` and `is_in_progress()` predicates for symmetry with `is_completed()`
  - Task requirement explicitly lists this as optional
  - Recommend implementing if time permits; add tests if done

---

## Implementation Priority

1. **First:** Implement the five methods on Task class
   - `mark_in_progress()`, `mark_done()`, `reopen()` with status and timestamp updates
   - `is_completed()` as a simple boolean check
   - Verify `is_overdue()` is correct
   
2. **Second:** Write comprehensive unit tests
   - All 9+ status transition test cases
   - 3 predicate test cases
   - Timestamp update verification
   - Idempotence tests for no-op transitions
   
3. **Third (COULD):** Add optional predicates
   - `is_pending()` and `is_in_progress()` for symmetry
   - Add corresponding test cases if implemented

4. **Fourth:** Update UML class diagram
   - Add new method signatures
   - Correct state diagram to show reopen → PENDING (not IN_PROGRESS)

---

## File Paths & Dependencies

### Primary File to Modify
- **Task model:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task.py`
  - Add methods here; no imports needed beyond current (datetime, timezone, timedelta, TaskStatus)

### Test File to Modify
- **Task tests:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/tests/test_task.py`
  - Add 9+ new test functions
  - Follow existing pattern (Task creation, method call, assertion)

### Diagram Files to Update
- **Class diagram:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/artifacts/class_diagram.puml`
  - Add method signatures to Task class
  
- **State diagram:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/artifacts/state_diagram.puml`
  - Correct reopen transition to PENDING (not IN_PROGRESS)

### No Changes Needed
- TaskManager, TodoService, CLI modules
- Storage layer
- Baseline files
- Governance files (CLAUDE.md, prompts/, agents/)

---

## Summary of Methods to Implement

| Method | Signature | Returns | Mutates | Purpose |
|--------|-----------|---------|---------|---------|
| `mark_in_progress` | `def mark_in_progress(self) -> None:` | None | status, updated_at | Transition to IN_PROGRESS, update timestamp to CEST |
| `mark_done` | `def mark_done(self) -> None:` | None | status, updated_at | Transition to DONE, update timestamp to CEST |
| `reopen` | `def reopen(self) -> None:` | None | status, updated_at | Transition to PENDING, update timestamp to CEST |
| `is_completed` | `def is_completed(self) -> bool:` | bool | none | Return True if status is DONE |
| `is_overdue` | (already exists) | bool | none | Return True if due_date set and in past |

---

## Expected Test Count

Current baseline: 59 tests (41 original + 18 for Task 01 due_date feature)

Expected after Task 02: ~70+ tests
- Add 9-13 tests for status transitions (including idempotence)
- Add 3 tests for is_completed predicate
- Add 2-3 tests for timestamp behavior
- Optional: 2 tests for is_pending/is_in_progress if implemented

