# Layer Separation Analysis: TODO Application

## Executive Summary

The TODO application currently has a reasonable logical layer structure divided into five key components (models, storage, services, CLI, and utilities), but exhibits several coupling problems that prevent clean separation. The most critical issues are:

1. **Mixed responsibility in CLI layer**: Both TodoCLI and InteractiveMenu import and catch exceptions from multiple service/manager layers
2. **Service-to-manager coupling**: TodoService acts as a facade but directly instantiates and manages three separate manager instances
3. **Manager-to-storage coupling**: All three managers (TaskManager, CommentManager, ProjectManager) directly access `_path` properties and manipulate storage files
4. **Public interface violations in import/export**: ImportService directly accesses private `_tasks`, `_comments`, `_projects` dict attributes on managers
5. **Missing abstraction**: No clear repository or unit-of-work pattern to coordinate changes across multiple related entities

The application exhibits **NO circular dependencies** in the traditional sense, but has **tight vertical coupling** where lower layers are tightly bound to specific implementations.

---

## Current Layer Structure

### Layer 1: Entry Point
- **File**: `src/__main__.py`
- **Responsibility**: Route between CLI and interactive modes
- **Dependencies**: CLI layer (TodoCLI, InteractiveMenu)
- **Behavior**: If arguments present, use CLI mode; otherwise use interactive menu

### Layer 2: CLI (Interface/Presentation)
- **Files**: 
  - `src/cli/todo_cli.py` — Argument-parsed command handler
  - `src/cli/interactive_menu.py` — REPL-style interactive interface
- **Responsibility**: User interaction, command parsing, output formatting
- **Dependencies**: 
  - Services layer (TodoService)
  - Models layer (Task, TaskStatus, TaskComment, Project)
  - Storage layer (JsonStorage) — **Tight coupling here**
  - Exception types from all manager layers
- **Current issues**:
  - Knows about JsonStorage constructor directly
  - Must catch exceptions from TaskManager, CommentManager, ProjectManager, and ImportExportError separately
  - Creates its own TodoService instance rather than receiving injected dependency

### Layer 3: Services (Business Logic)
- **File**: `src/services/todo_service.py`
- **Type**: Facade/Orchestrator
- **Responsibility**: 
  - High-level business operations (add_task, complete_task, get_statistics, etc.)
  - Cascading deletes (delete_task cascades to delete_comment)
  - Cross-entity validation (verify project exists before assigning task)
  - Delegates to three managers for CRUD operations
- **Dependencies**: 
  - TaskManager, CommentManager, ProjectManager
  - Models layer (Task, TaskComment, TaskStatus, Project, TaskStatistics)
  - Storage layer (JsonStorage)
- **Current issues**:
  - Tightly couples to specific manager implementations
  - Creates managers internally rather than receiving them
  - No abstraction layer to swap implementations

### Layer 4: Managers (Data Access / Domain Operations)
- **Files**:
  - `src/services/task_manager.py` — CRUD for tasks, task filtering
  - `src/services/comment_manager.py` — CRUD for comments
  - `src/services/project_manager.py` — CRUD for projects
- **Responsibility**: 
  - CRUD operations on specific entity types
  - In-memory caching of entities
  - Persistence delegation to storage
  - Prefix-based ID resolution (matching short IDs to full UUIDs)
- **Dependencies**: 
  - Models layer (Task, TaskComment, Project, TaskStatus)
  - Storage layer (JsonStorage)
- **Current issues**:
  - Direct file path manipulation: `_derive_comments_path()`, `_derive_projects_path()`
  - Direct access to `_storage._path` and override of `_storage._path` property
  - Duplicate code pattern (load/persist, get with prefix matching) across all three managers
  - Exception types defined in manager layer but needed in CLI layer

### Layer 5: Storage (Persistence)
- **File**: `src/storage/json_storage.py`
- **Type**: Simple persistence abstraction
- **Responsibility**: JSON file read/write operations
- **Dependencies**: Only stdlib (pathlib, json)
- **Current design**: 
  - Single file for task data (or custom path)
  - Derived files for comments and projects (determined by CallerManagers)
  - Proper file existence checks and parent directory creation

### Layer 6: Models (Domain Entities)
- **Files**:
  - `src/models/task.py` — Task dataclass with status, due_date, project_id
  - `src/models/task_comment.py` — TaskComment dataclass with foreign key to task
  - `src/models/project.py` — Project dataclass
  - `src/models/task_status.py` — TaskStatus enum
  - `src/models/task_statistics.py` — TaskStatistics dataclass
