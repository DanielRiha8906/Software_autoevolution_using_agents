# TODO Application: Add due_date Field Analysis

## Executive Summary

The task requires adding an optional `due_date: Optional[datetime]` field to the Task model with CEST (UTC+2) timezone enforcement, full serialization support, and backward compatibility with existing stored data. This is a straightforward domain model enhancement with clear serialization/deserialization patterns already established in the codebase.

## Current Task Model Structure

**File:** `/src/models/task.py`

The Task model is a Python dataclass with the following attributes:
- `title: str` — required
- `id: str` — auto-generated UUID
- `description: Optional[str]` — optional, defaults to None
- `status: TaskStatus` — enum (PENDING, IN_PROGRESS, DONE), defaults to PENDING
- `created_at: datetime` — auto-generated, defaults to `datetime.now(timezone.utc)`
- `updated_at: datetime` — auto-generated, defaults to `datetime.now(timezone.utc)`

**Current serialization pattern:**
- `to_dict()` — converts datetime objects to ISO 8601 strings via `.isoformat()`
- `from_dict()` — reconstructs datetime objects via `datetime.fromisoformat()`
- Status is stored as the enum value (string from the TaskStatus.value property)

**Key detail:** Both `created_at` and `updated_at` are already datetime objects with UTC timezone (via `timezone.utc`). The serialization uses `.isoformat()` which preserves timezone info in the ISO 8601 string (e.g., "2025-05-01T17:33:00+00:00").

## Requirements Analysis

1. **Optional due_date field**: Must be `Optional[datetime]` with default `None`
2. **CEST timezone**: Must enforce UTC+2 (Central European Summer Time) — reject naive or non-CEST datetimes
3. **ISO 8601 string storage**: Serialize to ISO format string in `to_dict()`, deserialize in `from_dict()`
4. **Full serialization support**: Both `to_dict()` and `from_dict()` must handle the new field
5. **Backward compatibility**: Loading old data without `due_date` key must work (None as default)
6. **Test validation**: Tests validate attribute existence, default None, setting/getting, serialization, round-tripping, old data loading, and type rejection

## What Needs to Be Added/Changed

### 1. Task Model Class (`src/models/task.py`)

**Add to dataclass:**
```python
due_date: Optional[datetime] = None
```

**Add validation method** (recommended as a `__post_init__` validator):
- Check if `due_date` is not None: ensure it has a timezone
- Check that the timezone offset is UTC+2 (equivalent to CEST)
- Raise TypeError or ValueError with a clear message if validation fails

**Update `to_dict()` method:**
- Add: `"due_date": self.due_date.isoformat() if self.due_date else None`
- This handles the None case and preserves ISO 8601 string format for non-None values

**Update `from_dict()` method:**
- Use `.get("due_date")` instead of dict access (for backward compatibility)
- Parse the datetime string if present: `datetime.fromisoformat(data["due_date"])` if `data.get("due_date")`
- Pass None if the key is missing or value is None
- This allows loading old tasks that lack the due_date field entirely

### 2. Timezone Validation Logic

**Challenge:** CEST is a daylight saving time offset, not a fixed timezone. Checking for UTC+2 is straightforward via the datetime object's `tzinfo` but requires care:

The `datetime.fromisoformat()` method will correctly parse "2025-05-01T17:33:00+02:00" (UTC+2) into a timezone-aware datetime. The `utcoffset()` method returns a `timedelta`, which can be checked:

```python
if due_date.tzinfo is None:
    raise TypeError("due_date must be timezone-aware")
if due_date.utcoffset() != timedelta(hours=2):
    raise ValueError("due_date must be in CEST (UTC+2)")
```

**Important:** This validation must happen in `__post_init__`, not just in `from_dict()`, to catch direct instantiation with invalid timezones.

### 3. Files That Don't Need Changes

The following files require NO changes:
- `src/storage/json_storage.py` — generic dict storage, no Task-specific logic
- `src/services/task_manager.py` — uses `task.to_dict()` and `Task.from_dict()` for persistence; the serialization methods handle all fields
- `src/services/todo_service.py` — thin validation layer; no changes needed unless API must support setting due_date
- `src/cli/todo_cli.py` — displays timestamps via `isoformat()` in `_cmd_show()`; due_date display is optional for this task
- `src/models/task_status.py` — unrelated
- Tests for storage and manager will continue to pass because the serialization/deserialization is encapsulated in Task

## Backward Compatibility Analysis

**Risk Level: Low**

1. **Old data loading (no due_date key):**
   - Current `from_dict()` uses `data.get("description")` pattern for optional fields
   - Implementing the same for due_date (`data.get("due_date")`) ensures old JSON files load without error
   - Missing key → `None` is passed to the dataclass field → defaults to None ✓

