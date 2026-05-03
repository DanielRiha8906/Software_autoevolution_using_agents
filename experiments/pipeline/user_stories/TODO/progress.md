# TODO Application Progress — Pipeline / User Stories

## Task 01: Add Due Date Support

**Status:** COMPLETE ✓

### Changes Made
- **Task Model:** Added optional `due_date: Optional[datetime] = None` field with timezone-aware validation in `__post_init__()`
- **Serialization:** Updated `to_dict()` and `from_dict()` for ISO 8601 support with backward compatibility
- **TaskManager:** Added `due_date` parameter to `add()` and `update()` methods; added new `set_due_date()` method
- **TodoService:** Added `due_date` parameter to `add_task()` and `update_task()` with validation; added new `set_due_date()` method
- **TodoCLI:** Added `--due-date` flag to `add` and `update` subcommands; added new `due-date` subcommand; updated `show` to display due_date
- **InteractiveMenu:** Updated menu to include "Set due date" option; added prompts for due_date in add/update; added `_do_set_due_date()` method
- **Diagrams:** Updated class_diagram.puml, activity_diagram.puml, use_case_diagram.puml to reflect new due_date field and methods

### Files Changed
- src/models/task.py
- src/services/task_manager.py
- src/services/todo_service.py
- src/cli/todo_cli.py
- src/cli/interactive_menu.py
- artifacts/class_diagram.puml
- artifacts/activity_diagram.puml
- artifacts/use_case_diagram.puml

### Test Results
**89 tests total: ALL PASSED**
- 13 new tests for Task class (validation, serialization, backward compatibility)
- 8 new tests for TaskManager (due_date operations, persistence)
- 12 new tests for TodoService (validation, method operations)
- 2 new tests for backward compatibility (loading legacy tasks)
- 13 new tests for TodoCLI (command handling, display)

### Acceptance Criteria Verification
✓ Task has optional `due_date` attribute (None by default)
✓ Tasks without due_date load and behave correctly
✓ `due_date` is stored and loaded through storage layer
✓ Dates use timezone-aware ISO 8601 representation
✓ Invalid datetime values rejected before save
✓ Existing stored tasks without `due_date` field load without error

Duration: 614.7s | Cost: $1.099172 USD | Turns: 14

---

## Task 02: Task Status Transition Methods

**Status:** COMPLETE ✓

### Changes Made
- **Task Model:** Added 7 new methods for state management:
  - Query methods: `is_pending()`, `is_in_progress()`, `is_completed()`, `is_overdue()`
  - Mutation methods: `mark_in_progress()`, `mark_done()`, `reopen()`
  - All mutations update `updated_at` to current UTC timestamp
  - All mutations validate state transitions and raise ValueError on invalid transitions
  - Mutation methods return self for method chaining
- **TaskManager:** Refactored `set_status()` to call Task transition methods, enforcing state machine rules
- **TodoService:** Updated `reopen_task()` to transition to IN_PROGRESS (not PENDING), aligning with spec
- **Diagrams:** Updated class_diagram.puml to show all 7 new methods with proper signatures

### Files Changed
- src/models/task.py (7 new methods)
- src/services/task_manager.py (refactored set_status())
- src/services/todo_service.py (fixed reopen_task())
- artifacts/class_diagram.puml (added method signatures)

### Test Results
**131 tests total: ALL PASSED**
- 42 new tests for Task methods (valid transitions, invalid transitions, error messages)
- 3 tests for mark_in_progress() (valid + 2 invalid states)
- 3 tests for mark_done() (valid + 2 invalid states)
- 3 tests for reopen() (valid + 2 invalid states, goes to IN_PROGRESS not PENDING)
- 3 tests for updated_at timestamp verification on all mutations
- 3 tests each for is_pending(), is_in_progress(), is_completed()
- 6 tests for is_overdue() (None due_date, past/future dates, status override)
- 5 tests for TaskManager.set_status() integration
- 3 tests for TodoService integration (start, complete, reopen)
- 4 tests for error handling and method chaining

