# DESIGN PLAN: Task 08 - Projects Functionality

**Date:** 2026-05-03  
**Architecture:** Pipeline  
**Working Directory:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/`

---

## ARCHITECTURE OVERVIEW

The implementation adds a Project domain model alongside the existing Task model, with:
- **Models Layer:** New `Project` dataclass mirroring `Task` structure
- **Storage Layer:** Modified `JsonStorage` to persist both tasks and projects in a single JSON file with structure `{"tasks": [...], "projects": [...]}`
- **Manager Layer:** New `ProjectManager` class following the same pattern as `TaskManager`
- **Service Layer:** Enhanced `TodoService` with project CRUD and task-project relationship methods; enhanced `TaskManager` with project filtering
- **CLI Layer:** Five new subcommands for project management; enhanced `add` and `update` with `--project` flag
- **Menu Layer:** New menu option "12. Manage Projects" with submenu for CRUD operations

**Data Flow:**
1. Projects and tasks coexist in a single JSON file with distinct arrays
2. Tasks have optional `project_id` field (backward compatible: old files load as `project_id=None`)
3. Deleting a project orphans tasks (sets `project_id=None`, does not cascade delete)
4. All mutations persist to disk via `JsonStorage._persist()`

---

## FILE-BY-FILE IMPLEMENTATION DETAILS

### NEW FILES TO CREATE

#### 1. `src/models/project.py`

```python
from __future__ import annotations
import uuid
from dataclasses import dataclass, field

@dataclass
class Project:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self) -> None:
        """Validate that name is not empty."""
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")
        self.name = self.name.strip()
    
    def to_dict(self) -> dict:
        """Convert to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "name": self.name,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Project:
        """Reconstruct from JSON-compatible dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
        )
```

**Exports:** Class `Project` with methods `to_dict()`, `from_dict()`, validation in `__post_init__`.

---

#### 2. `src/services/project_manager.py`

```python
from typing import Optional
from ..models.project import Project
from ..storage.json_storage import JsonStorage

class ProjectNotFoundError(Exception):
    pass

