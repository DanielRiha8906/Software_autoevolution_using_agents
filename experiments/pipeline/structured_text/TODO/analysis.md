# TaskComment Class Analysis

## Task Summary

Introduce a new `TaskComment` domain class to extend the TODO application with task commenting functionality. The new class must support:

**MUST (Mandatory):**
- `id` field as UUID string (auto-generated)
- `task_id` field as string (foreign key to Task)
- `content` field as string (comment text)
- `created_at` field as datetime with CEST/UTC+2 timezone (ISO 8601 format)
- JSON serialization via `to_dict()` method
- JSON deserialization via `from_dict()` class method

**SHOULD (High Priority):**
- Validate that `content` is not empty
- Maintain relationship integrity with Task (ensure referenced task exists)
- Maintain data consistency through storage layer

**COULD (Optional but valuable):**
- `author` field as string (who wrote the comment)
- `updated_at` field as datetime (when comment was last modified)

**WON'T (Out of Scope):**
- Rich text or markdown formatting
- Nested comments (comments on comments)
- Comment threading or replies

---

## Current Domain Model Analysis

### Task Class Structure

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task.py`

**Current implementation:**
```python
@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

**Key characteristics:**
- Uses Python dataclass decorator
- ID generation: UUID4 converted to string via `str(uuid.uuid4())`
- Datetime fields: UTC timezone via `timezone.utc`
- Serialization methods already implemented: `to_dict()` and `from_dict()`
- Optional fields use `Optional[T] = None` pattern
- Dataclass fields follow order: required field first, then optional fields with defaults

**Serialization pattern (to_dict):**
```python
def to_dict(self) -> dict:
    result = {
        "id": self.id,
        "title": self.title,
        "description": self.description,
        "status": self.status.value,  # Enum conversion
        "created_at": self.created_at.isoformat(),  # ISO 8601 string
        "updated_at": self.updated_at.isoformat(),
    }
    if self.due_date is not None:
        result["due_date"] = self.due_date.isoformat()
    return result
```

**Deserialization pattern (from_dict):**
```python
@classmethod
def from_dict(cls, data: dict) -> Task:
    due_date_str = data.get("due_date")  # Optional fields use .get()
    due_date = datetime.fromisoformat(due_date_str) if due_date_str else None
    return cls(
        id=data["id"],
        title=data["title"],
        description=data.get("description"),  # Optional with .get()
        status=TaskStatus(data["status"]),  # Enum from string value
        due_date=due_date,
        created_at=datetime.fromisoformat(data["created_at"]),  # Required fields use direct access
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )
```

**Key observations:**
- Required fields accessed directly: `data["key"]` raises KeyError if missing
- Optional fields accessed via `.get()`: returns None if missing (backward compatible)
- Datetime strings parsed via `datetime.fromisoformat()` which understands ISO 8601 with timezone
- Enum values stored as string in JSON, reconstructed via `TaskStatus(value)` lookup

---

## Storage Layer Implementation

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/storage/json_storage.py`

**Current implementation:**
```python
class JsonStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else Path.home() / ".todo_data.json"

    def load(self) -> list[dict]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, tasks: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
```

**Design pattern:**
- Generic list[dict] storage (not Task-specific)
- Default path: `~/.todo_data.json`
- Handles missing files gracefully (returns empty list)
- Creates parent directories as needed
- Uses standard `json` module (no custom serialization)

**Persistence flow:**
1. TaskManager iterates tasks and calls `task.to_dict()`
2. JsonStorage.save receives `list[dict]` and writes as JSON
3. On load: JsonStorage.load() returns raw dicts
4. TaskManager calls `Task.from_dict(d)` to reconstruct objects

**Current JSON structure sample:**
```json
{
  "id": "2c97feb8-de4d-4175-9094-5040fa0e0f8b",
  "title": "Test Task",
  "description": "A test task",
  "status": "pending",
  "due_date": "2026-06-01T12:30:00+00:00",
  "created_at": "2026-05-02T21:25:29.121374+00:00",
  "updated_at": "2026-05-02T21:25:29.121378+00:00"
}
```

---

## Service Layer Architecture

### TaskManager (CRUD operations)

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/task_manager.py`

**Structure:**
- Owns in-memory dict of tasks: `self._tasks: dict[str, Task]`
- Delegates storage to JsonStorage
- Implements load/persist pattern: loads on init, persists after mutations
- CRUD methods: `add()`, `get()`, `list_all()`, `list_by_status()`, `update()`, `set_status()`, `delete()`
- Handles task prefix lookup (e.g., first 8 chars of UUID)
- Raises `TaskNotFoundError` for missing tasks

