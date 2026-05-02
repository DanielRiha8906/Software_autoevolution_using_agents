# Status Transition Methods Implementation Analysis

## Task Overview

Implement status transition methods on the Task domain model (in `src/models/task.py`) to allow programmatic state changes with validation, timestamp updates, and predicate queries.

---

## Current Task Domain Model

### Task Class Structure (`src/models/task.py`)

**Type**: Python dataclass (immutable structure, mutable attributes)

**Current Attributes**:
```
- id: str (UUID, auto-generated)
- title: str (required)
- description: Optional[str] (nullable)
- status: TaskStatus (enum: PENDING, IN_PROGRESS, DONE)
- created_at: datetime (UTC timezone-aware, immutable after creation)
- updated_at: datetime (UTC timezone-aware, mutable)
- due_date: Optional[datetime] (timezone-aware, mutable, nullable)
```

**Existing Methods**:
- `to_dict()` → dict (serialization)
- `from_dict(data: dict)` → Task (deserialization, class method)

### TaskStatus Enum (`src/models/task_status.py`)

```
PENDING = "pending"         # Initial state, task not started
IN_PROGRESS = "in_progress" # Task is being worked on
DONE = "done"               # Task completed
```

### Datetime Behavior

**Current Implementation**:
- Uses `datetime.now(timezone.utc)` for default timestamps (UTC-based)
- Interactive menu has helper `_to_cest()` that converts UTC to CEST (UTC+2) for display only
- Storage uses ISO 8601 strings via `.isoformat()` and `datetime.fromisoformat()`

**Requirement**: Status-mutating methods must update `updated_at` to **current CEST time**
- This means either:
  - (A) Convert current UTC time to CEST and store as CEST datetime object
  - (B) Store UTC internally but interpret the requirement as "reflect CEST equivalent of current moment"
- **Assumption**: Store as UTC (consistent with existing `created_at` and `updated_at`), but interpret "current CEST time" as the current moment as would be observed in the CEST timezone.

---

## Valid State Transitions

Based on the state diagram artifact (`artifacts/state_diagram.puml`):

```
[*] → PENDING
PENDING → IN_PROGRESS : via start/mark_in_progress()
IN_PROGRESS → DONE : via complete/mark_done()
DONE → IN_PROGRESS : via reopen()

No direct transitions:
- PENDING → DONE (must go through IN_PROGRESS)
- IN_PROGRESS → PENDING (can only reopen from DONE)
- DONE → PENDING (should reopen to IN_PROGRESS instead)
```

---

## Required Methods

### Status-Mutating Methods (update `updated_at`)

1. **`mark_in_progress()`**
   - Signature: `def mark_in_progress(self) -> None`
   - Effect: `PENDING` → `IN_PROGRESS` or `DONE` → `IN_PROGRESS`
   - Invalid: No-op or raise error if already `IN_PROGRESS`
   - Updates: `self.status` and `self.updated_at` to current time (CEST)

2. **`mark_done()`**
   - Signature: `def mark_done(self) -> None`
   - Effect: `IN_PROGRESS` → `DONE`
   - Invalid: No-op or raise error if not `IN_PROGRESS`
   - Updates: `self.status` and `self.updated_at` to current time (CEST)

3. **`reopen()`**
   - Signature: `def reopen(self) -> None`
   - Effect: `DONE` → `IN_PROGRESS`
   - Invalid: No-op or raise error if not `DONE`
   - Updates: `self.status` and `self.updated_at` to current time (CEST)

### Predicate Methods (read-only, no side effects)

4. **`is_completed()`**
   - Signature: `def is_completed(self) -> bool`
   - Returns: `True` if `status == TaskStatus.DONE`, else `False`

5. **`is_overdue()`**
   - Signature: `def is_overdue(self) -> bool`
   - Returns: `True` if `due_date` is set AND `due_date < now` AND `status != DONE`, else `False`
   - Reasoning: Completed tasks are not overdue; overdue only applies to pending/in-progress work
   - Requires comparing current time with `self.due_date`

6. **`is_pending()`** (symmetry predicate)
   - Signature: `def is_pending(self) -> bool`
   - Returns: `True` if `status == TaskStatus.PENDING`, else `False`

7. **`is_in_progress()`** (symmetry predicate)
   - Signature: `def is_in_progress(self) -> bool`
   - Returns: `True` if `status == TaskStatus.IN_PROGRESS`, else `False`

---

## Behavior Specification

### Invalid Transitions

**Question**: How to handle invalid transitions?

**Options**:
- (A) Silently no-op (do nothing, return normally)
- (B) Raise a custom exception (e.g., `InvalidStatusTransitionError`)
- (C) Return a boolean indicating success

