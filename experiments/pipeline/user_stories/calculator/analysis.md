# Task 02 Analysis: Advanced Operations (square, sqrt, power, modulo)

## Task Summary

Implement four new operations for the calculator: `square(x)`, `sqrt(x)`, `power(x, y)`, and `modulo(x, y)`. These must follow the same interface pattern as existing operations (`add`, `subtract`, etc.) and be accessible both through an interactive menu and one-shot CLI flags.

## Current Structure

### Operation Enum
**File**: `src/models/operation.py`

Currently defines four operations:
- `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE`

Each has:
- A string value (e.g., `"add"`)
- A `from_string(value)` class method for parsing CLI input
- A `display_name()` method for menu display

Pattern: `Operation(Enum)` with value binding to lowercase string.

### Calculator Class
**File**: `src/services/calculator.py`

Implements four methods:
- `add(a, b)`, `subtract(a, b)`, `multiply(a, b)`, `divide(a, b)` — all `(float, float) -> float`
- `divide()` guards against division by zero with `ValueError`
- `calculate(operation: Operation, a: float, b: float) -> float` — dispatcher that maps Operation enum to method via dictionary

**Interface Pattern**: All methods are binary (two operands). New operations must follow the same signature.

### CalculationResult Dataclass
**File**: `src/models/calculation_result.py`

Stores:
- `operation: str` — the operation name (e.g., `"add"`)
- `operand_a: float`, `operand_b: float` — input values
- `result: float` — the result
- `timestamp: str`, `execution_time_ms: float` — metadata

The `__str__()` method uses a `_SYMBOLS` dict mapping operation names to display symbols.

**Key observation**: `operand_b` is always populated, even for unary operations. This is a constraint imposed by the current dataclass structure.

### CalculatorService
**File**: `src/services/calculator_service.py`

- `perform(operation: Operation, a: float, b: float) -> CalculationResult` — calls `Calculator.calculate()`, wraps result in CalculationResult, saves to storage
- Handles timing via `time.perf_counter()`
- Always saves successful results to storage

### CLI Layer
**File**: `src/cli/calculator_cli.py`

- **Interactive**: `_MENU` list of `(Operation, str)` tuples displayed as numbered choices
- **One-shot**: `run_command(operation_str, a, b)` — calls `Operation.from_string()` to parse, then calls `service.perform()`
- Menu dynamically adds "View history" and "Exit" options based on `len(_MENU)`

### Entry Point
**File**: `src/__main__.py`

- `argparse` parser with `--operation {add,subtract,multiply,divide}` choices
- Positional `operands` for numeric arguments
- Validation: exactly 2 operands required when using `--operation`
- Help text documents available operations

## How Operations Are Exposed

### Interactive Menu
1. `CalculatorCLI._MENU` contains tuples of `(Operation, label)` — used to render the menu
2. `run_interactive()` loops, printing the menu with numbered choices
3. User input parsed by `_resolve_menu_choice()` which indexes into `_MENU`

**Adding a new operation**: Add a tuple `(Operation.SQUARE, "Square")` to `_MENU`.

### CLI Flags (One-Shot)
1. `argparse` parser defines `--operation` with explicit `choices=['add', ...]`
2. User provides `--operation <op> <arg1> <arg2>`
3. `run_command()` calls `Operation.from_string(operation_str)` which raises `ValueError` if not recognized
4. `_as_number()` validates operands as floats

**Adding a new operation**: 
1. Add operation name to `argparse` choices
2. Operation must exist in `Operation` enum so `from_string()` can find it
3. Operation must be callable in `Calculator.calculate()`

## Ambiguities and Constraints

### 1. Unary vs. Binary Operations
**Issue**: The current system is strictly binary.
- `CalculationResult` has `operand_a` and `operand_b` (both floats)
- `Calculator.calculate(operation, a, b)` always takes two operands
- CLI `run_command()` always validates exactly 2 operands

**Required operations**:
- `square(x)` — unary, mathematically x²
- `sqrt(x)` — unary, mathematically √x
- `power(x, y)` — binary, x^y
- `modulo(x, y)` — binary, x % y

**Assumption to move forward**: 
We will adapt the unary operations (`square`, `sqrt`) to the binary interface by requiring the second operand but ignoring it. This preserves the existing dataclass and CLI validation logic.

For `square(x)`: pass `x` as `operand_a`, and a dummy value (e.g., `0` or `1`) as `operand_b`.
For `sqrt(x)`: same approach.

**Alternative** (not chosen here): Refactor CalculationResult to support variable arity — but this breaks the current design and would require changes throughout the stack.

### 2. Error Handling for sqrt(negative)
**Requirement**: "sqrt of a negative number raises an error or returns a defined error result"

**Current pattern**: Division by zero raises `ValueError` in `Calculator.divide()`, which propagates up and is caught in `CalculatorCLI.run_command()` (exits with error) and in interactive mode (caught in try/except, prints error message).

