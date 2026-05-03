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
