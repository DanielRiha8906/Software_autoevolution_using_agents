from typing import List

from ..models.workflow_run_attempt import WorkflowRunAttempt


class AttemptService:
    def __init__(self) -> None:
        self._attempts: List[WorkflowRunAttempt] = []

    def create(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """
        Create and store a new workflow run attempt.

        Enforces uniqueness of (run_id, attempt_number) composite key.

        Args:
            attempt: The WorkflowRunAttempt to create.

        Returns:
            The created attempt.

        Raises:
            ValueError: If an attempt with the same run_id and attempt_number already exists.
        """
        if any(
            a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
            for a in self._attempts
        ):
            raise ValueError(
                f"Attempt with run_id={attempt.run_id} and attempt_number={attempt.attempt_number} already exists."
            )
        self._attempts.append(attempt)
        return attempt

    def get_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        """
        Retrieve all attempts for a given run_id, sorted by attempt_number.

        Args:
            run_id: The run ID to filter by.

        Returns:
            A new list of attempts for the run_id, sorted by attempt_number ascending.
        """
        filtered = [a for a in self._attempts if a.run_id == run_id]
        return sorted(filtered, key=lambda a: a.attempt_number)
