# CommentsService Implementation Design Plan

## Overview

Implement a dedicated `CommentsService` class that centralizes all comment lifecycle management (add, list, delete, and edit). The service will follow the existing architectural patterns used by `TodoService` and `TaskManager`, maintain backward compatibility with existing tests, and ensure comments cascade delete when their parent task is deleted.

---

## 1. Class Structure & Interface

### CommentsService Class Signature

```python
class CommentsService:
    """Service for managing task comments.
    
    Centralizes all comment lifecycle operations: create, retrieve, update, and delete.
    Depends on TaskManager for task validation and persistence.
    Comments are stored as nested objects within Task entities.
    """
    
    def __init__(self, task_manager: TaskManager) -> None:
        """Initialize CommentsService with a TaskManager instance.
        
        Args:
            task_manager: TaskManager instance for task access and persistence
        """
```

### Methods

#### add_comment(task_id: str, content: str, author: Optional[str] = None) -> TaskComment

- Strip and validate content (non-empty after strip)
- Lookup task via task_manager.get(task_id) — raises TaskNotFoundError if not found
- Create TaskComment with auto-generated UUID and UTC created_at
- Append to task.comments list
- Call task_manager._persist()
- Return created TaskComment

**Errors**: ValueError (empty content), TaskNotFoundError (task not found)

#### list_comments(task_id: str) -> list[TaskComment]

- Lookup task via task_manager.get(task_id) — raises TaskNotFoundError if not found
- Return task.comments (already ordered by creation)

**Errors**: TaskNotFoundError (task not found)

#### delete_comment(task_id: str, comment_id: str) -> None

- Lookup task via task_manager.get(task_id)
- Search task.comments for comment by id
- If found: remove from list and call task_manager._persist()
- If not found: raise ValueError

**Errors**: TaskNotFoundError (task not found), ValueError (comment not found)

#### edit_comment(task_id: str, comment_id: str, new_content: str) -> TaskComment

- Strip and validate new_content (non-empty after strip)
- Lookup task via task_manager.get(task_id)
- Search task.comments for comment by id
- If found: update content, set updated_at to datetime.now(timezone.utc), call task_manager._persist(), return updated comment
- If not found: raise ValueError

**Errors**: ValueError (empty content, comment not found), TaskNotFoundError (task not found)

---

## 2. Integration Points

**CommentsService ← TaskManager**:
- Uses task_manager.get(task_id) for task validation and ID resolution
- Uses task_manager._persist() to persist mutations
- Directly accesses and mutates task.comments list

**Task ← CommentsService**:
- Mutates task.comments list (append, pop, in-place edit)
- Does NOT call Task.add_comment() method
- Task model unchanged

**TodoService ← CommentsService**:
- Both are independent service classes
- TodoService methods remain unchanged (backward compatibility)
- No refactoring of TodoService in this task

---

## 3. Cascade Delete Behavior

Cascade delete is **implicit** — no explicit code needed:
1. When TaskManager.delete(task_id) called, task removed from _tasks dict
2. _persist() serializes remaining tasks only
3. Comments automatically deleted because they're nested in task
4. No orphaned comment records in storage

**Verification**: Task deletion removes entire task dict including comments array

---

## 4. Files to Create/Modify

**NEW**:
- `src/services/comments_service.py` — CommentsService implementation

**NEW**:
- `tests/test_comments_service.py` — Comprehensive test suite (27 tests)

**MODIFY**:
- `src/services/__init__.py` — Export CommentsService

**OPTIONAL**:
- `artifacts/class_diagram.puml` — Add CommentsService diagram

---

## 5. Test Structure

**Fixture**:
```python
@pytest.fixture
def comments_service(tmp_path):
    storage = JsonStorage(str(tmp_path / "tasks.json"))
    manager = TaskManager(storage)
    return CommentsService(manager)
```

**Tests**:
- add_comment: 8 tests (validation, persistence, error cases)
- list_comments: 4 tests (retrieval, empty, order, error cases)
- delete_comment: 5 tests (removal, persistence, error cases)
- edit_comment: 8 tests (update, timestamp, validation, error cases)
- cascade delete: 2 tests (implicit behavior verification)

Total: 27 tests

---

## 6. Implementation Sequence

1. **Phase 1**: Create CommentsService class skeleton with docstrings
2. **Phase 2**: Implement add_comment, list_comments, delete_comment, edit_comment in order
3. **Phase 3**: Update src/services/__init__.py exports
4. **Phase 4**: Write all 27 tests in test_comments_service.py
5. **Phase 5**: Verify existing tests still pass (backward compatibility)
6. **Phase 6**: Update diagrams (optional)

---

## 7. Key Implementation Patterns

**Validation**: Check content non-empty, strip whitespace, raise ValueError if invalid

**Task Lookup**: Use task_manager.get(task_id) — handles prefix matching, raises TaskNotFoundError

**Append & Persist**: 
```python
task.comments.append(comment)
self._task_manager._persist()
```

**Search & Modify**:
```python
for i, c in enumerate(task.comments):
    if c.id == comment_id:
        task.comments.pop(i)
        self._task_manager._persist()
        return
raise ValueError(...)
```

**Timestamps**: Use `datetime.now(timezone.utc)` for created_at and updated_at

---

## 8. Assumptions

- Comment IDs are full UUIDs (no prefix lookup)
- Cascade delete is implicit (no explicit code needed)
- TaskManager.get() is the canonical task lookup method
- Direct mutation of task.comments is safe for single-threaded CLI use
- TodoService methods remain unchanged (backward compatibility)

---

## Scope: What This Task Includes

✓ CommentsService class with all 4 methods  
✓ Integration with TaskManager  
✓ Cascade delete (implicit, verify it works)  
✓ Comprehensive test coverage  
✓ Error handling (ValueError, TaskNotFoundError)  

✗ Refactoring TodoService (out of scope, separate task)  
✗ Separate comment storage (out of scope)  
✗ Comment ID prefix lookup (out of scope)
