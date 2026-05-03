# Design Specification: MemoryEntry Domain Class

## 1. Class Definition Structure

**File Location:** `src/models/memory_entry.py`

**Fields with Types and Rationale:**

### Required Fields (Constructor Parameters):
- **operation: str** — The name of the operation performed (e.g., "add", "multiply")
- **operands: list** — All inputs to the operation as a sequence; supports unary and n-ary operations
- **result: Optional[float]** — The numeric result, or None if failed
- **success: bool** — Boolean flag indicating whether the calculation succeeded
- **execution_time_ms: float** — Time taken in milliseconds

### Auto-Generated Fields (with defaults):
- **id: str** — UUID string via `str(uuid4())` in default_factory. Guaranteed unique per instance.
- **timestamp: str** — ISO format timestamp, generated in `__post_init__()`. Default initialized to empty string.

---

## 2. __post_init__() Logic

```python
def __post_init__(self) -> None:
    if not self.timestamp:
        self.timestamp = datetime.now().isoformat()
```

**Behavior:**
- Checks if timestamp is empty string (default value)
- If empty, calls `datetime.now().isoformat()` to generate ISO 8601 formatted string
- If timestamp was provided explicitly (deserialization), preserves it
- Ensures every MemoryEntry has valid, non-empty timestamp

---

## 3. to_dict() Implementation

```python
def to_dict(self) -> dict:
    return asdict(self)
```

**Why This Works:**
- `id` is stored as string (via `str(uuid4())`)
- String is JSON serializable; no conversion needed
- `timestamp` is already ISO format string
- `operands` (list) and `result` (float or None) are naturally JSON serializable
- `success` (bool) is naturally JSON serializable

---

## 4. from_dict() Classmethod Implementation

```python
@classmethod
def from_dict(cls, data: dict) -> "MemoryEntry":
    return cls(**data)
```

**Parameter Handling:**
- Accepts dict with all 7 fields
- Unpacks dict as keyword arguments
- `id` is string (no conversion needed)
- `timestamp` is string (no conversion needed)
- `result` is None if originally None (JSON null → Python None)
- `__post_init__()` will NOT override timestamp (it's not empty)

---

## 5. Edge Cases and Handling

### result=None Handling
- Field declared as `result: Optional[float]`
- JSON represents None as null → Python json.loads() deserializes to None
- No special handling needed in to_dict() or from_dict()
- `success` flag clarifies whether None is intentional

### UUID Uniqueness
- `default_factory=lambda: str(uuid4())` generates new UUID string for each instance
- When deserializing, id is preserved (not regenerated)

### Timestamp Format
- `datetime.now().isoformat()` produces ISO 8601: "2025-02-10T14:30:45.123456"
- Round-trip safe; isoformat() can parse its own output
- Naive datetime (no timezone) — matches CalculationResult pattern

---

## 6. Files to Create/Modify

### File 1: CREATE src/models/memory_entry.py
- **Path:** `src/models/memory_entry.py`
- **Purpose:** Define MemoryEntry domain class
- **Dependencies:** dataclasses (asdict, field), datetime, uuid, typing
- **Estimated size:** 30-40 lines
- **Imports:**
  ```python
  from dataclasses import dataclass, asdict, field
  from datetime import datetime
  from uuid import uuid4
  from typing import Optional
  ```
- **Class Structure:**
  - @dataclass decorator
  - 5 required fields + 2 auto-generated fields
  - __post_init__() method
  - to_dict() method
  - from_dict() classmethod

### File 2: UPDATE src/models/__init__.py
- **Current:** Imports Operation and CalculationResult
- **Add:** Import MemoryEntry and add to __all__
- **Changes:**
  - Add: `from .memory_entry import MemoryEntry`
  - Add to __all__: `"MemoryEntry"`

---

## 7. Test Expectations

The test suite will verify:
1. Constructor accepts 5 required positional args
2. Auto-generated `id` is unique UUID string per instance
3. Auto-generated `timestamp` is set at construction in ISO format
4. `result=None, success=False` is valid for failed calculations
5. `to_dict()` produces a dictionary with all 7 fields
6. Timestamp in dict is string (not datetime object)
7. Round-trip: `MemoryEntry.from_dict(entry.to_dict())` preserves all fields exactly
8. No print() statements in the module

---

## Implementation Checklist

- [ ] Create src/models/memory_entry.py with @dataclass MemoryEntry
- [ ] Define 7 fields (5 required + 2 auto-generated)
- [ ] Implement __post_init__() for timestamp auto-generation
- [ ] Implement to_dict() using asdict()
- [ ] Implement from_dict() classmethod
- [ ] Update src/models/__init__.py to export MemoryEntry
- [ ] Verify zero print statements in module
- [ ] All tests pass
