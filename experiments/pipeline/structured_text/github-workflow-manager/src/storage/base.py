"""
Abstract base interfaces (Protocols) for storage layer.

These protocols define the contract that storage implementations must follow.
This allows services to depend on abstract interfaces rather than concrete storage types.
"""

from typing import Protocol, List

from ..models.workflow_run import WorkflowRun
from ..models.workflow_attempt import WorkflowRunAttempt


class WorkflowRunRepository(Protocol):
    """Abstract interface for WorkflowRun persistence."""

    def save(self, runs: List[WorkflowRun]) -> None:
        """
        Save workflow runs to storage.

        Args:
            runs: List of WorkflowRun instances to save

        Raises:
            IOError: If save operation fails
        """
        ...

    def load(self) -> List[WorkflowRun]:
        """
        Load all workflow runs from storage.

        Returns:
            List of WorkflowRun instances (empty list if no data)

        Raises:
            IOError: If load operation fails
        """
        ...


class WorkflowAttemptRepository(Protocol):
    """Abstract interface for WorkflowRunAttempt persistence."""

    def save(self, attempts: List[WorkflowRunAttempt]) -> None:
        """
        Save workflow attempts to storage.

        Args:
            attempts: List of WorkflowRunAttempt instances to save

        Raises:
            IOError: If save operation fails
        """
        ...

    def load(self) -> List[WorkflowRunAttempt]:
        """
        Load all workflow attempts from storage.

        Returns:
            List of WorkflowRunAttempt instances (empty list if no data)

        Raises:
            IOError: If load operation fails
        """
        ...
