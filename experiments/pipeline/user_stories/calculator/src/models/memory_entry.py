from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4


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
class MemoryEntry:
    operation: str
    operand_a: float
    operand_b: float
    result: float | None
    error: str | None
    error_type: str | None
    execution_time_ms: float = field(default=0.0)
    timestamp: str = field(default="")
    uuid: str = field(default="")

    def __post_init__(self) -> None:
        if not self.uuid:
            self.uuid = str(uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        data = data.copy()
        data.setdefault("uuid", str(uuid4()))
        data.setdefault("error", None)
        data.setdefault("error_type", None)
        data.setdefault("execution_time_ms", 0.0)
        return cls(**data)

    def __str__(self) -> str:
        symbol = _SYMBOLS.get(self.operation, self.operation)
        a = int(self.operand_a) if self.operand_a == int(self.operand_a) else self.operand_a
        b = int(self.operand_b) if self.operand_b == int(self.operand_b) else self.operand_b

        if self.result is None:
            return f"{a} {symbol} {b} = ERROR: {self.error}"

        r = int(self.result) if self.result == int(self.result) else self.result
        return f"{a} {symbol} {b} = {r}"
