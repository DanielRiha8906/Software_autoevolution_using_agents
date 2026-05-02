# Calculator Application Analysis: Task 02 - Add New Operations

**Date:** 2026-05-02  
**Task:** Add `square`, `sqrt`, `power`, and `modulo` operations to Calculator, following existing conventions.  
**Status:** Analysis Complete

---

## 1. Current Calculator Implementation

### Location and Current Methods

**File:** `src/services/calculator.py`

The `Calculator` class currently contains 5 methods:

```python
class Calculator:
    def add(self, a: float, b: float) -> float
    def subtract(self, a: float, b: float) -> float
    def multiply(self, a: float, b: float) -> float
    def divide(self, a: float, b: float) -> float
    def calculate(self, operation: Operation, a: float, b: float) -> float
```

### Existing Method Patterns

1. **Binary operations** (`add`, `subtract`, `multiply`, `divide`):
   - Accept two parameters: `a: float, b: float`
   - Return `float`
   - Raise `ValueError` for domain errors (division by zero)

2. **Dispatcher method** (`calculate`):
   - Accepts an `Operation` enum and two operands
   - Routes to appropriate method via dispatch dictionary
   - Raises `ValueError` if operation not in dispatch dictionary

### Key Implementation Details

- **Error handling pattern:** Uses `ValueError` with descriptive message (e.g., "Division by zero is not allowed")
- **Dispatch dictionary:** Located in `calculate()` method, maps `Operation` enum to methods
- **No return type annotations on divide:** Returns `float` implicitly

### CalculationResult Dataclass Integration

**File:** `src/models/calculation_result.py`

Current fields:
- `operation: str` — stored as operation enum value (e.g., "add", "divide")
- `operand_a: float`, `operand_b: float` — input operands
- `result: float` — calculation result
- `timestamp: str` — auto-populated by `__post_init__()`
- `execution_time_ms: float` — added in Task 01, has default 0.0

The `_SYMBOLS` dictionary maps operation strings to display symbols:
```python
_SYMBOLS = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}
```

New operations will need entries here for display in CLI and history.

### Operation Enum

**File:** `src/models/operation.py`

Current enum members:
```python
class Operation(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
```

Methods:
- `from_string(value: str)` — parses operation name from CLI input
- `display_name()` — returns capitalized operation name

---

## 2. What New Methods Must Be Added

### 2.1 Method Signatures (in Calculator class)

Four new methods required, following existing binary operation pattern:

```python
def square(self, a: float) -> float:
    """
    Returns the square of a number (a²).
    Single operand (unlike existing binary operations).
    Range: works for all real numbers.
    Exception: None (mathematically valid for all inputs).
    """

def sqrt(self, a: float) -> float:
    """
    Returns the square root of a number (√a).
    Single operand.
    Range: valid for non-negative numbers only.
    Exception: Must raise Exception (user prompt specifies generic Exception, not ValueError) for negative input.
    """

def power(self, a: float, b: float) -> float:
    """
    Returns a raised to the power b (a^b).
    Two operands (binary like existing operations).
    Supports: integer exponents, fractional exponents, negative exponents.
    Range: works for all combinations that Python's ** operator supports.
    Exception: None typically needed; Python handles edge cases internally.
    """

def modulo(self, a: float, b: float) -> float:
    """
    Returns a modulo b (a % b).
    Two operands (binary like existing operations).
    Range: valid when b != 0.
    Exception: Must raise Exception (user prompt specifies generic Exception) when b == 0.
    """
```

### 2.2 Key Design Observations

**Signature difference from existing operations:**
- `square(a)` and `sqrt(a)` are unary operations (single operand)
- `power(a, b)` and `modulo(a, b)` are binary operations (two operands, like existing methods)

**Implication for dispatcher:**
- Current `calculate()` method assumes all operations are binary (takes `a` and `b`)
- Unary operations cannot be dispatched through the current `calculate()` method
- Unary operations require direct method calls or a redesigned dispatcher

---

## 3. Edge Cases and Exception Requirements

### 3.1 square(x)

| Input | Behavior | Notes |
|-------|----------|-------|
| Positive | x² | Works for all positive reals |
| Zero | 0 | 0² = 0 |
| Negative | x² | Works mathematically (e.g., (-3)² = 9) |
| Floating-point | Works | No special handling needed |

**Exceptions:** None. All real inputs are valid.

### 3.2 sqrt(x)

| Input | Behavior | Exception |
|-------|----------|-----------|
| Positive (x > 0) | √x | Returns float |
| Zero (x == 0) | 0.0 | Returns float |
| Negative (x < 0) | — | **Must raise Exception** |

**Key requirement:** Test uses `pytest.raises(Exception)` — accepts any exception type (ValueError, TypeError, RuntimeError, or custom). Prompt says "must raise an exception."

