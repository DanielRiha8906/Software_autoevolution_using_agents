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
}


@dataclass
class CalculationResult:
    operation: str
    operand_a: float
    operand_b: float | None
    result: float
    timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CalculationResult":
        if "execution_time_ms" not in data:
            data["execution_time_ms"] = 0.0
        return cls(**data)

    def __str__(self) -> str:
        a = int(self.operand_a) if self.operand_a == int(self.operand_a) else self.operand_a
        r = int(self.result) if self.result == int(self.result) else self.result

        # Unary operations (operand_b is None)
        if self.operand_b is None:
            if self.operation == "sqrt":
                return f"√{a} = {r}"
            elif self.operation == "square":
                return f"{a}² = {r}"
            else:
                symbol = _SYMBOLS.get(self.operation, self.operation)
                return f"{symbol}({a}) = {r}"

        # Binary operations
        b = int(self.operand_b) if self.operand_b == int(self.operand_b) else self.operand_b
        symbol = _SYMBOLS.get(self.operation, self.operation)
        return f"{a} {symbol} {b} = {r}"
