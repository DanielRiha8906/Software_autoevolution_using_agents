# Task 09 Analysis: Refactor Architecture for Layer Separation and Eliminate Circular Dependencies

**Analysis Date:** 2026-05-04  
**Working Directory:** `experiments/pipeline/user_stories/TODO/`  
**Task 09 Goal:** Create clear boundaries between task, comment, project, storage, and interface layers with no circular dependencies while preserving all public interfaces.

---

## 1. What Task 09 Is Asking For

Refactor the TODO application to establish clean architectural layers with strict boundaries and eliminate any circular dependencies. The refactoring must:

- Create clear separation between task, comment, project, storage, and interface layers
- Eliminate all circular dependencies (if present)
- Preserve all existing public interfaces (function signatures, class names, return types)
- Use abstract base classes or protocols to decouple layers where appropriate
- Keep domain logic and algorithms unchanged
- Ensure `python -m src` behaves identically before and after refactoring

---

## 2. Current Architecture and Layer Structure

The TODO application currently has **5 logical layers**:

### Layer 1: Domain Models (`src/models/`)
**Files:** task.py, task_status.py, task_comment.py, project.py, task_summary_report.py

**Responsibility:** Define domain entities as immutable/semi-mutable dataclasses with:
- Fields representing domain concepts (id, title, status, etc.)
- Serialization methods: `to_dict()` and `from_dict()` for JSON persistence
- Domain logic: validation (`__post_init__`), state queries (`is_pending()`, `is_overdue()`), state mutations (`mark_done()`, `reopen()`)

**Current Dependencies:**
- `Task` imports: `task_status`, `task_comment` (models-to-models)
- `TaskComment` imports: none
- `Project` imports: none
- `TaskStatus` imports: none
- `TaskSummaryReport` imports: none

**Characterization:** Pure domain layer. No external dependencies. Sealed layer—nothing above should bypass it.

---

### Layer 2: Persistence (`src/storage/`)
**Files:** json_storage.py

**Responsibility:** Abstract the details of persisting domain data to JSON files. Provides:
- `load()` → returns dict with "tasks" and "projects" keys
- `save(data: dict)` → writes dict to ~/.todo_data.json

**Current Dependencies:**
- `JsonStorage` imports: none (stdlib only: json, Path)

**Characterization:** Infrastructure layer. Should not import from services or models. Models call `to_dict()` to serialize; storage is format-agnostic.

**Current Issue:** Storage has knowledge of the data structure ("tasks" and "projects" keys). No true abstraction—just a wrapper around json.dump/load.

---

### Layer 3: Service/Business Logic (`src/services/`)
**Files:** task_manager.py, project_manager.py, todo_service.py, import_validator.py

**Responsibility:** Implement CRUD operations, filtering, validation, and orchestration of domain models. Subdivided into:

#### 3a. Manager Classes (Task and Project)
**TaskManager:**
- In-memory cache: `_tasks: dict[str, Task]`
- Direct storage access: `self._storage.load()`, `self._storage.save()`
- Internal helper methods: `_get_week_boundaries()`, `_get_month_boundaries()`, `_get_year_boundaries()`
- Public methods: `add()`, `get()`, `list_*()`, `update()`, `set_status()`, `set_project()`, `delete()`, `add_comment()`, `get_comments()`, `delete_comment()`, `edit_comment()`, `orphan_project_tasks()`

**ProjectManager:**
- In-memory cache: `_projects: dict[str, Project]`
- Direct storage access: `self._storage.load()`, `self._storage.save()`
- Public methods: `add()`, `get()`, `list_all()`, `delete()`

**TodoService:**
- Composition of managers: `self._manager` (TaskManager), `self._project_manager` (ProjectManager)
- Higher-level orchestration and validation
- Public methods: `add_task()`, `list_tasks()`, `list_tasks_by_*()`, `get_task()`, `create_project()`, `list_projects()`, `get_project()`, `delete_project()`, `move_task_to_project()`, `start_task()`, `complete_task()`, `reopen_task()`, `update_task()`, `set_due_date()`, `delete_task()`, `add_comment()`, `get_comments()`, `delete_comment()`, `edit_comment()`, `generate_report()`, `export_tasks()`, `import_tasks()`

**ImportValidator:**
- Static validation logic: `validate_file()`, `validate_task_dict()`
- No state; utility class

