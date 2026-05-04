# Task 08 Analysis: ScientificCalculator Implementation

## Task Overview

Implement a `ScientificCalculator` class that extends the existing calculator functionality with trigonometric, logarithmic, and exponential operations. The new class must reuse existing `Calculator` logic (composition or inheritance) and expose all operations via `python -m src` (both interactive menu and CLI flags).

**Operations to implement:**
1. `sin(x)` — trigonometric sine
2. `cos(x)` — trigonometric cosine
3. `tan(x)` — trigonometric tangent
4. `log(x)` — logarithm base 10 (raises Exception for x <= 0)
5. `ln(x)` — natural logarithm base e
6. `exp(x)` — exponential function e^x

**Existing operations must still work:**
- `add(a, b)`, `subtract(a, b)`, `multiply(a, b)`, `divide(a, b)` (from Calculator)
- `square(a)`, `sqrt(a)`, `power(a, b)`, `modulo(a, b)` (already in Calculator)

## Current State: Source Code Structure

### Existing Calculator Class
**Location:** `src/services/calculator.py`

Contains 8 methods:
- Basic operations: `add()`, `subtract()`, `multiply()`, `divide()`
- Advanced operations: `square()`, `sqrt()`, `power()`, `modulo()`
- Dispatch method: `calculate(operation: Operation, a: float, b: float)` with dispatch table

**Key observations:**
- Single-responsibility: core math operations only
- Uses Python `math` module for sqrt and (implicitly) for power
- Error handling: raises `ValueError` for division by zero and sqrt of negative
- Dispatch pattern: maps Operation enum members to method references

### Operation Enum
**Location:** `src/models/operation.py`

Defines 8 enum members:
- ADD, SUBTRACT, MULTIPLY, DIVIDE, SQUARE, SQRT, POWER, MODULO
- Has `from_string(value: str)` classmethod for CLI parsing
- Has `display_name()` method for UI output

**Observation:** No scientific operations defined yet (SIN, COS, TAN, LOG, LN, EXP)

### CalculatorService (Orchestration Layer)
**Location:** `src/services/calculator_service.py`

- Wraps Calculator and JsonStorage
- `perform(operation: Operation, a: float, b: float) -> CalculationResult` — executes and persists calculations
- `get_history() -> list[CalculationResult]` — retrieves stored results
- Times execution and records it in CalculationResult

**Observation:** Service expects Operation enum and calls `calculator.calculate(operation, a, b)`

### CLI Integration Points
**Entry Point:** `src/__main__.py`
- Hard-coded operation choices: `["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"]` (line 43)
- Usage string lists same 8 operations (line 38)
- Requires CLI updates to expose new operations

**Interactive Menu:** `src/cli/calculator_cli.py`
- Static `_MENU` list with 8 (Operation, label) tuples (lines 10-19)
- Menu numbering and dispatch logic tied to `_MENU` length
- Requires menu update to include scientific operations

## Files That Exist vs. Missing

### Existing
- ✓ `src/services/calculator.py` — base Calculator with 8 operations
- ✓ `src/services/calculator_service.py` — orchestration layer
- ✓ `src/models/operation.py` — Operation enum (8 members)
- ✓ `src/__main__.py` — CLI entry point
- ✓ `src/cli/calculator_cli.py` — interactive menu
- ✓ `src/__init__.py`, `src/services/__init__.py`, `src/models/__init__.py` — package exports
- ✓ `tests/test_advanced_operations.py` — comprehensive test suite for existing operations
- ✓ `artifacts/class_diagram.puml` — UML class diagram

### Missing (Must Create)
- ✗ `src/services/scientific_calculator.py` — ScientificCalculator class
- ✗ Test file for scientific operations (user said tests are provided, so this may be added by tester)
- ✗ Extensions to Operation enum to add SIN, COS, TAN, LOG, LN, EXP

## Test Suite Requirements

From prompt.txt, 8 test cases:
1. `test_scientific_calculator_exists()` — instantiation works
2. `test_sin()` — sin(0) ≈ 0.0
3. `test_cos()` — cos(0) ≈ 1.0
4. `test_tan()` — tan(0) ≈ 0.0
5. `test_log_base_10()` — log(100) ≈ 2.0
6. `test_log_of_non_positive_raises()` — log(0) raises Exception, log(-1) raises Exception
7. `test_ln()` — ln(e) ≈ 1.0
8. `test_exp()` — exp(1) ≈ e
9. `test_standard_operations_still_work()` — ScientificCalculator.add(2, 3) == 5, ScientificCalculator.divide(10, 2) == 5

**Key constraint:** Imports from `src.services.scientific_calculator import ScientificCalculator` — must be accessible from services package

## Identified Gaps and Missing Pieces

### 1. ScientificCalculator Class Missing
- Must be at `src/services/scientific_calculator.py`
- Must provide methods: `sin()`, `cos()`, `tan()`, `log()`, `ln()`, `exp()`
- Must inherit from or wrap Calculator to reuse `add()`, `subtract()`, etc.
- All methods should follow Calculator's style: take float args, return float, raise Exception on domain errors

### 2. Operation Enum Must Extend
- Add 6 new enum members: SIN, COS, TAN, LOG, LN, EXP
- Each needs a string value (e.g., "sin", "cos", "tan", "log", "ln", "exp")
- Required for dispatch logic and CLI parsing

