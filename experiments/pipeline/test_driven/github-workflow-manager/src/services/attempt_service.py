from typing import List

from ..models.workflow_run_attempt import WorkflowRunAttempt


class AttemptService:
    """In-memory service for managing WorkflowRunAttempt objects.

    Enforces uniqueness on (run_id, attempt_number) composite keys.
    No persistence or file I/O.
    """

    def __init__(self) -> None:
        """Initialize the service with an empty attempts list."""
        self._attempts: List[WorkflowRunAttempt] = []

    def create(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """Add a new attempt to the service.

        Args:
            attempt: The WorkflowRunAttempt to add

        Returns:
            The added attempt

        Raises:
            ValueError: If an attempt with the same (run_id, attempt_number)
                       composite key already exists
        """
        if any(
            a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
            for a in self._attempts
        ):
            raise ValueError(
                f"Attempt with run_id '{attempt.run_id}' and attempt_number "
                f"{attempt.attempt_number} already exists."
            )
        self._attempts.append(attempt)
        return attempt

    def get_by_run_id(self, run_id: str) -> List[WorkflowRunAttempt]:
        """Retrieve all attempts for a given run_id, sorted by attempt_number.

        Args:
            run_id: The run identifier

        Returns:
            List of attempts for the run, sorted by attempt_number ascending.
            Returns empty list if run_id not found.
        """
        matching_attempts = [a for a in self._attempts if a.run_id == run_id]
        return sorted(matching_attempts, key=lambda a: a.attempt_number)
