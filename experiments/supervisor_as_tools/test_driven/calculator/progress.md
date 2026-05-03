# Progress Log

## Task 01: Execution Time Tracking for CalculationResult

### Summary
Implemented execution time tracking for calculation results while preserving existing behavior. Each calculation result now exposes elapsed execution time in milliseconds.

### Files Changed
- `src/models/calculation_result.py` - Added `execution_time_ms` field with default 0.0, updated `from_dict()` for backward compatibility
- `src/services/calculator_service.py` - Implemented timing measurement using `time.perf_counter()` around `calculator.calculate()` call
- `artifacts/class_diagram.puml` - Updated CalculationResult class to reflect new field

### Test Results
- All 38 tests passed
- No existing tests broken
- Implementation satisfies all requirements:
  - CalculationResult has execution_time_ms attribute
  - Field is numeric (float) and non-negative
  - Service automatically populates it during perform()
  - Serialization (to_dict/from_dict) includes field
  - Backward compatible with old JSON records (default 0.0)

### Implementation Details
- Used `time.perf_counter()` for high-precision timing
- Timing measured only for `calculator.calculate()` call
- Elapsed time rounded to 2 decimal places for readability
- Field defaults to 0.0 for backward compatibility
- No new dependencies (Python standard library only)

Duration: 198.6s | Cost: $0.364763 USD | Turns: 22

## Task 02: Extended Calculator Operations (square, sqrt, power, modulo)

### Summary
Implemented four new mathematical operations for the Calculator class following test-driven development principles. All new functionality is accessible via both interactive menu and CLI flags.

### Files Changed
- `src/services/calculator.py` - Added square(), sqrt(), power(), modulo() methods
- `src/models/operation.py` - Added SQUARE, SQRT, POWER, MODULO enum values
- `src/cli/calculator_cli.py` - Extended _MENU with new operations
- `src/__main__.py` - Updated argparse to support new operations
- `tests/test_calculator.py` - Added 11 new test cases (+ 1 regression test)
- `tests/test_cli.py` - Updated menu indices to account for expanded menu
- `artifacts/class_diagram.puml` - Updated Calculator and Operation definitions

### Test Results
- All 48 tests passed
- New tests: 11 test cases covering square, sqrt, power, modulo operations
- Existing tests: All 12 original tests still pass
- CLI tests: 26 tests (updated for expanded menu structure)
- Service tests: All service integration tests pass

### Implementation Details
- square(x) returns x² using Python's ** operator
- sqrt(x) returns √x using math.sqrt(), raises ValueError for negative input
- power(x, y) returns x^y, supports fractional and negative exponents
- modulo(x, y) returns x % y, raises ValueError when y == 0
- All operations follow same method signature style as existing operations
- Error handling via raised exceptions (no sentinel values)
- Dispatch mechanism updated to handle unary/binary operations uniformly

### Accessibility
- Interactive mode: New operations appear as menu options 5-8 (Square Root, Power, Modulo, Square)
- CLI mode: `python -m src --operation square 4 0` → 16
- Error handling: `python -m src --operation sqrt -- -1` → Error (negative sqrt)
- All operations support both integer and floating-point operands

Duration: 278.4s | Cost: $0.567642 USD | Turns: 32
