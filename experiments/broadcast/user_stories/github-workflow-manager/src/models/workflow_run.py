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

    def is_running(self) -> bool:
        """Check if the workflow run is currently running.

        A run is considered running if its status is in the active state.
        Terminal and running states are mutually exclusive.

        Returns:
            True if the run is queued, in progress, waiting, requested, or pending.
        """
        return self.status in (
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.WAITING,
            WorkflowStatus.REQUESTED,
            WorkflowStatus.PENDING,
        )

    def is_terminal(self) -> bool:
        """Check if the workflow run has completed.

        A run is considered terminal if its status is completed.
        Terminal and running states are mutually exclusive.

        Returns:
            True if the run status is completed.
        """
        return self.status == WorkflowStatus.COMPLETED

    def is_successful(self) -> bool:
        """Check if the workflow run completed successfully.

        A run is considered successful if it is terminal and its conclusion is success.
        Successful and failed states are mutually exclusive.

        Returns:
            True if the run completed with a success conclusion.
        """
        return self.conclusion == WorkflowConclusion.SUCCESS

    def is_failed(self) -> bool:
        """Check if the workflow run completed with a failure.

        A run is considered failed if it is terminal and its conclusion is failure.
        Successful and failed states are mutually exclusive.

        Returns:
            True if the run completed with a failure conclusion.
        """
        return self.conclusion == WorkflowConclusion.FAILURE

    def is_cancelled(self) -> bool:
        """Check if the workflow run was cancelled.

        A run is considered cancelled if its conclusion is cancelled.

        Returns:
            True if the run was cancelled.
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
        )
