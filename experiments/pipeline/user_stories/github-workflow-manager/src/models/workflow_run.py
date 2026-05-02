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

    def is_terminal(self) -> bool:
        """Check if the workflow run has reached a terminal state.

        A workflow run is terminal when it has completed execution and will not
        transition to any other state. This occurs when the status is COMPLETED.

        Returns:
            bool: True if the run has reached a terminal state, False otherwise.
        """
        return self.status == WorkflowStatus.COMPLETED

    def is_running(self) -> bool:
        """Check if the workflow run is actively executing or queued to run.

        A workflow run is considered running or in-progress when it is in one of
        the following states: IN_PROGRESS, QUEUED, REQUESTED, PENDING, or WAITING.

        Returns:
            bool: True if the run is actively executing or queued, False otherwise.
        """
        return self.status in (
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.QUEUED,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
            WorkflowStatus.WAITING,
        )

    def is_successful(self) -> bool:
        """Check if the workflow run completed with a successful conclusion.

        Returns True only if the run's conclusion is SUCCESS. Returns False if
        the conclusion is None or any other value.

        Returns:
            bool: True if the run concluded with success, False otherwise.
        """
        return self.conclusion == WorkflowConclusion.SUCCESS

    def is_failed(self) -> bool:
        """Check if the workflow run completed with a failure conclusion.

        Returns True only if the run's conclusion is FAILURE. Returns False if
        the conclusion is None or any other value.

        Returns:
            bool: True if the run concluded with failure, False otherwise.
        """
        return self.conclusion == WorkflowConclusion.FAILURE

    def is_cancelled(self) -> bool:
        """Check if the workflow run was cancelled.

        Returns True only if the run's conclusion is CANCELLED. Returns False if
        the conclusion is None or any other value. This is a convenience method
        for checking cancellation status independent of success or failure.

        Returns:
            bool: True if the run was cancelled, False otherwise.
        """
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
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            run_number=data.get("run_number"),
            commit_sha=data.get("commit_sha"),
            duration_seconds=data.get("duration_seconds", 0.0),
        )
