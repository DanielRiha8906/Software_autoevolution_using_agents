from typing import List

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..storage.attempt_json_storage import AttemptJsonStorage


class AttemptService:
    def __init__(self, storage: AttemptJsonStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()

    def _persist(self) -> None:
        self._storage.save(self._attempts)

    def create_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """
        Create a new attempt.

        Args:
            attempt: The WorkflowRunAttempt to create.

        Returns:
            The created attempt.

        Raises:
            ValueError: If an attempt with the same (run_id, attempt_number) already exists.
        """
        if any(
            a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
            for a in self._attempts
        ):
            raise ValueError(
                f"Attempt with run_id={attempt.run_id} and attempt_number={attempt.attempt_number} already exists."
            )
        self._attempts.append(attempt)
        self._persist()
        return attempt

    def get_attempts_for_run(self, run_id: int) -> List[WorkflowRunAttempt]:
        """
        Get all attempts for a given run_id, sorted by attempt_number.

        Args:
            run_id: The run ID to filter by.

        Returns:
            A list of attempts sorted by attempt_number in ascending order.
        """
        attempts = [a for a in self._attempts if a.run_id == run_id]
        return sorted(attempts, key=lambda a: a.attempt_number)
