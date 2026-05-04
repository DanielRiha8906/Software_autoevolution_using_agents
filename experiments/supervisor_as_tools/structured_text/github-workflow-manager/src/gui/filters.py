from typing import Optional, Dict, Any

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion


class FilterState:
    """Encapsulates filter state for workflow runs.

    Data members:
        status: Optional WorkflowStatus filter.
        conclusion: Optional WorkflowConclusion filter.
    """

    def __init__(
        self,
        status: Optional[WorkflowStatus] = None,
        conclusion: Optional[WorkflowConclusion] = None,
    ) -> None:
        """Initialize filter state.

        Args:
            status: Filter by WorkflowStatus enum value or None.
            conclusion: Filter by WorkflowConclusion enum value or None.
        """
        self.status = status
        self.conclusion = conclusion

    def is_active(self) -> bool:
        """Return True if any filter is active.

        Returns:
            True if status or conclusion filter is set, False otherwise.
        """
        return self.status is not None or self.conclusion is not None

    def to_filter_params(self) -> Dict[str, Any]:
        """Convert filter state to service filter parameters.

        Returns:
            Dictionary with status and conclusion keys (value is None if not filtered).
        """
        return {
            "status": self.status,
            "conclusion": self.conclusion,
        }

    def reset(self) -> None:
        """Reset all filters to inactive state."""
        self.status = None
        self.conclusion = None
