import math

from ..models.operation import Operation
from .calculator import Calculator


class ScientificCalculator(Calculator):
    def sin(self, x: float) -> float:
        return math.sin(x)

    def cos(self, x: float) -> float:
        return math.cos(x)

    def tan(self, x: float) -> float:
        return math.tan(x)

    def log(self, x: float) -> float:
        if x <= 0:
            raise ValueError("Cannot take logarithm of non-positive number")
        return math.log10(x)

    def ln(self, x: float) -> float:
        if x <= 0:
            raise ValueError("Cannot take logarithm of non-positive number")
        return math.log(x)

    def exp(self, x: float) -> float:
        return math.exp(x)

    def calculate(self, operation: Operation, a: float, b: float) -> float:
        dispatch = {
            Operation.SIN: lambda: self.sin(a),
            Operation.COS: lambda: self.cos(a),
            Operation.TAN: lambda: self.tan(a),
            Operation.LOG: lambda: self.log(a),
            Operation.LN: lambda: self.ln(a),
            Operation.EXP: lambda: self.exp(a),
            Operation.ADD: lambda: self.add(a, b),
            Operation.SUBTRACT: lambda: self.subtract(a, b),
            Operation.MULTIPLY: lambda: self.multiply(a, b),
            Operation.DIVIDE: lambda: self.divide(a, b),
            Operation.SQUARE: lambda: self.square(a),
            Operation.SQRT: lambda: self.sqrt(a),
            Operation.POWER: lambda: self.power(a, b),
            Operation.MODULO: lambda: self.modulo(a, b),
        }
        if operation not in dispatch:
            raise ValueError(f"Unsupported operation: {operation}")
        return dispatch[operation]()