**Current Dependencies:**
- `TaskManager` → `JsonStorage`, `Task`, `TaskStatus`, `TaskComment`
- `ProjectManager` → `JsonStorage`, `Project`
- `TodoService` → `TaskManager`, `ProjectManager`, `ImportValidator`, all models, `JsonStorage`
- `ImportValidator` → `TaskStatus`

**Characterization:** High-level business logic layer. Orchestrates models and storage.

**Current Issues:**
1. **Manager classes directly access storage:** TaskManager and ProjectManager each hold their own storage reference and call `_load()` and `_persist()` independently. This creates **shared state management across two independent caches**.
2. **TodoService bypasses public interfaces:** In `import_tasks()`, TodoService directly mutates `self._manager._tasks[task_id] = task` and calls `self._manager._persist()`. This violates encapsulation of TaskManager.
3. **TodoService accesses private methods of TaskManager:** Calls `self._manager._get_week_boundaries()`, `self._manager._get_month_boundaries()`, `self._manager._get_year_boundaries()` directly.
4. **Dual persistence responsibility:** Both managers independently load and save from the same storage, creating coordination issues:
   - When TaskManager calls `_persist()`, it reads fresh storage, modifies tasks, and writes back, potentially losing concurrent changes to projects.
   - When ProjectManager calls `_persist()`, same issue in reverse.
   - No atomic transactions or locking mechanism.

---

### Layer 4: Interface/CLI (`src/cli/`)
**Files:** todo_cli.py, interactive_menu.py

**Responsibility:** Present a user-facing interface (command-line and interactive menu) to the TodoService.

**TodoCLI:**
- Parses command-line arguments via argparse
- Delegates to TodoService methods
- Returns exit codes (0 success, 1 error)
- Catches and prints errors to stderr

**InteractiveMenu:**
- Infinite loop menu with screen clearing and user input prompts
- Delegates to TodoService methods
- Prints formatted output to stdout

**Current Dependencies:**
- Both import: `TodoService`, `JsonStorage`, `Task`, `TaskStatus`, `Project`, exception classes from managers
- Both instantiate: `JsonStorage()` then `TodoService(storage)`

**Characterization:** User-facing layer. Should only depend on TodoService (the public service contract).

**Current Issues:**
1. **Unnecessary imports of low-level classes:** Both CLI classes import exception classes (`TaskNotFoundError`, `ProjectNotFoundError`) directly from managers. These should either be exported from a higher-level module or use a unified exception hierarchy.
2. **Both CLI classes instantiate storage and service:** Creates coupling to instantiation details. Dependency injection is manual.

---

## 3. Identified Problems: Circular Dependencies and Layer Violations

### 3.1 Circular Dependency Analysis

**Finding:** NO pure circular dependencies in the import graph.

**Evidence:** The dependency graph is acyclic:
- Models layer: No imports from other internal modules
- Storage layer: No imports from models, managers, or services
- Manager classes: Import models and storage (no circular path back)
- TodoService: Imports managers, models, storage (no circular path back)
- CLI: Imports TodoService and models (no circular path back)

**However:** While no strict circular import exists, there are **architectural violations and layer crossings** that create tight coupling:

### 3.2 Layer Violations (Not Circular, but Problematic)

#### Violation 1: TodoService Accesses Private Manager State
**Location:** `src/services/todo_service.py`, lines 409, 421

```python
# Line 409: Direct mutation of private cache
self._manager._tasks[task_id] = task

# Line 421: Direct call to private persistence method
self._manager._persist()
```

**Problem:** 
- TodoService reaches past TaskManager's public interface to modify internal state directly
- Breaks encapsulation; changes to TaskManager internals would break TodoService
- Other code might assume TaskManager is the only writer to `_tasks`

**Impact:** High coupling, fragility

---

#### Violation 2: TodoService Accesses Private Manager Helper Methods
**Location:** `src/services/todo_service.py`, lines 45, 66, 83

```python
# Lines 45, 66, 83: Access to private date boundary helper methods
week_start, week_end = self._manager._get_week_boundaries(year, week)
month_start, month_end = self._manager._get_month_boundaries(year, month)
year_start, year_end = self._manager._get_year_boundaries(year)
```

**Problem:**
- These are private utility methods (prefixed `_`) in TaskManager
- TodoService relies on these internals; they're not part of the public contract
- If TaskManager refactors these helpers, TodoService breaks

