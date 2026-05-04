# Task 08 Analysis: Add Project Mode for Grouping Tasks

## Task Summary

Add a `Project` domain class with support for organizing tasks into projects. Tasks will gain an optional `project_id` field. The implementation must:
- Create new `Project` model with `id: str` (UUID) and `name: str`
- Add `project_id: Optional[str]` to `Task`
- Support creating, listing projects, and filtering tasks by project
- Preserve backward compatibility with existing tasks
- Expose all functionality via CLI (interactive menu + one-shot flags)

## Current Architecture Overview

### Storage Layer
- **JsonStorage** (`src/storage/json_storage.py`):
  - Single-file JSON persistence via `load()` and `save()`
  - Defaults to `~/.todo_data.json` if no path provided
  - Loads entire file into memory; saves entire list atomically
  - Each manager creates its own storage instance or derives path from provided storage
  
- **Task Storage**: Stored in single JSON file containing list of dicts
- **Comment Storage**: Derived path `~/.todo_comments.json` via `_derive_comments_path()`
  - CommentManager overrides storage path to comments file
  - Comments stored separately from tasks

### Domain Models

#### Task (`src/models/task.py`)
- **Dataclass** with fields:
  - `id: str` (default: UUID via `uuid.uuid4()`)
  - `title: str` (required)
  - `description: Optional[str]`
  - `status: TaskStatus` (enum: PENDING, IN_PROGRESS, DONE)
  - `due_date: Optional[datetime]`
  - `created_at: datetime` (default: UTC now)
  - `updated_at: datetime` (default: UTC now)
- **Methods**:
  - `to_dict()`: Serializes to dict; conditionally includes `due_date` only if set
  - `from_dict(data)`: Deserializes; safely parses `due_date` with backward compatibility
  - `is_overdue()`: Returns True if due_date is set, task not DONE, and past due_date
  - `mark_in_progress()`, `mark_done()`, `reopen()`: Mutate status and `updated_at`
  - `is_completed()`: Returns True if status == DONE

#### TaskComment (`src/models/task_comment.py`)
- **Dataclass** with fields:
  - `id: str` (UUID, auto-generated)
  - `task_id: str` (foreign key reference)
  - `content: str` (required)
  - `author: Optional[str]`
  - `created_at: datetime` (UTC)
  - `updated_at: Optional[datetime]`
- **Methods**:
  - `to_dict()`: Omits `updated_at` if None
  - `from_dict(data)`: Safely parses optional `updated_at`

#### TaskStatus (`src/models/task_status.py`)
- Enum with three values: PENDING, IN_PROGRESS, DONE

### Service Layer

#### TaskManager (`src/services/task_manager.py`)
- **State**: `_storage: JsonStorage`, `_tasks: dict[str, Task]`
- **Load/Persist**:
  - `_load()`: Reads JSON, converts each dict to Task via `Task.from_dict()`
  - `_persist()`: Converts all tasks to dicts via `to_dict()`, saves list to storage
- **CRUD Operations**:
  - `add(title, description)`: Creates Task, stores in `_tasks` dict, persists
  - `get(task_id)`: Returns Task by full ID or unique prefix (first 8 chars usable)
  - `list_all()`: Returns list of all tasks
  - `list_by_status(status)`: Filters by TaskStatus
  - `list_by_filter(status, due_after, due_before, overdue)`: Combined filtering
  - `update(task_id, title, description)`: Mutates and persists
  - `set_status(task_id, status)`: Mutates status and persists
  - `delete(task_id)`: Removes from dict and persists
- **Exception**: `TaskNotFoundError` raised if task not found or ambiguous prefix

#### CommentManager (`src/services/comment_manager.py`)
- **State**: `_storage: JsonStorage`, `_comments: dict[str, TaskComment]`
- **Path Derivation**: Overrides storage path via `_derive_comments_path()` to `~/.todo_comments.json`
- **Load/Persist**: Same pattern as TaskManager
- **CRUD Operations**:
  - `add(task_id, content, author)`: Creates comment
  - `get(comment_id)`: Returns comment by full ID or prefix
  - `list_all()`: Returns all comments sorted by created_at
  - `list_by_task(task_id)`: Returns comments for task, sorted by created_at
  - `delete(comment_id)`: Removes from dict and persists
  - `delete_all_by_task(task_id)`: Cascading delete for task deletion
