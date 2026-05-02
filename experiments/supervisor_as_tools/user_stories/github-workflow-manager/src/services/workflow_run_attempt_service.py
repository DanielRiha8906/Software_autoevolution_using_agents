from typing import List, Optional

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..models.attempt_run_status import RunAttemptStatus
from ..models.attempt_run_conclusion import RunAttemptConclusion
from ..storage.workflow_run_attempt_json_storage import WorkflowRunAttemptJsonStorage


class WorkflowRunAttemptService:
    """Service layer for WorkflowRunAttempt CRUD and filtering."""

    def __init__(self, storage: WorkflowRunAttemptJsonStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()

    def _persist(self) -> None:
        """Delegate persistence to storage."""
        self._storage.save(self._attempts)

    def add_workflow_run_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """
        Add a new attempt.

        Raises ValueError if (run_id, attempt_number) composite key already exists.
        """
        if any(
            a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
            for a in self._attempts
        ):
            raise ValueError(
                f"Attempt with run_id={attempt.run_id}, attempt_number={attempt.attempt_number} already exists."
            )
        self._attempts.append(attempt)
        self._persist()
        return attempt

    def list_attempts(self) -> List[WorkflowRunAttempt]:
        """Return all attempts."""
        return list(self._attempts)

    def get_attempt(self, run_id: int, attempt_number: int) -> Optional[WorkflowRunAttempt]:
        """
        Retrieve a single attempt by composite key (run_id, attempt_number).

        Returns None if not found.
        """
        return next(
            (
                a for a in self._attempts
                if a.run_id == run_id and a.attempt_number == attempt_number
            ),
            None,
        )

    def list_attempts_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        """Retrieve all attempts for a given run_id, ordered by attempt_number."""
        return sorted(
            [a for a in self._attempts if a.run_id == run_id],
            key=lambda a: a.attempt_number,
        )

    def filter_by_status(self, status: RunAttemptStatus) -> List[WorkflowRunAttempt]:
        """Return all attempts matching the status."""
        return [a for a in self._attempts if a.status == status]

    def filter_by_conclusion(self, conclusion: RunAttemptConclusion) -> List[WorkflowRunAttempt]:
        """Return all attempts matching the conclusion."""
        return [a for a in self._attempts if a.conclusion == conclusion]
