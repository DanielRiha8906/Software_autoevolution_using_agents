# Task 03: Add TaskComment Support — Analysis Report

## Executive Summary

Task 03 requires implementing a new `TaskComment` model to enable users to attach comments to tasks. This is a new feature requiring a complete domain model (TaskComment class), persistence integration, and service-layer support. The feature has well-defined acceptance criteria with explicit out-of-scope items.

---

## Task Overview

**User Story**: "As a user collaborating on tasks, I want to attach comments to a task, so that I can record notes, decisions, or updates alongside the task itself."

**Scope**: Core data model and serialization; does NOT include UI, nested comments, markdown, or rich text.

---

## Current Codebase Structure

### 1. Models Layer (`src/models/`)

#### Task Class (`src/models/task.py`)
- **Type**: Python dataclass (mutable attributes)
- **Attributes**:
  - `id`: str (UUID, auto-generated)
  - `title`: str (required)
  - `description`: Optional[str]
  - `status`: TaskStatus enum (PENDING, IN_PROGRESS, DONE)
  - `created_at`: datetime (UTC, immutable after creation)
  - `updated_at`: datetime (UTC, mutable on status changes)
  - `due_date`: Optional[datetime] (UTC, nullable)
- **Methods**: `to_dict()`, `from_dict()`, status transition methods (mark_in_progress, mark_done, reopen), predicate methods (is_completed, is_pending, is_in_progress, is_overdue)

#### TaskStatus Enum (`src/models/task_status.py`)
- Values: PENDING, IN_PROGRESS, DONE
- Used exclusively for task status tracking

### 2. Storage Layer (`src/storage/`)

#### JsonStorage Class (`src/storage/json_storage.py`)
- **Methods**:
  - `load()`: Returns `list[dict]` from JSON file
  - `save(tasks: list[dict])`: Writes list of dicts to JSON file
- **Implementation**: Default path is `~/.todo_data.json`; supports custom paths
- **Structure**: Stores raw list of dictionaries; does NOT know about Task/TaskComment classes

### 3. Service Layer (`src/services/`)

#### TaskManager Class (`src/services/task_manager.py`)
- **Responsibilities**: CRUD operations on tasks, persistence coordination
- **Methods**:
  - `add()`: Creates task, stores in `_tasks` dict, calls `_persist()`
  - `get()`: Returns task by full or prefix ID; raises `TaskNotFoundError` if missing
  - `list_all()`, `list_by_status()`: Return task lists
  - `update()`: Modifies task fields, calls `_persist()`
  - `set_status()`: Updates status, calls `_persist()`
  - `delete()`: Removes task, calls `_persist()`
  - `_load()`: Reconstructs `Task` objects from storage
  - `_persist()`: Converts `Task` objects to dicts and saves to storage
- **In-Memory Structure**: `_tasks: dict[str, Task]` — maps task ID to Task object

#### TodoService Class (`src/services/todo_service.py`)
- **Responsibilities**: Validation layer above TaskManager
- **Methods**: Wrapper methods that validate inputs (e.g., non-empty title, ISO 8601 date format) and delegate to `TaskManager`
- **Validation patterns**: String trimming, format validation, raises `ValueError` for invalid inputs

### 4. CLI Layer (`src/cli/`)

#### TodoCLI Class (`src/cli/todo_cli.py`)
- One-shot command interface with argument parsing
- Commands: add, list, show, start, done, reopen, update, delete

#### InteractiveMenu Class (`src/cli/interactive_menu.py`)
- Full-screen terminal menu for interactive task management
- Prompts for user input, displays lists, handles status changes

---

## What Needs to Be Added: TaskComment Model

### New Class: TaskComment (`src/models/task_comment.py`)

**Acceptance Criteria Breakdown**:
1. **Has attributes**:
   - `id`: UUID (auto-generated, required)
   - `task_id`: str (required, must reference valid task)
   - `content`: str (required, non-empty)
   - `created_at`: datetime (CEST/UTC timezone-aware, immutable)
   - `author`: str (optional)
   - `updated_at`: datetime (optional, for consistency with Task model)