- **Exception**: `CommentNotFoundError`

#### TodoService (`src/services/todo_service.py`)
- **Composition**: Wraps `TaskManager` and `CommentManager`
- **Task Operations**: Delegates to `_manager` (all task methods)
- **Comment Operations**: Delegates to `_comment_manager`
- **Validation**: Validates non-empty titles and descriptions; rejects empty strings
- **Cascade Delete**: `delete_task()` calls `_comment_manager.delete_all_by_task()` before deleting task
- **Import/Export**: Delegates to `ExportService` and `ImportService`
- **Statistics**: Aggregates task counts by status, overdue, and due_date presence

#### ExportService / ImportService (`src/services/import_export_service.py`)
- **Export**: Reads all tasks and comments, writes JSON with `{ "tasks": [...], "comments": [...] }`
- **Import**: Reads JSON, validates schema, handles conflicts per mode (fail/skip/replace)
- **Exception**: `ImportExportError`

### CLI Layer

#### TodoCLI (`src/cli/todo_cli.py`)
- **Parser**: argparse with subcommands for: add, list, show, start, done, reopen, update, delete, is-completed, check-overdue, add-comment, show-comments, delete-comment, stats, export, import
- **Arguments**:
  - `add`: title (positional), `-d/--description` (optional)
  - `list`: `--status`, `--due-after`, `--due-before`, `--overdue`, `--not-overdue`
  - Other commands: task_id/comment_id as positional
- **Status Symbols**: `[ ]` (pending), `[~]` (in progress), `[x]` (done)
- **Error Handling**: Catches `TaskNotFoundError`, `CommentNotFoundError`, `ImportExportError`, `ValueError`

#### InteractiveMenu (`src/cli/interactive_menu.py`)
- **Navigation**: Main menu (11 options) → submenu → actions
- **Menu Options**:
  1. List/filter tasks (status, date range, overdue)
  2. Add task
  3. Show task details
  4. Change status
  5. Update task
  6. Delete task
  7. Check if completed
  8. Check if overdue
  9. Manage comments (submenu with view/add/delete)
  10. View statistics
  11. Import/export (submenu)
- **Helpers**: `_clear()`, `_prompt()`, `_pick()`, `_task_line()`

#### Entry Point (`src/__main__.py`)
- If `sys.argv > 1`: Run `TodoCLI().run()` (one-shot mode)
- Otherwise: Run `InteractiveMenu().run()` (interactive mode)

## Current Task Structure

When a Task is serialized to JSON via `to_dict()`:
```json
{
  "id": "uuid-string",
  "title": "...",
  "description": "...",
  "status": "pending|in_progress|done",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "due_date": "ISO8601"  // omitted if None
}
```

When deserialized via `from_dict()`, missing `due_date` is handled safely (returns None).

## What Must Change to Support Projects

### 1. New Project Model (`src/models/project.py`)
- **Dataclass** with:
  - `id: str` (default: UUID via `uuid.uuid4()`)
  - `name: str` (required, non-empty after validation)
  - `created_at: datetime` (default: UTC now)
  - Optional: `updated_at: datetime`
- **Methods**:
  - `to_dict()`: Serialize to dict for JSON
  - `from_dict(data)`: Deserialize from dict
  - Validation: Reject empty/whitespace-only names

### 2. Task Model Changes (`src/models/task.py`)
- Add `project_id: Optional[str] = None` field
- Update `to_dict()`: Include `project_id` only if set (mirror pattern of `due_date`)
- Update `from_dict()`: Safely parse `project_id` with backward compatibility
- **Backward Compatibility**: Existing tasks without `project_id` must load without error

