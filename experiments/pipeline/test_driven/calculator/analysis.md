# Task 02: Add Advanced Mathematical Operations — Analysis Report

## Task Summary

Add four new mathematical methods to the Calculator class: `square(x)`, `sqrt(x)`, `power(x, y)`, and `modulo(x, y)`. These methods must be integrated into the existing operation dispatch system, exposed via CLI, and supported by comprehensive test coverage.

**Test Suite Requirements (from task description):**
- `square(4) == 16`, `square(0) == 0`
- `sqrt(9) ≈ 3.0`, `sqrt(-1)` raises `Exception`
- `power(2, 10) == 1024`, `power(8, 1/3) ≈ 2.0`, `power(2, -1) ≈ 0.5`
- `modulo(10, 3) == 1`, `modulo(10, 0)` raises `Exception`
- Existing operations (add, subtract, multiply, divide) must remain unchanged and still work

---

## Current State Analysis

### 1. Calculator Implementation (src/services/calculator.py)

**Current methods:**
- `add(a: float, b: float) -> float` — addition
- `subtract(a: float, b: float) -> float` — subtraction
- `multiply(a: float, b: float) -> float` — multiplication
- `divide(a: float, b: float) -> float` — division with zero check
- `calculate(operation: Operation, a: float, b: float) -> float` — dispatch method

**Status:** The class currently supports only 4 binary operations (ADD, SUBTRACT, MULTIPLY, DIVIDE). No unary operations or advanced mathematical functions exist.

**Constraints:**
- The `calculate()` method uses a dispatch dictionary keyed by `Operation` enum members
- All current methods accept exactly 2 operands
- `divide()` raises `ValueError("Division by zero is not allowed")` for division by zero

### 2. Operation Enum (src/models/operation.py)

**Current members:**
```python
ADD = "add"
SUBTRACT = "subtract"
MULTIPLY = "multiply"
DIVIDE = "divide"
```

**Methods:**
- `from_string(value: str) -> Operation` — parses string to enum member
- `display_name() -> str` — returns capitalized operation name

**Status:** Enum supports only 4 operations. Adding new operations requires extending this enum.

### 3. CalculationResult Model (src/models/calculation_result.py)

**Current fields:**
```python
@dataclass
class CalculationResult:
    operation: str         # operation name
    operand_a: float       # first operand
    operand_b: float       # second operand
    result: float          # result value
    timestamp: str         # ISO format timestamp
    execution_time_ms: float  # execution time in milliseconds (Task 01)
```

**Status:** All fields use generic float types and string operation names. The model supports arbitrary operations without modification.

**Serialization:** Uses `asdict()` and `from_dict()` for JSON round-tripping. Will transparently handle new operations.

### 4. CLI Integration (src/cli/calculator_cli.py)

**Current menu:**
```python
_MENU: list[tuple[Operation, str]] = [
    (Operation.ADD,      "Add"),
    (Operation.SUBTRACT, "Subtract"),
    (Operation.MULTIPLY, "Multiply"),
    (Operation.DIVIDE,   "Divide"),
]
```

**Interactive mode:**
- Prompts for two operands (a, b) for the selected operation
- Displays result and saves to history

**One-shot mode:**
- `python -m src --operation <op> <a> <b>`
- Currently accepts: `add`, `subtract`, `multiply`, `divide`

**Status:** Menu is hard-coded to 4 operations. New operations must be added to `_MENU` list and CLI argument parser.

### 5. CLI Entry Point (src/__main__.py)

**Argument parser configuration:**
```python
parser.add_argument(
    "--operation",
    metavar="OP",
    choices=["add", "subtract", "multiply", "divide"],
    help="Operation to perform (add | subtract | multiply | divide)",
)
```

**Status:** The `choices` list is hard-coded to the 4 current operations. New operations must be added here.

### 6. CalculatorService (src/services/calculator_service.py)

**Current flow in `perform()` method:**
1. Measure execution time
2. Call `calculator.calculate(operation, a, b)`
3. Create `CalculationResult` with all fields including `execution_time_ms`
4. Save to storage
5. Return result

**Status:** Generic and operation-agnostic. No changes needed for new operations.

### 7. Test Coverage (tests/test_calculator.py)

**Current test count:** 12 tests for Calculator class
- Basic tests: add, subtract, multiply, divide
- Edge cases: negative numbers, floats, division by zero
- Dispatch test: `calculate()` with all 4 operations