**Implementation approach**: 
- `Calculator.sqrt(x)` should check `x < 0` and raise `ValueError("Cannot take square root of negative number")`
- Same error handling path as division by zero

### 3. Modulo by Zero
**Requirement**: "modulo by zero raises an error"

**Implementation approach**:
- `Calculator.modulo(x, y)` should check `y == 0` and raise `ValueError("Modulo by zero is not allowed")`
- Same error handling path as division by zero

### 4. Power with Fractional/Negative Exponents
**Requirement**: "power with negative or fractional exponents returns correct results"

**Current state**: Python's `**` operator handles all exponent types natively.
- `power(2, -1)` → 0.5 ✓
- `power(4, 0.5)` → 2.0 ✓
- `power(-8, 1/3)` → complex number (Python returns complex, not real cube root)

**Implementation approach**:
- Use Python's `**` operator directly: `result = a ** b`
- No special guards needed (fractional/negative exponents are valid)
- Note: Raising a negative number to a fractional exponent may return complex — this is mathematically correct but will fail when storing in `result: float`

**Assumption**: We accept that complex results will cause a runtime error. The acceptance criteria say "returns correct results" which implies real results; complex results are out of scope.

### 5. Display Symbols
**Current**: `_SYMBOLS = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}`

**For new operations**, we need to add symbols:
- `"square"`: `"²"` (superscript 2) or `"^2"`
- `"sqrt"`: `"√"` or `"√x"`
- `"power"`: `"^"` or `"**"`
- `"modulo"`: `"%"`

**Assumption**: Use math symbols where possible. If encoding is problematic, fall back to ASCII (e.g., `"^2"` instead of `"²"`).

## Required Changes

### 1. Operation Enum
**File**: `src/models/operation.py`

Add four new enum members:
```python
SQUARE = "square"
SQRT = "sqrt"
POWER = "power"
MODULO = "modulo"
```

No changes to `from_string()` or `display_name()` — they are generic.

### 2. Calculator Class
**File**: `src/services/calculator.py`

Add four new methods:
- `square(a: float, b: float) -> float` — ignores b, returns a²
- `sqrt(a: float, b: float) -> float` — ignores b, checks a >= 0, returns √a
- `power(a: float, b: float) -> float` — returns a^b (handles negative/fractional exponents)
- `modulo(a: float, b: float) -> float` — checks b != 0, returns a % b

Update `calculate()` dispatcher to add these four operations to the dispatch dictionary.

Error handling:
- `sqrt()` raises `ValueError("Cannot take square root of negative number")` if a < 0
- `modulo()` raises `ValueError("Modulo by zero is not allowed")` if b == 0

### 3. CalculationResult
**File**: `src/models/calculation_result.py`

Update `_SYMBOLS` dict to include:
```python
"square": "²",  # or "^2" if encoding issues
"sqrt": "√",    # or "sqrt" if encoding issues
"power": "^",   # or "**"
"modulo": "%"
```

No changes to the dataclass structure itself.

### 4. CLI Class
**File**: `src/cli/calculator_cli.py`

Update `_MENU` to add four new entries:
```python
_MENU: list[tuple[Operation, str]] = [
    (Operation.ADD,      "Add"),
    (Operation.SUBTRACT, "Subtract"),
    (Operation.MULTIPLY, "Multiply"),
    (Operation.DIVIDE,   "Divide"),
    (Operation.SQUARE,   "Square"),     # NEW
    (Operation.SQRT,     "Square Root"), # NEW
    (Operation.POWER,    "Power"),       # NEW
    (Operation.MODULO,   "Modulo"),      # NEW
]
```

The rest of the class (`run_interactive()`, `run_command()`, etc.) requires no changes — it is menu-driven.

### 5. Entry Point (__main__.py)
**File**: `src/__main__.py`

Update `argparse` to include new operation names:
```python
choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"]
```

Update usage string (optional):
```python
usage="python -m src [--operation {add,subtract,...,modulo} A B]"
```

No changes to validation or dispatch logic.

## Integration Points

### Order of Integration
1. **Operation Enum** — must come first; everything depends on it
2. **Calculator methods** — add arithmetic implementations and error guards
3. **Calculator.calculate() dispatch** — register the new methods
4. **CalculationResult symbols** — for display only, doesn't block testing
5. **CalculatorCLI menu** — for interactive mode
6. **argparse choices** — for one-shot mode
7. **Tests** — verify each component

### No Changes Required To
- `CalculatorService` — already generic over Operation
- `JsonStorage` — already stores any CalculationResult
- `_prompt_number()`, `_resolve_menu_choice()`, `run_interactive()` flow — all generic

## Files to Modify

