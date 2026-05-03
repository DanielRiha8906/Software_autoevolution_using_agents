# Task 03 Analysis: MemoryEntry Class for Calculator History

## Task Summary

Implement a dedicated `MemoryEntry` class to replace (or wrap) the current `CalculationResult` for history data. The new class must:
1. Capture everything about a single calculation attempt (operation name, input operands, result, success/error state, execution timestamp, execution time)
2. Support both successful and failed calculations
3. Be JSON-serializable and deserializable
4. Have a unique identifier
5. Avoid presentation/formatting logic
6. Maintain backward compatibility with existing calculation history
7. Be accessible via CLI (both interactive menu and one-shot flags)

## Current Architecture Analysis

### Current History Mechanism
- `CalculationResult` dataclass (src/models/calculation_result.py) stores completed calculations
- Fields: `operation` (str), `operand_a` (float), `operand_b` (float), `result` (float), `timestamp` (str), `execution_time_ms` (float)
- Only successful calculations are stored (errors raise ValueError in Calculator and are caught before saving)
- JsonStorage (src/storage/json_storage.py) serializes/deserializes to/from JSON via `to_dict()` and `from_dict()`
- CalculatorCLI displays history via `_show_history()` which calls `service.get_history()` and prints each entry

### Existing Code Structure
- `src/models/calculation_result.py` — Contains CalculationResult dataclass with `to_dict()`, `from_dict()`, `__str__()`
- `src/services/calculator_service.py` — Performs calculations and saves successful results only
- `src/storage/json_storage.py` — Handles all persistence via CalculationResult.to_dict() / from_dict()
- `src/cli/calculator_cli.py` — Shows history in `_show_history()` method
- `src/__main__.py` — Entry point with argparse (no history-specific flags currently)

### Test Coverage
- test_calculator_service.py: 73 tests covering perform() and get_history()
- test_execution_time_feature.py: 84 tests for execution_time_ms field
- test_json_storage.py: 6 tests for save/load round-trips
- test_cli.py: 11 tests including history display

## Key Findings

1. **Current Limitation**: Only successful calculations are stored. Failed operations (divide by zero, sqrt of negative, modulo by zero) raise exceptions before being saved.

2. **CalculationResult is Already History-Like**: The dataclass already has operation name, operands, result, timestamp, and execution_time_ms. It functions as the history entry.

3. **No Unique Identifiers Currently**: CalculationResult has no ID field. Two identical calculations at different times have no distinguishing identifier.

4. **Formatting is Mixed Into CalculationResult**: The `__str__()` method uses `_SYMBOLS` dict for presentation. This violates the "keep presentation logic out" requirement.

5. **Error State Not Tracked**: There is no error/success state field. Only successful calculations exist in history.

6. **JSON Round-Trip Already Works**: CalculationResult.to_dict() and from_dict() handle JSON serialization.

## Ambiguities and Working Assumptions

**Ambiguity 1: MemoryEntry vs. CalculationResult**
- Are these two separate classes (MemoryEntry for history, CalculationResult for service layer)?
- Or does MemoryEntry replace CalculationResult entirely?
- **Assumption**: They are separate. MemoryEntry is the history record (with ID, error state). CalculationResult is the service layer's return type. Storage layer converts between them.

**Ambiguity 2: How to Capture Failed Calculations?**
- Task says "Both successful and failed calculations can be represented"
- Current system doesn't save failed operations
- **Assumption**: CalculatorService must be modified to catch calculation errors and save them as MemoryEntry with error state set, before re-raising.

**Ambiguity 3: Unique Identifier Strategy**
- UUID v4? Incrementing counter? Timestamp-based?
- **Assumption**: UUID4 (most robust, no collision risk, no state management needed)

**Ambiguity 4: CLI Interface for History**
- Task says "accessible via CLI ... both as interactive menu option and as one-shot flag"
- Interactive menu already has "View history" (option 9)
- Does "one-shot flag" mean `python -m src --show-history` or something else?
- **Assumption**: Add a `--show-history` or `--history` flag to display all recorded entries (success and failure). Keep existing interactive "View history" menu option.

**Ambiguity 5: Backward Compatibility**
- Existing calculations.json has CalculationResult-shaped data (no ID, no error field)
- **Assumption**: MemoryEntry.from_dict() must handle both old format (set ID=None or auto-generate, default error=False) and new format seamlessly.

## Scope Signals

### In Scope
- New `MemoryEntry` class with required fields
- UUID or unique ID generation
- Success/error state tracking
- JSON serialization/deserialization
- Modification to CalculatorService to catch and record errors
- CLI flag and menu option for viewing history
- Tests for MemoryEntry serialization
- Tests for error capture in service

