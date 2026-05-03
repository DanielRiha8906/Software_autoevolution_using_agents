import sys

from .storage.workflow_json_storage import WorkflowJsonStorage
from .storage.attempt_json_storage import AttemptJsonStorage
from .services.workflow_run_service import WorkflowRunService
from .services.attempt_service import AttemptService
from .cli.workflow_cli import run_cli
from .cli.interactive_menu import run_interactive


def main() -> None:
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    attempt_storage = AttemptJsonStorage("artifacts/workflow_attempts.json")
    service = WorkflowRunService(storage)
    attempt_service = AttemptService(attempt_storage)

    # No sub-command args → launch interactive menu
    if len(sys.argv) == 1:
        run_interactive(service, attempt_service)
    else:
        run_cli(service, attempt_service)


if __name__ == "__main__":
    main()