| File | Changes | Type |
|------|---------|------|
| `src/models/operation.py` | Add SQUARE, SQRT, POWER, MODULO enum members | Enum extension |
| `src/services/calculator.py` | Add square(), sqrt(), power(), modulo() methods; update calculate() dispatcher | Methods + dispatch |
| `src/models/calculation_result.py` | Add symbols for new operations in _SYMBOLS dict | Display config |
| `src/cli/calculator_cli.py` | Add 4 entries to _MENU list | Menu config |
| `src/__main__.py` | Update argparse choices to include new operation names | CLI config |
| `tests/test_calculator.py` | Add ~12 tests for new Calculator methods (normal cases + error cases) | New tests |
| `tests/test_calculator_service.py` | Add ~8 tests for service integration with new operations | New tests |
| `tests/test_cli.py` | Add ~8 tests for CLI with new operations (interactive + one-shot) | New tests |
| `artifacts/class_diagram.puml` | Add new methods to Calculator class | Diagram update |

## Test Patterns

### Existing Test Structure

**Calculator tests** (`test_calculator.py`):
- Unit tests for each operation method
- Test normal cases, edge cases (negative, zero, floats)
- Test error conditions (e.g., `divide(5, 0)` raises)
- Test dispatcher (`calculate()`) with all operations

Example:
```python
def test_divide_by_zero_raises(self):
    with pytest.raises(ValueError, match="Division by zero"):
        self.calc.divide(5, 0)
```

**Service tests** (`test_calculator_service.py`):
- Test `perform()` method with each operation
- Verify result structure (operation, operands, result)
- Verify storage is called
- Verify errors don't save to storage
- Verify timestamp is set

Example:
```python
def test_perform_divide_by_zero_does_not_save(self):
    with pytest.raises(ValueError):
        self.service.perform(Operation.DIVIDE, 5, 0)
    self.storage.save.assert_not_called()
```

**CLI tests** (`test_cli.py`):
- Test `run_command()` with valid operation (checks output)
- Test `run_command()` with invalid operation (checks SystemExit)
- Test service errors (side_effect = ValueError) cause exit
- Test interactive menu with mocked `input()` and `service`
- Verify menu choices work and invalid input retries

Example:
```python
def test_invalid_operation_exits(self):
    cli, _ = _make_cli()
    with pytest.raises(SystemExit):
        cli.run_command("modulo", 3, 5)  # Currently invalid
```

### New Tests Required

**For Calculator**:
1. `test_square_positive` — square(3) == 9
2. `test_square_negative` — square(-2) == 4
3. `test_square_zero` — square(0) == 0
4. `test_square_float` — square(2.5) ≈ 6.25
5. `test_sqrt_positive` — sqrt(9) == 3.0
6. `test_sqrt_float` — sqrt(2.5) ≈ 1.58...
7. `test_sqrt_zero` — sqrt(0) == 0.0
8. `test_sqrt_negative_raises` — sqrt(-1) raises ValueError
9. `test_power_positive_exponent` — power(2, 3) == 8
10. `test_power_negative_exponent` — power(2, -1) == 0.5
11. `test_power_fractional_exponent` — power(4, 0.5) ≈ 2.0
12. `test_power_zero_exponent` — power(99, 0) == 1.0
13. `test_modulo_positive` — modulo(10, 3) == 1
14. `test_modulo_negative_dividend` — modulo(-10, 3) == 2 (Python semantics)
15. `test_modulo_negative_divisor` — modulo(10, -3) == -2
16. `test_modulo_zero_divisor_raises` — modulo(5, 0) raises ValueError
17. `test_calculate_dispatches_new_operations` — verify all 4 operations in dispatcher

**For CalculatorService**:
1. `test_perform_square` — service.perform(Operation.SQUARE, 3, X) → result=9
2. `test_perform_sqrt` — service.perform(Operation.SQRT, 9, X) → result=3.0
3. `test_perform_sqrt_negative_raises` — service.perform(..., -1, X) raises and doesn't save
4. `test_perform_power` — service.perform(Operation.POWER, 2, 3) → result=8
5. `test_perform_modulo` — service.perform(Operation.MODULO, 10, 3) → result=1
6. `test_perform_modulo_zero_raises` — service.perform(..., 5, 0) raises and doesn't save

**For CLI**:
1. `test_run_command_square` — checks output contains "9"
2. `test_run_command_sqrt` — checks output contains "3"
3. `test_run_command_power` — checks output contains "8"
4. `test_run_command_modulo` — checks output contains "1"
5. `test_interactive_square_choice` — mocked input ["2", "3", dummy, "exit"]
6. `test_interactive_sqrt_with_negative_error` — shows error message
7. `test_interactive_modulo_by_zero_error` — shows error message

**Total new tests**: ~28 tests (on top of current 71, yielding ~99 total)

## Display Output Example

Current behavior:
```
$ python -m src --operation add 3 5
3 + 5 = 8
```

Expected with new operations:
```
$ python -m src --operation square 4 0
4 ² 0 = 16

$ python -m src --operation sqrt 9 0
9 √ 0 = 3.0

$ python -m src --operation power 2 3
2 ^ 3 = 8

$ python -m src --operation modulo 10 3
10 % 3 = 1
```

Note: The middle operand in the display is the dummy value (for unary operations). This is acceptable given the current dataclass design. A future refactor could hide it (e.g., only display operand_b for operations that truly need it).

