from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class MemoryEntry:
    """Domain class representing one stored calculation attempt."""
    operation_name: str
    operand_a: float
    operand_b: float
    result: Optional[float] = field(default=None)
    success: bool = field(default=True)
    error_message: Optional[str] = field(default=None)
    execution_timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)

    def __post_init__(self) -> None:
        if not self.execution_timestamp:
            self.execution_timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert the MemoryEntry to a dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Create a MemoryEntry from a dictionary (e.g., deserialized from JSON)."""
        return cls(**data)
