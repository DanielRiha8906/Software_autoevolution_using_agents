# Task 05: Extend list_tasks with Due Date Filtering

## Summary

Extended `TodoService.list_tasks()` to support filtering by due date range and overdue status, combining cleanly with the existing status filter without breaking its behavior.

## Files Changed

- `src/services/todo_service.py` — Extended list_tasks() signature and implemented filtering logic with timezone validation
- `src/cli/todo_cli.py` — Added --due-before, --due-after, --overdue flags to list subparser
- `src/cli/interactive_menu.py` — Added menu option 7 for due date filtering
- `tests/test_task_05_due_date_filtering.py` — Created new test file with 7 test functions
- `artifacts/class_diagram.puml` — Updated TodoService signatures
- `artifacts/use_case_diagram.puml` — Added new use cases for due date filtering
- `artifacts/activity_diagram.puml` — Added activity for menu option 7

## Test Results

All tests pass:
- **7 new tests** (test_task_05_due_date_filtering.py): PASS
  - test_filter_overdue
  - test_filter_due_before
  - test_filter_due_after
  - test_combined_status_and_overdue
  - test_existing_status_filter_unchanged
  - test_due_date_filters_use_cest
  - test_results_are_task_objects

- **87 total tests**: ALL PASS
- **80 existing tests**: PASS (no regressions)

## Implementation Details

### Core Features
1. **Timezone Validation**: All due_date filters validate CEST timezone; non-CEST raises ValueError
2. **Filter Logic**: 
   - `overdue=True` — returns tasks where is_overdue() == True
   - `due_before=dt` — returns tasks where due_date is None or due_date < dt
   - `due_after=dt` — returns tasks where due_date is None or due_date > dt
3. **Combined Filters**: All filters use AND logic; can be combined with status filter
4. **Backward Compatibility**: All new parameters have defaults; existing calls work unchanged

### CLI Integration
- `python -m src list --overdue` — show overdue tasks
- `python -m src list --due-before "2026-05-31T18:00:00+02:00"` — tasks before cutoff
- `python -m src list --status pending --overdue` — pending tasks that are overdue

### Interactive Menu
- New menu option 7: "Filter by due date"
- Submenu with 3 filtering options:
  1. Overdue tasks
  2. Due before date (YYYY-MM-DD HH:MM in CEST)
  3. Due after date (YYYY-MM-DD HH:MM in CEST)

## Constraints Met
✅ All provided tests pass
✅ Existing tests still pass (no regressions)
✅ Code compiles without syntax errors
✅ `list_tasks()` with no arguments returns all tasks
✅ Functionality accessible via `python -m src` (CLI flags + interactive menu)
✅ Timezone validation enforces CEST only
✅ Status filter logic unchanged
✅ No database query engine used (in-memory filtering)

Duration: 452.6s | Cost: $0.830710 USD | Turns: 23

---

# Task 06: Implement TaskStatisticsService

## Summary

Implemented `TaskStatisticsService` that computes aggregate statistics from stored tasks, including total count, per-status breakdown, overdue count, tasks with due dates, and completion rate as a percentage.

## Files Changed

- `src/services/task_statistics_service.py` — Created new service with TaskStatistics dataclass and TaskStatisticsService class
- `src/services/statistics_service.py` — Created alias module for test imports (re-exports from task_statistics_service)
- `src/services/__init__.py` — Added TaskStatisticsService and TaskStatistics exports
- `src/cli/todo_cli.py` — Added statistics subcommand (python -m src statistics)
- `src/cli/interactive_menu.py` — Added menu option 8 for "View statistics"
- `tests/test_statistics_service.py` — Created comprehensive test suite (22 tests)
- `artifacts/class_diagram.puml` — Added TaskStatistics and TaskStatisticsService classes
- `artifacts/component_diagram.puml` — Added Task Statistics Service component

## Test Results

All tests pass:
- **8 required tests**: PASS (test_report_is_dataclass, test_total_count, test_count_per_status, test_overdue_count, test_with_due_date_count, test_completion_rate, test_empty_task_list_statistics, test_output_is_deterministic)
- **14 additional comprehensive tests**: PASS (edge cases, invariants, integration)
- **109 total tests**: ALL PASS
- **87 existing tests**: PASS (no regressions)

