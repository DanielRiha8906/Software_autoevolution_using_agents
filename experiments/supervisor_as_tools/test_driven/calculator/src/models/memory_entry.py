from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4


@dataclass
class MemoryEntry:
    operation: str
    operands: list
    result: float | None
    success: bool
    execution_time_ms: float
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
