# Task 03 Analysis: MemoryEntry Domain Class

## Task Summary

Create a new `MemoryEntry` domain class that represents a stored calculation attempt. This class must:
- Store operation name, input operands, result, success/error state, execution timestamp, and execution_time_ms
- Support both successful and failed calculations
- Provide JSON serialization/deserialization
- Maintain compatibility with existing calculation history
- Use clear field names for querying and reporting
- Keep display formatting out of the domain class

## Current Structure

### Existing Calculation Representation

**CalculationResult** (src/models/calculation_result.py):
- Dataclass using `@dataclass` decorator
- Fields: `operation` (str), `operand_a` (float), `operand_b` (float), `result` (float), `timestamp` (str, ISO 8601), `execution_time_ms` (float)
- Auto-generates timestamp via `__post_init__` if not provided
- Methods: `to_dict()` and `from_dict()` for JSON serialization
- String representation with symbol mapping (displays as "a + b = r" format)
- Currently assumes all calculations are successful (no error state)

### Storage Implementation

**JsonStorage** (src/storage/json_storage.py):
- Persists `CalculationResult` objects to JSON (artifacts/calculations.json)
- Methods: `save(result: CalculationResult)`, `load_all()` → list[CalculationResult]
- Handles missing files gracefully, returns empty list
- Supports backward compatibility (old JSON without execution_time_ms field)

### Current JSON Format

```json
[
  {
    "operation": "add",
    "operand_a": 3.0,
    "operand_b": 5.0,
    "result": 8.0,
    "timestamp": "2026-04-29T12:01:36.308310",
    "execution_time_ms": null  // optional, defaults to 0.0
  }
]
```

### How Results Flow

1. **CalculatorService.perform()** → Measures execution time, creates CalculationResult, calls storage.save()
2. **CalculationResult.__str__()** → Used by CLI for display (formatting happens here, not in domain class)
3. **JsonStorage** → Persists via `to_dict()`, loads via `from_dict()`
4. **CalculatorCLI._show_history()** → Iterates history, prints each entry with timestamp

### Error Handling in Current System

- **Calculator.calculate()** → Raises ValueError for invalid operations or math errors (division by zero, negative sqrt, modulo by zero)
- **CalculatorService.perform()** → Does NOT catch exceptions; they propagate to CLI
- **CLI** → Catches ValueError, prints to stderr, exits with code 1
- **No failures are persisted** — only successful calculations are saved to storage

## Critical Gap: Error State Support

The current system has a significant constraint:
- **CalculationResult only represents successful calculations**
- Errors during calculation abort the entire flow before storage
- Test evidence: `test_perform_divide_by_zero_does_not_save()` confirms failed calculations are never saved
- This is intentional behavior to avoid storing erroneous results

## What MemoryEntry Should Provide

### Required Fields

1. **operation**: str (operation name: "add", "subtract", etc.)
2. **operand_a**: float (first operand)
3. **operand_b**: float (second operand)
4. **result**: float (result value; only valid if success=True)
5. **success**: bool (True if calculation succeeded, False if error occurred)
6. **error_message**: str | None (error text if success=False, None otherwise)
7. **timestamp**: str (ISO 8601 execution time)
8. **execution_time_ms**: float (milliseconds to execute)

### Optional Fields (Could)

- **entry_id**: str (unique identifier, e.g., UUID or auto-incrementing integer)

### Design Implications

1. **result field must be optional** — Only populated when success=True
   - Could use float | None, or keep as float with sentinel value like NaN
   - JSON serialization needs handling for None values

2. **Field naming for clarity**
   - Use `operand_a` and `operand_b` (matches existing CalculationResult)
   - Use `success` (boolean) for clarity vs. storing only successful results
   - Use `error_message` (explicit) vs. generic error field

3. **JSON compatibility**
   - Current format expects only successful calculations
   - New format must be backward-compatible: old records have no `success` or `error_message` fields
   - Default interpretation: missing `success` field → assume success=True for old data
   - Missing `error_message` → assume None

4. **Display formatting**
   - MemoryEntry should provide access to fields, not formatted strings
   - CLI/services remain responsible for display logic
   - Keep `__str__()` minimal or descriptive (e.g., for logging)

## Existing Classes That May Interact with MemoryEntry

1. **JsonStorage** — Will need to support loading/saving MemoryEntry objects
   - Current code: `save(result: CalculationResult)` → must change to accept MemoryEntry
   - Backward compatibility: `from_dict()` must handle both old and new JSON formats

