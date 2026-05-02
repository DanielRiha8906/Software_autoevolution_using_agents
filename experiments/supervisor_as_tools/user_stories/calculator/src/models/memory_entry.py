from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4


@dataclass
class MemoryEntry:
    operation: str
    operand_a: float
    operand_b: float
    result: float | None
    success: bool
    error_message: str | None
    execution_time_ms: float
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default="")

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**data)