2. **Round-tripping:**
   - New tasks created without setting due_date will have `due_date=None`
   - Serializing None to `"due_date": None` in JSON is valid
   - Deserializing `None` back to the field will work with `.get()` pattern ✓

3. **No task instantiation in service/manager code:**
   - TaskManager calls `Task.from_dict()` only; no direct instantiation with positional args
   - TodoService delegates all Task creation to TaskManager
   - Safe from breaking changes ✓

4. **Timezone-aware datetime requirement:**
   - `created_at` and `updated_at` already use `timezone.utc`
   - External code creating tasks programmatically must pass CEST-aware datetime or None
   - This is a new requirement, not a breaking change to existing fields

## Potential Pitfalls and Edge Cases

### 1. Timezone Validation Strictness
- **Issue:** CEST is only UTC+2 during daylight saving (roughly late March to late October). Outside DST, Central Europe is CET (UTC+1).
- **Assumption:** The requirement means "accept UTC+2 only." If flexibility is needed for UTC+1 (CET), this must be clarified.
- **Implementation detail:** The validation must use `utcoffset()` to check the offset at the specific datetime instant, not a fixed string check.

### 2. `datetime.fromisoformat()` Limitations
- **Issue:** Python 3.11+ handles more ISO 8601 formats, but 3.12 is required here (per README).
- **Assumption:** `.fromisoformat()` will correctly parse "2025-05-01T17:33:00+02:00" style strings.
- **Safe:** Test round-tripping to confirm.

### 3. Naive Datetime Rejection
- **Issue:** The requirement says "reject naive or non-CEST datetimes."
- **Implementation:** Check `due_date.tzinfo is None` first to catch naive datetimes, then validate the offset.
- **Type:** Should this be a TypeError (wrong type/state) or ValueError (invalid value)? The requirement says "rejecting invalid types" — TypeError is appropriate for naive datetimes, ValueError for wrong timezone.

### 4. Empty/None JSON Values
- **Issue:** JSON serialization of `None` produces `null`. When deserializing, `data.get("due_date")` returns None, and `.fromisoformat(None)` will fail.
- **Implementation:** Use conditional: `if data.get("due_date") is not None: datetime.fromisoformat(...)`
- **Safe:** Follows the existing pattern for optional fields.

### 5. Dataclass Field Order
- **Issue:** Adding a new optional field with a default value after other fields is allowed in Python 3.10+.
- **Assumption:** The existing code is Python 3.12, so this is safe.
- **Current order:** non-optional fields (title) followed by optional fields with defaults. Adding `due_date: Optional[datetime] = None` at the end is safe.

### 6. Import Requirements
- **New imports needed in `task.py`:**
  - Already present: `from datetime import datetime, timezone`
  - Need to add: `from datetime import timedelta` (for offset validation)
- **No external dependencies** — timedelta is stdlib.

## Scope Clarifications

### In Scope
- Add `due_date` field to Task dataclass
- Implement timezone validation (CEST = UTC+2)
- Update `to_dict()` to serialize due_date
- Update `from_dict()` to deserialize due_date
- Ensure backward compatibility with old stored data
- Pass provided test suite

### Out of Scope
- CLI commands to set due_date (not mentioned in requirements)
- Display due_date in CLI output (not mentioned)
- Update service methods to accept/set due_date (not mentioned)
- Update diagrams (that is the UML designer's responsibility)

### Borderline
- Should the `updated_at` field be modified when due_date is set? — Not specified; likely no (only title/description changes trigger updated_at update in TaskManager.update())
- Should TaskManager have a method to update due_date separately? — Not specified; assume no

## Summary of Changes Required

| File | Change | Complexity |
|------|--------|------------|
| `src/models/task.py` | Add due_date field, validation in __post_init__, update to_dict() and from_dict() | Medium |
| All other src/ files | None | Low |
| Tests | Test suite provided; no changes to existing tests | N/A |

## Key Implementation Notes

1. **Use `datetime.fromisoformat()` for parsing** — it handles ISO 8601 with timezone info correctly in Python 3.12.

2. **Validation timing:** Put timezone validation in `__post_init__` so it triggers for all paths (direct instantiation and from_dict).

3. **Backward compatibility pattern:** Use `data.get("due_date")` and only call `.fromisoformat()` if the value is not None.

4. **Serialization:** Use conditional ternary: `self.due_date.isoformat() if self.due_date else None` in `to_dict()`.

5. **Test the boundary:** Ensure that `created_at` and `updated_at` (already UTC) are not mistakenly validated as CEST in the same method.