### 3. New ProjectManager Service (`src/services/project_manager.py`)
- **State**: `_storage: JsonStorage`, `_projects: dict[str, Project]`
- **Pattern**: Mirror TaskManager structure
- **CRUD Operations**:
  - `add(name)`: Validate non-empty name, create Project, persist
  - `get(project_id)`: Return by full ID or prefix
  - `list_all()`: Return all projects
  - `delete(project_id)`: Remove from dict, persist
  - `update(project_id, name)`: Validate and mutate
- **Exception**: `ProjectNotFoundError`
- **Storage Path Derivation**: Need to define where projects are stored (suggest: `.todo_projects.json` derived similarly to comments)

### 4. Task Manager Changes (`src/services/task_manager.py`)
- Add methods to filter by project:
  - `list_by_project(project_id)`: Return tasks assigned to project
  - Optionally: `assign_to_project(task_id, project_id)`: Change project assignment
  - Optionally: `unassign_from_project(task_id)`: Set `project_id` to None
- When filtering (list_by_filter), may need to add optional `project_id` parameter

### 5. TodoService Changes (`src/services/todo_service.py`)
- Inject `ProjectManager` alongside `TaskManager` and `CommentManager`
- **Public methods**:
  - `create_project(name)`: Delegate to ProjectManager
  - `list_projects()`: Delegate to ProjectManager
  - `get_project(project_id)`: Delegate to ProjectManager
  - `list_tasks_by_project(project_id)`: Delegate to TaskManager
  - `assign_task_to_project(task_id, project_id)`: Delegate to TaskManager
  - Optional: `delete_project(project_id)`: Delegate to ProjectManager
- **Validation**: Ensure project exists before assigning task to it

### 6. CLI Changes (`src/cli/todo_cli.py`)
- Add new subcommands:
  - `project create <name>`: Create project
  - `project list`: List all projects
  - `project show <project_id>`: Show project details
  - Optional: `project delete <project_id>`
  - Optional: `project update <project_id> -n/--name <new_name>`
- Add `list` command filters:
  - `--project <project_id>`: Filter tasks by project
- Add task operations:
  - `assign <task_id> <project_id>`: Assign task to project
  - `unassign <task_id>`: Unassign task from project
- Update help text and argparse for new options
- Update error handling for `ProjectNotFoundError`

### 7. Interactive Menu Changes (`src/cli/interactive_menu.py`)
- Add new main menu option (12+):
  - "Manage projects" (submenu: create, list, view, delete)
- Update "List tasks" to support project filtering
- Update "Add task" optionally to assign project at creation
- Update task display to show project assignment
- Update "Update task" to support reassigning project

### 8. Import/Export Updates (`src/services/import_export_service.py`)
- Update export structure to include projects:
  ```json
  {
    "tasks": [...],
    "comments": [...],
    "projects": [...]
  }
  ```
- Update import to handle projects with same conflict modes
- Maintain backward compatibility: importing old files without "projects" key must work
- Return tuple: (tasks_imported, comments_imported, projects_imported)

## Storage Structure After Implementation

Files on disk:
1. `~/.todo_data.json` — Tasks (existing, will have new `project_id` field)
2. `~/.todo_comments.json` — Comments (existing, unchanged)
3. `~/.todo_projects.json` — Projects (new, derived from storage path)

JSON format for tasks after change:
```json
[
  {
    "id": "uuid",
    "title": "...",
    "status": "...",
    "project_id": "uuid|null"
  }
]
```

JSON format for projects:
```json
[
  {
    "id": "uuid",
    "name": "...",
    "created_at": "ISO8601"
  }
]
```

## Backward Compatibility Strategy

1. **Task Model**: `project_id: Optional[str] = None` — existing tasks load fine
2. **Task.from_dict()**: Use `data.get("project_id")` — missing key returns None
3. **Task.to_dict()**: Only include `project_id` if not None (matches `due_date` pattern)
4. **Import Service**: If import file has no "projects" key, treat as empty list
5. **No Migration**: Tasks loaded from old storage files automatically get `project_id=None`

