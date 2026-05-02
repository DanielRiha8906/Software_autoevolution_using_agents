from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4
from typing import Optional


@dataclass
class MemoryEntry:
    """
    Comprehensive audit entry for a calculator operation attempt.

    Tracks both successful and failed operations with unique identifiers,
    execution status, and detailed error information.

    Attributes:
        entry_id (str): Unique identifier (UUID4). Can be set explicitly for testing.
        operation (str): Operation name (e.g., "add", "sqrt"). Must match Operation enum values.
        operand_a (float): First operand.
        operand_b (float): Second operand.
        result (Optional[float]): Calculation result (None if operation failed).
        success (bool): True if operation completed without error, False otherwise.
        error_message (Optional[str]): Error message if operation failed, None if successful.
        timestamp (str): ISO 8601 timestamp of operation attempt.
        execution_time_ms (float): Time taken to execute operation, in milliseconds. Default 0.0.
    """
    operation: str
    operand_a: float
    operand_b: float
    result: Optional[float]
    success: bool
    error_message: Optional[str]
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default="")
    execution_time_ms: float = 0.0

    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serialize MemoryEntry to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Deserialize MemoryEntry from dictionary."""
        return cls(**data)
