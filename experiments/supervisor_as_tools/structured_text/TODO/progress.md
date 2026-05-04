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

---

## Task 06: Add task statistics

### Status: COMPLETED ✓

### Files Changed
- `src/models/task_statistics.py` — New file with TaskStatistics dataclass (8 fields)
- `src/models/__init__.py` — Added TaskStatistics to imports and __all__
- `src/services/todo_service.py` — Added get_statistics() method to compute all statistics
- `src/cli/todo_cli.py` — Added stats subcommand and _cmd_stats() handler
- `src/cli/interactive_menu.py` — Added option 7 "View statistics" and _do_stats() method; shifted comment menu to option 8 and delete to option 9
- `artifacts/class_diagram.puml` — Added TaskStatistics class, methods to TodoService/TodoCLI/InteractiveMenu, and relationships
- `artifacts/use_case_diagram.puml` — Added "View statistics" use cases for both interactive and CLI modes
- `artifacts/activity_diagram.puml` — Added statistics computation activity with detailed steps
- `artifacts/component_diagram.puml` — Added Statistics Model component and relationship

### Test Results
- **Total tests: 150**
- **Passed: 150**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: Compute total task count
✓ MUST: Compute count per status (pending, in_progress, done)
✓ MUST: Compute count of overdue tasks
✓ MUST: Compute count of tasks with due date set
✓ MUST: Return a dataclass (not dict) as structured report object
✓ MUST: All functionality accessible via python -m src (interactive menu option 7 + stats subcommand)
✓ SHOULD: Include completion rate as percentage (done / total)
✓ SHOULD: Ensure deterministic output format regardless of task ordering
✓ COULD: Include average days from creation to completion for done tasks

### Implementation Summary
- TaskStatistics dataclass with 8 fields: total_count, pending_count, in_progress_count, done_count, overdue_count, tasks_with_due_date, completion_rate (0-100%), avg_days_to_completion (Optional[float])
- TodoService.get_statistics() iterates all tasks, counts by status using existing list operations, counts overdue using is_overdue() method, counts with due_date
- Completion rate computed as (done_count / total_count * 100), rounded to 1 decimal place; handles zero total gracefully
- Avg days to completion calculated as average of (updated_at - created_at).days for done tasks only; returns None if no done tasks
- CLI integration: `python -m src stats` displays formatted statistics with proper alignment and percentage formatting
- Interactive menu: option 7 displays statistics with "—" for missing avg_days value, waits for user to press Enter
- All statistics computations handle empty task lists and edge cases gracefully
- Output format is deterministic (same result for same task set every time)
- All 150 existing tests continue to pass

Duration: 394.1s | Cost: $0.784273 USD | Turns: 20

---

## Task 07: Add import and export of tasks and comments

### Status: COMPLETED ✓

### Files Changed
- `src/services/todo_service.py` — Added export_tasks() and import_tasks() with comprehensive validation
- `src/storage/json_storage.py` — Added import_data() method for bulk data loading
- `src/services/task_manager.py` — Added _load_from_dicts() for bulk task loading
- `src/services/comments_service.py` — Added _load_from_dicts() for bulk comment loading
- `src/cli/todo_cli.py` — Added export and import subcommands with CLI handlers
- `src/cli/interactive_menu.py` — Added menu options 10 and 11 for export/import with handlers
- `artifacts/class_diagram.puml` — Updated to show new export/import methods
- `artifacts/activity_diagram.puml` — Updated to show export/import workflows
- `artifacts/activity_diagram_import_export.puml` — New file with detailed workflows
- `artifacts/component_diagram.puml` — Updated to show import/export infrastructure
- `artifacts/use_case_diagram.puml` — Added export/import use cases for both modes

### Test Results
- **Total tests: 150**
- **Passed: 150**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: Allow exporting all stored Task records (including associated TaskComment records) to a JSON file
✓ MUST: Allow importing Task and TaskComment records from a JSON file
✓ MUST: Preserve task IDs, statuses, due dates, and comments on import
✓ MUST: Validate imported data structure before applying it
✓ MUST: Existing stored data must not be overwritten without explicit intent
✓ MUST: All new functionality must be accessible via python -m src (interactive menu + CLI flags)
✓ SHOULD: Schema must match the Task.to_dict() and TaskComment.to_dict() serialization formats