2. **Serialization**:
   - `to_dict()` → JSON-compatible dictionary
   - `from_dict(data: dict)` → TaskComment class method

3. **Validation**:
   - Empty content must be rejected (at model or service level)
   - Must validate task_id references a valid task (at service level, not model level)

4. **Out of Scope**:
   - Rich text rendering
   - Markdown support
   - Nested/threaded comments
   - Author identification mechanism (just store string)

### Implementation Approach

#### Option A: Comments stored with Task (nested)
- Task.comments: list[TaskComment]
- Pros: Everything in one JSON object
- Cons: Modifies Task structure, requires deep serialization/deserialization, updating task also rewrites all comments

#### Option B: Comments stored separately (flat)
- Storage stores both tasks and comments in the same JSON file (two arrays)
- Pros: Clean separation, TaskManager owns task list, CommentManager owns comment list
- Cons: Two arrays to manage in JSON, consistency checking

#### Option C: Comments stored separately in separate file
- Comments in `~/.todo_comments.json`
- Pros: Clear separation of concerns
- Cons: Two files to manage, sync complexity

**Recommended**: **Option A (nested in Task)** — simplest for ACID consistency, matches typical TODO app pattern where comments are task-scoped. Matches task serialization pattern exactly.

---

## Classes and Files to Create

### New Files

1. **`src/models/task_comment.py`** — TaskComment dataclass
   - **Attributes**: id, task_id, content, created_at, author (optional), updated_at (optional)
   - **Methods**: `to_dict()`, `from_dict()`
   - **Validation**: Content non-empty check (if at model level), or defer to service
   - **Imports**: uuid, dataclass, datetime, timezone, Optional

2. **`src/services/comment_manager.py`** (optional at this stage)
   - If comments are managed separately from tasks, will need CommentManager
   - For now, keep comments nested in Task; CommentManager can be added in future task

3. **`tests/test_task_comment.py`** — Comprehensive tests
   - Test instantiation with required/optional fields
   - Test serialization roundtrip (to_dict → from_dict)
   - Test empty content rejection
   - Test auto-generated id and created_at
   - Test optional author and updated_at fields

---

## Classes and Files to Modify

### 1. Task Model (`src/models/task.py`)

**Changes**:
- Add field: `comments: list[TaskComment] = field(default_factory=list)`
- Update `to_dict()` to include comments: `"comments": [c.to_dict() for c in self.comments]`
- Update `from_dict()` to deserialize comments:
  ```python
  comments=[TaskComment.from_dict(c) for c in data.get("comments", [])]
  ```
- Add method: `add_comment(content: str, author: Optional[str] = None) -> TaskComment`
  - Creates new TaskComment with task_id=self.id
  - Appends to self.comments
  - Returns the created comment
- Add method: `get_comment(comment_id: str) -> TaskComment` (optional, for navigation)
- Update `__init__` to accept comments parameter (or use field default)

**Impact on Existing Tests**:
- Existing tests should continue to pass (comments default to empty list)
- May need minor adjustments if deserialization fails on missing comments field

### 2. Models Init (`src/models/__init__.py`)

**Changes**:
- Export TaskComment: `from .task_comment import TaskComment`
- Add to `__all__`: `"TaskComment"`

### 3. TaskManager Service (`src/services/task_manager.py`)

**Changes** (to support comment operations):
- No structural changes needed if comments are nested in Task
- Task creation and persistence already handles nested objects via `to_dict()/from_dict()`
- If task is updated via TaskManager.update(), comment list is preserved (not overwritten)
- **Verify**: `update()` method only updates specified fields; comment list should be untouched

**No changes needed** if comments are nested in Task and only accessed via Task.add_comment().

### 4. TodoService (`src/services/todo_service.py`)

