import json
from pathlib import Path
from typing import List, Tuple

from ..models.workflow_run import WorkflowRun
from .workflow_run_service import WorkflowRunService


class WorkflowRunExportService:
    """Service for exporting and importing workflow runs to/from JSON files."""

    @staticmethod
    def export_to_file(service: WorkflowRunService, filepath: str) -> int:
        """Export all workflow runs to a JSON file.

        Args:
            service: The WorkflowRunService instance to export from.
            filepath: Path to the output JSON file.

        Returns:
            Number of runs exported.
        """
        runs = service.list_runs()
        data = [run.to_dict() for run in runs]

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2))

        return len(runs)

    @staticmethod
    def import_from_file(service: WorkflowRunService, filepath: str) -> Tuple[int, List[str]]:
        """Import workflow runs from a JSON file.

        Invalid or duplicate entries are skipped individually.
        Each run must have valid structure and a unique ID.

        Args:
            service: The WorkflowRunService instance to import into.
            filepath: Path to the input JSON file.

        Returns:
            Tuple of (number_imported, list_of_skip_reasons).
            Skip reasons describe why individual runs were skipped.
        """
        input_path = Path(filepath)

        if not input_path.exists():
            raise FileNotFoundError(f"Import file not found: {filepath}")

        raw = json.loads(input_path.read_text())

        if not isinstance(raw, list):
            raise ValueError("Import file must contain a JSON array of workflow runs")

        imported_count = 0
        skip_reasons = []

        for index, item in enumerate(raw):
            try:
                # Validate structure
                if not isinstance(item, dict):
                    skip_reasons.append(f"Entry {index}: Not a dictionary")
                    continue

                # Parse WorkflowRun
                run = WorkflowRun.from_dict(item)

                # Try to add
                service.add_workflow_run(run)
                imported_count += 1
            except ValueError as e:
                # This handles both parsing errors and duplicate ID errors
                skip_reasons.append(f"Entry {index} (id: {item.get('id', 'unknown')}): {str(e)}")
            except KeyError as e:
                skip_reasons.append(f"Entry {index}: Missing required field {str(e)}")
            except Exception as e:
                skip_reasons.append(f"Entry {index}: {type(e).__name__}: {str(e)}")

        return imported_count, skip_reasons