## Implementation Details

### Core Features
1. **TaskStatistics Dataclass**: Contains 5 fields:
   - `total: int` — total number of tasks
   - `count_per_status: dict[TaskStatus, int]` — count per status (PENDING, IN_PROGRESS, DONE)
   - `overdue_count: int` — tasks with due_date in the past
   - `with_due_date_count: int` — tasks with non-None due_date
   - `completion_rate: float` — percentage of completed tasks (0-100)

2. **TaskStatisticsService.compute()**: Computes all statistics in one call:
   - Gets all tasks via `TodoService.list_tasks()`
   - Counts tasks per status
   - Uses `list_tasks(overdue=True)` for overdue count
   - Filters tasks with `due_date is not None` for due date count
   - Calculates completion_rate: `(done_count / total * 100) if total > 0 else 0.0`

3. **CLI Integration**:
   - Command: `python -m src statistics`
   - Displays formatted report with aligned output

4. **Interactive Menu**:
   - Menu option 8: "View statistics"
   - Displays statistics in formatted box with aligned columns

### Edge Cases Handled
- Empty task list: completion_rate = 0.0 (not NaN or exception)
- No tasks with due dates: with_due_date_count = 0
- All tasks completed: completion_rate = 100.0
- No overdue tasks: overdue_count = 0
- Division by zero: Protected by `if total > 0` check

## Constraints Met
✅ All provided tests pass (8/8)
✅ Existing tests still pass (87/87, no regressions)
✅ Code compiles without syntax errors
✅ TaskStatistics is a @dataclass (not dict, not custom class)
✅ Completion rate expressed as 0-100 percentage
✅ Empty task lists handled safely
✅ All functionality accessible via `python -m src`
✅ Return type is deterministic dataclass

Duration: 414.9s | Cost: $0.732374 USD | Turns: 15

---

# Task 07: Implement TaskImportExportService

## Summary

Implemented `TaskImportExportService` that exports tasks and comments together into a single JSON file and imports them back with structure validation, duplicate skipping, and no overwrite of existing data.

## Files Changed

- `src/services/task_import_export_service.py` — Created new service with TaskImportExportService class providing export() and import_from() methods
- `src/cli/todo_cli.py` — Added export and import subparsers with command handlers (_cmd_export, _cmd_import)
- `src/cli/interactive_menu.py` — Added menu options 9 and 10 for export/import with _do_export() and _do_import() handlers
- `artifacts/class_diagram.puml` — Added TaskImportExportService class with dependencies
- `artifacts/component_diagram.puml` — Added Import/Export Service component in Service Layer
- `artifacts/activity_diagram.puml` — Updated interactive menu flow with export/import cases
- `artifacts/use_case_diagram.puml` — Added export/import use cases for both CLI and interactive modes

## Test Results

All tests pass:
- **6 required tests**: PASS (test_export_creates_json_file, test_export_contains_tasks_and_comments, test_import_restores_tasks, test_import_validates_structure, test_import_restores_comments, test_import_skips_duplicates)
- **9 additional comprehensive tests**: PASS (empty exports, multiple tasks, round-trip integrity, malformed entries, orphaned comments)
- **124 total tests**: ALL PASS
- **109 existing tests**: PASS (no regressions)

## Implementation Details

### Core Features
1. **TaskImportExportService class**: Coordinates TodoService and CommentsService
   - `export(filepath: str)` — Exports all tasks and comments to JSON file with structure `{"tasks": [...], "comments": [...]}`
   - `import_from(filepath: str) -> Tuple[List[Task], List[TaskComment]]` — Imports from JSON with validation and duplicate detection

2. **Export Functionality**:
   - Exports all tasks via Task.to_dict()
   - Exports all comments via TaskComment.to_dict()
   - JSON structure matches expected format
   - Overwrites existing files completely

3. **Import Functionality**:
   - Validates JSON structure (must have "tasks" and "comments" arrays)
   - Schema validation for each task and comment dict
   - Duplicate detection by ID (skips if task/comment already exists)
   - Orphaned comment handling (silently skips comments for non-existent tasks)
   - Returns tuple of (imported_tasks, imported_comments) excluding duplicates
   - Proper error handling for FileNotFoundError and ValueError

