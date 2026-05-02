# Analysis: Add Additional Mathematical Operations

## Task Summary

Task 02 requires implementing four new mathematical operations to extend the calculator with:
- **square(x)** — x^2
- **sqrt(x)** — square root
- **power(x, y)** — x raised to power y
- **modulo(x, y)** — remainder after division

These operations must follow the existing architecture and operation interface, handle edge cases properly, and maintain the testing patterns already established in Task 01.

## Current Architecture

### Operation Enum and Registration

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/models/operation.py`

```python
class Operation(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"

    @classmethod
    def from_string(cls, value: str) -> "Operation":
        # Case-insensitive lookup by string value
        # Raises ValueError if unknown

    def display_name(self) -> str:
        return self.value.capitalize()
```

**Key observations**:
- Operations are registered as enum members with string values (lowercase)
- `from_string()` is case-insensitive and used by CLI to parse operation names
- `display_name()` is used for menu display (capitalizes the operation name)

### Calculator Implementation

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/services/calculator.py`

Current structure:
```python
class Calculator:
    def add(self, a: float, b: float) -> float
    def subtract(self, a: float, b: float) -> float
    def multiply(self, a: float, b: float) -> float
    def divide(self, a: float, b: float) -> float
        # Raises ValueError("Division by zero is not allowed") if b == 0

    def calculate(self, operation: Operation, a: float, b: float) -> float
        # Dispatch table maps Operation to method
        # Raises ValueError if operation not in dispatch
```

**Key patterns**:
- Each operation is a named method taking two float operands (a, b)
- Exception handling for error cases (e.g., division by zero) occurs in the method itself
- The `calculate()` method dispatches via a dictionary mapping Operation enum members to methods
- Methods return float directly or raise ValueError for invalid inputs

### Operation Dispatch Mechanism

The dispatch table in `calculate()` shows the coupling point:
```python
dispatch = {
    Operation.ADD: self.add,
    Operation.SUBTRACT: self.subtract,
    Operation.MULTIPLY: self.multiply,
    Operation.DIVIDE: self.divide,
}
```

To add new operations, this dispatch table must be updated to include new enum values.

### CalculationResult Persistence

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/models/calculation_result.py`

```python
@dataclass
class CalculationResult:
    operation: str           # stores operation.value (e.g., "add")
    operand_a: float
    operand_b: float
    result: float
    timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)
```

**Key observation**: Operation is stored as a string (operation.value), not the enum itself. This allows JSON serialization.

### CalculatorService Orchestration

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/services/calculator_service.py`

```python
def perform(self, operation: Operation, a: float, b: float) -> CalculationResult:
    start = time.perf_counter()
    result = self.calculator.calculate(operation, a, b)  # May raise ValueError
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    calc_result = CalculationResult(
        operation=operation.value,
        operand_a=a,
        operand_b=b,
        result=result,
        execution_time_ms=elapsed_ms,
    )
    self.storage.save(calc_result)
    return calc_result
```

**Error handling**: Exceptions from `calculator.calculate()` propagate uncaught, preventing result creation and storage. This is correct for fatal errors like division by zero.

### CLI Integration

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/cli/calculator_cli.py`

Menu definition:
```python
_MENU: list[tuple[Operation, str]] = [
    (Operation.ADD,      "Add"),
    (Operation.SUBTRACT, "Subtract"),
    (Operation.MULTIPLY, "Multiply"),
    (Operation.DIVIDE,   "Divide"),
]
```

**Key observation**: Menu entries are hardcoded. Adding new operations requires updating this list.

Command parsing uses `Operation.from_string()`:
```python
def run_command(self, operation_str: str, a: float, b: float) -> None:
    try:
        operation = Operation.from_string(operation_str)
        result = self.service.perform(operation, a, b)
        print(result)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
```

### Testing Patterns

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/tests/test_calculator.py`

Pattern for operation tests:
```python
def test_operation_name(self):
    assert self.calc.operation_method(operand1, operand2) == expected_result

def test_operation_edge_case(self):
    with pytest.raises(ValueError, match="error message"):
        self.calc.operation_method(operand1, operand2)
```

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/tests/test_calculator_service.py`

Pattern for service integration:
```python
def test_perform_operation_returns_result(self):
    result = self.service.perform(Operation.OPERATION, operand1, operand2)
    assert result.result == expected
    assert result.operation == "operation_name"

def test_perform_operation_error_raises(self):
    with pytest.raises(ValueError, match="error message"):
        self.service.perform(Operation.OPERATION, operand1, operand2)
```

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/tests/test_cli.py`

Pattern for CLI:
```python
def test_operation_via_command(self, capsys):
    cli, service = _make_cli()
    service.perform.return_value = CalculationResult("operation", a, b, result, _TS, 0.0)
    cli.run_command("operation", a, b)
    assert "result" in capsys.readouterr().out
```

