from typing import List, Optional

from ..models.workflow_attempt import WorkflowRunAttempt
from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..storage.workflow_attempt_json_storage import WorkflowAttemptJsonStorage


class WorkflowAttemptService:
    def __init__(self, storage: WorkflowAttemptJsonStorage):
        self._storage = storage
        self._attempts: List[WorkflowRunAttempt] = storage.load()

    def _persist(self) -> None:
        self._storage.save(self._attempts)

    def add_attempt(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        if any(a.id == attempt.id for a in self._attempts):
            raise ValueError(f"Attempt with id '{attempt.id}' already exists.")
        if any(a.run_id == attempt.run_id and a.attempt_number == attempt.attempt_number
               for a in self._attempts):
            raise ValueError(f"Attempt number {attempt.attempt_number} already exists for run '{attempt.run_id}'.")
        self._attempts.append(attempt)
        self._persist()
        return attempt

    def list_attempts(self) -> List[WorkflowRunAttempt]:
        return list(self._attempts)

    def get_attempt_detail(self, attempt_id: str) -> Optional[WorkflowRunAttempt]:
        return next((a for a in self._attempts if a.id == attempt_id), None)

    def filter_by_run_id(self, run_id: str) -> List[WorkflowRunAttempt]:
        return sorted(
            [a for a in self._attempts if a.run_id == run_id],
            key=lambda a: a.attempt_number
        )

    def filter_by_status(self, status: WorkflowStatus) -> List[WorkflowRunAttempt]:
        return [a for a in self._attempts if a.status == status]

    def filter_by_conclusion(self, conclusion: WorkflowConclusion) -> List[WorkflowRunAttempt]:
        return [a for a in self._attempts if a.conclusion == conclusion]
