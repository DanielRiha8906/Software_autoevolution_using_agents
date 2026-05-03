from typing import List

from ..models.workflow_run_attempt import WorkflowRunAttempt


class AttemptService:
    """Service for managing WorkflowRunAttempt instances with in-memory storage."""

    def __init__(self) -> None:
        """Initialize with empty in-memory storage."""
        self._attempts: List[WorkflowRunAttempt] = []

    def create(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """
        Store an attempt and return it.

        Args:
            attempt: The WorkflowRunAttempt to store.

        Returns:
            The stored attempt.

        Raises:
            ValueError: If an attempt with the same (run_id, attempt_number) already exists.
        """
        # Check for uniqueness constraint
        for existing in self._attempts:
            if (
                existing.run_id == attempt.run_id
                and existing.attempt_number == attempt.attempt_number
            ):
                raise ValueError(
                    f"Attempt with run_id={attempt.run_id} and "
                    f"attempt_number={attempt.attempt_number} already exists"
                )

        self._attempts.append(attempt)
        return attempt

    def get_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        """
        Retrieve all attempts for a given run_id, sorted by attempt_number ascending.

        Args:
            run_id: The workflow run ID to filter by.

        Returns:
            A list of WorkflowRunAttempt objects sorted by attempt_number in ascending order.
            Returns an empty list if no attempts are found for the run_id.
        """
        matching = [a for a in self._attempts if a.run_id == run_id]
        return sorted(matching, key=lambda a: a.attempt_number)

    def get_all_attempts(self) -> List[WorkflowRunAttempt]:
        """
        Retrieve all stored attempts.

        Returns:
            A list of all WorkflowRunAttempt objects in insertion order.
            Returns an empty list if no attempts are stored.
        """
        return list(self._attempts)
