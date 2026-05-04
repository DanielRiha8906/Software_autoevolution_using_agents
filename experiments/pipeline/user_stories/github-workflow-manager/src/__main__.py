import sys
import tkinter as tk

from .storage.workflow_json_storage import WorkflowJsonStorage
from .services.workflow_run_service import WorkflowRunService
from .services.workflow_run_attempt_service import WorkflowRunAttemptService
from .cli.workflow_cli import run_cli
from .cli.interactive_menu import run_interactive
from .gui.workflow_gui import WorkflowRunMainWindow


def main() -> None:
    storage = WorkflowJsonStorage(
        "artifacts/workflow_runs.json",
        "artifacts/workflow_run_attempts.json",
    )
    service = WorkflowRunService(storage)
    attempt_service = WorkflowRunAttemptService(storage)

    # Check for --gui flag
    if "--gui" in sys.argv:
        root = tk.Tk()
        window = WorkflowRunMainWindow(root, service, attempt_service)
        window.run()
    # No sub-command args → launch interactive menu
    elif len(sys.argv) == 1:
        run_interactive(service, attempt_service)
    else:
        run_cli(service, attempt_service)


if __name__ == "__main__":
    main()