### 3. CLI Hard-Coded Values Must Update
- `src/__main__.py` line 43: operation choices list
- `src/__main__.py` line 38: usage string
- Must include new operation strings

### 4. Interactive Menu Must Extend
- `src/cli/calculator_cli.py` line 10-19: _MENU list
- Add 6 new menu entries with (Operation, label) tuples
- Labels could be: "Sine", "Cosine", "Tangent", "Logarithm (base 10)", "Natural Logarithm", "Exponential"

### 5. Calculator.calculate() Dispatch Must Extend
- Update dispatch table in `src/services/calculator.py` (lines 38-50)
- Must handle new Operation enum members
- Must route to corresponding ScientificCalculator methods

### 6. Package Exports May Need Update
- `src/services/__init__.py` — may need to add ScientificCalculator to exports (depends on how other services are integrated)

## Architectural Observations

### How to Extend Calculator Without Duplication

**Option A: Inheritance (Recommended by Task)**
```python
class ScientificCalculator(Calculator):
    def sin(self, x: float) -> float:
        return math.sin(x)
    # ... other scientific operations ...
    # inherit add, subtract, multiply, divide, square, sqrt, power, modulo from parent
```

**Option B: Composition**
```python
class ScientificCalculator:
    def __init__(self):
        self.calc = Calculator()
    
    def add(self, a, b):
        return self.calc.add(a, b)  # delegate
    # ... reimplement all Calculator methods ...
    def sin(self, x):
        return math.sin(x)
```

Task requirement says "Do not reimplement basic operations" and "extend or reuse existing Calculator logic" → **Inheritance is correct choice.**

### Integration with CalculatorService

Current flow:
1. CLI calls `CalculatorService.perform(operation, a, b)`
2. Service calls `calculator.calculate(operation, a, b)`
3. Calculator uses dispatch table

**Question:** Will CalculatorService receive a ScientificCalculator instance instead of Calculator?

Looking at `src/__main__.py` line 16:
```python
return CalculatorService(Calculator(), JsonStorage(storage_path))
```

For scientific operations to work through CalculatorService, either:
- Option 1: Change line 16 to `ScientificCalculator()` instead of `Calculator()`
- Option 2: Keep Calculator but ScientificCalculator duplicates dispatch logic (violates task rule)

**Most likely:** Change __main__.py to use ScientificCalculator (since it's a drop-in subclass, polymorphism works)

### Domain Error Handling

Tests expect:
- `log(0)` raises Exception
- `log(negative)` raises Exception
- `ln(0)` raises Exception (implied by math domain)
- `sqrt(negative)` already raises ValueError in Calculator

All unary scientific operations should validate input and raise ValueError with clear message.

## CLI Exposure Requirements

From experiment governance:
- "All functionality must be reachable via `python -m src`"
- Must support both: interactive menu + one-shot CLI flag
- No internal-only implementations allowed

**Required CLI additions:**
1. Update argparse choices to include: sin, cos, tan, log, ln, exp
2. Update usage string to show new operations
3. Update interactive menu (_MENU list) to show new operations as menu items
4. Each scientific operation takes 1 argument (unary), so CLI must handle --operation flag with 1 operand

**Current constraint:** argparse setup assumes all operations need 2 operands (checks `len(args.operands) != 2` on line 71)

**Problem to solve:** How to handle unary operations in CLI that expects 2 operands?

Looking at existing Calculator: `square()` and `sqrt()` are unary but have optional `b=0` parameter for dispatch compatibility. Same pattern must apply to scientific operations.

## Summary: Scope In vs. Out

**In Scope (Task 08):**
- Implement ScientificCalculator class with 6 new methods
- Extend Operation enum with 6 new members
- Update __main__.py to expose new operations via CLI
- Update CalculatorCLI menu to show new operations
- All tests pass
- Existing tests still pass
- Code compiles without errors

**Borderline (Likely In Scope):**
- Update CalculatorService to use ScientificCalculator instead of Calculator
- Update artifact diagrams to show new ScientificCalculator class and operations

**Out of Scope:**
- GUI implementation (not mentioned)
- Persist scientific calculations to storage (existing storage already does this)
- Create new test file (tests are provided in prompt)

## Suggested Priorities

1. **HIGH:** Implement ScientificCalculator class with inheritance from Calculator
   - Directly unblocks tests
   - Foundation for everything else

2. **HIGH:** Extend Operation enum to add 6 scientific operations
   - Required for dispatch logic
   - Required for CLI parsing

3. **HIGH:** Update Calculator.calculate() dispatch table
   - Required for operations to be executable

4. **HIGH:** Update __main__.py CLI argument parsing
   - Required to expose scientific operations via CLI
   - Handle unary operations constraint (all use b=0 pattern)

5. **MEDIUM:** Update CalculatorCLI interactive menu
   - Required for "python -m src" interactive mode to show new operations
   - Governance rule: all functionality must be reachable via CLI

6. **MEDIUM:** Update __main__.py to use ScientificCalculator
   - Ensures operations work through normal CalculatorService flow
   - Makes operations persist to history correctly

7. **LOW:** Update package exports in src/services/__init__.py
   - May be needed if ScientificCalculator must be publicly exported
   - Check existing import patterns first

8. **LOW:** Update UML diagrams (class_diagram.puml, component_diagram.puml)
   - Shows new ScientificCalculator class and relationships
   - Consistency with documentation

