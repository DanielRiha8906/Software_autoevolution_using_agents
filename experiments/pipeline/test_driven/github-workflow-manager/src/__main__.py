import sys

from .storage.workflow_json_storage import WorkflowJsonStorage
from .services.workflow_run_service import WorkflowRunService
from .services.attempt_service import AttemptService
from .cli.workflow_cli import run_cli
from .cli.interactive_menu import run_interactive


def main() -> None:
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    service = WorkflowRunService(storage)
    attempt_service = AttemptService()

    # Check for --gui flag
    if "--gui" in sys.argv:
        # Lazy import to avoid import errors if tkinter is not available
        from .gui.workflow_gui import WorkflowGUI
        gui = WorkflowGUI(service, attempt_service)
        gui.run()
    # No sub-command args → launch interactive menu
    elif len(sys.argv) == 1:
        run_interactive(service, attempt_service)
    else:
        run_cli(service, attempt_service)


if __name__ == "__main__":
    main()
