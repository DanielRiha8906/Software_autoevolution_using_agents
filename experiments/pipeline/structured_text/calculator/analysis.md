# Task 02 Analysis: Calculator Extension (Square, Sqrt, Power, Modulo)

## Task Summary

Add four new mathematical operations to the calculator: square (x²), sqrt(x), power(x, y), and modulo(x, y). Each operation must:
- Follow the existing operation interface pattern
- Handle specified edge cases and raise appropriate errors
- Be fully tested with edge case coverage
- Integrate into the CLI menu
- Be persisted in calculations.json

## Current Architecture Overview

### Layered Design
The application follows a layered architecture with clear separation of concerns:

1. **Models Layer** (`src/models/`): Domain objects
   - `Operation` enum: Represents supported operations with string deserialization
   - `CalculationResult` dataclass: Immutable result record with metadata (timestamp, execution_time_ms)

2. **Services Layer** (`src/services/`): Business logic
   - `Calculator`: Stateless class with individual operation methods + dispatch method
   - `CalculatorService`: Orchestrates Calculator + JsonStorage, wraps results with metadata

3. **Storage Layer** (`src/storage/`): Persistence
   - `JsonStorage`: Reads/writes CalculationResult objects to `artifacts/calculations.json`
   - Handles file creation, JSON serialization, and backward compatibility

4. **CLI Layer** (`src/cli/`): User interaction
   - `CalculatorCLI`: Interactive menu + one-shot command mode
   - Menu dynamically built from `_MENU` list that references Operation enum members

5. **Entry Point** (`src/__main__.py`): Argument parsing and initialization

### Key Design Patterns

**Operation Enum Pattern:**
```python
class Operation(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    
    @classmethod
    def from_string(cls, value: str) -> "Operation":
        # Deserialize from CLI input or file
    
    def display_name(self) -> str:
        # Return human-readable label
```

**Calculator Dispatch Pattern:**
```python
def calculate(self, operation: Operation, a: float, b: float) -> float:
    dispatch = {
        Operation.ADD: self.add,
        Operation.SUBTRACT: self.subtract,
        Operation.MULTIPLY: self.multiply,
        Operation.DIVIDE: self.divide,
    }
    return dispatch[operation](a, b)
```

**CalculationResult Pattern:**
- Dataclass with immutable field layout
- Includes metadata: timestamp (ISO 8601), execution_time_ms
- Has `to_dict()` and `from_dict()` for JSON round-tripping
- Has `__str__()` that renders using symbol map in same file
- Backward compatible: missing execution_time_ms defaults to 0.0

**Error Handling Pattern:**
- Exceptions raised in Calculator, caught and propagated by CalculatorService
- CalculatorService does NOT save results if Calculator raises ValueError
- CLI catches ValueError and prints to stderr, exits with code 1

**CLI Menu Pattern:**
- `_MENU` is a list of (Operation, label) tuples
- Menu indices dynamically computed
- History and Exit are offset-indexed after main menu
- User input retried on invalid choice or number format

## Existing Operation Interface Pattern

**For each operation in Calculator:**
1. Individual method: `def operation_name(self, a: float, b: float) -> float`
2. Added to `dispatch` dict in `calculate()` method using Operation enum key
3. Edge cases handled via `ValueError` exceptions (e.g., divide by zero)

**For each operation in Operation enum:**
1. Entry in enum: `OPERATION_NAME = "operation_name"` (lowercase string value)
2. Automatically discovered by `from_string()` method
3. Used as key in dispatch dict
4. Used as value in CalculationResult.operation field
5. Used as key in symbol map in CalculationResult

**For each operation in CLI:**
1. Added to `_MENU` list as (Operation.OPERATION_NAME, "Display Name") tuple
2. Automatically included in menu numbering
3. Automatically available in run_command() via Operation.from_string()

**For each operation in tests:**
- Unit tests in test_calculator.py for the operation method
- Service tests in test_calculator_service.py for perform() dispatch
- CLI tests in test_cli.py for command-line invocation
- Edge case tests with expected error behavior

## Existing Edge Case Handling Patterns

From `divide()` implementation:
```python
def divide(self, a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b
```

Tests for edge cases follow this pattern (from test_calculator.py):
```python
def test_divide_by_zero_raises(self):
    with pytest.raises(ValueError, match="Division by zero"):
        self.calc.divide(5, 0)
```

Service-level tests verify errors prevent storage writes:
```python
def test_perform_divide_by_zero_does_not_save(self):
    with pytest.raises(ValueError):
        self.service.perform(Operation.DIVIDE, 5, 0)
    self.storage.save.assert_not_called()
```

## Files That Need Modification

### 1. `src/models/operation.py`
- Add four new enum members: SQUARE, SQRT, POWER, MODULO
- Use lowercase string values: "square", "sqrt", "power", "modulo"
- No method changes needed (from_string, display_name work generically)

### 2. `src/services/calculator.py`
- Add four instance methods: square(), sqrt(), power(), modulo()
- Update dispatch dict to include the four new operations
- square(x): accepts float, returns float, no edge cases
- sqrt(x): raise ValueError for negative x
- power(x, y): accept any exponent (negative, fractional), return float
- modulo(x, y): raise ValueError for y == 0

### 3. `src/models/calculation_result.py`
- Add symbol entries to `_SYMBOLS` dict: "square": "²", "sqrt": "√", "power": "^", "modulo": "%"
- (No structural changes; __str__() already reads from _SYMBOLS)

