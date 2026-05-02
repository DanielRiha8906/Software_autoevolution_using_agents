from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion

if TYPE_CHECKING:
    from .workflow_run_attempt import WorkflowRunAttempt


@dataclass
class WorkflowRun:
    id: str
    workflow_name: str
    branch: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    updated_at: Optional[datetime]
    run_number: Optional[int]
    commit_sha: Optional[str]
    duration_seconds: float = 0.0
    attempts: List["WorkflowRunAttempt"] = field(default_factory=list)

    def __post_init__(self):
        if self.duration_seconds < 0:
            raise ValueError(f"duration_seconds must be non-negative, got {self.duration_seconds}")

    def is_running(self) -> bool:
        """Check if the workflow is actively executing."""
        return self.status == WorkflowStatus.IN_PROGRESS

    def is_terminal(self) -> bool:
        """Check if the workflow has reached a final state."""
        return self.status == WorkflowStatus.COMPLETED

    def is_successful(self) -> bool:
        """Check if the workflow completed successfully."""
        return (
            self.status == WorkflowStatus.COMPLETED
            and self.conclusion == WorkflowConclusion.SUCCESS
        )

    def is_failed(self) -> bool:
        """Check if the workflow completed with failure."""
        return (
            self.status == WorkflowStatus.COMPLETED
            and self.conclusion == WorkflowConclusion.FAILURE
        )

    def is_cancelled(self) -> bool:
        """Check if the workflow was explicitly cancelled."""
        return self.conclusion == WorkflowConclusion.CANCELLED

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "branch": self.branch,
            "status": self.status.value,
            "conclusion": self.conclusion.value if self.conclusion else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "run_number": self.run_number,
            "commit_sha": self.commit_sha,
            "duration_seconds": self.duration_seconds,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRun":
        from .workflow_run_attempt import WorkflowRunAttempt

        attempts_data = data.get("attempts", [])
        attempts = [WorkflowRunAttempt.from_dict(attempt_dict) for attempt_dict in attempts_data]

        return cls(
            id=data["id"],
            workflow_name=data["workflow_name"],
            branch=data["branch"],
            status=WorkflowStatus(data["status"]),
            conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            run_number=data.get("run_number"),
            commit_sha=data.get("commit_sha"),
            duration_seconds=data.get("duration_seconds", 0.0),
            attempts=attempts,
        )
