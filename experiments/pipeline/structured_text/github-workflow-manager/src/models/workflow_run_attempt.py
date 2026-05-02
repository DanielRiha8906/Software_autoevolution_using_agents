from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkflowRunAttempt:
    """Represents a single attempt of a workflow run.

    A workflow run can have multiple attempts (retries), each with independent
    status, conclusion, and timing information.
    """

    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: Optional[str]
    created_at: datetime
    duration_seconds: Optional[float] = None

    def __post_init__(self):
        """Validate attempt_number is >= 1."""
        if self.attempt_number < 1:
            raise ValueError(f"attempt_number must be >= 1, got {self.attempt_number}")

    def to_dict(self) -> dict:
        """Serialize to a dictionary with ISO datetime formatting."""
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
        """Deserialize from a dictionary with datetime parsing."""
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds"),
        )
