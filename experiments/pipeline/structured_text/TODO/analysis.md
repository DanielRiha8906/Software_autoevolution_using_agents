# CommentsService Implementation Analysis

## Executive Summary

The TODO project needs a new CommentsService to manage TaskComment objects. The TaskComment model is already defined and tested. This analysis identifies the current architecture patterns, storage mechanism, service validation strategies, and the exact changes needed to integrate CommentsService into the existing codebase.

---

## Current Codebase Structure

### Directory Layout
```
src/
├── __init__.py
├── __main__.py
├── models/
│   ├── __init__.py         (exports Task, TaskStatus, TaskComment)
│   ├── task.py             (Task dataclass)
│   ├── task_comment.py     (TaskComment dataclass)
│   └── task_status.py      (TaskStatus enum)
├── services/
│   ├── __init__.py         (exports TaskManager, TaskNotFoundError, TodoService)
│   ├── task_manager.py     (CRUD for Task objects)
│   └── todo_service.py     (High-level API wrapping TaskManager)
├── storage/
│   ├── __init__.py
│   └── json_storage.py     (JSON persistence layer)
└── cli/
    ├── __init__.py
    ├── interactive_menu.py
    └── todo_cli.py
```

### Models Layer

#### TaskComment (already exists)
**File:** `src/models/task_comment.py` (lines 1-54)
**Class definition:**
```python
@dataclass
class TaskComment:
    task_id: str                      # Foreign key to Task
    content: str                      # Comment text
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone(timedelta(hours=2))))
    
    def to_dict(self) -> dict:        # Serializes to JSON-compatible dict
    @classmethod
    def from_dict(cls, data: dict) -> TaskComment:  # Deserializes with validation
```

**Validation in from_dict():**
- Checks all required fields present: id, task_id, content, created_at
- Validates content is not empty or whitespace-only
- Parses created_at using datetime.fromisoformat() with error handling
- Raises ValueError for validation failures

**Timezone:** CEST (UTC+2) via `timezone(timedelta(hours=2))`
**ID generation:** UUID (auto-generated)
**Ordering field:** created_at (ISO 8601 format when serialized)

#### Task (existing)
**File:** `src/models/task.py` (lines 1-85)
- Primary key: id (UUID)
- Fields: title, description (optional), status (TaskStatus enum), created_at, updated_at, due_date (optional)
- Methods: to_dict(), from_dict(), is_overdue(), mark_in_progress(), mark_done(), reopen(), is_completed()

---

## Storage Mechanism

**Single storage implementation:** JsonStorage
**File:** `src/storage/json_storage.py` (lines 1-24)

```python
class JsonStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else Path.home() / ".todo_data.json"
    
    def load(self) -> list[dict]:      # Returns raw list of dicts
    def save(self, tasks: list[dict]) -> None:  # Saves list of dicts to JSON
```

**Current behavior:**
- Single file: `~/.todo_data.json`
- Returns/accepts `list[dict]` (not type-specific; currently used only for Tasks)
- No schema validation at storage layer
- Path can be overridden in constructor (used in tests with tmp_path)
- Parent directory creation: `mkdir(parents=True, exist_ok=True)`
- JSON serialization: `json.dump(tasks, f, indent=2, ensure_ascii=False)`

**Integration pattern:**
1. Service loads raw dicts from storage
2. Service deserializes dicts to model objects (validation happens in from_dict())
3. Service performs business logic
4. Service serializes model objects back to dicts
5. Service calls storage.save() with list of dicts

---

## Service Architecture

### TaskManager (Low-level CRUD service)
**File:** `src/services/task_manager.py` (lines 1-79)

**Responsibilities:**
- Load/persist Task objects via JsonStorage
- CRUD operations on Task collection
- In-memory cache of Task objects (dict[task_id, Task])
- Task lookup with prefix matching (e.g., "abc123..." can be found by "abc12")

