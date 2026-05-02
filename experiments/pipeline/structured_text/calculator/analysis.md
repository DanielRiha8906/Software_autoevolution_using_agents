# Task 02: Add Additional Mathematical Operations

## Task Requirements

Implement four new operations:
- **Must:** square (x²), sqrt(x), power(x, y), modulo(x, y) following existing interface
- **Must:** Handle edge cases: sqrt of negative, modulo by zero, negative/fractional exponents
- **Could:** Support operator aliases (e.g., '^' for power)
- **Won't:** Introduce duplicates or deviate from naming conventions

## Current Architecture Analysis

### Operation Enum Pattern (src/models/operation.py)
- Enum with 4 members: ADD, SUBTRACT, MULTIPLY, DIVIDE
- Maps to lowercase strings: Operation.ADD.value = "add"
- Methods: `from_string(value: str) -> Operation`, `display_name() -> str`

### Calculator Service Interface (src/services/calculator.py)
- Binary operations: `operation(a: float, b: float) -> float`
- Methods: add(), subtract(), multiply(), divide()
- Central dispatch: `calculate(operation: Operation, a: float, b: float) -> float`
- Error pattern: `raise ValueError("message")`
- Example: divide() checks if b == 0, raises ValueError("Division by zero is not allowed")

### Calculation Result Model (src/models/calculation_result.py)
- Fields: operation (str), operand_a (float), operand_b (float), result (float), timestamp (str), execution_time_ms (float)
- Display symbols in _SYMBOLS dict: {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}
- Format: `{operand_a} {symbol} {operand_b} = {result}`
- Methods: to_dict(), from_dict(), __str__()

### CLI Layer (src/cli/calculator_cli.py)
- Menu defined as list of (Operation, label) tuples
- Interactive mode: prompts for two operands
- One-shot mode: --operation flag with two operands
- Error handling: ValueError caught and printed to stderr

### Entry Point (src/__main__.py)
- argparse with --operation choices: ["add", "subtract", "multiply", "divide"]
- Both interactive and one-shot modes converge on service.perform()

## Critical Design Constraint: Unary vs Binary

**Problem:** Square and sqrt are mathematically unary (require one operand), but the system is entirely binary.

**Solution Chosen:** Adapt unary operations as binary with ignored second operand
- User provides two numbers; second is silently ignored in computation
- Example: `python -m src --operation square 5 0` (0 ignored)
- Display shows: "5 ^ = 25" (second operand omitted in rendering, or shown empty)
- Minimal interface changes; preserves existing patterns

## Edge Cases to Handle

1. **sqrt(negative):** raise ValueError("Cannot take square root of negative number")
2. **modulo by zero:** raise ValueError("Modulo by zero is not allowed")
3. **power(x, 0):** returns 1.0 (for any x)
4. **power(x, negative):** returns x^(-n) = 1/(x^n) — allowed
5. **power(x, fractional):** returns correct result (e.g., 4^0.5 = 2.0) — allowed
6. **square(any number):** always valid (no edge cases)
7. **modulo(negative operands):** Python % operator behavior — allowed

## Files Requiring Changes

**src/models/operation.py**
- Add enum members: SQUARE, SQRT, POWER, MODULO

**src/services/calculator.py**
- Import math module
- Add methods: square(a), sqrt(a), power(a, b), modulo(a, b) with error handling
- Update calculate() dispatch dict

**src/models/calculation_result.py**
- Add symbol mappings: {"square": "^", "sqrt": "√", "power": "^", "modulo": "%"}

**src/cli/calculator_cli.py**
- Add menu entries for SQUARE, SQRT, POWER, MODULO

**src/__main__.py**
- Update argparse choices to include: "square", "sqrt", "power", "modulo"

**tests/** (all test files)
- Add ~20-25 tests covering: basic math, edge cases, service integration, CLI behavior

## Implementation Notes

- No new external dependencies required (math module is standard library)
- Existing error handling pattern (raise ValueError) applies to both sqrt and modulo
- Symbol '√' and '%' are standard; power uses '^' to avoid conflict with Python's '**'
- Tests must validate both positive and negative paths for edge cases