### 3.3 power(x, y)

| Input | Behavior | Notes |
|-------|----------|-------|
| Integer exponent (y is int) | x^y | e.g., 2^10 = 1024 |
| Fractional exponent (y = p/q) | x^(p/q) | e.g., 8^(1/3) = 2.0 |
| Negative exponent (y < 0) | x^(-y) = 1/(x^y) | e.g., 2^(-1) = 0.5 |
| Zero exponent | x^0 = 1 | Standard behavior |
| Base zero | Depends on exponent | 0^0 is platform-specific; Python returns 1 |

**Exceptions:** None typically, unless Python's `**` operator raises (e.g., overflow). Prompt says "raise exceptions for domain errors in this task" but power() has no specified domain restrictions in the test suite.

**Implementation approach:** Use Python's built-in `**` operator:
```python
return a ** b
```

### 3.4 modulo(x, y)

| Input | Behavior | Exception |
|-------|----------|-----------|
| y != 0 | x % y | Returns float (or int if both inputs are int) |
| y == 0 | — | **Must raise Exception** |

**Key requirement:** Must raise exception when divisor (y) is zero, parallel to divide() which raises "Division by zero is not allowed."

**Implementation approach:** Check divisor before operation:
```python
if b == 0:
    raise ValueError("Modulo by zero is not allowed")
return a % b
```

---

## 4. Integration Points and Required Changes

### 4.1 Files That MUST Be Modified

#### 1. **src/services/calculator.py**
- Add four new method definitions: `square()`, `sqrt()`, `power()`, `modulo()`
- No changes to existing methods (`add`, `subtract`, `multiply`, `divide`, `calculate`)
- **Note on dispatcher:** Current `calculate()` method dispatch dictionary only handles binary operations. Unary operations (`square`, `sqrt`) will NOT be included in the dispatcher without redesign.

#### 2. **src/models/operation.py**
- Add four new enum members:
  ```python
  SQUARE = "square"
  SQRT = "sqrt"
  POWER = "power"
  MODULO = "modulo"
  ```
- No changes to `from_string()` or `display_name()` methods; they are generic and work for new members automatically

#### 3. **src/models/calculation_result.py**
- Add symbols for new operations in `_SYMBOLS` dictionary:
  ```python
  _SYMBOLS = {
      "add": "+",
      "subtract": "-",
      "multiply": "×",
      "divide": "÷",
      "square": "²",        # or similar
      "sqrt": "√",
      "power": "^",
      "modulo": "%"
  }
  ```
- **Consider:** `square()` and `sqrt()` are unary and return single operand. The `__str__()` method in CalculationResult currently formats as `a symbol b = r`. Unary operations will show as `a ² = r` (without a second operand), which may look odd but will work.

#### 4. **src/cli/calculator_cli.py**
- Add new operations to `_MENU` list:
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
- **Issue to consider:** The CLI assumes binary operations (prompts for two operands in `run_interactive()`). Unary operations (`square`, `sqrt`) will break the current interactive flow that always calls `service.perform(operation, a, b)` with two operands.
- **Design choice needed:** Either redesign CLI to handle unary vs binary operations, or exclude unary operations from the interactive menu (keep them CLI-only via `run_command()`).

### 4.2 Files That Need Tests

**File:** Tests already exist in prompt specification. Tests will be added by pytest-tester.

Current test count: 38 tests (all passing)
New tests: 9 tests provided in prompt (10 if counting `test_existing_operations_unchanged`)

**Test file likely location:** `tests/test_calculator.py` (extend TestCalculator class with new test methods)

### 4.3 Files That MAY Be Modified

#### CalculatorService
**File:** `src/services/calculator_service.py`

Current implementation:
- `perform(operation: Operation, a: float, b: float)` — always passes two operands
- Calls `calculator.calculate(operation, a, b)`

**Potential issue:** The dispatcher `calculate()` method in Calculator doesn't know about unary operations. If unary operations are to be dispatched through the service, either:
1. Update `calculate()` dispatcher to handle unary operations (redesign needed)
2. Skip service dispatch for unary operations (CLI must call methods directly)
3. Require unary operations to always pass a dummy second operand

**Current expectation:** Tests call `Calculator().square(4)` directly, not through the dispatcher, so no changes to CalculatorService may be needed.

---

## 5. Existing Tests to Verify No Regression

### Current Test Count
- **Total:** 38 tests across 5 test files
- **Status:** All passing

### Regression Risk Analysis

**Low risk for Calculator methods:**
- New methods are additions, not modifications
- Existing methods (`add`, `subtract`, `multiply`, `divide`) are unchanged
- Test `test_existing_operations_unchanged()` explicitly verifies this

**Test coverage by category:**

