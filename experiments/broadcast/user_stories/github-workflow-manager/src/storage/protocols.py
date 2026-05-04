"""Protocol definitions for storage layer."""

from typing import Protocol, List
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt


class StorageBackend(Protocol):
    """Protocol for storage backends.

    Defines the contract that any storage implementation must satisfy.
    Allows duck typing without requiring inheritance.
    """

    def save(self, data: List) -> None:
        """Save data to persistent storage.

        Args:
            data: A list of domain model objects to persist.
        """
        ...

    def load(self) -> List:
        """Load data from persistent storage.

        Returns:
            A list of domain model objects, or an empty list if none exist.
        """
        ...


class GitHubAPIClient(Protocol):
    """Protocol for GitHub API client implementations.

    Defines the contract for fetching workflow runs from GitHub.
    Allows duck typing without requiring inheritance.
    """

    def fetch_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow: str | None = None,
        token: str | None = None,
        validate: bool = True,
    ) -> List[WorkflowRun]:
        """Fetch workflow runs from GitHub API.

        Args:
            owner: Repository owner (username or organization).
            repo: Repository name.
            workflow: Optional workflow ID or filename to filter by.
            token: Optional GitHub PAT. If not provided, will be resolved.
            validate: If True, validate token before fetching.

        Returns:
            List of WorkflowRun instances fetched from GitHub.

        Raises:
            ValueError: If token cannot be resolved or is invalid.
            RuntimeError: If no API client is available.
        """
        ...

    def fetch_incremental(
        self,
        owner: str,
        repo: str,
        latest_run_timestamp: object | None = None,
        workflow: str | None = None,
        token: str | None = None,
    ) -> List[WorkflowRun]:
        """Fetch only workflow runs newer than the latest stored run.

        Args:
            owner: Repository owner.
            repo: Repository name.
            latest_run_timestamp: Timestamp of the latest stored run. If provided,
                                 only fetch runs created after this timestamp.
            workflow: Optional workflow ID or filename to filter by.
            token: Optional GitHub PAT.

        Returns:
            List of new WorkflowRun instances.
        """
        ...


__all__ = ["StorageBackend", "GitHubAPIClient"]
