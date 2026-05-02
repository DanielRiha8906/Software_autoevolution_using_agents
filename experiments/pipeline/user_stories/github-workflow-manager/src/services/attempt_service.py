from typing import List, Optional

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..storage.attempt_json_storage import AttemptJsonStorage


class AttemptService:
    """Service layer for managing workflow run attempts.

    Provides CRUD operations and filtering capabilities for WorkflowRunAttempt
    instances, with automatic persistence to storage.
    """

    def __init__(self, storage: AttemptJsonStorage):
        """Initialize service with a storage backend.

        Args:
            storage: AttemptJsonStorage instance for persistence.
        """
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()

    def _persist(self) -> None:
        """Persist current attempts to storage."""
        self._storage.save(self._attempts)

    def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        """Add a new attempt to the collection.

        Enforces uniqueness constraint on (run_id, attempt_number) pair.

        Args:
            attempt: WorkflowRunAttempt instance to add.

        Returns:
            The added attempt.

        Raises:
            ValueError: If an attempt with the same (run_id, attempt_number)
                pair already exists.
        """
        if any(
            a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
            for a in self._attempts
        ):
            raise ValueError(
                f"Attempt {attempt.attempt_number} for run {attempt.run_id} already exists"
            )
        self._attempts.append(attempt)
        self._persist()
        return attempt

    def list_attempts(self) -> List[WorkflowRunAttempt]:
        """List all attempts.

        Returns:
            Copy of the attempts list.
        """
        return list(self._attempts)

    def get_attempt_by_id(self, attempt_id: int) -> Optional[WorkflowRunAttempt]:
        """Retrieve a single attempt by its ID.

        Args:
            attempt_id: The attempt's ID.

        Returns:
            The WorkflowRunAttempt if found, None otherwise.
        """
        return next((a for a in self._attempts if a.id == attempt_id), None)

    def filter_by_run(self, run_id: int) -> List[WorkflowRunAttempt]:
        """Filter attempts by parent run ID.

        Args:
            run_id: The parent WorkflowRun ID.

        Returns:
            List of attempts belonging to the specified run.
        """
        return [a for a in self._attempts if a.run_id == run_id]

    def filter_by_status(self, status: str) -> List[WorkflowRunAttempt]:
        """Filter attempts by status.

        Args:
            status: Status string to filter by (e.g., "in_progress", "completed").

        Returns:
            List of attempts with the specified status.
        """
        return [a for a in self._attempts if a.status == status]
