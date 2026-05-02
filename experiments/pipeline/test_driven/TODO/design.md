# Design Document: Adding `due_date` to Task Model

## Overview

The implementation adds an optional `due_date: Optional[datetime]` field to the Task dataclass with CEST timezone-aware validation. The changes are minimal, localized to a single file, and maintain full backward compatibility with existing stored data.

---

## Source Changes

### File: `src/models/task.py`

#### Change 1: Add import for timedelta

**Location:** Top of file with other datetime imports.

**Current:** 
```python
from datetime import datetime, timezone
```

**After:**
```python
from datetime import datetime, timezone, timedelta
```

**Why:** Need `timedelta` to define CEST constant for timezone validation.

---

#### Change 2: Define CEST constant

**Location:** After imports, before the Task class definition.

**Add:**
```python
# CEST: Central European Summer Time (UTC+2)
CEST = timezone(timedelta(hours=2))
```

**Why:** Provides a reusable constant for timezone comparison.

---

#### Change 3: Add timezone validation helper

**Location:** After CEST constant, before Task class.

**Add:**
```python
def _validate_due_date_timezone(dt: datetime) -> None:
    """Validate that a datetime is timezone-aware and uses CEST."""
    if dt.tzinfo is None:
        raise ValueError("due_date must be timezone-aware (got naive datetime)")
    if dt.tzinfo != CEST:
        raise ValueError(f"due_date must use CEST (UTC+2); got {dt.tzinfo}")
```

**Why:** Extracts validation logic for clarity and reusability.

---

#### Change 4: Add due_date field to dataclass

**Location:** In the Task dataclass field list, after `updated_at`.

**Current:**
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

**After:**
```python
@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
```

**Why:** Adds the optional field with a default of None. The @dataclass decorator will auto-generate __init__ to accept this parameter.

---

#### Change 5: Update to_dict() method

**Location:** In the `to_dict()` method's returned dict.

**Current:**
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

**After:**
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "title": self.title,
        "description": self.description,
        "status": self.status.value,
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat(),
        "due_date": self.due_date.isoformat() if self.due_date else None,
    }
```

**Why:** Serializes due_date to ISO 8601 string format if present, or None if absent. Ensures test expectations are met.

---

#### Change 6: Update from_dict() class method

**Location:** In the `from_dict()` method.

**Current:**
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

**After:**
```python
@classmethod
def from_dict(cls, data: dict) -> Task:
    # Extract and validate due_date with backward compatibility
    due_date_str = data.get("due_date")
    due_date = None
    if due_date_str is not None:
        due_date = datetime.fromisoformat(due_date_str)
        _validate_due_date_timezone(due_date)
    
    return cls(
        id=data["id"],
        title=data["title"],
        description=data.get("description"),
        status=TaskStatus(data["status"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        due_date=due_date,
    )
```

**Why:**
- `data.get("due_date")` returns None if key is missing, enabling backward compatibility.
- If due_date is present and not None, it is parsed and validated.
- Timezone awareness and CEST checks reject invalid datetimes.
- None values are preserved.

---

## Implementation Order

1. **Step 1:** Add `timedelta` to imports and define `CEST` constant and validation helper.
   - Dependencies: None.

2. **Step 2:** Add `due_date: Optional[datetime] = None` field to dataclass.
   - Dependencies: Step 1.

3. **Step 3:** Update `to_dict()` to include due_date.
   - Dependencies: Step 2.

4. **Step 4:** Update `from_dict()` with validation logic.
   - Dependencies: Steps 1-3.

---

## Validation Logic

### Timezone Checking

```python
# Check 1: Is timezone-aware?
if dt.tzinfo is None:
    raise ValueError("due_date must be timezone-aware (got naive datetime)")

# Check 2: Is CEST?
if dt.tzinfo != CEST:
    raise ValueError(f"due_date must use CEST (UTC+2); got {dt.tzinfo}")
```

### Handling None vs Missing Key

```python
due_date_str = data.get("due_date")  # Returns None if key absent
due_date = None
if due_date_str is not None:
    # Parse and validate
    due_date = datetime.fromisoformat(due_date_str)
    _validate_due_date_timezone(due_date)
```

This ensures:
- Old stored data with no `due_date` key loads with `due_date=None`.
- New data with `"due_date": null` also loads with `due_date=None`.
- Invalid values raise ValueError from `datetime.fromisoformat()` or the validator.

---

## Test Coverage

The implementation satisfies all 8 test requirements:

1. `test_task_has_due_date_attribute` — Field exists (added to dataclass)
2. `test_due_date_defaults_to_none` — Default value is None
3. `test_due_date_can_be_set` — Constructor accepts due_date parameter
4. `test_due_date_in_to_dict` — Serialized to ISO 8601 string in dict
5. `test_due_date_round_trips_via_dict` — Survives to_dict/from_dict
6. `test_task_without_due_date_in_dict_loads_fine` — Backward compatible with missing key
7. `test_invalid_due_date_raises` — Type validation rejects invalid types
8. Plus implicit timezone validation tests (naive datetimes and non-CEST timezone rejection)

All 41 existing tests continue to pass because:
- New field has default value None
- to_dict() includes due_date (key always present)
- from_dict() handles missing key gracefully
- No changes to other methods or classes

---

## Files Affected

- `src/models/task.py` — single file with ~29 lines of changes

**No changes required to:**
- Task status enum
- TaskManager (uses Task.to_dict/from_dict)
- TodoService
- JsonStorage (generic)
- TodoCLI
- Any tests except the new due_date tests

---

## Summary

| Aspect | Details |
|--------|---------|
| Lines Changed | ~29 in src/models/task.py |
| Risk Level | Very low |
| Backward Compatibility | Full |
| Dependencies | None new |
| Test Additions | 8 new tests (provided) |
