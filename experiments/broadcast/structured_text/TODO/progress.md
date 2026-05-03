# Experiment Progress: Broadcast / Structured Text / TODO

## Task 01: Add due date to tasks

### Broadcast Fan-out Results

Three independent implementations were created on separate branches:

| Candidate | Approach | Test Results | Notes |
|-----------|----------|--------------|-------|
| **A** | Full-stack: Model + Services + CLI | 41/41 ✓ | Added --due-date CLI args, service layer support, overdue display |
| **B** | Full-stack: Model + Services + CLI | 41/41 ✓ | **Selected** - Robust validation, error handling, ISO 8601 format |
| **C** | Model-only | 41/41 ✓ | Minimal approach, no service/CLI extensions |

### Selected Solution: Implementer-B (broadcast-candidate-b)

**Rationale**: While all three solutions passed all 41 tests, Implementer-B provided the most complete implementation. According to CLAUDE.md, "All functionality must be reachable via `python -m src` — a feature is not complete until it has a CLI entry point." Implementer-B included:
- Full CLI support with `--due-date` arguments for `add` and `update` commands
- Service layer integration (TaskManager and TodoService)
- Robust validation and user-friendly error messages
- Overdue status display in the `show` command

### Files Changed

1. **src/models/task.py**
   - Added `due_date: Optional[datetime] = None` attribute
   - Added CEST timezone constant (UTC+2)
   - Updated `to_dict()` to serialize due_date in ISO 8601 format
   - Updated `from_dict()` with backward compatibility for legacy JSON
   - Added `is_overdue()` method

2. **src/services/task_manager.py**
   - Extended `add()` method to accept optional `due_date` parameter
   - Extended `update()` method to accept optional `due_date` parameter

3. **src/services/todo_service.py**
   - Extended `add_task()` method to accept optional `due_date` parameter
   - Extended `update_task()` method to accept optional `due_date` parameter

4. **src/cli/todo_cli.py**
   - Added `--due-date` argument to `add` command
   - Added `--due-date` argument to `update` command
   - Implemented ISO 8601 date parsing and validation
   - Display due date and overdue status in `show` command

### Requirements Compliance

**Must:**
- ✓ Add attribute `due_date: Optional[datetime]` to Task
- ✓ Allow tasks without a due date (None by default)
- ✓ Ensure due_date is stored and persisted through storage layer
- ✓ Update to_dict() and from_dict() accordingly
- ✓ Use CEST (UTC+2) timezone-aware datetime (ISO 8601)

**Should:**
- ✓ Preserve backward compatibility with stored JSON data
- ✓ Validate that provided due dates are valid datetime values

**Could:**
- ✓ Added `is_overdue()` predicate

**Won't:**
- ✗ External calendar integration (not required)

### Test Results

- Baseline tests: 41/41 passing ✓
- No test modifications were needed
- Full backward compatibility verified

Duration: 131.5s | Cost: $0.798627 USD | Turns: 28

## Task 03: Introduce TaskComment domain class

### Broadcast Fan-out Results

Three independent implementations were created on separate branches:

| Candidate | Approach | Test Results | Notes |
|-----------|----------|--------------|-------|
| **A** | TaskComment dataclass with validation, serialization, optional fields | 57/57 ✓ | **Selected** - Clean implementation with proper validation |
| **B** | TaskComment dataclass with validation, serialization, optional fields | 57/57 ✓ | Identical to A |
| **C** | TaskComment dataclass with validation, serialization, optional fields | 57/57 ✓ | Identical to A and B |

### Selected Solution: Implementer-A (broadcast-candidate-a)

**Rationale**: All three candidates produced identical implementations with all 57 tests passing. Implementer-A was selected arbitrarily as the winner. The implementation follows the established patterns from the Task model and includes all required and suggested features with comprehensive test coverage.

### Files Changed

1. **src/models/task_comment.py** (new file)
   - Created TaskComment dataclass with attributes: id (UUID), task_id (string reference), content (string), created_at (UTC datetime)
   - Added optional fields: author (string), updated_at (datetime)
   - Implemented `__post_init__()` validation: content and task_id must not be empty
   - Implemented `to_dict()` for JSON serialization with selective field inclusion
   - Implemented `from_dict()` classmethod for JSON deserialization with proper datetime parsing
   - Uses CEST timezone constant (UTC+2) from task.py

2. **src/models/__init__.py** (modified)
   - Added TaskComment to module exports for public API

3. **tests/test_task_comment.py** (new file)
   - 16 comprehensive tests covering:
     - Default construction and auto-generated IDs
     - Unique ID generation
     - Optional fields (author, updated_at)
     - Content validation (empty and whitespace)
     - Task ID validation (empty and whitespace)
     - Serialization with selective field inclusion
     - Deserialization with proper datetime parsing
     - Full roundtrip serialization/deserialization

4. **artifacts/class_diagram.puml** (modified)
   - Added TaskComment class to models package
   - Added relationship from TaskComment to Task (references via task_id)

### Requirements Compliance

**Must:**
- ✓ Create TaskComment class with id (UUID), task_id, content, created_at (CEST/UTC+2)
- ✓ Support JSON serialization via to_dict()
- ✓ Support JSON deserialization via from_dict()

