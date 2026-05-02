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

    def square(self, a: float) -> float:
        return a * a

    def sqrt(self, a: float) -> float:
        if a < 0:
            raise ValueError("Square root of negative number")
        return math.sqrt(a)

    def power(self, a: float, b: float) -> float:
        return a ** b

    def modulo(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Modulo by zero")
        return a % b

    def calculate(self, operation: Operation, *args: float) -> float:
        # Define expected arg counts for each operation
        unary_ops = {Operation.SQUARE, Operation.SQRT}
        binary_ops = {Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE, Operation.POWER, Operation.MODULO}

        if operation in unary_ops:
            expected = 1
            if len(args) != expected:
                raise ValueError(f"Operation {operation.display_name()} requires {expected} operand(s), got {len(args)}")
        elif operation in binary_ops:
            expected = 2
            if len(args) != expected:
                raise ValueError(f"Operation {operation.display_name()} requires {expected} operand(s), got {len(args)}")
        else:
            raise ValueError(f"Unsupported operation: {operation}")

        # Dispatch to correct method
        dispatch = {
            Operation.ADD: lambda: self.add(args[0], args[1]),
            Operation.SUBTRACT: lambda: self.subtract(args[0], args[1]),
            Operation.MULTIPLY: lambda: self.multiply(args[0], args[1]),
            Operation.DIVIDE: lambda: self.divide(args[0], args[1]),
            Operation.SQUARE: lambda: self.square(args[0]),
            Operation.SQRT: lambda: self.sqrt(args[0]),
            Operation.POWER: lambda: self.power(args[0], args[1]),
            Operation.MODULO: lambda: self.modulo(args[0], args[1]),
        }
        return dispatch[operation]()
