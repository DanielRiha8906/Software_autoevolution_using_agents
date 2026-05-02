from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4
from typing import Optional


@dataclass
class MemoryEntry:
    """
    Domain class representing a single calculation attempt in memory.

    Supports both successful and failed calculations with full error tracking.
    Provides JSON serialization/deserialization with backward compatibility to CalculationResult.
    """
    operation: str
    operand_a: float
    operand_b: float
    result: Optional[float]  # None for failed operations
    status: str  # "success" or "error"
    error_message: Optional[str]  # None for successful, error text for failures
    timestamp: str  # ISO 8601 format, auto-generated if empty
    execution_time_ms: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))  # Unique identifier

    def __post_init__(self) -> None:
        """Validate fields and auto-generate timestamp if needed."""
        # Validate status
        if self.status not in ("success", "error"):
            raise ValueError(f"Invalid status '{self.status}'. Must be 'success' or 'error'.")

        # Validate result/status consistency
        if self.status == "success" and self.result is None:
            raise ValueError("Success status requires a non-None result value.")
        if self.status == "error" and self.result is not None:
            raise ValueError("Error status requires result to be None.")

        # Auto-generate timestamp if empty
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """
        Convert to JSON-serializable dictionary.

        Returns:
            dict: All fields as dict. None values for result/error_message are preserved.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """
        Deserialize from dictionary, with backward compatibility for CalculationResult format.

        Handles:
        - New format: includes 'status' and 'error_message' fields
        - Legacy format: assumes success status, no error_message
        - Missing timestamp: auto-generates if empty string or missing

        Args:
            data: Dictionary with calculation fields

        Returns:
            MemoryEntry instance

        Raises:
            KeyError: If required fields (operation, operand_a, operand_b, result) are missing
            ValueError: If data fails validation
        """
        # Create copy to avoid mutating input
        entry_data = dict(data)

        # Handle legacy format (no status field)
        if "status" not in entry_data:
            entry_data["status"] = "success"

        # Handle legacy format (no error_message field)
        if "error_message" not in entry_data:
            entry_data["error_message"] = None

        # Handle missing or empty timestamp (legacy data may have "" or be missing)
        if not entry_data.get("timestamp"):
            entry_data["timestamp"] = ""  # Let __post_init__ auto-generate

        # Provide default id if missing (legacy data)
        if "id" not in entry_data:
            entry_data["id"] = str(uuid4())

        # Provide default execution_time_ms if missing
        if "execution_time_ms" not in entry_data:
            entry_data["execution_time_ms"] = 0.0

        return cls(**entry_data)

    @staticmethod
    def success(
        operation: str,
        operand_a: float,
        operand_b: float,
        result: float,
        execution_time_ms: float = 0.0,
        timestamp: str = "",
    ) -> "MemoryEntry":
        """
        Factory for successful calculations.

        Args:
            operation: Operation name (e.g., "add")
            operand_a: First operand
            operand_b: Second operand
            result: Calculation result
            execution_time_ms: Time taken in milliseconds (default 0.0)
            timestamp: ISO 8601 timestamp (auto-generated if empty)

        Returns:
            MemoryEntry with status="success"
        """
        return MemoryEntry(
            operation=operation,
            operand_a=operand_a,
            operand_b=operand_b,
            result=result,
            status="success",
            error_message=None,
            timestamp=timestamp,
            execution_time_ms=execution_time_ms,
        )

    @staticmethod
    def error(
        operation: str,
        operand_a: float,
        operand_b: float,
        error_message: str,
        execution_time_ms: float = 0.0,
        timestamp: str = "",
    ) -> "MemoryEntry":
        """
        Factory for failed calculations.

        Args:
            operation: Operation name that failed (e.g., "divide")
            operand_a: First operand (before failure)
            operand_b: Second operand (before failure)
            error_message: Error description (e.g., "division by zero")
            execution_time_ms: Time taken before error in milliseconds (default 0.0)
            timestamp: ISO 8601 timestamp (auto-generated if empty)

        Returns:
            MemoryEntry with status="error", result=None
        """
        return MemoryEntry(
            operation=operation,
            operand_a=operand_a,
            operand_b=operand_b,
            result=None,
            status="error",
            error_message=error_message,
            timestamp=timestamp,
            execution_time_ms=execution_time_ms,
        )
