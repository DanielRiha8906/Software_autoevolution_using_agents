from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4


@dataclass
class MemoryEntry:
    operation_name: str
    operand_a: float
    operand_b: float
    result: float | None
    success: bool
    entry_id: str = field(default="")
    error_message: str | None = field(default=None)
    timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)

    def __post_init__(self) -> None:
        if not self.entry_id:
            self.entry_id = uuid4().hex
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**data)