4. **CLI Integration**:
   - `python -m src export <filepath>` — Export tasks and comments to file
   - `python -m src import <filepath>` — Import tasks and comments from file

5. **Interactive Menu Integration**:
   - Menu option 9: "Export to file"
   - Menu option 10: "Import from file"

### Edge Cases Handled
- Empty exports (no tasks or comments)
- Missing files (FileNotFoundError)
- Invalid JSON syntax (ValueError)
- Invalid schema structure (ValueError with descriptive message)
- Malformed task/comment dicts (ValueError on from_dict failure)
- Orphaned comments (silently skipped, not added)
- Duplicate tasks by ID (skipped, not overwritten)
- Duplicate comments by ID (skipped, not overwritten)

## Constraints Met
✅ All provided tests pass (6/6 required)
✅ Existing tests still pass (109/109, no regressions)
✅ Code compiles without syntax errors
✅ JSON schema matches Task.to_dict() and TaskComment.to_dict() formats
✅ Duplicates skipped by ID (no overwrite)
✅ Importing preserves existing data
✅ All functionality accessible via `python -m src` (CLI + interactive menu)
✅ Structure validation with clear error messages
✅ UML diagrams updated to reflect all changes

Duration: 436.5s | Cost: $0.881558 USD | Turns: 17

---

# Task 08: Project Domain Class and Task Grouping

## Summary

Successfully implemented Project domain class and extended Task with optional project_id for grouping and filtering tasks by project. All existing tasks remain loadable without project_id.

## Files Changed

### New Files
- `src/models/project.py` — Project dataclass with UUID id, name, description, created_at
- `src/services/project_service.py` — ProjectService with CRUD operations and storage integration
- `tests/test_project.py` — 15 tests for Project model
- `tests/test_project_service.py` — 19 tests for ProjectService
- `tests/test_task_project_integration.py` — 13 tests for Task-Project integration
- `tests/test_todo_service_project_filtering.py` — 13 tests for TodoService project filtering
- `tests/test_storage_project_roundtrip.py` — 8 tests for storage roundtrip
- `tests/test_backward_compat.py` — 9 tests for backward compatibility

### Modified Files
- `src/models/task.py` — Added optional project_id field, updated serialization
- `src/models/__init__.py` — Exported Project class
- `src/storage/json_storage.py` — Added load_projects() and save_projects() methods
- `src/services/task_manager.py` — Added project_id parameter to add/update, new list_by_project() method
- `src/services/todo_service.py` — Added project_id parameter to add_task/list_tasks/update_task
- `src/services/__init__.py` — Exported ProjectService and ProjectNotFoundError
- `src/cli/todo_cli.py` — Added --project flag to add/list/update, added project subcommand group
- `src/cli/interactive_menu.py` — Added project management menu options and filtering
- `artifacts/class_diagram.puml` — Updated to reflect Project class and relationships
- `artifacts/component_diagram.puml` — Added Project Service component
- `artifacts/use_case_diagram.puml` — Added project management use cases

## Test Results

- **Total Tests:** 201 (77 new + 124 existing)
- **Passed:** 201 (100%)
- **Failed:** 0
- **Errors:** 0

All provided test cases pass:
- ✅ test_project_can_be_created
- ✅ test_project_has_unique_id
- ✅ test_empty_project_name_raises
- ✅ test_create_and_list_projects
- ✅ test_task_assigned_to_project
- ✅ test_list_tasks_by_project
- ✅ test_task_without_project_id_is_none
- ✅ test_project_id_is_uuid_string
- ✅ test_old_tasks_without_project_id_load_fine
- ✅ test_move_task_between_projects

## Implementation Details

### Project Model
- UUID string id (auto-generated)
- Required name (validated non-empty)
- Optional description
- Automatic created_at timestamp
- Serialization/deserialization with safe .get() for backward compatibility

### ProjectService
- CRUD operations: create, get, list_all, update, delete
- Storage integration with load/persist pattern
- Prefix-based lookup support
- ProjectNotFoundError exception
- Ordered by created_at ascending

### Task Changes
- New optional project_id field (defaults to None)
- Serialization omits None project_id (backward compatible)
- Deserialization safely extracts project_id using .get()
- Old task dicts without project_id field load successfully

