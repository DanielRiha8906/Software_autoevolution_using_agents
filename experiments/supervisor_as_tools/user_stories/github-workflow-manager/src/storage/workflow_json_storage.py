import json
from pathlib import Path
from typing import List

from ..models.workflow_run import WorkflowRun
from ..models.validation_error import ValidationError


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

    def export_to_file(self, runs: List[WorkflowRun], output_path: str) -> None:
        """Export workflow runs to a JSON file.

        Args:
            runs: List of WorkflowRun objects to export
            output_path: Path where the JSON file will be written

        Raises:
            IOError: If the file cannot be written
        """
        output_file = Path(output_path)
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            data = [run.to_dict() for run in runs]
            output_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            raise IOError(f"Failed to export to {output_path}: {e}") from e

    def import_from_file(self, input_path: str) -> List[WorkflowRun]:
        """Import workflow runs from a JSON file.

        Args:
            input_path: Path to the JSON file to import

        Returns:
            List of deserialized WorkflowRun objects

        Raises:
            FileNotFoundError: If the input file does not exist
            json.JSONDecodeError: If the JSON is malformed
            ValidationError: If validation fails
        """
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Import file not found: {input_path}")

        raw = json.loads(input_file.read_text())

        if not isinstance(raw, list):
            raise ValidationError("Root element must be an array")

        runs = []
        for item in raw:
            WorkflowRun.validate_dict(item)
            runs.append(WorkflowRun.from_dict(item))

        return runs
