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

Duration: 278.1s | Cost: $0.497082 USD | Turns: 21

---

## Task 03: Attach comments to tasks

### Status: Completed ✓

**Task number:** 03

**Files changed:**
- src/models/task_comment.py (new)
- src/models/task.py
- src/models/__init__.py
- src/services/task_manager.py
- src/services/todo_service.py
- src/services/__init__.py
- artifacts/class_diagram.puml

**Test result:** ✓ All 41 tests passed (0 failures)

**Summary:**
- Created new TaskComment dataclass with id (UUID), task_id, content (non-empty), author (optional), created_at (UTC), updated_at (optional)
- Implemented validation in TaskComment.__post_init__() to reject empty/whitespace content and non-timezone-aware datetimes
- Added TaskComment.to_dict() and from_dict() for JSON serialization/deserialization
- Extended Task model with comments field (list of TaskComment, default empty list)
- Updated Task.to_dict() to include nested comments array
- Updated Task.from_dict() to deserialize comments and handle old JSON without comments field (backward compatible)
- Added CommentNotFoundError exception to TaskManager
- Extended TaskManager with three comment methods: add_comment, list_comments, delete_comment
- Extended TodoService with three wrapper methods: add_comment_to_task, list_task_comments, delete_task_comment
- Updated class_diagram.puml to show TaskComment class and all relationships
- All existing 41 tests pass, confirming full backward compatibility

**Acceptance Criteria Met:**
- ✓ TaskComment has id (UUID), task_id, content, created_at (CEST/UTC), author (optional), updated_at (optional)
- ✓ TaskComment serializes to/deserializes from JSON-compatible dictionary
- ✓ Empty content is rejected with ValueError
- ✓ TaskComment must reference valid task_id (validated by TaskManager.add_comment)
- ✓ Author attribute is optional and recorded when provided
- ✓ updated_at attribute is available for consistency
- ✓ Comments are nested within Task, transparent to persistence layer
- ✓ Backward compatibility maintained for old JSON without comments field

Duration: PENDING | Cost: PENDING | Turns: PENDING