### Implementation Summary
- **Export functionality:** export_tasks(filepath) exports all tasks and comments to JSON file with format: {"tasks": [...], "comments": [...]}. Returns (task_count, comment_count) tuple.
- **Import functionality:** import_tasks(filepath, overwrite=False) imports tasks and comments from JSON file with comprehensive validation. Returns (task_count, comment_count, []) tuple.
- **Validation:** Comprehensive checks including:
  - File existence and JSON syntax validity
  - Required keys ("tasks", "comments")
  - Task fields: id, title, description, status, created_at, updated_at, due_date
  - Comment fields: id, task_id, content, created_at
  - Status values must be in {pending, in_progress, done}
  - Datetime fields must be ISO 8601 parseable
  - All comment task_ids must reference valid task ids in the import
  - Comments cannot have empty/whitespace-only content
- **Overwrite protection:** If database not empty and overwrite=False, raises ValueError. If overwrite=True, clears all existing data before loading.
- **Error messages:** Exact error context with field/index information for debugging
- **CLI commands:** 
  - `python -m src export <filepath>` — exports to file with success message
  - `python -m src import <filepath> [--overwrite]` — imports with optional overwrite flag
  - Both commands return 0 on success, 1 on error
  - Errors printed to stderr with "Error: " prefix
- **Interactive menu:** 
  - Option 10: Export — prompts for filepath, shows confirmation
  - Option 11: Import — prompts for filepath, checks database state, asks for overwrite confirmation if needed
- **Data integrity:** All task IDs, statuses, due dates, and comment IDs preserved exactly on round-trip import/export

Duration: 465.9s | Cost: $0.993832 USD | Turns: 18

---

## Task 08: Add project mode for grouping tasks

### Status: COMPLETED ✓

### Files Changed
- `src/models/project.py` — New Project dataclass with id (UUID) and name attributes, validation, serialization
- `src/models/task.py` — Added optional project_id field to Task
- `src/models/__init__.py` — Exported Project class
- `src/storage/json_storage.py` — Added load_projects() and save_projects() methods for project persistence
- `src/services/project_manager.py` — New ProjectManager service with add(), get(), list_all(), delete() methods
- `src/services/task_manager.py` — Extended add() to accept optional project_id, added list_by_project() and unassign_from_project() methods
- `src/services/todo_service.py` — Added project management methods (add_project, get_project, list_projects, delete_project), updated task methods to support project filtering
- `src/cli/todo_cli.py` — Added project-add, project-list, project-delete subcommands; extended add and list commands with --project flag
- `src/cli/interactive_menu.py` — Added project management menu option (7) with add, list, delete, and filter by project functionality
- `tests/test_project.py` — 8 tests for Project model
- `tests/test_project_manager.py` — 8 tests for ProjectManager CRUD
- `tests/test_task_project.py` — 8 tests for Task/TaskManager project support
- `tests/test_json_storage_projects.py` — 6 tests for storage persistence
- `tests/test_todo_service_projects.py` — 10 tests for service layer
- `tests/test_cli_projects.py` — 8 tests for CLI commands
- `artifacts/class_diagram.puml` — Added Project class, extended TaskManager and TodoService with project methods
- `artifacts/component_diagram.puml` — Added Project Manager component
- `artifacts/use_case_diagram.puml` — Added project management use cases
- `artifacts/activity_diagram.puml` — Updated menu flow to include project management

### Test Results
- **Total tests: 198**
- **Passed: 198**
- **Failed: 0**
- **Success rate: 100%**

### Requirements Met
✓ MUST: Introduce a `Project` domain class with attributes: `id: str` (UUID), `name: str`
✓ MUST: Add optional `project_id: Optional[str]` to `Task` to assign it to a project
✓ MUST: Support creating and listing projects
✓ MUST: Support listing tasks filtered by project
✓ MUST: Preserve existing behavior for tasks without a project assignment
✓ MUST: All new functionality must be accessible via `python -m src` — both as an interactive menu option and as a one-shot CLI flag
✓ SHOULD: Validate that project names are not empty
✓ SHOULD: Naming and structure must follow existing conventions in the codebase
✓ SHOULD: Preserve backward compatibility with stored tasks (tasks without `project_id` must load without error)

