# Due Date Feature Analysis

## Task Summary

Add optional `due_date: Optional[datetime]` field to the Task class with the following requirements:
- Must: Add field, allow None default, persist through storage, update serialization methods, use CEST timezone (ISO 8601)
- Should: Backward compatibility with existing JSON (tasks without due_date must load without error), validate datetime
- Could: Add is_overdue() predicate method

---

## Current Task Class Structure

**File:** `/src/models/task.py`

**Current definition (dataclass):**
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
- Uses dataclass with field defaults
- Timestamps (created_at, updated_at) use UTC timezone via `timezone.utc`
- Serialization methods: `to_dict()` and `from_dict(cls, data: dict)` already exist
- Both timestamps are initialized to current UTC time using `datetime.now(timezone.utc)`

**Current serialization (to_dict):**
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "title": self.title,
        "description": self.description,
        "status": self.status.value,
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat(),
    }
```

**Current deserialization (from_dict):**
```python
@classmethod
def from_dict(cls, data: dict) -> Task:
    return cls(
        id=data["id"],
        title=data["title"],
        description=data.get("description"),
        status=TaskStatus(data["status"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )
```

---

## Storage Layer Implementation

**File:** `/src/storage/json_storage.py`

**Structure:**
- Simple JSON file storage with default location: `~/.todo_data.json`
- Two methods: `load()` returns `list[dict]` and `save(tasks: list[dict])`
- Handles path creation, missing files gracefully
- Uses standard json module (no custom serialization logic)

**JSON persistence flow:**
1. TaskManager calls `Task.to_dict()` on each task
2. JsonStorage.save() receives list of dicts and writes as JSON
3. On load: JsonStorage.load() returns raw dicts
4. TaskManager calls `Task.from_dict(d)` to reconstruct Task objects

**Current sample JSON structure (created 2026-05-02):**
```json
{
  "id": "2c97feb8-de4d-4175-9094-5040fa0e0f8b",
  "title": "Test Task",
  "description": "A test task",
  "status": "pending",
  "created_at": "2026-05-02T21:25:29.121374+00:00",
  "updated_at": "2026-05-02T21:25:29.121378+00:00"
}
```

---

## Files That Will Need Changes

### Core (Must Change)

1. **`/src/models/task.py`**
   - Add `due_date: Optional[datetime] = None` field to Task dataclass
   - Update `to_dict()` to include due_date (only if not None, or always as null?)
   - Update `from_dict()` to handle missing due_date key (backward compatibility)
   - Optionally add `is_overdue()` method

2. **`/tests/test_task.py`**
   - Add test for Task with due_date
   - Add test for Task.from_dict() with missing due_date (backward compatibility)
   - Add roundtrip test including due_date
   - Optionally test is_overdue() predicate

### Service Layer (May Change)

3. **`/src/services/task_manager.py`**
   - May need to add `add()` parameter for due_date (currently: `add(title, description=None)`)
   - May need to add `update()` parameter for due_date (currently: `update(task_id, title=None, description=None)`)
   - May need setter/update method for due_date specifically

4. **`/src/services/todo_service.py`**
   - May need to add due_date parameters to `add_task()` and `update_task()`
   - May need new method to update due_date (if not through generic update)

### CLI/UI Layer (May Change)

5. **`/src/cli/todo_cli.py`**
   - May add `--due-date` flag to `add` command
   - May add due_date display to `show` command
   - May add `--due-date` flag to `update` command
   - May add filtering/sorting by due_date
   - May add `--overdue` flag to `list` command

6. **`/src/cli/interactive_menu.py`**
   - May add due_date input prompt to add task flow
   - May add due_date display in `_do_show()`
   - May add due_date editing to `_do_update()`
   - May add due_date to task line display (with visual indicator for overdue)

### Tests (Must Change)

7. **`/tests/test_task_manager.py`**
   - Add tests for add/update with due_date parameter
   - Test persistence of due_date

8. **`/tests/test_todo_service.py`**
   - Add tests for add_task/update_task with due_date

9. **`/tests/test_todo_cli.py`**
   - Add tests for add command with --due-date flag
   - Add tests for show command displaying due_date
   - Test backward compatibility (loading old JSON without due_date)

10. **`/tests/test_json_storage.py`**
    - May add test for loading JSON with missing due_date field

---

## How to_dict / from_dict Currently Work

### to_dict() Pattern
- Converts all fields to JSON-serializable types
- datetime objects are converted via `.isoformat()` → RFC 3339 string (includes timezone)
- Enum values converted to their `.value` (string)
- Optional fields included as-is (None passes through)

### from_dict() Pattern
- Uses `.get()` for optional fields (description)
- Uses direct dict access with KeyError for required fields
- `datetime.fromisoformat()` can parse ISO 8601 strings with timezone info
- `TaskStatus(value)` enum lookup by string value

### Backward Compatibility Consideration
Currently `from_dict()` uses direct dict access for required fields:
```python
created_at=datetime.fromisoformat(data["created_at"])  # KeyError if missing
```
But uses `.get()` for optional fields:
```python
description=data.get("description")  # Returns None if missing
```

For due_date to be backward compatible, must use `.get()` like description does.

---

## Timezone / Datetime Handling Approach

### Current Approach
- Uses UTC timezone exclusively (`timezone.utc`)
- Serializes with `.isoformat()` → produces RFC 3339 format
- Example: `"2026-05-02T21:25:29.121374+00:00"`

### Requirement Conflict
**Task requirement states:** "use CEST timezone (ISO 8601)"
**Current system uses:** UTC

### Options to Resolve

**Option A (Recommended):** Store in UTC internally, display in CEST
- Store due_date as UTC in the Task object (consistent with created_at/updated_at)
- Serialize to UTC ISO 8601 in JSON (standard practice)
- Convert to CEST only in UI layer (CLI/menu) for display
- Rationale: Maintains consistency, enables multi-timezone support, standard database practice

**Option B:** Store in CEST locally
- Use `ZoneInfo('Europe/Paris')` or similar for CEST
- Serialize to CEST ISO 8601 string
- Breaks consistency with existing created_at/updated_at fields
- Less portable (different timezones have different daylight saving transitions)

**Option C:** Store as naive datetime, interpret as CEST
- Don't include timezone in stored datetime
- Interpret as CEST when loading
- Rationale: Simple, but loses information and is fragile

### Recommended Implementation
- Add `due_date: Optional[datetime] = None` to dataclass
- Use CEST when creating due_date via CLI (pass ZoneInfo('Europe/Paris') or equivalent)
- Store as UTC (convert on input if needed)
- Display as CEST in UI
- Serialize as ISO 8601 with timezone

**Python approach:**
```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # Python 3.9+

# Creating a due date with CEST timezone
cest = ZoneInfo('Europe/Paris')
due_date = datetime(2026-06-01, 14, 30, tzinfo=cest)  # User input
# or: datetime.fromisoformat("2026-06-01T14:30:00+02:00")

# Store internally (convert to UTC for consistency)
due_date_utc = due_date.astimezone(timezone.utc)

# Serialize
due_date_utc.isoformat()  # "2026-06-01T12:30:00+00:00"

# Display (convert back to CEST for UI)
due_date_utc.astimezone(cest).strftime('%Y-%m-%d %H:%M CEST')
```

---

## Backward Compatibility Concerns

### JSON Compatibility (Should)
**Concern:** Old JSON files without due_date field should load without error

**Current risk:** `from_dict()` would crash if key is missing for required fields
**Solution:** Use `.get("due_date")` in `from_dict()` to return None if missing

**Test case needed:**
```python
def test_load_task_without_due_date():
    # Old format JSON (no due_date key)
    old_data = {
        "id": "123",
        "title": "Old Task",
        "status": "pending",
        "created_at": "2026-05-02T21:25:29+00:00",
        "updated_at": "2026-05-02T21:25:29+00:00"
    }
    task = Task.from_dict(old_data)
    assert task.due_date is None
```

### Serialization Consistency
**Concern:** New tasks will have `due_date: None` in JSON, creating inconsistency

**Options:**
1. Include `"due_date": null` always (verbose but consistent)
2. Omit null due_date from JSON (cleaner, but must use `.get()` on load)
3. Have `to_dict()` skip null due_date: `if self.due_date: {...}`

**Recommendation:** Option 2 (skip null) - consistent with optional description pattern in existing code

---

## Current Datetime Handling Details

### Created/Updated Timestamps
- Both use `field(default_factory=lambda: datetime.now(timezone.utc))`
- Set at object creation time (created_at) or modification (updated_at)
- Updated whenever status or content changes (in TaskManager.update/set_status)

### Display in UI
**In interactive_menu.py (lines 167-168):**
```python
print(f"  Created:     {task.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
print(f"  Updated:     {task.updated_at.strftime('%Y-%m-%d %H:%M UTC')}")
```

**In todo_cli.py (lines 121-122):**
```python
print(f"Created:     {task.created_at.isoformat()}")
print(f"Updated:     {task.updated_at.isoformat()}")
```

Note: CLI displays ISO format; menu displays formatted string with explicit UTC label.

---

## Design Implications for Implementation

### Dataclass Field Ordering
Dataclass fields must have a specific order: fields with defaults must come after fields without.

**Current order:** title (no default) → id, description, status, created_at, updated_at (all with defaults)

**Adding due_date:**
- Must come after title (has no default)
- Should come after status and before/after timestamps (convention-dependent)
- Suggested: after status, before timestamps (semantic grouping)

```python
@dataclass
class Task:
    title: str
    id: str = field(default_factory=...)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None  # NEW
    created_at: datetime = field(default_factory=...)
    updated_at: datetime = field(default_factory=...)
```

### Optional: is_overdue() Method
**Signature:**
```python
def is_overdue(self) -> bool:
    if self.due_date is None:
        return False
    return datetime.now(timezone.utc) > self.due_date.astimezone(timezone.utc)
```

**Logic:**
- Return False if no due_date set
- Compare current UTC time to due_date (must normalize both to same timezone)
- Account for completed tasks (DONE status) - could return False regardless

**Alternative (include status):**
```python
def is_overdue(self) -> bool:
    if self.due_date is None or self.status == TaskStatus.DONE:
        return False
    return datetime.now(timezone.utc) > self.due_date.astimezone(timezone.utc)
```

---

## Summary of Findings

| Category | Finding |
|----------|---------|
| **Current Task structure** | Dataclass with 6 fields; optional description uses `.get()` on deserialize |
| **Storage mechanism** | Simple JSON file; uses to_dict/from_dict round-trip |
| **Serialization** | datetime → isoformat() string; uses ISO 8601 with timezone |
| **Required changes** | Task.py (field + methods), all tests, optional CLI/service updates |
| **Backward compatibility** | Use `.get("due_date")` in from_dict() to match description pattern |
| **Timezone approach** | Recommend: Store UTC internally, display CEST in UI (consistent with created/updated) |
| **Test coverage** | Must add roundtrip test with due_date, must add backward compat test |
| **is_overdue() complexity** | Low; simple comparison with timezone normalization |

---

## Files Summary (Absolute Paths)

Must Change:
- `/src/models/task.py` — Add field and update serialization
- `/tests/test_task.py` — Add due_date tests

Should Change:
- `/tests/test_task_manager.py` — Test persistence of due_date
- `/tests/test_todo_service.py` — Validate due_date parameter (if added to service)
- `/tests/test_todo_cli.py` — Test backward compatibility and CLI flags

May Change:
- `/src/services/task_manager.py` — Add due_date parameter to add/update if needed
- `/src/services/todo_service.py` — Add due_date parameter to add_task/update_task if needed
- `/src/cli/todo_cli.py` — Add --due-date flag to add/update commands if needed
- `/src/cli/interactive_menu.py` — Add due_date input/display in menus if needed

