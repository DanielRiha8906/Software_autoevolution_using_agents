from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4
from typing import Optional


@dataclass
class MemoryEntry:
    """Domain class representing a single calculation entry in system memory.

    Required fields capture the calculation state; auto-generated fields track
    identity and timing. The class supports round-trip serialization via
    to_dict() and from_dict().
    """
    operation: str
    operands: list
    result: Optional[float]
    success: bool
    execution_time_ms: float
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default="")

    def __post_init__(self) -> None:
        """Auto-generate timestamp if not provided.

        Called automatically after __init__. If timestamp is empty string
        (the default), generates ISO 8601 timestamp. If timestamp was
        provided (e.g., during deserialization), preserves it.
        """
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert MemoryEntry to dictionary.

        Returns:
            dict: Dictionary with all 7 fields. UUID and timestamp are strings,
                  which are JSON serializable.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Create MemoryEntry from dictionary.

        Args:
            data: Dictionary with keys matching all 7 fields. Preserves
                  existing id and timestamp; does not regenerate them.

        Returns:
            MemoryEntry: New instance with all fields populated from data.
        """
        return cls(**data)
