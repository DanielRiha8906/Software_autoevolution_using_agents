# Task 02 Design: Add Additional Mathematical Operations

## Overview

Implement four new mathematical operations (square, sqrt, power, modulo) following the existing binary operation pattern. Unary operations (square, sqrt) will accept two operands with the second silently ignored.

## Operation Enum Changes (src/models/operation.py)

Add four new enum members:
```python
SQUARE = "square"
SQRT = "sqrt"
POWER = "power"
MODULO = "modulo"
```

No changes to `from_string()` or `display_name()` methods needed—they work automatically with new members.

## Calculator Service Changes (src/services/calculator.py)

### New Import
```python
import math
```

### New Methods

#### square(a: float) -> float
```python
def square(self, a: float) -> float:
    return a ** 2
```

#### sqrt(a: float) -> float
```python
def sqrt(self, a: float) -> float:
    if a < 0:
        raise ValueError("Cannot take square root of negative number")
    return math.sqrt(a)
```

#### power(a: float, b: float) -> float
```python
def power(self, a: float, b: float) -> float:
    return a ** b
```

#### modulo(a: float, b: float) -> float
```python
def modulo(self, a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Modulo by zero is not allowed")
    return a % b
```

### Update calculate() Dispatch

Modify dispatch dict to include:
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

## Calculation Result Changes (src/models/calculation_result.py)

Update _SYMBOLS dict:
```python
_SYMBOLS = {
    "add": "+",
    "subtract": "-",
    "multiply": "×",
    "divide": "÷",
    "square": "^",
    "sqrt": "√",
    "power": "^",
    "modulo": "%"
}
```

No changes to `__str__()` method needed.

## CLI Menu Changes (src/cli/calculator_cli.py)

Update _MENU list:
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

## Entry Point Changes (src/__main__.py)

Update argparse choices:
```python
choices=["add", "subtract", "multiply", "divide", "square", "sqrt", "power", "modulo"]
```

## Test Coverage (for pytest-tester)

### test_calculator.py (~14 tests)
- square: positive, zero, negative, float
- sqrt: perfect square, zero, fraction, negative (error)
- power: positive exponent, zero exponent, negative exponent, fractional
- modulo: basic, by zero (error)

### test_calculator_service.py (~8 tests)
- perform() for each operation
- Error handling and non-persistence for invalid cases
- Dispatch verification

### test_cli.py (~6 tests)
- One-shot mode for each operation
- Error cases (sqrt negative, modulo zero) exit with error

## Implementation Order

1. operation.py — Add enum members
2. calculator.py — Add methods and update dispatch
3. calculation_result.py — Update symbols
4. calculator_cli.py — Add menu entries
5. __main__.py — Update argparse choices

## Edge Cases Handled

- sqrt(negative) → ValueError
- modulo(_, 0) → ValueError
- 0^0 → 1.0 (Python convention, accepted)
- Negative/fractional exponents → Allowed
- Backward compatibility → All changes additive
