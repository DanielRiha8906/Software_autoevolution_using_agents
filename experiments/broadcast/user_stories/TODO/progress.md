# Task 01: Add Due Date Support

## Task Overview

**User Story:** As a user managing my tasks, I want to assign a due date to a task, so that I can track deadlines and know when work is expected to be completed.

**Acceptance Criteria:**
- ✅ Task has an optional `due_date` attribute (`None` by default)
- ✅ Tasks without a due date load and behave correctly
- ✅ `due_date` is stored and loaded through the storage layer
- ✅ Dates use timezone-aware ISO 8601 representation in CEST (UTC+2)
- ✅ Providing an invalid datetime value is rejected before the task is saved
- ✅ Existing stored tasks that lack a `due_date` field load without error

## Implementation Results

### Candidate Evaluation

| Candidate | Approach | Tests Passing | Selection |
|-----------|----------|---------------|-----------|
| A (broadcast-candidate-a) | ZoneInfo with validation, ISO serialization with timezone preservation | 50/50 | **SELECTED** |
| B (broadcast-candidate-b) | ZoneInfo with validation, ISO serialization with timezone preservation | 50/50 | Equivalent |
| C (broadcast-candidate-c) | ZoneInfo with validation, ISO serialization with timezone preservation | 50/50 | Equivalent |

**Winner:** Candidate A (all candidates converged on identical implementation)

### Files Changed

1. **`src/models/task.py`**
   - Added `due_date: Optional[datetime] = None` field
   - Added `CEST = ZoneInfo("Europe/Paris")` constant
   - Implemented `__post_init__()` validation method:
     - Rejects non-datetime values
     - Rejects naive (timezone-unaware) datetimes
   - Updated `to_dict()` to serialize due_date with ISO 8601 format and timezone key preservation
   - Updated `from_dict()` to deserialize due_date with backward compatibility for tasks without the field

2. **`tests/test_task.py`**
   - Added 9 new comprehensive tests:
     - `test_task_with_due_date` — UTC timezone support
     - `test_task_with_cest_due_date` — CEST timezone support
     - `test_task_due_date_serialization` — ISO 8601 format verification
     - `test_task_due_date_roundtrip` — Serialization/deserialization integrity
     - `test_task_without_due_date_in_serialized` — Optional field handling
     - `test_task_backward_compatibility_no_due_date` — Legacy task loading
     - `test_task_validation_rejects_naive_datetime` — Timezone awareness requirement
     - `test_task_validation_rejects_non_datetime` — Type validation
     - `test_task_due_date_with_cest_serialization` — CEST roundtrip verification

3. **`artifacts/class_diagram.puml`**
   - Added `due_date : DateTime [0..1]` attribute to Task class
   - Added `__post_init__() : void` method to Task class
   - Fixed naming conventions for consistency (camelCase → snake_case)

### Test Results

```
..................................................                       [100%]
50 passed in 0.12s
```

### Design Decisions

1. **Validation Strategy:** Used dataclass `__post_init__()` hook to validate datetime type and timezone awareness at instantiation time, preventing invalid states from being saved.

2. **Serialization:** ISO 8601 with timezone key preservation:
   - Stores datetime as ISO string with offset (e.g., `2026-05-02T14:30:00+02:00`)
   - Additionally stores `due_date_tz` key if timezone is ZoneInfo, enabling proper reconstruction
   - Backward compatible: old tasks without the field load without error

3. **Timezone Handling:** Uses Python standard library `zoneinfo.ZoneInfo("Europe/Paris")` for CEST, which:
   - Automatically handles DST transitions
   - Is timezone-aware and preserves offset during serialization
   - Requires no external dependencies (available in Python 3.9+)

4. **Backward Compatibility:** 
   - `from_dict()` safely handles missing `due_date` field
   - Existing stored tasks load without error
   - Optional field omitted from JSON when None (compact serialization)

### Dependencies

No new dependencies added. Implementation uses Python standard library:
- `zoneinfo.ZoneInfo` (Python 3.9+)
- `datetime` module

