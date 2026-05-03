import json
from pathlib import Path
from typing import List

from ..models.workflow_run_attempt import WorkflowRunAttempt


class AttemptJsonStorage:
    def __init__(self, filepath: str = "artifacts/workflow_attempts.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def save(self, attempts: List[WorkflowRunAttempt]) -> None:
        data = [attempt.to_dict() for attempt in attempts]
        self.filepath.write_text(json.dumps(data, indent=2))

    def load(self) -> List[WorkflowRunAttempt]:
        if not self.filepath.exists():
            return []
        raw = json.loads(self.filepath.read_text())
        return [WorkflowRunAttempt.from_dict(item) for item in raw]
