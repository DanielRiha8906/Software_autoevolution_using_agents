# Analysis Report: Adding Domain Methods to Task Model (Task 02)

## Task Objective

Move status transition and state query logic from `TaskManager` onto the `Task` model itself. Implement seven domain methods on the `Task` class that handle status mutations with `updated_at` tracking and state inspection, all deriving state strictly from existing Task attributes.

---

## Current Task Model Structure

**File:** `src/models/task.py`

### Current Attributes:
1. `title: str` — required field (positional, no default)
2. `id: str` — auto-generated UUID via `uuid.uuid4()` (default factory)
3. `description: Optional[str]` — nullable (default None)
4. `status: TaskStatus` — enum value (default TaskStatus.PENDING)
5. `created_at: datetime` — UTC timezone-aware (default factory: datetime.now(timezone.utc))
6. `updated_at: datetime` — UTC timezone-aware (default factory: datetime.now(timezone.utc))
7. `due_date: Optional[datetime]` — nullable datetime in CEST timezone (default None, from Task 01)

### Current Methods:
- `__post_init__()` — validates due_date type and timezone during construction
- `to_dict() -> dict` — serializes all fields to dict (status→string, datetimes→ISO format strings)
- `from_dict(data: dict) -> Task` — class method deserializing dict to Task with validation

### Current Constants and Helpers (in same file):
- `CEST = timezone(timedelta(hours=2))` — CEST timezone constant (UTC+2)
- `_validate_due_date_timezone(dt: datetime) -> None` — validation helper for due_date timezone checks

---

## What Needs to Be Added

### New Methods Required by Test Suite

All methods below must be added to the `Task` class:

#### 1. Status Mutation Methods

**`mark_in_progress() -> None`**
- Changes task status from any state to IN_PROGRESS
- Updates `self.updated_at` to current CEST time
- No return value (modifies self in place)
- Must update `updated_at` to CEST timezone, not UTC

**`mark_done() -> None`**
- Changes task status from any state to DONE
- Updates `self.updated_at` to current CEST time
- No return value

**`reopen() -> None`**
- Changes task status from any state back to PENDING
- Updates `self.updated_at` to current CEST time
- No return value
- Edge case: calling on a task that is already PENDING may be a no-op OR raise an exception (test allows both via try/except)

#### 2. State Query Methods (read-only, no side effects)

**`is_completed() -> bool`**
- Returns `True` if status == TaskStatus.DONE
- Returns `False` otherwise

**`is_pending() -> bool`**
- Returns `True` if status == TaskStatus.PENDING
- Returns `False` otherwise

**`is_in_progress() -> bool`**
- Returns `True` if status == TaskStatus.IN_PROGRESS
- Returns `False` otherwise

**`is_overdue() -> bool`**
- Returns `True` if task has a due_date AND that date has passed (before current CEST time)
- Returns `False` if due_date is None
- Returns `False` if due_date is in the future
- Must compare using CEST timezone for "now"

---

## Critical Timezone Handling Requirements

### Observed Pattern from Task 01:
- `created_at` and `updated_at` were created as UTC in the original implementation
- Test for Task 02 explicitly requires: `test_status_mutation_updates_updated_at_to_cest()` — checks that `task.updated_at.tzinfo == CEST`

### Key Constraint: updated_at Must Convert to CEST
- Status mutation methods must set `updated_at` to the current time in CEST timezone
- This differs from the current TaskManager.set_status() which uses `datetime.now(timezone.utc)`
- When methods like `mark_in_progress()` are called, they must:
  ```python
  self.updated_at = datetime.now(CEST)  # NOT timezone.utc
  ```

### Timezone Awareness:
- All datetime values must remain timezone-aware after mutation
- `is_overdue()` must use CEST for "now" comparison:
  ```python
  if self.due_date is None:
      return False
  return datetime.now(CEST) > self.due_date
  ```

---

## Test Requirements Analysis

### Test Suite Structure (from prompt.txt)