**Key methods:**
```python
def add(self, title: str, description: Optional[str] = None) -> Task:
    task = Task(title=title, description=description)
    self._tasks[task.id] = task
    self._persist()  # Always persists after mutation
    return task

def _persist(self) -> None:
    self._storage.save([t.to_dict() for t in self._tasks.values()])

def _load(self) -> None:
    raw = self._storage.load()
    self._tasks = {d["id"]: Task.from_dict(d) for d in raw}
```

### TodoService (Business logic layer)

**File:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/todo_service.py`

**Purpose:**
- Validation layer above TaskManager
- Public API for business operations
- Input validation (e.g., "Task title cannot be empty")

**Methods:**
- `add_task()`, `get_task()`, `list_tasks()`, `start_task()`, `complete_task()`, `reopen_task()`, `update_task()`, `delete_task()`

---

## Datetime and Timezone Handling

### Current Approach in Codebase

**Timezone used:** UTC (`timezone.utc`)
**Serialization format:** ISO 8601 with timezone offset via `.isoformat()`
**Example:** `"2026-05-02T21:25:29.121374+00:00"`

**Python implementation pattern:**
```python
from datetime import datetime, timezone

# Creation (stored in UTC)
created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

# Comparison (normalized to UTC)
if datetime.now(timezone.utc) > self.due_date:
    return True

# Serialization (isoformat preserves timezone)
result["created_at"] = self.created_at.isoformat()  # → "2026-05-02T21:25:29+00:00"

# Deserialization (fromisoformat parses timezone)
created_at=datetime.fromisoformat(data["created_at"])  # Parses with timezone
```

### Requirement: CEST/UTC+2 Timezone

**Current status:** All existing timestamps use UTC internally.
**Task requirement:** `created_at` for TaskComment should use "CEST/UTC+2" and ISO 8601 format.

**Design options:**

1. **Store UTC, display CEST (Recommended - matches existing pattern)**
   - Store all datetimes in UTC internally (consistent with Task)
   - Convert to CEST only in UI layer for display
   - Advantages: consistent, portable, supports multi-timezone use cases
   - Disadvantages: requires conversion code in UI

2. **Store CEST, use ZoneInfo**
   - Use `zoneinfo.ZoneInfo('Europe/Paris')` for CEST
   - Serialize as ISO 8601 with CEST offset: `"2026-05-02T23:25:29+02:00"`
   - Breaks consistency with Task's UTC timestamps
   - Disadvantages: inconsistent with existing code

3. **Store naive datetime interpreted as CEST**
   - No timezone info in datetime object
   - Interpret as CEST on load
   - Disadvantages: fragile, loses information

**Recommendation:** Option 1 (store UTC internally, display CEST in UI) maintains consistency with existing Task class while meeting the ISO 8601 requirement.

---

## Test Coverage Analysis

### Existing Test Structure

**File locations:**
- `/tests/test_task.py` — Task model tests (48 tests)
- `/tests/test_json_storage.py` — Storage tests (4 tests)
- `/tests/test_task_manager.py` — CRUD and persistence tests
- `/tests/test_todo_service.py` — Business logic tests
- `/tests/test_todo_cli.py` — CLI argument parsing tests

**Test patterns observed:**

1. **Roundtrip serialization tests:**
   ```python
   def test_task_roundtrip():
       task = Task(title="Test", description="desc")
       restored = Task.from_dict(task.to_dict())
       assert restored.id == task.id
       # ... all fields match
   ```

2. **Backward compatibility tests:**
   ```python
   def test_task_from_dict_without_due_date():
       old_data = {
           "id": "test-id",
           "title": "Old Task",
           # ... missing due_date
       }
       task = Task.from_dict(old_data)
       assert task.due_date is None
   ```

3. **Datetime handling tests:**
   ```python
   def test_task_due_date_set():
       due_date = datetime(2025, 12, 25, 10, 0, 0, tzinfo=timezone.utc)
       task = Task(title="Test", due_date=due_date)
       assert task.due_date == due_date
   ```

4. **Persistence tests:**
   ```python
   def test_persistence(tmp_path):
       m1 = TaskManager(JsonStorage(path))
       task = m1.add("Persisted")
       m2 = TaskManager(JsonStorage(path))  # new instance
       assert m2.get(task.id).title == "Persisted"
   ```

---

## Proposed TaskComment Class Design

### Basic Structure

```python
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

