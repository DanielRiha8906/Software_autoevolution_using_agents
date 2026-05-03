from typing import List, Dict, Tuple

from ..models.workflow_run_attempt import WorkflowRunAttempt


class AttemptService:
    def __init__(self):
        self._attempts: Dict[Tuple[int, int], WorkflowRunAttempt] = {}

    def create(self, attempt: WorkflowRunAttempt) -> WorkflowRunAttempt:
        key = (attempt.run_id, attempt.attempt_number)
        if key in self._attempts:
            raise Exception(
                f"Attempt with run_id={attempt.run_id} and attempt_number={attempt.attempt_number} already exists."
            )
        self._attempts[key] = attempt
        return attempt

    def get_by_run_id(self, run_id: int) -> List[WorkflowRunAttempt]:
        attempts = [
            attempt
            for attempt in self._attempts.values()
            if attempt.run_id == run_id
        ]
        return sorted(attempts, key=lambda a: a.attempt_number)
