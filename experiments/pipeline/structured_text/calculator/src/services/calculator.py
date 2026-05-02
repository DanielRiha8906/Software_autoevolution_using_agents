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
            raise ValueError("Cannot compute square root of negative number")
        return a ** 0.5

    def power(self, a: float, b: float) -> float:
        return a ** b

    def modulo(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Modulo by zero is not allowed")
        return a % b

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
        }
        if operation not in dispatch:
            raise ValueError(f"Unsupported operation: {operation}")
        return dispatch[operation](a, b)
