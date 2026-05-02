from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class MemoryEntry:
    """
    Represents one stored calculation attempt in memory.

    Supports both successful and failed calculations with detailed
    metadata for querying and reporting.
    """
    operation: str
    operand_a: float
    operand_b: float
    result: Optional[float] = field(default=None)
    success: bool = field(default=True)
    error_message: Optional[str] = field(default=None)
    timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**data)
