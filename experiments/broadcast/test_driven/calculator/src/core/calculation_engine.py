"""Abstract calculation engine protocol and base implementation.

This module defines the interface for calculation engines and provides
the core pure calculation logic without any side effects.
"""

from typing import Protocol
import math

from ..models.operation import Operation


class CalculationEngine(Protocol):
    """Protocol defining the contract for a calculation engine.

    Any implementation of this protocol must support basic arithmetic,
    power/modulo, and square root operations.
    """

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        ...

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        ...

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        ...

    def divide(self, a: float, b: float) -> float:
        """Divide a by b. Raises ValueError if b is zero."""
        ...

    def square(self, x: float) -> float:
        """Square a number."""
        ...

    def sqrt(self, x: float) -> float:
        """Calculate square root. Raises Exception if x is negative."""
        ...

    def power(self, x: float, y: float) -> float:
        """Raise x to the power of y."""
        ...

    def modulo(self, x: float, y: float) -> float:
        """Calculate x modulo y. Raises Exception if y is zero."""
        ...

    def calculate(self, operation: Operation, a: float, b: float) -> float:
        """Dispatch a calculation based on operation type."""
        ...


class BasicCalculationEngine:
    """Pure calculation logic for basic arithmetic and mathematical operations.

    This is a stateless calculation engine that contains no side effects,
    no dependencies on storage, history, or CLI. It implements the
    CalculationEngine protocol.
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

    def square(self, x: float) -> float:
        return x * x

    def sqrt(self, x: float) -> float:
        if x < 0:
            raise Exception("Cannot compute square root of negative number")
        return math.sqrt(x)

    def power(self, x: float, y: float) -> float:
        return x ** y

    def modulo(self, x: float, y: float) -> float:
        if y == 0:
            raise Exception("Modulo by zero is not allowed")
        return x % y

    def calculate(self, operation: Operation, a: float, b: float) -> float:
        """Dispatch calculation based on operation type.

        Args:
            operation: The operation to perform
            a: First operand
            b: Second operand

        Returns:
            The result of the calculation

        Raises:
            ValueError: If operation is not supported
        """
        dispatch = {
            Operation.ADD: self.add,
            Operation.SUBTRACT: self.subtract,
            Operation.MULTIPLY: self.multiply,
            Operation.DIVIDE: self.divide,
            Operation.SQUARE: lambda x, _: self.square(x),
            Operation.SQRT: lambda x, _: self.sqrt(x),
            Operation.POWER: self.power,
            Operation.MODULO: self.modulo,
        }
        if operation not in dispatch:
            raise ValueError(f"Unsupported operation: {operation}")
        return dispatch[operation](a, b)
