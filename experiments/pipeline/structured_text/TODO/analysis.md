# Task 01: Add Due Dates to TODO Tasks — Analysis Report

**Date:** 2026-05-01  
**Status:** Analysis complete

---

## What the Task Requires

Add due date support to the TODO application. Tasks must optionally store a `due_date` as a timezone-aware datetime (CEST / UTC+2) in ISO 8601 format. Tasks without due dates must be supported (None by default), and all data must persist through the JSON storage layer.

### Must-Have Requirements
1. Add `due_date: Optional[datetime]` to the Task dataclass
2. Default to None (tasks without due dates are valid)
3. Persist due dates through the storage layer
4. Update `to_dict()` to serialize `due_date` as ISO 8601 string
5. Update `from_dict()` to deserialize due_date with timezone awareness
6. Use CEST (UTC+2, UTC+timedelta(hours=2)) timezone-aware datetime

### Should-Have Requirements
- Backward compatibility: existing JSON (without `due_date` field) must load without error
- Validate datetime values when provided

### Could-Have Requirements
- Add `is_overdue()` predicate method to Task

---

## Current Architecture

### Task Class (`src/models/task.py`)
- **Location:** `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task.py`
- **Pattern:** Python `@dataclass` with UUID-based `id`
- **Current attributes:**
  - `title: str` (required)
  - `id: str` (auto-generated UUID)
  - `description: Optional[str]` (defaults to None)
  - `status: TaskStatus` (enum: PENDING, IN_PROGRESS, DONE)
  - `created_at: datetime` (UTC timezone, auto-generated)
  - `updated_at: datetime` (UTC timezone, auto-generated)

- **Serialization:**
  - `to_dict()`: Converts all fields to a dictionary; datetimes use `.isoformat()`
  - `from_dict()`: Reconstructs Task from dict; uses `datetime.fromisoformat()` for timestamps

**Current `to_dict()` output (example):**
```json
{
  "id": "cfb1c5c7-40eb-473c-82c6-44a6304f0e29",
  "title": "Sample Task",
  "description": "This is a sample task",
  "status": "pending",
  "created_at": "2026-05-01T17:49:05.712688+00:00",
  "updated_at": "2026-05-01T17:49:05.712693+00:00"
}
```

### Storage Layer (`src/storage/json_storage.py`)
- **Pattern:** Simple JSON file persistence via `json.dump()` / `json.load()`
- **Behavior:** 
  - Reads and writes plain Python dicts (no schema validation)
  - Creates parent directories if needed
  - Returns empty list if file doesn't exist
  - Accepts list of dicts (task data)
- **No special handling needed:** JSON serialization is transparent; datetimes are already serialized as ISO 8601 strings

### Service Layer
- **TaskManager** (`src/services/task_manager.py`): CRUD operations
  - Calls `Task.from_dict()` on load
  - Calls `task.to_dict()` on persist
  - Updates `updated_at` on status/title/description changes
  
- **TodoService** (`src/services/todo_service.py`): Higher-level API (add_task, start_task, complete_task, etc.)
  - Delegates to TaskManager
  - Validates empty titles

### CLI Interfaces
- **TodoCLI** (`src/cli/todo_cli.py`): Command-line interface
  - Current operations: add, list, show, start, done, reopen, update, delete
  - `_cmd_add()` accepts title and optional description
  - `_cmd_show()` displays all task attributes including `created_at` and `updated_at`
  
- **InteractiveMenu** (`src/cli/interactive_menu.py`): Interactive menu
  - `_do_add()` prompts for title and optional description
  - `_do_show()` displays task details

---

## Key Findings

### 1. Timezone Handling in Current Code
- Currently uses `datetime.now(timezone.utc)` for `created_at` and `updated_at`
- All times are stored in UTC (offset `+00:00`)
- The requirement specifies **CEST (UTC+2)** for due dates only

**Clarification:** The requirement states "CEST timezone-aware datetime in ISO 8601 format." This applies to the `due_date` field. Since CEST is a specific offset (+2), we will use a fixed-offset timezone (`timezone(timedelta(hours=2))`) rather than trying to detect daylight saving rules.

### 2. Backward Compatibility Path
- The `from_dict()` method currently uses `data["created_at"]` (direct key access)
- For backward compatibility with existing JSON (tasks without `due_date`), we must use `.get("due_date")` instead of direct key access
- This allows loading old tasks without errors

### 3. Datetime Serialization Format
- `.isoformat()` on a timezone-aware datetime produces strings like: `"2026-05-01T19:49:08.905942+02:00"`
- `datetime.fromisoformat()` correctly parses these strings, preserving timezone info
- No additional parsing logic is needed; Python's standard library handles it

### 4. Dataclass Field Defaults
- New field should use a factory: `due_date: Optional[datetime] = field(default_factory=lambda: None)`
- Or simpler: `due_date: Optional[datetime] = None` (works for None)

### 5. Validation Considerations
- Datetime validation could reject invalid types or out-of-range dates
- `from_dict()` should handle `ValueError` from `datetime.fromisoformat()` gracefully, or raise with clear context
- For "could-have" `is_overdue()`: requires comparing due_date to current time in CEST

---

## Changes Required

### 1. Task Model (`src/models/task.py`)
**Change 1a:** Add import for timezone offset
```python
from datetime import datetime, timezone, timedelta
```

**Change 1b:** Add `due_date` field to Task dataclass
```python
due_date: Optional[datetime] = None
```

**Change 1c:** Update `to_dict()` to include due_date
- Serialize as ISO 8601 string (or None if null)
- Options:
  - Option A: `"due_date": self.due_date.isoformat() if self.due_date else None`
  - Option B: Use conditional in dict literal

