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

Duration: 193.5s | Cost: $0.364279 USD | Turns: 19

## Task 03: Create TaskComment domain class

### Summary
Created a new `TaskComment` domain class with full serialization support, CEST timezone enforcement, and content validation. TaskComment serves as an independent domain model for attaching comments to tasks by `task_id`.

### Files Changed
- `src/models/task_comment.py` — New domain class with id, task_id, content, created_at, author, updated_at fields
- `src/models/__init__.py` — Added TaskComment export
- `artifacts/class_diagram.puml` — Added TaskComment class to models package with Task relationship
- `artifacts/component_diagram.puml` — Added TaskComment to Domain Model layer
- `tests/test_task_comment.py` — New test suite (19 comprehensive tests)

### Test Results
- All 19 new TaskComment tests: ✓ PASS
- All 67 total tests: ✓ PASS (48 existing + 19 new)
- No regressions in existing tests

### Implementation Details
- `id` field: UUID string, auto-generated via uuid.uuid4()
- `task_id` field: String reference to Task (no FK constraint, file-based system)
- `content` field: Required non-empty string, validated in __post_init__()
- `created_at` field: Automatically set to current time in CEST timezone (UTC+2)
- `author` field: Optional string, defaults to None
- `updated_at` field: Optional datetime in CEST timezone, defaults to None
- Serialization: Full to_dict()/from_dict() support with ISO 8601 string timestamps
- Timezone handling: All datetimes use CEST (timezone(timedelta(hours=2))), not UTC
- Validation: Empty content raises ValueError; timezone-aware datetime enforcement

Duration: 407.7s | Cost: $0.637273 USD | Turns: 24

## Task 04: Implement CommentsService with lifecycle management

### Summary
Implemented `CommentsService` to manage the full lifecycle of `TaskComment` objects with validation, ordering, and cascade-delete support. Service integrates with existing `TodoService` and `JsonStorage` without direct file I/O.

### Files Changed
- `src/services/comments_service.py` — New CommentsService class with add/list/delete operations
- `src/services/__init__.py` — Added CommentsService export
- `artifacts/class_diagram.puml` — Added CommentsService class with method signatures and dependencies
- `artifacts/component_diagram.puml` — Added Comments Service component to service layer

### Test Results
- All 7 required tests: ✓ PASS
- All 16 new CommentsService tests: ✓ PASS
- All 83 total tests: ✓ PASS (67 existing + 16 new)
- No regressions in existing tests

### Implementation Details
- **In-memory cache**: `Dict[task_id → List[TaskComment]]` for fast access
- **Task validation**: Every operation calls `todo_service.get_task(task_id)` to verify existence
- **Content validation**: Delegates to TaskComment's `__post_init__()` for non-empty/non-whitespace check
- **Ordering**: `list_comments()` returns comments sorted by `created_at` ascending
- **Cascade delete**: `delete_comments_for_task()` clears all comments for a task
- **ID generation**: UUID4 for globally unique comment identifiers
- **No file I/O**: All storage interactions through TodoService; no JSON operations in service

### Key Methods
- `add_comment(task_id: str, content: str) → TaskComment` — Create comment with validation
- `list_comments(task_id: str) → List[TaskComment]` — Retrieve ordered comments
- `delete_comment(comment_id: str) → None` — Remove single comment
- `delete_comments_for_task(task_id: str) → None` — Remove all comments for task

Duration: 351.8s | Cost: $0.610275 USD | Turns: 13
