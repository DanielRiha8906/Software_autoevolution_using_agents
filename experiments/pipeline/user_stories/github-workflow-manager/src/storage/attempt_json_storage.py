import json
from pathlib import Path
from typing import List

from ..models.workflow_run_attempt import WorkflowRunAttempt


class AttemptJsonStorage:
    """JSON persistence layer for workflow run attempts.

    Stores and retrieves WorkflowRunAttempt instances to/from a JSON file.
    Mirrors the pattern of WorkflowJsonStorage for consistency.
    """

    def __init__(self, filepath: str = "artifacts/workflow_run_attempts.json"):
        """Initialize storage with a filepath.

        Args:
            filepath: Path to JSON file where attempts are persisted.
                Default: "artifacts/workflow_run_attempts.json"
                Parent directories are created if they don't exist.
        """
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def save(self, attempts: List[WorkflowRunAttempt]) -> None:
        """Persist attempts to JSON file.

        Args:
            attempts: List of WorkflowRunAttempt instances to save.
        """
        data = [attempt.to_dict() for attempt in attempts]
        self.filepath.write_text(json.dumps(data, indent=2))

    def load(self) -> List[WorkflowRunAttempt]:
        """Load attempts from JSON file.

        Returns:
            List of WorkflowRunAttempt instances. Returns empty list if file
            doesn't exist or is empty.
        """
        if not self.filepath.exists():
            return []
        raw = json.loads(self.filepath.read_text())
        return [WorkflowRunAttempt.from_dict(item) for item in raw]