**Should:**
- ✓ Validate content is not empty
- ✓ Validate task_id references a valid task (non-empty validation implemented)

**Could:**
- ✓ Added optional author attribute
- ✓ Added optional updated_at datetime attribute

**Won't:**
- ✗ Rich text, markdown rendering, or nested/threaded comments

### Test Results

- New tests: 16/16 passing ✓
- Total tests: 57/57 passing ✓ (41 existing + 16 new)
- No regressions in existing functionality
- Full test coverage of TaskComment functionality

Duration: 279.9s | Cost: $0.520896 USD | Turns: 42

## Task 04: Add CommentsService for managing TaskComments

### Broadcast Fan-out Results

Three independent implementations were created on separate branches:

| Candidate | Approach | Test Results | ID Resolution | Notes |
|-----------|----------|--------------|----------------|-------|
| **A** | Full CommentsService + CLI integration | 81/81 ✓ | Basic (no prefix resolution in cascade) | Comments stored with provided ID (may be prefix) |
| **B** | Full CommentsService + CLI integration | 81/81 ✓ | **Robust** (resolves prefix to UUID) | **Selected** - Correct prefix handling in all operations |
| **C** | Full CommentsService + CLI integration | 81/81 ✓ | Basic | Comments stored with provided ID |

### Selected Solution: Implementer-B (broadcast-candidate-b)

**Rationale**: While all three candidates passed 81 tests, Implementer-B demonstrated superior implementation quality through robust ID resolution. When a user provides a task ID prefix (e.g., "abc123ef"), Candidate-B correctly resolves it to the full UUID before storing/accessing comments in all operations (add, list, delete, cascade delete). This prevents potential bugs where cascade delete might fail to find comments if the task was deleted using a prefix. Candidates A and C lacked this safeguard, making them prone to leaving orphaned comments.

### Files Changed

1. **src/services/comments_service.py** (new file)
   - Created CommentsService class for managing TaskComment objects
   - Methods: add_comment(), list_comments_by_task(), get_comment(), delete_comment(), update_comment(), delete_comments_by_task()
   - Integrated with JsonStorage for persistence (stores comments in "comments" key)
   - Validates comment content (non-empty) and task_id (non-empty)
   - Supports prefix lookup for comment IDs (matching TaskManager pattern)

2. **src/services/todo_service.py** (modified)
   - Added comment management methods: add_comment(), list_comments(), get_comment(), delete_comment(), update_comment()
   - **Robust ID resolution**: All methods resolve task_id prefixes to full UUIDs before accessing/storing comments
   - Cascade delete in delete_task(): deletes all associated comments when a task is deleted
   - Task validation before adding comments

3. **src/services/task_manager.py** (modified)
   - Updated _load() and _persist() to handle new JSON structure with "comments" key
   - Maintains backward compatibility with legacy JSON format

4. **src/storage/json_storage.py** (modified)
   - Enhanced to support both list (legacy) and dict (tasks/comments) formats
   - Preserves comments when persisting tasks

5. **src/services/__init__.py** (modified)
   - Exported CommentsService and CommentNotFoundError

6. **src/cli/todo_cli.py** (modified)
   - Added three new subcommands: comment-add, comment-list, comment-delete, comment-update
   - Proper CLI argument parsing for comment operations
   - Exception handling for CommentNotFoundError

7. **src/cli/interactive_menu.py** (modified)
   - Added menu option 7: "Manage comments"
   - Implemented submenu: add comment, delete comment, edit comment, list comments
   - Interactive operations for comment management

8. **tests/test_comments_service.py** (new file)
   - 24 comprehensive tests covering:
     - Basic CRUD operations (add, get, list, delete, update)
     - Content validation (empty, whitespace)
     - List ordering by created_at ascending
     - Filtering by task_id
     - Persistence and reloading
     - Cascade delete functionality
     - Prefix lookup support
     - Update with timestamp management

### Requirements Compliance

**Must:**
- ✓ Implement CommentsService to manage TaskComment objects
- ✓ Add comment to task - add_comment(task_id, content, author)
- ✓ List comments by task (ordered by created_at) - list_comments_by_task(task_id)
- ✓ Delete comment by id - delete_comment(comment_id)
- ✓ Validate task exists before adding comment
- ✓ Integrate with JsonStorage for persistence
- ✓ Accessible via python -m src: interactive menu option AND one-shot CLI flags

**Should:**
- ✓ Service limited to TaskComment lifecycle; storage implementation separate
- ✓ Deleting a task cascades to delete its comments

**Could:**
- ✓ Support editing comment content with updated_at timestamp

**Won't:**
- ✗ Nested or threaded comment structures

### CLI Commands Available

```
Interactive: Menu option 7 "Manage comments"

One-shot flags:
  python -m src comment-add <task_id> <content> [-a author]
  python -m src comment-list <task_id>
  python -m src comment-update <comment_id> <content>
  python -m src comment-delete <comment_id>
```

### Test Results

- Baseline tests: 57/57 passing ✓
- New CommentsService tests: 24/24 passing ✓
- Total tests: 81/81 passing ✓
- No regressions in existing functionality
- Full integration testing verified

Duration: 595.3s | Cost: $1.896795 USD | Turns: 51
