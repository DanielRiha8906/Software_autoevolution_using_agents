from enum import Enum


class Operation(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    SQUARE = "square"
    SQRT = "sqrt"
    POWER = "power"
    MODULO = "modulo"
    SIN = "sin"
    COS = "cos"
    TAN = "tan"
    LOG = "log"
    LN = "ln"
    EXP = "exp"

    @classmethod
    def from_string(cls, value: str) -> "Operation":
        normalized = value.lower()
        for member in cls:
            if member.value == normalized:
                return member
        valid = [m.value for m in cls]
        raise ValueError(f"Unknown operation: '{value}'. Valid options: {valid}")

    def display_name(self) -> str:
        return self.value.capitalize()

    def arity(self) -> int:
        """Return the number of operands required: 1 for unary, 2 for binary."""
        if self in (Operation.SIN, Operation.COS, Operation.TAN, Operation.LOG, Operation.LN, Operation.EXP, Operation.SQUARE, Operation.SQRT):
            return 1
        return 2

    def is_unary(self) -> bool:
        """Return True if this is a unary operation (requires one operand)."""
        return self.arity() == 1