**Status:** No tests exist for the new methods. Test coverage will need to be significantly expanded.

---

## Files That Need Modification

### 1. src/models/operation.py — **REQUIRED**

**Changes needed:**
- Add four new enum members: `SQUARE`, `SQRT`, `POWER`, `MODULO`
- Each member must have a string value matching the operation name

**Current enum:**
```python
class Operation(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
```

**Required enum additions:**
```python
SQUARE = "square"
SQRT = "sqrt"
POWER = "power"
MODULO = "modulo"
```

**No changes needed to methods:**
- `from_string()` will automatically handle new values
- `display_name()` will work for all operations

### 2. src/services/calculator.py — **REQUIRED**

**Methods to add:**

#### `square(x: float) -> float`
- Mathematical function: x²
- Expected behavior: `square(4) == 16`, `square(0) == 0`
- Implementation: `return x * x` or `return x ** 2`
- Handles negative inputs: `square(-3) == 9` (squared negatives become positive)

#### `sqrt(x: float) -> float`
- Mathematical function: √x (square root)
- Expected behavior: `sqrt(9) ≈ 3.0`
- Edge case: `sqrt(-1)` must raise an `Exception`
- Implementation: Use `math.sqrt()` from Python standard library
- Must guard against negative inputs with an explicit check

#### `power(x: float, y: float) -> float`
- Mathematical function: x^y (x to the power of y)
- Expected behaviors:
  - `power(2, 10) == 1024` (integer exponents)
  - `power(8, 1/3) ≈ 2.0` (fractional exponents, cube root of 8)
  - `power(2, -1) ≈ 0.5` (negative exponents, reciprocals)
