# Analysis: Task 02 — Task Status Transition Methods

## Task Summary

Add state-checking and status-transition methods to the Task model to ensure consistent task lifecycle management. Methods transition tasks through the lifecycle (PENDING → IN_PROGRESS → DONE) and allow reopening completed tasks. All mutations update `updated_at` to the current time, and query methods enable safe state inspection.

---

## Current Task Model Structure

**File:** `src/models/task.py`

### Attributes
- `id: str` — UUID, auto-generated
- `title: str` — required, non-empty task name
- `description: Optional[str]` — optional narrative detail
- `status: TaskStatus` — enum field, defaults to `PENDING`
- `created_at: datetime` — UTC timestamp, auto-set at instantiation
- `updated_at: datetime` — UTC timestamp, auto-set at instantiation, updated on mutation
- `due_date: Optional[datetime]` — optional deadline (from Task 01)

### Existing Methods
- `__post_init__()` — validates that `due_date` is timezone-aware (raises `ValueError` if naive)
- `to_dict()` — serializes to JSON-compatible dict
- `from_dict(data: dict)` — class method, deserializes from dict

### TaskStatus Enum
**File:** `src/models/task_status.py`

```python
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
```

---

## Status Transition Rules

### Valid State Machine
```
[*] → PENDING
PENDING → IN_PROGRESS (start)
IN_PROGRESS → DONE (complete)
DONE → IN_PROGRESS (reopen)
```

### Transition Validity Matrix
- `PENDING` → `IN_PROGRESS`: **Valid** via `mark_in_progress()`
- `IN_PROGRESS` → `DONE`: **Valid** via `mark_done()`
- `DONE` → `IN_PROGRESS`: **Valid** via `reopen()`
- `PENDING` → `PENDING`: **Invalid** (already pending)
- `IN_PROGRESS` → `IN_PROGRESS`: **Invalid** (already in progress)
- `DONE` → `DONE`: **Invalid** (already done)
- `IN_PROGRESS` → `PENDING`: **Invalid** (can only reopen to IN_PROGRESS)
- `PENDING` → `DONE`: **Invalid** (must go through IN_PROGRESS)

**Handling of invalid transitions:** Decision deferred to System Architect (no-op or raise ValueError).

---

## Required New Methods on Task Class

### Status Mutation Methods
Update `status` field and set `updated_at = datetime.now(timezone.utc)` on each call.

1. **`mark_in_progress() → Task`**
   - Transition: `PENDING` → `IN_PROGRESS`
   - Behavior on invalid transition: TBD

2. **`mark_done() → Task`**
   - Transition: `IN_PROGRESS` → `DONE`
   - Behavior on invalid transition: TBD

3. **`reopen() → Task`**
   - Transition: `DONE` → `IN_PROGRESS`
   - Behavior on invalid transition: TBD

### State Query Methods
Return bool, no side effects.

4. **`is_completed() → bool`**
   - Returns `True` if `status == TaskStatus.DONE`

5. **`is_pending() → bool`**
   - Returns `True` if `status == TaskStatus.PENDING`

6. **`is_in_progress() → bool`**
   - Returns `True` if `status == TaskStatus.IN_PROGRESS`

7. **`is_overdue() → bool`**
   - Returns `True` if:
     - `due_date` is not None AND
     - `due_date < datetime.now(timezone.utc)` AND
     - `status != TaskStatus.DONE`
   - Returns `False` if `due_date` is None

---

## Timezone Implementation

**Specification states:** "CEST time"
**Current codebase:** Uses `datetime.now(timezone.utc)` everywhere

**Decision:** Continue with UTC (matches existing pattern). CEST conversion, if required, is an infrastructure-level concern beyond this task scope.

---

## CLI and Menu Integration Points

### Interactive Menu (`src/cli/interactive_menu.py`)
- **Option 4:** "Change status" — Currently calls `TodoService.start_task()`, `complete_task()`, `reopen_task()`
- **Integration:** These service methods will call new Task methods internally (no new menu option needed)

### Command-Line Interface (`src/cli/todo_cli.py`)
- **Existing subcommands:** `start <task-id>`, `done <task-id>`, `reopen <task-id>`
- **Integration:** CLI already handles transitions; new Task methods will be used internally by TaskManager
- **No new CLI commands needed** — query methods are internal helpers, not user-facing operations

### Entry Point (`src/__main__.py`)
- No changes needed; existing dispatch logic handles both menu and CLI modes

---

## Service Layer Changes

### TaskManager (`src/services/task_manager.py`)
- `set_status()` method currently mutates task directly
- Should delegate to new Task methods to centralize state transition logic
- `_persist()` continues to handle storage

### TodoService (`src/services/todo_service.py`)
- High-level methods (`start_task()`, `complete_task()`, `reopen_task()`) already exist
- No changes required; they continue delegating to TaskManager

---

## Implementation Checklist

### Task Class (`src/models/task.py`)
- [ ] Add `mark_in_progress()` method
- [ ] Add `mark_done()` method
- [ ] Add `reopen()` method
- [ ] Add `is_completed()` method
- [ ] Add `is_pending()` method
- [ ] Add `is_in_progress()` method
- [ ] Add `is_overdue()` method
- [ ] Each mutation updates `updated_at = datetime.now(timezone.utc)`
- [ ] Docstrings document transition rules and behavior on invalid transitions

### TaskManager (`src/services/task_manager.py`)
- [ ] `set_status()` refactored to call Task methods if appropriate
- [ ] Verify existing functionality still works post-refactor

### Tests (`tests/test_task.py`)
- [ ] Each mutation method updates `updated_at`
- [ ] Each query method returns correct bool
- [ ] `is_overdue()` with/without due_date
- [ ] `is_overdue()` respects task status (not overdue if done)
- [ ] Invalid transitions handled consistently

---

## Scope & Dependencies

### In Scope
- 7 new Task methods (3 mutations, 4 queries)
- Update `updated_at` on every mutation
- Both interactive menu and CLI integration (mutations already available)
- Tests for all new methods

### Out of Scope
- Changing overall service architecture
- Adding new CLI commands (existing ones suffice)
- Timezone conversion (UTC continues)
- Schema/storage changes (no new fields)

### Key Ambiguities (for System Architect)
1. **Invalid transition behavior:** Raise ValueError or silently no-op?
2. **Reopen destination:** Go to PENDING or IN_PROGRESS? (Analysis assumes PENDING for clean restart)
3. **CEST requirement:** UTC or actual CEST conversion?