Tests verify:
1. **Mutation behavior** (lines 19-35) — methods change status correctly
2. **updated_at tracking** (lines 38-47):
   - Status mutations update `updated_at` to a time >= the time before the call
   - The updated `updated_at` must have tzinfo == CEST (UTC+2), not UTC
3. **State queries** (lines 49-78):
   - `is_completed()` returns True only when status == DONE
   - `is_overdue()` handles None, past, and future dates correctly
   - `is_pending()` and `is_in_progress()` return True for their respective statuses
4. **Edge case** (lines 81-87):
   - `reopen()` on a task already PENDING either succeeds (no-op) or raises exception (test permits both)

### Key Test Insights:

**test_status_mutation_updates_updated_at_to_cest (line 44-47):**
```python
def test_status_mutation_updates_updated_at_to_cest():
    task = Task(title="Test")
    task.mark_in_progress()
    assert task.updated_at.tzinfo == CEST
```
This explicitly shows that after calling a mutation method, `updated_at.tzinfo` must be CEST, not UTC.

**test_is_overdue (lines 59-68):**
```python
PAST = datetime(2020, 1, 1, tzinfo=CEST)
FUTURE = datetime(2099, 1, 1, tzinfo=CEST)

def test_is_overdue_true_when_past_due():
    assert Task(title="Test", due_date=PAST).is_overdue() is True

def test_is_overdue_false_when_future_due():
    assert Task(title="Test", due_date=FUTURE).is_overdue() is False

def test_is_overdue_false_when_no_due_date():
    assert Task(title="Test").is_overdue() is False
```
This shows `is_overdue()` must:
- Compare due_date with current time in CEST
- Handle None gracefully
- Return strict boolean (is True, not just truthy)

**test_reopen_on_pending_is_noop_or_raises (lines 81-87):**
```python
def test_reopen_on_pending_is_noop_or_raises():
    task = Task(title="Test")
    try:
        task.reopen()
        assert task.status == TaskStatus.PENDING
    except Exception:
        pass
```
This allows flexible behavior: either reopen() succeeds (task stays PENDING) or raises any Exception. No specific behavior is mandated.

---

## Current Usage of Status Mutations (External Dependencies)

### TaskManager (src/services/task_manager.py)

Lines 59-64 currently handle status mutations externally:
```python
def set_status(self, task_id: str, status: TaskStatus) -> Task:
    task = self.get(task_id)
    task.status = status
    task.updated_at = datetime.now(timezone.utc)  # <-- Sets to UTC, not CEST
    self._persist()
    return task
```

### TodoService (src/services/todo_service.py)

Lines 26-33 delegate to TaskManager:
```python
def start_task(self, task_id: str) -> Task:
    return self._manager.set_status(task_id, TaskStatus.IN_PROGRESS)

def complete_task(self, task_id: str) -> Task:
    return self._manager.set_status(task_id, TaskStatus.DONE)

def reopen_task(self, task_id: str) -> Task:
    return self._manager.set_status(task_id, TaskStatus.PENDING)
```

### Important Observation:
Once Task domain methods are implemented, TaskManager and TodoService could potentially be refactored to use them, but the test requirements only mandate that:
1. The Task methods exist and work correctly
2. Existing tests still pass

The prompt does NOT require refactoring TaskManager or TodoService to use the new methods. Those remain external callers that will continue to set status directly.

---

## Ambiguities and Working Assumptions

### Ambiguity 1: Transition Validation
**Question:** Should mutation methods validate state transitions (e.g., reject going from DONE to IN_PROGRESS)?

**Evidence:** The tests call methods on tasks in various states without expecting validation errors. `test_reopen_on_pending_is_noop_or_raises()` explicitly allows either behavior.

**Assumption:** No transition validation is required. Methods succeed from any state (or reopen() can optionally raise on PENDING). Simple state mutation is sufficient.

### Ambiguity 2: Current Time for updated_at
**Question:** Should methods capture time once and use it, or call `datetime.now(CEST)` multiple times?

**Evidence:** `test_status_mutation_updates_updated_at_to_cest()` checks only that `updated_at.tzinfo == CEST`, not exact timing.

