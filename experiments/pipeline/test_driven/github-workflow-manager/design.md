# Design Plan: Add `duration_seconds` to WorkflowRun

## Overview

Add a new optional field `duration_seconds: float = 0.0` to the `WorkflowRun` dataclass with validation to reject negative values, while ensuring full backward compatibility with existing serialized data.

## Source Changes

### File: `src/models/workflow_run.py`

**Change 1: Add field to dataclass (after `commit_sha` field)**

```
    duration_seconds: float = 0.0
```

The field has a default value, so it is safe to place after optional fields. This preserves constructor backward compatibility.

---

**Change 2: Add `__post_init__()` method (after field definitions, before `to_dict()` method)**

```
    def __post_init__(self) -> None:
        """Validate that duration_seconds is not negative."""
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")
```

The dataclass decorator will call `__post_init__()` automatically after `__init__()` completes. This is the idiomatic way to add validation to Python dataclasses.

---

**Change 3: Update `to_dict()` method**

Add to the returned dictionary (before the closing `}`):
```
            "duration_seconds": self.duration_seconds,
```

No special serialization needed; floats serialize directly to JSON.

---

**Change 4: Update `from_dict()` classmethod**

Add to the `cls()` constructor call (before the closing `)`):
```
            duration_seconds=data.get("duration_seconds", 0.0),
```

`data.get("duration_seconds", 0.0)` provides backward compatibility: old dicts without the key will default to `0.0`.

---

## Implementation Order

1. Add the field (Change 1)
2. Add `__post_init__()` validation (Change 2)
3. Update `to_dict()` (Change 3)
4. Update `from_dict()` (Change 4)

## Backward Compatibility Strategy

**Old JSON without `duration_seconds`:** `from_dict()` uses `.get()` to supply default `0.0`

**New JSON with `duration_seconds`:** Explicit value is preserved

**Round-trip (to_dict → from_dict):** No data loss

## Edge Cases

- Negative values: `__post_init__()` raises `ValueError`
- Zero value: Allowed (validation is `< 0`, not `<= 0`)
- Old JSON missing field: Uses default `0.0`
- Very large/small floats: Accepted (no range validation)

## Summary of Changes

| File | Lines | Change |
|---|---|---|
| `src/models/workflow_run.py` | After field block | Add `duration_seconds: float = 0.0` |
| `src/models/workflow_run.py` | Before `to_dict()` | Add `__post_init__()` validation method |
| `src/models/workflow_run.py` | In `to_dict()` return dict | Add `"duration_seconds": self.duration_seconds` |
| `src/models/workflow_run.py` | In `from_dict()` constructor call | Add `duration_seconds=data.get("duration_seconds", 0.0)` |

**Total files modified:** 1  
**Methods changed:** 3 (`__init__` auto-generated, `__post_init__` new, `to_dict()`, `from_dict()`)  
**Approximate lines added:** 5-6

## Notes for Implementer

- The dataclass will automatically generate `__init__` that accepts `duration_seconds` with default `0.0`
- `__post_init__()` is invoked automatically by dataclass machinery
- No import changes needed
- No other methods should be modified
- Diagrams will be updated by UML designer separately
