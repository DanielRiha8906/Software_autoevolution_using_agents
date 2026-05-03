from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkflowRunAttempt:
    id: int
    run_id: int
    attempt_number: int
    status: str
    conclusion: Optional[str]
    created_at: datetime
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError(f"id must be greater than 0, got {self.id}")
        if self.run_id <= 0:
            raise ValueError(f"run_id must be greater than 0, got {self.run_id}")
        if self.attempt_number < 1:
            raise ValueError(f"attempt_number must be >= 1, got {self.attempt_number}")
        if self.duration_seconds < 0.0:
            raise ValueError(
                f"duration_seconds must be non-negative, got {self.duration_seconds}"
            )

    def to_dict(self) -> dict:
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
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=float(data.get("duration_seconds", 0.0)),
        )

    def is_successful(self) -> bool:
        """Return True if the attempt completed successfully."""
        return self.status == "completed" and self.conclusion == "success"

    def is_failed(self) -> bool:
        """Return True if the attempt completed with a failure."""
        return self.status == "completed" and self.conclusion == "failure"

    def is_running(self) -> bool:
        """Return True if the attempt is still running (not in a terminal state)."""
        return self.status != "completed"
