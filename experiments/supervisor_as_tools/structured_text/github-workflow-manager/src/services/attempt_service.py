from typing import List, Optional
from datetime import datetime

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..storage.attempt_json_storage import AttemptJsonStorage


class AttemptService:
    def __init__(self, storage: AttemptJsonStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()

    def _persist(self) -> None:
        self._storage.save(self._attempts)

    def create_attempt(
        self,
        run_id: int,
        attempt_number: int,
        status: str,
        conclusion: Optional[str],
        created_at: datetime,
        duration_seconds: float = 0.0,
    ) -> WorkflowRunAttempt:
        # Composite key validation: prevent duplicate (run_id, attempt_number) pairs
        if any(a.run_id == run_id and a.attempt_number == attempt_number for a in self._attempts):
            raise ValueError(
                f"Attempt with run_id={run_id} and attempt_number={attempt_number} already exists."
            )

        # Auto-incrementing ID: max(existing ids) + 1, starting at 1
        attempt_id = max([a.id for a in self._attempts], default=0) + 1

        attempt = WorkflowRunAttempt(
            id=attempt_id,
            run_id=run_id,
            attempt_number=attempt_number,
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            duration_seconds=duration_seconds,
        )
        self._attempts.append(attempt)
        self._persist()
        return attempt

    def list_attempts(self) -> List[WorkflowRunAttempt]:
        return list(self._attempts)

    def get_attempts_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        filtered = [a for a in self._attempts if a.run_id == run_id]
        return sorted(filtered, key=lambda a: a.attempt_number)

    def get_attempt_detail(self, attempt_id: int) -> Optional[WorkflowRunAttempt]:
        return next((a for a in self._attempts if a.id == attempt_id), None)