@dataclass
class TaskComment:
    task_id: str  # Foreign key reference to Task
    content: str  # Comment text (required)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: Optional[str] = None  # COULD: who wrote it
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None  # COULD: modification timestamp
```

**Key design decisions:**

1. **Field ordering:** `task_id` and `content` first (required), then id and optional fields
2. **ID generation:** Same pattern as Task (UUID4 as string)
3. **Timezone:** UTC internally (consistent with Task)
4. **Updated_at:** Optional because comments might not be editable, or is separate requirement
5. **Author:** Optional per COULD requirement

### Serialization Methods

**Pattern: Consistent with Task**

```python
def to_dict(self) -> dict:
    result = {
        "id": self.id,
        "task_id": self.task_id,
        "content": self.content,
        "author": self.author,
        "created_at": self.created_at.isoformat(),
    }
    if self.updated_at is not None:
        result["updated_at"] = self.updated_at.isoformat()
    return result

@classmethod
def from_dict(cls, data: dict) -> TaskComment:
    updated_at_str = data.get("updated_at")
    updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None
    return cls(
        id=data["id"],
        task_id=data["task_id"],
        content=data["content"],
        author=data.get("author"),  # Optional
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=updated_at,
    )
```

### Validation Method

**Pattern: Matches TodoService validation approach**

```python
def validate(self) -> None:
    """Validate comment content is not empty."""
    if not self.content or not self.content.strip():
        raise ValueError("Comment content cannot be empty")
```

Or as a class-level validation in a service layer.

---

## Integration Points

### Where TaskComment Will Be Used

1. **New Service: CommentManager (parallel to TaskManager)**
   - Store comments in JSON (separate file or nested in tasks)
   - CRUD operations for comments
   - Query comments by task_id
   - File: `/src/services/comment_manager.py`

2. **Enhanced TodoService**
   - Delegate to CommentManager
   - Methods: `add_comment()`, `get_comments()`, `delete_comment()`, etc.
   - File: `/src/services/todo_service.py` (add methods)

3. **CLI Commands**
   - `add-comment <task_id> <content>` — Add comment to task
   - `show-comments <task_id>` — List comments on task
   - `delete-comment <comment_id>` — Remove comment
   - File: `/src/cli/todo_cli.py` (add subcommands)

4. **Interactive Menu**
   - Menu option to add/view comments on selected task
   - File: `/src/cli/interactive_menu.py` (add menu items)

5. **Storage Format**
   - Option A: Comments in separate JSON file (e.g., `~/.todo_comments.json`)
   - Option B: Comments nested under Task in JSON (changes Task structure)
   - Option C: Flat list of comments in single file with task_id references
   - **Recommendation:** Option C (separate flat list, simpler, scalable)

### Storage Format Decision

**Recommended approach: Flat comment list in separate JSON file**

File: `~/.todo_comments.json`

Example structure:
```json
[
  {
    "id": "abc123...",
    "task_id": "2c97feb8...",
    "content": "This is a comment",
    "author": "alice",
    "created_at": "2026-05-03T15:30:00+00:00",
    "updated_at": null
  }
]
```

**Advantages:**
- Clean separation of concerns
- Easy to query all comments for a task
- Doesn't modify existing Task serialization
- Easier to delete all comments for a task

---

## Required Changes by Component

### Domain Model Layer

**File:** `/src/models/task_comment.py` (NEW)
- Create new `TaskComment` dataclass
- Implement `to_dict()` method (MUST)
- Implement `from_dict()` class method (MUST)
- Optional: validation method or move to service layer
- Optional: `update()` method if comments are editable

**File:** `/src/models/__init__.py` (MODIFY)
- Export TaskComment alongside Task

### Service Layer

**File:** `/src/services/comment_manager.py` (NEW)
- Create `CommentManager` class (parallel to TaskManager)
- Implement CRUD: `add()`, `get()`, `list_by_task()`, `delete()`, `list_all()`
- Handle persistence to JSON storage
- Raise exception if referenced task doesn't exist

**File:** `/src/services/todo_service.py` (MODIFY)
- Add `_comment_manager` field
- Add methods: `add_comment()`, `get_comments()`, `delete_comment()`
- Validation: non-empty content, task exists

### Storage Layer

**File:** `/src/storage/json_storage.py` (REVIEW)
- No changes needed (generic list[dict] storage works for comments too)
- May want to refactor to `CommentStorage` class or reuse existing

**File implications:**
- Task storage: `~/.todo_data.json` (unchanged)
- Comment storage: `~/.todo_comments.json` (new)

### CLI Layer

**File:** `/src/cli/todo_cli.py` (MODIFY)
- Add `add-comment <task_id>` subcommand
  - Arguments: task_id (positional), content (positional or -c flag)
  - Optional: --author flag
- Add `show-comments <task_id>` subcommand
  - List all comments on task in chronological order
- Add `delete-comment <comment_id>` subcommand

**File:** `/src/cli/interactive_menu.py` (MODIFY)
- Add menu option: "View/manage comments on task"
- Add comment input dialog
- Display comments in task details view

### Test Layer

**File:** `/tests/test_task_comment.py` (NEW)
- Test TaskComment initialization and defaults
- Test UUID generation uniqueness
- Test `to_dict()` and `from_dict()` roundtrip
- Test backward compatibility (JSON without updated_at)
- Test content validation (empty/whitespace)
- Test datetime serialization/deserialization with timezone

**File:** `/tests/test_comment_manager.py` (NEW)
- Test CRUD operations
- Test persistence to JSON
- Test querying comments by task_id
- Test exception when task_id doesn't exist in Task storage

**File:** `/tests/test_todo_service.py` (MODIFY)
- Add tests for `add_comment()`, `get_comments()`, `delete_comment()`
- Integration tests with tasks

**File:** `/tests/test_json_storage.py` (OPTIONAL)
- Test comment storage (if separate storage class created)

**File:** `/tests/test_todo_cli.py` (MODIFY)
- Test new CLI commands for comments

### Diagram Updates

**File:** `/artifacts/class_diagram.puml` (MODIFY)
- Add TaskComment class
- Show relationship: TaskComment → Task (foreign key)
- Add CommentManager class
- Update service layer to show comment operations

---

## JSON Serialization Strategy

### Current Task JSON Example
```json
{
  "id": "2c97feb8-de4d-4175-9094-5040fa0e0f8b",
  "title": "Test Task",
  "description": "A test task",
  "status": "pending",
  "due_date": "2026-06-01T12:30:00+00:00",
  "created_at": "2026-05-02T21:25:29.121374+00:00",
  "updated_at": "2026-05-02T21:25:29.121378+00:00"
}
```

### Proposed TaskComment JSON Structure
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "2c97feb8-de4d-4175-9094-5040fa0e0f8b",
  "content": "This needs clarification on requirement XYZ",
  "author": "alice",
  "created_at": "2026-05-03T15:30:00+00:00",
  "updated_at": null
}
```

