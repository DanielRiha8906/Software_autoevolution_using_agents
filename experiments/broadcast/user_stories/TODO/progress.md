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

Duration: PENDING | Cost: PENDING | Turns: PENDING