### Implementation Summary
- **Project Model:** Dataclass with auto-generated UUID id and required non-empty name field. Full serialization support (to_dict/from_dict).
- **Task Updates:** Added optional project_id field (defaults to None). Backward compatible: old task files without project_id load successfully.
- **ProjectManager Service:** Standalone CRUD service managing projects. Supports prefix-based ID lookup for CLI convenience. Raises ProjectNotFoundError when project not found.
- **Storage:** Extended JsonStorage with load_projects()/save_projects() methods. Storage format: {"tasks": [...], "comments": [...], "projects": [...]}. Handles files without projects key gracefully.
- **TaskManager Extensions:** add() accepts optional project_id. New list_by_project(project_id) method filters tasks by project. unassign_from_project() unassigns all tasks when project deleted.
- **TodoService:** Coordinates TaskManager and ProjectManager. Exposes: add_project(), get_project(), list_projects(), delete_project(). Project deletion unassigns tasks (project_id → None) rather than deleting them.
- **CLI Commands:**
  - `python -m src project-add "Project Name"` — creates project
  - `python -m src project-list` — lists all projects
  - `python -m src project-delete <id>` — deletes project (unassigns tasks)
  - `python -m src add "Task" --project <id>` — creates task in project
  - `python -m src list --project <id>` — lists tasks filtered by project
- **Interactive Menu:** New menu option (7) for project management with submenu: Add project, List projects, List tasks by project, Delete project.
- **Error Handling:** New ProjectNotFoundError exception. Proper validation of project names (non-empty). Graceful handling of missing project references.
- **Cascade Behavior:** Deleting a project unassigns all tasks (sets project_id to None), preserving task data while removing project association.

Duration: 525.7s | Cost: $1.225336 USD | Turns: 19

---

## Task 09: Separate core components of the TODO manager

### Status: COMPLETED ✓

### Files Changed
- `src/storage/storage.py` — NEW: Abstract base class defining Storage interface with abstract methods for load/save operations
- `src/repositories/__init__.py` — NEW: Package initialization exporting TaskRepository and TaskExistenceValidator
- `src/repositories/task_validator.py` — NEW: TaskExistenceValidator protocol defining task existence validation interface
- `src/repositories/task_repository.py` — NEW: TaskRepository class implementing TaskExistenceValidator, coordinates TaskManager and CommentsService
- `src/storage/__init__.py` — Updated to export Storage ABC and JsonStorage
- `src/storage/json_storage.py` — Refactored to inherit from Storage ABC; all implementations unchanged
- `src/services/task_manager.py` — Removed _comments_service field and TYPE_CHECKING import; added has_tasks() and clear() public methods; removed cascade delete from delete()
- `src/services/comments_service.py` — Replaced TaskManager dependency with TaskExistenceValidator protocol; added has_comments() and clear() public methods; removed task manager instantiation
- `src/services/project_manager.py` — Updated type hints to use Storage abstraction instead of JsonStorage
- `src/services/todo_service.py` — Refactored to use repository pattern; updated initialization sequence; updated import_tasks() to use public APIs; updated delete_task() to use repository
- `artifacts/class_diagram.puml` — Updated to show Storage abstraction, TaskExistenceValidator protocol, TaskRepository, and refactored service dependencies
- `artifacts/component_diagram.puml` — Updated to show clean layering without circular dependencies

### Test Results
- **Total tests: 198**
- **Passed: 198**
- **Failed: 0**
- **Success rate: 100%**

### Architecture Changes

#### Removed Circular Dependencies
- **Before:** TaskManager ↔ CommentsService (bidirectional at runtime)
- **After:** TaskRepository mediates between them; neither imports the other at module level

