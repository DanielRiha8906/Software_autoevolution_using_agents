from typing import List, Optional

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..storage.attempt_json_storage import AttemptJsonStorage


class AttemptService:
    def __init__(self, storage: AttemptJsonStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()

    def _persist(self) -> None:
        self._storage.save(self._attempts)

    def add_workflow_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """Add a new workflow attempt.

        Validates that attempt number is unique per run.
        """
        if any(
            a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
            for a in self._attempts
        ):
            raise ValueError(
                f"Attempt {attempt.attempt_number} for run {attempt.run_id} already exists."
            )
        self._attempts.append(attempt)
        self._persist()
        return attempt

    def get_attempts_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        """Retrieve all attempts for a given run_id."""
        return [a for a in self._attempts if a.run_id == run_id]

    def list_attempts(self) -> List[WorkflowRunAttempt]:
        """Return all attempts."""
        return list(self._attempts)
