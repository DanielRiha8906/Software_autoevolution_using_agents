from typing import List

from ..models.workflow_run_attempt import WorkflowRunAttempt


class AttemptService:
    """Service for managing WorkflowRunAttempt objects in memory.

    Does not handle persistence - that responsibility remains outside this service.
    """

    def __init__(self) -> None:
        """Initialize the AttemptService with an empty in-memory store."""
        self._attempts: List[WorkflowRunAttempt] = []

    def create(self, attempt: WorkflowRunAttempt) -> None:
        """Store an attempt.

        Args:
            attempt: The WorkflowRunAttempt to store.

        Raises:
            ValueError: If an attempt with the same (run_id, attempt_number) already exists.
        """
        # Check for duplicate (run_id, attempt_number) combination
        if any(
            a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
            for a in self._attempts
        ):
            raise ValueError(
                f"Attempt with run_id={attempt.run_id} and "
                f"attempt_number={attempt.attempt_number} already exists"
            )
        self._attempts.append(attempt)

    def get_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        """Get all attempts for a given run_id, sorted by attempt_number ascending.

        Args:
            run_id: The run ID to filter by.

        Returns:
            A list of WorkflowRunAttempt objects sorted by attempt_number in ascending order.
        """
        matching = [a for a in self._attempts if a.run_id == run_id]
        return sorted(matching, key=lambda a: a.attempt_number)
