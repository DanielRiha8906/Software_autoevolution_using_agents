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
        return a * a

    def sqrt(self, a: float, b: float) -> float:
        if a < 0:
            raise ValueError("Cannot take the square root of a negative number")
        return math.sqrt(a)

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
        # Check for poles near pi/2 and multiples
        normalized = a / math.pi
        # tan is undefined at odd multiples of pi/2
        remainder = abs(normalized - round(normalized))
        if remainder < 1e-10:
            raise ValueError("Tangent is undefined at poles (odd multiples of π/2)")
        return math.tan(a)

    def log10(self, a: float, b: float) -> float:
        if a <= 0:
            raise ValueError("Logarithm undefined for non-positive values")
        return math.log10(a)

    def ln(self, a: float, b: float) -> float:
        if a <= 0:
            raise ValueError("Logarithm undefined for non-positive values")
        return math.log(a)

    def exp(self, a: float, b: float) -> float:
        try:
            return math.exp(a)
        except OverflowError:
            raise ValueError("Exponential overflow: result too large to represent")

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
            Operation.LOG10: self.log10,
            Operation.LN: self.ln,
            Operation.EXP: self.exp,
        }
        if operation not in dispatch:
            raise ValueError(f"Unsupported operation: {operation}")
        return dispatch[operation](a, b)
