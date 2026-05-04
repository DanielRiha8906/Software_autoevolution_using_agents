# Task 08 Analysis: Project Domain Model and Organization

**Analysis Date:** 2026-05-03  
**Working Directory:** `experiments/pipeline/user_stories/TODO/`

## 1. What Task 08 Is Asking For

Implement a project management feature that allows tasks to be grouped and organized by projects. The feature must:

- Create a new `Project` domain class with `id` (UUID) and `name` fields
- Add an optional `project_id` field to the existing `Task` model
- Support full CRUD operations on projects (create, list, delete)
- Support filtering tasks by project
- Support moving tasks between projects
- Maintain backward compatibility with existing tasks (tasks without project_id continue to work)
- Support projects being deleted without cascading to tasks (tasks become unassigned)
- Enforce project name non-emptiness
- Be accessible via both interactive menu AND CLI flags

---

## 2. Current Codebase Structure

### Models Layer (`src/models/`)
- **task.py** - Task dataclass with fields: id, title, description, status, created_at, updated_at, due_date, comments
- **task_status.py** - Enum (PENDING, IN_PROGRESS, DONE)
- **task_comment.py** - TaskComment dataclass (id, content, task_id, author, created_at, updated_at)
- **task_summary_report.py** - Report model (total, pending, in_progress, done, overdue, due_date_set, completion_rate, avg_days)

**KEY OBSERVATION:** Tasks use UUID strings for `id` generated with `uuid.uuid4()`. All models have `to_dict()` and `from_dict()` methods for JSON serialization.

### Services Layer (`src/services/`)
- **task_manager.py** - Low-level CRUD for tasks with persistence
  - Methods: add(), get(), list_all(), list_by_status(), list_by_due_date_range(), update(), set_status(), delete(), add_comment(), get_comments(), delete_comment(), edit_comment()
  - Uses dictionary `_tasks: dict[str, Task]` as in-memory cache, persists via JsonStorage._persist()
  - Supports prefix lookup for task IDs (first 8 chars)
  - Raises TaskNotFoundError when task not found

- **todo_service.py** - High-level business logic wrapping TaskManager
  - Methods: add_task(), list_tasks(), list_tasks_by_week/month/year(), get_task(), start_task(), complete_task(), reopen_task(), update_task(), set_due_date(), delete_task(), add_comment(), get_comments(), delete_comment(), edit_comment(), generate_report(), export_tasks(), import_tasks()
  - Validates inputs (empty titles, timezone-aware datetimes)

- **import_validator.py** - Validates JSON files for import, handles task dict validation

### Storage Layer (`src/storage/`)
- **json_storage.py** - Simple JSON persistence
  - Stores at `~/.todo_data.json` by default
  - Methods: load() returns list[dict], save(tasks: list[dict])
  - Creates parent directories as needed

### CLI Layer (`src/cli/`)
- **todo_cli.py** - Command-line interface using argparse
  - Subcommands: add, list, show, start, done, reopen, update, delete, due-date, add-comment, list-comments, delete-comment, edit-comment, report, export, import
  - Supports filtering: --status, --due-before, --due-after, --week, --month, --year, --overdue
  - Returns exit code 0 on success, 1 on error
  - Catches TaskNotFoundError and ValueError, prints to stderr

- **interactive_menu.py** - Terminal UI menu system
  - Clears screen, prints header, lists tasks, offers menu options
  - Menu options: 1=List, 2=Add, 3=Show, 4=Change status, 5=Update, 6=Set due date, 7=Delete, 8=Manage comments, 9=Report, 10=Export, 11=Import

### Entry Point (`src/__main__.py`)
- Routes to TodoCLI if arguments present, otherwise starts InteractiveMenu

---

## 3. What Currently Exists vs What Needs to Be Added

### Currently Exists
- Task model with all persistence plumbing (to_dict/from_dict, serialization to JSON)
- TaskComment model with same pattern
- Complete task CRUD in TaskManager + TodoService
- Import/export functionality with validation
- Full CLI with subcommands and interactive menu
- Test suite covering tasks, comments, import/export, date filtering

### Needs to Be Added

#### 3.1 New Domain Class
- **`Project` dataclass** (new file: `src/models/project.py`)
  - Fields: id (UUID string), name (string)
  - Methods: to_dict(), from_dict() for JSON serialization
  - Validation: name cannot be empty (check in __post_init__)

