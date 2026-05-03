# Analysis: CommentsService Implementation

**Task:** Implement a CommentsService that manages the full lifecycle of TaskComment objects.

**Date:** 2026-05-03

---

## Executive Summary

The TaskComment model, data structures, and persistence layer **already exist and are fully implemented**. The primary gap is the absence of a dedicated **CommentsService** class to provide a cohesive, high-level API for comment operations. Currently, comment logic is split between TaskManager (business logic) and TodoService (validation/passthrough). CLI integration for comments is also **missing entirely** — no interactive menu options or CLI flags expose comment operations.

The task requires:
1. Creating a new `CommentsService` class in `src/services/`
2. Adding interactive menu options for add/list/delete comments
3. Adding CLI subcommands for add/list/delete comments
4. Updating `__main__.py` to wire the new service and entry points

---

## Current State Analysis

### 1. Data Model: TaskComment (Complete)

**File:** `src/models/task_comment.py`

```python
@dataclass
class TaskComment:
    content: str
    task_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
```

**Status:** Fully implemented with:
- UUID auto-generation for `id`
- Timezone-aware `created_at` (UTC)
- Optional `author` field
- Optional `updated_at` for edit tracking
- `__post_init__()` validates non-empty content (raises ValueError if empty/whitespace-only)
- `to_dict()` and `from_dict()` serialization methods

**Task Model Integration:** The Task model already has:
- `comments: list[TaskComment]` field (line 21 in task.py)
- Serialization support: `to_dict()` includes comments (line 134), `from_dict()` deserializes comments (lines 141-142)

### 2. Storage Layer: JsonStorage (Complete)

**File:** `src/storage/json_storage.py`

- Handles persistence of task data (which includes comments as nested objects)
- Comments cascade-delete when a task is deleted (because Task.to_dict() only serializes existing comment list)
- No schema changes needed — comments are already in the JSON payload

**Current behavior verified by tests:** `test_task_comment.py` lines 699-705 confirm that deleting a task deletes its associated comments.

### 3. TaskManager Service (Partial)

**File:** `src/services/task_manager.py`, lines 89-141

Implements three comment methods directly:

```python
def add_comment(task_id: str, content: str, author: Optional[str] = None) -> TaskComment
def get_comments(task_id: str) -> list[TaskComment]
def delete_comment(task_id: str, comment_id: str) -> None
```

**Status:**
- All methods work correctly
- They validate inputs and handle errors appropriately (e.g., TaskNotFoundError, ValueError)
- They persist changes via `_persist()`
- **Missing feature:** `get_comments()` does NOT order by created_at (acceptance criterion requirement)
- **Missing feature:** No edit_comment() method (acceptance criterion bonus feature)

### 4. TodoService (Partial)

**File:** `src/services/todo_service.py`, lines 54-98

Delegates to TaskManager with validation:

```python
def add_comment(task_id: str, content: str, author: Optional[str] = None) -> TaskComment
def get_comments(task_id: str) -> list[TaskComment]
def delete_comment(task_id: str, comment_id: str) -> None
```

**Status:**
- Validates empty content (strips whitespace before delegating)
- Correctly propagates TaskNotFoundError
- Same gaps as TaskManager regarding ordering and edit support

### 5. CLI Layer (Non-existent for Comments)

**File:** `src/cli/todo_cli.py`

**Status:** No comment subcommands exist. Parser covers:
- add, list, show, start, done, reopen, update, delete, due-date

**Missing:** add-comment, list-comments, delete-comment (and possibly edit-comment)

### 6. Interactive Menu (Non-existent for Comments)

**File:** `src/cli/interactive_menu.py`

**Status:** Main menu (line 104-112) has no comment options.

**Missing:** Interactive submenu options for comment add/view/delete

### 7. Tests (Comprehensive for Model/Manager/Service)

**File:** `tests/test_task_comment.py`

**Status:** Very comprehensive — 150+ lines covering:
- TaskComment model creation, validation, serialization
- TaskManager.add_comment(), get_comments(), delete_comment()
- TodoService equivalents
- Integration tests including cascade delete
- BUT does NOT test for:
  - `get_comments()` ordering by created_at
  - CLI commands for comments (no test_todo_cli.py comment tests exist)
  - Interactive menu comment operations

---

## Acceptance Criteria Deep Dive

### Core Requirements

1. **add_comment(task_id, content, author)** ✓ Exists
   - Validates task exists ✓
   - Integrates with storage ✓
   - Creates TaskComment object ✓
   - **Gap:** No dedicated CommentsService

