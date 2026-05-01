# Analysis: Add Execution Time Tracking to Calculator

## Task Summary

Add an `execution_time_ms` attribute to the `CalculationResult` class to track how long each calculation takes (in milliseconds). The timing should be measured during actual calculation execution, set for every calculation, be reasonably accurate, follow naming conventions, and preserve backward compatibility. Use only built-in Python timing (no external libraries).

## Current Architecture

### CalculationResult Structure

**File**: `/src/models/calculation_result.py`

Current dataclass with 5 attributes:
- `operation: str` — operation name (e.g., "add")
- `operand_a: float` — first operand
- `operand_b: float` — second operand
- `result: float` — calculation result
- `timestamp: str` — ISO format timestamp, auto-generated in `__post_init__`

Key methods:
- `__post_init__()` — auto-generates timestamp if not provided
- `to_dict()` — serializes to dictionary using `asdict()`
- `from_dict()` — deserializes from dictionary using `cls(**data)`
- `__str__()` — formats result as readable string (e.g., "3 + 5 = 8")

### Calculation Execution Flow

**Primary calculation path** (line 12-21 in `calculator_service.py`):

1. `CalculatorService.perform()` is called with operation and operands
2. Calls `self.calculator.calculate(operation, a, b)` → returns float result
3. Creates `CalculationResult` with operation, operands, and computed result
4. Calls `self.storage.save(calc_result)` → persists to JSON
5. Returns `CalculationResult` to caller

**Calculation implementation** (in `calculator.py`):
- `Calculator.calculate()` dispatches to specific method (add/subtract/multiply/divide)
- Each method performs simple arithmetic (no intentional delay)
- Only `divide()` has control logic (zero-check raises ValueError)

**Storage** (in `json_storage.py`):
- `CalculationResult.to_dict()` converts object to dictionary
- Dictionary is appended to list and written to `artifacts/calculations.json`
- Deserialization uses `CalculationResult.from_dict()` to reconstruct objects

### Testing Patterns

**Test files**:
- `test_calculator.py` — unit tests for Calculator arithmetic methods
- `test_calculator_service.py` — tests CalculatorService.perform() and get_history()
- `test_json_storage.py` — tests JSON persistence
- `test_cli.py` — tests CLI interaction

**Key observations**:
- Tests use `MagicMock` for storage in service tests
- Tests instantiate `CalculationResult` directly with hardcoded timestamp "2026-01-01T00:00:00"
- Tests verify result attributes: operation, operands, result, timestamp
- No current tests verify execution timing

## What Needs to Change

### 1. CalculationResult Class (`src/models/calculation_result.py`)

**Add new attribute**:
```
execution_time_ms: float = field(default=0.0)
```
- Type: `float` (milliseconds as decimal for sub-millisecond precision)
- Default: 0.0 (fallback for backward compatibility, but should always be set by service)
- Naming follows convention: `execution_time_ms` (not `exec_time`, `timing`, or `duration_ms`)

**Impact on serialization**:
- `to_dict()` will automatically include `execution_time_ms` via `asdict()`
- `from_dict()` will automatically accept it (with default if missing)
- **Backward compatibility**: Old JSON records lacking `execution_time_ms` will get 0.0 when loaded, allowing graceful upgrade

**Impact on `__str__()`**:
- Current implementation does not display execution time
- No change needed (execution_time_ms is internal/persisted, not user-facing display)

### 2. CalculatorService (`src/services/calculator_service.py`)

**Timing implementation location**: The `perform()` method is the orchestrator that:
1. Has access to the raw execution point
2. Controls the CalculationResult creation
3. Must wrap the calculation call

**Key implementation detail**:
- Import `time.perf_counter()` (built-in, highest resolution, monotonic)
- Measure time between calculator.calculate() call boundaries
- Convert nanoseconds/seconds to milliseconds: `(end - start) * 1000`

**Code structure**:
```python
def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
    start = time.perf_counter()
    result = self.calculator.calculate(operation, a, b)  # ← measure this
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    calc_result = CalculationResult(
        operation=operation.value,
        operand_a=a,
        operand_b=b,
        result=result,
        execution_time_ms=elapsed_ms,  # ← new parameter
    )
    self.storage.save(calc_result)
    return calc_result
```

**Error behavior**:
- If `calculator.calculate()` raises ValueError (division by zero), the exception propagates before result creation
- Timing is not recorded for failed calculations (current code already does not save failures)
- This is correct behavior per task requirements (only "every calculation" that succeeds)

### 3. Test Updates (`tests/`)

**Backward compatibility tests needed**:
- Test loading old JSON records without `execution_time_ms` field
- Verify `from_dict()` defaults to 0.0 gracefully
- Verify serialization includes `execution_time_ms`

**Calculator service tests**:
- Existing tests instantiate `CalculationResult` with hardcoded timestamp
- Must add `execution_time_ms=0.0` to all direct instantiations to match new signature
- Add assertions that returned results have `execution_time_ms > 0.0` (non-negative and non-zero for real calls)
- Add test verifying execution_time_ms is always set after perform()

**JSON storage tests**:
- Verify persisted JSON includes execution_time_ms field
- Verify round-trip: save with execution_time_ms, load, verify field preserved

**CLI tests**:
- No changes needed — CLI only calls service, doesn't directly instantiate CalculationResult
- Service returns results with execution_time_ms already set
- If CLI test fixtures create CalculationResult directly (for mocking), add execution_time_ms parameter

