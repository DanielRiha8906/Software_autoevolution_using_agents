# Task Progress

## Task 01: Add due date to tasks

### Status: COMPLETED ✓

### Files Changed
- `src/models/task.py` — Added due_date attribute, is_overdue() method, serialization
- `src/services/task_manager.py` — Added set_due_date() and _validate_due_date() methods
- `src/services/todo_service.py` — Added set_due_date() wrapper method
- `src/cli/todo_cli.py` — Added due-date subcommand and display logic
- `src/cli/interactive_menu.py` — Added menu option 6 for setting due dates
- `tests/test_task.py` — Added 6 new tests for due date functionality
- `tests/test_task_manager.py` — Added 6 new tests for service layer
- `artifacts/class_diagram.puml` — Updated UML to reflect due_date feature

### Test Results
- **Total tests: 53**
- **Passed: 53**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: Add attribute `due_date: Optional[datetime]` to `Task`
✓ MUST: Allow tasks without a due date (`None` by default)
✓ MUST: Ensure `due_date` is stored and persisted through storage layer
✓ MUST: Update `to_dict` and `from_dict` accordingly
✓ MUST: Use CEST (UTC+2) timezone-aware datetime representation (ISO 8601)
✓ SHOULD: Preserve backward compatibility with stored JSON data
✓ SHOULD: Validate that a provided due date is a valid datetime before accepting
✓ COULD: Add `is_overdue()` predicate to `Task` returning True when past due

### Implementation Summary
- Due dates stored internally as UTC (ISO 8601), displayed as CEST (Europe/Paris timezone)
- User input interpreted as CEST time ("YYYY-MM-DD HH:MM" format)
- Validation prevents setting past due dates
- Backward compatibility: old tasks without due_date field load without error
- Two CLI modes: interactive (option 6) and one-shot (`due-date` subcommand)
- UML diagrams updated to reflect new classes and methods

Duration: 367.9s | Cost: $0.723867 USD | Turns: 18

---

## Task 02: Add status and due date methods to Task

### Status: COMPLETED ✓

### Files Changed
- `src/models/task.py` — Added mark_in_progress(), mark_done(), reopen(), is_completed() methods
- `tests/test_task_transitions.py` — New file with 27 unit tests for Task status methods
- `tests/test_todo_service_transitions.py` — New file with 17 service integration tests
- `tests/test_cli_transitions.py` — New file with 22 CLI command tests
- `artifacts/class_diagram.puml` — Updated UML to reflect new Task methods

### Test Results
- **Total tests: 119**
- **Passed: 119**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: mark_in_progress() — transitions status to IN_PROGRESS
✓ MUST: mark_done() — transitions status to DONE
✓ MUST: reopen() — transitions status to PENDING
✓ MUST: is_completed() — returns True when status is DONE
✓ MUST: is_overdue() — returns True when due_date is earlier than current CEST time
✓ MUST: Each status-mutating method updates updated_at to current CEST time
✓ MUST: Methods derive state strictly from existing Task attributes
✓ MUST: All functionality accessible via python -m src (interactive menu + CLI flag)
✓ SHOULD: Prevent invalid status transitions (silent no-op strategy)
✓ SHOULD: Add unit tests covering all status transitions and overdue combinations

### Implementation Summary
- Four new instance methods on Task class: mark_in_progress(), mark_done(), reopen(), is_completed()
- Invalid status transitions result in silent no-ops (idempotent behavior)
- updated_at timestamp updated only when status actually changes
- Timezone handling: datetime.now(ZoneInfo("Europe/Paris")).astimezone(timezone.utc)
- 66 new tests across three test files: unit, service integration, and CLI tests
- Existing CLI commands (start, done, reopen) already support new functionality
- Existing service layer (TodoService.start_task, complete_task, reopen_task) fully utilized
- All status mutations properly persist to storage via Task.to_dict/from_dict

Duration: 279.6s | Cost: $0.533964 USD | Turns: 13

---

## Task 03: Introduce TaskComment domain class

### Status: COMPLETED ✓

### Files Changed
- `src/models/task_comment.py` — New file with TaskComment dataclass
- `src/models/__init__.py` — Added TaskComment export
- `artifacts/class_diagram.puml` — Added TaskComment class and relationship to Task

### Test Results
- **Total tests: 119**
- **Passed: 119**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: Create class `TaskComment` with attributes: id, task_id, content, created_at
✓ MUST: Support serialization and deserialization to/from JSON-compatible dictionaries
✓ MUST: id is UUID (generated via uuid.uuid4())
✓ MUST: created_at is datetime with CEST timezone (UTC+2)
✓ SHOULD: Validate that content is not empty (implemented in __post_init__)
✓ SHOULD: Maintain relationship integrity (task_id references parent Task by id)

### Implementation Summary
- TaskComment is a dataclass following the same pattern as Task
- UUID id auto-generated via default_factory
- created_at auto-generated as UTC timezone-aware datetime
- Content validation rejects empty or whitespace-only strings
- Serialization: to_dict() converts datetime to isoformat() strings
- Deserialization: from_dict() parses isoformat() strings back to datetime
- Relationship to Task represented in class diagram as: TaskComment --> Task (task_id references Task.id)
- No service layer or CLI integration in this task (future work)

Duration: 153.9s | Cost: $0.284884 USD | Turns: 22

---

## Task 04: Add CommentsService for managing TaskComments

### Status: COMPLETED ✓

