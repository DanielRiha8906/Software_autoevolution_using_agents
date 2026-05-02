# Analysis: Square, Square Root, Power, and Modulo Operations

## Task Summary
Extend the calculator with four new mathematical operations: square(x), sqrt(x), power(x, y), and modulo(x, y). Each must follow the same interface pattern as existing operations (add, subtract, multiply, divide), handle errors appropriately, and not duplicate or rename any existing operations.

## Current Architecture

### Classes and Structure
- **Operation** (enum, src/models/operation.py): Defines available operations as enum members (ADD, SUBTRACT, MULTIPLY, DIVIDE) with factory method from_string() and display method display_name()
- **CalculationResult** (dataclass, src/models/calculation_result.py): Stores operation name (as string), operand_a, operand_b, result, timestamp, and execution_time_ms
- **Calculator** (service, src/services/calculator.py): Implements individual operation methods (add, subtract, multiply, divide) and a dispatch method calculate(operation: Operation, a: float, b: float) -> float
- **CalculatorService** (orchestrator, src/services/calculator_service.py): Calls Calculator, wraps result in CalculationResult, times execution, and saves to storage
- **CalculatorCLI** (UI, src/cli/calculator_cli.py): Interactive menu showing operations and one-shot command mode; menu is a list of tuples (Operation, label)
- **JsonStorage** (persistence, src/storage/json_storage.py): Saves/loads CalculationResult objects to JSON

### Current Operations Interface Pattern
All existing operations follow this pattern:
1. Enum member in Operation enum with a string value (e.g., ADD = "add")
2. Instance method on Calculator with signature (a: float, b: float) -> float (e.g., add(a, b))
3. Entry in dispatch dict in Calculator.calculate() mapping Operation enum to method
4. Menu entry in CalculatorCLI._MENU as tuple (Operation.CONSTANT, "Display Label")
5. Display symbol in CalculationResult._SYMBOLS dict for string representation

### Current Error Handling
- Division by zero: Raises ValueError("Division by zero is not allowed") in Calculator.divide()
- Invalid operations: Raises ValueError in Operation.from_string() and Calculator.calculate()
- Results propagate up through CalculatorService.perform() and are caught in CLI with try/except ValueError

### Testing Pattern
- Unit tests use pytest with setup_method() fixtures
- Calculator methods tested individually (test_calculator.py)
- CalculatorService tested with mocked storage (test_calculator_service.py)
- Tests verify operation results, error conditions, and side effects (storage calls)

## Exact Changes Required

### 1. Operation Enum (src/models/operation.py)
Add four new enum members:
- SQUARE = "square"
- SQRT = "sqrt"
- POWER = "power"
- MODULO = "modulo"

No changes to from_string() or display_name() methods—they work generically.

### 2. Calculator Class (src/services/calculator.py)
Add four new instance methods:

square(a: float, b: float) -> float
  - Return a * a (b is ignored, for consistency with 2-operand interface)

sqrt(a: float, b: float) -> float
  - If a < 0, raise ValueError("Square root of negative number is not allowed")
  - Import math module and return math.sqrt(a) (b is ignored)

power(a: float, b: float) -> float
  - Use a ** b operator
  - Handles negative exponents (e.g., 2 ** -1 = 0.5) and fractional exponents natively

modulo(a: float, b: float) -> float
  - If b == 0, raise ValueError("Modulo by zero is not allowed")
  - Use a % b operator
  - Works with floats (Python % supports it)

Update Calculator.calculate() dispatch dict:
- Add mappings: Operation.SQUARE -> self.square, Operation.SQRT -> self.sqrt, Operation.POWER -> self.power, Operation.MODULO -> self.modulo

### 3. CalculationResult Display (src/models/calculation_result.py)
Add symbols for new operations to _SYMBOLS dict:
_SYMBOLS = {
    "add": "+",
    "subtract": "-",
    "multiply": "×",
    "divide": "÷",
    "square": "²",
    "sqrt": "√",
    "power": "^",
    "modulo": "%"
}

Update __str__() method to handle single-operand display:
- For square: Display as "a² = result" (use only operand_a, not operand_b)
- For sqrt: Display as "√a = result"
- For power: Display as "a ^ b = result" (use both operands)
- For modulo: Display as "a % b = result"

### 4. CalculatorCLI Menu (src/cli/calculator_cli.py)
Add four new entries to CalculatorCLI._MENU:
(Operation.SQUARE, "Square"),
(Operation.SQRT, "Square root"),
(Operation.POWER, "Power"),
(Operation.MODULO, "Modulo"),

Menu items are appended to the end (after divide). Menu auto-numbers based on list length.

