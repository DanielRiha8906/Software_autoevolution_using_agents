import sys

from .storage.workflow_json_storage import WorkflowJsonStorage
from .services.workflow_run_service import WorkflowRunService
from .services.workflow_run_attempt_service import WorkflowRunAttemptService
from .cli.workflow_cli import run_cli
from .cli.interactive_menu import run_interactive


def main() -> None:
    storage = WorkflowJsonStorage(
        "artifacts/workflow_runs.json",
        "artifacts/workflow_run_attempts.json",
    )
    service = WorkflowRunService(storage)
    attempt_service = WorkflowRunAttemptService(storage)

    # No sub-command args → launch interactive menu
    if len(sys.argv) == 1:
        run_interactive(service, attempt_service)
    else:
        run_cli(service, attempt_service)


if __name__ == "__main__":
    main()
