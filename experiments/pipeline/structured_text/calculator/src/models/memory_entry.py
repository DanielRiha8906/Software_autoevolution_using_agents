from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class MemoryEntry:
    """
    Represents a single stored calculation attempt, capturing both successful
    and failed calculations with full metadata including execution timestamp,
    execution time, and error information.
    """
    operation: str
    operand_a: float
    operand_b: float
    result: Optional[float]
    success: bool
    error_message: Optional[str]
    execution_timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)
    memory_entry_id: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        """Auto-generate execution_timestamp if empty and memory_entry_id if None."""
        if not self.execution_timestamp:
            self.execution_timestamp = datetime.now().isoformat()
        if self.memory_entry_id is None:
            self.memory_entry_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        """Convert to JSON-compatible dictionary."""
        return {
            "operation": self.operation,
            "operand_a": self.operand_a,
            "operand_b": self.operand_b,
            "result": self.result,
            "success": self.success,
            "error_message": self.error_message,
            "execution_timestamp": self.execution_timestamp,
            "execution_time_ms": self.execution_time_ms,
            "memory_entry_id": self.memory_entry_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """
        Create MemoryEntry from dict with backward compatibility support.

        Handles old JSON format by:
        - Converting old "timestamp" field to "execution_timestamp"
        - Defaulting missing execution_time_ms to 0.0
        - Inferring success=True and error_message=None for old records
        - Leaving memory_entry_id as None if not present (will be auto-generated in __post_init__)
        """
        # Create a normalized copy of the input data
        normalized = dict(data)

        # Handle backward compatibility: old "timestamp" field
        if "timestamp" in normalized and "execution_timestamp" not in normalized:
            normalized["execution_timestamp"] = normalized.pop("timestamp")

        # Ensure all required fields exist with defaults
        if "execution_timestamp" not in normalized:
            normalized["execution_timestamp"] = ""

        if "execution_time_ms" not in normalized:
            normalized["execution_time_ms"] = 0.0

        if "success" not in normalized:
            # Infer success=True for old records
            normalized["success"] = True

        if "error_message" not in normalized:
            normalized["error_message"] = None

        if "memory_entry_id" not in normalized:
            normalized["memory_entry_id"] = None

        # Only pass fields that the dataclass expects
        allowed_fields = {
            "operation",
            "operand_a",
            "operand_b",
            "result",
            "success",
            "error_message",
            "execution_timestamp",
            "execution_time_ms",
            "memory_entry_id",
        }
        filtered_data = {k: v for k, v in normalized.items() if k in allowed_fields}

        return cls(**filtered_data)

    def __str__(self) -> str:
        """String representation for display."""
        if self.success:
            return f"{self.operation}: {self.operand_a} and {self.operand_b} → {self.result}"
        else:
            return f"{self.operation}: {self.operand_a} and {self.operand_b} → Error: {self.error_message}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"MemoryEntry(operation={self.operation!r}, operand_a={self.operand_a}, "
            f"operand_b={self.operand_b}, result={self.result}, success={self.success}, "
            f"error_message={self.error_message!r}, execution_timestamp={self.execution_timestamp!r}, "
            f"execution_time_ms={self.execution_time_ms}, memory_entry_id={self.memory_entry_id!r})"
        )
