# TODO Application - Task Progress

## Task 01: Add optional `due_date` attribute to Task

### Status: Completed ✓

**Task number:** 01

**Files changed:**
- src/models/task.py
- src/services/task_manager.py
- src/services/todo_service.py
- artifacts/class_diagram.puml

**Test result:** ✓ All 41 tests passed (0 failures)

**Summary:**
- Added optional `due_date: Optional[datetime] = None` field to Task dataclass
- Implemented timezone validation in Task.__post_init__() to ensure due_date is timezone-aware
- Updated Task.to_dict() to conditionally include due_date (only when not None)
- Updated Task.from_dict() to gracefully handle missing due_date field (backward compatible)
- Extended TaskManager.update() to accept optional due_date parameter
- Extended TodoService.add_task() and update_task() to accept optional due_date parameter with validation
- Updated class_diagram.puml to reflect the new due_date field and updated method signatures
- All existing 41 tests pass, confirming full backward compatibility

**Acceptance Criteria Met:**
- ✓ Task has optional due_date attribute (None by default)
- ✓ Tasks without due_date load and behave correctly
- ✓ due_date is stored and loaded through storage layer
- ✓ Dates use timezone-aware datetime objects (timezone info preserved in ISO 8601 format)
- ✓ Invalid datetime values (non-datetime or naive datetime) are rejected in Task.__post_init__()
- ✓ Existing stored tasks lacking due_date field load without error (uses .get() in from_dict())

Duration: PENDING | Cost: PENDING | Turns: PENDING
