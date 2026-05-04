import math

from ..models.operation import Operation
from .calculator import Calculator


class ScientificCalculator(Calculator):
    """Extended calculator with trigonometric, logarithmic, and exponential operations.

    Inherits all basic and advanced operations from Calculator:
    - add, subtract, multiply, divide
    - square, sqrt, power, modulo

    Adds scientific operations:
    - sin, cos, tan (trigonometric)
    - log (base 10), ln (natural logarithm)
    - exp (exponential e^x)
    """

    def sin(self, a: float, b: float = 0) -> float:
        """Compute sine of a (in radians)."""
        return math.sin(a)

    def cos(self, a: float, b: float = 0) -> float:
        """Compute cosine of a (in radians)."""
        return math.cos(a)

    def tan(self, a: float, b: float = 0) -> float:
        """Compute tangent of a (in radians)."""
        return math.tan(a)

    def log(self, a: float, b: float = 0) -> float:
        """Compute logarithm base 10 of a.

        Args:
            a: Value must be positive (> 0)
            b: Unused (for dispatch compatibility)

        Raises:
            ValueError: If a <= 0
        """
        if a <= 0:
            raise ValueError("Logarithm is not defined for non-positive values")
        return math.log10(a)

    def ln(self, a: float, b: float = 0) -> float:
        """Compute natural logarithm (base e) of a.

        Args:
            a: Value must be positive (> 0)
            b: Unused (for dispatch compatibility)

        Raises:
            ValueError: If a <= 0
        """
        if a <= 0:
            raise ValueError("Natural logarithm is not defined for non-positive values")
        return math.log(a)

    def exp(self, a: float, b: float = 0) -> float:
        """Compute exponential function e^a."""
        return math.exp(a)

    def calculate(self, operation: Operation, a: float, b: float) -> float:
        """Execute a calculation with the given operation and operands.

        Extends the parent Calculator.calculate() to support scientific operations.

        Args:
            operation: Operation enum member (includes SIN, COS, TAN, LOG, LN, EXP)
            a: First operand (or sole operand for unary operations)
            b: Second operand (unused for unary operations)

        Returns:
            Result of the calculation as float

        Raises:
            ValueError: If operation is unsupported or domain errors occur
        """
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