**Impact:** Medium coupling, fragility

---

#### Violation 3: Dual Independent Persistence with Shared Storage
**Location:** TaskManager and ProjectManager both:
- Hold their own `_storage` reference
- Call `_load()` independently to populate their in-memory caches
- Call `_persist()` independently, which re-reads storage, modifies it, and writes back

**Problem:**
- TaskManager's `_persist()` reads the entire file, modifies tasks, saves—potentially overwriting concurrent project changes
- ProjectManager's `_persist()` does the same with projects
- Example race condition:
  1. TaskManager reads: `{"tasks": [T1], "projects": [P1]}`
  2. ProjectManager reads: `{"tasks": [T1], "projects": [P1]}`
  3. TaskManager modifies T1 and writes: `{"tasks": [T1'], "projects": [P1]}`
  4. ProjectManager modifies P1 and writes: `{"tasks": [T1], "projects": [P1']}` (overwriting T1' with old T1)

- No single authority for storage; two caches that must stay in sync
- No transaction semantics or atomic multi-step persistence

**Impact:** High risk of data loss in concurrent scenarios (though current single-threaded CLI usage masks this)

---

#### Violation 4: CLI Imports from Multiple Manager Classes
**Location:** `src/cli/todo_cli.py` and `src/cli/interactive_menu.py`

```python
from ..services.task_manager import TaskNotFoundError
from ..services.project_manager import ProjectNotFoundError
```

**Problem:**
- CLI couples to specific manager exception classes
- If exception hierarchy refactors, CLI breaks
- CLI should depend only on TodoService's exception contract, not manager implementations

**Impact:** Medium coupling

---

## 4. Public Interfaces That Must Be Preserved

To ensure `python -m src` behaves identically, the following public signatures must NOT change:

### Models Layer (Fully Public)
```python
# task_status.py
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"

# task.py
class Task:
    id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    comments: list[TaskComment]
    project_id: Optional[str]
    
    def __post_init__(self) -> None: ...
    def is_pending(self) -> bool: ...
    def is_in_progress(self) -> bool: ...
    def is_completed(self) -> bool: ...
    def is_overdue(self) -> bool: ...
    def mark_in_progress(self) -> Task: ...
    def mark_done(self) -> Task: ...
    def reopen(self) -> Task: ...
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> Task: ...

# task_comment.py
class TaskComment:
    id: str
    task_id: str
    content: str
    author: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    def __post_init__(self) -> None: ...
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> TaskComment: ...

# project.py
class Project:
    id: str
    name: str
    
    def __post_init__(self) -> None: ...
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> Project: ...

# task_summary_report.py
class TaskSummaryReport:
    total_count: int
    pending_count: int
    in_progress_count: int
    done_count: int
    overdue_count: int
    due_date_set_count: int
    completion_rate: float
    avg_days_to_completion: Optional[float]
```

### Storage Layer (Minimal Public Interface)
```python
# json_storage.py
class JsonStorage:
    def __init__(self, path: Optional[str] = None) -> None: ...
    @property
    def path(self) -> Path: ...
    def load(self) -> Union[dict, list[dict]]: ...
    def save(self, data: Union[dict, list[dict]]) -> None: ...
```

### Service Layer (CRITICAL—TodoService is the public contract)
```python
# todo_service.py
class TodoService:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None: ...
    
    # Task operations
    def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task: ...
    def get_task(self, task_id: str) -> Task: ...
    def list_tasks(self, status: Optional[TaskStatus] = None, before: Optional[datetime] = None, after: Optional[datetime] = None, overdue_only: bool = False) -> list[Task]: ...
    def list_tasks_by_week(self, year: int, week: int, status: Optional[TaskStatus] = None) -> list[Task]: ...
    def list_tasks_by_month(self, year: int, month: int, status: Optional[TaskStatus] = None) -> list[Task]: ...
    def list_tasks_by_year(self, year: int, status: Optional[TaskStatus] = None) -> list[Task]: ...
    def list_tasks_by_project(self, project_id: str) -> list[Task]: ...
    def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task: ...
    def start_task(self, task_id: str) -> Task: ...
    def complete_task(self, task_id: str) -> Task: ...
    def reopen_task(self, task_id: str) -> Task: ...
    def set_due_date(self, task_id: str, due_date: Optional[datetime]) -> Task: ...
    def delete_task(self, task_id: str) -> None: ...
    
    # Project operations
    def create_project(self, name: str) -> Project: ...
    def list_projects(self) -> list[Project]: ...
    def get_project(self, project_id: str) -> Project: ...
    def delete_project(self, project_id: str) -> None: ...
    def move_task_to_project(self, task_id: str, project_id: Optional[str]) -> Task: ...
    
    # Comment operations
    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment: ...
    def get_comments(self, task_id: str) -> list[TaskComment]: ...
    def delete_comment(self, task_id: str, comment_id: str) -> None: ...
    def edit_comment(self, task_id: str, comment_id: str, content: str) -> TaskComment: ...
    
    # Report and export/import
    def generate_report(self) -> TaskSummaryReport: ...
    def export_tasks(self, file_path: Optional[str] = None) -> int: ...
    def import_tasks(self, file_path: str, duplicate_strategy: str = "skip") -> dict: ...

# Exception classes (part of public contract)
class TaskNotFoundError(Exception): ...
class ProjectNotFoundError(Exception): ...
```

### CLI Layer (Entry Point)
```python
# todo_cli.py
class TodoCLI:
    def __init__(self, storage_path: Optional[str] = None) -> None: ...
    def run(self, argv: Optional[list[str]] = None) -> int: ...

# interactive_menu.py
class InteractiveMenu:
    def __init__(self, storage_path: Optional[str] = None) -> None: ...
    def run(self) -> None: ...

# __main__.py
# Must accept both CLI args and interactive mode
# python -m src → InteractiveMenu.run()
# python -m src add "title" → TodoCLI.run(["add", "title"])
```

---

## 5. Recommended Layer Separation Strategy

### 5.1 Define Layer Boundaries

**Layer 0: Domain Models** (read-only from higher layers)
- Pure data objects with no dependencies on other layers
- Methods: validation, serialization, simple domain queries
- Public interface: fully stable

**Layer 1: Storage Abstraction** (read-only from higher layers)
- Abstract interface for persistence (could be JSON, SQLite, etc.)
- Must NOT know about manager logic; only formats
- Public interface: `load()` and `save()` only

**Layer 2: Service/Business Logic** (uses Layers 0 and 1)
- Implements CRUD, filtering, validation, orchestration
- Must NOT depend on CLI layer
- Must NOT reach into private members of other components
- **Key refactor:** Consolidate storage coordination; single authority for persistence
- Public interface: TodoService only; managers become internal

**Layer 3: Interface/CLI** (uses Layer 2 only)
- Depends ONLY on TodoService and models
- Does NOT import exception classes from managers
- Public interface: TodoCLI, InteractiveMenu, entry point

### 5.2 Decouple Manager Classes from Each Other

**Current:** TaskManager and ProjectManager are independent; both manage storage directly.

**Refactored:** 
- Create an internal `StorageCoordinator` (or similar) that acts as single authority for reading/writing the entire storage file
- TaskManager and ProjectManager become pure in-memory caches; they notify the coordinator when changes occur
- TodoService orchestrates: it uses TaskManager, ProjectManager, and coordinates persistence through the coordinator

**Benefit:** Eliminates the race condition and ensures atomicity

### 5.3 Extract Date Boundary Logic into Utility Module

**Current:** `_get_week_boundaries()`, `_get_month_boundaries()`, `_get_year_boundaries()` are private methods of TaskManager.

**Refactored:** 
- Move these to a private utility module `src/services/_date_utils.py` (or keep in TaskManager but expose as public if TodoService legitimately needs them)
- TodoService calls the utility, not TaskManager's private methods
- OR: Add public methods to TaskManager: `get_week_boundaries()`, `get_month_boundaries()`, `get_year_boundaries()`

**Benefit:** Eliminates the private method dependency; makes boundaries explicit

### 5.4 Unify Exception Hierarchy

**Current:** `TaskNotFoundError` and `ProjectNotFoundError` defined in their respective manager modules; CLI imports them directly.

**Refactored:**
- Move both to `src/services/__init__.py` or a new `src/services/exceptions.py`
- Optionally create a base exception class: `TodoError(Exception)` or `ManagerError(Exception)`
- CLI imports from `src.services` (the public layer interface)

**Benefit:** CLI depends on service layer contract, not implementation details

### 5.5 Fix TodoService Encapsulation Violations

**Current:** In `import_tasks()`, TodoService directly mutates `self._manager._tasks[task_id] = task` and calls `self._manager._persist()`.

**Refactored:**
- Add public method to TaskManager: `set_task(task_id: str, task: Task) -> Task`
- TodoService calls `self._manager.set_task(task_id, task)` instead of mutating `_tasks` directly
- Internal persistence remains within TaskManager; TodoService doesn't call `_persist()`

**Benefit:** Restores encapsulation; TaskManager remains the single authority over its state

---

## 6. Scope Signals: What's In, Out, and Borderline

### Explicitly In (Required by Task 09)
- Refactor to create clear layer separation (task, comment, project, storage, interface)
- Eliminate all circular dependencies (finding: none currently exist, but layer violations must be fixed)
- Preserve all public interfaces (signatures, class names, return types)
- Use abstract base classes or protocols to decouple layers where appropriate
- Keep domain logic and algorithms unchanged
- Ensure `python -m src` behaves identically before and after

### Explicitly Out
- GUI or graphical refactoring
- Persistence to different backends (SQLite, database, cloud)
- Authorization or access control
- Performance optimizations beyond what's necessary for correctness

### Borderline (Assumptions)
- **Should TaskManager and ProjectManager be visible internally?** Yes. They remain internal to the service layer, not exported from the public API. Only TodoService is the public contract.
- **Should date boundary methods be public on TaskManager?** Making them public is safer (explicit public contract) than TodoService calling private methods. Recommend making them public.
- **Should we create a StorageCoordinator abstraction?** Yes, to eliminate the dual-persistence race condition and make the architecture cleaner.

---

## 7. Ambiguities and Working Assumptions

### Ambiguity 1: How much abstraction is "clean"?
**Question:** Should we create abstract base classes (ABC) for managers and storage, or just move private details and keep structure similar?

**Working assumption:** Create ABCs or Protocols minimally:
- `StorageInterface` (abstract): `load()`, `save()` - helps with testing and future backends
- `EntityManager` (protocol): Common interface for TaskManager and ProjectManager - optional; may be overkill
- Keep it pragmatic: only abstract what changes or is tested independently

### Ambiguity 2: Should TaskManager and ProjectManager be exposed from services module?
**Question:** Are they part of the public API or strictly internal?

**Working assumption:** Strictly internal. Only TodoService is exported from `src/services/__init__.py`. Tests and CLI never import TaskManager or ProjectManager directly.

### Ambiguity 3: Should date boundary helpers be public on TaskManager?
**Question:** Are `_get_week_boundaries()`, etc., temporary internals or legitimate public utilities?

**Working assumption:** Make them public and part of TaskManager's contract. They're useful helper functions that TodoService legitimately needs. Prefixing with `_` suggests they're temporary; they're not.

---

## 8. Summary: Current Problems and Refactoring Goals

| Problem | Impact | Solution |
|---------|--------|----------|
| TodoService directly mutates `_manager._tasks` | Breaks encapsulation; TaskManager not the sole authority | Add public `set_task()` method to TaskManager |
| TodoService calls private `_manager._get_*_boundaries()` | High coupling to internals | Make these methods public on TaskManager |
| TaskManager and ProjectManager both manage storage independently | Race condition risk; no atomic multi-step persistence | Create StorageCoordinator as single authority |
| CLI imports exception classes from managers | Depends on implementation details not public contract | Move exceptions to `src/services/__init__.py` |
| No clear layer boundaries | Difficult to reason about data flow and responsibilities | Document and enforce via architecture |

---

## 9. Recommended Refactoring Steps (Implementation Order)

### Phase 1: Extract and Unify Exception Handling
1. Create `src/services/exceptions.py` or add to `src/services/__init__.py`
2. Move `TaskNotFoundError` from task_manager.py
3. Move `ProjectNotFoundError` from project_manager.py
4. Update imports in all files
5. Update CLI to import from `src.services`

### Phase 2: Expose Private Date Utilities
1. In `task_manager.py`: Remove `_` prefix from `_get_week_boundaries`, `_get_month_boundaries`, `_get_year_boundaries`
2. Update TodoService to call public methods (no change needed; just removes the "private" designation)

### Phase 3: Create Storage Coordinator
1. Create `src/services/_storage_coordinator.py` (or inline in todo_service.py as private)
2. Implement: `load()` → dict with "tasks" and "projects", `save(tasks, projects)` → atomic write
3. Refactor TaskManager to use coordinator instead of direct storage
4. Refactor ProjectManager to use coordinator instead of direct storage
5. Remove `_storage`, `_load()`, `_persist()` from both managers

### Phase 4: Add Public Methods to TaskManager
1. Add `set_task(task_id: str, task: Task) -> Task` to persist a task
2. Remove direct `_tasks` mutation from TodoService

### Phase 5: Clean Up Encapsulation in TodoService
1. Replace `self._manager._tasks[task_id] = task` with `self._manager.set_task(task_id, task)`
2. Replace `self._manager._persist()` calls with explicit persist via coordinator or remove (should be implicit)

### Phase 6: Documentation
1. Update this analysis.md with final architecture
2. Add layer diagram to artifacts/

---

## 10. Files Involved in Refactoring

### Files to Create
- `src/services/exceptions.py` (or update `src/services/__init__.py`)
- `src/services/_storage_coordinator.py` (optional; could be inline in todo_service.py)

### Files to Modify
- `src/services/task_manager.py` — expose date methods, add set_task(), remove storage direct access
- `src/services/project_manager.py` — remove storage direct access
- `src/services/todo_service.py` — use public methods, remove private member access
- `src/cli/todo_cli.py` — import exceptions from src.services
- `src/cli/interactive_menu.py` — import exceptions from src.services
- `src/services/__init__.py` — export exception classes
- Tests may need minor updates for exception imports (if they import directly from managers)

### Files NOT Modified (Immutable)
- `src/models/` — fully stable; no changes
- `src/storage/json_storage.py` — interface stable; internal only refactoring if any

---

## 11. Public Interface Checklist (For Verification After Refactoring)

- [ ] `TodoService.__init__(storage: Optional[JsonStorage])` → unchanged
- [ ] All `TodoService` public methods exist with same signatures
- [ ] `TodoCLI.__init__(storage_path)` and `run(argv)` → unchanged
- [ ] `InteractiveMenu.__init__(storage_path)` and `run()` → unchanged
- [ ] All models and enums exist with same fields and methods
- [ ] `python -m src --help` outputs all commands
- [ ] `python -m src` starts interactive menu
- [ ] All tests pass (519 tests currently)

---

## 12. Architecture Diagram (Proposed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Entry Point                                  │
│                      src/__main__.py                                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
        ┌────────────────┐    ┌──────────────────┐
        │  TodoCLI       │    │  InteractiveMenu │
        │ (Interface)    │    │  (Interface)     │
        └────────┬───────┘    └────────┬─────────┘
                 │                     │
                 └──────────────┬──────┘
                                ▼
                    ┌─────────────────────────┐
                    │   TodoService (Public)  │
                    │  (Service Layer)        │
                    └─────┬────────────┬──────┘
                          │            │
             ┌────────────┘            └─────────────┐
             ▼                                       ▼
    ┌──────────────────────┐            ┌──────────────────────┐
    │   TaskManager        │            │  ProjectManager      │
    │  (Internal Service)  │            │ (Internal Service)   │
    └──────────┬───────────┘            └────────┬─────────────┘
               │                                 │
               └──────────────┬──────────────────┘
                              ▼
                    ┌──────────────────────────────┐
                    │  StorageCoordinator          │
                    │  (Private Coordination)      │
                    └──────────┬───────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │   JsonStorage        │
                    │  (Infrastructure)    │
                    └──────────┬───────────┘
                               ▼
                        ~/.todo_data.json
```

**Data Model Dependencies (must not be imported from above):**
- Task, Project, TaskComment, TaskStatus, TaskSummaryReport (all in models/)
- Exceptions: TaskNotFoundError, ProjectNotFoundError (service layer)

---

## 13. Final Checklist Before Implementation

- [ ] All public method signatures documented
- [ ] Exception hierarchy defined
- [ ] Storage coordinator design approved
- [ ] Test coverage understood (519 tests currently passing)
- [ ] Backward compatibility verified (old storage format still loads)
- [ ] No circular imports will be created
- [ ] All changes confined to src/ (tests/ updated but not expanded with new test files)