2. **CalculatorService** — Creates CalculationResult today
   - May need refactoring to create MemoryEntry instead
   - Or MemoryEntry becomes the persistent model while CalculationResult is a view

3. **CalculatorCLI** — Consumes CalculationResult from get_history()
   - If MemoryEntry replaces CalculationResult in storage, must handle error states
   - Must not break existing display logic (the `__str__()` method)

## Compatibility Constraints

### Backward Compatibility

1. **Existing JSON** → Must load without modification
   - Old records lack `success`, `error_message`, `entry_id` fields
   - Logic: treat missing `success` field as True
   - Logic: treat missing `error_message` as None

2. **Existing CalculationResult** → Should not break
   - Option A: Keep CalculationResult, add separate MemoryEntry class
   - Option B: Refactor CalculationResult to support error states (more intrusive)
   - Option C: MemoryEntry extends or wraps CalculationResult (tighter coupling)
   - **Recommendation**: Option A — parallel classes with conversion logic

3. **Existing Tests** → 87 tests currently pass
   - Tests use CalculationResult directly
   - Adding MemoryEntry should not require rewriting existing tests
   - New tests should cover MemoryEntry separately

### Storage Format Evolution

Current approach: JsonStorage reads/writes a list of plain dicts, relies on `from_dict()` for deserialization.

If MemoryEntry is added:
- Option 1: Create `MemoryEntryStorage` class (separate from JsonStorage)
- Option 2: Refactor JsonStorage to handle both CalculationResult and MemoryEntry
- **Recommendation**: Option 1 — keeps separation of concerns, allows parallel operation

## Implementation Approach Outline

### Phase 1: Define MemoryEntry Class

Create `src/models/memory_entry.py`:
- Dataclass with fields listed above
- `to_dict()` → JSON-compatible dict
- `from_dict(data: dict)` → MemoryEntry with backward-compatibility logic
- `__post_init__()` → Auto-generate timestamp if missing, validate state
- Minimal `__str__()` for debugging (not for display)

### Phase 2: Serialization Support

- Implement `to_dict()` to handle None result field
- Implement `from_dict()` with:
  - Default success=True if field missing
  - Default error_message=None if field missing
  - Handle result field safely (use None or NaN as sentinel)
- Add validation: if success=False, result should be None

### Phase 3: Optional: MemoryEntryStorage

Create `src/storage/memory_entry_storage.py` (or extend JsonStorage):
- Similar interface to JsonStorage
- Methods: `save(entry: MemoryEntry)`, `load_all() → list[MemoryEntry]`
- Uses same JSON file or separate file
- Handles backward compatibility with CalculationResult format

### Phase 4: Integration Points (NOT in this task, but noted for system-architect)

- CalculatorService could be extended to catch errors and create failed MemoryEntry objects
- CLI could display error entries separately
- Query/report functions could filter by success state

## Key Assumptions

1. **Error persistence is new capability** — Current system intentionally doesn't save failed calculations. MemoryEntry enables this, but actual error-saving logic comes in a later task.

2. **Operands are always floats** — System uses float(a), float(b) throughout. MemoryEntry assumes same type.

3. **Entry ID is optional** — Task says "Could", so primary implementation uses (operation, timestamp, operands) as natural identity. UUID can be added in a future enhancement.

4. **Backward compatibility is required** — Existing artifacts/calculations.json must remain loadable by existing tests.

5. **CalculationResult remains unchanged** — New MemoryEntry class is added, not refactoring existing code to reduce risk and test impact.

## Test Coverage Priorities

When tests are written, prioritize:
1. **Successful calculation serialization/deserialization** — matches current behavior
2. **Failed calculation handling** — new, represents error state
3. **Backward compatibility** — old JSON loads correctly as successful entries
4. **Field validation** — error_message should be None when success=True
5. **JSON format** — produced JSON is valid and readable

## Files to Create/Modify

### Create
- `src/models/memory_entry.py` — MemoryEntry class definition

### Potentially Modify (in later tasks)
- `src/storage/json_storage.py` or new `src/storage/memory_entry_storage.py` — if integration with storage is required
- `src/models/__init__.py` — to export MemoryEntry
- Tests — to validate MemoryEntry behavior

### Do NOT Modify (for compatibility)
- `src/models/calculation_result.py` — keep existing
- Existing test files — don't require changes to pass this task
- `artifacts/class_diagram.puml` — updated by UML designer in later step