### Result Display

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/models/calculation_result.py`

```python
_SYMBOLS = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}

def __str__(self) -> str:
    symbol = _SYMBOLS.get(self.operation, self.operation)
    # formats as "a symbol b = result"
```

**Key observation**: New operations need symbols in `_SYMBOLS` dictionary for proper display. If not present, the operation name is used as fallback.

## What New Operations Need to Be Added

### 1. Square Operation (x^2)

**Enum value**: `SQUARE = "square"`

**Method signature**: `square(self, a: float, b: float=None) -> float`

**Issue**: The task specifies "square(x)" (unary), but the Calculator interface takes two operands. Options:
- Option A: Ignore the second operand (simpler, consistent interface)
- Option B: Interpret as square of (a+b) or other binary variant
- Option C: Modify Calculator.calculate() signature

**Assumption**: Use Option A — implement as `a * a`, ignoring `b`. This keeps the interface uniform and follows principle of least surprise.

**Edge cases**: None for floating-point square (always valid).

### 2. Sqrt Operation (√x)

**Enum value**: `SQRT = "sqrt"`

**Method signature**: `sqrt(self, a: float, b: float=None) -> float`

**Edge case**: Negative numbers must raise an error.
- `math.sqrt()` raises ValueError for negative inputs
- Error message should be clear: "Cannot compute square root of negative number"

**Assumption**: Second operand is ignored; sqrt(a) computes the square root of a only.

### 3. Power Operation (x^y)

**Enum value**: `POWER = "power"`

**Method signature**: `power(self, a: float, b: float) -> float`

**Behavior**: a ** b (both operands used)

**Edge cases**:
- Negative base with fractional exponent: e.g., (-2) ** 0.5 produces complex number
  - Python handles this by raising ValueError: "negative number cannot be raised to a fractional power"
- Zero base with negative exponent: e.g., 0 ** -1 produces ZeroDivisionError
  - Python raises ZeroDivisionError: "0.0 cannot be raised to a negative power"
- These exceptions should propagate naturally (no special handling needed)

**Assumption**: Let Python's built-in ** operator handle edge cases and raise appropriate errors.

### 4. Modulo Operation (x % y)

**Enum value**: `MODULO = "modulo"`

**Method signature**: `modulo(self, a: float, b: float) -> float`

**Behavior**: a % b (remainder after division)

**Edge case**: Division by zero (b == 0) must raise an error.
- Error message should be: "Modulo by zero is not allowed"

**Assumption**: Follow the pattern from divide() — check for zero before operation and raise ValueError explicitly.

## Implementation Checklist

### Required Changes to Add All Four Operations

#### 1. `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/models/operation.py`

Add enum members:
```python
SQUARE = "square"
SQRT = "sqrt"
POWER = "power"
MODULO = "modulo"
```

No changes to `from_string()` or `display_name()` (they're generic).

#### 2. `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/services/calculator.py`

Add four methods:
```python
def square(self, a: float, b: float) -> float:
    return a * a

def sqrt(self, a: float, b: float) -> float:
    if a < 0:
        raise ValueError("Cannot compute square root of negative number")
    return a ** 0.5  # or import math; return math.sqrt(a)

def power(self, a: float, b: float) -> float:
    return a ** b