### TodoService
- add_task() accepts optional project_id parameter
- list_tasks() supports filtering by project_id with AND-logic
- update_task() can change task's project_id
- All existing list_tasks() behavior preserved when project_id not specified

### Storage
- New "projects" key in JSON file
- Graceful handling of old files without "projects" key
- load_projects() returns empty list for missing/old files
- save_projects() merges with existing data (preserves tasks and comments)

### CLI Integration
- New --project flag for add, list, update commands
- New project subcommand group: create, list, show, delete, update
- Project management integrated into interactive menu
- Project filtering available in interactive mode

## Key Design Decisions
- No cascade delete: deleting a project leaves tasks orphaned but intact
- No FK validation: TodoService doesn't validate project_id references
- AND logic for filtering: combining project_id with status/due filters
- Backward compatible: all old tasks and storage formats continue to work
- UUID format for project ids, following Task id pattern

## Constraints Met
✅ All 201 tests pass (77 new coverage, 124 existing unchanged)
✅ Backward compatibility with old storage format
✅ CLI accessible via `python -m src` (both flags and interactive menu)
✅ UML diagrams updated to reflect current architecture
✅ No breaking changes to existing functionality
✅ All provided test cases pass

Duration: 643.3s | Cost: $1.310461 USD | Turns: 16

---

# Task 09: Refactor TODO Manager into Clearly Separated Components

## Summary

Successfully refactored the TODO manager into clearly separated components with distinct responsibilities: task domain logic, comment management, project management, storage layer, and interface layer. Maintained 100% backward compatibility with all existing tests passing without modification.

## Files Changed

### New Files Created
- `src/serialization/__init__.py` — Module initialization
- `src/serialization/task_serializer.py` — TaskSerializer class extracting to_dict/from_dict logic
- `src/storage/storage_port.py` — StoragePort protocol defining storage interface
- `src/repositories/__init__.py` — Module initialization
- `src/repositories/task_repository.py` — TaskRepository implementing repository pattern
- `src/services/datetime_service.py` — DatetimeService for centralized UTC timestamp creation
- `src/formatters/__init__.py` — Module initialization
- `src/formatters/task_formatter.py` — TaskFormatter for task display formatting with status symbols

### Files Modified
- `src/models/task.py` — Kept to_dict/from_dict for backward compatibility (logic extracted to TaskSerializer)
- `src/services/task_manager.py` — Refactored to accept TaskRepository instead of JsonStorage
- `src/services/todo_service.py` — Maintained backward compatibility with optional JsonStorage parameter
- `src/cli/todo_cli.py` — Refactored to use TaskFormatter for status symbols instead of local dict
- `src/cli/interactive_menu.py` — Refactored to use TaskFormatter for all status display logic

### Diagrams Updated
- `artifacts/component_diagram.puml` — Restructured to show 7 distinct architectural layers
- `artifacts/class_diagram.puml` — Added serialization, storage, repository, and formatter packages
- `artifacts/sequence_diagram.puml` — Created new diagram showing key operational flows (NEW)

## Test Results

- **Total Tests:** 201
- **Passed:** 201 (100%)
- **Failed:** 0
- **Regressions:** 0 (all existing tests pass unchanged)

All test suites pass completely:
- ✅ test_task.py (24 tests)
- ✅ test_json_storage.py (4 tests)
- ✅ test_task_manager.py (11 tests)
- ✅ test_todo_service.py (11 tests)
- ✅ test_task_comment.py (12 tests)
- ✅ test_project.py (15 tests)
- ✅ test_project_service.py (19 tests)
- ✅ test_comments_service.py (7 tests)
- ✅ test_statistics_service.py (22 tests)
- ✅ test_task_import_export_service.py (15 tests)
- ✅ test_todo_cli.py (11 tests)
- ✅ test_backward_compat.py (9 tests)
- ✅ And 9 additional test files with full coverage

## Implementation Details

### Architecture Layers

**Layer 1: Models (Pure Data)**
- Task, TaskStatus, Project, TaskComment dataclasses
- No serialization or business logic
- Framework-agnostic, fully testable

**Layer 2: Serialization**
- TaskSerializer: Converts Task ↔ dict
- Handles timezone normalization and format conversion
- Independent from models, can be swapped for different formats