**New Methods**:
- `add_comment(task_id: str, content: str, author: Optional[str] = None) -> TaskComment`
  - Validates task exists: `self._manager.get(task_id)`
  - Validates content non-empty: `if not content or not content.strip(): raise ValueError(...)`
  - Delegates to `task.add_comment(content.strip(), author)`
  - Calls `self._manager._persist()` to save updated task
  - Returns the created TaskComment
- `get_task_comments(task_id: str) -> list[TaskComment]`
  - Returns `self._manager.get(task_id).comments`
- `delete_comment(task_id: str, comment_id: str) -> None` (optional, not in acceptance criteria but useful)
  - Finds comment in task.comments and removes it
  - Calls `self._manager._persist()`

**Validation**:
- Empty content rejection
- task_id existence check

---

## Summary Table: What Needs to Be Done

| File | Type | Action | Details |
|---|---|---|---|
| `src/models/task_comment.py` | New | Create | TaskComment dataclass with id, task_id, content, created_at, author, updated_at |
| `src/models/task.py` | Modify | Update | Add comments field, update to_dict/from_dict, add add_comment() method |
| `src/models/__init__.py` | Modify | Update | Export TaskComment |
| `src/services/todo_service.py` | Modify | Extend | Add add_comment(), get_task_comments(), optionally delete_comment() |
| `tests/test_task_comment.py` | New | Create | Test TaskComment serialization, validation, auto-generated fields |
| `tests/test_task.py` | Modify | Extend | Add tests for Task.add_comment(), comments persistence in roundtrip |
| `tests/test_todo_service.py` | Modify | Extend | Add tests for TodoService.add_comment() with validation |
| `artifacts/class_diagram.puml` | Modify | Update | Add TaskComment class, show relationship to Task |

---

## Key Design Decisions and Constraints

### 1. Comment Storage Location

**Decision**: Comments are **nested within Task** in the serialized JSON.

**Rationale**:
- Task comment is a semantic child of Task (comments belong to a task)
- Simplifies persistence (one JSON array per file)
- Aligns with typical TODO app architecture
- Easier transaction semantics (update Task → all comments included)

**Alternative Rejected**: Separate comment storage would require two-phase deletion (delete comments first, then task), higher complexity.

### 2. task_id Validation

**Decision**: `task_id` is stored as a string and validated at **service layer** (TodoService), not at model level.

**Rationale**:
- Model layer should not depend on external state (TaskManager)
- Validation at service layer allows reuse in multiple contexts
- Enables testing of TaskComment without TaskManager
- Storage/deserialization doesn't need to know about task existence

**Implementation**:
- TaskComment.from_dict() accepts any task_id (no validation)
- TodoService.add_comment() validates task_id exists before creating comment

### 3. Empty Content Validation

**Decision**: Empty content rejection happens at **service layer** (TodoService.add_comment()).

**Rationale**:
- Consistent with TodoService's validation pattern (see TodoService.add_task())
- Allows model layer to be logic-agnostic
- But: Consider adding at model level too for defense-in-depth (check in __post_init__)

**Implementation**:
```python
# In TodoService.add_comment()
if not content or not content.strip():
    raise ValueError("Comment content cannot be empty")
```

### 4. Optional Fields

**Decision**: `author` and `updated_at` are optional.

**Rationale**:
- `author`: Requirement says "optional"
- `updated_at`: Requirement says "optional for consistency with Task model"
- Default: author=None, updated_at=None (or omit from dict if not set)

**Serialization Impact**:
- to_dict() includes fields even if None: `"author": None, "updated_at": None`
- from_dict() handles both presence and absence gracefully

### 5. Timezone Representation

**Decision**: Dates stored as UTC (consistent with Task model), displayed/described as CEST.

**Rationale**:
- Maintains consistency with existing Task.created_at/updated_at behavior
- Storage is ISO 8601 via .isoformat()
- UI layer converts to CEST for display (like InteractiveMenu does)

---

## Acceptance Criteria Checklist

