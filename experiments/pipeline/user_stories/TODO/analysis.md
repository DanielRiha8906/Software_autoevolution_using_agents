# Due Date Support Implementation Analysis

## Current State of the Codebase

### Task Model (`src/models/task.py`)
- **Type**: Dataclass with the following attributes:
  - `id`: UUID string (auto-generated)
  - `title`: Required string
  - `description`: Optional string
  - `status`: TaskStatus enum (PENDING, IN_PROGRESS, DONE)
  - `created_at`: datetime (UTC timezone-aware)
  - `updated_at`: datetime (UTC timezone-aware)

- **Serialization methods**:
  - `to_dict()`: Converts task to dictionary; dates are serialized via `.isoformat()`
  - `from_dict(data)`: Class method to reconstruct task from dictionary; uses `datetime.fromisoformat()` for date parsing

- **Current datetime handling**:
  - Uses `datetime.now(timezone.utc)` for default timestamps
  - All datetime fields are timezone-aware (UTC)
  - ISO 8601 format is used for serialization

### Storage Layer (`src/storage/json_storage.py`)
- **JsonStorage** class handles persistence:
  - Loads/saves tasks as JSON to a file (default: `~/.todo_data.json`)
  - `load()` returns list of dictionaries
  - `save(tasks)` accepts list of dictionaries and writes to JSON
  - No validation of dictionary schema; accepts any valid JSON

### Service Layer
- **TaskManager** (`src/services/task_manager.py`):
  - Manages in-memory task dictionary
  - `add()` method creates new tasks (title + optional description only)
  - `update()` method allows changing title and description
  - `get()` supports prefix-based task ID lookup
  - No validation of input formats beyond empty title checks
  - Updates `updated_at` on any modification

- **TodoService** (`src/services/todo_service.py`):
  - Higher-level API wrapping TaskManager
  - Validates empty titles
  - No date/datetime validation currently

### CLI Layer (`src/cli/todo_cli.py` and `src/cli/interactive_menu.py`)
- **TodoCLI**: Command-line interface with subcommands:
  - `add --title [--description]`
  - `update --id [--title] [--description]`
  - `show --id` displays dates in ISO format
  - No due date command or option exists

- **InteractiveMenu**: Interactive UI:
  - Can add/update tasks but only title and description fields
  - Shows timestamps in human-readable format: `'%Y-%m-%d %H:%M UTC'`
  - No due date display or input

### Test Pattern (from `tests/test_task.py`)
- Tests focus on object creation, serialization roundtrips, and status handling
- Use `task.to_dict()` and `Task.from_dict()` for serialization testing
- Check that attributes preserve values through serialization cycles

---

## Gap Analysis

### What's Missing for Acceptance Criteria

| Criterion | Current State | Gap |
|-----------|---------------|-----|
| `Task` has optional `due_date` attribute | **Missing** | Need to add `due_date: Optional[datetime] = None` field to Task dataclass |
| Tasks without due date load correctly | **Unknown** | Depends on how `from_dict()` handles missing `due_date` key |
| `due_date` stored/loaded via storage | **Missing** | Need to include in `to_dict()` and handle in `from_dict()` |
| Timezone-aware ISO 8601 in CEST (UTC+2) | **Partial** | Current code uses UTC; requires timezone conversion for display/storage |
| Invalid datetime rejected before save | **Missing** | No validation layer for datetime input; need to add validation |
| Backward compatibility (missing `due_date` field) | **At risk** | `from_dict()` uses direct key access; must use `.get()` with default |

### Specific Issues

1. **Task.from_dict() is not backward-compatible**
   - Line 31-39 in `task.py` uses direct dictionary access: `data["created_at"]`, `data["updated_at"]`
   - If a stored task lacks `due_date` key, deserialization will fail with KeyError
   - Must change to use `.get("due_date")` for optional fields

2. **Timezone handling mismatch**
   - Current code uses UTC (e.g., `datetime.now(timezone.utc)`)
   - Acceptance criteria requires CEST (UTC+2) representation
   - Question: Does this mean:
     - (A) Store internally as UTC, display as CEST? (Most common)
     - (B) Store as CEST, operate as CEST?
     - Assumption: Store as UTC internally, convert to CEST for display only

3. **No datetime validation layer**
   - TodoService validates title (empty check) but not datetime inputs
   - Need to add validation that rejects invalid ISO 8601 strings before Task creation

4. **CLI needs new due date commands**
   - `add` command needs optional `--due-date` flag
   - `update` command needs `--due-date` flag
   - `show` command needs to display due date
   - Interactive menu needs input/display for due dates

5. **Service method signatures unchanged**
   - `TaskManager.add()` only accepts title + description
   - `TaskManager.update()` only accepts title + description
   - Both need to accept optional due_date parameter

---

## Files and Classes Requiring Modification

### Core Model Changes
- **`src/models/task.py`**
  - Add `due_date: Optional[datetime] = None` field to Task dataclass
  - Update `to_dict()` to include `due_date` (serialized as ISO 8601 string or null)
  - Update `from_dict()` to safely load `due_date` with `.get("due_date")` as default None
  - Handle ISO 8601 string parsing for `due_date` field

