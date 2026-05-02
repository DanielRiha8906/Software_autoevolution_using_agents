from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4
from typing import Optional


@dataclass
class MemoryEntry:
    """Represents a stored calculation attempt (successful or failed)."""

    operation: str
    operand_a: float
    operand_b: float
    result: Optional[float]
    success: bool
    error_message: Optional[str]
    timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)
    entry_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        """Auto-generate timestamp if missing and validate state consistency."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

        # Validation: error_message should only be set when success=False
        if self.success and self.error_message is not None:
            raise ValueError(
                "error_message must be None when success=True"
            )

        # Validation: result should only be set when success=True
        if not self.success and self.result is not None:
            raise ValueError(
                "result must be None when success=False"
            )

        # Validation: when success=True, result must not be None
        if self.success and self.result is None:
            raise ValueError(
                "result must not be None when success=True"
            )

        # Validation: when success=False, error_message must not be None
        if not self.success and self.error_message is None:
            raise ValueError(
                "error_message must not be None when success=False"
            )

    def to_dict(self) -> dict:
        """Serialize MemoryEntry to JSON-compatible dictionary."""
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Deserialize MemoryEntry from dictionary with backward compatibility.

        Backward compatibility: old CalculationResult format lacks success,
        error_message, and entry_id fields. Default them appropriately.
        """
        # Create a copy to avoid modifying the original
        entry_data = dict(data)

        # Backward compatibility: assume success=True if not present
        if "success" not in entry_data:
            entry_data["success"] = True

        # Backward compatibility: assume error_message=None if not present
        if "error_message" not in entry_data:
            entry_data["error_message"] = None

        # Backward compatibility: assume entry_id is UUID if not present
        if "entry_id" not in entry_data:
            entry_data["entry_id"] = str(uuid4())

        return cls(**entry_data)

    def __str__(self) -> str:
        """Minimal string representation for logging/debugging."""
        if self.success:
            return (
                f"MemoryEntry(id={self.entry_id}, "
                f"operation={self.operation}, "
                f"result={self.result}, "
                f"timestamp={self.timestamp})"
            )
        else:
            return (
                f"MemoryEntry(id={self.entry_id}, "
                f"operation={self.operation}, "
                f"error={self.error_message}, "
                f"timestamp={self.timestamp})"
            )
