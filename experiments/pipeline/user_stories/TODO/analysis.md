# Analysis: Task 01 — Add Due Date Support

## Task Summary

Implement an optional `due_date` attribute for tasks, allowing users to assign and track deadlines. The feature must:
- Store dates in timezone-aware ISO 8601 format (CEST, UTC+2)
- Validate datetime values before persisting
- Load existing tasks that lack `due_date` without error
- Be fully accessible via both CLI and interactive menu

---

## Current Architecture Overview

### Class Diagram Components
The codebase follows a layered architecture:

1. **Domain Model** (`src/models/`)
   - `Task`: dataclass with id, title, description, status, created_at, updated_at
   - `TaskStatus`: enum (PENDING, IN_PROGRESS, DONE)

2. **Storage Layer** (`src/storage/`)
   - `JsonStorage`: handles JSON read/write to file (~/.todo_data.json by default)
   - Converts task objects to/from dictionaries via `to_dict()` and `from_dict()`

3. **Service Layer** (`src/services/`)
   - `TaskManager`: CRUD operations, task persistence, prefix-based lookup
   - `TodoService`: higher-level operations with validation (e.g., empty title check)

4. **CLI Layer** (`src/cli/`)
   - `TodoCLI`: command-line interface with subcommands (add, list, show, start, done, reopen, update, delete)
   - `InteractiveMenu`: terminal-based interactive menu
   - Both use `TodoService` as their backend

---

## Current Task Model Implementation

**File:** `/src/models/task.py`