- **Responsibility**: Entity definitions and serialization
- **Dependencies**: Only stdlib (dataclasses, uuid, datetime)
- **Current design**: Clean, well-isolated. No cross-dependencies between models.

### Layer 7: Import/Export Service
- **File**: `src/services/import_export_service.py`
- **Classes**: ExportService, ImportService
- **Responsibility**: Bulk export/import of tasks, comments, and projects
- **Dependencies**: All manager types
- **Current issues**:
  - Directly accesses manager private attributes: `self._task_manager._tasks[task.id] = task`
  - Calls private methods: `self._task_manager._persist()`
  - Should use public interfaces for consistency

### Layer 8: Utilities (Optional)
- **File**: `src/utils/timezone_utils.py`
- **Responsibility**: CEST (Europe/Paris) timezone conversion
- **Usage**: Imported by models/services but largely unused in current code
- **Current design**: Well-isolated, no dependencies on domain logic

---

## Public Interfaces That Must Be Preserved

### TodoService (Primary Public API)
```python
class TodoService:
    def add_task(title, description=None) -> Task
    def get_task(task_id) -> Task
    def list_tasks(status=None, due_after=None, due_before=None, overdue=None) -> List[Task]
    def start_task(task_id) -> Task
    def complete_task(task_id) -> Task
    def reopen_task(task_id) -> Task
    def update_task(task_id, title=None, description=None) -> Task
    def delete_task(task_id) -> None
    def add_comment(task_id, content, author=None) -> TaskComment
    def get_comments(task_id) -> List[TaskComment]
    def delete_comment(comment_id) -> None
    def get_statistics() -> TaskStatistics
    def create_project(name) -> Project
    def list_projects() -> List[Project]
    def get_project(project_id) -> Project
    def delete_project(project_id) -> None
    def list_tasks_by_project(project_id) -> List[Task]
    def assign_task_to_project(task_id, project_id) -> Task
    def unassign_task_from_project(task_id) -> Task
    def update_project(project_id, name) -> Project
    def export_tasks_and_comments(filepath) -> Tuple[int, int, int]
    def import_tasks_and_comments(filepath, mode) -> Tuple[int, int, int, int]
```

### Exception Types (Caught by CLI)
```python
TaskNotFoundError (from task_manager)
CommentNotFoundError (from comment_manager)
ProjectNotFoundError (from project_manager)
ImportExportError (from import_export_service)
ValueError (raised by service validation)
```

### Manager Public Interfaces (Used by TodoService and Import/Export)
**TaskManager**:
- `add(title, description=None) -> Task`
- `get(task_id) -> Task`
- `list_all() -> List[Task]`
- `list_by_status(status) -> List[Task]`
- `list_by_filter(...) -> List[Task]`
- `update(task_id, title=None, description=None) -> Task`
- `set_status(task_id, status) -> Task`
- `delete(task_id) -> None`
- `list_by_project(project_id) -> List[Task]`
- `assign_to_project(task_id, project_id) -> Task`
- `unassign_from_project(task_id) -> Task`

**CommentManager**:
- `add(task_id, content, author=None) -> TaskComment`
- `get(comment_id) -> TaskComment`
- `list_all() -> List[TaskComment]`
- `list_by_task(task_id) -> List[TaskComment]`
- `delete(comment_id) -> None`
- `delete_all_by_task(task_id) -> None`

**ProjectManager**:
- `add(name) -> Project`
- `get(project_id) -> Project`
- `list_all() -> List[Project]`
- `delete(project_id) -> None`
- `update(project_id, name) -> Project`

### Model Serialization (Used by Storage and Import/Export)
```python
Task.to_dict() -> Dict
Task.from_dict(data: Dict) -> Task
TaskComment.to_dict() -> Dict
TaskComment.from_dict(data: Dict) -> TaskComment
Project.to_dict() -> Dict
Project.from_dict(data: Dict) -> Project
```

### CLI Entry Point Behavior (Must Preserve)
```bash
python -m src [command] [args]  # Command-line mode
python -m src                    # Interactive menu mode
```

---

## Circular Dependencies and Coupling Issues

### NO Traditional Circular Dependencies
The import graph is acyclic. No module directly or indirectly imports itself.

### TIGHT VERTICAL COUPLING

