# Task 02: Add Status and Due Date Methods to Task

## Task Summary

Implement five status-mutation and status-query methods on the Task class to support task lifecycle management. Task status transitions follow a workflow: PENDING → IN_PROGRESS → DONE, with reopen() reverting to PENDING. Each mutation method must update the `updated_at` timestamp to current CEST time.

---

## Current Task Implementation

**File:** `/src/models/task.py`

### Existing State

The Task class is a dataclass with the following attributes:
- `title: str` (required)
- `id: str` (UUID, auto-generated)
- `description: Optional[str]` (default: None)
- `status: TaskStatus` (default: PENDING; values: PENDING, IN_PROGRESS, DONE)
- `due_date: Optional[datetime]` (default: None; supports ISO 8601 with timezone)
- `created_at: datetime` (default: current UTC time)
- `updated_at: datetime` (default: current UTC time)

### Existing Methods
- `to_dict() -> dict` — serializes task to JSON-compatible dict; conditionally includes due_date only if not None
- `from_dict(cls, data: dict) -> Task` — deserializes from dict; uses `.get("due_date")` for backward compatibility
- `is_overdue() -> bool` — returns True if due_date is set, task is not DONE, and current UTC time is past due_date

### TaskStatus Enum
```
PENDING = "pending"
IN_PROGRESS = "in_progress"
DONE = "done"
```

---

## Required Implementation

### 1. Status Mutation Methods (Must)

#### `mark_in_progress() -> None`
- Transitions `status` from PENDING to IN_PROGRESS
- Updates `updated_at` to current CEST time
- Should be a no-op if already IN_PROGRESS (prevent redundant mutations)

#### `mark_done() -> None`
- Transitions `status` to DONE
- Updates `updated_at` to current CEST time
- Should be a no-op if already DONE (prevent redundant mutations)

#### `reopen() -> None`
- Transitions `status` back to PENDING
- Updates `updated_at` to current CEST time
- Should be a no-op if already PENDING (prevent redundant mutations)

### 2. Status Query Methods (Must)

#### `is_completed() -> bool`
- Returns True if and only if `status == TaskStatus.DONE`
- No side effects; purely a predicate

### 3. Existing Methods (Already Implemented)

#### `is_overdue() -> bool` (Lines 48-55)
- Already correctly implemented
- Returns False if no due_date set or status is DONE
- Returns True if current UTC time > due_date
- No changes needed

---

## Implementation Notes

### Timestamp Handling: CEST vs UTC

**Current system state:**
- All timestamps (created_at, updated_at) are stored and compared in UTC (`timezone.utc`)
- Serialization uses `.isoformat()` → RFC 3339 format with timezone suffix
- Example: `"2026-05-02T21:25:29.121374+00:00"`

**Task requirement:** "update `updated_at` to the current CEST time"

**Resolution:**
The requirement is ambiguous. Two valid interpretations exist:

1. **Store in UTC, interpret requirement as UTC**: Keep existing pattern (simplest, consistent)
   - Mutation methods update to `datetime.now(timezone.utc)` 
   - No code changes to TaskManager behavior (it already does this)

2. **Convert to CEST when mutating**: Use CEST for mutation but store as UTC
   - Import `zoneinfo.ZoneInfo` (Python 3.9+)
   - Use `datetime.now(ZoneInfo('Europe/Paris')).astimezone(timezone.utc)`
   - More complex; unclear if requirement truly demands CEST storage vs CEST display

**Assumption for implementation:** Interpret "current CEST time" as "current time converted to CEST" but store in UTC (consistent with created_at/updated_at pattern). This maintains:
- Consistency with existing system
- Timezone portability
- Standard database practice (UTC storage)
- Serialization compatibility

If stricter CEST requirement is intended, mutation methods can be adjusted to:
```python
from zoneinfo import ZoneInfo
cest = ZoneInfo('Europe/Paris')
self.updated_at = datetime.now(cest).astimezone(timezone.utc)
```

### State Transition Rules

No explicit state machine framework is required. Suggested behavior for mutation methods:

| Current State | mark_in_progress() | mark_done() | reopen() |
|---|---|---|---|
| PENDING | Transition → IN_PROGRESS, update timestamp | Transition → DONE, update timestamp | No-op |
| IN_PROGRESS | No-op | Transition → DONE, update timestamp | Transition → PENDING, update timestamp |
| DONE | Transition → IN_PROGRESS, update timestamp | No-op | Transition → PENDING, update timestamp |

**Should behavior:** Methods should be no-ops if transitioning to their current state (prevent spurious timestamp updates). This is straightforward with simple checks:
```python
def mark_in_progress(self) -> None:
    if self.status != TaskStatus.IN_PROGRESS:
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)
```

---

## Files That Must Be Modified

