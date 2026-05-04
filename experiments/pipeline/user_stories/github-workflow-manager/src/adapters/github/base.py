"""Base protocol for GitHub workflow fetchers."""

from typing import Protocol, List, Optional
from datetime import datetime

from ...models.workflow_run import WorkflowRun


class WorkflowFetcher(Protocol):
    """Abstract interface for fetching workflow runs from any source."""

    def fetch_runs(
        self,
        owner: str,
        repo: str,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        created_after: Optional[datetime] = None,
    ) -> List[WorkflowRun]:
        """Fetch workflow runs from source."""
        ...
