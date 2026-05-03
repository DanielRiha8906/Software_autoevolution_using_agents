# Analysis: Add Status Transition Methods to Task Model

## Task Summary

Add seven instance methods to the `Task` class to enable status transitions and state queries:
- **Transition methods**: `mark_in_progress()`, `mark_done()`, `reopen()`
- **Query methods**: `is_completed()`, `is_overdue()`, `is_pending()`, `is_in_progress()`

All methods must derive state from existing Task attributes only and update `updated_at` to CEST (UTC+2) when mutations occur.

---

## Current Implementation Analysis

### 1. Task Model Structure (src/models/task.py)

**Current Attributes:**
- `id: str` — UUID (auto-generated)
- `title: str` — required task name
- `description: Optional[str]` — optional details
- `status: TaskStatus` — enum (PENDING, IN_PROGRESS, DONE)
- `created_at: datetime` — UTC timezone-aware, set at creation
- `updated_at: datetime` — UTC timezone-aware, set at creation
- `due_date: Optional[datetime]` — optional, timezone-aware (validated in `__post_init__`)

**Current Methods:**
- `__post_init__()` — validates that `due_date` is timezone-aware if provided
- `to_dict()` — serializes to dict (includes due_date only if not None)
- `from_dict(data: dict)` — deserializes from dict (handles missing due_date)

### 2. TaskStatus Enum (src/models/task_status.py)

```python
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
```

Three states as defined in the state diagram (artifacts/state_diagram.puml).

### 3. Current Status Transition Pattern

TaskManager (src/services/task_manager.py) currently handles all transitions externally:
- `set_status(task_id: str, status: TaskStatus) -> Task` — manually sets status and updates `updated_at` to UTC
- TodoService wraps this with semantic wrappers: `start_task()`, `complete_task()`, `reopen_task()`

This pattern keeps transitions stateless, but the requirement moves responsibility into the Task model itself.

---

## What Needs to Be Added to Task Class

### Transition Methods (Mutators)

These methods change internal state and update `updated_at` to CEST:

**1. `mark_in_progress() -> None`**
- Precondition: can be called from any state (no validation required)
- Sets `self.status = TaskStatus.IN_PROGRESS`
- Sets `self.updated_at` to current time in CEST
- Returns nothing

**2. `mark_done() -> None`**
- Precondition: can be called from any state
- Sets `self.status = TaskStatus.DONE`
- Sets `self.updated_at` to current time in CEST
- Returns nothing

**3. `reopen() -> None`**
- Precondition: can be called from any state
- Sets `self.status = TaskStatus.PENDING`
- Sets `self.updated_at` to current time in CEST
- Returns nothing

### Query Methods (Accessors)

These methods return boolean without mutation:

**4. `is_completed() -> bool`**
- Returns `self.status == TaskStatus.DONE`

**5. `is_pending() -> bool`**
- Returns `self.status == TaskStatus.PENDING`

**6. `is_in_progress() -> bool`**
- Returns `self.status == TaskStatus.IN_PROGRESS`

**7. `is_overdue() -> bool`**
- Returns `True` if:
  - `self.due_date` is not None AND
  - `self.due_date` < current time in CEST
- Returns `False` otherwise (no due_date or due_date is in future)

---

## Key Constraints & Dependencies

### 1. Timezone Handling: CEST (UTC+2)

The requirement specifies CEST throughout:
- Current implementation uses `timezone.utc` for `created_at` and `updated_at`
- The three mutation methods must set `updated_at` to **CEST**, not UTC
- Existing code in test_task.py shows CEST defined as `timezone(timedelta(hours=2))`
- `is_overdue()` must compare `due_date` against current time in CEST

**Import needed:**
```python
from datetime import timezone, timedelta
```

**CEST definition:**
```python
CEST = timezone(timedelta(hours=2))
```

### 2. State Mutation Only in Transition Methods

- Query methods must not modify any state
- Transition methods modify only `status` and `updated_at`
- No side effects beyond these two fields
- All other attributes remain unchanged

### 3. No Validation on Transitions

