import sys
from datetime import datetime, timezone
from typing import Optional

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_attempt_service import WorkflowRunAttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.statistics_service import StatisticsService
from ..services.workflow_export_import_service import WorkflowRunExportImportService
from ..services.github_api_fetcher import GitHubAPIFetcher
from ..services.github_cli_fetcher import GitHubCLIFetcher
from ..auth.github_auth import GitHubAuthManager
from ..exceptions import (
    GitHubAuthError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubRateLimitError,
)


def _parse_datetime(date_str: str) -> datetime:
    """
    Parse a datetime string in either YYYY-MM-DD or ISO format.
    Returns a timezone-aware UTC datetime.
    """
    # Try ISO format first
    try:
        dt = datetime.fromisoformat(date_str)
        # Ensure it's timezone-aware; if not, add UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass

    # Try YYYY-MM-DD format
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        # Add UTC timezone
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(
            f"Could not parse date '{date_str}'. Use YYYY-MM-DD or ISO format (e.g., 2025-05-03 or 2025-05-03T10:30:00)"
        )


def _prompt(label: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    return value if value else (default or "")


def _choose(label: str, options: list, allow_blank: bool = False) -> Optional[str]:
    print(f"\n{label}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    if allow_blank:
        print("  0. (none)")
    while True:
        raw = input("Choice: ").strip()
        if allow_blank and raw in ("", "0"):
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("Invalid choice, try again.")


def _fmt_run(run: WorkflowRun) -> str:
    conclusion = run.conclusion.value if run.conclusion else "—"
    return (
        f"  id               : {run.id}\n"
        f"  workflow         : {run.workflow_name}\n"
        f"  branch           : {run.branch}\n"
        f"  status           : {run.status.value}\n"
        f"  conclusion       : {conclusion}\n"
        f"  run_number       : {run.run_number or '—'}\n"
        f"  commit_sha       : {run.commit_sha or '—'}\n"
        f"  duration_seconds : {run.duration_seconds}\n"
        f"  created_at       : {run.created_at.isoformat()}\n"
        f"  updated_at       : {run.updated_at.isoformat() if run.updated_at else '—'}\n"
    )


def _fmt_attempt(attempt: WorkflowRunAttempt) -> str:
    return (
        f"  id               : {attempt.id}\n"
        f"  run_id           : {attempt.run_id}\n"
        f"  attempt_number   : {attempt.attempt_number}\n"
        f"  status           : {attempt.status}\n"
        f"  conclusion       : {attempt.conclusion or '—'}\n"
        f"  duration_seconds : {attempt.duration_seconds}\n"
        f"  created_at       : {attempt.created_at.isoformat()}\n"
    )


def _add_run(service: WorkflowRunService) -> None:
    tracker = WorkflowRunTracker(service)
    print("\n--- Add Workflow Run ---")
    name = _prompt("Workflow name")
    branch = _prompt("Branch")
    status_val = _choose("Status", [s.value for s in WorkflowStatus])
    conclusion_val = _choose("Conclusion (optional)", [c.value for c in WorkflowConclusion], allow_blank=True)
    run_number_raw = _prompt("Run number (leave blank to skip)", "")
    commit_sha = _prompt("Commit SHA (leave blank to skip)", "") or None
    duration_raw = _prompt("Duration in seconds", "0.0")

    run_number = int(run_number_raw) if run_number_raw else None
    conclusion = WorkflowConclusion(conclusion_val) if conclusion_val else None
    duration_seconds = float(duration_raw) if duration_raw else 0.0

    run = tracker.track(
        workflow_name=name,
        branch=branch,
        status=WorkflowStatus(status_val),
        conclusion=conclusion,
        run_number=run_number,
        commit_sha=commit_sha,
        duration_seconds=duration_seconds,
    )
    print(f"\nAdded run {run.id}")


def _list_runs(service: WorkflowRunService) -> None:
    runs = service.list_runs()
    if not runs:
        print("\nNo runs recorded.")
        return
    print(f"\n--- {len(runs)} run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _detail_run(service: WorkflowRunService) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
    else:
        print(_fmt_run(run))


def _filter_menu(service: WorkflowRunService) -> None:
    filter_by = _choose("Filter by", ["branch", "status", "conclusion"])
    if filter_by == "branch":
        branch = _prompt("Branch name")
        runs = service.filter_by_branch(branch)
    elif filter_by == "status":
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        runs = service.filter_by_status(WorkflowStatus(status_val))
    else:
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        runs = service.filter_by_conclusion(WorkflowConclusion(conclusion_val))

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _check_run_state(service: WorkflowRunService) -> None:
    """Check state of a run."""
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
        return

    print(f"\n--- Run State: {run.id} ---")
    print(f"  is_terminal      : {run.is_terminal()}")
    print(f"  is_successful    : {run.is_successful()}")
    print(f"  is_failed        : {run.is_failed()}")
    print(f"  is_running       : {run.is_running()}")
    print(f"  is_cancelled     : {run.is_cancelled()}")


def _add_attempt(attempt_service: WorkflowRunAttemptService) -> None:
    print("\n--- Add Workflow Run Attempt ---")
    attempt_id_raw = _prompt("Attempt ID (integer)")
    run_id_raw = _prompt("Parent run ID (integer)")
    attempt_number_raw = _prompt("Attempt number (positive integer)")
    status = _prompt("Status")
    conclusion = _prompt("Conclusion (leave blank to skip)", "") or None
    duration_raw = _prompt("Duration in seconds", "0.0")

    try:
        attempt_id = int(attempt_id_raw)
        run_id = int(run_id_raw)
        attempt_number = int(attempt_number_raw)
        duration_seconds = float(duration_raw) if duration_raw else 0.0
    except ValueError:
        print("Invalid input: ID and attempt number must be integers, duration must be numeric.")
        return

    attempt = WorkflowRunAttempt(
        id=attempt_id,
        run_id=run_id,
        attempt_number=attempt_number,
        status=status,
        conclusion=conclusion,
        created_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )
    attempt_service.add_attempt(attempt)
    print(f"\nAdded attempt {attempt.id}")


def _list_attempts(attempt_service: WorkflowRunAttemptService) -> None:
    sort_choice = _choose("Sort by attempt number?", ["Yes", "No"])
    sorted_param = sort_choice == "Yes"
    attempts = attempt_service.list_attempts(sorted=sorted_param)
    if not attempts:
        print("\nNo attempts recorded.")
        return
    print(f"\n--- {len(attempts)} attempt(s) ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _detail_attempt(attempt_service: WorkflowRunAttemptService) -> None:
    attempt_id_raw = _prompt("\nEnter attempt ID")
    try:
        attempt_id = int(attempt_id_raw)
    except ValueError:
        print("Invalid attempt ID: must be an integer.")
        return
    attempt = attempt_service.get_attempt(attempt_id)
    if attempt is None:
        print(f"No attempt found with id {attempt_id}.")
    else:
        print(_fmt_attempt(attempt))


def _list_attempts_for_run(attempt_service: WorkflowRunAttemptService) -> None:
    run_id_raw = _prompt("\nEnter parent run ID")
    try:
        run_id = int(run_id_raw)
    except ValueError:
        print("Invalid run ID: must be an integer.")
        return
    sort_choice = _choose("Sort by attempt number?", ["Yes", "No"])
    sorted_param = sort_choice == "Yes"
    attempts = attempt_service.get_attempts_for_run(run_id, sorted=sorted_param)
    if not attempts:
        print(f"\nNo attempts found for run {run_id}.")
        return
    print(f"\n--- {len(attempts)} attempt(s) for run {run_id} ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _advanced_filter_menu(service: WorkflowRunService, attempt_service: WorkflowRunAttemptService) -> None:
    """Advanced filtering interface for workflow runs."""
    print("\n--- Advanced Filter ---")

    # Gather filter criteria
    created_after = None
    created_before = None
    duration_min = None
    duration_max = None
    has_attempts_filter = None
    branch = None
    status_filter = None
    conclusion_filter = None

    # Branch filter
    use_branch = _choose("Filter by branch?", ["Yes", "No"]) == "Yes"
    if use_branch:
        branch = _prompt("Branch name")

    # Status filter
    use_status = _choose("Filter by status?", ["Yes", "No"]) == "Yes"
    if use_status:
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        status_filter = WorkflowStatus(status_val)

    # Conclusion filter
    use_conclusion = _choose("Filter by conclusion?", ["Yes", "No"]) == "Yes"
    if use_conclusion:
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        conclusion_filter = WorkflowConclusion(conclusion_val)

    # Created after filter
    use_created_after = _choose("Filter by created date (after)?", ["Yes", "No"]) == "Yes"
    if use_created_after:
        date_str = _prompt("Date (YYYY-MM-DD or ISO format)")
        try:
            created_after = _parse_datetime(date_str)
        except ValueError as e:
            print(f"Error parsing date: {e}")
            return

    # Created before filter
    use_created_before = _choose("Filter by created date (before)?", ["Yes", "No"]) == "Yes"
    if use_created_before:
        date_str = _prompt("Date (YYYY-MM-DD or ISO format)")
        try:
            created_before = _parse_datetime(date_str)
        except ValueError as e:
            print(f"Error parsing date: {e}")
            return

    # Duration filters
    use_duration_min = _choose("Filter by minimum duration?", ["Yes", "No"]) == "Yes"
    if use_duration_min:
        duration_min_str = _prompt("Minimum duration (seconds)")
        try:
            duration_min = float(duration_min_str)
            if duration_min < 0:
                print("Duration must be non-negative.")
                return
        except ValueError:
            print("Duration must be a number.")
            return

    use_duration_max = _choose("Filter by maximum duration?", ["Yes", "No"]) == "Yes"
    if use_duration_max:
        duration_max_str = _prompt("Maximum duration (seconds)")
        try:
            duration_max = float(duration_max_str)
            if duration_max < 0:
                print("Duration must be non-negative.")
                return
        except ValueError:
            print("Duration must be a number.")
            return

    # Attempt presence filter
    use_attempts = _choose("Filter by attempt presence?", ["Yes", "No"]) == "Yes"
    if use_attempts:
        attempt_choice = _choose("Include runs", ["With attempts", "Without attempts"])
        has_attempts_filter = attempt_choice == "With attempts"

    # Apply query
    runs = service.query(
        branch=branch,
        status=status_filter,
        conclusion=conclusion_filter,
        created_after=created_after,
        created_before=created_before,
        duration_min=duration_min,
        duration_max=duration_max,
        has_attempts=has_attempts_filter,
        attempt_service=attempt_service if has_attempts_filter is not None else None,
    )

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _export_runs(service: WorkflowRunService, attempt_service: WorkflowRunAttemptService) -> None:
    """Export workflow runs to a JSON file."""
    print("\n--- Export Workflow Runs ---")
    filepath = _prompt("Output file path")
    include_attempts_choice = _choose("Include attempts?", ["Yes", "No"])
    include_attempts = include_attempts_choice == "Yes"

    try:
        export_service = WorkflowRunExportImportService()
        export_service.export_to_file(
            filepath,
            service,
            attempt_service=attempt_service if include_attempts else None,
            include_attempts=include_attempts,
        )
        runs_count = len(service.list_runs())
        print(f"\nExported {runs_count} run(s) to {filepath}")
    except IOError as e:
        print(f"Error: {e}")


def _import_runs(service: WorkflowRunService, attempt_service: WorkflowRunAttemptService) -> None:
    """Import workflow runs from a JSON file."""
    print("\n--- Import Workflow Runs ---")
    filepath = _prompt("Input file path")
    overwrite_choice = _choose("Overwrite existing runs with same ID?", ["Yes", "No"])
    overwrite = overwrite_choice == "Yes"
    dry_run_choice = _choose("Dry run (validate without persisting)?", ["Yes", "No"])
    dry_run = dry_run_choice == "Yes"

    try:
        import_service = WorkflowRunExportImportService()
        result = import_service.import_from_file(
            filepath,
            service,
            attempt_service=attempt_service,
            overwrite=overwrite,
            dry_run=dry_run,
        )

        print(f"\n--- Import Result ---")
        print(f"Filepath: {result.filepath}")
        print(f"Total records: {result.total_records}")
        print(f"Imported runs: {result.imported_runs}")
        print(f"Skipped runs: {result.skipped_runs}")
        print(f"Imported attempts: {result.imported_attempts}")
        print(f"Skipped attempts: {result.skipped_attempts}")

        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for i, error in enumerate(result.errors[:10], 1):
                print(f"  {i}. {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more")

        if dry_run:
            print("\n(dry run: no changes persisted)")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")


def _fetch_from_github(service: WorkflowRunService, attempt_service: WorkflowRunAttemptService) -> None:
    """Fetch workflow runs from GitHub repository."""
    print("\n--- Fetch from GitHub ---")

    owner = _prompt("GitHub repository owner (username or organization)")
    repo = _prompt("GitHub repository name")

    mode_choice = _choose("Fetch mode", ["GitHub REST API", "GitHub CLI (gh)"])
    mode = "api" if mode_choice == "GitHub REST API" else "cli"

    # Optional filters
    use_filters = _choose("Apply filters?", ["Yes", "No"]) == "Yes"
    branch = None
    status = None
    created_after = None

    if use_filters:
        use_branch = _choose("Filter by branch?", ["Yes", "No"]) == "Yes"
        if use_branch:
            branch = _prompt("Branch name")

        use_status = _choose("Filter by status?", ["Yes", "No"]) == "Yes"
        if use_status:
            status = _prompt("Status (e.g., completed, in_progress)")

        use_created_after = _choose("Filter by created date?", ["Yes", "No"]) == "Yes"
        if use_created_after:
            date_str = _prompt("Date (YYYY-MM-DD or ISO format)")
            try:
                created_after = _parse_datetime(date_str)
            except ValueError as e:
                print(f"Error parsing date: {e}")
                return

    # Token handling
    token_choice = _choose("Provide token?", ["Use env/secrets file", "Enter token"])
    explicit_token = None
    if token_choice == "Enter token":
        explicit_token = input("GitHub Personal Access Token (hidden): ").strip()
        if not explicit_token:
            print("Token cannot be empty.")
            return

    try:
        # Resolve token
        auth_manager = GitHubAuthManager()
        token = auth_manager.get_token(explicit_token=explicit_token)

        # Validate token format
        if not auth_manager.validate_token(token):
            print(
                "Error: Invalid GitHub token format. "
                "Expected GitHub Personal Access Token (e.g., ghp_xxx)."
            )
            return

        # Fetch runs
        if mode == "api":
            fetcher = GitHubAPIFetcher(token)
            runs = fetcher.fetch_runs(
                owner=owner,
                repo=repo,
                status=status,
                branch=branch,
                created_after=created_after,
            )
        else:  # mode == "cli"
            fetcher = GitHubCLIFetcher()
            runs = fetcher.fetch_runs(
                owner=owner,
                repo=repo,
                status=status,
                branch=branch,
                created_after=created_after,
            )

        # Add fetched runs to service
        added_count = 0
        skipped_count = 0
        for run in runs:
            if service.get_run_detail(run.id) is None:
                service.add_workflow_run(run)
                added_count += 1
            else:
                skipped_count += 1

        print(
            f"\nFetched {len(runs)} run(s) from {owner}/{repo} "
            f"({added_count} added, {skipped_count} already tracked)"
        )

    except GitHubAuthError as e:
        print(f"Authentication error: {e}")
    except GitHubRateLimitError as e:
        print(f"Rate limit error: {e}")
    except GitHubAPIError as e:
        print(f"GitHub API error: {e}")
    except GitHubNetworkError as e:
        print(f"Network error: {e}")
    except Exception as e:
        print(f"Unexpected error during fetch: {e}")


def _get_statistics(service: WorkflowRunService, attempt_service: WorkflowRunAttemptService) -> None:
    """Get aggregated statistics over workflow runs with optional filtering."""
    print("\n--- Get Statistics ---")

    # Gather filter criteria
    created_after = None
    created_before = None
    duration_min = None
    duration_max = None
    has_attempts_filter = None
    branch = None
    status_filter = None
    conclusion_filter = None

    # Branch filter
    use_branch = _choose("Filter by branch?", ["Yes", "No"]) == "Yes"
    if use_branch:
        branch = _prompt("Branch name")

    # Status filter
    use_status = _choose("Filter by status?", ["Yes", "No"]) == "Yes"
    if use_status:
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        status_filter = WorkflowStatus(status_val)

    # Conclusion filter
    use_conclusion = _choose("Filter by conclusion?", ["Yes", "No"]) == "Yes"
    if use_conclusion:
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        conclusion_filter = WorkflowConclusion(conclusion_val)

    # Created after filter
    use_created_after = _choose("Filter by created date (after)?", ["Yes", "No"]) == "Yes"
    if use_created_after:
        date_str = _prompt("Date (YYYY-MM-DD or ISO format)")
        try:
            created_after = _parse_datetime(date_str)
        except ValueError as e:
            print(f"Error parsing date: {e}")
            return

    # Created before filter
    use_created_before = _choose("Filter by created date (before)?", ["Yes", "No"]) == "Yes"
    if use_created_before:
        date_str = _prompt("Date (YYYY-MM-DD or ISO format)")
        try:
            created_before = _parse_datetime(date_str)
        except ValueError as e:
            print(f"Error parsing date: {e}")
            return

    # Duration filters
    use_duration_min = _choose("Filter by minimum duration?", ["Yes", "No"]) == "Yes"
    if use_duration_min:
        duration_min_str = _prompt("Minimum duration (seconds)")
        try:
            duration_min = float(duration_min_str)
            if duration_min < 0:
                print("Duration must be non-negative.")
                return
        except ValueError:
            print("Duration must be a number.")
            return

    use_duration_max = _choose("Filter by maximum duration?", ["Yes", "No"]) == "Yes"
    if use_duration_max:
        duration_max_str = _prompt("Maximum duration (seconds)")
        try:
            duration_max = float(duration_max_str)
            if duration_max < 0:
                print("Duration must be non-negative.")
                return
        except ValueError:
            print("Duration must be a number.")
            return

    # Attempt presence filter
    use_attempts = _choose("Filter by attempt presence?", ["Yes", "No"]) == "Yes"
    if use_attempts:
        attempt_choice = _choose("Include runs", ["With attempts", "Without attempts"])
        has_attempts_filter = attempt_choice == "With attempts"

    # Apply query
    runs = service.query(
        branch=branch,
        status=status_filter,
        conclusion=conclusion_filter,
        created_after=created_after,
        created_before=created_before,
        duration_min=duration_min,
        duration_max=duration_max,
        has_attempts=has_attempts_filter,
        attempt_service=attempt_service if has_attempts_filter is not None else None,
    )

    # Calculate and display statistics
    stats_service = StatisticsService()
    report = stats_service.calculate_statistics(runs, attempt_service)

    print("\n--- Statistics Report ---")
    print("Count by Conclusion:")
    if report.count_by_conclusion:
        for conclusion, count in sorted(report.count_by_conclusion.items()):
            print(f"  {conclusion}: {count}")
    else:
        print("  (none)")

    print(f"\nAverage Duration: {report.average_duration_seconds:.2f} seconds")
    print(f"Average Attempts per Run: {report.average_attempts_per_run:.2f}")
    print(f"Min Duration: {report.min_duration_seconds if report.min_duration_seconds is not None else '—'} seconds")
    print(f"Max Duration: {report.max_duration_seconds if report.max_duration_seconds is not None else '—'} seconds")

    print("\nDuration by Status:")
    for status, duration in sorted(report.duration_by_status.items()):
        print(f"  {status}: {duration:.2f} seconds")


MENU = [
    ("Add workflow run", _add_run),
    ("List all runs", _list_runs),
    ("Get run detail", _detail_run),
    ("Check run state", _check_run_state),
    ("Filter runs", _filter_menu),
    ("Advanced filter runs", _advanced_filter_menu),
    ("Get statistics", _get_statistics),
    ("Fetch from GitHub", _fetch_from_github),
    ("Export runs to JSON", _export_runs),
    ("Import runs from JSON", _import_runs),
    ("Add workflow run attempt", _add_attempt),
    ("List all attempts", _list_attempts),
    ("Get attempt detail", _detail_attempt),
    ("List attempts for run", _list_attempts_for_run),
    ("Exit", None),
]


def run_interactive(
    service: WorkflowRunService,
    attempt_service: WorkflowRunAttemptService,
) -> None:
    print("\nGitHub Workflow Tracker — Interactive Menu")
    while True:
        print("\n" + "=" * 44)
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i}. {label}")
        raw = input("\nSelect option: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(MENU)):
            print("Invalid selection.")
            continue
        label, handler = MENU[int(raw) - 1]
        if handler is None:
            print("Goodbye.")
            sys.exit(0)
        try:
            # Determine which service(s) to pass based on handler name
            if handler.__name__ in ("_advanced_filter_menu", "_get_statistics", "_export_runs", "_import_runs", "_fetch_from_github"):
                handler(service, attempt_service)
            elif handler.__name__.startswith("_add_attempt") or handler.__name__.startswith("_list_attempt") or handler.__name__.startswith("_detail_attempt"):
                handler(attempt_service)
            else:
                handler(service)
        except KeyboardInterrupt:
            print()
