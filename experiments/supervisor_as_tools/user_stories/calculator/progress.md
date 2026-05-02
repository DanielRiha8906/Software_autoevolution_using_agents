# Progress Log

## Task 01: Add execution_time_ms tracking to CalculationResult

**Objective:** Add automatic execution time measurement to calculation results for performance profiling.

**Acceptance Criteria:** ✅ All met
- `CalculationResult` has an `execution_time_ms` attribute representing elapsed time in milliseconds
- The attribute is populated automatically for every calculation — no manual input required
- Measurement uses only the standard library (no third-party timing packages)
- Existing code that constructs or reads `CalculationResult` continues to work without changes

**Files Changed:**
- `src/models/calculation_result.py` — Added `execution_time_ms: float` field with default 0.0; updated `from_dict()` for backward compatibility
- `src/services/calculator_service.py` — Added timing measurement using `time.perf_counter()` around calculation
- `tests/test_calculator_service.py` — Enhanced 5 existing tests with execution_time_ms assertions; added 2 new tests
- `tests/test_json_storage.py` — Enhanced 1 existing test; added 2 new backward-compatibility tests
- `artifacts/class_diagram.puml` — Added `executionTimeMs : float` field to CalculationResult class
- `artifacts/activity_diagram.puml` — Added timing measurement steps to flow diagram

**Test Results:**
- Total tests: 42
- Passed: 42 ✅
- Failed: 0
- Coverage: All operation types (ADD, SUBTRACT, MULTIPLY, DIVIDE) verified to measure execution time

**Implementation Notes:**
- Timing measures only Calculator.calculate() work, excludes JSON storage I/O
- Uses `time.perf_counter()` for high-precision wall-clock measurement
- Default value of 0.0 allows graceful loading of old JSON records without execution_time_ms
- No breaking changes to API; all existing code continues to work

Duration: 220.3s | Cost: $0.388252 USD | Turns: 13

---

## Task 02: Add square, sqrt, power, and modulo operations

**Objective:** Extend the calculator with advanced arithmetic operations beyond basic four-function math.

**Acceptance Criteria:** ✅ All met
- The following operations are available: `square(x)`, `sqrt(x)`, `power(x, y)`, `modulo(x, y)` ✅
- Each operation follows the same interface as existing operations ✅
- `sqrt` of a negative number raises an error ✅
- `modulo` by zero raises an error ✅
- `power` with negative or fractional exponents returns correct results ✅
- No existing operation is duplicated or renamed ✅

**Files Changed:**
- `src/models/operation.py` — Added SQUARE, SQRT, POWER, MODULO enum members (8 operations total)
- `src/models/calculation_result.py` — Made operand_b optional (`float | None = None`); updated `__str__()` to handle unary operations with mathematical symbols; extended _SYMBOLS dict
- `src/services/calculator.py` — Added square(a), sqrt(a), power(a, b), modulo(a, b) methods with error handling; refactored calculate() to accept varargs (*args) with arity validation
- `src/services/calculator_service.py` — Updated perform() signature to varargs; correctly constructs CalculationResult with operand_b=None for unary operations
- `src/cli/calculator_cli.py` — Updated _MENU structure to include arity (1 or 2); refactored run_interactive() to prompt based on arity; refactored run_command() to accept varargs
- `src/__main__.py` — Updated argparse to support all 8 operations; added dynamic operand count validation
- `artifacts/class_diagram.puml` — Updated Operation enum to show 8 members; added 4 new methods to Calculator class; made operand_b optional in CalculationResult; updated calculate() signature
- `tests/test_cli.py` — Fixed 7 failing tests (menu option updates); added 8 new tests covering square, sqrt, power, modulo in both interactive and one-shot modes

**Test Results:**
- Total tests: 50
- Passed: 50 ✅
- Failed: 0
- Coverage: All 8 operations tested (32 core calculator tests + 18 CLI/integration tests)
  - Core operations: square, sqrt (with negative error), power (negative/fractional exponents), modulo (with zero divisor error)
  - CLI: interactive menu and one-shot command-line modes for all operations
  - Edge cases: division by zero, sqrt of negative, modulo by zero, zero base with power

**Implementation Highlights:**
- Square and square root are unary operations (1 operand); power and modulo are binary (2 operands)
- Unary operations render with mathematical symbols: `5² = 25`, `√9 = 3`
- Binary operations use infix notation: `2 ^ 3 = 8`, `10 % 3 = 1`
- CLI menu expanded to 8 operations with arity-aware prompting
- Error messages are descriptive (e.g., "Square root of negative number", "Modulo by zero")
- No breaking changes; all existing operations and tests continue to pass

Duration: 446.0s | Cost: $0.778298 USD | Turns: 24
