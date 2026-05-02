from datetime import datetime
from typing import List, Optional

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from .workflow_run_service import WorkflowRunService


class AttemptService:
    def __init__(self, run_service: WorkflowRunService) -> None:
        self._run_service = run_service

    def _persist(self) -> None:
        self._run_service._persist()

    def create_attempt(
        self,
        run_id: str,
        attempt_number: int,
        status: str,
        conclusion: Optional[str],
        created_at: datetime,
        duration_seconds: Optional[float] = None,
    ) -> WorkflowRunAttempt:
        run = self._run_service.get_run_detail(run_id)
        if run is None:
            raise ValueError(f"Run with id '{run_id}' not found.")

        if any(a.attempt_number == attempt_number for a in run.attempts):
            raise ValueError(
                f"Attempt with attempt_number {attempt_number} already exists for run '{run_id}'."
            )

        attempt_id = len(run.attempts) + 1
        attempt = WorkflowRunAttempt(
            id=attempt_id,
            run_id=int(run_id) if run_id.isdigit() else hash(run_id) & 0x7FFFFFFF,
            attempt_number=attempt_number,
            status=status,
            conclusion=conclusion,
            created_at=created_at,
            duration_seconds=duration_seconds,
        )

        run.attempts.append(attempt)
        self._persist()
        return attempt

    def get_attempts_by_run_id(self, run_id: str) -> List[WorkflowRunAttempt]:
        run = self._run_service.get_run_detail(run_id)
        if run is None:
            return []

        return sorted(run.attempts, key=lambda a: a.attempt_number)
