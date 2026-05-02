# COMPREHENSIVE ANALYSIS: CommentsService Implementation

## Task Summary

Implement a dedicated `CommentsService` class that centralizes all comment lifecycle management operations (add, list by task, delete, and edit as bonus). This service should abstract comment operations away from TodoService, follow existing architectural patterns, and ensure comments cascade delete when their parent task is deleted.

---

## Current State of the Codebase

### 1. **Models Layer** (`src/models/`)

**TaskComment Model** (exists in `src/models/task_comment.py`)
- Dataclass with fields: `id` (UUID), `task_id` (str), `content` (str), `created_at` (datetime UTC), `author` (Optional[str]), `updated_at` (Optional[datetime])
- Methods: `to_dict()`, `from_dict()` for JSON serialization
- No validation at model level; validation is at service layer
- Fully functional with serialization support

**Task Model** (exists in `src/models/task.py`)
- Contains `comments: list[TaskComment]` field
- Has `add_comment(content, author)` method that creates a TaskComment and appends to the list
- `to_dict()` and `from_dict()` already handle comment serialization/deserialization

### 2. **Storage Layer** (`src/storage/`)

**JsonStorage** (exists in `src/storage/json_storage.py`)
- Simple interface: `load()` returns `list[dict]`, `save(tasks: list[dict])` writes to file
- Does NOT handle comments separately — comments are embedded in the task dict
- Comments cascade delete automatically when a task is deleted (because comments are part of task serialization)

### 3. **Service Layer** (`src/services/`)

**TaskManager** (exists in `src/services/task_manager.py`)
- Manages in-memory cache `_tasks: dict[str, Task]`
- Methods: `add()`, `get()`, `list_all()`, `list_by_status()`, `update()`, `set_status()`, `delete()`
- Calls `_persist()` after mutations to save to storage
- Prefix-based task ID lookup

**TodoService** (exists in `src/services/todo_service.py`)
- Currently has comment operations mixed in:
  - `add_comment(task_id, content, author)` — validates non-empty content, calls `task.add_comment()`, then `_manager._persist()`
  - `get_task_comments(task_id)` — returns `task.comments` list
  - `delete_comment(task_id, comment_id)` — finds and removes comment, then `_manager._persist()`
- **Issue**: These methods directly access and manipulate task internals. Comments are not isolated.

### 4. **Test Coverage**

Existing comment tests (in `tests/test_todo_service.py`):
- Comment creation, validation, persistence
- Listing all comments for a task (ordered by creation)
- Comment deletion and persistence
- Error handling for nonexistent tasks/comments
- 38 tests covering all acceptance criteria

---

## What Needs to Be Implemented

### **1. CommentsService Class**

**File**: New file `src/services/comments_service.py`

**Interface**:
- `add_comment(task_id, content, author=None)` — Create and persist a comment
- `list_comments(task_id)` — Get all comments ordered by created_at
- `delete_comment(task_id, comment_id)` — Remove a comment
- `edit_comment(task_id, comment_id, new_content)` — Edit content and update timestamp (bonus)

**Key design decisions**:
1. Takes `TaskManager` in constructor, not `JsonStorage` directly
2. Validates task existence using `TaskManager.get()` before operating
3. Directly accesses in-memory task's comment list
4. Calls `_manager._persist()` after mutations
5. Returns `TaskComment` objects (not dicts)
6. Cascade delete is implicit (comments embedded in task)

### **2. Integration Points**

**In TaskManager** (`src/services/task_manager.py`):
- No changes needed — comments already cascade delete when task is deleted

**In TodoService** (`src/services/todo_service.py`):
- Keep existing methods for backward compatibility (already have 38 tests)

**In Storage** (`src/storage/json_storage.py`):
- No changes — comments are already nested in task dicts

### **3. Cascade Delete Mechanism**

**Current behavior (already working)**:
1. When `TaskManager.delete(task_id)` is called, it removes the entire task from `_tasks` dict
2. When `_persist()` is called, it serializes all remaining tasks (comments are part of task dict)
3. Comments are automatically deleted because they're nested in the task data

### **4. Storage Integration Details**

**Data flow for adding a comment**:
1. CommentsService.add_comment(task_id, content, author)
2. Validates content (non-empty after strip)
3. Gets task from TaskManager via `self._manager.get(task_id)` — raises TaskNotFoundError if not found
4. Creates TaskComment object with auto-generated id and created_at
5. Appends to `task.comments` list
6. Calls `self._manager._persist()` to serialize and save

### **5. Files to Modify/Create**

| File | Action | Reason |
|------|--------|--------|
| `src/services/comments_service.py` | CREATE | New CommentsService class |
| `src/services/__init__.py` | MODIFY | Export CommentsService |
| `tests/test_comments_service.py` | CREATE | New test suite for CommentsService |
| `artifacts/class_diagram.puml` | MODIFY | Add CommentsService to diagram |

---

## Implementation Constraints

1. **No Storage Layer Changes** — Comments stay embedded in Task JSON
2. **Must use TaskManager** — Cannot bypass to access storage directly
3. **In-Memory Model Mutation** — Task.comments is mutable list
4. **Cascade Delete is Implicit** — No explicit code needed
5. **Timezone Handling** — Use `datetime.now(timezone.utc)` for consistency
6. **ID Prefix Lookup** — TaskManager.get() supports prefix matching for task IDs

---

## Key Findings Summary

1. **TaskComment model already exists and is fully functional**
2. **Comments are already embedded in Task storage** — cascade delete is implicit
3. **TodoService already has comment methods**, but they're mixed with task operations
4. **Storage layer doesn't need changes**
5. **Testing infrastructure is ready** — 38 existing tests provide patterns
6. **Architecture is consistent** — CommentsService follows same patterns as TodoService
