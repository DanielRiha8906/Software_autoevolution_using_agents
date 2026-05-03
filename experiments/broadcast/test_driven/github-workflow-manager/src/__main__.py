import sys

from .storage.workflow_json_storage import WorkflowJsonStorage
from .services.workflow_run_service import WorkflowRunService
from .services.attempt_service import AttemptService
from .cli.workflow_cli import run_cli
from .cli.interactive_menu import run_interactive


def main() -> None:
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    attempt_service = AttemptService()
    service = WorkflowRunService(storage, attempt_service)

    # No sub-command args → launch interactive menu
    if len(sys.argv) == 1:
        run_interactive(service)
    else:
        run_cli(service)


if __name__ == "__main__":
    main()
