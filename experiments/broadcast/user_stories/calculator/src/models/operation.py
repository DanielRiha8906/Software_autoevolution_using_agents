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
