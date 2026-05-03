import json
from pathlib import Path
from typing import List

from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt


class WorkflowJsonStorage:
    def __init__(
        self,
        filepath: str = "artifacts/workflow_runs.json",
        attempts_filepath: str = "artifacts/workflow_run_attempts.json",
    ):
        self.filepath = Path(filepath)
        self.attempts_filepath = Path(attempts_filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def save(self, runs: List[WorkflowRun]) -> None:
        data = [run.to_dict() for run in runs]
        self.filepath.write_text(json.dumps(data, indent=2))

    def load(self) -> List[WorkflowRun]:
        if not self.filepath.exists():
            return []
        raw = json.loads(self.filepath.read_text())
        return [WorkflowRun.from_dict(item) for item in raw]

    def save_attempts(self, attempts: List[WorkflowRunAttempt]) -> None:
        data = [attempt.to_dict() for attempt in attempts]
        self.attempts_filepath.write_text(json.dumps(data, indent=2))

    def load_attempts(self) -> List[WorkflowRunAttempt]:
        if not self.attempts_filepath.exists():
            return []
        raw = json.loads(self.attempts_filepath.read_text())
        return [WorkflowRunAttempt.from_dict(item) for item in raw]
