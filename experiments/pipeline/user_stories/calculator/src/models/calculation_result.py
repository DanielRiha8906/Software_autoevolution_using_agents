from dataclasses import dataclass, asdict, field
from datetime import datetime


_SYMBOLS = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷", "power": "^", "modulo": "%"}
_UNARY_OPS = {"square", "sqrt"}


@dataclass
class CalculationResult:
    operation: str
    operand_a: float
    operand_b: float
    result: float
    timestamp: str = field(default="")
    execution_time_ms: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CalculationResult":
        return cls(**data)

    def __str__(self) -> str:
        a = int(self.operand_a) if self.operand_a == int(self.operand_a) else self.operand_a
        r = int(self.result) if self.result == int(self.result) else self.result

        if self.operation in _UNARY_OPS:
            if self.operation == "square":
                return f"{a}² = {r}"
            elif self.operation == "sqrt":
                return f"√{a} = {r}"
            else:
                return f"{self.operation}({a}) = {r}"

        symbol = _SYMBOLS.get(self.operation, self.operation)
        b = int(self.operand_b) if self.operand_b == int(self.operand_b) else self.operand_b
        return f"{a} {symbol} {b} = {r}"