### Files Changed
- `src/services/comments_service.py` — New file with CommentsService class and CommentNotFoundError exception
- `src/storage/json_storage.py` — Extended to support comments storage with load_comments() and save_comments()
- `src/services/task_manager.py` — Added optional comments_service parameter, updated delete() for cascade
- `src/services/todo_service.py` — Added CommentsService instantiation and public delegation methods
- `src/services/__init__.py` — Exported CommentsService and CommentNotFoundError
- `src/cli/todo_cli.py` — Added comment-add, comment-list, comment-delete subcommands
- `src/cli/interactive_menu.py` — Added comment management submenu with view/add/delete options
- `artifacts/class_diagram.puml` — Updated to show CommentsService, relationships, and exception
- `artifacts/component_diagram.puml` — Updated to include Comments Service component
- `artifacts/use_case_diagram.puml` — Added comment management use cases for both interactive and CLI modes
- `artifacts/activity_diagram.puml` — Updated main menu activity to include manage comments option

### Test Results
- **Total tests: 119**
- **Passed: 119**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: Implement CommentsService to manage TaskComment objects
✓ MUST: Add a comment to a task
✓ MUST: List all comments for a given task, ordered by created_at
✓ MUST: Delete a comment by id
✓ MUST: Validate that the referenced task exists before adding a comment
✓ MUST: Integrate with the existing storage mechanism (JsonStorage)
✓ MUST: All functionality accessible via python -m src (interactive menu + CLI flags)
✓ SHOULD: Service responsibilities limited to TaskComment lifecycle; storage separate
✓ SHOULD: Cascade delete — deleting a task deletes its associated comments

### Implementation Summary
- CommentsService follows TaskManager pattern: storage injection, in-memory dict, load/persist lifecycle
- Validates task existence via TaskManager.get() before adding comments
- Returns comments ordered by created_at (ascending)
- JsonStorage extended to store both tasks and comments in single file: {"tasks": [...], "comments": [...]}
- Backward compatible with old list-only format (auto-converts on load)
- TaskManager updated to cascade delete comments when a task is deleted
- TodoService orchestrates both services with proper initialization order (avoids circular dependencies)
- CLI additions: comment-add <task_id> <content>, comment-list <task_id>, comment-delete <comment_id>
- Interactive menu additions: option 7 "Manage comments" with sub-menu for view/add/delete
- All diagrams updated to reflect new CommentsService, relationships, and exception handling

Duration: 441.1s | Cost: $0.832739 USD | Turns: 17

---

## Task 05: Add due date and overdue filtering to task queries

### Status: COMPLETED ✓

### Files Changed
- `src/services/task_manager.py` — Added list_by_due_date_range() and list_overdue() methods
- `src/services/todo_service.py` — Extended list_tasks() with due_before, due_after, and overdue parameters
- `src/cli/todo_cli.py` — Added --due-before, --due-after, --overdue flags to list subcommand; added _parse_cest_datetime() helper
- `src/cli/interactive_menu.py` — Enhanced _do_list() with submenu for filtering by status, due date range, and overdue
- `tests/test_task_manager.py` — Added 13 new tests for filtering methods
- `tests/test_todo_service.py` — Added 11 new tests for extended list_tasks()
- `tests/test_todo_cli.py` — Added 8 new tests for CLI flags
- `artifacts/class_diagram.puml` — Updated to show new filtering methods and extended signatures
- `artifacts/use_case_diagram.puml` — Added "Filter by due date range" and "View overdue tasks" use cases
- `artifacts/activity_diagram.puml` — Enhanced list/filter activity with detailed filter type options

### Test Results
- **Total tests: 150**
- **Passed: 150**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: Extend task query interface with due date range filters (before/after datetime)
✓ MUST: Extend task query interface with overdue status filter
✓ MUST: Return filtered collections consistent with existing list_tasks format
✓ MUST: Overdue detection uses current CEST time (UTC+2)
✓ MUST: All functionality accessible via python -m src (interactive menu + CLI flags)
✓ SHOULD: Support combining new filters with existing status filter in single call
✓ SHOULD: Preserve existing list_tasks(status=...) behavior unchanged

### Implementation Summary
- TaskManager now provides two new methods:
  - list_by_due_date_range(start, end, status): filters tasks by due_date range with inclusive bounds
  - list_overdue(status): returns tasks where is_overdue() == True
- TodoService.list_tasks() extended to accept optional parameters: due_before, due_after, overdue
  - Filtering priority: overdue > date range > status > all
  - Backward compatible: existing calls (no params or status only) work unchanged
- TodoCLI.list command enhanced with three new flags:
  - --due-before: filter tasks due on or before datetime (YYYY-MM-DD HH:MM CEST format)
  - --due-after: filter tasks due on or after datetime
  - --overdue: show only overdue tasks
  - Added _parse_cest_datetime() helper to convert CEST strings to UTC
- InteractiveMenu._do_list() expanded with submenu supporting:
  - Option 1: Filter by status (pending/in_progress/done/all)
  - Option 2: Filter by due date range (start/end in YYYY-MM-DD HH:MM CEST)
  - Option 3: Show only overdue tasks
  - Option 4: Combine filters (status + date range + overdue)
  - Option 0: Show all tasks
- All filtering uses CEST timezone (Europe/Paris) for user-facing dates
- Boundary dates are inclusive; tasks without due_date excluded from range filters
- Error handling for invalid date formats with graceful fallback and user feedback

Duration: 410.3s | Cost: $0.852108 USD | Turns: 19
