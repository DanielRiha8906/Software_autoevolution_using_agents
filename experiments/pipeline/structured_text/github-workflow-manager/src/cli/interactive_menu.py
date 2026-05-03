import sys
from datetime import datetime
from typing import Optional

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_attempt_service import WorkflowAttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.workflow_statistics_service import WorkflowStatisticsService
from ..services.workflow_data_portability_service import WorkflowDataPortabilityService
from ..utils.timezone_converter import parse_datetime_with_timezone


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
        f"  id              : {run.id}\n"
        f"  workflow        : {run.workflow_name}\n"
        f"  branch          : {run.branch}\n"
        f"  status          : {run.status.value}\n"
        f"  conclusion      : {conclusion}\n"
        f"  run_number      : {run.run_number or '—'}\n"
        f"  commit_sha      : {run.commit_sha or '—'}\n"
        f"  created_at      : {run.created_at.isoformat()}\n"
        f"  updated_at      : {run.updated_at.isoformat() if run.updated_at else '—'}\n"
        f"  duration_seconds: {run.duration_seconds}\n"
    )


def _fmt_attempt(attempt: WorkflowRunAttempt) -> str:
    conclusion = attempt.conclusion.value if attempt.conclusion else "—"
    completed = attempt.completed_at.isoformat() if attempt.completed_at else "—"
    logs_url = attempt.logs_url or "—"
    return (
        f"  id              : {attempt.id}\n"
        f"  run_id          : {attempt.run_id}\n"
        f"  attempt_number  : {attempt.attempt_number}\n"
        f"  status          : {attempt.status.value}\n"
        f"  conclusion      : {conclusion}\n"
        f"  started_at      : {attempt.started_at.isoformat()}\n"
        f"  completed_at    : {completed}\n"
        f"  duration_seconds: {attempt.duration_seconds}\n"
        f"  logs_url        : {logs_url}\n"
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


def _build_filter_criteria_menu(attempt_service: Optional[WorkflowAttemptService] = None) -> dict:
    """Build filter criteria through interactive prompts."""
    criteria = {}

    print("\n--- Build Filter Criteria (leave blank to skip any filter) ---")

    # Branch filter
    branch = _prompt("Branch (leave blank to skip)", "")
    if branch:
        criteria["branch"] = branch

    # Status filter
    use_status = input("Filter by status? (y/n, default n): ").strip().lower()
    if use_status == "y":
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        criteria["status"] = WorkflowStatus(status_val)

    # Conclusion filter
    use_conclusion = input("Filter by conclusion? (y/n, default n): ").strip().lower()
    if use_conclusion == "y":
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        criteria["conclusion"] = WorkflowConclusion(conclusion_val)

    # Duration range filter
    use_duration = input("Filter by duration range? (y/n, default n): ").strip().lower()
    if use_duration == "y":
        duration_min_str = _prompt("Minimum duration in seconds (leave blank for no limit)", "")
        if duration_min_str:
            try:
                criteria["duration_min_seconds"] = float(duration_min_str)
            except ValueError:
                print("Invalid duration value, skipping minimum.")
        duration_max_str = _prompt("Maximum duration in seconds (leave blank for no limit)", "")
        if duration_max_str:
            try:
                criteria["duration_max_seconds"] = float(duration_max_str)
            except ValueError:
                print("Invalid duration value, skipping maximum.")

    # Timestamp filters
    use_timestamps = input("Filter by creation timestamp? (y/n, default n): ").strip().lower()
    if use_timestamps == "y":
        timezone_str = _prompt("Timezone (e.g., UTC, Europe/Paris)", "UTC")
        created_after_str = _prompt(
            "Created after (ISO format, e.g., 2026-05-03T10:00:00, leave blank for no limit)",
            ""
        )
        if created_after_str:
            try:
                criteria["created_after"] = parse_datetime_with_timezone(created_after_str, timezone_str)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")
        created_before_str = _prompt(
            "Created before (ISO format, e.g., 2026-05-03T10:00:00, leave blank for no limit)",
            ""
        )
        if created_before_str:
            try:
                criteria["created_before"] = parse_datetime_with_timezone(created_before_str, timezone_str)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")

    # Updated timestamp filters
    use_updated = input("Filter by update timestamp? (y/n, default n): ").strip().lower()
    if use_updated == "y":
        timezone_str = _prompt("Timezone (e.g., UTC, Europe/Paris)", "UTC")
        updated_after_str = _prompt(
            "Updated after (ISO format, e.g., 2026-05-03T10:00:00, leave blank for no limit)",
            ""
        )
        if updated_after_str:
            try:
                criteria["updated_after"] = parse_datetime_with_timezone(updated_after_str, timezone_str)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")
        updated_before_str = _prompt(
            "Updated before (ISO format, e.g., 2026-05-03T10:00:00, leave blank for no limit)",
            ""
        )
        if updated_before_str:
            try:
                criteria["updated_before"] = parse_datetime_with_timezone(updated_before_str, timezone_str)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")

    # Attempts filter
    if attempt_service is not None:
        use_attempts = input("Filter by attempts presence? (y/n, default n): ").strip().lower()
        if use_attempts == "y":
            attempts_choice = _choose("Show runs with or without attempts",
                                     ["with attempts", "without attempts"])
            if attempts_choice == "with attempts":
                criteria["with_attempts"] = True
            else:
                criteria["with_attempts"] = False
            criteria["attempt_service"] = attempt_service

    return criteria


def _filter_menu(service: WorkflowRunService, attempt_service: Optional[WorkflowAttemptService] = None) -> None:
    """Advanced filter menu for runs."""
    criteria = _build_filter_criteria_menu(attempt_service)

    if not criteria:
        print("\nNo filters selected.")
        return

    # Apply filters using composite filter
    runs = service.filter_runs(
        branch=criteria.get("branch"),
        status=criteria.get("status"),
        conclusion=criteria.get("conclusion"),
        duration_min_seconds=criteria.get("duration_min_seconds"),
        duration_max_seconds=criteria.get("duration_max_seconds"),
        created_before=criteria.get("created_before"),
        created_after=criteria.get("created_after"),
        updated_before=criteria.get("updated_before"),
        updated_after=criteria.get("updated_after"),
        with_attempts=criteria.get("with_attempts"),
        attempt_service=criteria.get("attempt_service"),
    )

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _query_run_state(service: WorkflowRunService) -> None:
    run_id = _prompt("\nEnter run ID")
    run = service.get_run_detail(run_id)
    if run is None:
        print(f"No run found with id '{run_id}'.")
        return
    print(f"\n--- Run State ---")
    print(f"  ID        : {run.id}")
    print(f"  Terminal  : {'yes' if run.is_terminal() else 'no'}")
    print(f"  Running   : {'yes' if run.is_running() else 'no'}")
    print(f"  Successful: {'yes' if run.is_successful() else 'no'}")
    print(f"  Failed    : {'yes' if run.is_failed() else 'no'}")
    print(f"  Cancelled : {'yes' if run.is_cancelled() else 'no'}")


def _add_attempt(attempt_service: WorkflowAttemptService) -> None:
    from ..services.workflow_attempt_tracker import WorkflowAttemptTracker
    tracker = WorkflowAttemptTracker(attempt_service)
    print("\n--- Add Workflow Attempt ---")
    run_id = _prompt("Run ID")
    attempt_number_raw = _prompt("Attempt number")
    status_val = _choose("Status", [s.value for s in WorkflowStatus])
    conclusion_val = _choose("Conclusion (optional)", [c.value for c in WorkflowConclusion], allow_blank=True)
    completed_at_raw = _prompt("Completed at (ISO format, leave blank to skip)", "")
    duration_raw = _prompt("Duration in seconds", "0.0")
    logs_url = _prompt("Logs URL (leave blank to skip)", "") or None

    attempt_number = int(attempt_number_raw)
    conclusion = WorkflowConclusion(conclusion_val) if conclusion_val else None
    completed_at = None
    if completed_at_raw:
        completed_at = datetime.fromisoformat(completed_at_raw)
    duration_seconds = float(duration_raw) if duration_raw else 0.0

    attempt = tracker.create_attempt(
        run_id=run_id,
        attempt_number=attempt_number,
        status=WorkflowStatus(status_val),
        conclusion=conclusion,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
        logs_url=logs_url,
    )
    print(f"\nAdded attempt {attempt.id}")


def _list_attempts(attempt_service: WorkflowAttemptService) -> None:
    attempts = attempt_service.list_attempts()
    if not attempts:
        print("\nNo attempts recorded.")
        return
    print(f"\n--- {len(attempts)} attempt(s) ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _detail_attempt(attempt_service: WorkflowAttemptService) -> None:
    attempt_id = _prompt("\nEnter attempt ID")
    attempt = attempt_service.get_attempt_detail(attempt_id)
    if attempt is None:
        print(f"No attempt found with id '{attempt_id}'.")
    else:
        print(_fmt_attempt(attempt))


def _build_attempt_filter_criteria_menu() -> dict:
    """Build attempt filter criteria through interactive prompts."""
    criteria = {}

    print("\n--- Build Attempt Filter Criteria (leave blank to skip any filter) ---")

    # Run ID filter
    run_id = _prompt("Run ID (leave blank to skip)", "")
    if run_id:
        criteria["run_id"] = run_id

    # Status filter
    use_status = input("Filter by status? (y/n, default n): ").strip().lower()
    if use_status == "y":
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        criteria["status"] = WorkflowStatus(status_val)

    # Conclusion filter
    use_conclusion = input("Filter by conclusion? (y/n, default n): ").strip().lower()
    if use_conclusion == "y":
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        criteria["conclusion"] = WorkflowConclusion(conclusion_val)

    # Duration range filter
    use_duration = input("Filter by duration range? (y/n, default n): ").strip().lower()
    if use_duration == "y":
        duration_min_str = _prompt("Minimum duration in seconds (leave blank for no limit)", "")
        if duration_min_str:
            try:
                criteria["duration_min_seconds"] = float(duration_min_str)
            except ValueError:
                print("Invalid duration value, skipping minimum.")
        duration_max_str = _prompt("Maximum duration in seconds (leave blank for no limit)", "")
        if duration_max_str:
            try:
                criteria["duration_max_seconds"] = float(duration_max_str)
            except ValueError:
                print("Invalid duration value, skipping maximum.")

    # Started timestamp filters
    use_started = input("Filter by start timestamp? (y/n, default n): ").strip().lower()
    if use_started == "y":
        timezone_str = _prompt("Timezone (e.g., UTC, Europe/Paris)", "UTC")
        started_after_str = _prompt(
            "Started after (ISO format, e.g., 2026-05-03T10:00:00, leave blank for no limit)",
            ""
        )
        if started_after_str:
            try:
                criteria["started_after"] = parse_datetime_with_timezone(started_after_str, timezone_str)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")
        started_before_str = _prompt(
            "Started before (ISO format, e.g., 2026-05-03T10:00:00, leave blank for no limit)",
            ""
        )
        if started_before_str:
            try:
                criteria["started_before"] = parse_datetime_with_timezone(started_before_str, timezone_str)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")

    # Completed timestamp filters
    use_completed = input("Filter by completion timestamp? (y/n, default n): ").strip().lower()
    if use_completed == "y":
        timezone_str = _prompt("Timezone (e.g., UTC, Europe/Paris)", "UTC")
        completed_after_str = _prompt(
            "Completed after (ISO format, e.g., 2026-05-03T10:00:00, leave blank for no limit)",
            ""
        )
        if completed_after_str:
            try:
                criteria["completed_after"] = parse_datetime_with_timezone(completed_after_str, timezone_str)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")
        completed_before_str = _prompt(
            "Completed before (ISO format, e.g., 2026-05-03T10:00:00, leave blank for no limit)",
            ""
        )
        if completed_before_str:
            try:
                criteria["completed_before"] = parse_datetime_with_timezone(completed_before_str, timezone_str)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}")

    return criteria


def _filter_attempts_menu(attempt_service: WorkflowAttemptService) -> None:
    """Advanced filter menu for attempts."""
    criteria = _build_attempt_filter_criteria_menu()

    if not criteria:
        print("\nNo filters selected.")
        return

    # Apply filters using composite filter
    attempts = attempt_service.filter_attempts(
        run_id=criteria.get("run_id"),
        status=criteria.get("status"),
        conclusion=criteria.get("conclusion"),
        duration_min_seconds=criteria.get("duration_min_seconds"),
        duration_max_seconds=criteria.get("duration_max_seconds"),
        started_before=criteria.get("started_before"),
        started_after=criteria.get("started_after"),
        completed_before=criteria.get("completed_before"),
        completed_after=criteria.get("completed_after"),
    )

    if not attempts:
        print("\nNo matching attempts.")
        return
    print(f"\n--- {len(attempts)} matching attempt(s) ---")
    for attempt in attempts:
        print(_fmt_attempt(attempt))


def _query_attempt_state(attempt_service: WorkflowAttemptService) -> None:
    attempt_id = _prompt("\nEnter attempt ID")
    attempt = attempt_service.get_attempt_detail(attempt_id)
    if attempt is None:
        print(f"No attempt found with id '{attempt_id}'.")
        return
    print(f"\n--- Attempt State ---")
    print(f"  ID        : {attempt.id}")
    print(f"  Terminal  : {'yes' if attempt.is_terminal() else 'no'}")
    print(f"  Running   : {'yes' if attempt.is_running() else 'no'}")
    print(f"  Successful: {'yes' if attempt.is_successful() else 'no'}")
    print(f"  Failed    : {'yes' if attempt.is_failed() else 'no'}")
    print(f"  Cancelled : {'yes' if attempt.is_cancelled() else 'no'}")


def _view_statistics(stats_service: WorkflowStatisticsService) -> None:
    """Display workflow statistics report."""
    report = stats_service.compute_report()
    print("\n--- Workflow Statistics Report ---")
    print(f"Total Runs: {report.total_runs}")
    print(f"\nRuns by Conclusion:")
    # Sort with None at the end for display
    items = sorted(
        report.conclusion_counts.items(),
        key=lambda x: (x[0] is None, x[0])
    )
    for conclusion, count in items:
        label = conclusion if conclusion is not None else "incomplete"
        print(f"  {label}: {count}")
    print(f"\nDuration Statistics (seconds):")
    print(f"  Average: {report.average_duration_seconds:.2f}")
    print(f"  Min: {report.min_duration_seconds}")
    print(f"  Max: {report.max_duration_seconds}")
    print(f"\nAverage Duration by Conclusion (seconds):")
    # Sort with None at the end for display
    items = sorted(
        report.duration_by_conclusion.items(),
        key=lambda x: (x[0] is None, x[0])
    )
    for conclusion, avg_duration in items:
        label = conclusion if conclusion is not None else "incomplete"
        print(f"  {label}: {avg_duration:.2f}")
    print(f"\nAttempt Statistics:")
    print(f"  Total Attempts: {report.total_attempts}")
    print(f"  Average Attempts per Run: {report.average_attempts_per_run:.2f}")
    print(f"  Runs with Attempts: {report.runs_with_attempts}")
    print(f"  Runs without Attempts: {report.runs_with_no_attempts}")
    print(f"\nGenerated at: {report.generated_at.isoformat()}")


def _export_runs_menu(portability_service) -> None:
    """Export runs to a JSON file."""
    filepath = _prompt("\nEnter output file path")
    if not filepath:
        print("No file path provided.")
        return
    try:
        count = portability_service.export_runs(filepath)
        print(f"Successfully exported {count} run(s) to {filepath}")
    except Exception as e:
        print(f"Error exporting runs: {e}")


def _import_runs_menu(portability_service) -> None:
    """Import runs from a JSON file."""
    filepath = _prompt("\nEnter input file path")
    if not filepath:
        print("No file path provided.")
        return
    skip_dup = input("Skip duplicate IDs? (y/n, default n): ").strip().lower() == "y"
    try:
        result = portability_service.import_runs(filepath, skip_duplicates=skip_dup)
        print(f"\nImport Results:")
        print(f"  Total in file: {result['count']}")
        print(f"  Successfully imported: {result['successful']}")
        if result['skipped']:
            print(f"  Skipped (duplicates): {len(result['skipped'])}")
        if result['failed'] > 0:
            print(f"  Failed: {result['failed']}")
    except Exception as e:
        print(f"Error importing runs: {e}")


def _export_attempts_menu(portability_service) -> None:
    """Export attempts to a JSON file."""
    filepath = _prompt("\nEnter output file path")
    if not filepath:
        print("No file path provided.")
        return
    try:
        count = portability_service.export_attempts(filepath)
        print(f"Successfully exported {count} attempt(s) to {filepath}")
    except Exception as e:
        print(f"Error exporting attempts: {e}")


def _import_attempts_menu(portability_service) -> None:
    """Import attempts from a JSON file."""
    filepath = _prompt("\nEnter input file path")
    if not filepath:
        print("No file path provided.")
        return
    skip_dup = input("Skip duplicate IDs? (y/n, default n): ").strip().lower() == "y"
    try:
        result = portability_service.import_attempts(filepath, skip_duplicates=skip_dup)
        print(f"\nImport Results:")
        print(f"  Total in file: {result['count']}")
        print(f"  Successfully imported: {result['successful']}")
        if result['skipped']:
            print(f"  Skipped (duplicates): {len(result['skipped'])}")
        if result['failed'] > 0:
            print(f"  Failed: {result['failed']}")
    except Exception as e:
        print(f"Error importing attempts: {e}")


def _run_menu(
    service: WorkflowRunService,
    attempt_service: Optional[WorkflowAttemptService] = None,
) -> None:
    # Create a wrapper for the filter menu to pass both service and attempt_service
    def filter_handler(s: WorkflowRunService) -> None:
        _filter_menu(s, attempt_service)

    run_menu = [
        ("Add workflow run", lambda s: _add_run(s)),
        ("List all runs", lambda s: _list_runs(s)),
        ("Get run detail", lambda s: _detail_run(s)),
        ("Filter runs", filter_handler),
        ("Query workflow state", lambda s: _query_run_state(s)),
        ("Back", None),
    ]
    print("\n--- Workflow Runs ---")
    while True:
        print("\n" + "=" * 44)
        for i, (label, _) in enumerate(run_menu, 1):
            print(f"  {i}. {label}")
        raw = input("\nSelect option: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(run_menu)):
            print("Invalid selection.")
            continue
        label, handler = run_menu[int(raw) - 1]
        if handler is None:
            return
        try:
            handler(service)
        except KeyboardInterrupt:
            print()


def _attempt_menu(
    attempt_service: WorkflowAttemptService,
) -> None:
    attempt_menu = [
        ("Add workflow attempt", lambda s: _add_attempt(s)),
        ("List all attempts", lambda s: _list_attempts(s)),
        ("Get attempt detail", lambda s: _detail_attempt(s)),
        ("Filter attempts", lambda s: _filter_attempts_menu(s)),
        ("Query attempt state", lambda s: _query_attempt_state(s)),
        ("Back", None),
    ]
    print("\n--- Workflow Attempts ---")
    while True:
        print("\n" + "=" * 44)
        for i, (label, _) in enumerate(attempt_menu, 1):
            print(f"  {i}. {label}")
        raw = input("\nSelect option: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(attempt_menu)):
            print("Invalid selection.")
            continue
        label, handler = attempt_menu[int(raw) - 1]
        if handler is None:
            return
        try:
            handler(attempt_service)
        except KeyboardInterrupt:
            print()


def _portability_menu(portability_service) -> None:
    """Data export/import menu."""
    portability_menu = [
        ("Export runs", lambda s: _export_runs_menu(s)),
        ("Import runs", lambda s: _import_runs_menu(s)),
        ("Export attempts", lambda s: _export_attempts_menu(s)),
        ("Import attempts", lambda s: _import_attempts_menu(s)),
        ("Back", None),
    ]
    print("\n--- Export/Import Data ---")
    while True:
        print("\n" + "=" * 44)
        for i, (label, _) in enumerate(portability_menu, 1):
            print(f"  {i}. {label}")
        raw = input("\nSelect option: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(portability_menu)):
            print("Invalid selection.")
            continue
        label, handler = portability_menu[int(raw) - 1]
        if handler is None:
            return
        try:
            handler(portability_service)
        except KeyboardInterrupt:
            print()


MENU = [
    ("Workflow Runs", "runs"),
    ("Workflow Attempts", "attempts"),
    ("View Statistics", "statistics"),
    ("Export/Import Data", "portability"),
    ("Exit", None),
]


def run_interactive(
    service: WorkflowRunService,
    attempt_service: Optional[WorkflowAttemptService] = None,
    stats_service: Optional[WorkflowStatisticsService] = None,
    portability_service=None,
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
        label, submenu = MENU[int(raw) - 1]
        if submenu is None:
            print("Goodbye.")
            sys.exit(0)
        try:
            if submenu == "runs":
                _run_menu(service, attempt_service)
            elif submenu == "attempts":
                if attempt_service is None:
                    print("Attempt service not initialized.")
                    continue
                _attempt_menu(attempt_service)
            elif submenu == "statistics":
                if stats_service is None:
                    print("Statistics service not initialized.")
                    continue
                _view_statistics(stats_service)
            elif submenu == "portability":
                if portability_service is None:
                    print("Data portability service not initialized.")
                    continue
                _portability_menu(portability_service)
        except KeyboardInterrupt:
            print()
