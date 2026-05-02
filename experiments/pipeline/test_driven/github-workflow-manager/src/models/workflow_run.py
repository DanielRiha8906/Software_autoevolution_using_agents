from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .workflow_status import WorkflowStatus
from .workflow_conclusion import WorkflowConclusion


@dataclass
class WorkflowRun:
    id: str
    workflow_name: str
    branch: str
    status: WorkflowStatus
    conclusion: Optional[WorkflowConclusion]
    created_at: datetime
    duration_seconds: float = 0.0
    updated_at: Optional[datetime] = None
    run_number: Optional[int] = None
    commit_sha: Optional[str] = None

    def __post_init__(self) -> None:
        if self.duration_seconds < 0.0:
            raise ValueError("duration_seconds must be non-negative")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "branch": self.branch,
            "status": self.status.value,
            "conclusion": self.conclusion.value if self.conclusion else None,
            "created_at": self.created_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "run_number": self.run_number,
            "commit_sha": self.commit_sha,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRun":
        return cls(
            id=data["id"],
            workflow_name=data["workflow_name"],
            branch=data["branch"],
            status=WorkflowStatus(data["status"]),
            conclusion=WorkflowConclusion(data["conclusion"]) if data.get("conclusion") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            duration_seconds=data.get("duration_seconds", 0.0),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            run_number=data.get("run_number"),
            commit_sha=data.get("commit_sha"),
        )

    def is_running(self) -> bool:
        """Return True if workflow is currently running."""
        return self.status == WorkflowStatus.IN_PROGRESS

    def is_terminal(self) -> bool:
        """Return True if workflow has reached a terminal state."""
        return self.status == WorkflowStatus.COMPLETED

    def is_successful(self) -> bool:
        """Return True if workflow completed successfully."""
        return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.SUCCESS

    def is_failed(self) -> bool:
        """Return True if workflow completed with failure."""
        return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.FAILURE

    def is_cancelled(self) -> bool:
        """Return True if workflow was cancelled."""
        return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.CANCELLED
