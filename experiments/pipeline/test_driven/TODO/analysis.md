# Task 08 Analysis: Project Domain Class and Task Grouping

## Task Summary
Introduce a `Project` domain class to organize tasks, extend `Task` with an optional `project_id` field for grouping and filtering, and ensure backward compatibility with existing stored tasks that lack `project_id`.

## Current State Analysis

### Task Model Structure
**File:** `/src/models/task.py`

The `Task` dataclass currently has these fields:
- `id`: UUID string (auto-generated)
- `title`: Required string
- `description`: Optional string
- `status`: TaskStatus enum (PENDING, IN_PROGRESS, DONE)
- `created_at`: Datetime with timezone (defaults to UTC)
- `updated_at`: Datetime with timezone (defaults to UTC)
- `due_date`: Optional datetime with timezone

Key methods:
- `to_dict()`: Serializes task to dictionary, includes `due_date` only if not None
- `from_dict()`: Deserializes from dictionary using `data.get()` for optional fields
- Status mutation methods: `mark_in_progress()`, `mark_done()`, `reopen()` (update `updated_at` to CEST)
- Query methods: `is_completed()`, `is_pending()`, `is_in_progress()`, `is_overdue()`

### Storage and Serialization
**File:** `/src/storage/json_storage.py`

The JSON storage uses a dict structure:
```json
{
  "tasks": [...],
  "comments": [...]
}
```

Key patterns:
- `load()` returns a list of task dictionaries
- `save(tasks)` expects a list of task dictionaries
- Supports legacy list format for backward compatibility
- Preserves existing data structure when saving (merges with existing tasks/comments)

**Serialization chain:**
1. Task → dict via `to_dict()` → JSON string via `json.dump()`
2. JSON string via `json.load()` → dict → Task via `from_dict()`

### TodoService and TaskManager
**Files:** `/src/services/todo_service.py`, `/src/services/task_manager.py`

**TaskManager** (lower level):
- Owns `_tasks: dict[str, Task]` in-memory cache
- Methods: `add()`, `get()`, `list_all()`, `list_by_status()`, `update()`, `set_status()`, `delete()`
- Loads all tasks from storage on init via `_load()`
- Persists to storage after every mutation via `_persist()`

**TodoService** (higher level, public API):
- Wraps TaskManager
- `add_task()`: Creates task, optionally sets due_date
- `list_tasks()`: Filters by status, due_before, due_after, overdue (boolean)
- Status change: `start_task()`, `complete_task()`, `reopen_task()`
- CRUD: `get_task()`, `update_task()`, `delete_task()`

### Current Filtering Capabilities
`TodoService.list_tasks()` currently supports:
- `status: Optional[TaskStatus]` — exact match on task status
- `due_before: Optional[datetime]` — tasks with due_date < cutoff
- `due_after: Optional[datetime]` — tasks with due_date > cutoff
- `overdue: bool` — filter to only overdue tasks (due_date < now)

All filters are combined with AND logic on the in-memory task list.

### CLI Entry Points
**File:** `/src/cli/todo_cli.py`

Available commands:
- `add` — add task (--description optional)
- `list` — list tasks (--status, --due-before, --due-after, --overdue)
- `show` — show task details
- `start` — mark in-progress
- `done` — mark done
- `reopen` — reopen task
- `update` — update title/description
- `delete` — delete task
- `statistics` — show aggregates
- `export` — export to JSON file
- `import` — import from JSON file

The CLI runs through argparse subcommands. Interactive menu also exists.

### Model Exports
**File:** `/src/models/__init__.py`

Currently exports: `Task`, `TaskStatus`, `TaskComment`

## Key Design Constraints

1. **Backward Compatibility**: Tasks stored without `project_id` must load successfully. The `from_dict()` method must handle missing `project_id` as None.

2. **JSON Persistence**: The existing JSON structure and serialization pattern must be maintained. A task without `project_id` should not have it in the dict (or have it as null).