#### 3.2 Task Model Changes
- Add optional `project_id: Optional[str] = None` field to Task
- Update Task.to_dict() to include project_id
- Update Task.from_dict() to handle project_id (must handle missing field for backward compatibility)
- Update existing test for task serialization/deserialization to verify project_id field

#### 3.3 Service Layer
- **`ProjectManager` class** (new file: `src/services/project_manager.py`)
  - Similar to TaskManager pattern
  - Methods: add(), get(), list_all(), delete()
  - In-memory dict `_projects: dict[str, Project]`
  - Persistence via JsonStorage (may need separate file or merged storage)
  - Raises ProjectNotFoundError when project not found

- **Update `TodoService`**
  - Add methods: create_project(), list_projects(), delete_project(), list_tasks_by_project(), move_task_to_project()
  - Validation: project name non-empty

- **Update `TaskManager`**
  - Add method: list_by_project(project_id) to filter tasks by project_id
  - Ensure delete() and other mutation methods preserve project_id field

#### 3.4 Storage Changes
- **Storage architecture decision needed:**
  - **Option A (preferred based on existing patterns):** Extend JsonStorage to handle both tasks and projects in one file (JSON array at root, or dict with "tasks" and "projects" keys)
  - **Option B:** Use separate JSON files (~/.todo_projects.json alongside ~/.todo_data.json)
  - Currently JsonStorage stores a simple list of task dicts at root

#### 3.5 CLI Layer
- **Update `TodoCLI`** with new subcommands:
  - `create-project <name>` - Create a project, print project ID
  - `list-projects` - List all projects with task counts
  - `delete-project <project_id>` - Delete project (tasks become unassigned)
  - `add-task` enhancement: optional `--project` flag to assign task to project on creation
  - `update` enhancement: optional `--project` flag to move task to project
  - `list` enhancement: optional `--project` flag to filter by project

- **Update `InteractiveMenu`**
  - Add menu option for project management (new menu level: Projects / Tasks)
  - Menu items: Create project, List projects, Manage project tasks, Delete project
  - When listing tasks, show which project they belong to (or "Unassigned")
  - When updating/creating task, allow assigning to project

#### 3.6 Models __init__.py
- Export new Project class: `from .project import Project`

#### 3.7 Services __init__.py
- May need to export ProjectManager if used externally

---

## 4. Files That Will Need Modifications

### New Files to Create
1. `src/models/project.py` - New Project dataclass
2. `src/services/project_manager.py` - New ProjectManager CRUD class
3. `tests/test_project.py` - Unit tests for Project model
4. `tests/test_project_manager.py` - Unit tests for ProjectManager
5. `tests/test_task_project_integration.py` - Integration tests for task-project interaction

### Files to Modify

**Critical Changes:**
- `src/models/task.py`
  - Add `project_id: Optional[str] = None` field
  - Update `to_dict()` method to include project_id
  - Update `from_dict()` classmethod to extract project_id with `.get("project_id")` (supports old format)

- `src/models/__init__.py`
  - Add `from .project import Project` export

- `src/services/todo_service.py`
  - Add create_project(), list_projects(), delete_project() methods
  - Add list_tasks_by_project() method
  - Add move_task_to_project() method
  - Add validation for project_id when passed to task operations

- `src/services/task_manager.py`
  - Add list_by_project(project_id) method
  - Ensure _tasks dict still handles tasks with and without project_id

- `src/storage/json_storage.py` (or create new)
  - **Decision required:** How to store both tasks and projects?
    - If merging: Change save/load to handle dict with {"tasks": [...], "projects": [...]}
    - If separate files: Create JsonProjectStorage or extend JsonStorage with mode parameter

- `src/cli/todo_cli.py`
  - Add 5-6 new subparsers for project commands
  - Implement command handlers (_cmd_create_project, _cmd_list_projects, _cmd_delete_project, etc.)
  - Update _cmd_add to accept optional --project flag
  - Update _cmd_update to accept optional --project flag for moving tasks

- `src/cli/interactive_menu.py`
  - Add new top-level menu option (or submenu structure) for project management
  - Implement _do_manage_projects() and related project interaction methods
  - Update _do_add() to allow selecting project
  - Update task listing to show project information

