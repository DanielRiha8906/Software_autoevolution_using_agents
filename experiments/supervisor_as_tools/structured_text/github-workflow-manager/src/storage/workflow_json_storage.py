import json
from pathlib import Path
from typing import List

from ..models.workflow_run import WorkflowRun


class WorkflowJsonStorage:
    def __init__(self, filepath: str = "artifacts/workflow_runs.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def save(self, runs: List[WorkflowRun]) -> None:
        data = [run.to_dict() for run in runs]
        self.filepath.write_text(json.dumps(data, indent=2))

    def load(self) -> List[WorkflowRun]:
        if not self.filepath.exists():
            return []
        raw = json.loads(self.filepath.read_text())
        return [WorkflowRun.from_dict(item) for item in raw]
