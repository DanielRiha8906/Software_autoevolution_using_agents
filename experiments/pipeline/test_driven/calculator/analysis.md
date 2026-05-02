# Test-Driven Evolution Analysis: Calculator Enhancement

**Date:** 2026-05-02  
**Task:** Identify changes required to pass new test requirements for square, sqrt, power, and modulo operations.

---

## Current System State

### Calculator Class (src/services/calculator.py)

**Current Interface:**
```python
class Calculator:
    def add(a: float, b: float) -> float
    def subtract(a: float, b: float) -> float
    def multiply(a: float, b: float) -> float
    def divide(a: float, b: float) -> float
    def calculate(operation: Operation, a: float, b: float) -> float
```

**Implementation Patterns:**
1. **Binary operations** — All existing methods take two operands (a, b)
2. **Error handling** — Only `divide()` validates input; raises `ValueError` on invalid state
3. **Dispatch mechanism** — `calculate()` method uses a dictionary lookup to dispatch to operation methods based on `Operation` enum
4. **Type handling** — Methods accept and return `float`; no strict type validation at method entry

### Operation Enum (src/models/operation.py)

**Current Members:**
- `ADD = "add"`
- `SUBTRACT = "subtract"`
- `MULTIPLY = "multiply"`
- `DIVIDE = "divide"`

**Methods:**
- `from_string(value: str) -> Operation` — case-insensitive lookup
- `display_name() -> str` — returns capitalized value

### CalculationResult Model (src/models/calculation_result.py)

**Fields:**
- `operation: str` — operation name (matches Operation enum values)
- `operand_a: float`, `operand_b: float` — operands
- `result: float` — calculation result
- `timestamp: str`, `execution_time_ms: float` — metadata

**Symbol Mapping:** 
```python
_SYMBOLS = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}
```

---

## New Methods Required

### 1. square(a: float) -> float

**Test Requirements:**
- `square(4)` returns `16`
- `square(0)` returns `0`

**Characteristics:**
- **Arity:** Unary (single operand) — differs from existing binary pattern
- **Edge Cases:** 
  - Zero input (must return 0, not undefined)
  - Negative inputs (mathematically valid; e.g., `square(-4) = 16`)
  - Large inputs (should handle floats without precision loss)

**Implementation Pattern:**
- Return `a * a` or `a ** 2`
- No error conditions expected

---

### 2. sqrt(a: float) -> float

**Test Requirements:**
- `sqrt(9)` returns `pytest.approx(3.0)` (floating-point tolerance required)
- `sqrt(-1)` raises `Exception` (must not allow negative input)

**Characteristics:**
- **Arity:** Unary
- **Error Handling:** Must raise exception for negative operands
- **Float Precision:** Result requires `pytest.approx()` comparison tolerance

**Edge Cases:**
- Negative numbers → must raise exception
- Zero → should return 0.0
- Non-perfect squares → returns float with potential precision issues
- Very large numbers → may lose precision

**Implementation Pattern:**
- Use `math.sqrt()` for correctness
- Validate input: `if a < 0: raise Exception(...)`
- Consider whether to use generic `Exception` or `ValueError`

---

### 3. power(a: float, b: float) -> float

**Test Requirements:**
- `power(2, 10)` returns `1024` (integer exponent)
- `power(8, 1/3)` returns `pytest.approx(2.0, rel=1e-5)` (fractional exponent, looser tolerance)
- `power(2, -1)` returns `pytest.approx(0.5)` (negative exponent)

**Characteristics:**
- **Arity:** Binary (base and exponent)
- **Error Handling:** None specified in tests; behavior for edge cases undefined
- **Precision:** Fractional exponents require relative tolerance of 1e-5 (stricter than default `pytest.approx()`)

**Edge Cases:**
- Integer exponents (must be exact for small integers)
- Fractional exponents (cube roots, square roots via exponent)
- Negative exponents (reciprocal behavior)
- Zero base with negative exponent (mathematically undefined; behavior TBD)
- Negative base with fractional exponent (complex result; behavior TBD)

**Implementation Pattern:**
- Use `a ** b` or `math.pow(a, b)`
- No validation specified; assume valid inputs or handle edge cases gracefully
- Test accepts `rel=1e-5` tolerance for fractional cases

---

### 4. modulo(a: float, b: float) -> float

**Test Requirements:**
- `modulo(10, 3)` returns `1`
- `modulo(10, 0)` raises `Exception` (must not allow zero divisor)

**Characteristics:**
- **Arity:** Binary
- **Error Handling:** Must raise exception for zero divisor
- **Float Support:** Tests use integer inputs, but method signature accepts floats

**Edge Cases:**
- Divisor is zero → must raise exception
- Negative operands → Python's `%` operator behavior (floor modulo)
- Float operands → Python's `%` operator supports floats; result precision TBD
- Negative divisor → valid in Python; behavior inherited from `%` operator

