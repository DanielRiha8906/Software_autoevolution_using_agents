from typing import List

from ..models.workflow_run_attempt import WorkflowRunAttempt
from .workflow_run_service import WorkflowRunService


class AttemptService:
    """Service for managing workflow run attempts."""

    def __init__(self, run_service: WorkflowRunService):
        """Initialize AttemptService with a WorkflowRunService reference.

        Args:
            run_service: The WorkflowRunService instance to use for run operations
        """
        self._run_service = run_service

    def create_attempt(self, run_id: str, attempt_data: dict) -> WorkflowRunAttempt:
        """Create and add an attempt to a workflow run.

        Args:
            run_id: The ID of the workflow run
            attempt_data: Dictionary containing attempt data with keys:
                         id, run_id, attempt_number, status, conclusion (optional),
                         created_at, duration_seconds (optional)

        Returns:
            The created WorkflowRunAttempt object

        Raises:
            ValueError: If run not found or duplicate attempt_number
        """
        run = self._run_service.get_run_detail(run_id)
        if run is None:
            raise ValueError(f"Run with id '{run_id}' not found.")

        attempt = WorkflowRunAttempt.from_dict(attempt_data)

        # Check for duplicate attempt number
        if any(a.attempt_number == attempt.attempt_number for a in run.attempts):
            raise ValueError(
                f"Attempt number {attempt.attempt_number} already exists in run '{run_id}'."
            )

        return self._run_service.add_workflow_run_attempt(run_id, attempt)

    def get_attempts_by_run(
        self, run_id: str, sort_by_number: bool = False
    ) -> List[WorkflowRunAttempt]:
        """Retrieve all attempts for a given run.

        Args:
            run_id: The ID of the workflow run
            sort_by_number: If True, sort attempts by attempt_number ascending

        Returns:
            List of WorkflowRunAttempt objects

        Raises:
            ValueError: If run not found
        """
        run = self._run_service.get_run_detail(run_id)
        if run is None:
            raise ValueError(f"Run with id '{run_id}' not found.")

        attempts = list(run.attempts)
        if sort_by_number:
            attempts.sort(key=lambda a: a.attempt_number)
        return attempts

    def validate_duplicate_attempt_number(
        self, attempts: List[WorkflowRunAttempt]
    ) -> bool:
        """Validate that all attempt numbers are unique.

        Args:
            attempts: List of WorkflowRunAttempt objects to validate

        Returns:
            True if all attempt numbers are unique

        Raises:
            ValueError: If duplicate attempt numbers are found
        """
        attempt_numbers = [attempt.attempt_number for attempt in attempts]
        if len(attempt_numbers) != len(set(attempt_numbers)):
            raise ValueError("Attempt numbers must be unique within a workflow run")
        return True