### Serialization Rules

**to_dict() rules (matching Task pattern):**
- Include all fields except optional ones set to None
- Datetime fields: use `.isoformat()` for ISO 8601 strings
- Optional fields not set: omit key (e.g., if `updated_at` is None, don't include key)
- String fields: include as-is, even if empty (content validation is in service layer)

**from_dict() rules (matching Task pattern):**
- Required fields: direct access with KeyError if missing (`data["task_id"]`)
- Optional fields: use `.get()` to return None if missing (`data.get("author")`)
- Datetime parsing: use `datetime.fromisoformat()` to parse ISO 8601 strings

### Backward Compatibility

**Concern:** What if old comments have different structure or missing fields?

**Strategy (matching Task approach):**
- If `author` is missing from JSON: load as None
- If `updated_at` is missing: load as None
- If `content` or `task_id` is missing: KeyError (data corruption, should fail)
- If unknown keys present: ignore them (safe for schema evolution)

**Test requirement:**
```python
def test_comment_from_dict_without_author():
    old_data = {
        "id": "550e8400...",
        "task_id": "2c97feb8...",
        "content": "Old comment",
        "created_at": "2026-05-03T15:30:00+00:00"
        # missing author and updated_at
    }
    comment = TaskComment.from_dict(old_data)
    assert comment.author is None
    assert comment.updated_at is None
```

---

## Relationship Integrity & Validation

### Foreign Key Constraint: task_id Must Reference Existing Task

**Problem:** TaskComment references Task via `task_id`, but nothing prevents orphaned comments.

**Enforcement options:**

1. **Constraint in CommentManager (Recommended)**
   ```python
   def add(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
       # Check task exists via TaskManager
       if not self._task_manager.exists(task_id):
           raise TaskNotFoundError(f"Task '{task_id}' not found")
       comment = TaskComment(task_id=task_id, content=content, author=author)
       self._comments[comment.id] = comment
       self._persist()
       return comment
   ```

2. **Constraint in TodoService**
   ```python
   def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
       self._manager.get(task_id)  # Raises TaskNotFoundError if missing
       return self._comment_manager.add(task_id, content, author)
   ```

3. **No constraint (check at query time)**
   - Allow orphaned comments to exist
   - Filter on query to avoid displaying them
   - Simplest but allows data inconsistency

**Recommendation:** Implement in CommentManager (option 1) to prevent invalid inserts at the source.

### Cascading Deletion

**Problem:** When a Task is deleted, what happens to its comments?

**Options:**
1. **Cascade delete:** Automatically delete all comments when Task deleted
2. **Cascade null:** Not applicable (no nullable foreign keys in this design)
3. **Restrict deletion:** Raise error if task has comments
4. **Orphan deletion:** Allow orphaned comments to persist

**Recommendation:** Cascade delete (option 1) - maintain integrity automatically.

```python
# In TaskManager.delete()
def delete(self, task_id: str) -> None:
    task = self.get(task_id)
    self._comment_manager.delete_all_by_task(task.id)  # Cascade
    del self._tasks[task.id]
    self._persist()
```

---

## Design Constraints & Tradeoffs

### Constraint 1: No Rich Text or Markdown

**Implication:**
- Store `content` as plain string only
- No formatting metadata in JSON
- UI layer displays as-is (no rendering needed)
- Validation: check for empty/whitespace only

### Constraint 2: No Nested Comments

**Implication:**
- TaskComment doesn't reference other comments
- No `parent_comment_id` field
- Simpler data model, simpler queries
- All comments equal, no hierarchy

### Constraint 3: Not Editable (or editable?)

**Current requirement:** No mention of editing comments.
**Assumption:** Comments are created and can be deleted, but not edited.
**Alternative:** Include `updated_at` to allow edits (currently marked as COULD).

**If editable:**
- Add `update()` method to TaskComment
- Include `updated_at` in serialization
- Add `update_comment()` method in CommentManager/TodoService
- Update CLI to support edit command

**Current recommendation:** Implement `updated_at` as optional (COULD requirement), but don't implement edit functionality yet. Makes future enhancement easier.

---

## Implementation Scope Matrix

| Component | MUST | SHOULD | COULD | Notes |
|-----------|------|--------|-------|-------|
| TaskComment class | id, task_id, content, created_at, to_dict, from_dict | Content validation | author, updated_at | Dataclass in models/ |
| CommentManager | CRUD ops, persistence | Query by task_id, FK check | - | New service class |
| TodoService integration | add_comment, delete_comment | get_comments, list_comments | - | Delegation methods |
| Storage | Save/load comments JSON | - | - | Uses existing JsonStorage |
| CLI support | - | show-comments, add-comment | delete-comment | New subcommands |
| Interactive menu | - | Comment view/add option | - | Optional UI enhancement |
| Tests | Roundtrip, backward compat, validation | Persistence, FK checks | - | Parallel to Task tests |
| Diagrams | Update class diagram | - | - | Add TaskComment + CommentManager |

---

## File Changes Summary

### New Files (Must Create)
1. `/src/models/task_comment.py` — TaskComment dataclass
2. `/src/services/comment_manager.py` — CommentManager CRUD
3. `/tests/test_task_comment.py` — TaskComment tests
4. `/tests/test_comment_manager.py` — CommentManager tests

### Modified Files (Must Update)
1. `/src/models/__init__.py` — Export TaskComment
2. `/src/services/todo_service.py` — Add comment methods
3. `/tests/test_todo_service.py` — Add comment operation tests

### Optional/Enhanced Files
1. `/src/cli/todo_cli.py` — Add comment subcommands
2. `/src/cli/interactive_menu.py` — Add comment UI
3. `/artifacts/class_diagram.puml` — Show TaskComment and CommentManager

### Unmodified Files
1. `/src/storage/json_storage.py` — Generic, works as-is
2. `/src/models/task.py` — No changes needed
3. `/src/services/task_manager.py` — No Task changes needed

---

## Key Implementation Patterns to Follow

### 1. UUID Generation
```python
id: str = field(default_factory=lambda: str(uuid.uuid4()))
```
Convert to string immediately (matches Task pattern).

### 2. Datetime Handling
```python
created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```
Use UTC internally, convert to display format in UI (matches Task pattern).

### 3. Optional Fields with Backward Compatibility
```python
@classmethod
def from_dict(cls, data: dict) -> TaskComment:
    author = data.get("author")  # Returns None if missing
    updated_at_str = data.get("updated_at")
    updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None
```
Use `.get()` for optional, handle None gracefully.

### 4. Persistence
```python
def _persist(self) -> None:
    self._storage.save([c.to_dict() for c in self._comments.values()])

def _load(self) -> None:
    raw = self._storage.load()
    self._comments = {d["id"]: TaskComment.from_dict(d) for d in raw}
```
Load on init, persist after every mutation (matches TaskManager pattern).

### 5. Validation
```python
def add_comment(self, task_id: str, content: str) -> TaskComment:
    if not content or not content.strip():
        raise ValueError("Comment content cannot be empty")
    # ... rest of add logic
```
Validation in service layer (matches TodoService pattern).

---

## Ambiguities & Working Assumptions

### Ambiguity 1: Storage Format

**Question:** Should comments be in same file as tasks or separate file?

**Options:**
- Option A: Separate file (`~/.todo_comments.json`) — easier querying, clean separation
- Option B: Nested in Task JSON — simpler unified storage, but requires Task serialization change
- Option C: Nested in single flat file with type field — hybrid

**Working assumption:** Option A (separate file). Rationale: matches pattern of Task, doesn't require changing existing Task class, easier to scale.

### Ambiguity 2: Comment Editability

**Question:** Are comments immutable once created, or can they be edited?

**Options:**
- Immutable: No `updated_at` or edit methods
- Editable: Include `updated_at`, add update methods, track changes
- Soft delete: Add deleted flag instead of true deletion

**Working assumption:** Not currently editable. Include `updated_at` field as optional (COULD requirement) for future extensibility, but don't implement edit operations.

### Ambiguity 3: Author Field Usage

**Question:** Is author auto-filled (e.g., from system user) or user-provided?

**Options:**
- Auto-filled: Get from environment (not in this design)
- User-provided: Pass via CLI/API
- Optional: Can be null if not provided

**Working assumption:** Optional, user-provided. User can pass via `--author` flag in CLI or leave blank. Stored as-is in JSON.

### Ambiguity 4: Cascading Behavior

**Question:** When Task is deleted, what happens to comments?

**Options:**
- Cascade delete: Remove comments too
- Restrict: Prevent task deletion if comments exist
- Orphan: Allow comments to persist without task

**Working assumption:** Cascade delete. When Task is deleted, all its comments are deleted. Maintains referential integrity.

### Ambiguity 5: Timezone for created_at

**Question:** Task requirement says "CEST/UTC+2" but implementation uses UTC. Which is correct?

**Options:**
- Store UTC internally: consistent with Task, convert to CEST in UI
- Store CEST: use ZoneInfo('Europe/Paris'), inconsistent with Task
- Naive datetime: no timezone, ambiguous

**Working assumption:** Store UTC internally (consistent with Task), serialize to ISO 8601 with UTC offset. Conversion to CEST display format happens in UI layer only.

---

## Summary Table

| Aspect | Status | Notes |
|--------|--------|-------|
| **UUID ID generation** | Clear | Use `str(uuid.uuid4())` pattern |
| **Datetime handling** | Clear | UTC internally, ISO 8601 serialization |
| **Optional fields** | Clear | Use `.get()` in from_dict for backward compat |
| **Storage format** | Decided | Separate `~/.todo_comments.json` file |
| **Relationship validation** | Decided | Check FK in CommentManager.add() |
| **Cascade deletion** | Decided | Delete comments when task deleted |
| **Content validation** | Clear | Non-empty check in service layer |
| **Author field** | Optional | User-provided, can be null |
| **Updated_at field** | Optional | Include but don't implement editing |
| **Rich text support** | Out of scope | Plain text only |
| **Nested comments** | Out of scope | No comment-on-comment support |

---

## Files to Modify/Create (Absolute Paths)

### Must Create
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task_comment.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/comment_manager.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/tests/test_task_comment.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/tests/test_comment_manager.py`

### Must Modify
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/__init__.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/todo_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/tests/test_todo_service.py`

### Should Modify (Lower Priority)
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/cli/todo_cli.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/cli/interactive_menu.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/artifacts/class_diagram.puml`

### Unchanged (No changes needed)
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/storage/json_storage.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/task_manager.py`

