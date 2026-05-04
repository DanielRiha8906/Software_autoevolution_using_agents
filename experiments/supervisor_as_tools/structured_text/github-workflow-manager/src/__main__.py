import sys

from .storage.workflow_json_storage import WorkflowJsonStorage
from .storage.attempt_json_storage import AttemptJsonStorage
from .services.workflow_run_service import WorkflowRunService
from .services.attempt_service import AttemptService
from .services.statistics_service import StatisticsService
from .services.data_portability_service import DataPortabilityService
from .services.github_fetch_service import GitHubFetchService
from .adapters.github_cli_adapter import GhCliGitHubAdapter
from .adapters.github_data_mapper import GithubDataMapperImpl
from .adapters.json_file_adapter import JsonFileAdapter
from .cli.workflow_cli import run_cli
from .cli.interactive_menu import run_interactive
from .gui.workflow_run_gui import WorkflowRunGUI


def launch_gui(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
) -> None:
    """Launch the GUI viewer.

    Args:
        service: WorkflowRunService instance.
        attempt_service: AttemptService instance.
        statistics_service: StatisticsService instance.
    """
    try:
        gui = WorkflowRunGUI(service, attempt_service, statistics_service)
        gui.run()
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Failed to launch GUI: {e}")


def main() -> None:
    # Initialize adapters
    github_api_client = GhCliGitHubAdapter()
    data_mapper = GithubDataMapperImpl()
    file_handler = JsonFileAdapter()

    # Initialize storage
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    service = WorkflowRunService(storage)
    attempt_storage = AttemptJsonStorage("artifacts/workflow_attempts.json")
    attempt_service = AttemptService(attempt_storage)

    # Initialize services with injected adapters
    statistics_service = StatisticsService(service, attempt_service)
    portability_service = DataPortabilityService(file_handler)
    github_fetch_service = GitHubFetchService("", "", github_api_client, data_mapper)

    # Check for --gui flag
    if "--gui" in sys.argv:
        launch_gui(service, attempt_service, statistics_service)
    # No sub-command args → launch interactive menu
    elif len(sys.argv) == 1:
        run_interactive(service, attempt_service, statistics_service, portability_service, github_fetch_service)
    else:
        run_cli(service, attempt_service, statistics_service, portability_service, github_fetch_service)


if __name__ == "__main__":
    main()
