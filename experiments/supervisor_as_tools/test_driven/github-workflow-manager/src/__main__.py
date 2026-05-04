import sys

from .storage.workflow_json_storage import WorkflowJsonStorage
from .storage.attempt_json_storage import AttemptJsonStorage
from .services.workflow_run_service import WorkflowRunService
from .services.attempt_service import AttemptService
from .services.workflow_statistics_service import WorkflowStatisticsService
from .services.import_export_service import WorkflowImportExportService
from .cli.workflow_cli import run_cli
from .cli.interactive_menu import run_interactive


def main() -> None:
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    attempt_storage = AttemptJsonStorage("artifacts/workflow_attempts.json")
    attempt_service = AttemptService(attempt_storage)
    service = WorkflowRunService(storage)
    import_export_service = WorkflowImportExportService(service, attempt_service)

    # No sub-command args → launch interactive menu
    if len(sys.argv) == 1:
        run_interactive(service, import_export_service)
    else:
        run_cli(service, import_export_service)


if __name__ == "__main__":
    main()
