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

    def square(self, a: float, b: float) -> float:
        return a ** 2

    def sqrt(self, a: float, b: float) -> float:
        if a < 0:
            raise ValueError("Cannot take square root of negative number")
        return a ** 0.5

    def power(self, a: float, b: float) -> float:
        return a ** b

    def modulo(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Modulo by zero is not allowed")
        return a % b

    def sin(self, a: float, b: float) -> float:
        return math.sin(a)

    def cos(self, a: float, b: float) -> float:
        return math.cos(a)

    def tan(self, a: float, b: float) -> float:
        return math.tan(a)

    def log(self, a: float, b: float) -> float:
        if a <= 0:
            raise ValueError("Logarithm of non-positive number is not allowed")
        return math.log10(a)

    def ln(self, a: float, b: float) -> float:
        if a <= 0:
            raise ValueError("Natural logarithm of non-positive number is not allowed")
        return math.log(a)

    def exp(self, a: float, b: float) -> float:
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
