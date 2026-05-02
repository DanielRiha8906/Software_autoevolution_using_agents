import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class MemoryEntry:
    operation: str
    operands: list[float]
    result: Optional[float]
    success: bool
    execution_time_ms: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default="")

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**data)
