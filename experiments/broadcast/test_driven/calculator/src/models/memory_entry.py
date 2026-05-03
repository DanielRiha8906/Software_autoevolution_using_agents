import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional


@dataclass
class MemoryEntry:
    operation: str
    operands: list[Any]
    result: Optional[Any]
    success: bool
    execution_time_ms: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default="")

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**data)