- Implementation: `return x ** y` (Python's built-in power operator)
- Note: Unlike `sqrt()`, negative bases with fractional exponents may produce complex numbers (out of scope; use `x ** y` directly)

#### `modulo(x: float, y: float) -> float`
- Mathematical function: x mod y (remainder of division)
- Expected behavior: `modulo(10, 3) == 1` (10 % 3 = 1)
- Edge case: `modulo(10, 0)` must raise an `Exception`
- Implementation: `return x % y`
- Must guard against division by zero

**Dispatch table update:**

The `calculate()` method currently uses a dispatch dictionary:
```python
dispatch = {
    Operation.ADD: self.add,
    Operation.SUBTRACT: self.subtract,
    Operation.MULTIPLY: self.multiply,
    Operation.DIVIDE: self.divide,
}
```

**Problem:** The new methods (`square`, `sqrt`, `power`, `modulo`) have different signatures:
- `square()` and `sqrt()` are **unary** (take 1 operand, but caller passes 2)
- `power()` and `modulo()` are **binary** (take 2 operands, same as existing operations)

**Solution:** The dispatch must handle both unary and binary operations. Two approaches are possible:

**Option A: Always pass two arguments; unary operations ignore the second**
```python
def calculate(self, operation: Operation, a: float, b: float) -> float:
    dispatch = {
        Operation.ADD: self.add,
        Operation.SUBTRACT: self.subtract,
        Operation.MULTIPLY: self.multiply,
        Operation.DIVIDE: self.divide,
        Operation.SQUARE: self.square,
        Operation.SQRT: self.sqrt,
        Operation.POWER: self.power,
        Operation.MODULO: self.modulo,
    }
    if operation not in dispatch:
        raise ValueError(f"Unsupported operation: {operation}")
    return dispatch[operation](a, b)
```

This means:
- `square()` and `sqrt()` must accept `(a, b)` but only use `a`
- Caller must always provide two operands (second is ignored for unary ops)
- This maintains CLI interface consistency (always prompt for 2 numbers)

**Option B: Use method inspection to detect unary vs. binary (more complex)**
```python
# Check function signature and call accordingly
# Less straightforward; not recommended
```

**Recommendation:** Option A is simpler, more maintainable, and keeps the CLI unchanged. Unary operations will have `b` passed but unused.

**Update `calculate()` to include new dispatch entries:**
```python
dispatch = {
    Operation.ADD: self.add,
    Operation.SUBTRACT: self.subtract,
    Operation.MULTIPLY: self.multiply,
    Operation.DIVIDE: self.divide,
    Operation.SQUARE: self.square,
    Operation.SQRT: self.sqrt,
    Operation.POWER: self.power,
    Operation.MODULO: self.modulo,
}
```

### 3. src/cli/calculator_cli.py — **REQUIRED**

**Update the _MENU list:**
```python
_MENU: list[tuple[Operation, str]] = [
    (Operation.ADD,      "Add"),
    (Operation.SUBTRACT, "Subtract"),
    (Operation.MULTIPLY, "Multiply"),
    (Operation.DIVIDE,   "Divide"),
    (Operation.SQUARE,   "Square"),
    (Operation.SQRT,     "Square Root"),
    (Operation.POWER,    "Power"),
    (Operation.MODULO,   "Modulo"),
]
```

**Impact on interactive mode:**
- Menu will now show 8 options instead of 4
- History option will move from `len(self._MENU) + 1` to index 9
- Exit option will move to index 10
- Menu numbering: all automatic via `enumerate(self._MENU, 1)`

**Impact on one-shot mode:**
- No changes needed to `run_command()` — it delegates to `Operation.from_string()`
- Input parsing remains the same — always expects 2 operands

**Potential UX consideration (unary operations):**
- For `square` and `sqrt`, the caller provides two operands but only the first is used
- Example: `python -m src --operation square 4 99` — the `99` is ignored
- This is consistent but may confuse users
- **Alternative:** Modify CLI to accept variable operand counts (more complex; not required by task description)

### 4. src/__main__.py — **REQUIRED**

**Update argument choices:**
```python
parser.add_argument(
    "--operation",
    metavar="OP",
    choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"],
    help="Operation to perform (add | subtract | multiply | divide | square | sqrt | power | modulo)",
)
```

**Update usage string:**
```python
usage="python -m src [--operation {add,subtract,multiply,divide,square,sqrt,power,modulo} A B]",
```

**No changes needed to:**
- Argument parsing logic
- Operand count validation (always expects exactly 2)
- Error handling

### 5. tests/ — **NOT DIRECTLY REQUIRED FOR TASK 02**

**Note:** The task description states "test suite provided," implying tests will be created separately. As data analyst, I am **not** writing tests (per role boundaries), but the following test structure is expected:

**Expected test file: tests/test_advanced_operations.py (or expansion of test_calculator.py)**

Tests for each operation:
- `square()`: basic cases, edge cases (0, negative)
- `sqrt()`: basic case, error case (negative input)
- `power()`: integer exponents, fractional exponents, negative exponents
- `modulo()`: basic case, error case (divisor = 0)

Tests for integration:
- `calculate()` dispatch works for new operations
- `CalculatorService.perform()` works with new operations
- CLI accepts new operation names

### 6. src/models/calculation_result.py — **NO CHANGES REQUIRED**

The `CalculationResult` dataclass generically stores:
- `operation: str` — operation name (e.g., "square", "sqrt")
- `operand_a: float` — first operand
- `operand_b: float` — second operand
- `result: float` — result value

For unary operations:
- `operand_a` = the actual input (e.g., for `sqrt(9)`: operand_a=9)
- `operand_b` = unused but stored (can be 0, None placeholder, or any value)
- Serialization will include both operands

This is semantically imperfect (storing unused operand_b) but requires no changes.

---

## Test Requirements Summary

### Basic Functionality Tests

**square()**
```
square(4) == 16
square(0) == 0
square(-3) == 9 (implicit from algebra)
square(0.5) == 0.25
```

**sqrt()**
```
sqrt(9) == 3.0 (or approx 3.0)
sqrt(0) == 0.0
sqrt(-1) raises Exception  [CRITICAL]
sqrt(0.25) == 0.5
```

**power()**
```
power(2, 10) == 1024
power(8, 1/3) ≈ 2.0  (cube root of 8)
power(2, -1) ≈ 0.5   (1/2)
power(5, 0) == 1.0   (any number to power 0 is 1)
power(0, 2) == 0.0   (0 squared is 0)
```

**modulo()**
```
modulo(10, 3) == 1
modulo(10, 0) raises Exception  [CRITICAL]
modulo(7, 7) == 0
modulo(5, 10) == 5  (remainder when 5 < divisor)
```

### Integration Tests

**Calculator.calculate() dispatch:**
- `calculate(Operation.SQUARE, 4, _) == 16`
- `calculate(Operation.SQRT, 9, _) ≈ 3.0`
- `calculate(Operation.POWER, 2, 10) == 1024`
- `calculate(Operation.MODULO, 10, 3) == 1`

**CalculatorService.perform():**
- All new operations can be passed through the service layer
- Results are stored with correct operation names
- Execution time is tracked

**CLI integration:**
- `python -m src --operation square 4` → prints result
- `python -m src --operation sqrt 9` → prints result
- Interactive menu shows all 8 operations
- `Operation.from_string()` recognizes new operation names

---

## Edge Cases and Error Handling

### sqrt() Negative Input
- **Requirement:** `sqrt(-1)` must raise an Exception
- **Type:** Likely `ValueError` (matches pattern of `divide(_, 0)`)
- **Message:** Suggest something like "Cannot compute square root of negative number"

### modulo() Divisor Zero
- **Requirement:** `modulo(10, 0)` must raise an Exception
- **Type:** Likely `ValueError` (matches pattern of `divide(_, 0)`)
- **Message:** Suggest something like "Modulo by zero is not allowed"

### power() with Fractional Exponents
- **No error handling needed:** Python's `**` operator handles fractional exponents natively
- `power(8, 1/3)` will compute the cube root without exception

### Floating-Point Precision
- Tests for `sqrt()` and `power()` with fractional exponents should use `pytest.approx()` for comparisons
- Example: `assert result ≈ 2.0` for `power(8, 1/3)`

---

## Backward Compatibility Considerations

1. **Existing operations unchanged:** All 4 current operations remain untouched in signature and behavior
2. **CalculationResult semantics:** New operations will have `operand_b` set (even for unary ops); this is non-breaking
3. **CLI behavior:** Users expecting only 4 operations will see expanded menu; this is additive, not breaking
4. **Serialization:** New operations will serialize/deserialize transparently; old records remain valid

---

## Implementation Dependencies and Order

1. **Operation enum** (src/models/operation.py) — must come first (defines new enum members)
2. **Calculator methods** (src/services/calculator.py) — depends on Operation enum
3. **CLI menu and __main__.py** — depend on Operation enum
4. **Tests** — depend on all of the above

**Suggested implementation order:**
1. Add enum members to `Operation`
2. Implement the 4 new methods in `Calculator`
3. Update dispatch dictionary in `calculate()`
4. Update CLI menu in `CalculatorCLI`
5. Update argparse choices in `__main__.py`
6. Write and run tests

---

## Summary of Changes

| File | Change Type | Scope | Details |
|------|-------------|-------|---------|
| `src/models/operation.py` | Enum extension | Add 4 members | SQUARE, SQRT, POWER, MODULO |
| `src/services/calculator.py` | New methods + dispatch | Add 4 methods + update dict | `square()`, `sqrt()`, `power()`, `modulo()` + error handling |
| `src/cli/calculator_cli.py` | Menu expansion | Update _MENU | Add 4 new menu entries |
| `src/__main__.py` | CLI constraints | Update choices | Add new operation names to argparse |
| `tests/test_*.py` | Test coverage | New test file or expansion | ~20-30 new tests across all new operations |
| `src/models/calculation_result.py` | No changes | — | Works transparently with new operations |
| `src/services/calculator_service.py` | No changes | — | Works transparently with new operations |
| `src/storage/json_storage.py` | No changes | — | Serialization works transparently |

---

## Ambiguities and Assumptions

1. **Unary operation handling:** Assumed Option A (pass 2 args always; unary ops ignore second). CLI remains unchanged; user experience slightly inconsistent but simpler to implement.

2. **sqrt() error type:** Assumed `ValueError` matching the pattern of existing error handling, but `Exception` (more general) would also satisfy test requirement "raises Exception".

3. **modulo() with negative numbers:** Python's `%` operator works with negatives (e.g., `-10 % 3 == 2`). No special handling assumed; will use native Python semantics.

4. **power() and complex numbers:** Assumed no special handling for complex results (e.g., `power(-1, 0.5)` would yield a complex number). Python's `**` operator will handle this natively.

5. **Test file location:** Task says "test suite provided" but no test files exist yet. Assumed tests will be added as a separate step, not part of this analysis task.

---

## No Further Clarifications Needed

All requirements are explicit and implementable as stated. The constraint of supporting both unary and binary operations is manageable via the dispatch approach outlined above.
