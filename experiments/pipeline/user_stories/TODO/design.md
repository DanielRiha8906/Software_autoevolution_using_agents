# Design: Task 02 — Task Status Transition Methods

## Design Decisions

### 1. Invalid Transition Handling
**Decision: Raise ValueError with clear message**
- Fail-fast ensures bugs are caught early
- Existing error handling in CLI/menu already catches ValueError
- Aligns with existing validation patterns (e.g., empty title check)

### 2. Reopen Destination State
**Decision: DONE → IN_PROGRESS**
- Per spec: `DONE → IN_PROGRESS (reopen)` in analysis.md
- "Reopen" semantically means resuming, not restarting
- Updates TodoService.reopen_task() to use IN_PROGRESS instead of PENDING

### 3. CEST Timezone vs UTC
**Decision: Continue with UTC**
- Matches existing codebase pattern (all timestamps use UTC)
- No external dependencies
- CEST is infrastructure concern, not business logic

### 4. TaskManager Integration
**Decision: Refactor set_status() to call Task methods**
- Centralizes state machine validation in Task class
- Prevents duplication of rules
- TaskManager handles persistence after Task methods update state

---

## Method Specifications

### Mutation Methods (return self, raise ValueError on invalid transition)

#### `mark_in_progress() -> Task`
- Transition: PENDING → IN_PROGRESS
- Updates: status, updated_at (current UTC)
- Error: "Cannot mark in_progress: task is already in {status}"

#### `mark_done() -> Task`
- Transition: IN_PROGRESS → DONE
- Updates: status, updated_at (current UTC)
- Error: "Cannot mark done: task is {status}"

#### `reopen() -> Task`
- Transition: DONE → IN_PROGRESS
- Updates: status, updated_at (current UTC)
- Error: "Cannot reopen: task is {status}"

### Query Methods (return bool, no side effects)

#### `is_pending() -> bool`
- Returns: status == TaskStatus.PENDING

#### `is_in_progress() -> bool`
- Returns: status == TaskStatus.IN_PROGRESS

#### `is_completed() -> bool`
- Returns: status == TaskStatus.DONE

#### `is_overdue() -> bool`
- Returns: False if due_date is None or status == DONE
- Returns: due_date < datetime.now(timezone.utc) otherwise

---

## Integration Points

### TaskManager.set_status() Refactoring
Pattern:
```python
def set_status(self, task_id: str, status: TaskStatus) -> Task:
    task = self.get(task_id)
    if status == TaskStatus.IN_PROGRESS and task.status == TaskStatus.PENDING:
        task.mark_in_progress()
    elif status == TaskStatus.DONE and task.status == TaskStatus.IN_PROGRESS:
        task.mark_done()
    elif status == TaskStatus.IN_PROGRESS and task.status == TaskStatus.DONE:
        task.reopen()
    elif task.status == status:
        raise ValueError(f"Task is already {status.value}")
    else:
        raise ValueError(f"Cannot transition from {task.status.value} to {status.value}")
    self._persist()
    return task
```

### TodoService.reopen_task() Fix
Change: `set_status(task_id, TaskStatus.PENDING)` → `set_status(task_id, TaskStatus.IN_PROGRESS)`

---

## Test Coverage

Total target: 37+ test cases across:
- Mutation methods: Valid transitions + 2 invalid states each (A-D: 12 tests)
- Query methods: True/false patterns (E-H: 18 tests)
- Integration: TaskManager and TodoService (I-J: 8 tests)
- Error handling: Messages and state preservation (K-L: 2 tests)

Key test groups:
- A1-A3: mark_in_progress() valid/invalid
- B1-B3: mark_done() valid/invalid
- C1-C3: reopen() valid/invalid
- D1-D3: updated_at timestamp verification
- E1-E3: is_pending() patterns
- F1-F3: is_in_progress() patterns
- G1-G3: is_completed() patterns
- H1-H6: is_overdue() edge cases (None, past, future, DONE status)
- I1-I5: TaskManager transitions via set_status()
- J1-J3: TodoService method integration
- K1-K2: Error messages and state corruption prevention
- L1: Method chaining (return self)

---

## Implementation Sequence

1. Add query methods to Task (is_pending, is_in_progress, is_completed, is_overdue)
2. Add mutation methods to Task (mark_in_progress, mark_done, reopen)
3. Refactor TaskManager.set_status() to use Task methods
4. Fix TodoService.reopen_task() to use IN_PROGRESS
5. Add tests for query methods
6. Add tests for mutation methods and updated_at
7. Add integration tests for TaskManager and TodoService
8. Add error handling and edge case tests

---

## Files to Change

1. **src/models/task.py** — Add 7 new methods after __post_init__()
2. **src/services/task_manager.py** — Refactor set_status() method
3. **src/services/todo_service.py** — Change PENDING to IN_PROGRESS in reopen_task()
4. **tests/test_task.py** — Add ~37 tests organized by group
