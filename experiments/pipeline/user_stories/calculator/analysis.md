# Analysis: Add Execution Time Tracking to CalculationResult

## Task Summary
Add automatic execution time measurement to each calculation. The `CalculationResult` class must record how long each operation took (in milliseconds) without requiring manual input and using only the Python standard library.

## Current Implementation

### CalculationResult (src/models/calculation_result.py)
- Currently a dataclass with 5 fields:
  - `operation: str` (operation name, e.g., "add")
  - `operand_a: float`, `operand_b: float` (inputs)
  - `result: float` (computed output)
  - `timestamp: str` (ISO format, auto-populated in `__post_init__`)
- Has `to_dict()` and `from_dict()` methods for serialization
- Has `__str__()` for display formatting

### Calculation Flow
1. **CalculatorService.perform()** (src/services/calculator_service.py, lines 12-21)
   - Calls `Calculator.calculate(op, a, b)` to get raw result
   - Creates `CalculationResult` instance with operation, operands, and result
   - Saves to storage immediately
   - Returns the result to caller

2. **Calculator.calculate()** (src/services/calculator.py, lines 19-28)
   - Dispatches to operation-specific methods (add, subtract, multiply, divide)
   - Each method performs the arithmetic
   - Execution happens here, but timing is not tracked

3. **Storage & Retrieval**
   - JsonStorage uses `to_dict()` → JSON file → `from_dict()` round-trip
   - Tests construct CalculationResult directly with explicit values
   - CLI displays results and history

## What Must Change

### Primary Changes
1. **CalculationResult** — add `execution_time_ms: float` field with default=0.0
   - Must be optional in `__init__` for backward compatibility with direct construction
   - Should be included in `to_dict()` and deserialized from `from_dict()`
   - Consider whether to display in `__str__()` (not specified in requirements)

2. **CalculatorService.perform()** — wrap calculation with timing
   - Use `time.perf_counter()` (standard library, high-resolution clock)
   - Measure wall time around `Calculator.calculate()` call
   - Pass computed execution time to CalculationResult constructor

### Backward Compatibility Constraints
- **Direct construction**: Tests create CalculationResult with positional args: `CalculationResult("add", 3, 5, 8, _TS)`. Adding a new field will break unless it has a default value.
- **JSON round-trip**: Old calculation records in storage will not have `execution_time_ms` key. The `from_dict()` method must handle missing keys gracefully.
- **Existing tests**: 38 existing tests must continue to pass. Tests that directly construct CalculationResult will still work if the new field has a default.

## Implementation Details

### Timing Mechanism
- Use `time.perf_counter()` (available in standard library since Python 3.3)
- Capture time before and after `Calculator.calculate()` call
- Convert elapsed seconds to milliseconds: `(end - start) * 1000`
- Precision: microsecond-level accuracy, sufficient for profiling

### Field Ordering in CalculationResult
Current order: operation, operand_a, operand_b, result, timestamp
- Adding execution_time_ms as 6th field with default maintains backward compatibility
- Existing positional-arg construction (`CalculationResult("op", a, b, r, ts)`) will work because new field is last with a default

### Serialization Implications
- `asdict()` will include execution_time_ms in JSON output
- `from_dict()` will fail if key is missing (dict unpacking with `**data`)
- Must add handling: check if key exists, use 0.0 as fallback, or modify `from_dict()` signature

### Division by Zero Handling
- `Calculator.divide()` raises ValueError before calculation completes
- No timing needed for failed operations (correct behavior per existing test expectations)
- CalculatorService.perform() does not save on exception, so no CalculationResult created

## Ambiguities and Assumptions

1. **Display in __str__()**: Requirements don't specify whether execution_time_ms should appear in string representation. Assumption: not required initially; can be added in UI without changing core model.

2. **Precision level**: No specification on decimal places. Assumption: store as float milliseconds with Python's default repr.

3. **Measurement scope**: Time includes only the arithmetic operation (Calculator.calculate() call), not JSON serialization or other overhead. This aligns with the profiling intent stated in requirements.

## File Changes Summary

| File | Change Type | Details |
|------|-------------|---------|
| src/models/calculation_result.py | Modify | Add `execution_time_ms: float = 0.0` field; update `from_dict()` to handle missing key |
| src/services/calculator_service.py | Modify | Wrap `Calculator.calculate()` with `time.perf_counter()` timing; pass elapsed time to CalculationResult |
| src/services/calculator.py | No change | Calculation logic unaffected |
| src/storage/json_storage.py | No change | Serialization via to_dict/from_dict works transparently |
| src/cli/calculator_cli.py | No change | Display unaffected (unless execution_time_ms shown in UI later) |
| tests/*.py | No change | Existing tests pass with default 0.0 for execution_time_ms |

## Scope Signals

**In Scope:**
- Adding execution_time_ms attribute to CalculationResult
- Automatic timing in CalculatorService.perform()
- Backward compatibility for direct CalculationResult construction
- Backward compatibility for JSON deserialization

**Out of Scope:**
- Modifying Calculator methods to be aware of timing
- Changing display/UI to show execution time
- Performance optimization of operations
- Statistical analysis of timing data

**Borderline:**
- Whether CLI should display execution_time_ms in output (current __str__() only shows calculation, not metadata)