**Tests (updates):**
- `tests/test_task.py`
  - Add tests for project_id field in Task
  - Test task serialization/deserialization with project_id present and absent

- All other test files that create Task objects should verify backward compatibility with project_id

---

## 5. Key Implementation Challenges and Decisions

### 5.1 Storage Architecture
**Challenge:** Current JsonStorage stores only task dicts in a simple array. Projects need persistent storage too.

**Options:**
- **Option A (Simplest):** Store everything in one JSON file with structure:
  ```json
  {
    "tasks": [{...}, {...}],
    "projects": [{...}, {...}]
  }
  ```
  Requires modest refactor of JsonStorage.load() (returns dict not list) and TaskManager._load()

- **Option B:** Use separate files (~/.todo_projects.json and ~/.todo_data.json)
  - Simpler storage changes (new JsonProjectStorage class)
  - More file I/O overhead
  - Import/export complexity increases

**Recommendation:** Option A is cleaner architecturally and aligns with test patterns (single storage object).

### 5.2 Task Deletion Cascade (or Not)
**Requirement:** "Deleting a project leaves tasks unassigned."

**Implementation:** When delete_project(project_id) is called:
- Delete the project from _projects
- Iterate through _tasks, set project_id = None for all tasks with that project_id
- Persist both

Do NOT delete tasks; this is an orphaning operation, not cascade delete.

### 5.3 Backward Compatibility on Load
**Challenge:** Existing .todo_data.json files have no project_id field; loading them must not fail.

**Solution:** 
- Task.from_dict() uses `.get("project_id")` with default None
- Storage layer handles old format gracefully:
  - Old format: `[{task}, {task}]` → new format: `{"tasks": [{task}, {task}], "projects": []}`
  - OR gracefully detect old format and migrate on first load

**Test coverage needed:**
- Load old task file without project_id → tasks load with project_id=None
- Load new task file with project_id → tasks load with project_id preserved
- Export and re-import preserves project_id

### 5.4 Prefix Lookup for Projects
**Question:** Should projects support prefix lookup like tasks?

**Assumption:** Yes. Implement similar logic in ProjectManager.get() (not required by spec but consistent with existing pattern).

### 5.5 Project Name Uniqueness
**Requirement mentions:** "Project names cannot be empty"

**Assumption:** Project names are NOT required to be unique (user can have two projects named "Work" if they want). Only non-empty is enforced.
- If uniqueness is required, it would be mentioned explicitly
- Empty name validation via __post_init__ in Project class

### 5.6 CLI Naming Conventions
**Existing patterns:**
- Subcommand names use hyphens: add, list, add-comment, delete-comment
- Long names: list-comments, delete-comment, edit-comment
- Flags use hyphens: --status, --due-before, --project

**New commands should follow:**
- `create-project <name>` (not add-project)
- `list-projects` (not list-project, matches pattern of list-comments)
- `delete-project <project_id>`
- `move-task <task_id> --project <project_id>` (or integrate into update?)

### 5.7 Interactive Menu Structure
**Current structure:** Single main menu (1-11)
**Challenge:** Adding projects increases menu options; need to avoid overwhelming menu

**Options:**
- Add "Projects" as menu option 12 that opens sub-menu
- OR replace "List" menu with top-level chooser (Tasks vs Projects view)

**Assumption:** Add "12. Manage Projects" menu option that opens ProjectManager sub-menu (Create/List/Delete/Assign).

---

## 6. Scope Signals: What's In, Out, Borderline

### Explicitly In (per requirements)
- Project domain class with id and name
- Add project_id to Task (optional)
- Create/list/delete projects
- Filter tasks by project
- Move tasks between projects
- Delete project → tasks become unassigned (not deleted)
- Project names cannot be empty
- CLI flags AND interactive menu

### Explicitly Out
- Project permissions / access control
- Project templates or hierarchy
- Project archive/soft-delete
- Recurring tasks or task templates
- Gantt charts or visualizations

### Borderline (Assumptions Made)
- **Project name uniqueness:** Not enforced (names can repeat)
- **Prefix lookup for projects:** Implemented (consistent with Task pattern)
- **Menu structure for projects:** Separate sub-menu, not inline with tasks
- **Export/import of projects:** Not mentioned in requirements; assume projects are NOT exported/imported in task export files. Or they are? **[Clarification needed]**

---

