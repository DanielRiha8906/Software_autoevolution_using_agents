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
    updated_at: Optional[datetime]
    run_number: Optional[int]
    commit_sha: Optional[str]
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")

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
        }

    def is_terminal(self) -> bool:
        """
        Returns True if the workflow run has reached a terminal state.
        Terminal = COMPLETED status AND conclusion is set (not None).
        Mutually exclusive with: is_running()
        """
        return self.status == WorkflowStatus.COMPLETED and self.conclusion is not None

    def is_successful(self) -> bool:
        """
        Returns True if the workflow completed successfully.
        Success = COMPLETED status AND conclusion is SUCCESS.
        Mutually exclusive with: is_failed(), is_cancelled()
        """
        return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.SUCCESS

    def is_failed(self) -> bool:
        """
        Returns True if the workflow completed with failure.
        Failure = COMPLETED status AND conclusion is FAILURE.
        Mutually exclusive with: is_successful(), is_cancelled()
        """
        return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.FAILURE

    def is_running(self) -> bool:
        """
        Returns True if the workflow is actively executing.
        Running = status is IN_PROGRESS, REQUESTED, or PENDING.
        Mutually exclusive with: is_terminal()
        """
        return self.status in (
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING
        )

    def is_cancelled(self) -> bool:
        """
        Returns True if the workflow was cancelled.
        Cancelled = COMPLETED status AND conclusion is CANCELLED.
        Mutually exclusive with: is_successful(), is_failed()
        """
        return self.status == WorkflowStatus.COMPLETED and self.conclusion == WorkflowConclusion.CANCELLED

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowRun":
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
        )