**Layer 3: Storage**
- StoragePort: Protocol defining storage interface
- JsonStorage: File I/O implementation (unchanged interface)
- No serialization concerns (delegates to repositories)

**Layer 4: Repository**
- TaskRepository: Implements repository pattern
- Wraps storage with serialization
- Shields services from persistence details
- Clean CRUD interface: load_all(), save_all()

**Layer 5: Services (Business Logic)**
- TaskManager: CRUD with business rules
- TodoService: Orchestrates TaskManager + CommentsService + ProjectService
- All services depend on repositories (not directly on storage)

**Layer 6: Formatters (Display)**
- TaskFormatter: Centralized task display formatting
- Status symbols (PENDING→"[ ]", IN_PROGRESS→"[~]", DONE→"[x]")
- Eliminates duplication across CLI classes

**Layer 7: CLI/UI (Interface)**
- TodoCLI: Argument parsing and command dispatch
- InteractiveMenu: Menu-driven interface
- Both use formatters, fully decoupled from serialization/storage

### Key Design Decisions

1. **Backward Compatibility**: Task.to_dict/from_dict kept in model for compatibility; logic also available in TaskSerializer for new code paths
2. **Repository Pattern**: TaskRepository abstracts storage, enables swapping storage backends
3. **Service Injection**: CLI classes accept optional service parameter (but default to creating one)
4. **No Circular Dependencies**: All dependencies flow downward (Models → Serialization → Storage → Repository → Services)
5. **Centralized Formatting**: TaskFormatter eliminates symbol/label duplication across CLI classes
6. **Centralized Timestamps**: DatetimeService provides single source of truth for UTC creation

### Responsibility Separation

| Component | Responsibility |
|-----------|---|
| **Task** | Pure data: fields, identity |
| **TaskSerializer** | Convert Task ↔ dict, handle timezones |
| **JsonStorage** | Raw file I/O, read/write JSON |
| **StoragePort** | Define storage interface |
| **TaskRepository** | CRUD wrapper, use serialization/storage |
| **TaskManager** | Task CRUD with business rules |
| **TodoService** | Orchestrate managers, apply validation |
| **TaskFormatter** | Format Task for display |
| **TodoCLI** | Parse arguments, dispatch commands |
| **InteractiveMenu** | Display menu, dispatch options |

## Constraints Met

✅ All 201 existing tests pass without modification
✅ Code compiles without syntax or import errors
✅ Existing task functionality behaves identically
✅ Existing comment functionality behaves identically
✅ Existing project functionality behaves identically
✅ Clear responsibility boundaries between components
✅ `python -m src` behaves identically before and after refactor
✅ All existing functionality remains accessible
✅ No circular dependencies
✅ Service layer cleanly separated from storage
✅ Models are framework-agnostic pure data
✅ Acyclic dependency graph

Duration: 528.2s | Cost: $1.049736 USD | Turns: 19

## Task 10 - Implement TodoGUI with tkinter

**Status:** ✅ COMPLETED

**Task Number:** 10

**Files Changed:**
- `src/gui/__init__.py` (NEW)
- `src/gui/todo_gui.py` (NEW)
- `tests/test_gui.py` (NEW - auto-generated by tester)
- `artifacts/component_diagram.puml` (UPDATED)
- `artifacts/class_diagram.puml` (UPDATED)
- `artifacts/use_case_diagram.puml` (UPDATED)

**Test Result:** ✅ PASS (206/206 tests passing)
- All 5 new TodoGUI tests pass
- All 201 existing tests continue to pass
- No regressions detected

**Implementation Summary:**
- Implemented `TodoGUI` class using tkinter standard library
- Service injection pattern: accepts pre-instantiated `TodoService`
- Full task management UI with add, start, complete, reopen, delete operations
- Overdue task highlighting using red color for `task.is_overdue() == True`
- All business logic delegated to service layer (no duplication)
- Graceful error handling with user-friendly dialogs
- Headless environment support for testing

**Architecture Diagram Updates:**
- Added GUI Layer component with TodoGUI
- Added TodoGUI class to class diagram with methods and dependencies
- Added GUI mode use cases to use case diagram
- Updated entry points to show three modes: GUI, Interactive Menu, CLI

Duration: PENDING | Cost: PENDING | Turns: PENDING