#### 1. **CLI Layer Coupling to Managers**
**Problem**: TodoCLI and InteractiveMenu import exceptions directly from managers
```python
# In todo_cli.py and interactive_menu.py:
from ..services.task_manager import TaskNotFoundError
from ..services.comment_manager import CommentNotFoundError
from ..services.project_manager import ProjectNotFoundError
from ..services.import_export_service import ImportExportError
```
**Impact**: CLI layer is aware of three specific manager implementations. Any refactoring of manager layer requires CLI changes.

#### 2. **Service-to-Manager Tight Coupling**
**Problem**: TodoService instantiates managers directly
```python
# In todo_service.py __init__:
self._manager = TaskManager(storage)
self._comment_manager = CommentManager(storage)
self._project_manager = ProjectManager(storage)
```
**Impact**: Cannot swap managers for test doubles or alternate implementations without modifying TodoService.

#### 3. **Manager-to-Storage Path Manipulation**
**Problem**: CommentManager and ProjectManager directly manipulate storage file paths
```python
# In comment_manager.py and project_manager.py:
self._storage._path = _derive_comments_path(self._storage.path)
self._storage._path = _derive_projects_path(self._storage.path)
```
**Impact**: Violates encapsulation. Storage layer's `_path` property is private but is overridden by managers. Makes it impossible to change storage path resolution without changing managers.

#### 4. **Import/Export Accessing Private Manager State**
**Problem**: ImportService directly accesses and mutates private dictionaries
```python
# In import_export_service.py:
self._task_manager._tasks[task.id] = task
self._comment_manager._comments[comment.id] = comment
self._project_manager._projects[project.id] = project
self._task_manager._persist()
```
**Impact**: Import/Export layer bypasses manager public interfaces. Duplicates responsibility for persistence coordination.

#### 5. **CLI Storage Instantiation**
**Problem**: Both TodoCLI and InteractiveMenu instantiate JsonStorage directly
```python
# In both cli modules:
storage = JsonStorage(storage_path) if storage_path else JsonStorage()
self._service = TodoService(storage)
```
**Impact**: CLI layer knows about storage layer implementation. Cannot change storage layer or use composition differently without CLI changes.

---

## What `python -m src` Currently Does

### Command-Line Mode (with arguments)
```bash
python -m src add "Title" -d "Description"
python -m src list --status pending
python -m src show <task-id>
python -m src start <task-id>
python -m src done <task-id>
# ... (20+ other commands)
```
1. Parses command-line arguments using argparse
2. Creates TodoCLI instance (which instantiates JsonStorage and TodoService)
3. Calls appropriate command handler based on subcommand
4. Catches domain exceptions and prints errors to stderr
5. Returns exit code (0 for success, 1 for error)

### Interactive Mode (no arguments)
```bash
python -m src
```
1. Creates InteractiveMenu instance (which instantiates JsonStorage and TodoService)
2. Displays main menu in a loop
3. Routes user choices to menu handler methods
4. Exits on user selection or Ctrl+C

### Both Modes
- Use the same TodoService facade
- Share the same file-based storage (~/.todo_data.json and derived files)
- Perform identical CRUD and cross-entity operations
- Catch identical exception types
- Use a single JsonStorage instance per session

---

## What Needs to Be Separated and How

### Priority 1: Extract Repository Abstraction
**Current Problem**: Managers directly mutate private state and storage, ImportService bypasses managers

**Solution**: Create an abstract repository layer
```
src/repositories/
  __init__.py
  base_repository.py (abstract base class)
  task_repository.py (concrete impl)
  comment_repository.py (concrete impl)
  project_repository.py (concrete impl)
  unit_of_work.py (coordinates related repositories)
```

**Why**: 
- Defines a clear boundary between business logic and persistence
- Allows TodoService and ImportService to use consistent public interfaces
- Enables swapping storage implementations (e.g., database instead of JSON)
- Eliminates private state access in ImportService

### Priority 2: Extract Exception Layer
**Current Problem**: CLI imports exceptions from multiple manager modules

**Solution**: Create a central exceptions module
```
src/exceptions.py
  TaskNotFoundError
  CommentNotFoundError
  ProjectNotFoundError
  ImportExportError
  DomainError (base class)
```

**Why**: 
- Single import location for CLI layer
- Clear definition of application error contract
- Decouples manager implementations from exception contracts

### Priority 3: Dependency Injection Pattern
**Current Problem**: CLI instantiates JsonStorage directly; TodoService instantiates managers