```python
@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

**Key observations:**
- Uses dataclass decorator for automatic `__init__`, `__repr__`, equality
- DateTime fields already use `timezone.utc` (currently)
- Has `to_dict()` method that serializes to ISO format strings
- Has `from_dict()` classmethod that deserializes from dictionaries
- Currently stores timestamps with `.isoformat()` and restores with `datetime.fromisoformat()`

---

## Current Storage Layer Implementation

**File:** `/src/storage/json_storage.py`

**Key observations:**
- `load()` returns list of dictionaries (empty list if file doesn't exist)
- `save(tasks)` expects list of dictionaries
- No validation of dictionary structure
- Parent directories created automatically
- Uses UTF-8 encoding

**Current serialization flow:**
```
Task object → task.to_dict() → JSON string → file
file → JSON parse → dict → Task.from_dict() → Task object
```

---

## Current Service Layer

### TaskManager (`src/services/task_manager.py`)

**Key observations:**
- `add()` method creates new Task with default status, timestamps
- `update()` modifies title/description and updates `updated_at`
- `set_status()` changes status and updates `updated_at`
- Both `update()` and `set_status()` call `_persist()` after changes
- Methods use prefix matching for task lookup
- No validation of input datetime values

### TodoService (`src/services/todo_service.py`)

**Key observations:**
- `add_task()` validates non-empty title; delegates to TaskManager
- `update_task()` validates title if provided; delegates to TaskManager
- No date-related methods or validation currently

---

## Current CLI Implementation

### TodoCLI (`src/cli/todo_cli.py`)

**Key observations:**
- `add` command accepts title and optional `-d` description
- `update` command accepts `-t` title and `-d` description
- `show` command displays task details including timestamps in ISO format
- No due_date fields in command arguments or output display
- Error handling for ValueError and TaskNotFoundError

### InteractiveMenu (`src/cli/interactive_menu.py`)

**Key observations:**
- `_do_add()` prompts for title and optional description
- `_do_show()` displays created_at and updated_at using strftime
- `_do_update()` modpts for title and description
- No due_date input or display
- Uses helper functions `_prompt()` and `_pick()` for user input

---

## Existing Test Coverage

**Files affected:**
- `tests/test_task.py`: Tests Task construction, serialization (roundtrip), status
- `tests/test_json_storage.py`: Tests load/save, persistence, file creation
- `tests/test_task_manager.py`: Tests CRUD, status changes, prefix lookup
- `tests/test_todo_service.py`: Tests service validation, task operations
- `tests/test_todo_cli.py`: Tests CLI commands, output parsing

**Testing patterns:**
- Uses pytest fixtures for setup (tmp_path for temporary storage)
- Uses capsys for capturing stdout/stderr
- Tests expect specific output strings in CLI

---

## Acceptance Criteria Analysis

### Criterion 1: Task has optional due_date (None by default)
**Implementation point:** Add `due_date: Optional[datetime]` field to Task dataclass with default None

### Criterion 2: Tasks without due_date load correctly
**Implementation point:** 
- Task.from_dict() must use `.get("due_date")` instead of `["due_date"]`
- Handle missing due_date gracefully (returns None)
- Existing JSON files with no due_date field will deserialize without error

### Criterion 3: due_date stored/loaded through storage layer
**Implementation point:**
- Task.to_dict() must add due_date to output (None or ISO string)
- Task.from_dict() must extract from dict and parse
- JsonStorage layer unchanged (already handles any dict structure)

### Criterion 4: Timezone-aware ISO 8601 in CEST (UTC+2)
**Implementation point:**
- When serializing: use `.isoformat()` on datetime (preserves timezone offset)
- When deserializing: use `datetime.fromisoformat()` (handles timezone strings)
- Task constructor should accept and preserve timezone info
- Default due_date should be None; when set, must have timezone info
- CLI input parsing must create timezone-aware datetime objects

**Note on CEST:** CEST is UTC+2 (daylight saving time). Since Python's pytz is not required by task, either:
- Use `datetime.fromisoformat()` to parse user-provided ISO strings with explicit offset
- Or convert UTC timestamps to CEST at display time using timezone.tzinfo
- The requirement likely means: serialize in CEST offset format and accept CEST timestamps as valid input

### Criterion 5: Invalid datetime rejected before save
**Implementation point:**
- Add validation in Task constructor or as a separate validator
- Validate before Task object is created or before _persist() is called
- Raise ValueError with clear message
- CLI must catch ValueError and report to user

### Criterion 6: Existing stored tasks load without error
**Implementation point:**
- Task.from_dict() uses `.get("due_date")` to safely extract optional field
- JsonStorage._load() in TaskManager handles gracefully
- No breaking changes to existing JSON files

---

## Data Type & Validation Strategy

### Data Type Decision
- **Field type:** `Optional[datetime]` (from datetime module)
- **Serialization:** ISO 8601 string with timezone offset (via `.isoformat()`)
- **Deserialization:** `datetime.fromisoformat()` handles ISO 8601 with timezone
- **In-memory:** Python datetime.datetime object (supports comparison, formatting)

### Validation Points

1. **In Task class (constructor or validator):**
   - Check if due_date is provided (if not None)
   - Validate it's a datetime.datetime instance
   - Validate it has timezone info (is_aware or tzinfo is not None)
   - Reject naive datetime (no timezone)

2. **In CLI parsing (TodoCLI._cmd_add, _cmd_update):**
   - Parse ISO 8601 string from user input
   - Create datetime.datetime with timezone
   - Catch ValueError and report: "Invalid date format: {input}. Use ISO 8601 format (e.g., 2026-05-02T15:30:00+02:00)"

3. **In Service layer (TodoService):**
   - Consider adding `set_due_date()` method for explicit due date assignment
   - Validate before calling TaskManager

4. **In Storage layer:**
   - No validation needed; storage just writes what it receives

### Timezone Handling

Since CEST is UTC+2 and specified as required format:
- Accept input as ISO 8601 with any timezone offset (pytz not available, so can't auto-convert)
- When serializing, use `.isoformat()` which preserves the timezone offset from the datetime object
- When displaying, show the ISO string as-is or convert to user's local timezone if feasible

**Practical approach:**
- Accept ISO 8601 strings with timezone offset: "2026-05-02T15:30:00+02:00"
- Store them as-is via `.isoformat()`
- When deserializing, `datetime.fromisoformat()` restores the timezone offset

---

## Files Requiring Changes

### Model Layer

1. **`src/models/task.py`**
   - Add `due_date: Optional[datetime] = None` field to Task dataclass
   - Add validation in `__post_init__()` to check timezone-aware if provided
   - Update `to_dict()` to serialize due_date as ISO string or None
   - Update `from_dict()` to safely extract and parse due_date

### Service Layer

2. **`src/services/task_manager.py`**
   - Add `set_due_date(task_id, due_date)` method
   - Add optional `due_date` parameter to `add()` method (with default None)
   - Add optional `due_date` parameter to `update()` method

3. **`src/services/todo_service.py`**
   - Add optional `due_date` parameter to `add_task()` method
   - Add `set_due_date(task_id, due_date)` method with validation
   - Add optional `due_date` parameter to `update_task()` method
   - Validate datetime and reject invalid formats with clear error message

### CLI Layer

4. **`src/cli/todo_cli.py`**
   - Add `--due-date` / `--due_date` option to `add` subcommand (optional)
   - Add `--due-date` / `--due_date` option to `update` subcommand (optional)
   - Add `due-date` / `due_date` subcommand to set/change due date on existing task
   - Update `_cmd_show()` to display due_date in ISO format
   - Update `_cmd_list()` to optionally show due_date (or add a separate mode)
   - Handle ValueError exceptions from date parsing and report to user

5. **`src/cli/interactive_menu.py`**
   - Update `_do_add()` to optionally prompt for due date
   - Update `_do_show()` to display due_date
   - Add new menu option to set/change due date on existing task (or extend _do_update)
   - Use `_prompt()` helper to get date input with validation

### Storage Layer

- **`src/storage/json_storage.py`** — No changes needed (already handles any dict keys)

### Tests

6. **`tests/test_task.py`**
   - Add test for Task with due_date field
   - Add test for Task without due_date (default None)
   - Add test for to_dict/from_dict roundtrip with due_date
   - Add test for timezone-aware validation
   - Add test for naive datetime rejection

7. **`tests/test_task_manager.py`**
   - Add test for add() with due_date
   - Add test for set_due_date() method
   - Add test for update() with due_date
   - Add test for persistence of due_date across manager instances

8. **`tests/test_todo_service.py`**
   - Add test for add_task() with due_date
   - Add test for set_due_date() method with validation
   - Add test for invalid date format rejection

9. **`tests/test_todo_cli.py`**
   - Add test for `add` command with `--due-date` option
   - Add test for `update` command with `--due-date` option
   - Add test for invalid date format error handling
   - Add test for `show` command displaying due_date

10. **`tests/test_json_storage.py`**
    - Add test for loading legacy tasks without due_date field

---

## Implementation Sequence Recommendation

1. **Model changes first** (Task dataclass, serialization)
2. **Service changes** (validation, method signatures)
3. **CLI changes** (argument parsing, display)
4. **Interactive menu changes** (prompts, display)
5. **Tests** (comprehensive coverage at each layer)

---

## Edge Cases & Constraints

1. **Backward compatibility:** Existing JSON files must load without error when due_date is missing
2. **Timezone awareness:** All datetime objects must have timezone info (reject naive datetimes)
3. **CEST format:** Input and output should use CEST (UTC+2) or preserve user timezone in ISO string
4. **Validation timing:** Date validation must occur before Task object creation or persistence
5. **CLI prefix matching:** Due date must work with existing prefix-based task ID lookup
6. **Null/None handling:** Due date can be None; operations must handle this gracefully

---

## Summary of Changes by Layer

| Layer | Component | Change Type | Scope |
|-------|-----------|-------------|-------|
| Model | Task | Add field, validation, serialization | 1 file |
| Service | TaskManager | Add methods, parameter updates | 1 file |
| Service | TodoService | Add methods, parameter updates, validation | 1 file |
| CLI | TodoCLI | Add argument, command, output | 1 file |
| CLI | InteractiveMenu | Add prompts, display, menu option | 1 file |
| Tests | All test files | Add coverage for due_date feature | 5 files |

**Total files to modify: 9** (3 src + 1 storage baseline, 5 tests)

