from dataclasses import dataclass, asdict, field
from datetime import datetime


_SYMBOLS = {
    "add": "+",
    "subtract": "-",
    "multiply": "×",
    "divide": "÷",
    "square": "²",
    "sqrt": "√",
    "power": "^",
    "modulo": "%",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "log10": "log10",
    "ln": "ln",
    "exp": "exp",
}


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
        data = {**data, "execution_time_ms": data.get("execution_time_ms", 0.0)}
        return cls(**data)

    def __str__(self) -> str:
        symbol = _SYMBOLS.get(self.operation, self.operation)
        a = int(self.operand_a) if self.operand_a == int(self.operand_a) else self.operand_a
        b = int(self.operand_b) if self.operand_b == int(self.operand_b) else self.operand_b
        r = int(self.result) if self.result == int(self.result) else self.result
        return f"{a} {symbol} {b} = {r}"
