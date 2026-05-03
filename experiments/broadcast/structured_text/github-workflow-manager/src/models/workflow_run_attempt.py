from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion


@dataclass
class WorkflowRunAttempt:
    """Represents a single attempt of a workflow run.

    A workflow run can have multiple attempts if it is retried.
    Each attempt tracks its own status, conclusion, and execution time.
    """
    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: Optional[str]
    created_at: datetime
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        """Validate that duration_seconds is non-negative."""
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")

    def is_terminal(self) -> bool:
        """Return True if the attempt is in a terminal state."""
        return self.status == "completed"

    def is_running(self) -> bool:
        """Return True if the attempt is currently executing."""
        return self.status == "in_progress"

    def is_successful(self) -> bool:
        """Return True if the attempt concluded successfully."""
        return self.conclusion == "success"

    def is_failed(self) -> bool:
        """Return True if the attempt concluded with failure."""
        return self.conclusion == "failure"

    def is_cancelled(self) -> bool:
        """Return True if the attempt was cancelled."""
        return self.conclusion == "cancelled"

    def to_dict(self) -> dict:
        """Serialize the WorkflowRunAttempt to a dictionary."""
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
        """Deserialize a WorkflowRunAttempt from a dictionary."""
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds", 0.0),
        )
