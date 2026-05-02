import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class MemoryEntry:
    operation: str
    operands: list
    result: float | None
    success: bool
    execution_time_ms: float
    id: str | None = field(default=None)
    timestamp: str = field(default="")

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**data)