## Key Patterns to Follow

1. **UUID Generation**: Use `uuid.uuid4()` as string, as done in Task and TaskComment
2. **Dataclass Pattern**: All domain objects are dataclasses with field defaults
3. **to_dict/from_dict**: Conditional inclusion of optional fields
4. **Manager Pattern**: Each manager owns a storage instance, dict of objects, and _load/_persist
5. **Validation**: Empty strings/whitespace rejected at service/manager level
6. **Prefix Lookup**: Support first 8 chars of ID for user convenience
7. **Cascading Delete**: When deleting project, decide: delete tasks or unassign them (task spec says "tasks become unassigned")
8. **Storage Path Derivation**: Comments use `_derive_comments_path()` — projects should follow same pattern
9. **Error Handling**: Explicit custom exceptions (ProjectNotFoundError), caught in CLI
10. **Service Composition**: TodoService is facade over managers, no direct manager access in CLI

## Data Flow

```
CLI (todo_cli.py / interactive_menu.py)
  ↓
TodoService (todo_service.py)
  ↓
ProjectManager + TaskManager + CommentManager (services/*.py)
  ↓
JsonStorage (storage/json_storage.py)
  ↓
File system (~/.todo_projects.json, ~/.todo_data.json, ~/.todo_comments.json)
```

## Testing Considerations

Existing tests in `tests/` follow pytest pattern with fixtures for temporary storage.
New tests must cover:
1. Project creation with validation (non-empty names)
2. Task assignment to projects
3. Filtering tasks by project
4. Backward compatibility: old tasks without `project_id` load and work
5. Cascading behavior: deleting project unassigns tasks
6. CLI: new subcommands and flags work end-to-end
7. Import/export: projects included in exported data, imported correctly

## Assumptions

1. **UUID Format**: IDs are string representations of UUID4, same as Task
2. **Storage Path**: Projects stored in `~/.todo_projects.json`, derived via `_derive_projects_path(storage_path)`
3. **Deletion Semantics**: Deleting a project sets tasks' `project_id` to None (not deleted); tasks become "unassigned"
4. **Moving Tasks**: Assigning a task to a different project replaces (not append) the `project_id`
5. **Prefix Lookup**: Projects also support prefix ID lookup like tasks (not explicitly required, but consistent)
6. **No Project Nesting**: Projects are flat; no subprojects
7. **No Archiving**: Projects are either present or deleted; no soft-delete/archival
8. **No Project Metadata**: Only `id`, `name`, `created_at` required; no description, tags, etc.

## Ambiguities

1. **Project Deletion**: Task spec says "tasks become unassigned" — implementation will call `unassign_from_project()` for each task in project before deleting. Does this persist immediately or batch? (Recommend: batch for efficiency)

2. **Project Name Uniqueness**: Not required by spec. Allowing duplicate names is simpler; enforcing uniqueness would require index. (Recommend: allow duplicates, let user avoid them)

3. **Import Conflict Resolution**: When importing projects, what if project ID already exists? (Recommend: same conflict modes as tasks: fail/skip/replace)

4. **One-shot CLI for Project Assignment**: Should `assign` be separate command or flag on `add`? (Recommend: separate command for clarity; optional flag on `add` could be added later)

5. **Project Statistics**: Should there be a statistics view showing project summary? (Recommend: "Could" priority per spec; out of scope for MVP)

## Summary of Implementation Scope

**Must Implement**:
- Project model with id and name
- ProjectManager with CRUD ops
- Task.project_id field (optional)
- TaskManager: list_by_project method
- TodoService: project CRUD and task filtering methods
- CLI: subcommands for project CRUD, task assignment
- Interactive menu: project management submenu
- Backward compatibility for existing tasks
- Import/export with projects

**Should Implement**:
- Validation: non-empty project names
- Naming/structure convention matching (ProjectManager mirrors TaskManager)
- Backward compatibility loading

**Could Implement**:
- Move task between projects
- Delete project (unassign tasks)
- Project metadata beyond name (description, etc.)

