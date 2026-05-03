from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4


@dataclass
class MemoryEntry:
    operation: str
    operand_a: float
    operand_b: float
    success: bool
    timestamp: str = field(default="")
    execution_time_ms: float = 0.0
    result: float | None = None
    error_message: str | None = None
    id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.id:
            self.id = str(uuid4())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        data = {
            **data,
            "result": data.get("result"),
            "error_message": data.get("error_message"),
            "execution_time_ms": data.get("execution_time_ms", 0.0),
        }
        return cls(**data)