The requirement states "can be called from any state" implicitly. The state diagram shows valid transitions (PENDING→IN_PROGRESS→DONE→PENDING), but the requirement does not mandate enforcement. **Assumption:** transitions are unconditional (no state validation required).

### 4. Backward Compatibility

- Existing Task instances must continue to work
- Existing serialization (to_dict/from_dict) unaffected
- Existing tests in test_task.py must pass
- No changes to TaskManager or TodoService required by the requirement itself

---

## Files That Will Need Modification

### Primary File (Must Modify)
1. **src/models/task.py**
   - Add import: `from datetime import timezone, timedelta`
   - Define CEST constant: `CEST = timezone(timedelta(hours=2))`
   - Add all 7 methods to Task dataclass

### Test Files (Will Be Provided/Written)
1. **tests/test_task.py**
   - Tests for all 7 new methods will be added by pytest-tester
   - Existing tests must continue to pass

### Diagrams (Must Update)
1. **artifacts/class_diagram.puml**
   - Add the 7 new method signatures to Task class box
   - Show return types: transition methods return void, query methods return bool

### No Changes Required
- `src/models/task_status.py` — enum is complete
- `src/services/task_manager.py` — external transition logic unaffected
- `src/services/todo_service.py` — semantic wrappers unaffected
- `src/storage/json_storage.py` — serialization pattern unchanged
- `src/cli/` — CLI layer unaffected
- Existing test suites — should continue to pass

---

## Implementation Notes

### CEST vs UTC

**Current state:**
```python
created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

**After implementation:**
- `created_at` should remain UTC (no change required)
- `updated_at` will be set to CEST only when mutation methods are called
- Existing records created before this change will have UTC timestamps
- This mixed-timezone approach is acceptable per the requirement

### Method Implementation Pattern

Transition methods will follow this pattern:
```python
def mark_in_progress(self) -> None:
    self.status = TaskStatus.IN_PROGRESS
    self.updated_at = datetime.now(CEST)
```

Query methods:
```python
def is_completed(self) -> bool:
    return self.status == TaskStatus.DONE

def is_overdue(self) -> bool:
    if self.due_date is None:
        return False
    return self.due_date < datetime.now(CEST)
```

---

## Test Expectations

Based on the requirement statement "These tests must pass (provided in the task)":
- Tests will verify each method works correctly
- All 7 methods must be testable independently
- `updated_at` must be timezone-aware CEST after mutations
- `is_overdue()` must correctly compare timestamps in CEST
- All existing tests must continue to pass

**Example test patterns anticipated:**
- `mark_in_progress()` changes status from PENDING to IN_PROGRESS
- `updated_at` is set to current CEST (within 1 second)
- `is_overdue()` returns True for past due_dates, False for future
- `is_overdue()` returns False when due_date is None
- Query methods return correct boolean values

---

## Summary Table

| Method | Type | Mutates | Returns | CEST Required |
|--------|------|---------|---------|---------------|
| `mark_in_progress()` | Transition | ✓ status, updated_at | void | ✓ |
| `mark_done()` | Transition | ✓ status, updated_at | void | ✓ |
| `reopen()` | Transition | ✓ status, updated_at | void | ✓ |
| `is_completed()` | Query | ✗ | bool | ✗ |
| `is_pending()` | Query | ✗ | bool | ✗ |
| `is_in_progress()` | Query | ✗ | bool | ✗ |
| `is_overdue()` | Query | ✗ | bool | ✓ |

---

## Scope Summary

**In Scope:**
- Add 7 methods to Task class
- Use CEST for current time in mutations and is_overdue()
- Update class diagram with new method signatures

**Out of Scope:**
- State transition validation (no state guards required)
- Changes to TaskManager or TodoService
- Changes to storage layer
- CLI integration (beyond existing start/done/reopen commands)

**Ambiguities Resolved:**
- Assumption: Transitions are unconditional (no validation)
- Assumption: CEST is `timezone(timedelta(hours=2))`
- Assumption: Mixed UTC/CEST timestamps in same record are acceptable