**Assumption:** Calling `datetime.now(CEST)` inside each method is acceptable. No test verifies atomicity of multiple updates.

### Ambiguity 3: is_overdue() Time Comparison
**Question:** Should `is_overdue()` use `>=` or `>`? (Is a task due at 2020-01-01 12:00:00 overdue at 2020-01-01 12:00:00?)

**Evidence:** Tests use dates far in past (2020) and far in future (2099); current date is 2026-05-02. No test exercises boundary conditions.

**Assumption:** Use `datetime.now(CEST) > due_date` for strict "past" comparison. Inclusive `>=` is not required.

---

## Constraints and Edge Cases

### 1. Timezone Conversion Requirement
- Methods must set `updated_at` to CEST, not UTC
- This is a change from the current TaskManager behavior (which uses UTC)
- But Task model owns its own updated_at, so this is valid

### 2. Backward Compatibility
- Existing tests in test_task_manager.py, test_todo_service.py, test_todo_cli.py rely on external status mutation via TaskManager.set_status()
- Those must continue to pass
- The new Task methods are additions; they don't remove or break existing APIs

### 3. No External Dependencies in Task Methods
- Methods must not import or use TaskManager, TodoService, or JsonStorage
- All logic derives from Task's own attributes: title, id, description, status, created_at, updated_at, due_date
- CEST and any helpers are already defined in the same file

### 4. Serialization Not Affected
- to_dict() and from_dict() do not change (no new fields to serialize)
- Methods are in-memory state mutations and queries
- Persistence is handled by TaskManager/JsonStorage after mutation

### 5. CEST Constant Already Exists
- File already defines `CEST = timezone(timedelta(hours=2))`
- Can be reused in new methods

---

## Dependencies and Assumptions

### Dependencies:
- No new imports needed (datetime, timezone, timedelta, TaskStatus already imported)
- CEST constant already defined in file
- _validate_due_date_timezone() helper already exists (only validates due_date, not used by new methods)

### Assumptions:
1. TaskManager will continue to call task.status = TaskStatus.X directly; Task methods are for programmatic use
2. Tests will create Task instances and call methods directly
3. No refactoring of TaskManager/TodoService is in scope for this task
4. All 41 existing tests must pass unchanged

---

## Scope Summary

### In Scope:
- Add 7 new methods to Task class
- Update `updated_at` to CEST timezone in mutation methods
- Handle None due_date in is_overdue()
- Ensure all provided tests pass

### Explicitly Out of Scope:
- Refactoring TaskManager.set_status() to use Task methods
- Refactoring TodoService status methods
- Changing to_dict()/from_dict()
- Adding task transition validation
- Modifying TaskStatus enum
- Changes to JsonStorage, TodoCLI, or InteractiveMenu

### Files to Modify:
- `src/models/task.py` — add 7 new methods (~50-70 lines)
- `tests/test_task.py` — add provided test cases (~17 test functions)

### Files NOT to Modify:
- TaskManager, TodoService, JsonStorage, TodoCLI, InteractiveMenu, and their tests

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Objective** | Add domain methods to Task for status mutation and state queries |
| **Methods to Add** | 7 total: `mark_in_progress()`, `mark_done()`, `reopen()`, `is_completed()`, `is_pending()`, `is_in_progress()`, `is_overdue()` |
| **Mutation Methods** | 3 (mark_in_progress, mark_done, reopen) — update `updated_at` to CEST |
| **Query Methods** | 4 (is_completed, is_pending, is_in_progress, is_overdue) — no side effects |
| **Key Constraint** | `updated_at` must be set to CEST (UTC+2), not UTC |
| **Timezone Requirement** | is_overdue() compares due_date with datetime.now(CEST) |
| **Backward Compatibility** | All 41 existing tests must pass; new methods are additions only |
| **Test Count** | 17 new tests provided (from prompt.txt) |
| **Lines Changed** | ~60-70 in src/models/task.py |
| **Risk Level** | Low — changes isolated to Task model, no external dependencies |