**Implementation Pattern:**
- Return `a % b`
- Validate input: `if b == 0: raise Exception(...)`
- Consider type consistency with `divide()`

---

## Operation Enum Impact

**Required Changes:**
1. Add four new enum members:
   - `SQUARE = "square"`
   - `SQRT = "sqrt"`
   - `POWER = "power"`
   - `MODULO = "modulo"`

2. Update `from_string()` lookup to recognize new operations
3. Update symbol mapping in `CalculationResult` for string representation

---

## CalculationResult Model Impact

**Unary vs. Binary Operations:**
- Current model assumes binary operations (`operand_a`, `operand_b`)
- `square()` and `sqrt()` are unary
- **Decision Required:** 
  - Option A: Store unary operation in `operand_a` with `operand_b = 0` or `None`
  - Option B: Extend model to support optional `operand_b`
  - Option C: Store unary operations with operand in `operand_a` and mark `operand_b` as unused

- No test requirement constrains this choice; implementation team must decide

---

## Error Handling Consistency

**Current Pattern:**
- `divide()` raises `ValueError` with descriptive message
- Tests expect generic `Exception` for new methods

**Decision Points:**
1. Should `sqrt(-1)` raise `ValueError` or `math.ValueError` or generic `Exception`?
2. Should `modulo(10, 0)` raise the same exception type as `divide(10, 0)`?
3. Should exception messages be consistent across operations?

**Assumption:** Use `ValueError` for consistency with `divide()`, since test uses bare `Exception` and `ValueError` is a subclass of `Exception`.

---

## Dispatch Mechanism Update

**Calculator.calculate() Method:**
Current dispatch dictionary only includes binary operations. Options:
1. Extend `calculate()` to accept variable arguments and dispatch based on operation arity
2. Keep `calculate()` for binary-only operations; leave unary operations for direct method calls
3. Create separate dispatcher for unary operations

**Assumption:** Tests only test direct method calls (`Calculator().square(4)`, not `Calculator().calculate(...)`), so `calculate()` update is secondary. However, CLI and CalculatorService may need updates if they call `calculate()`.

---

## Test Coverage

### Existing Tests (test_calculator.py)
- 13 tests for existing operations (add, subtract, multiply, divide)
- Tests cover: positive/negative inputs, floats, edge cases, error conditions, dispatch

### Required New Tests (from specification)
- 10 tests for new operations (square, sqrt, power, modulo)
- Tests cover:
  - **square:** positive result, zero input
  - **sqrt:** positive result, negative input error
  - **power:** integer exponent, fractional exponent, negative exponent
  - **modulo:** normal result, zero divisor error
- All new methods tested via direct instantiation and method call

### Test Structure
- Tests use `pytest.approx()` for floating-point comparisons where needed
- Tests expect bare `Exception` for error cases, not specific subtypes
- Tests assume methods return float even for operations that could be int

---

## Summary of Required Changes

| Component | Change | Detail |
|-----------|--------|--------|
| `Calculator` | Add 4 methods | `square(a)`, `sqrt(a)`, `power(a, b)`, `modulo(a, b)` |
| `Operation` enum | Add 4 members | `SQUARE`, `SQRT`, `POWER`, `MODULO` |
| `Calculator.calculate()` | Update dispatch | Add entries for new operations (if needed) |
| `CalculationResult` | Symbol mapping | Add symbols for new operations |
| `CalculationResult` | Model structure | Handle unary operations (design TBD) |
| `CalculatorService` | Potentially | Update if it restricts operations |
| `CalculatorCLI` | Potentially | Add menu items and one-shot flags for new operations |
| `tests/test_calculator.py` | Append tests | Add 10 new test methods per specification |

---

## Key Ambiguities & Working Assumptions

1. **Unary operation storage in CalculationResult:**
   - **Ambiguity:** Current model designed for binary operations
   - **Assumption:** Store unary operand in `operand_a`, set `operand_b = 0.0` (or handle in service layer)

2. **Exception type for validation errors:**
   - **Ambiguity:** Tests use bare `Exception`; current code uses `ValueError`
   - **Assumption:** Raise `ValueError` (subclass of `Exception`); tests will pass

3. **Float vs. Int handling:**
   - **Ambiguity:** `modulo(10, 3)` uses integers but returns as float
   - **Assumption:** All methods return `float` for consistency

4. **Power operation edge cases:**
   - **Ambiguity:** No test for `power(0, 0)`, `power(-1, 0.5)`, etc.
   - **Assumption:** Rely on Python's `**` operator behavior; let math exceptions propagate if needed

5. **CLI/Service integration:**
   - **Ambiguity:** Tests don't require CLI or CalculatorService updates
   - **Assumption:** May be needed for full feature completeness per governance rules

---

## Relevant Files

- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/services/calculator.py` — main implementation target
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/models/operation.py` — enum to extend
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/src/models/calculation_result.py` — symbol mapping to update
- `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/test_driven/calculator/tests/test_calculator.py` — new tests to add
