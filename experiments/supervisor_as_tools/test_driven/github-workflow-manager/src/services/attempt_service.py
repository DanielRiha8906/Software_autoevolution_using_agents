from typing import List, Dict, Tuple, Optional

from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..storage.attempt_json_storage import AttemptJsonStorage


class AttemptService:
    def __init__(self, storage: Optional[AttemptJsonStorage] = None):
        self._attempts: Dict[Tuple[int, int], WorkflowRunAttempt] = {}
        self._storage = storage
        # Load from storage if available
        for attempt in self._load_from_storage():
            key = (attempt.run_id, attempt.attempt_number)
            self._attempts[key] = attempt

    def _persist(self) -> None:
        """Save all attempts to storage if available."""
        if self._storage is not None:
            self._storage.save(list(self._attempts.values()))

    def _load_from_storage(self) -> List[WorkflowRunAttempt]:
        """Load attempts from storage if available."""
        if self._storage is None:
            return []
        return self._storage.load()

    def create(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        key = (attempt.run_id, attempt.attempt_number)
        if key in self._attempts:
            raise Exception(
                f"Attempt with run_id={attempt.run_id} and attempt_number={attempt.attempt_number} already exists."
            )
        self._attempts[key] = attempt
        self._persist()
        return attempt

    def get_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        attempts = [
            attempt
            for attempt in self._attempts.values()
            if attempt.run_id == run_id
        ]
        return sorted(attempts, key=lambda a: a.attempt_number)
