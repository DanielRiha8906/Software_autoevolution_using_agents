from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional


@dataclass
class WorkflowRunAttempt:
    """
    Represents a single attempt of a workflow run.

    Each workflow run can have multiple attempts (e.g., retries).
    The (run_id, attempt_number) tuple must be unique.
    """
    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: Optional[str]
    created_at: datetime
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        """Validate attempt_number and duration_seconds."""
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be a positive integer >= 1")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds cannot be negative")

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "conclusion": self.conclusion,
            "created_at": self.created_at.isoformat(),
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRunAttempt":
        """Deserialize from a JSON-compatible dictionary."""
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds", 0.0),
        )
