from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .attempt_run_status import RunAttemptStatus
from .attempt_run_conclusion import RunAttemptConclusion


@dataclass
class WorkflowRunAttempt:
    id: int
    run_id: int
    attempt_number: int
    status: RunAttemptStatus
    conclusion: Optional[RunAttemptConclusion]
    created_at: datetime
    duration_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate composite key and field constraints."""
        if self.attempt_number < 1:
            raise ValueError(f"attempt_number must be positive integer >= 1, got {self.attempt_number}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "attempt_number": self.attempt_number,
            "status": self.status.value,
            "conclusion": self.conclusion.value if self.conclusion else None,
            "created_at": self.created_at.isoformat(),
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRunAttempt":
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=RunAttemptStatus(data["status"]),
            conclusion=RunAttemptConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds"),
        )