- [ ] TaskComment has id (UUID, auto-generated)
- [ ] TaskComment has task_id (required, string)
- [ ] TaskComment has content (required, non-empty)
- [ ] TaskComment has created_at (datetime, UTC timezone-aware)
- [ ] TaskComment has optional author attribute
- [ ] TaskComment has optional updated_at attribute (for consistency)
- [ ] TaskComment serializes to JSON-compatible dict via to_dict()
- [ ] TaskComment deserializes from dict via from_dict()
- [ ] Empty content is rejected (service layer validation)
- [ ] task_id validation references valid task (service layer validation)
- [ ] Rich text, markdown, nested comments are out of scope

---

## Test Coverage Strategy

### Unit Tests for TaskComment (`tests/test_task_comment.py`)

1. **Instantiation**:
   - Create with all fields
   - Create with minimal fields (content, task_id)
   - Verify id is auto-generated
   - Verify created_at is set to current time

2. **Serialization**:
   - to_dict() with all fields populated
   - to_dict() with None fields (author, updated_at)
   - from_dict() roundtrip preserves all fields
   - from_dict() handles missing optional fields

3. **Validation** (at model level, if applicable):
   - from_dict() accepts any task_id (no validation)
   - from_dict() accepts empty strings if provided (validation is service layer)

### Integration Tests for Task (`tests/test_task.py`)

1. Task.comments default to empty list
2. Task.add_comment() creates and appends TaskComment
3. Task.to_dict() includes comments array
4. Task.from_dict() reconstructs comments
5. Roundtrip: Task with comments → to_dict() → from_dict() preserves comments

### Integration Tests for TodoService (`tests/test_todo_service.py`)

1. TodoService.add_comment() validates content non-empty
2. TodoService.add_comment() validates task_id exists
3. TodoService.add_comment() creates TaskComment and persists
4. TodoService.get_task_comments() returns all comments for task
5. Comment appears in task after persistence/reload

---

## Dependencies and Imports

### TaskComment (`src/models/task_comment.py`)

```python
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
```

### Task (`src/models/task.py`)

**Add**:
```python
from .task_comment import TaskComment
```

**Field Addition**:
```python
comments: list[TaskComment] = field(default_factory=list)
```

### No New External Dependencies

- All needed imports are in Python standard library
- dataclass, uuid, datetime already imported
- No new packages required

---

## File Paths (Absolute)

**Files to Create**:
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/models/task_comment.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/tests/test_task_comment.py`

**Files to Modify**:
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/models/task.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/models/__init__.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/services/todo_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/tests/test_task.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/tests/test_todo_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/artifacts/class_diagram.puml`

---

## Potential Edge Cases and Constraints

1. **Circular Dependency**: TaskComment references task_id (string), Task contains list[TaskComment]. No circular import risk because task_id is string, not Task object.

2. **Backward Compatibility**: Existing tasks without comments field must load gracefully.
   - Task.from_dict() should use `data.get("comments", [])` to default to empty list.

3. **Persistence Atomicity**: When task is updated, all comments are written with it. Comments cannot be updated independently (in this task scope).

4. **Comment ID Uniqueness**: IDs are UUIDs, globally unique (no task-scoped ID needed). No need for TaskComment ID validation at model level.

5. **Deleted Tasks**: If task is deleted, all comments are deleted with it (by design). No orphaned comments.

6. **Empty Author**: author=None is valid; don't enforce non-empty author string.

---

## Summary

**Feature**: Add TaskComment model with serialization, storage integration, and service-layer operations.

**New Components**:
- TaskComment dataclass with id, task_id, content, created_at, author (optional), updated_at (optional)
- Task integration: comments list, add_comment() method, updated to_dict()/from_dict()
- TodoService methods: add_comment(), get_task_comments()
- Comprehensive tests covering serialization, validation, and integration

**Scope Limits**:
- No UI (CLI commands not in this task)
- No nested comments
- No markdown or rich text
- No author authentication (just store string)

**Test Coverage**: ~30 new tests covering TaskComment unit tests, Task integration tests, and TodoService validation tests.
