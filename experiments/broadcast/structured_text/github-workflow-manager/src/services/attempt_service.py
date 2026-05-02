from typing import List, Optional
from datetime import datetime

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..storage.workflow_json_storage import WorkflowJsonStorage


class AttemptService:
    """Service for managing workflow run attempts.

    Handles creation and retrieval of attempts with automatic attempt numbering
    and duplicate prevention per run.
    """

    def __init__(self, storage: WorkflowJsonStorage):
        """Initialize AttemptService with storage backend.

        Args:
            storage: WorkflowJsonStorage instance for persistence.
        """
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = self._load_attempts()
        self._next_id = self._calculate_next_id()

    def _load_attempts(self) -> List[WorkflowRunAttempt]:
        """Load attempts from storage.

        Returns:
            List[WorkflowRunAttempt]: Loaded attempts, empty list if no storage file.
        """
        # Attempts are stored in a separate file from workflow runs
        attempts_file = str(self._storage.filepath).replace("workflow_runs.json", "attempts.json")
        from pathlib import Path
        attempts_path = Path(attempts_file)

        if not attempts_path.exists():
            return []

        import json
        raw = json.loads(attempts_path.read_text())
        return [WorkflowRunAttempt.from_dict(item) for item in raw]

    def _calculate_next_id(self) -> int:
        """Calculate the next ID for a new attempt.

        Returns:
            int: Next available ID (max ID + 1, or 1 if no attempts exist).
        """
        if not self._attempts:
            return 1
        return max(a.id for a in self._attempts) + 1

    def _persist(self) -> None:
        """Persist all attempts to storage."""
        import json
        from pathlib import Path

        attempts_file = str(self._storage.filepath).replace("workflow_runs.json", "attempts.json")
        attempts_path = Path(attempts_file)
        attempts_path.parent.mkdir(parents=True, exist_ok=True)

        data = [attempt.to_dict() for attempt in self._attempts]
        attempts_path.write_text(json.dumps(data, indent=2))

    def create_attempt(
        self,
        run_id: int,
        status: str,
        conclusion: Optional[str],
        created_at: datetime,
    ) -> WorkflowRunAttempt:
        """Create a new attempt for a workflow run.

        Automatically assigns the next attempt_number for the run.

        Args:
            run_id: ID of the workflow run.
            status: Current status of the attempt.
            conclusion: Optional conclusion (e.g., success, failure).
            created_at: Timestamp when the attempt was created.

        Returns:
            WorkflowRunAttempt: The newly created attempt.

        Raises:
            ValueError: If the run_id is invalid (non-positive).
        """
        if run_id <= 0:
            raise ValueError(f"run_id must be positive, got {run_id}")

        # Determine the next attempt number for this run
        existing_attempts = self.get_attempts_by_run_id(run_id)
        attempt_number = len(existing_attempts) + 1

        attempt = WorkflowRunAttempt(
            id=self._next_id,
            run_id=run_id,
            attempt_number=attempt_number,
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            duration_seconds=0.0,
        )

        self._attempts.append(attempt)
        self._next_id += 1
        self._persist()

        return attempt

    def get_attempts_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        """Retrieve all attempts for a given run, sorted by attempt_number.

        Args:
            run_id: ID of the workflow run.

        Returns:
            List[WorkflowRunAttempt]: All attempts for the run, sorted ascending
                                      by attempt_number.
        """
        attempts = [a for a in self._attempts if a.run_id == run_id]
        return sorted(attempts, key=lambda a: a.attempt_number)