2. **list_comments(task_id)** ⚠️ Exists but **NOT ordered by created_at**
   - Current: Returns `task.comments` in append order (which happens to be creation order if no mutations)
   - Required: MUST order by `created_at`
   - **Fix needed in both TaskManager.get_comments() and CommentsService**

3. **delete_comment(task_id, comment_id)** ✓ Exists
   - Works correctly ✓
   - Persists deletion ✓

4. **Task existence validation** ✓ Exists
   - Both TaskManager and TodoService call `get(task_id)` which raises TaskNotFoundError

5. **Storage integration** ✓ Exists
   - Comments stored as part of Task JSON structure ✓
   - No separate storage layer needed ✓

6. **Cascade delete on task deletion** ✓ Exists
   - Verified by test line 699-705
   - When task deleted, its comment list is discarded ✓

7. **Bonus: edit_comment()** ✗ Missing
   - Should update `content` and `updated_at`
   - Needs TaskComment mutation method or direct field access

8. **CLI/Menu accessibility** ✗ Missing
   - No interactive menu options
   - No CLI subcommands
   - Must add both (per Runtime & CLI Exposure Requirements)

---

## What Needs to Be Created/Modified

### 1. New File: `src/services/comments_service.py`

**Purpose:** Centralized API for comment operations

**Responsibilities:**
- CRUD operations on comments
- Input validation (delegate to models where possible)
- Error handling (propagate TaskNotFoundError, ValueError)
- Ordering of results (list_comments must return sorted by created_at)
- Persist changes (delegate to storage via TaskManager)

**Methods to implement:**
- `add_comment(task_id: str, content: str, author: Optional[str] = None) -> TaskComment`
- `list_comments(task_id: str) -> list[TaskComment]` (sorted by created_at)
- `delete_comment(task_id: str, comment_id: str) -> None`
- `edit_comment(task_id: str, comment_id: str, content: str) -> TaskComment` (bonus)

**Dependencies:**
- Receive `TodoService` as constructor argument (to access task_manager)
- OR receive `TaskManager` directly

**Pattern to follow:**
- TodoService wraps TaskManager for high-level business logic
- CommentsService could wrap TaskManager OR be a sibling service
- **Design decision needed:** Should CommentsService be:
  - Option A: Instantiated inside TodoService (composition)?
  - Option B: Independent service accepting TaskManager in constructor?
  - Option C: Static methods/module-level functions?
  - **Assumption:** Following TodoService pattern, CommentsService receives TaskManager

### 2. Modify: `src/services/task_manager.py`

**Changes needed:**
- Fix `get_comments()` to sort by created_at (line 110-123)
- Add `edit_comment()` method for bonus feature

**Current code (line 110-123):**
```python
def get_comments(self, task_id: str) -> list[TaskComment]:
    task = self.get(task_id)
    return task.comments  # Currently unsorted
```

**Required fix:**
```python
def get_comments(self, task_id: str) -> list[TaskComment]:
    task = self.get(task_id)
    return sorted(task.comments, key=lambda c: c.created_at)
```

### 3. Modify: `src/services/todo_service.py`

**Changes needed:**
- Optionally: wrap/delegate to CommentsService instead of directly to TaskManager
- OR: Update existing methods to use TaskManager's fixed `get_comments()` with sorting
- Minimum change: Ensure consistency

**Current behavior:** Already valid, just needs TaskManager.get_comments() fix to cascade up

### 4. Modify: `src/cli/todo_cli.py`

**Add subcommands:**
```
add-comment TASK_ID CONTENT [--author AUTHOR]
list-comments TASK_ID
delete-comment TASK_ID COMMENT_ID
edit-comment TASK_ID COMMENT_ID CONTENT  (bonus)
```

**Patterns to follow:**
- Use existing command structure (add, list, show, start, done, reopen, update, delete, due-date)
- Follow argparse pattern already established
- Print user-friendly output with status symbols (e.g., "Added comment to task abc123")

### 5. Modify: `src/cli/interactive_menu.py`

**Add menu items in _print_main_menu():**
```
8. Manage comments  (add/view/edit/delete)
```

**Add new method (following _do_* pattern):**
- `_do_comment_menu()` — submenu for add/list/delete/edit comment operations
- Reuses existing `_pick()`, `_prompt()` helpers
- Shows comment list with IDs and content previews

**Integration points:**
- Call CommentsService or TodoService comment methods
- Update task selection flow to allow navigating to comments after viewing task

### 6. Modify: `src/__main__.py`

**Current (lines 1-20):**
```python
def main() -> None:
    if len(sys.argv) > 1:
        sys.exit(TodoCLI().run())
    menu = InteractiveMenu()
    try:
        menu.run()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
```

