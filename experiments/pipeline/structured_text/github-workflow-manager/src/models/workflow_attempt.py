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
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float = 0.0
    logs_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "attempt_number": self.attempt_number,
            "status": self.status.value,
            "conclusion": self.conclusion.value if self.conclusion else None,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "logs_url": self.logs_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRunAttempt":
        duration = data.get("duration_seconds", 0.0)
        if duration < 0:
            raise ValueError(f"duration_seconds must be non-negative, got {duration}")
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            attempt_number=data["attempt_number"],
            status=WorkflowStatus(data["status"]),
            conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            duration_seconds=duration,
            logs_url=data.get("logs_url"),
        )

    def is_terminal(self) -> bool:
        """Returns True if the attempt has reached a terminal state (completed)."""
        return self.status == WorkflowStatus.COMPLETED

    def is_running(self) -> bool:
        """Returns True if the attempt is actively running or queued."""
        return self.status != WorkflowStatus.COMPLETED

    def is_successful(self) -> bool:
        """Returns True if the attempt completed successfully."""
        return (self.status == WorkflowStatus.COMPLETED and
                self.conclusion == WorkflowConclusion.SUCCESS)

    def is_failed(self) -> bool:
        """Returns True if the attempt completed with failure."""
        return (self.status == WorkflowStatus.COMPLETED and
                self.conclusion in (WorkflowConclusion.FAILURE,
                                    WorkflowConclusion.TIMED_OUT,
                                    WorkflowConclusion.ACTION_REQUIRED))

    def is_cancelled(self) -> bool:
        """Returns True if the attempt was cancelled."""
        return (self.status == WorkflowStatus.COMPLETED and
                self.conclusion == WorkflowConclusion.CANCELLED)
