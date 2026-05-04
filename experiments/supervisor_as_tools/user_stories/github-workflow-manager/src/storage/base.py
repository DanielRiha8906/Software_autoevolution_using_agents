from typing import List, Protocol

from ..models.workflow_run import WorkflowRun


class StorageAdapter(Protocol):
    """Protocol defining the interface for workflow run storage adapters."""

    def load(self) -> List[WorkflowRun]:
        """Load all workflow runs from storage.

        Returns:
            List of WorkflowRun objects
        """
        ...

    def save(self, runs: List[WorkflowRun]) -> None:
        """Save workflow runs to storage.

        Args:
            runs: List of WorkflowRun objects to save
        """
        ...

    def export_to_file(self, runs: List[WorkflowRun], output_path: str) -> None:
        """Export workflow runs to a file.

        Args:
            runs: List of WorkflowRun objects to export
            output_path: Path where the JSON file will be written
        """
        ...

    def import_from_file(self, input_path: str) -> List[WorkflowRun]:
        """Import workflow runs from a file.

        Args:
            input_path: Path to the JSON file to import

        Returns:
            List of deserialized WorkflowRun objects
        """
        ...
