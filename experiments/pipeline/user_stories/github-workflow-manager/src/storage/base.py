"""Base protocols for storage layer abstraction."""

from typing import Protocol, List

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt


class WorkflowRunStorage(Protocol):
    """Abstract storage contract for workflow runs."""

    def save(self, runs: List[WorkflowRun]) -> None:
        """Persist workflow runs."""
        ...

    def load(self) -> List[WorkflowRun]:
        """Load all workflow runs."""
        ...


class WorkflowRunAttemptStorage(Protocol):
    """Abstract storage contract for workflow run attempts."""

    def save_attempts(self, attempts: List[WorkflowRunAttempt]) -> None:
        """Persist workflow run attempts."""
        ...

    def load_attempts(self) -> List[WorkflowRunAttempt]:
        """Load all workflow run attempts."""
        ...
