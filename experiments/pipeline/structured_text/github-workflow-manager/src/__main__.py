import sys

from .storage.workflow_json_storage import WorkflowJsonStorage
from .storage.workflow_attempt_json_storage import WorkflowAttemptJsonStorage
from .services.workflow_run_service import WorkflowRunService
from .services.workflow_attempt_service import WorkflowAttemptService
from .services.workflow_statistics_service import WorkflowStatisticsService
from .services.workflow_data_portability_service import WorkflowDataPortabilityService
from .services.github_integration_service import GitHubIntegrationService
from .cli.workflow_cli import run_cli
from .cli.interactive_menu import run_interactive
from .gui.gui_viewer import run_gui


def main() -> None:
    storage = WorkflowJsonStorage("artifacts/workflow_runs.json")
    service = WorkflowRunService(storage)

    attempt_storage = WorkflowAttemptJsonStorage("artifacts/workflow_attempts.json")
    attempt_service = WorkflowAttemptService(attempt_storage)

    # Initialize statistics service
    stats_service = WorkflowStatisticsService(service, attempt_service)

    # Initialize data portability service
    portability_service = WorkflowDataPortabilityService(service, attempt_service)

    # Initialize GitHub integration service
    github_service = GitHubIntegrationService(fetch_mode="api")

    # Check for --gui flag first
    if "--gui" in sys.argv:
        run_gui(service, attempt_service)
    # No sub-command args → launch interactive menu
    elif len(sys.argv) == 1:
        run_interactive(service, attempt_service, stats_service, portability_service, github_service)
    else:
        run_cli(service, attempt_service, stats_service, portability_service, github_service)


if __name__ == "__main__":
    main()
