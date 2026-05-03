from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class MemoryEntry:
    operation: str
    operands: list
    result: Optional[float]
    success: bool
    execution_time_ms: float
    id: str = field(default="")
    timestamp: str = field(default="")

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        # Make a copy to avoid mutating input dict
        data_copy = dict(data)
        instance = cls(**data_copy)
        return instance