## 7. Key Questions / Ambiguities

1. **Export/Import behavior for projects:**
   - Should `export` include both tasks AND projects, or only tasks?
   - If a task refers to a project_id that doesn't exist locally, what happens on import?
   - **Working assumption:** Task export includes project_id field. Projects are managed separately. Import validates that project_id exists or sets to None.

2. **Storage format for backward compatibility:**
   - Should load() auto-migrate old .todo_data.json to new format on first load, or keep old format supported indefinitely?
   - **Working assumption:** Auto-migrate on first load, write new format to disk.

3. **UI/Menu entry point for projects:**
   - Should the default menu show projects or tasks first?
   - **Working assumption:** Current default (tasks list) is unchanged. Add "12. Manage Projects" option to main menu.

4. **Task creation with project:**
   - Should `add` command require project or allow optional --project?
   - **Working assumption:** Optional --project flag. Tasks can be created unassigned, assigned later.

5. **Moving tasks between projects:**
   - New command `move-task` or extend `update` with --project flag?
   - **Working assumption:** Extend `update` command with --project flag to move task to project (simpler than new command).

---

## 8. Suggested Implementation Priority

### Phase 1: Core Domain Model (Foundation)
1. **`src/models/project.py`** - Create Project dataclass
   - id (UUID), name (string with validation)
   - to_dict(), from_dict()
2. **Task.project_id field** - Add optional field, update serialization
3. **`src/models/__init__.py`** - Export Project

### Phase 2: Storage & Service Layer
4. **Storage architecture decision & refactor**
   - Extend JsonStorage or create separate file handling
   - Update TaskManager._load()/_persist() to handle storage format
5. **`src/services/project_manager.py`** - ProjectManager CRUD class
6. **`src/services/todo_service.py`** - Add project-related methods to TodoService
7. **TaskManager.list_by_project()** - Add project filtering to TaskManager

### Phase 3: CLI (Critical for "accessible via CLI")
8. **`src/cli/todo_cli.py`** - Add project subcommands
   - create-project, list-projects, delete-project
   - Enhance add/update with --project flag
9. **Fix __help__ output** - Ensure all project commands visible in --help

### Phase 4: Interactive Menu
10. **`src/cli/interactive_menu.py`** - Add project management menu
    - Sub-menu for projects
    - Integrate with task creation/updating

### Phase 5: Testing
11. **Unit tests** - Project model, ProjectManager, integration
12. **Backward compatibility tests** - Old format loading, migration
13. **CLI tests** - Project commands, flags, error handling

### Phase 6: Documentation & Cleanup
14. **Verify __help__ is complete**
15. **Verify all commands reachable via both CLI and menu**

---

## 9. Critical Implementation Patterns to Follow

Based on code review, any new feature must:

1. **Use dataclass with uuid.uuid4() for ID generation**
   ```python
   id: str = field(default_factory=lambda: str(uuid.uuid4()))
   ```

2. **Implement to_dict() and from_dict() for serialization**
   - to_dict(): Convert all datetime to isoformat(), enums to .value
   - from_dict(): Reverse; use .get() for optional fields

3. **Use Optional[T] for nullable fields, default to None in dataclass**

4. **In Manager classes, use dict cache pattern:**
   ```python
   self._dict[id] = model
   self._persist()  # after mutations
   ```

5. **In Service layer, validate inputs before passing to Manager**

6. **In CLI, use argparse subparsers, set_defaults(func=handler), catch exceptions**

7. **Prefix lookup pattern for ID resolution:**
   ```python
   matches = [t for tid, t in self._dict.items() if tid.startswith(task_id)]
   ```

8. **Always use timezone-aware datetimes (timezone.utc) in domain models**

---

## 10. Summary of Changes by Layer

| Layer | Changes |
|-------|---------|
| **Models** | New Project; Task adds project_id field |
| **Storage** | Refactor to handle tasks + projects (single or dual JSON files) |
| **Services** | New ProjectManager; TodoService gains project methods; TaskManager gains project filtering |
| **CLI** | 5+ new subcommands; enhanced add/update with --project flag |
| **Menu** | New "Manage Projects" menu option with sub-items |
| **Tests** | New test files for Project/ProjectManager; updates to existing tests for backward compat |

**Estimated scope:** ~400-600 lines of new code, ~200-300 lines of refactoring in existing files.