Duration: 257.2s | Cost: $0.894447 USD | Turns: 35

---

# Task 02: Status Transition Methods

## Task Overview

**User Story:** As a developer working with the Task domain model, I want clear methods for transitioning task status and checking task state, so that status changes are consistent and all business rules are enforced in one place.

**Acceptance Criteria:**
- ✅ Task provides: `mark_in_progress()`, `mark_done()`, `reopen()`, `is_completed()`, `is_overdue()`
- ✅ Each status-mutating method updates `updated_at` to the current CEST time
- ✅ Methods derive state strictly from existing Task attributes — no external input required
- ✅ Invalid transitions (e.g. `reopen()` on a PENDING task) are either a no-op or raise an error
- ✅ `is_pending()` and `is_in_progress()` predicates are available for symmetry

## Implementation Results

### Candidate Evaluation

| Candidate | Tests Passing | Lines of Test Code | Selection |
|-----------|---------------|-------------------|-----------|
| A (broadcast-candidate-a) | 50 | 120 | Converged |
| B (broadcast-candidate-b) | 50 | 120 | Converged |
| C (broadcast-candidate-c) | **68** | 289 | **SELECTED** ✓ |

**Winner:** Candidate C (most comprehensive test coverage: 36% more tests than A/B)

### Files Changed

1. **`src/models/task.py`**
   - Added `mark_in_progress()` method: Transitions PENDING → IN_PROGRESS, updates `updated_at` to CEST time
   - Added `mark_done()` method: Transitions to DONE from any state, updates `updated_at` to CEST time
   - Added `reopen()` method: Transitions DONE → PENDING, updates `updated_at` to CEST time
   - Added `is_pending()` predicate: Returns True if status is PENDING
   - Added `is_in_progress()` predicate: Returns True if status is IN_PROGRESS
   - Added `is_completed()` predicate: Returns True if status is DONE
   - Added `is_overdue()` predicate: Returns True if task has past due_date and is not completed
   - All status-mutating methods handle invalid transitions as no-ops (silent guards)

2. **`tests/test_task.py`**
   - Added 18 comprehensive test cases (candidate C added more edge cases):
     - Status transition coverage: PENDING → IN_PROGRESS → DONE → PENDING
     - Idempotency tests for all transitions
     - Invalid transition handling (e.g., DONE → IN_PROGRESS via mark_in_progress)
     - State predicate verification for all statuses
     - `is_overdue()` with due_date in past, future, None, and completed states
     - CEST timezone verification for `updated_at` updates
     - Integration tests combining multiple transitions

### Test Results

```
....................................................................     [100%]
68 passed in 0.14s
```

### Design Decisions

1. **Status Transition State Machine:**
   - PENDING ↔ IN_PROGRESS ↔ DONE
   - `reopen()` explicitly transitions DONE → PENDING
   - Invalid forward transitions (e.g., DONE → IN_PROGRESS) are no-ops (guards prevent state corruption)

2. **Timestamp Updates:** All status-mutating methods call `datetime.now(CEST)` to ensure `updated_at` reflects the timezone requirement and business logic intent.

3. **Overdue Logic:** Task is overdue only if:
   - Has a `due_date`
   - `due_date` is in the past (relative to CEST now)
   - Task is NOT completed (is_completed() returns False)
   
   This prevents marking completed tasks as overdue, which is a common business rule.

4. **Predicate Consistency:** Seven public query methods provide symmetry and clarity:
   - State predicates: `is_pending()`, `is_in_progress()`, `is_completed()`
   - Temporal predicate: `is_overdue()`
   - State mutators: `mark_in_progress()`, `mark_done()`, `reopen()`

### Candidate Convergence

All three candidates implemented the same core logic correctly, but Candidate C distinguished itself through:
- More edge case tests (e.g., is_overdue with various due_date states)
- Multiple transition sequences tested together
- Explicit CEST timezone verification in test assertions

Duration: PENDING | Cost: PENDING | Turns: PENDING