**Status:** No changes needed
- TodoCLI and InteractiveMenu already instantiated
- They will be updated to support comments internally
- Entry point remains the same

### 7. Update: `src/services/__init__.py`

**Current (lines 1-4):**
```python
from .task_manager import TaskManager, TaskNotFoundError
from .todo_service import TodoService

__all__ = ["TaskManager", "TaskNotFoundError", "TodoService"]
```

**Change:**
```python
from .task_manager import TaskManager, TaskNotFoundError
from .todo_service import TodoService
from .comments_service import CommentsService

__all__ = ["TaskManager", "TaskNotFoundError", "TodoService", "CommentsService"]
```

---

## Testing Implications

### New Tests Needed

**File:** `tests/test_comments_service.py` (new)
- CommentsService instantiation
- add_comment() with/without author
- list_comments() returns sorted by created_at
- delete_comment() removes comment
- Error handling (TaskNotFoundError, ValueError)

**File:** `tests/test_todo_cli.py` (additions)
- `add-comment` subcommand
- `list-comments` subcommand
- `delete-comment` subcommand
- `edit-comment` subcommand (if implemented)
- Error output on invalid task/comment IDs

**File:** `tests/test_task_manager.py` (additions)
- Verify `get_comments()` returns sorted list

### Existing Tests

- `tests/test_task_comment.py` — All pass as-is (no changes to TaskComment model)
- `tests/test_task.py` — No changes needed
- `tests/test_task_manager.py` — Need to add sort verification for get_comments()
- `tests/test_todo_service.py` — May need to verify ordering behavior

---

## Data Structure: JSON Serialization

Comments are stored **nested inside each Task** in the JSON file:

```json
[
  {
    "id": "uuid-for-task",
    "title": "Task title",
    "description": "...",
    "status": "pending",
    "created_at": "2026-05-03T...",
    "updated_at": "2026-05-03T...",
    "due_date": null,
    "comments": [
      {
        "id": "uuid-for-comment",
        "task_id": "uuid-for-task",
        "content": "Comment text",
        "author": "John",
        "created_at": "2026-05-03T...",
        "updated_at": null
      }
    ]
  }
]
```

**Key points:**
- Comments are **not a separate root-level array** — they're embedded in each Task
- `task_id` in comment redundantly stores the parent task ID (for integrity)
- Cascade delete happens naturally: when a task is deleted, its comments array is discarded
- Sorting comments by `created_at` happens in-memory after load (no database index needed)

---

## Architecture Layers

### Current Stack

```
Entry Point (__main__.py)
    ↓
CLI Layer (TodoCLI, InteractiveMenu)
    ↓
Service Layer (TodoService, TaskManager)
    ↓
Model Layer (Task, TaskStatus, TaskComment)
    ↓
Storage Layer (JsonStorage)
    ↓
File System (todo_data.json)
```

### After CommentsService

```
Entry Point (__main__.py)
    ↓
CLI Layer (TodoCLI, InteractiveMenu)  ← Add comment subcommands and menu options
    ↓
Service Layer (TodoService, TaskManager, CommentsService)  ← NEW SERVICE
    ↓
Model Layer (Task, TaskStatus, TaskComment)
    ↓
Storage Layer (JsonStorage)
    ↓
File System (todo_data.json)
```

**CommentsService positioning:**
- Sits alongside TodoService (not nested inside it)
- Uses TaskManager as dependency (same as TodoService does)
- Provides high-level comment API to CLI layer
- Handles business logic (validation, error handling, ordering)

---

## Ambiguities & Assumptions

### 1. CommentsService Constructor Signature

**Unclear:** Should CommentsService accept StoragePath, TodoService, or TaskManager?

**Assumption:** Following TodoService pattern:
```python
def __init__(self, storage: Optional[JsonStorage] = None):
    self._manager = TaskManager(storage)
```

OR simpler, receive TaskManager:
```python
def __init__(self, manager: TaskManager):
    self._manager = manager
```

**Design decision deferred to System Architect.** Either works; second is cleaner.

### 2. Ordering Implementation

**Requirement:** "ordered by created_at"

**Assumption:** Ascending order (oldest comments first). This is standard for discussion threads.

**Alternative:** Descending (newest first, like Twitter). **System Architect to confirm.**

### 3. Edit Comment Implementation

**Requirement (bonus):** "Editing a comment's content (with updated_at updated)"

**Ambiguity:** How should edit be exposed?
- Option A: `CommentsService.edit_comment(task_id, comment_id, new_content) -> TaskComment`
- Option B: Modify TaskComment in-place: `comment.content = "..."; comment.updated_at = now()`
- Option C: CLI-only (not in service layer)

