# Task Progress

## Task 01: Add optional due_date field to Task model

### Summary
Extended Task model with an optional `due_date: Optional[datetime]` field that persists through the storage layer with full backward compatibility.

### Files Changed
- `src/models/task.py` — Added due_date field, validation helper, serialization/deserialization support
- `src/services/task_manager.py` — Added due_date parameter to add() method with validation
- `src/services/todo_service.py` — Added due_date parameter to add_task() method with validation
- `tests/test_due_date.py` — New test suite (7 tests)
- `artifacts/class_diagram.puml` — Updated Task class definition

### Test Results
- All 7 new due_date tests: ✓ PASS
- All 48 total tests: ✓ PASS
- No regressions in existing tests

### Implementation Details
- `due_date` field defaults to None
- Stored/serialized as ISO 8601 string with timezone
- Timezone validation: rejects naive datetimes, requires timezone-aware
- Backward compatible: old records without due_date key load correctly
- Validation occurs in `from_dict()` and service layer entry points

Duration: PENDING | Cost: PENDING | Turns: PENDING