1. **test_calculator.py** (12 tests) — unit tests for Calculator class
   - Tests for each existing operation: `add`, `subtract`, `multiply`, `divide`
   - Tests edge cases: negative numbers, zero, floats
   - Tests dispatcher `calculate()` method
   - **Risk:** Low. No changes to existing Calculator methods.

2. **test_calculator_service.py** (9 tests) — integration tests for CalculatorService
   - Tests `perform()` with existing operations
   - Tests storage integration
   - Tests error handling (division by zero)
   - **Risk:** Low to Medium. If unary operations require service changes, may need new tests; otherwise no changes needed.

3. **test_cli.py** (4 + 6 = 10 tests) — CLI interaction tests
   - Tests command-line interface
   - Tests interactive mode menu
   - **Risk:** Medium. If CLI adds new operations to menu and they're unary, interactive flow may break (expects two operands for all operations).

4. **test_json_storage.py** (7 tests) — storage layer
   - Tests saving and loading calculations
   - **Risk:** Low. Storage format unchanged; new operation strings will serialize like existing ones.

### Key Test to Verify

Test in `test_cli.py` line 24:
```python
def test_invalid_operation_exits(self):
    cli, _ = _make_cli()
    with pytest.raises(SystemExit):
        cli.run_command("modulo", 3, 5)
```

Currently "modulo" is **invalid**. After Task 02, this test will fail unless updated to accept "modulo" as valid. This is a **regression risk** — this test expects failure and will now get success.

**Expected behavior after Task 02:**
- `cli.run_command("modulo", 3, 5)` should succeed and print "3 % 5 = 0"
- This test will need to be updated or removed by the test team

---

## 6. Summary: What Changes for Task 02

### Must Add (in order of integration dependency)

1. **Operation Enum** (`src/models/operation.py`)
   - Add: `SQUARE`, `SQRT`, `POWER`, `MODULO` enum members

2. **Calculator Class** (`src/services/calculator.py`)
   - Add: `square(a: float) -> float` method
   - Add: `sqrt(a: float) -> float` method with exception for negative input
   - Add: `power(a: float, b: float) -> float` method
   - Add: `modulo(a: float, b: float) -> float` method with exception for zero divisor
   - **Do NOT modify:** Existing methods, dispatcher logic

3. **CalculationResult** (`src/models/calculation_result.py`)
   - Add symbols for new operations in `_SYMBOLS` dictionary
   - No changes to fields or methods

4. **CLI** (`src/cli/calculator_cli.py`)
   - Add new operations to `_MENU` list
   - **Design issue:** Unary operations may break interactive mode

### Exception Types

**User prompt specification:** "Domain errors in this task must be represented by raised exceptions."

Test specifications use generic `Exception`:
```python
with pytest.raises(Exception):
    Calculator().sqrt(-1)
```

**Recommendation:** Follow existing pattern with `ValueError`:
- `sqrt(-1)` → `raise ValueError("Square root of negative number is not allowed")`
- `modulo(x, 0)` → `raise ValueError("Modulo by zero is not allowed")`

This aligns with existing error handling in `divide()` method.

### No Changes Required

- `src/services/calculator_service.py` — unless dispatcher needs unary support (current tests suggest not)
- `src/storage/json_storage.py` — serialization handles new strings automatically
- `tests/` — new tests provided by prompt; existing tests should pass except `test_invalid_operation_exits` (which tests unary operations as invalid)

---

## 7. Key Ambiguities and Assumptions

| Issue | Current Assumption | Risk |
|-------|-------------------|------|
| Unary vs binary in dispatcher | Unary methods NOT added to `calculate()` dispatcher; called directly only | Medium — if tests expect dispatched calls, dispatcher needs redesign |
| Exception type for sqrt/modulo errors | Use `ValueError` (consistent with divide); tests accept `Exception` | Low — tests are permissive |
| CLI menu for unary operations | Need to decide: exclude from interactive menu, or redesign input flow | High — current code assumes all operations are binary |
| Display format for unary in history | "3 ² = 9" looks odd but works; alternative is to special-case `__str__()` | Low — acceptable as-is |
| Backward compatibility of old calculations | CalculationResult has new enum values; old JSON files have no entries for these — not an issue since saved data uses enum string value | Low |

---

## Files to Read/Modify Summary

**Absolute Paths in Working Directory:**

**Read (already analyzed):**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/services/calculator.py` — current methods
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/models/operation.py` — enum definition
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/models/calculation_result.py` — result model
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/cli/calculator_cli.py` — CLI menu
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/tests/test_calculator.py` — existing tests
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/tests/test_cli.py` — CLI tests

**Modify:**
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/services/calculator.py` — add 4 methods
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/models/operation.py` — add 4 enum members
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/models/calculation_result.py` — extend `_SYMBOLS` dict
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/cli/calculator_cli.py` — add menu entries