**Assumption:** Option A (full service-layer support), similar to add/delete pattern.

### 4. Author Field Handling

**Current:** `author: Optional[str]` in TaskComment

**Ambiguity:** Should CLI/menu auto-populate author from environment (e.g., git user)? Or always require explicit --author flag?

**Assumption:** Always optional, default to None (no auto-detection).

### 5. Comment ID Display in Menu

**Ambiguity:** Comments have 36-char UUIDs. Should menu show full ID or prefix?

**Assumption:** Show first 8 chars like tasks do (for consistency).

---

## Scope Boundaries

### In Scope

- [x] Create CommentsService class
- [x] Add list_comments() with created_at ordering
- [x] Add add_comment() with validation
- [x] Add delete_comment() with error handling
- [x] Bonus: edit_comment() with updated_at tracking
- [x] CLI subcommands: add-comment, list-comments, delete-comment, (edit-comment)
- [x] Interactive menu: comment management submenu
- [x] Tests for CommentsService
- [x] Update task_manager.get_comments() to sort by created_at

### Out of Scope

- [ ] Comment threading/replies (flat list only)
- [ ] Comment permissions/roles (no author verification)
- [ ] Comment search or filtering
- [ ] Rich text/markdown in comments
- [ ] File attachments to comments
- [ ] Comment notifications
- [ ] Comment history/audit trail (beyond updated_at)
- [ ] Separate comment storage table
- [ ] Comment pagination (load all for a task)

---

## Files to Modify/Create

| File | Action | Reason |
|------|--------|--------|
| `src/services/comments_service.py` | **CREATE** | New service class |
| `src/services/task_manager.py` | **MODIFY** | Fix get_comments() sorting, add edit_comment() |
| `src/services/todo_service.py` | **MODIFY** | Option: delegate to CommentsService (or leave as-is) |
| `src/services/__init__.py` | **MODIFY** | Export CommentsService |
| `src/cli/todo_cli.py` | **MODIFY** | Add comment subcommands |
| `src/cli/interactive_menu.py` | **MODIFY** | Add comment menu options |
| `tests/test_comments_service.py` | **CREATE** | Test new service |
| `tests/test_task_manager.py` | **MODIFY** | Add sort verification |
| `tests/test_todo_cli.py` | **MODIFY** | Test CLI comment commands |
| `artifacts/class_diagram.puml` | **MODIFY** | Show CommentsService |
| `artifacts/component_diagram.puml` | **MODIFY** | Show CommentsService in stack |
| `artifacts/use_case_diagram.puml` | **MODIFY** | Show comment use cases |

---

## Summary of Gaps

| Gap | Severity | Impact | Fix |
|-----|----------|--------|-----|
| No CommentsService class | HIGH | Acceptance criterion | Create new service |
| get_comments() not sorted by created_at | HIGH | Acceptance criterion | Fix in TaskManager, propagate to CommentsService |
| No CLI comment commands | HIGH | Acceptance criterion (must be accessible via `python -m src`) | Add subcommands to TodoCLI |
| No interactive menu for comments | HIGH | Acceptance criterion (menu option required) | Add comment submenu to InteractiveMenu |
| No edit_comment() | MEDIUM | Bonus feature | Implement in TaskManager and CommentsService |
| No tests for CommentsService | MEDIUM | Code quality | Write comprehensive tests |

---

## Implementation Order (for System Architect)

1. **Modify TaskManager** — Fix get_comments() sorting, add edit_comment()
2. **Create CommentsService** — Wrap TaskManager with high-level API
3. **Update TodoService** — Optional: delegate to CommentsService
4. **Add CLI subcommands** — add-comment, list-comments, delete-comment, (edit-comment)
5. **Add menu options** — Interactive comment submenu
6. **Write tests** — CommentsService, CLI, and sorting verification
7. **Update diagrams** — Reflect CommentsService in architecture

---

## Key Insights

1. **Infrastructure exists:** All data structures and persistence mechanisms are already in place. This is primarily a **service abstraction + CLI exposure task.**

2. **Cascade delete works:** When a task is deleted, its comments are automatically discarded (no orphans).

3. **Sorting is the main fix:** Most acceptance criteria are met; the key missing piece is ordering list_comments() by created_at.

4. **CLI is the blocker:** Without CLI/menu wiring, the feature is incomplete per Runtime Requirements. "All new functionality must be accessible via python -m src (both as interactive menu option and CLI flag)."

5. **Tests are comprehensive:** Existing test coverage for TaskComment, TaskManager, and TodoService is thorough. New tests should focus on CommentsService and CLI integration.