### 5. Testing (tests/)
Add new test methods in test_calculator.py:
- test_square_positive: square(5) == 25
- test_square_zero: square(0) == 0
- test_square_negative: square(-3) == 9
- test_sqrt_positive: sqrt(16) == 4.0
- test_sqrt_decimal: sqrt(2) ≈ 1.414...
- test_sqrt_zero: sqrt(0) == 0.0
- test_sqrt_negative_raises: sqrt(-1) raises ValueError with appropriate message
- test_power_positive_exponent: power(2, 3) == 8
- test_power_negative_exponent: power(2, -1) ≈ 0.5
- test_power_fractional_exponent: power(4, 0.5) == 2.0
- test_power_zero_exponent: power(5, 0) == 1
- test_modulo_positive: modulo(17, 5) == 2
- test_modulo_zero_divisor_raises: modulo(5, 0) raises ValueError
- test_calculate_dispatches_new_operations: Tests calculate() dispatch for all four

Add new test methods in test_calculator_service.py:
- test_perform_square: Verifies operation="square", correct result
- test_perform_sqrt: Verifies operation="sqrt", correct result
- test_perform_sqrt_negative_raises: Verifies ValueError propagates
- test_perform_power: Verifies operation="power", correct result
- test_perform_modulo: Verifies operation="modulo", correct result
- test_perform_modulo_by_zero_raises: Verifies ValueError, no save on error
- test_sqrt_negative_does_not_save: Verifies error prevents storage write

## Acceptance Criteria Mapping

| Criterion | Implementation | Files | Tests |
|-----------|----------------|-------|-------|
| Operations available: square, sqrt, power, modulo | Add 4 methods to Calculator + enum members | operation.py, calculator.py | test_calculator.py |
| Same interface as existing ops | (a, b) -> float signature; single-op ops ignore b | calculator.py | test_calculator.py, test_calculator_service.py |
| sqrt of negative raises error | Check a < 0, raise ValueError | calculator.py | test_calculator.py, test_calculator_service.py |
| sqrt of negative does not save | CalculatorService catches, re-raises without save | calculator_service.py | test_calculator_service.py |
| modulo by zero raises error | Check b == 0, raise ValueError | calculator.py | test_calculator.py, test_calculator_service.py |
| modulo by zero does not save | CalculatorService catches, re-raises without save | calculator_service.py | test_calculator_service.py |
| power with negative exponents | Native Python ** operator; e.g., 2 ** -1 = 0.5 | calculator.py | test_calculator.py |
| power with fractional exponents | Native Python ** operator; e.g., 4 ** 0.5 = 2.0 | calculator.py | test_calculator.py |
| No existing ops duplicated/renamed | Only add new enum members and methods; no modification of existing | operation.py, calculator.py | All tests pass for ADD, SUBTRACT, MULTIPLY, DIVIDE |
| Menu includes new operations | Add 4 tuples to _MENU list | calculator_cli.py | test_cli.py |

## Key Constraints and Patterns

1. **Consistent Dispatch Pattern**: All operations route through Calculator.calculate(Operation, a, b) -> dispatch dict -> instance method. New methods must be in both places.

2. **Two-Operand Signature**: Despite single-operand nature, square and sqrt methods must accept (a, b) for consistency. They simply ignore b.

3. **Error Handling Consistency**: Errors raised in Calculator methods are caught in CalculatorService.perform(), preventing storage of failed results. Must match this pattern.

4. **Operation Name Storage**: CalculationResult stores operation as a string (operation.value), not the enum. Symbols dict keys must match string values exactly.

5. **Menu Auto-Numbering**: CLI menu numbers auto-derive from list position. Adding 4 items will shift "View history" and "Exit" options down, but numeric logic is already relative.

6. **No Dependencies**: All operations use only math.sqrt() from stdlib; no new external dependencies required.

## Scope Boundaries

In scope:
- Add square, sqrt, power, modulo methods and enum members
- Error handling for sqrt(negative) and modulo(zero)
- Display formatting for new operations
- Menu integration and tests

Explicitly out of scope:
- Modifying existing operations (add, subtract, multiply, divide)
- Changing CalculationResult schema or storage format
- Changing interaction flow or CLI menu navigation logic
- Modifying baseline/ reference projects

## Implementation Order

1. operation.py: Add 4 enum members
2. calculator.py: Add 4 methods + update dispatch dict
3. calculation_result.py: Add symbols + update __str__
4. calculator_cli.py: Add 4 menu entries
5. tests/: Add comprehensive tests for all new operations and error cases
6. Verify: Run pytest; check no regressions in existing tests