### 4. `src/cli/calculator_cli.py`
- Add four tuples to `_MENU`: (Operation.SQUARE, "Square"), (Operation.SQRT, "Square Root"), (Operation.POWER, "Power"), (Operation.MODULO, "Modulo")
- No method changes needed; menu logic is generic

### 5. `src/__main__.py`
- Add four operation names to argparse choices: "square", "sqrt", "power", "modulo"
- No other changes needed; run_command() is generic

## Files That Need Creation

### 1. `tests/test_new_operations.py`
New test module for the four new operations (or extend existing test_calculator.py):

**test_square():**
- square(0) == 0
- square(5) == 25
- square(-3) == 9
- square(0.5) == 0.25

**test_sqrt():**
- sqrt(4) == 2.0
- sqrt(2) == pytest.approx(1.414..., rel=1e-3)
- sqrt(0) == 0.0
- sqrt(-1) raises ValueError with descriptive message
- sqrt(-0.1) raises ValueError

**test_power():**
- power(2, 3) == 8 (positive exponent)
- power(2, 0) == 1.0 (zero exponent)
- power(2, -1) == 0.5 (negative exponent)
- power(2, 0.5) == pytest.approx(1.414...) (fractional exponent)
- power(0, 0) == 1.0 (mathematical convention)
- power(-2, 3) == -8 (odd power of negative)
- power(-2, 2) == 4 (even power of negative)

**test_modulo():**
- modulo(10, 3) == 1
- modulo(7, 2) == 1
- modulo(9, 3) == 0 (exact divisor)
- modulo(-10, 3) == 2 (Python's modulo semantics)
- modulo(10.5, 3.2) == pytest.approx(...) (float operands)
- modulo(5, 0) raises ValueError with descriptive message

**Service-level edge case tests:**
- Verify sqrt(-1) prevents storage writes
- Verify modulo(x, 0) prevents storage writes

## Edge Case Handling Requirements

### Square (x²)
- No mathematical edge cases
- Handles negative inputs naturally (return positive)
- No error conditions

### Sqrt (√x)
- **Edge case: sqrt of negative number must raise ValueError**
  - Message: "Cannot calculate square root of negative number"
  - x < 0 → raise immediately
  - x == 0 → return 0.0 (valid)
  - x > 0 → use math.sqrt()

### Power (x^y)
- **Edge case: power with negative or fractional exponents must produce correct results**
  - Negative exponents: 2^(-1) = 0.5 (use ** operator or math.pow)
  - Fractional exponents: 2^0.5 = sqrt(2) ≈ 1.414 (** operator handles)
  - Zero exponent: x^0 = 1.0 for any x (including 0^0 = 1.0 in Python)
  - Negative base with even power: (-2)^2 = 4
  - Negative base with odd power: (-2)^3 = -8

### Modulo (x % y)
- **Edge case: modulo by zero must raise ValueError**
  - y == 0 → raise immediately
  - y != 0 → use % operator
  - Message: "Modulo by zero is not allowed"
  - Python semantics: -10 % 3 == 2 (not -1), follows Python convention

## Test Coverage Strategy

### Unit Tests (test_calculator.py or new test_new_operations.py)

**Square:**
- 4 tests (zero, positive, negative, float)

**Sqrt:**
- 6 tests (zero, positive perfect square, positive non-perfect, negative, boundary)

**Power:**
- 8 tests (positive exponent, zero exponent, negative exponent, fractional exponent, negative base even, negative base odd, 0^0)

**Modulo:**
- 6 tests (basic, zero remainder, negative operands, float operands, boundary conditions)

### Service-Level Tests (test_calculator_service.py)

For each operation:
- 1 test: normal case via perform(), verify result stored
- 1 test: edge case error, verify ValueError raised
- 1 test: edge case error, verify storage NOT called (for sqrt/modulo only)

Total: 12 new service tests (3 for each of sqrt, modulo; 2 for square, power)

### CLI Tests (test_cli.py)

For each operation:
- 1 test: run_command() success case
- 1 test: run_command() error case (sqrt/modulo only)

Total: 8 new CLI tests (4 for all + 4 for error cases)

### JSON Storage Tests (test_json_storage.py)

No new tests needed; CalculationResult.to_dict/from_dict already tested generically.

## Summary: Files to Modify and Create

### Modify (5 files)
1. `src/models/operation.py` — add enum members
2. `src/services/calculator.py` — add methods + dispatch
3. `src/models/calculation_result.py` — add symbol mappings
4. `src/cli/calculator_cli.py` — add menu items
5. `src/__main__.py` — add argparse choices

### Create (1 file, optional)
1. `tests/test_new_operations.py` — comprehensive new operation tests (OR extend test_calculator.py)

### Total Test Coverage
- Current: 38 tests
- New: ~26 tests (24 operation-specific + 2 backward compat already exist)
- Target: ~64 tests

## Implementation Order

1. Add Operation enum members
2. Add Calculator methods (square, sqrt, power, modulo)
3. Update Calculator.calculate() dispatch
4. Update CalculationResult._SYMBOLS
5. Update CalculatorCLI._MENU
6. Update __main__.py argparse
7. Write comprehensive tests
8. Verify all tests pass
9. Update PlantUML diagrams to reflect new operations
