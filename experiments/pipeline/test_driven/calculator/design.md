# Design for Task 02 — Add Square, Sqrt, Power, and Modulo to Calculator

## Summary

Add four new operations to the Calculator class:
1. `square(a: float) -> float` — unary, always succeeds
2. `sqrt(a: float) -> float` — unary, raises ValueError if a < 0
3. `power(a: float, b: float) -> float` — binary, supports all exponents
4. `modulo(a: float, b: float) -> float` — binary, raises ValueError if b == 0

## Files to Modify

### 1. src/models/operation.py

**Change:** Add four new enum members after the DIVIDE member.

Current:
```python
DIVIDE = "divide"
```

Add after:
```python
SQUARE = "square"
SQRT = "sqrt"
POWER = "power"
MODULO = "modulo"
```

**Reason:** The dispatcher and CLI need to recognize new operations.

---

### 2. src/services/calculator.py

**Change:** Add four new methods to the Calculator class.

Add these methods to the class (append at the end, before the closing brace):

```python
def square(self, a: float) -> float:
    return a * a

def sqrt(self, a: float) -> float:
    if a < 0:
        raise ValueError("Square root of negative number is not allowed")
    return a ** 0.5

def power(self, a: float, b: float) -> float:
    return a ** b

def modulo(self, a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Modulo by zero is not allowed")
    return a % b
```

**Reason:** Implement the mathematical operations. Use ValueError for domain errors (consistent with divide()).

**Important:** Do NOT modify the `calculate()` dispatcher. Unary operations (square, sqrt) are not added to the dispatcher; they remain callable only via direct method calls.

---

### 3. src/models/calculation_result.py

**Change:** Extend the `_SYMBOLS` dictionary to include four new operations.

Current (line 5):
```python
_SYMBOLS = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}
```

Replace with:
```python
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
```

**Reason:** Provide proper symbol display for calculation results.

---

### 4. src/cli/calculator_cli.py

**Change:** Add four new operations to the `_MENU` list.

Current (lines 8-13):
```python
_MENU: list[tuple[Operation, str]] = [
    (Operation.ADD,      "Add"),
    (Operation.SUBTRACT, "Subtract"),
    (Operation.MULTIPLY, "Multiply"),
    (Operation.DIVIDE,   "Divide"),
]
```

Replace with:
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

**Reason:** Add operations to the interactive menu for user accessibility.

---

## Implementation Notes

### Edge Cases Handled

- **sqrt(negative):** Raises ValueError
- **modulo(x, 0):** Raises ValueError  
- **power(negative_base, fractional_exponent):** Delegates to Python's `**` operator
- **square() and sqrt():** Unary operations; NOT added to the dispatcher (known limitation documented for future work)

### Exception Handling

All domain errors use `ValueError` with descriptive messages, consistent with the existing `divide()` method pattern.

### No Other Changes Required

- The `calculate()` dispatcher remains unchanged (unary operations don't need dispatcher support)
- Calculator service and JSON storage work with any enum member automatically
- Tests that check for invalid operations may need updates (test_cli.py line 24 will need attention after implementation)

---

## Implementation Order

1. Update `src/models/operation.py` — Add enum members
2. Update `src/services/calculator.py` — Add methods
3. Update `src/models/calculation_result.py` — Add symbols
4. Update `src/cli/calculator_cli.py` — Add menu entries

This order ensures dependencies are resolved correctly.