## Backward Compatibility Analysis

### Serialized JSON Format
**Current format** (artifacts/calculations.json):
```json
{
  "operation": "add",
  "operand_a": 3.0,
  "operand_b": 5.0,
  "result": 8.0,
  "timestamp": "2026-04-29T12:01:36.308310"
}
```

**New format**:
```json
{
  "operation": "add",
  "operand_a": 3.0,
  "operand_b": 5.0,
  "result": 8.0,
  "timestamp": "2026-04-29T12:01:36.308310",
  "execution_time_ms": 0.123
}
```

**Upgrade path**:
- Old JSON without `execution_time_ms` can still be loaded
- `from_dict()` uses `cls(**data)`, which allows missing fields with dataclass defaults
- Old records will have `execution_time_ms=0.0` when loaded
- New records will have accurate timing
- Mixed history (old + new) will work correctly

### Interface Compatibility
- `CalculatorService.perform()` signature unchanged (still returns CalculationResult)
- `CalculationResult` constructor will require new parameter or use default
- **Dataclass fields with defaults** must come after those without defaults
- Current order: operation, operand_a, operand_b, result, timestamp (last has default)
- New field: execution_time_ms (should also have default)
- **No breaking change** to callers passing positional args if we append with default

## Files to Modify

1. **src/models/calculation_result.py**
   - Add `execution_time_ms: float = field(default=0.0)` to dataclass
   - No changes to methods (auto-handled by dataclass machinery)

2. **src/services/calculator_service.py**
   - Import `time` module (built-in)
   - Wrap `calculator.calculate()` with `time.perf_counter()` timing
   - Pass `execution_time_ms` to CalculationResult constructor

3. **tests/test_calculator_service.py**
   - Update mock CalculationResult instantiations to include execution_time_ms
   - Add assertion that returned results have execution_time_ms >= 0
   - Add test for backward compatibility (loading old format)

4. **tests/test_json_storage.py**
   - Update mock CalculationResult instantiations to include execution_time_ms
   - Add test verifying execution_time_ms is persisted and loaded correctly
   - Add test for loading old JSON records without execution_time_ms

5. **tests/test_cli.py**
   - Update CalculationResult instantiations to include execution_time_ms (lines 17, 49, 76)

6. **tests/test_calculator.py**
   - No changes (only tests Calculator class, not CalculationResult creation)

## Ambiguities & Assumptions

### 1. What counts as "execution time"?
**Assumption**: Only the time spent in `Calculator.calculate()` method.
- Does NOT include: JSON serialization, storage I/O, CLI overhead
- Rationale: Task says "execution time" for "calculation results," implying only the arithmetic operation
- This is measured by wrapping the call in `CalculatorService.perform()`

### 2. Timing precision / unit choice
**Assumption**: Milliseconds as float (e.g., 0.123 ms for very fast operations)
- Task specifies: "execution_time_ms attribute (milliseconds)"
- Using `time.perf_counter()` (nanosecond resolution on Linux) and converting to ms gives adequate precision
- Alternative (nanoseconds) rejected because: task explicitly says "milliseconds"
- Alternative (integers) rejected because: Python integers would round very fast operations to 0, losing information

### 3. Failed calculations (division by zero)
**Assumption**: Do not record execution_time_ms for failed calculations.
- Division by zero raises ValueError before CalculationResult is created
- Current code does not persist failed calculations
- Task says "set for every calculation" — a failed calculation is arguably not "a calculation" (no result produced)
- This matches existing behavior (no special case needed)

### 4. Backward compatibility loading
**Assumption**: Missing `execution_time_ms` in loaded JSON defaults to 0.0.
- Dataclass field with `default=0.0` handles this automatically
- Allows old history to coexist with new records
- Does not require JSON migration script

## Scope Signals

### In Scope
- Adding execution_time_ms attribute to CalculationResult
- Measuring time in CalculatorService.perform()
- Persisting execution_time_ms to JSON
- Backward-compatible loading of old records
- Test coverage for timing and serialization

### Out of Scope (Won't)
- External timing libraries (task explicitly excludes)
- Complex timing scenarios (multi-threaded, async)
- Performance optimization of calculator methods
- Execution time display in CLI output (not requested)

### Borderline (Should Consider)
- Measuring time for CLI input/output overhead — out of scope (task is about calculation, not I/O)
- Reusable timing utility class — mentioned in "Could" section; simple wrapping in perform() is sufficient for now

## Priorities

1. **High**: Add `execution_time_ms` field to CalculationResult with default (prevents deserialization errors)
2. **High**: Implement timing in CalculatorService.perform() (core requirement)
3. **High**: Test that execution_time_ms is set on new calculations
4. **High**: Test backward compatibility (old JSON loads without errors)
5. **Medium**: Update all test instantiations of CalculationResult to include execution_time_ms
6. **Medium**: Verify JSON round-trip includes execution_time_ms
7. **Low**: Document the change in docstrings (optional, not requested)

## Summary of Implementation Strategy

**Minimal, non-breaking change**:
1. Add one dataclass field with a default (safe for deserialization)
2. Add 2-3 lines of timing code in one method
3. Update test fixtures to match new signature
4. Verify backward compatibility of JSON loading

**Expected outcome**:
- All new calculations have execution_time_ms set to measured time (milliseconds, float)
- Old history records load with execution_time_ms=0.0 (no errors)
- No changes to public APIs or CLI behavior
- 38 existing tests pass with minimal fixture updates
