import math

from ..models.operation import Operation


class Calculator:
    """Concrete implementation of the CalculationEngine protocol.

    Provides pure arithmetic and scientific calculation logic.
    No knowledge of persistence or user interface.
    """
    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b

    def square(self, a: float, b: float) -> float:
        """Return the square of the first operand (b is ignored)."""
        return a * a

    def sqrt(self, a: float, b: float) -> float:
        """Return the square root of the first operand (b is ignored)."""
        if a < 0:
            raise ValueError("Square root of a negative number is not allowed")
        return math.sqrt(a)

    def power(self, a: float, b: float) -> float:
        """Return a raised to the power of b."""
        return a ** b

    def modulo(self, a: float, b: float) -> float:
        """Return the remainder of a divided by b."""
        if b == 0:
            raise ValueError("Modulo by zero is not allowed")
        return a % b

    def sin(self, a: float, b: float) -> float:
        """Return the sine of the first operand (b is ignored). Angle in radians."""
        return math.sin(a)

    def cos(self, a: float, b: float) -> float:
        """Return the cosine of the first operand (b is ignored). Angle in radians."""
        return math.cos(a)

    def tan(self, a: float, b: float) -> float:
        """Return the tangent of the first operand (b is ignored). Angle in radians."""
        return math.tan(a)

    def log(self, a: float, b: float) -> float:
        """Return the base-10 logarithm of the first operand (b is ignored)."""
        if a <= 0:
            raise ValueError("Logarithm of zero or negative number is not allowed")
        return math.log10(a)

    def ln(self, a: float, b: float) -> float:
        """Return the natural logarithm of the first operand (b is ignored)."""
        if a <= 0:
            raise ValueError("Natural logarithm of zero or negative number is not allowed")
        return math.log(a)

    def exp(self, a: float, b: float) -> float:
        """Return e raised to the power of the first operand (b is ignored)."""
        return math.exp(a)

    def calculate(self, operation: Operation, a: float, b: float) -> float:
        dispatch = {
            Operation.ADD: self.add,
            Operation.SUBTRACT: self.subtract,
            Operation.MULTIPLY: self.multiply,
            Operation.DIVIDE: self.divide,
            Operation.SQUARE: self.square,
            Operation.SQRT: self.sqrt,
            Operation.POWER: self.power,
            Operation.MODULO: self.modulo,
            Operation.SIN: self.sin,
            Operation.COS: self.cos,
            Operation.TAN: self.tan,
            Operation.LOG: self.log,
            Operation.LN: self.ln,
            Operation.EXP: self.exp,
        }
        if operation not in dispatch:
            raise ValueError(f"Unsupported operation: {operation}")
        return dispatch[operation](a, b)