class ProjectManager:
    def __init__(self, storage: Optional[JsonStorage] = None) -> None:
        self._storage = storage or JsonStorage()
        self._projects: dict[str, Project] = {}
        self._load()
    
    def _load(self) -> None:
        """Load projects from storage."""
        data = self._storage.load()
        projects_data = data.get("projects", []) if isinstance(data, dict) else []
        self._projects = {d["id"]: Project.from_dict(d) for d in projects_data}
    
    def _persist(self) -> None:
        """Persist projects to storage."""
        # Must preserve tasks when saving
        data = self._storage.load()
        tasks_data = data.get("tasks", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        # Handle migration from old list format
        if isinstance(data, list):
            tasks_data = data
        self._storage.save({
            "tasks": tasks_data,
            "projects": [p.to_dict() for p in self._projects.values()]
        })
    
    def add(self, name: str) -> Project:
        """Create a new project.
        
        Args:
            name: Project name (non-empty string).
        
        Returns:
            Project: The created project.
        
        Raises:
            ValueError: If name is empty.
        """
        project = Project(name=name)
        self._projects[project.id] = project
        self._persist()
        return project
    
    def get(self, project_id: str) -> Project:
        """Get a project by ID or prefix.
        
        Args:
            project_id: Full or partial project ID (first 8+ chars).
        
        Returns:
            Project: The project.
        
        Raises:
            ProjectNotFoundError: If project not found or prefix is ambiguous.
        """
        if project_id in self._projects:
            return self._projects[project_id]
        # Prefix lookup support
        matches = [p for pid, p in self._projects.items() if pid.startswith(project_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ProjectNotFoundError(f"Ambiguous prefix '{project_id}' matches {len(matches)} projects")
        raise ProjectNotFoundError(f"Project '{project_id}' not found")
    
    def list_all(self) -> list[Project]:
        """Get all projects."""
        return list(self._projects.values())
    
    def delete(self, project_id: str) -> None:
        """Delete a project.
        
        Args:
            project_id: Full or partial project ID.
        
        Raises:
            ProjectNotFoundError: If project not found.
        """
        project = self.get(project_id)  # Resolves prefix, raises if missing
        del self._projects[project.id]
        self._persist()
```

**Exports:** Classes `ProjectManager`, `ProjectNotFoundError` with methods `add()`, `get()`, `list_all()`, `delete()`, plus internal `_load()` and `_persist()`.

---

#### 3. `tests/test_project.py`

Test specifications (see Test Specifications section below).

---

#### 4. `tests/test_project_manager.py`

Test specifications (see Test Specifications section below).

---

#### 5. `tests/test_task_project_integration.py`

Test specifications (see Test Specifications section below).

---

### EXISTING FILES TO MODIFY

#### 1. `src/models/task.py`

**Changes:**
- Add new field to dataclass after `comments`:
  ```python
  project_id: Optional[str] = None
  ```
- Update `to_dict()` method to include:
  ```python
  "project_id": self.project_id,
  ```
  (Insert after "comments" line, before closing brace)
- Update `from_dict()` classmethod to extract project_id:
  ```python
  project_id=data.get("project_id"),  # Add to return cls(...) constructor call
  ```

**Why:** Maintains task-project relationship; backward compatible (missing field defaults to None).

---

#### 2. `src/models/__init__.py`

**Changes:**
- Add import:
  ```python
  from .project import Project
  ```
- Add to `__all__` list:
  ```python
  "Project"
  ```

**Why:** Exports new Project class for use by services and CLI.

---

#### 3. `src/storage/json_storage.py`

**Changes:**
- Modify `load()` method signature and implementation:
  ```python
  def load(self) -> dict:
      """Load data from JSON file.
      
      Returns:
          dict: Data with "tasks" and "projects" keys, or legacy list format.
          
      Auto-migrates old format (list of dicts) to new format (dict with keys).
      """
      if not self._path.exists():
          return {"tasks": [], "projects": []}
      with self._path.open("r", encoding="utf-8") as f:
          data = json.load(f)
      
      # Auto-migrate old format (simple list) to new format (dict)
      if isinstance(data, list):
          return {"tasks": data, "projects": []}
      return data
  ```
- Modify `save()` method signature and implementation:
  ```python
  def save(self, data: dict | list) -> None:
      """Save data to JSON file.
      
      Args:
          data: Dict with "tasks" and "projects" keys, or legacy list format.
      """
      self._path.parent.mkdir(parents=True, exist_ok=True)
      with self._path.open("w", encoding="utf-8") as f:
          json.dump(data, f, indent=2, ensure_ascii=False)
  ```

**Why:** Enables storage of both tasks and projects; handles migration from old single-list format to new dict format transparently.

---

#### 4. `src/services/task_manager.py`

**Changes:**
- Update `_load()` method to handle new storage format:
  ```python
  def _load(self) -> None:
      raw = self._storage.load()
      # Handle both old (list) and new (dict) formats
      if isinstance(raw, dict):
          tasks_data = raw.get("tasks", [])
      else:
          tasks_data = raw
      self._tasks = {d["id"]: Task.from_dict(d) for d in tasks_data}
  ```
- Update `_persist()` method to preserve projects:
  ```python
  def _persist(self) -> None:
      data = self._storage.load()
      # Preserve projects when saving tasks
      projects_data = data.get("projects", []) if isinstance(data, dict) else []
      self._storage.save({
          "tasks": [t.to_dict() for t in self._tasks.values()],
          "projects": projects_data
      })
  ```
- Add new method after `list_by_status()`:
  ```python
  def list_by_project(self, project_id: str) -> list[Task]:
      """Filter tasks by project ID."""
      return [t for t in self._tasks.values() if t.project_id == project_id]
  ```
- Add new method after `delete()`:
  ```python
  def set_project(self, task_id: str, project_id: Optional[str]) -> Task:
      """Assign or unassign a task to/from a project."""
      task = self.get(task_id)
      task.project_id = project_id
      task.updated_at = datetime.now(timezone.utc)
      self._persist()
      return task
  
  def orphan_project_tasks(self, project_id: str) -> int:
      """Unassign all tasks from a project (when project is deleted)."""
      count = 0
      for task in self._tasks.values():
          if task.project_id == project_id:
              task.project_id = None
              count += 1
      if count > 0:
          self._persist()
      return count
  ```

**Why:** Supports new project filtering and task-project assignment; preserves projects during task persistence; handles deletion cascade (orphaning instead of cascading delete).

---

#### 5. `src/services/todo_service.py`

**Changes:**
- Add to `__init__()` after `self._manager = TaskManager(storage)`:
  ```python
  from .project_manager import ProjectManager
  self._project_manager = ProjectManager(storage)
  ```
- Add new methods after `list_tasks()`:
  ```python
  def list_tasks_by_project(self, project_id: str) -> list[Task]:
      """List all tasks in a project."""
      return self._manager.list_by_project(project_id)
  
  def create_project(self, name: str) -> Project:
      """Create a new project."""
      if not name or not name.strip():
          raise ValueError("Project name cannot be empty")
      return self._project_manager.add(name.strip())
  
  def list_projects(self) -> list[Project]:
      """Get all projects."""
      return self._project_manager.list_all()
  
  def get_project(self, project_id: str) -> Project:
      """Get a project by ID or prefix."""
      return self._project_manager.get(project_id)
  
  def delete_project(self, project_id: str) -> None:
      """Delete a project (tasks are orphaned, not deleted)."""
      project = self._project_manager.get(project_id)  # Validates existence
      self._manager.orphan_project_tasks(project.id)  # Orphan tasks first
      self._project_manager.delete(project_id)
  
  def move_task_to_project(self, task_id: str, project_id: Optional[str]) -> Task:
      """Assign or reassign a task to a project."""
      if project_id is not None:
          self._project_manager.get(project_id)  # Validates project exists
      return self._manager.set_project(task_id, project_id)
  ```
- Add imports at top:
  ```python
  from ..models.project import Project
  from .project_manager import ProjectManager, ProjectNotFoundError
  ```

**Why:** Exposes project CRUD operations and task-project relationship methods at the service layer with input validation.

---

#### 6. `src/cli/todo_cli.py`

**Changes:**
- Add imports at top:
  ```python
  from ..models.project import Project
  from ..services.project_manager import ProjectNotFoundError
  ```
- Add to `_build_parser()` after the import subparser definition, before `return parser`:
  ```python
  # create-project
  p_create_project = sub.add_parser("create-project", help="Create a new project")
  p_create_project.add_argument("name", help="Project name")
  p_create_project.set_defaults(func=self._cmd_create_project)
  
  # list-projects
  p_list_projects = sub.add_parser("list-projects", help="List all projects")
  p_list_projects.set_defaults(func=self._cmd_list_projects)
  
  # delete-project
  p_delete_project = sub.add_parser("delete-project", help="Delete a project")
  p_delete_project.add_argument("id", help="Project ID")
  p_delete_project.set_defaults(func=self._cmd_delete_project)
  ```
- Update `p_add` subparser to add:
  ```python
  p_add.add_argument("--project", help="Project ID to assign task to")
  ```
- Update `p_list` subparser to add:
  ```python
  p_list.add_argument("--project", help="Filter by project ID")
  ```
- Update `p_update` subparser to add:
  ```python
  p_update.add_argument("--project", help="Project ID to move task to (or none to unassign)")
  ```
- Update `run()` method to catch `ProjectNotFoundError`:
  ```python
  except ProjectNotFoundError as e:
      print(f"Error: {e}", file=sys.stderr)
      return 1
  ```
- Add new command handler methods before `_cmd_report()`:
  ```python
  def _cmd_create_project(self, args: argparse.Namespace) -> int:
      project = self._service.create_project(args.name)
      print(f"Created project {project.id[:8]}  {project.name}")
      return 0
  
  def _cmd_list_projects(self, args: argparse.Namespace) -> int:
      projects = self._service.list_projects()
      if not projects:
          print("No projects found.")
          return 0
      for project in projects:
          tasks = self._service.list_tasks_by_project(project.id)
          task_count = len(tasks)
          print(f"{project.id[:8]}  {project.name}  ({task_count} task{'s' if task_count != 1 else ''})")
      return 0
  
  def _cmd_delete_project(self, args: argparse.Namespace) -> int:
      project = self._service.get_project(args.id)
      self._service.delete_project(args.id)
      print(f"Deleted project {project.id[:8]}  {project.name}")
      return 0
  ```
- Update `_cmd_add()` to handle --project flag
- Update `_cmd_list()` to handle --project filter
- Update `_cmd_update()` to handle --project flag

**Why:** Adds project CLI commands and integrates project functionality with existing commands.

---

#### 7. `src/cli/interactive_menu.py`

**Changes:**
- Add imports at top:
  ```python
  from ..models.project import Project
  from ..services.project_manager import ProjectNotFoundError
  ```
- Update `_print_main_menu()` to add project option:
  ```python
  print("  12. Manage projects")
  ```
- Update `run()` method to add handling for menu option 12:
  ```python
  elif choice == "12":
      self._do_manage_projects()
  ```
- Add new methods: `_do_manage_projects()`, `_do_create_project()`, `_do_list_projects()`, `_do_delete_project()`, `_do_manage_project_tasks()`
- Update `_do_add()` to optionally assign project after creation

**Why:** Adds project management menu with full CRUD operations and integration with task management.

---

## IMPLEMENTATION ORDER

**Phase 1: Core Domain Model (Foundation)**
1. Create `src/models/project.py`
2. Modify `src/models/task.py` to add `project_id` field
3. Modify `src/models/__init__.py` to export `Project`

**Phase 2: Storage & Manager Layer**
4. Modify `src/storage/json_storage.py` to handle dict format
5. Create `src/services/project_manager.py`
6. Modify `src/services/task_manager.py` for storage format and project methods

**Phase 3: Service Layer**
7. Modify `src/services/todo_service.py` to expose project operations

**Phase 4: CLI Layer**
8. Modify `src/cli/todo_cli.py` for project commands

**Phase 5: Interactive Menu**
9. Modify `src/cli/interactive_menu.py` for project management

**Phase 6: Testing**
10. Create `tests/test_project.py`
11. Create `tests/test_project_manager.py`
12. Create `tests/test_task_project_integration.py`

**Phase 7: Verification**
13. Verify `python -m src --help` shows all project commands
14. Run full test suite

---

## TEST STRATEGY

**Total target:** 23+ test cases across:
- Project class: 6 tests
- ProjectManager: 10 tests
- Task-Project integration: 7+ tests

See Test Specifications section for detailed test cases.

---

## KEY IMPLEMENTATION NOTES

1. **Storage Migration:** Old files with `[{task}]` format auto-migrate to `{"tasks": [...], "projects": []}` on load.
2. **Persistence Coordination:** Both TaskManager and ProjectManager must preserve each other's data when persisting.
3. **Project Deletion Cascade:** Orphan tasks BEFORE deleting the project.
4. **Backward Compatibility:** Task.from_dict() must use `.get("project_id")` with default None.
5. **UUID Prefix Matching:** Use same pattern as TaskManager for prefix lookups.