#### New Storage Abstraction
- All managers now depend on Storage ABC, not concrete JsonStorage
- Enables easier testing with mock implementations
- Follows Dependency Inversion Principle

#### Repository Pattern for Coordination
- TaskRepository implements TaskExistenceValidator protocol
- Owns all knowledge of cascade deletion logic
- Breaking point for circular dependency: CommentsService → TaskExistenceValidator protocol (abstraction) rather than → TaskManager (concrete class)

#### Public API Enhancements
- TaskManager: has_tasks(), clear(), load_from_dicts()
- CommentsService: has_comments(), clear(), load_from_dicts()
- Enables TodoService to use public APIs instead of accessing private fields

#### Layer Dependencies (Strict Downward Flow)
```
Presentation: TodoCLI, InteractiveMenu
  ↓
Orchestration: TodoService
  ↓
Business Logic: TaskManager, CommentsService, ProjectManager, TaskRepository
  ↓
Storage Abstraction: Storage (ABC)
  ↓
Persistence: JsonStorage
```

### Requirements Met
✓ MUST: Separate into distinct layers with no circular dependencies (TaskManager ↔ CommentsService eliminated)
✓ MUST: Separate Task domain logic, Comment logic, Project logic, Storage layer, Interface layer
✓ MUST: Preserve existing public interfaces (all function signatures, class names, return types unchanged)
✓ MUST: `python -m src` behaves identically before/after; all existing functionality remains accessible
✓ SHOULD: Introduce abstract base classes/protocols to decouple service, storage, and interface layers (Storage ABC, TaskExistenceValidator protocol)
✓ SHOULD: Improve code structure and readability without changing external behavior

### Implementation Summary
- **Storage Abstraction:** Created Storage ABC with abstract methods for load/save operations on tasks, comments, and projects. JsonStorage inherits from Storage. All managers depend on Storage abstraction.
- **TaskExistenceValidator Protocol:** Defines task validation interface. CommentsService depends on this protocol instead of TaskManager directly. Implemented by TaskRepository.
- **TaskRepository:** New class that coordinates between TaskManager and CommentsService. Handles cascade deletion of comments when task is deleted. Breaks the circular dependency by being the single point that knows about both services.
- **Refactored TaskManager:** Removed _comments_service field and cascade delete logic. Now a pure task CRUD service. Added has_tasks() and clear() methods for public use.
- **Refactored CommentsService:** Removed TaskManager import and instantiation. Now accepts TaskExistenceValidator at construction. Validates tasks via protocol instead of direct dependency.
- **Refactored ProjectManager:** Updated to use Storage abstraction instead of concrete JsonStorage type.
- **Refactored TodoService:** Orchestrates managers and repository. Uses dependency injection pattern. Updated import_tasks() to use public methods instead of accessing private fields. Uses repository for cascade deletes.
- **No Circular Imports:** All modules import successfully; dependency graph is acyclic.
- **CLI Unchanged:** All existing commands work identically (20 commands tested and passing).
- **Backward Compatible:** All tests pass; JSON storage format unchanged; task persistence unchanged.

### Circular Dependency Elimination Strategy

**Original Problem:**
```python
# task_manager.py (TYPE_CHECKING import avoids load-time cycle)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .comments_service import CommentsService

# comments_service.py (direct import, needs TaskManager at load time)
from .task_manager import TaskManager
```

At runtime, TodoService sets `task_manager._comments_service = comments_service` after creating both, creating a circular reference in the object graph.

**Solution:**
1. Introduce TaskExistenceValidator protocol: CommentsService depends on this protocol (abstraction), not TaskManager (concrete class)
2. TaskRepository implements the protocol: it holds references to both TaskManager and CommentsService
3. TodoService wires them together: creates managers → creates repository → injects repository into CommentsService
4. Result: No circular imports; clear dependency direction; single point of cascade delete coordination

### Preservation of Public Interfaces
- All TodoService methods have identical signatures
- All TaskManager public methods preserved
- All CommentsService public methods preserved
- All ProjectManager public methods preserved
- All CLI commands work identically
- All test scenarios pass without modification

Duration: PENDING | Cost: PENDING | Turns: PENDING