**Solution**: Create a factory/bootstrap module
```
src/container.py or src/bootstrap.py
  Container class that:
    - Instantiates JsonStorage once
    - Creates all managers with the shared storage
    - Creates TodoService with managers
    - Provides these to CLI modules
```

**Why**: 
- Single place to configure dependencies
- Easier to inject test doubles in CLI layer tests
- Eliminates redundant instantiation pattern in both CLI modules

### Priority 4: Separate Storage Concerns
**Current Problem**: Managers derive file paths and override storage._path; hard-coded file names

**Solution**: Create a storage coordinator/mapper
```
src/storage/
  path_provider.py
    StoragePathProvider:
      get_tasks_path() -> Path
      get_comments_path() -> Path
      get_projects_path() -> Path
```

**Why**: 
- Centralize path resolution logic (no more _derive_*_path functions in managers)
- Decouple managers from storage file naming conventions
- Makes it possible to configure storage layout without touching managers

### Priority 5: Clean Up Import/Export Service
**Current Problem**: ImportService directly manipulates manager internals

**Solution**: Use repository public interfaces and add transactional methods to repositories
```
class Repository:
    def add_many(items: List[T]) -> int
    def replace_all(items: List[T]) -> int
    def merge(items: List[T], mode: str) -> Tuple[imported, conflicts]
```

**Why**: 
- ImportService becomes a high-level orchestrator, not a low-level mutator
- Repositories can enforce invariants during bulk operations
- Cleaner separation of concerns

### Priority 6: Model-Manager Separation
**Current Problem**: Managers implement both in-memory caching AND persistence logic

**Solution**: Consider separating into Repository (persistence) + Cache (in-memory)
```
src/repositories/task_repository.py
  - Handles persistence only
src/cache/task_cache.py (optional future)
  - Handles in-memory state
```

**Why**: 
- Currently merged, but if caching strategy changes (LRU, TTL, etc.) this matters
- Allows reasoning about persistence independently from runtime behavior
- Future-proofs against needing a database or caching layer

---

## Constraints: What Must Be Preserved

1. **Public API Shape**: All TodoService methods must exist with same signature
2. **Exception Types**: Must still raise TaskNotFoundError, CommentNotFoundError, ProjectNotFoundError, ImportExportError, ValueError
3. **CLI Behavior**: 
   - `python -m src [command] ...` must work identically
   - `python -m src` (interactive) must work identically
   - All subcommands must produce same output format and error handling
4. **File Behavior**:
   - Default storage paths must remain: `~/.todo_data.json`, `~/.todo_comments.json`, `~/.todo_projects.json`
   - JSON file format must remain compatible with existing data
5. **Import/Export Format**: Exported JSON structure must remain the same
6. **Serialization**: Task.to_dict(), Task.from_dict(), etc. must work identically
7. **ID Prefix Matching**: Ability to use short IDs (first 8 chars) must remain
8. **Cascading Deletes**: delete_task must still cascade to delete_comment
9. **Project Assignment**: Task.project_id foreign key behavior must work identically

---

## Summary Table: Current vs. Target

| Aspect | Current State | Issues | Target State |
|--------|---------------|--------|--------------|
| **Exception Handling** | Scattered across managers | CLI imports from 3 places | Centralized in `src/exceptions.py` |
| **Repository Access** | Direct dict mutation + private calls | ImportService bypasses interfaces | Public repository methods only |
| **Storage Path Mgmt** | Hard-coded in manager functions | Violates storage encapsulation | Centralized StoragePathProvider |
| **Dependency Injection** | Instantiated in CLI modules | Hard to test, redundant | Container/bootstrap module |
| **Manager Pattern** | Each manager is independent | Code duplication (load, persist, get) | Abstract base repository class |
| **CLI-Service Coupling** | Direct instantiation | CLI owns storage creation | CLI receives TodoService as dependency |

---

## Suggested Implementation Order

1. **Create `src/exceptions.py`** — Centralize all domain exceptions (simplest, no risk)
2. **Create `src/storage/path_provider.py`** — Externalize path derivation logic
3. **Create repository base class** — Abstract out common manager patterns
4. **Refactor managers to repositories** — One at a time (TaskManager → TaskRepository first)
5. **Create `src/container.py`** — Dependency injection for TodoService
6. **Update CLI to use container** — Inject TodoService instead of instantiating
7. **Refactor ImportService** — Use repository public methods
8. **Tests**: Update all unit tests to pass dependencies

This order minimizes breaking changes at each step and allows incremental validation.
