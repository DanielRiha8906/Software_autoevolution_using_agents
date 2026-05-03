from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any


_entry_counter = 0


def _get_next_id() -> int:
    """Generate the next sequential entry ID."""
    global _entry_counter
    _entry_counter += 1
    return _entry_counter


def _reset_id_counter() -> None:
    """Reset the entry counter. Use only for testing."""
    global _entry_counter
    _entry_counter = 0


@dataclass
class MemoryEntry(ABC):
    """Base class for a calculator operation history entry."""

    entry_id: int = field(default_factory=_get_next_id)
    operation: str = ""
    operands: list[float] = field(default_factory=list)
    timestamp: str = field(default="")
    execution_time_ms: float = field(default=0.0)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @abstractmethod
    def to_dict(self) -> dict:
        """Serialize entry to JSON-compatible dictionary."""
        raise NotImplementedError

    @abstractmethod
    def is_error(self) -> bool:
        """Return True if this entry represents an error."""
        raise NotImplementedError

    @staticmethod
    def from_dict(data: dict) -> "MemoryEntry":
        """Deserialize from JSON-compatible dictionary."""
        if data.get("type") == "result":
            return ResultEntry.from_dict(data)
        elif data.get("type") == "error":
            return ErrorEntry.from_dict(data)
        else:
            raise ValueError(f"Unknown entry type: {data.get('type')}")


@dataclass
class ResultEntry(MemoryEntry):
    """Entry representing a successful calculation."""

    result: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dictionary."""
        data = {
            "type": "result",
            "entry_id": self.entry_id,
            "operation": self.operation,
            "operands": self.operands,
            "result": self.result,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
        }
        return data

    def is_error(self) -> bool:
        return False

    @classmethod
    def from_dict(cls, data: dict) -> "ResultEntry":
        """Deserialize from JSON-compatible dictionary."""
        return cls(
            entry_id=data.get("entry_id", 0),
            operation=data.get("operation", ""),
            operands=data.get("operands", []),
            result=data.get("result", 0.0),
            timestamp=data.get("timestamp", ""),
            execution_time_ms=data.get("execution_time_ms", 0.0),
        )


@dataclass
class ErrorEntry(MemoryEntry):
    """Entry representing a failed calculation."""

    error_message: str = ""

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dictionary."""
        data = {
            "type": "error",
            "entry_id": self.entry_id,
            "operation": self.operation,
            "operands": self.operands,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
        }
        return data

    def is_error(self) -> bool:
        return True

    @classmethod
    def from_dict(cls, data: dict) -> "ErrorEntry":
        """Deserialize from JSON-compatible dictionary."""
        return cls(
            entry_id=data.get("entry_id", 0),
            operation=data.get("operation", ""),
            operands=data.get("operands", []),
            error_message=data.get("error_message", ""),
            timestamp=data.get("timestamp", ""),
            execution_time_ms=data.get("execution_time_ms", 0.0),
        )
