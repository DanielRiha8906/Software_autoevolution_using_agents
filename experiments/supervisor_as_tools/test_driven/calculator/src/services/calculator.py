import math

from ..models.operation import Operation


class Calculator:
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
        return x ** 2

    def sqrt(self, x: float) -> float:
        if x < 0:
            raise Exception("Square root of negative number is not allowed")
        return math.sqrt(x)

    def power(self, base: float, exponent: float) -> float:
        return base ** exponent

    def modulo(self, x: float, y: float) -> float:
        if y == 0:
            raise Exception("Modulo by zero is not allowed")
        return x % y

    def calculate(self, operation: Operation, a: float, b: float) -> float:
        dispatch = {
            Operation.ADD: self.add,
            Operation.SUBTRACT: self.subtract,
            Operation.MULTIPLY: self.multiply,
            Operation.DIVIDE: self.divide,
        }
        if operation not in dispatch:
            raise ValueError(f"Unsupported operation: {operation}")
        return dispatch[operation](a, b)
