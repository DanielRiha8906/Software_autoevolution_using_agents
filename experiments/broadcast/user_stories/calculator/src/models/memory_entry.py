import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MemoryEntry:
    """
    Represents a single calculation attempt in the calculator's history.

    Captures both successful and failed calculations with complete metadata.
    Each entry has a unique identifier and execution details.
    """

    operation: str
    operand_a: float
    operand_b: float
    result: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "operation": self.operation,
            "operand_a": self.operand_a,
            "operand_b": self.operand_b,
            "result": self.result,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
            "entry_id": self.entry_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Deserialize from a JSON-compatible dictionary."""
        return cls(**data)