### Acceptance Criteria Verification
✓ Task provides clear methods: `mark_in_progress()`, `mark_done()`, `reopen()`, `is_completed()`, `is_overdue()`
✓ Additional symmetry methods: `is_pending()`, `is_in_progress()`
✓ Each status-mutating method updates `updated_at` to current UTC time
✓ Methods derive state strictly from existing Task attributes (no external input)
✓ Invalid transitions raise ValueError with descriptive messages (fail-fast)
✓ All functionality accessible via `python -m src` (interactive menu option 4 + CLI flags start/done/reopen)

Duration: 496.0s | Cost: $0.844545 USD | Turns: 25

---

## Task 03: Task Comments

**Status:** COMPLETE ✓

### Changes Made
- **TaskComment Model:** Created new src/models/task_comment.py with dataclass:
  - Fields: `id` (UUID string, auto-generated), `task_id` (reference to parent), `content` (required, non-empty), `created_at` (timezone-aware UTC), `author` (optional), `updated_at` (optional)
  - Validation: Rejects empty/whitespace-only content, requires timezone-aware datetimes
  - Serialization: `to_dict()` converts datetimes to ISO 8601, `from_dict()` reconstructs from dict
- **Task Model:** Updated src/models/task.py:
  - Added `comments: list[TaskComment]` field with default empty list
  - Updated `to_dict()` to serialize comments list
  - Updated `from_dict()` to deserialize comments with backward compatibility
- **TaskManager:** Added 3 new methods in src/services/task_manager.py:
  - `add_comment(task_id, content, author=None)` — Creates and persists comment, validates task exists
  - `get_comments(task_id)` — Retrieves all comments for a task
  - `delete_comment(task_id, comment_id)` — Removes comment and persists
- **TodoService:** Added 3 new methods in src/services/todo_service.py:
  - `add_comment(task_id, content, author=None)` — Service-layer validation (non-empty, strips whitespace)
  - `get_comments(task_id)` — Delegates to TaskManager
  - `delete_comment(task_id, comment_id)` — Delegates to TaskManager
- **Diagrams:** Updated artifacts/:
  - class_diagram.puml: Added TaskComment class with fields/methods, updated Task with comments field, updated TaskManager/TodoService with new methods
  - component_diagram.puml: Added TaskComment Model component and dependencies
  - use_case_diagram.puml: Added interactive and CLI use cases for add/view/delete comments

### Files Changed
- src/models/task_comment.py (NEW)
- src/models/task.py
- src/models/__init__.py
- src/services/task_manager.py
- src/services/todo_service.py
- artifacts/class_diagram.puml
- artifacts/component_diagram.puml
- artifacts/use_case_diagram.puml

### Test Results
**210 tests total: ALL PASSED**
- 79 new TaskComment tests organized in 11 test classes
- 28 tests for TaskComment model (creation, defaults, validation, timezone handling)
- 8 tests for Task integration (comments field, serialization roundtrip, backward compatibility)
- 20 tests for TaskManager (add_comment, get_comments, delete_comment with persistence)
- 18 tests for TodoService (validation, whitespace stripping, delegation)
- 6 integration tests (persistence across reloads, comment lifecycle, isolation)
- 131 existing tests all still passing (no regressions)

### Acceptance Criteria Verification
✓ TaskComment has: `id` (UUID), `task_id`, `content`, `created_at` (CEST/UTC)
✓ TaskComment serializes to/from JSON-compatible dictionary
✓ Empty content is rejected with ValueError
✓ TaskComment must reference valid task_id (verified via TaskManager.get())
✓ Optional `author` attribute implemented
✓ Optional `updated_at` attribute implemented
✓ Rich text, markdown, and nested comments explicitly out of scope (confirmed in design, not implemented)

Duration: PENDING | Cost: PENDING | Turns: PENDING