### Service Layer Changes
- **`src/services/task_manager.py`**
  - Update `add()` signature: add `due_date: Optional[datetime] = None` parameter
  - Update `update()` signature: add `due_date: Optional[datetime] = None` parameter
  - Add validation: reject invalid datetime values before modifying task
  - Ensure `updated_at` is refreshed on due_date changes

- **`src/services/todo_service.py`**
  - Update `add_task()` signature: add `due_date` parameter
  - Update `update_task()` signature: add `due_date` parameter
  - Add datetime validation method (parse and validate ISO 8601 strings)
  - Raise ValueError if datetime is invalid

### CLI Layer Changes
- **`src/cli/todo_cli.py`**
  - Add `--due-date` option to `add` subcommand (optional)
  - Add `--due-date` option to `update` subcommand (optional)
  - Update `_cmd_show()` to display due_date in ISO 8601 format (or "—" if None)
  - Update `_cmd_list()` to optionally show due date in summary line

- **`src/cli/interactive_menu.py`**
  - Update `_do_add()` to prompt for optional due date
  - Update `_do_update()` to allow changing due date
  - Update `_do_show()` to display due date in human-readable format (CEST)
  - Add helper method `_parse_due_date()` to convert user input to datetime

### Storage Layer
- **`src/storage/json_storage.py`**
  - No changes required; already handles generic dictionary keys

---

## Key Implementation Concerns

### 1. Datetime Parsing and Validation
- **Issue**: Accept user input (ISO 8601 string) and convert to datetime object
- **Approach**: 
  - Use `datetime.fromisoformat()` for parsing (handles ISO 8601 strings)
  - Catch `ValueError` exceptions if parsing fails
  - Validate in TodoService before passing to TaskManager

### 2. Timezone Handling (CEST vs UTC)
- **Issue**: Accept criteria specifies CEST (UTC+2) representation
- **Assumption**: This means display/user-facing format is CEST, but storage is UTC
- **Implementation**:
  - Store all `due_date` values as timezone-aware UTC datetimes
  - When parsing user input, assume CEST input and convert to UTC
  - When displaying, convert UTC to CEST using timezone offset
  - Use `pytz` or `zoneinfo` (Python 3.9+) for timezone handling

### 3. Backward Compatibility (Critical)
- **Issue**: Existing stored tasks lack `due_date` field
- **Solution**: Use `.get()` in `from_dict()` with None default
- **Example**: `due_date_str = data.get("due_date")` then parse only if not None
- **Testing**: Must verify that tasks saved before this feature load without error

### 4. Optional Parameter Chaining
- **Issue**: `add()` and `update()` methods need optional due_date parameter
- **Challenge**: Must differentiate "not provided" from "set to None"
  - For add: no due date provided → use None (default)
  - For update: no due date provided → keep existing value
  - For update: due date provided as None → clear existing due date
- **Solution**: Use sentinel value or separate boolean flag to detect "not provided"

### 5. Display Format in Interactive Menu
- **Issue**: Current format shows `'%Y-%m-%d %H:%M UTC'`
- **Change needed**: Convert UTC to CEST before display
- **Approach**: Add helper method to convert timezone and format output

---

## Scope Summary

### In Scope
- Add `due_date` attribute to Task model
- Serialization/deserialization with backward compatibility
- Validation of datetime input before save
- CLI commands to set/display due date
- Interactive menu support for due date
- Timezone conversion (UTC storage → CEST display)

### Explicitly Out of Scope
- Task sorting by due date (not mentioned in acceptance criteria)
- Due date reminders or notifications
- Recurring tasks
- Time zone customization (fixed to CEST)

### Borderline (Clarification Needed)
- Format of user input for dates (ISO 8601? Natural language? Interactive prompt?)
  - **Assumption**: ISO 8601 string input (e.g., `2024-12-31T14:30:00+02:00`)
- Whether CLI `show` displays due date or only in interactive menu
  - **Assumption**: Both CLI and interactive menu should display it

---

## Suggested Priorities

### Priority 1 (Blockers)
1. **Task model and serialization** — Everything depends on this
   - Add `due_date` field
   - Update `to_dict()` and `from_dict()` with backward compatibility
   - Test roundtrip serialization

2. **Validation layer** — Prevents invalid data entering system
   - Add datetime validation to TodoService
   - Reject malformed ISO 8601 strings

### Priority 2 (Core Functionality)
3. **Service layer parameter updates** — Enable due date setting
   - Extend `TaskManager.add()` and `update()` signatures
   - Extend `TodoService.add_task()` and `update_task()` signatures

4. **CLI support** — Minimal user-facing feature
   - Add `--due-date` option to `add` and `update` commands
   - Update `show` command display

### Priority 3 (User Experience)
5. **Interactive menu enhancements** — Better UX but not blocking
   - Add date input prompts
   - Display dates in CEST format
   - Add timezone conversion helper

6. **Edge cases and testing** — Quality assurance
   - Test backward compatibility with old saved tasks
   - Test timezone conversions
   - Test invalid input rejection

---

## File Paths (Absolute)

- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/models/task.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/services/task_manager.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/services/todo_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/cli/todo_cli.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/cli/interactive_menu.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/src/storage/json_storage.py` (no changes needed)
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/user_stories/TODO/tests/test_task.py` (will need new tests)