**Assumption**: Based on requirements saying "Invalid transitions are no-ops or raise errors," recommend:
- Implement as no-ops by default (method returns `None`, does nothing if invalid)
- Caller can check `is_completed()`, `is_pending()` before calling if strict validation needed
- If an exception is preferred, use a custom exception class like `InvalidStatusTransitionError`

### CEST Timezone Requirement

**Current Behavior**:
- `updated_at` is set via `datetime.now(timezone.utc)` (UTC timezone-aware)
- Interactive menu shows CEST via helper function `_to_cest()` that converts UTC to CEST for display

**Implementation Path**:
- Method: `datetime.now(timezone.utc)` already gives the current moment in UTC
- CEST equivalent: Create a timezone-aware datetime in CEST using `timezone(timedelta(hours=2))`
- Store as: Timezone-aware `datetime` object (either UTC or CEST, but must be consistent with existing code)

**Recommendation**: 
- Store as UTC (consistent with `created_at` and existing `updated_at` behavior)
- The requirement "update to current CEST time" means set to the current moment (which IS the current CEST moment if UTC is converted)
- No code change to existing storage/serialization needed; UTC storage is correct

---

## Test Pattern Analysis

From `tests/test_task.py` and `tests/test_task_manager.py`:

**Patterns Observed**:
1. **Fixture usage**: `tmp_path` for temporary storage in TaskManager tests
2. **Assertion style**: Direct equality checks (`assert x == y`)
3. **Exception testing**: `pytest.raises(ExceptionType)` context manager
4. **State verification**: Create object → perform action → assert attribute changed
5. **Serialization testing**: `task.to_dict()` → `Task.from_dict()` → compare attributes

**Expected Test Structure for New Methods**:
```python
def test_mark_in_progress_from_pending():
    task = Task(title="Test", status=TaskStatus.PENDING)
    original_updated_at = task.updated_at
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at > original_updated_at  # Or use freeze_time

def test_is_completed_true():
    task = Task(title="Test", status=TaskStatus.DONE)
    assert task.is_completed() == True

def test_invalid_transition_no_op():
    task = Task(title="Test", status=TaskStatus.IN_PROGRESS)
    task.mark_in_progress()  # Already IN_PROGRESS
    assert task.status == TaskStatus.IN_PROGRESS  # No change
```

---

## Imports and Dependencies

**Required Imports in Task Class**:
- `from datetime import datetime, timezone, timedelta` (already imported for `created_at`/`updated_at`)
- Possibly: `from .task_status import TaskStatus` (already imported)

**New Dependencies**:
- None (all needed imports already present or available in standard library)

---

## Edge Cases and Constraints

1. **Concurrent/Race Conditions**: Dataclass is not thread-safe; assume single-threaded access
2. **Timezone Ambiguity**: CEST is UTC+2; no DST handling (always assume UTC+2 offset)
3. **Due Date Comparison**: Must handle `None` value for `is_overdue()`
4. **Attribute Mutability**: Methods mutate `self.status` and `self.updated_at` directly (in-place)
5. **Serialization**: Methods don't affect `to_dict()`/`from_dict()` behavior (no new fields)

---

## Summary of Required Additions

### New Instance Methods on Task Class
- `mark_in_progress()` → None
- `mark_done()` → None
- `reopen()` → None
- `is_completed()` → bool
- `is_overdue()` → bool
- `is_pending()` → bool
- `is_in_progress()` → bool

### Files to Modify
- **`src/models/task.py`** — Add all 7 new methods

### Files NOT Modified
- `src/models/task_status.py` — No enum changes needed
- `src/services/task_manager.py` — No changes (uses Task object directly)
- `src/services/todo_service.py` — No changes
- `src/cli/` — No changes at this stage
- `src/storage/json_storage.py` — No changes

### Test Files to Create/Extend
- `tests/test_task.py` — Add comprehensive tests for all 7 methods

---

## Key Uncertainties and Assumptions

| Uncertainty | Assumption |
|---|---|
| Invalid transition behavior (no-op vs exception) | Implement as no-ops; silent success if already in target state |
| CEST timezone storage (UTC vs CEST) | Store as UTC (consistent with current code), interpret requirement as "current moment in CEST" |
| `is_overdue()` when due_date is None | Return `False` (task with no due date cannot be overdue) |
| `is_overdue()` when task is DONE | Return `False` (completed tasks are not overdue) |
| Datetime comparison precision (seconds vs microseconds) | Use standard `<` operator (microsecond precision is acceptable) |

---

## File Paths (Absolute)

**Primary File to Modify**:
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/models/task.py`

**Test File to Extend**:
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/tests/test_task.py`

**Reference Files** (read-only):
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/artifacts/state_diagram.puml`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/artifacts/class_diagram.puml`

