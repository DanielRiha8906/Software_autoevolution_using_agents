from typing import List, Optional
from builtins import sorted as _sorted

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..storage.base import WorkflowRunAttemptStorage


class WorkflowRunAttemptService:
    def __init__(self, storage: WorkflowRunAttemptStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load_attempts()

    def _persist(self) -> None:
        self._storage.save_attempts(self._attempts)

    def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
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

    def replace_attempt(self, attempt: WorkflowRunAttempt) -> None:
        """Replace existing attempt or add if not exists. For import operations."""
        self._attempts = [a for a in self._attempts if a.id != attempt.id]
        self._attempts.append(attempt)
        self._persist()

    def delete_attempt(self, attempt_id: int) -> bool:
        """Delete attempt by id. Returns True if deleted, False if not found."""
        original_count = len(self._attempts)
        self._attempts = [a for a in self._attempts if a.id != attempt_id]
        if len(self._attempts) < original_count:
            self._persist()
            return True
        return False

    def list_attempts(self, sorted: bool = True) -> List[WorkflowRunAttempt]:
        attempts = list(self._attempts)
        if sorted:
            return _sorted(attempts, key=lambda a: a.attempt_number)
        return attempts

    def get_attempt(self, attempt_id: int) -> Optional[WorkflowRunAttempt]:
        return next((a for a in self._attempts if a.id == attempt_id), None)

    def get_attempts_for_run(self, run_id: int, sorted: bool = True) -> List[WorkflowRunAttempt]:
        attempts = [a for a in self._attempts if a.run_id == run_id]
        if sorted:
            return _sorted(attempts, key=lambda a: a.attempt_number)
        return attempts