def modulo(self, a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Modulo by zero is not allowed")
    return a % b
```

Update dispatch table in `calculate()`:
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

#### 3. `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/src/cli/calculator_cli.py`

Add symbols in `calculation_result.py`:
```python
_SYMBOLS = {
    "add": "+",
    "subtract": "-",
    "multiply": "×",
    "divide": "÷",
    "square": "²",        # or "^2"
    "sqrt": "√",
    "power": "^",
    "modulo": "%",
}
```

Update menu in `calculator_cli.py`:
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

No changes to `run_command()` or `run_interactive()` — they automatically adapt to new menu items.

#### 4. Tests

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/tests/test_calculator.py`

Add test methods following existing pattern:

```python
def test_square(self):
    assert self.calc.square(3, 0) == 9  # Note: second arg ignored

def test_square_zero(self):
    assert self.calc.square(0, 0) == 0

def test_square_negative(self):
    assert self.calc.square(-3, 0) == 9

def test_square_float(self):
    assert self.calc.square(2.5, 0) == pytest.approx(6.25)

def test_sqrt(self):
    assert self.calc.sqrt(9, 0) == 3.0

def test_sqrt_zero(self):
    assert self.calc.sqrt(0, 0) == 0.0

def test_sqrt_float(self):
    assert self.calc.sqrt(2, 0) == pytest.approx(1.414213562)

def test_sqrt_negative_raises(self):
    with pytest.raises(ValueError, match="Cannot compute square root of negative"):
        self.calc.sqrt(-1, 0)

def test_power(self):
    assert self.calc.power(2, 3) == 8

def test_power_zero_exponent(self):
    assert self.calc.power(5, 0) == 1

def test_power_fractional_exponent(self):
    assert self.calc.power(4, 0.5) == pytest.approx(2.0)

def test_power_negative_base_negative_exponent(self):
    assert self.calc.power(-2, -1) == pytest.approx(-0.5)

def test_power_zero_negative_exponent_raises(self):
    with pytest.raises(ZeroDivisionError):
        self.calc.power(0, -1)

def test_power_negative_base_fractional_exponent_raises(self):
    with pytest.raises(ValueError):
        self.calc.power(-2, 0.5)

def test_modulo(self):
    assert self.calc.modulo(10, 3) == 1

def test_modulo_negative_dividend(self):
    assert self.calc.modulo(-10, 3) == 2  # Python's modulo behavior

def test_modulo_zero_divisor_raises(self):
    with pytest.raises(ValueError, match="Modulo by zero"):
        self.calc.modulo(5, 0)

def test_modulo_float(self):
    assert self.calc.modulo(7.5, 2.5) == pytest.approx(0.0)
```

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/tests/test_calculator_service.py`

Add service tests:
```python
def test_perform_square_returns_result(self):
    result = self.service.perform(Operation.SQUARE, 3, 0)
    assert result.result == 9
    assert result.operation == "square"

def test_perform_sqrt_returns_result(self):
    result = self.service.perform(Operation.SQRT, 9, 0)
    assert result.result == 3.0

def test_perform_sqrt_negative_raises(self):
    with pytest.raises(ValueError, match="Cannot compute square root"):
        self.service.perform(Operation.SQRT, -1, 0)

def test_perform_power_returns_result(self):
    result = self.service.perform(Operation.POWER, 2, 3)
    assert result.result == 8

def test_perform_modulo_returns_result(self):
    result = self.service.perform(Operation.MODULO, 10, 3)
    assert result.result == 1

def test_perform_modulo_by_zero_raises(self):
    with pytest.raises(ValueError, match="Modulo by zero"):
        self.service.perform(Operation.MODULO, 5, 0)
```

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/tests/test_calculator.py`

Also add dispatch test:
```python
def test_calculate_dispatches_new_operations(self):
    assert self.calc.calculate(Operation.SQUARE, 3, 0) == 9
    assert self.calc.calculate(Operation.SQRT, 9, 0) == 3.0
    assert self.calc.calculate(Operation.POWER, 2, 3) == 8
    assert self.calc.calculate(Operation.MODULO, 10, 3) == 1
```

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/tests/test_cli.py`

Add command tests:
```python
def test_square_via_command(self, capsys):
    cli, service = _make_cli()
    service.perform.return_value = CalculationResult("square", 3, 0, 9, _TS, 0.0)
    cli.run_command("square", 3, 0)
    assert "9" in capsys.readouterr().out

def test_sqrt_via_command(self, capsys):
    cli, service = _make_cli()
    service.perform.return_value = CalculationResult("sqrt", 9, 0, 3.0, _TS, 0.0)
    cli.run_command("sqrt", 9, 0)
    assert "3" in capsys.readouterr().out

def test_power_via_command(self, capsys):
    cli, service = _make_cli()
    service.perform.return_value = CalculationResult("power", 2, 3, 8, _TS, 0.0)
    cli.run_command("power", 2, 3)
    assert "8" in capsys.readouterr().out

def test_modulo_via_command(self, capsys):
    cli, service = _make_cli()
    service.perform.return_value = CalculationResult("modulo", 10, 3, 1, _TS, 0.0)
    cli.run_command("modulo", 10, 3)
    assert "1" in capsys.readouterr().out
```

#### 5. Diagrams

Update UML diagrams to reflect new operations:

**File**: `/home/runner/work/Software_autoevolution_using_agents/Software_autoevolution_using_agents/experiments/pipeline/structured_text/calculator/artifacts/class_diagram.puml`

Update Operation enum:
```
enum Operation {
    ADD
    SUBTRACT
    MULTIPLY
    DIVIDE
    SQUARE
    SQRT
    POWER
    MODULO
    ...
}
```

Update Calculator methods list:
```
class Calculator {
    ...
    +square(a: float, b: float) : float
    +sqrt(a: float, b: float) : float
    +power(a: float, b: float) : float
    +modulo(a: float, b: float) : float
    ...
}
```

## Ambiguities and Assumptions

### 1. Unary vs Binary Operations

**Question**: How should unary operations (square, sqrt) handle the binary interface?

**Assumption**: Implement all operations with two float parameters. For unary operations (square, sqrt), the second parameter is ignored. This:
- Keeps the Calculator.calculate() signature uniform
- Maintains consistency with existing dispatch mechanism
- Simplifies CLI (doesn't need separate unary/binary handling)
- The second operand can be documented as "ignored for unary operations"

**Alternative rejected**: Modify Calculator.calculate() to accept variable arguments — would break existing dispatch mechanism and require major refactoring.

### 2. Sqrt Implementation

**Question**: Should we use `a ** 0.5` or `import math; math.sqrt(a)`?

**Assumption**: Use `a ** 0.5` to avoid external dependencies. The task says "Use only built-in Python" (implicitly, as Task 01 established). The power operator is sufficient and more consistent with power() implementation.

**Alternative**: `import math; math.sqrt()` is equally valid but adds an import for what power already does.

### 3. Error Messages

**Question**: What exact error messages should be used?

**Assumption**: Follow existing pattern from divide():
- "Modulo by zero is not allowed" (matches "Division by zero is not allowed")
- "Cannot compute square root of negative number" (clear and specific)
- Let Python's native errors propagate for power edge cases (ZeroDivisionError, ValueError for negative fractional roots)

### 4. Second Operand in CLI for Unary Ops

**Question**: When user calls `square` from CLI, should they be required to provide two operands?

**Assumption**: Yes, for consistency. The CLI interface remains uniform: all operations take two operands. For unary operations, the second is simply ignored. This is simpler than:
- Detecting operation type and prompting differently
- Modifying the CLI logic (fragile)

## Scope Signals

### Must (In Scope)
- Implement all four operations (square, sqrt, power, modulo)
- Each follows the existing operation interface (Operation enum member + Calculator method + dispatch entry)
- Edge case handling as specified (sqrt negative → error, modulo zero → error, power exceptions pass through)
- Unit tests for all operations and edge cases
- Service-level tests for integration
- CLI tests for command parsing

### Could (Optional but Beneficial)
- Add display symbols (^2, √, ^, %) in _SYMBOLS dictionary for prettier output
- Update diagrams to reflect new operations
- Add docstrings to operation methods

### Won't (Out of Scope)
- Support operator aliases ('^' for power) — not required
- Reuse shared computation logic — each method is simple, no duplication
- Introduce new operation types beyond these four
- Modify CLI interface (keep uniform binary operand handling)

## Suggested Priorities

1. **High**: Add four Operation enum members (square, sqrt, power, modulo)
   - Blocking: everything else depends on this

2. **High**: Implement four Calculator methods
   - Blocking: service and CLI need these

3. **High**: Update dispatch table in Calculator.calculate()
   - Blocking: dispatch won't find new operations without this

4. **High**: Write unit tests for all four operations and edge cases
   - Ensures correctness before integration

5. **High**: Update CalculatorCLI menu to include new operations
   - Required for interactive mode access

6. **Medium**: Add service-level tests (test_calculator_service.py)
   - Verifies integration and persistence

7. **Medium**: Add CLI-level tests (test_cli.py)
   - Verifies command parsing and output

8. **Medium**: Add symbols to _SYMBOLS dictionary
   - Improves user experience but not critical

9. **Low**: Update diagrams (class_diagram.puml, activity_diagram.puml)
   - Documentation, doesn't affect functionality

## Implementation Notes

### Unary Operations Behavior
For square and sqrt, the second operand is accepted by the method signature but ignored:
```python
def square(self, a: float, b: float) -> float:
    return a * a  # b is ignored

def sqrt(self, a: float, b: float) -> float:
    if a < 0:
        raise ValueError("Cannot compute square root of negative number")
    return a ** 0.5  # b is ignored
```

The method must accept `b` to match the dispatcher's expectations (all operations take 2 args), but it doesn't use it. This is acceptable in Python and a common pattern for polyadic interfaces.

### Edge Case Propagation
For power operation, Python's built-in exceptions are sufficient:
- `0 ** -1` → ZeroDivisionError: "0.0 cannot be raised to a negative power"
- `(-1) ** 0.5` → ValueError: "negative number cannot be raised to a fractional power"

These exceptions naturally propagate through Calculator.calculate() to CalculatorService.perform() to the CLI, where they're caught and displayed as errors. No custom handling needed.

### Modulo with Negative Numbers
Python's modulo has specific behavior with negative operands (different from some languages):
```python
-10 % 3 == 2  # Not -1
10 % -3 == -2  # Not 1
```

This is Python's defined behavior and should be preserved (no special cases).

## Summary

Task 02 requires adding 8 methods across 3 files:
- 4 new Operation enum members
- 4 new Calculator methods
- 1 updated dispatch table
- 1 updated menu
- 1 updated symbols dictionary
- Approximately 20-30 test methods to cover new operations and edge cases

All changes fit within the existing architecture and require no breaking changes to public APIs or CLI behavior. The implementation is straightforward; the main complexity is comprehensive edge case testing.