3. **In-Memory Caching**: TaskManager keeps all tasks in `_tasks` dict. New filtering by project_id must work with this existing pattern.

4. **Service Layering**: TodoService acts as a public facade; it should expose project filtering to callers, but TaskManager can be extended with lower-level project support.

5. **CLI Integration**: Any new project-related functionality must be wired into the argparse CLI and interactive menu to be accessible.

## Files to Create or Modify

### New Files

1. **`src/models/project.py`**
   - Define `Project` dataclass with:
     - `id`: UUID string (auto-generated)
     - `name`: Required string
     - `description`: Optional string
     - `created_at`: Datetime with timezone
   - Methods: `to_dict()`, `from_dict()`, `__repr__()` for CLI display

2. **`src/services/project_service.py`**
   - `ProjectService` class managing Project CRUD
   - Constructor: takes optional JsonStorage
   - Methods:
     - `create(name: str, description: Optional[str] = None) -> Project`
     - `get(project_id: str) -> Project`
     - `list_all() -> List[Project]`
     - `update(project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Project`
     - `delete(project_id: str) -> void`
   - Will need separate storage keys in JSON (similar to "tasks" and "comments")

### Modified Files

1. **`src/models/task.py`**
   - Add field: `project_id: Optional[str] = None`
   - Update `to_dict()` to include `project_id` only if not None
   - Update `from_dict()` to safely extract `project_id` using `data.get("project_id")`
   - No changes to timezone handling or other logic

2. **`src/models/__init__.py`**
   - Export `Project` alongside `Task`, `TaskStatus`, `TaskComment`

3. **`src/storage/json_storage.py`**
   - Add `load_projects()` and `save_projects()` methods
   - Store projects under "projects" key in JSON, preserving existing merging pattern
   - Maintain backward compatibility (file may lack "projects" key initially)

4. **`src/services/todo_service.py`**
   - Add optional `project_id: Optional[str] = None` parameter to:
     - `add_task()` — allow specifying project when creating
     - `list_tasks()` — add project_id filter (in addition to existing filters)
   - No changes to status, due_date, or other existing logic
   - Validation: optionally verify project_id exists (or defer to ProjectService)

5. **`src/services/task_manager.py`**
   - Add lower-level `list_by_project(project_id: str) -> List[Task]` method
   - No changes to existing public API; all project filtering done in TodoService

6. **`src/cli/todo_cli.py`**
   - Extend `add` command: add `--project` or `-p` optional argument
   - Extend `list` command: add `--project` optional filter argument
   - Add new `project` subcommand group:
     - `project create` — create new project
     - `project list` — list all projects
     - `project show <id>` — show project details
     - `project delete <id>` — delete project
     - `project update <id>` — update project name/description

7. **`src/cli/interactive_menu.py`**
   - Add project management menu option
   - Update task list display to optionally show project (or only when filtering)
   - Add "create project" and "filter by project" menu options

## Data Format Examples

### Task with project_id (new)
```json
{
  "id": "abc-123",
  "title": "Build dashboard",
  "description": "Create analytics dashboard",
  "status": "in_progress",
  "project_id": "proj-456",
  "created_at": "2026-05-03T10:00:00+00:00",
  "updated_at": "2026-05-03T10:00:00+00:00",
  "due_date": "2026-06-01T12:00:00+02:00"
}
```

### Task without project_id (backward compatible)
```json
{
  "id": "xyz-789",
  "title": "Review PR",
  "description": null,
  "status": "pending",
  "created_at": "2026-05-03T09:00:00+00:00",
  "updated_at": "2026-05-03T09:00:00+00:00"
}
```
Note: `project_id` key omitted entirely (not null), `due_date` omitted if None.

### Project
```json
{
  "id": "proj-456",
  "name": "Platform Modernization",
  "description": "Upgrade our backend to microservices",
  "created_at": "2026-05-01T08:00:00+00:00"
}
```

