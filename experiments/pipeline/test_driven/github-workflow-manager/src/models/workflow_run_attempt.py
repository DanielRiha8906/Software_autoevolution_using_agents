from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion


@dataclass
class WorkflowRunAttempt:
    id: str
    run_id: str
    attempt_number: int
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    duration_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be >= 1")

        if self.created_at.tzinfo is None or self.created_at.utcoffset().total_seconds() != 7200:
            raise ValueError("created_at must be timezone-aware CEST (UTC+2)")

        if self.duration_seconds is not None and self.duration_seconds < 0.0:
            raise ValueError("duration_seconds must be non-negative")

        # Convert string values to enums if necessary
        if isinstance(self.status, str):
            self.status = WorkflowStatus(self.status)
        if isinstance(self.conclusion, str):
            self.conclusion = WorkflowConclusion(self.conclusion)

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
            status=WorkflowStatus(data["status"]),
            conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds"),
        )
