from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from ..models.workflow_run_attempt import WorkflowRunAttempt
from .workflow_run_service import WorkflowRunService
from ..storage.workflow_json_storage import WorkflowJsonStorage


class AttemptService:
    """
    Manages workflow run attempts.

    Each workflow run can have multiple attempts (retries).
    AttemptService handles creation and retrieval of attempts
    while maintaining data consistency with the storage layer.
    """

    def __init__(self, storage: WorkflowJsonStorage, workflow_service: WorkflowRunService):
        """
        Initialize the AttemptService.

        Args:
            storage: JSON storage for persistence
            workflow_service: WorkflowRunService instance for run lookups
        """
        self._storage = storage
        self._workflow_service = workflow_service

    def create_attempt(
        self,
        run_id: str,
        status: str,
        conclusion: Optional[str] = None
    ) -> WorkflowRunAttempt:
        """
        Create a new workflow run attempt.

        Automatically assigns the next attempt_number for the run.
        Prevents duplicate attempt numbers within a single run.

        Args:
            run_id: The workflow run ID
            status: Status of the attempt (e.g., "queued", "in_progress", "completed")
            conclusion: Final conclusion if completed (e.g., "success", "failure")

        Returns:
            The created WorkflowRunAttempt

        Raises:
            ValueError: If run does not exist or duplicate attempt_number
        """
        # Verify run exists
        run = self._workflow_service.get_run_detail(run_id)
        if run is None:
            raise ValueError(f"Run with id '{run_id}' not found")

        # Get next attempt number
        attempt_number = self._get_next_attempt_number(run_id)

        # Check for duplicate
        if any(a.attempt_number == attempt_number for a in run.attempts):
            raise ValueError(
                f"Attempt with number {attempt_number} already exists for run '{run_id}'"
            )

        # Create new attempt
        attempt = WorkflowRunAttempt(
            id=uuid4().int,
            run_id=run_id,
            attempt_number=attempt_number,
            status=status,
            conclusion=conclusion,
            created_at=datetime.now(timezone.utc)
        )

        # Append to run's attempts
        run.attempts.append(attempt)

        # Persist via workflow service
        self._workflow_service._persist()

        return attempt

    def retrieve_attempts_by_run_id(self, run_id: str) -> List[WorkflowRunAttempt]:
        """
        Retrieve all attempts for a workflow run, sorted by attempt_number.

        Args:
            run_id: The workflow run ID

        Returns:
            List of WorkflowRunAttempt objects sorted by attempt_number ascending.
            Returns empty list if run does not exist.
        """
        run = self._workflow_service.get_run_detail(run_id)
        if run is None:
            return []
        return sorted(run.attempts, key=lambda a: a.attempt_number)

    def _get_next_attempt_number(self, run_id: str) -> int:
        """
        Get the next attempt number for a run.

        Args:
            run_id: The workflow run ID

        Returns:
            Next attempt number (1 for first attempt, then incremented)
        """
        run = self._workflow_service.get_run_detail(run_id)
        if run is None or not run.attempts:
            return 1
        return max(a.attempt_number for a in run.attempts) + 1