**Methods:**
- `add(title, description=None, due_date=None) -> Task`
- `get(task_id: str) -> Task` (raises TaskNotFoundError if not found; supports prefix lookup)
- `list_all() -> list[Task]`
- `list_by_status(status: TaskStatus) -> list[Task]`
- `update(task_id, title=None, description=None, due_date=None) -> Task`
- `set_status(task_id, status: TaskStatus) -> Task`
- `set_due_date(task_id, due_date) -> Task`
- `delete(task_id: str) -> None`

**Internal methods:**
- `_load()` → deserializes Task objects from storage
- `_persist()` → serializes Task objects to storage

**Error handling:**
- TaskNotFoundError (custom exception) raised when task_id not found (supports prefix matching)

**Pattern: Load/Persist cycle**
```python
def _load(self) -> None:
    raw = self._storage.load()
    self._tasks = {d["id"]: Task.from_dict(d) for d in raw}

def _persist(self) -> None:
    self._storage.save([t.to_dict() for t in self._tasks.values()])
```

### TodoService (High-level API)
**File:** `src/services/todo_service.py` (lines 1-46)

**Responsibilities:**
- Wrap TaskManager for public-facing API
- Input validation (non-empty titles)
- Delegate CRUD to TaskManager

**Methods:**
- `add_task(title, description=None, due_date=None) -> Task` (validates non-empty title)
- `get_task(task_id: str) -> Task`
- `list_tasks(status: TaskStatus | None) -> list[Task]`
- `start_task(task_id) -> Task` (set status to IN_PROGRESS)
- `complete_task(task_id) -> Task` (set status to DONE)
- `reopen_task(task_id) -> Task` (set status to PENDING)
- `update_task(task_id, title=None, description=None, due_date=None) -> Task` (validates non-empty title)
- `set_due_date(task_id, due_date) -> Task`
- `delete_task(task_id) -> None`

**Validation pattern:**
```python
def add_task(self, title: str, description: Optional[str] = None, due_date: Optional[datetime] = None) -> Task:
    if not title or not title.strip():
        raise ValueError("Task title cannot be empty")
    return self._manager.add(title.strip(), description, due_date)
```

---

## Task Validation Pattern in Other Services

**Where validation happens:**
1. **High-level API (TodoService):** Input validation (non-empty title)
2. **Model layer (TaskComment, Task):** Serialization validation in from_dict()
3. **Manager layer (TaskManager):** Task existence validation via get() method

**Reference validation example:**
TaskManager.delete() uses get() to resolve prefix and validate existence:
```python
def delete(self, task_id: str) -> None:
    task = self.get(task_id)  # resolves prefix; raises if missing
    del self._tasks[task.id]
    self._persist()
```

**No explicit reference validation at model level:**
- TaskComment.from_dict() does NOT validate that task_id exists
- It assumes validation happens at service layer (where TaskManager.get() can be called)

---

## Existing Architecture Diagrams

### Class Diagram Reference
**File:** `artifacts/class_diagram.puml`

**Task-to-TaskComment Relationship (lines 104-110):**
```
Task "1" --> "*" TaskComment : has
```

This indicates:
- One Task has many TaskComments
- TaskComment has a reference to Task via task_id field
- No explicit cascade delete specified in UML (needs to be handled by CommentsService)

### Component Diagram Reference
**File:** `artifacts/component_diagram.puml`

**Structure:**
- Entry Point (main) → CLI Layer (InteractiveMenu, TodoCLI)
- CLI Layer → Service Layer (TodoService, TaskManager)
- Service Layer → Domain Model (Task, TaskStatus, TaskComment)
- Domain Model → Persistence Layer (JsonStorage)
- Storage → Database (todo_data.json)

**Note:** CommentsService should be added to Service Layer, not CLI Layer.

---

## Storage Mechanism Details for Comments

**Current JSON storage structure (single file):**
The file `~/.todo_data.json` currently stores only Tasks:
```json
[
  {
    "id": "task-uuid-1",
    "title": "Buy milk",
    "description": null,
    "status": "pending",
    "created_at": "2026-05-02T10:30:00+02:00",
    "updated_at": "2026-05-02T10:30:00+02:00",
    "due_date": null
  }
]
```