### Full storage file (after Task 08)
```json
{
  "tasks": [...],
  "comments": [...],
  "projects": [...]
}
```

## Backward Compatibility Strategy

1. **Reading old files**: When `Task.from_dict()` is called on a dict without `project_id`, it defaults to None. No error.

2. **Writing**: New tasks always include `project_id` in dict (as None if not set). Existing tests should not break because `from_dict(task.to_dict())` round-trips correctly.

3. **Storage upgrade**: The first time the app writes, old-format files are preserved (no "projects" key yet). If a project is created/deleted, the "projects" key appears.

4. **Service initialization**: ProjectService and TodoService can be instantiated independently. TodoService doesn't require ProjectService to exist initially (project_id is optional).

## Integration Points

1. **TodoService.add_task()**: Needs to accept optional project_id. Should optionally validate that project exists (or leave as unchecked foreign key for simplicity).

2. **TodoService.list_tasks()**: Needs to filter by project_id when provided. Can use TaskManager's new `list_by_project()` internally.

3. **Task.from_dict()**: Must safely extract project_id; no error if missing.

4. **CLI `add` command**: Parse `--project` flag, pass to `add_task()`.

5. **CLI `list` command**: Parse `--project` flag, pass to `list_tasks()`.

6. **Interactive menu**: Detect if projects exist; optionally show on task lines or in a submenu.

## Testing Implications

1. **Backward compatibility tests**: Ensure old task dicts (no project_id) load as Task with project_id=None.

2. **Task.from_dict() tests**: Test with and without project_id key in input dict.

3. **Task.to_dict() tests**: Verify project_id omitted from dict if None, included if set.

4. **TodoService.list_tasks() tests**: Add tests for project_id filter combined with other filters.

5. **ProjectService tests**: Full CRUD cycle, unique ID generation, from_dict/to_dict round-trips.

6. **Storage tests**: Verify projects are saved/loaded, old files without projects key still work.

7. **CLI tests**: Test new `--project` flags on `add` and `list`, new `project` subcommand.

## Scope: In vs. Out

**In (Task 08 scope):**
- Project domain class
- Task.project_id optional field
- ProjectService CRUD
- TodoService integration (add_task with project_id, list_tasks by project)
- CLI: project commands and --project flag on add/list
- Backward compatibility for tasks without project_id

**Out (deferred):**
- Permission/authorization by project
- Project templates or quick-start
- Task grouping by other attributes (assignee, tag, category)
- Project archiving/soft delete
- Bulk operations across projects
- Advanced filtering (e.g., "all tasks in project X without due date")

## Remaining Ambiguities

1. **Foreign key validation**: Should TodoService.add_task() verify that a provided project_id actually exists, or allow orphaned references?
   - **Assumption**: Allow unchecked references for now (simpler, no circular dependency). ProjectService can validate on its side.

2. **Deletion cascade**: If a project is deleted, what happens to its tasks?
   - **Assumption**: Tasks are NOT automatically deleted. Their project_id becomes orphaned (which is allowed). User must manually delete or reassign tasks if needed.

3. **Project filtering priority**: If user provides both --status and --project filters, how are they combined?
   - **Assumption**: AND logic (tasks must match both filters). Consistent with current status + due_date filtering.

4. **Project list sorting**: How should `project list` output be ordered?
   - **Assumption**: By created_at ascending (oldest first) to match task display conventions.

5. **Default project**: Is there a "no project" or "default project" concept?
   - **Assumption**: No default project. project_id=None means "unassigned to any project".

## Summary

Task 08 adds lightweight project support to the TODO app by:
1. Introducing a simple Project model and ProjectService
2. Extending Task with optional project_id (backward compatible)
3. Extending TodoService and TaskManager with project-aware filtering
4. Wiring project management and task-project association into the CLI
5. Maintaining full backward compatibility with existing task data

The implementation is minimal, focused, and follows existing patterns (dataclass models, service layer, JSON storage, argparse CLI).