**Change 1d:** Update `from_dict()` to deserialize due_date
- Use `.get("due_date")` for backward compatibility
- Parse ISO 8601 string with timezone: `datetime.fromisoformat(due_date_str)` if not None

**Change 1e (Could):** Add `is_overdue()` method
- Compare `self.due_date` to `datetime.now(timezone(timedelta(hours=2)))`
- Return `False` if `due_date` is None

### 2. Service Layer Changes

**Change 2a: TaskManager** (`src/services/task_manager.py`)
- Add optional `due_date` parameter to `add()` method
- Update `update()` to optionally set `due_date`
- These propagate to the service layer

**Change 2b: TodoService** (`src/services/todo_service.py`)
- Add optional `due_date` parameter to `add_task()`
- Add method to set/update due dates: e.g., `set_due_date(task_id: str, due_date: Optional[datetime]) -> Task`
- Pass due_date through to TaskManager

### 3. CLI Changes (CLI is the interface to the feature)

**Change 3a: TodoCLI** (`src/cli/todo_cli.py`)
- Add `--due-date` / `-e` flag to `add` command
- Add `--due-date` / `-e` flag to `update` command
- Accept due_date in ISO 8601 format string
- Parse string to datetime with CEST timezone
- Display due_date in `_cmd_show()` output
- Display due_date in `_cmd_list()` output (optional: add column)

**Change 3b: InteractiveMenu** (`src/cli/interactive_menu.py`)
- Add due_date prompt in `_do_add()`
- Add due_date editing in `_do_update()`
- Display due_date in `_do_show()`

### 4. Test Coverage

**Change 4a: test_task.py**
- Add test for `due_date` defaults to None
- Add roundtrip test with due_date (serialize/deserialize)
- Test backward compatibility: `from_dict()` with missing `due_date` field
- (Could) Test `is_overdue()` predicate

**Change 4b: test_task_manager.py**
- Test `add()` with due_date
- Test `update()` to set/change due_date
- Test persistence with due_date

**Change 4c: test_todo_cli.py**
- Test `add` command with `--due-date` flag
- Test `show` displays due_date
- Test backward compatibility loading old JSON

### 5. Artifacts (Diagrams)

**Change 5a: class_diagram.puml**
- Update Task class to show `due_date: DateTime [0..1]` attribute
- Update `toDict()` and `fromDict()` method signatures if needed (optional)

---

## Ambiguities & Assumptions

### 1. CEST vs. Detecting Daylight Saving
**Ambiguity:** The requirement says "CEST timezone-aware datetime." CEST (Central European Summer Time) is a specific offset +2. In Europe, there's also CET (winter, +1).

**Assumption:** Store due dates with a fixed +2 offset (using `timezone(timedelta(hours=2))`). If the feature needs to handle daylight saving automatically, that would require a library like `zoneinfo` (Python 3.9+) or `pytz`. For now, a fixed +2 offset satisfies the requirement literally.

### 2. CLI Due Date Input Format
**Ambiguity:** Requirements don't specify how users provide due dates in the CLI.

**Assumption:** Accept ISO 8601 formatted strings (e.g., `"2026-05-15T14:30:00+02:00"`) on the command line. Interactive menu should guide users more clearly with a date/time prompt.

### 3. Validation & Error Handling
**Ambiguity:** Should invalid due_date strings cause the task to fail to load?

**Assumption:** 
- In `from_dict()`, catch `ValueError` from `datetime.fromisoformat()` and raise a more context-aware error (or log and set to None as a fallback)
- In CLI, if user provides invalid ISO 8601, reject with a helpful error message

### 4. Display Format in CLI
**Ambiguity:** How to display due_date in `show` and `list` commands?

**Assumption:**
- In `show`: Display full ISO 8601 (e.g., "2026-05-15T14:30:00+02:00")
- In `list`: Optionally show due date or an "overdue" indicator (if implementing `is_overdue()`)

---

## Scope Summary

### In Scope
- Add `due_date: Optional[datetime]` field to Task dataclass
- Serialize/deserialize via ISO 8601 strings
- Persist through JSON storage (no storage layer changes required)
- Backward compatibility for existing JSON without `due_date`
- CLI support for setting/viewing due dates
- Tests for serialization, backward compatibility, and persistence

### Out of Scope (Not Required)
- Daylight saving time auto-detection (fixed +2 offset only)
- Database migration scripts (JSON is schema-less)
- Recurring due dates or reminders

### Borderline (Could-Have)
- `is_overdue()` method on Task
- Overdue indicator in CLI list output
- Interactive date picker for due_date input

---

## Implementation Priority

1. **First:** Update Task model (add field, update to_dict/from_dict) — this is the core change
2. **Second:** Update service layer (add/update due_date parameters)
3. **Third:** Add comprehensive tests for Task serialization and backward compatibility
4. **Fourth:** CLI support (add command flags, display due_date)
5. **Fifth:** Could-have features (is_overdue, interactive prompts)
6. **Sixth:** Update diagrams

All changes are **isolated to src/ and tests/**; no changes to storage, baseline, or governance files are needed.

---

## File Paths Summary

**Core Files to Modify:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/models/task.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/task_manager.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/services/todo_service.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/cli/todo_cli.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/src/cli/interactive_menu.py`

**Test Files to Modify:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/tests/test_task.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/tests/test_task_manager.py`
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/tests/test_todo_cli.py`

**Diagram Files to Update:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/TODO/artifacts/class_diagram.puml`