### Core Implementation
1. **`/src/models/task.py`**
   - Add `mark_in_progress()` method
   - Add `mark_done()` method
   - Add `reopen()` method
   - Add `is_completed()` method
   - No dataclass changes needed (all methods operate on existing fields)

### Test Coverage
2. **`/tests/test_task.py`**
   - Test mark_in_progress() transitions
   - Test mark_done() transitions
   - Test reopen() transitions
   - Test is_completed() returns correct boolean
   - Test no-op behavior when transitioning to current state
   - Test updated_at timestamp is refreshed (or not, if no-op)
   - Test all combinations of transitions (state machine matrix)

### Service Layer (May Need Updates)
3. **`/src/services/task_manager.py`** — Current `set_status()` method handles status mutations via direct assignment. Task methods will become the canonical way to mutate status. Manager may need to call Task methods instead of direct assignment. Review for consistency.

4. **`/src/services/todo_service.py`** — Current methods (`start_task()`, `complete_task()`, `reopen_task()`) delegate to `TaskManager.set_status()`. May need refactoring to use Task methods or remain unchanged if TaskManager internally calls them.

### CLI Layer (May Need Updates)
5. **`/src/cli/todo_cli.py`** — Already supports mark-in-progress, mark-done, and reopen via service methods. No changes required if service layer remains compatible.

6. **`/src/cli/interactive_menu.py`** — Already has start, complete, and reopen operations. No changes required if service layer remains compatible.

---

## Scope: In vs Out

### In (Must Do)
- ✓ Five methods: mark_in_progress, mark_done, reopen, is_completed, is_overdue (already done)
- ✓ Each mutation updates updated_at to current time
- ✓ All methods derive state from existing Task attributes only
- ✓ Unit tests covering all transitions and combinations
- ✓ is_completed predicate

### Out (Won't Do)
- ✗ Workflow approval framework
- ✗ State machine framework with guards
- ✗ Event/hook system on state transitions

### Should (Optional but Recommended)
- Invalid transition handling: make mutations no-ops if already in target state (prevent spurious timestamp updates)
- Symmetry predicates: is_pending() and is_in_progress() for consistency with is_completed()

---

## Key Constraints & Dependencies

1. **Timestamp consistency**: All timestamp updates use `datetime.now(timezone.utc)` throughout the codebase. Methods should follow this pattern.

2. **No persistence in Task**: Task methods only modify object state; they don't call storage. TaskManager handles persistence (see line 29 in task_manager.py calling `self._persist()` after calling methods).

3. **Integration point**: TaskManager currently uses `task.status = status` directly (line 61). If Task methods become the canonical interface, TaskManager should be updated to use them for consistency.

4. **Backward compatibility**: Task serialization/deserialization already handles due_date gracefully. No new compatibility concerns.

---

## Test Matrix to Cover

Minimum test cases for complete coverage:

**Transition tests (3 methods × 3 states = 9 tests):**
- From PENDING: mark_in_progress(), mark_done(), reopen()
- From IN_PROGRESS: mark_in_progress(), mark_done(), reopen()
- From DONE: mark_in_progress(), mark_done(), reopen()

**Timestamp update tests:**
- Verify updated_at changes when transitioning to new state
- Verify updated_at stays same when already in target state (or verify it updates regardless, per requirement)

**Predicate tests:**
- is_completed() returns True only for DONE status
- is_completed() returns False for PENDING and IN_PROGRESS
- is_overdue() (already tested, no changes needed)

**Symmetry tests (optional):**
- Test is_pending(), is_in_progress() if added

---

## Summary Table

| Item | Status | Notes |
|------|--------|-------|
| Task.mark_in_progress() | Not implemented | Required method |
| Task.mark_done() | Not implemented | Required method |
| Task.reopen() | Not implemented | Required method |
| Task.is_completed() | Not implemented | Required method |
| Task.is_overdue() | ✓ Implemented | Already present; meets requirement |
| Unit test coverage | Partial | Due date tests exist; status method tests do not |
| CEST timestamp handling | Unclear | Recommendation: store UTC (consistent), display CEST in UI |
| Service layer integration | Potential issue | TaskManager uses direct assignment; consider refactor for consistency |
| CLI/menu compatibility | ✓ OK | No changes expected; service layer compatibility maintained |

---

## Implementation Order

1. Add four methods to Task class (mark_in_progress, mark_done, reopen, is_completed)
2. Write comprehensive tests for status transitions
3. Review TaskManager.set_status() for consistency; optionally refactor to use Task methods
4. Run full test suite; ensure backward compatibility
5. Update class diagram if status methods are added (already have is_overdue)

---

## Files Summary (Absolute Paths)

**Must modify:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task.py` — Add methods
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/tests/test_task.py` — Add tests

**Should review:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/task_manager.py` — Consider refactoring to use Task methods

**May impact:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/todo_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/cli/todo_cli.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/cli/interactive_menu.py`