**Key observation:**
JsonStorage is generic (accepts/returns `list[dict]`, no type checking). It does NOT distinguish between Task, TaskComment, or other types.

**For CommentsService integration, options:**

1. **Separate storage file for comments** (Recommended for simplicity)
   - CommentsStorage or reuse JsonStorage with different path
   - File: `~/.todo_comments.json`
   - Allows independent persistence of comments

2. **Unified storage file** (More complex)
   - Store both tasks and comments in single JSON structure
   - Would require: `{"tasks": [...], "comments": [...]}`
   - Would need JsonStorage enhancement to understand structure

**Recommended approach:** Separate file because:
- Maintains independence of TaskManager and CommentsService
- Simpler storage mechanism (no schema changes)
- Aligns with single-responsibility principle
- Comments can be independently versioned/migrated

---

## CommentsService Requirements Analysis

### Functional Requirements

1. **Add comment to task**
   - Input: task_id, content
   - Validation: task_id must exist (call TaskManager.get() to validate)
   - Output: TaskComment object
   - Side effect: Persist to storage

2. **List comments for task** (ordered by created_at)
   - Input: task_id
   - Output: list[TaskComment] sorted by created_at ascending
   - Optional: filter/pagination (not specified, so assume basic list)

3. **Delete comment**
   - Input: comment_id
   - Validation: comment must exist
   - Side effect: Persist to storage
   - Note: No task validation needed (we're just deleting the comment)

4. **Cascade delete on task deletion**
   - When TaskManager.delete() is called, CommentsService must delete associated comments
   - Trigger: Need to hook into task deletion somehow
   - Integration point: Modify delete_task() in TodoService or add cascade logic

### Service Responsibilities (Per Requirements)

**Explicit:** Limited to TaskComment lifecycle (storage separate)
- Add comment
- List comments
- Delete comment

**Implicit:** Integration points
- Validate task_id exists (call TaskManager.get)
- Cascade delete when task is deleted

**Out of scope:**
- Edit/update existing comment (not mentioned)
- Comment author/metadata beyond id, task_id, content, created_at (TaskComment model already defined)
- Soft deletes or comment visibility flags

---

## What Needs to Be Added/Changed

### 1. New Service: CommentsService
**File:** `src/services/comments_service.py` (new)

**Should implement:**
```python
class CommentsService:
    def __init__(self, storage: Optional[JsonStorage] = None, task_manager: TaskManager) -> None:
        # Store task_manager for validation
        # Initialize storage (separate file or parameter)
        
    def add_comment(self, task_id: str, content: str) -> TaskComment:
        # Validate task exists: task_manager.get(task_id) raises TaskNotFoundError if missing
        # Validate content non-empty
        # Create TaskComment
        # Persist to storage
        # Return TaskComment
        
    def list_comments(self, task_id: str) -> list[TaskComment]:
        # Optionally validate task exists (nice-to-have)
        # Load all comments for task_id
        # Sort by created_at ascending
        # Return sorted list
        
    def delete_comment(self, comment_id: str) -> None:
        # Validate comment exists
        # Delete comment
        # Persist to storage
        
    def delete_task_comments(self, task_id: str) -> None:
        # Delete all comments for task_id
        # Persist to storage
        # (Helper for cascade delete)
```

**Exceptions:**
- Should define `CommentNotFoundError` (parallel to TaskNotFoundError)
- May raise ValueError for validation failures (empty content)

### 2. Update services/__init__.py
**File:** `src/services/__init__.py`

Add exports:
```python
from .comments_service import CommentsService, CommentNotFoundError
__all__ = [..., "CommentsService", "CommentNotFoundError"]
```

### 3. Update TodoService for cascade delete
**File:** `src/services/todo_service.py`

**Current delete_task() method:**
```python
def delete_task(self, task_id: str) -> None:
    self._manager.delete(task_id)
```

**Should become:**
```python
def __init__(self, storage: Optional[JsonStorage] = None) -> None:
    self._manager = TaskManager(storage)
    self._comments_service = CommentsService(storage, self._manager)

def delete_task(self, task_id: str) -> None:
    # Cascade delete comments first
    self._comments_service.delete_task_comments(task_id)
    # Then delete task
    self._manager.delete(task_id)
```

### 4. Storage for Comments
**File:** `src/storage/json_storage.py` or new service-level logic

**Option 1 (Simpler):** Reuse JsonStorage with different path in CommentsService constructor
```python
# In CommentsService.__init__
self._storage = storage or JsonStorage(path=str(Path.home() / ".todo_comments.json"))
```

**Option 2 (More explicit):** Create CommentStorage class (mirroring JsonStorage)
- Would add: `src/storage/comment_storage.py`
- But this violates DRY (duplicates JsonStorage logic)
- Not recommended unless comments need different serialization

### 5. Update Class Diagram
**File:** `artifacts/class_diagram.puml`

Add to services section:
```
class CommentsService {
    -storage : JsonStorage
    -taskManager : TaskManager
    --
    +CommentsService(storage: JsonStorage [0..1], taskManager: TaskManager)
    +addComment(taskId: String, content: String) : TaskComment
    +listComments(taskId: String) : List<TaskComment>
    +deleteComment(commentId: String) : void
    +deleteTaskComments(taskId: String) : void
}

exception CommentNotFoundError

TodoService --> CommentsService : comments
TodoService ..> CommentNotFoundError : raises
CommentsService --> TaskManager : validates
CommentsService --> JsonStorage : storage
```

Update TodoService relationship:
```
TodoService --> CommentsService : delegates
```

### 6. Update Component Diagram
**File:** `artifacts/component_diagram.puml`

Add to Service Layer:
```
component "Comment Manager" as CMgr
```

Update relationships:
```
SVC --> CMgr : comments
CMgr --> Storage : (separate comments file)
```

### 7. Tests for CommentsService
**File:** `tests/test_comments_service.py` (new)

Patterns (from test_todo_service.py and test_task_manager.py):
```python
@pytest.fixture
def service(tmp_path):
    storage = JsonStorage(str(tmp_path / "comments.json"))
    task_manager = TaskManager(JsonStorage(str(tmp_path / "tasks.json")))
    return CommentsService(storage, task_manager)

# Test cases:
# - add_comment with valid task_id returns TaskComment
# - add_comment with invalid task_id raises TaskNotFoundError
# - add_comment with empty content raises ValueError
# - list_comments returns sorted list by created_at
# - list_comments with no comments returns empty list
# - delete_comment removes comment
# - delete_comment with invalid comment_id raises CommentNotFoundError
# - delete_task_comments deletes all comments for task
# - Persistence: add/load cycle preserves comment data
```

---

## Key Implementation Patterns to Follow

### 1. Storage Integration
From TaskManager:
```python
def _load(self) -> None:
    raw = self._storage.load()
    self._tasks = {d["id"]: Task.from_dict(d) for d in raw}

def _persist(self) -> None:
    self._storage.save([t.to_dict() for t in self._tasks.values()])
```

**Apply to CommentsService:**
- Use dict[comment_id, TaskComment] for in-memory cache
- Call _load() in __init__
- Call _persist() after any mutation
- Maintain comments keyed by comment_id (not task_id)

### 2. Error Handling
From TaskManager:
```python
class TaskNotFoundError(Exception):
    pass

def get(self, task_id: str) -> Task:
    if task_id in self._tasks:
        return self._tasks[task_id]
    # ... prefix lookup ...
    raise TaskNotFoundError(f"Task '{task_id}' not found")
```

**Apply to CommentsService:**
- Define CommentNotFoundError
- Raise from delete_comment() if comment_id not found
- Use TaskManager.get() to validate task_id (which raises TaskNotFoundError)

### 3. Validation
From TodoService:
```python
def add_task(self, title: str, ...) -> Task:
    if not title or not title.strip():
        raise ValueError("Task title cannot be empty")
    return self._manager.add(title.strip(), description, due_date)
```

**Apply to CommentsService:**
- Validate content in add_comment (non-empty, non-whitespace)
- Validate task_id by calling task_manager.get(task_id)

### 4. Sorting
From requirements: "ordered by created_at"

**Apply to CommentsService.list_comments():**
```python
def list_comments(self, task_id: str) -> list[TaskComment]:
    comments = [c for c in self._comments.values() if c.task_id == task_id]
    return sorted(comments, key=lambda c: c.created_at)
```

---

## Dependencies and Integration Points

### Internal Dependencies
- **TaskComment model:** Already defined in src/models/task_comment.py
- **TaskManager:** Needed in CommentsService.__init__ for task_id validation
- **JsonStorage:** For persistence (can be separate file)
- **CommentNotFoundError:** New exception, define in comments_service.py

### Integration Points
1. **TodoService.delete_task()** — Must call comments_service.delete_task_comments() first
2. **TodoService.__init__()** — Must initialize CommentsService with task_manager reference
3. **services/__init__.py** — Must export CommentsService and CommentNotFoundError
4. **Diagrams** — Must update class_diagram.puml and component_diagram.puml

### No Changes Needed To
- Task model (already has relationship to TaskComment)
- TaskManager (comments are separate concern)
- JsonStorage (generic, works with any list[dict])
- CLI layer (out of scope for this task)
- Existing tests (except add new CommentsService tests)

---

## Storage Data Structure Example

**~/.todo_comments.json** (recommended separate file):
```json
[
  {
    "id": "comment-uuid-1",
    "task_id": "task-uuid-1",
    "content": "Remember to buy quality milk",
    "created_at": "2026-05-02T10:45:00+02:00"
  },
  {
    "id": "comment-uuid-2",
    "task_id": "task-uuid-1",
    "content": "Check expiration date",
    "created_at": "2026-05-02T11:00:00+02:00"
  }
]
```

When task-uuid-1 is deleted:
- TaskManager.delete() removes from tasks
- TodoService.delete_task() calls CommentsService.delete_task_comments("task-uuid-1")
- CommentsService removes both comments from in-memory cache
- CommentsService persists empty list (or list without these comments)

---

## Scope Signals

### In Scope (Must Implement)
- CommentsService class with add_comment, list_comments, delete_comment methods
- Task existence validation via TaskManager.get()
- Comment persistence via JsonStorage
- Cascade delete via delete_task_comments() helper
- CommentNotFoundError exception
- Sorting by created_at in list_comments()
- Tests for all CommentsService methods

### Out of Scope
- Edit/update existing comments
- Comment author, edited_at, edit history
- Soft deletes or archiving
- Comment visibility/permissions
- CLI commands for comments (that's a separate task)
- Interactive menu for comments (that's a separate task)

### Borderline (Not Specified)
- Validation of task_id in list_comments() (nice-to-have, not essential)
- Pagination or filtering in list_comments() (not specified, assume no)
- Unique constraint on comment content (not specified, assume no)
- Comment threading/replies (not specified, assume flat list)

---

## Summary of Findings

1. **Model ready:** TaskComment is fully defined with proper serialization, validation, and CEST timezone awareness

2. **Storage mechanism:** JsonStorage is generic and extensible. Recommend separate file (~/.todo_comments.json) to avoid schema complexity

3. **Service patterns established:** TaskManager and TodoService show clear patterns for load/persist cycle, validation, error handling, and in-memory caching

4. **Task validation:** Done via TaskManager.get(), which raises TaskNotFoundError. CommentsService should call this to validate task_id before adding comments

5. **Cascade delete:** Requires integration point in TodoService.delete_task() to call CommentsService.delete_task_comments() before deleting task

6. **Architecture alignment:** CommentsService belongs in Service Layer (parallel to TodoService/TaskManager), NOT in CLI layer. Diagrams need updating

7. **Test patterns:** Follow fixtures with tmp_path for storage isolation, parallel to existing test_task_manager.py and test_todo_service.py

8. **Sorting:** TaskComment has created_at field ready for ordering. list_comments() should sort ascending by created_at
