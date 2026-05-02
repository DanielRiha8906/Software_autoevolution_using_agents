from typing import Dict, List

from ..models.workflow_run_attempt import WorkflowRunAttempt


class AttemptService:
    """Service for managing WorkflowRunAttempt objects."""

    def __init__(self) -> None:
        """Initialize the AttemptService with an in-memory store."""
        self._attempts: Dict[int, List[WorkflowRunAttempt]] = {}

    def create(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """
        Store a WorkflowRunAttempt object.

        Args:
            attempt: The WorkflowRunAttempt to store.

        Returns:
            The stored WorkflowRunAttempt.

        Raises:
            Exception: If a duplicate (run_id, attempt_number) pair already exists.
        """
        run_id = attempt.run_id
        attempt_number = attempt.attempt_number

        # Check if this run_id already has attempts
        if run_id in self._attempts:
            # Check if this attempt_number already exists for this run_id
            existing_numbers = [a.attempt_number for a in self._attempts[run_id]]
            if attempt_number in existing_numbers:
                raise Exception(
                    f"Duplicate attempt: run_id={run_id}, attempt_number={attempt_number}"
                )
            self._attempts[run_id].append(attempt)
        else:
            # First attempt for this run_id
            self._attempts[run_id] = [attempt]

        return attempt

    def get_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        """
        Retrieve all attempts for a specific run_id, sorted by attempt_number.

        Args:
            run_id: The run_id to filter by.

        Returns:
            A list of WorkflowRunAttempt objects sorted by attempt_number in ascending order.
        """
        if run_id not in self._attempts:
            return []

        # Sort by attempt_number in ascending order
        return sorted(self._attempts[run_id], key=lambda a: a.attempt_number)
