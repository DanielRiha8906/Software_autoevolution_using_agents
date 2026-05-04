"""Abstract repository interfaces for data persistence.

This module defines the contracts that storage implementations must fulfill,
allowing services to depend on abstractions rather than concrete storage classes.
"""

from abc import ABC, abstractmethod
from typing import List

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt


class WorkflowRunRepository(ABC):
    """Abstract interface for workflow run persistence."""

    @abstractmethod
    def save(self, runs: List[WorkflowRun]) -> None:
        """Persist workflow runs to storage.

        Args:
            runs: List of WorkflowRun objects to save.
        """
        pass

    @abstractmethod
    def load(self) -> List[WorkflowRun]:
        """Load all workflow runs from storage.

        Returns:
            List of WorkflowRun objects.
        """
        pass


class AttemptRepository(ABC):
    """Abstract interface for workflow attempt persistence."""

    @abstractmethod
    def save(self, attempts: List[WorkflowRunAttempt]) -> None:
        """Persist workflow attempts to storage.

        Args:
            attempts: List of WorkflowRunAttempt objects to save.
        """
        pass

    @abstractmethod
    def load(self) -> List[WorkflowRunAttempt]:
        """Load all workflow attempts from storage.

        Returns:
            List of WorkflowRunAttempt objects.
        """
        pass
