from typing import List, Optional

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..storage.protocols import StorageBackend


class AttemptService:
    def __init__(self, storage: StorageBackend):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()

    def _persist(self) -> None:
        self._storage.save(self._attempts)

    def create_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """Create and store a new workflow run attempt.

        Args:
            attempt: The WorkflowRunAttempt to create.

        Returns:
            The created attempt.

        Raises:
            ValueError: If an attempt with the same (run_id, attempt_number) pair already exists.
        """
        # Check for duplicate (run_id, attempt_number) pair
        if any(
            a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
            for a in self._attempts
        ):
            raise ValueError(
                f"Attempt with run_id '{attempt.run_id}' and attempt_number "
                f"'{attempt.attempt_number}' already exists."
            )
        self._attempts.append(attempt)
        self._persist()
        return attempt

    def get_attempts_for_run(self, run_id: int) -> List[WorkflowRunAttempt]:
        """Retrieve all attempts for a given run_id, sorted by attempt_number.

        Args:
            run_id: The ID of the workflow run.

        Returns:
            A list of attempts for the run, sorted by attempt_number in ascending order.
        """
        attempts = [a for a in self._attempts if a.run_id == run_id]
        return sorted(attempts, key=lambda a: a.attempt_number)

    def list_all_attempts(self) -> List[WorkflowRunAttempt]:
        """Retrieve all attempts across all runs.

        Returns:
            A list of all attempts.
        """
        return list(self._attempts)


__all__ = ["AttemptService"]