### Out of Scope
- Refactoring CalculationResult (keep it as-is for backward compatibility during transition)
- Querying/reporting on history (only access is "show all")
- Persistent ID generation strategy (use UUID to avoid state)
- GUI or graphical features

### Borderline
- Whether old JSON files are automatically migrated vs. read as-is with defaults

## Required Changes

### 1. New File: `src/models/memory_entry.py`
**Purpose**: Define MemoryEntry class

**Expected Structure**:
```python
@dataclass
class MemoryEntry:
    id: str                    # unique identifier (UUID)
    operation: str             # operation name
    operand_a: float           # first operand
    operand_b: float           # second operand
    result: float | None       # result (None if error)
    timestamp: str             # ISO timestamp
    execution_time_ms: float   # execution time
    success: bool              # True if no error
    error_message: str | None  # error message if success=False
    
    def to_dict(self) -> dict
    @classmethod
    def from_dict(cls, data: dict) -> MemoryEntry
```

### 2. Modify: `src/models/__init__.py`
Export new MemoryEntry class

### 3. Modify: `src/services/calculator_service.py`
- Wrap Calculator.calculate() in try/except to catch errors
- Create MemoryEntry with success=False and error message on exception
- Save failed entries to storage (likely via a new method or flag)
- Return MemoryEntry instead of CalculationResult (or keep returning CalculationResult for backward compatibility, add separate get_memory_history())

### 4. Modify: `src/storage/json_storage.py`
- Rename save() to save_calculation() or add new save_entry(memory_entry)
- Update load_all() to handle both CalculationResult and MemoryEntry formats
- Add load_all_entries() method to return MemoryEntry objects

### 5. Modify: `src/cli/calculator_cli.py`
- Add `--show-history` or `--history` flag support (how? currently no argparse in CLI class)
- OR modify __main__.py to add flag and pass to CLI
- Update interactive history display to show success/error state and error messages

### 6. Modify: `src/__main__.py`
- Add `--show-history` CLI flag
- Call cli.show_history() if flag is set
- Update help text

### 7. Tests
- test_memory_entry.py: serialization, deserialization, unique IDs
- Modify test_calculator_service.py: test error capture and storage
- Modify test_cli.py: test history display with success/error states

## File Inventory

| File | Purpose | Type | Modify? |
|------|---------|------|---------|
| src/models/calculation_result.py | Current history record class | Dataclass | Keep as-is |
| src/models/operation.py | Operation enum (add, subtract, ..., square, sqrt, power, modulo) | Enum | No |
| src/models/__init__.py | Model exports | Exports | Yes (add MemoryEntry) |
| src/models/memory_entry.py | **NEW** — History entry with ID, success state, error message | Dataclass | Create |
| src/services/calculator.py | Arithmetic operations | Methods | No |
| src/services/calculator_service.py | Orchestration + timing + persistence | Service | Yes (error handling) |
| src/services/__init__.py | Service exports | Exports | No |
| src/storage/json_storage.py | JSON persistence | Storage | Yes (MemoryEntry support) |
| src/storage/__init__.py | Storage exports | Exports | No |
| src/cli/calculator_cli.py | Interactive + one-shot CLI | CLI | Yes (history display) |
| src/cli/__init__.py | CLI exports | Exports | No |
| src/__main__.py | Entry point + argparse | Entry point | Yes (add --show-history) |
| src/__init__.py | Package exports | Exports | No |

## Suggested Priorities

1. **Create MemoryEntry class** — Foundation for all other changes. Highest priority because everything builds on it.

2. **Update CalculatorService to catch and record errors** — Changes the service contract. Moderate-high priority because it affects how results are returned.

3. **Update JsonStorage to handle MemoryEntry** — Required for persistence. Moderate priority because it depends on MemoryEntry being defined.

4. **Add CLI flag for --show-history** — User-facing feature. Moderate priority because the interactive menu already works.

5. **Update history display in CLI** — Cosmetic but expected. Low-moderate priority.

6. **Write tests** — Validates everything. Should be done throughout, not last.

---

## Summary for System Architect

The task requires introducing a `MemoryEntry` class as the canonical history record type. Key design decisions:

- MemoryEntry is separate from CalculationResult; the service layer likely uses MemoryEntry internally for history while CalculationResult remains the return type for backward compatibility.
- UUID is the safest unique ID strategy (no collision, no state).
- Error capture requires wrapping Calculator.calculate() in try/except in CalculatorService.
- Storage layer must be updated to serialize/deserialize MemoryEntry (with backward compatibility for old CalculationResult format).
- CLI needs a new --show-history flag and the interactive menu should be updated to show error state.

All new functionality must be exposed via `python -m src` (flag + interactive menu option).
