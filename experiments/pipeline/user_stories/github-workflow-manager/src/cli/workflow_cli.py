import argparse
import sys
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..models.statistics_report import StatisticsReport
from ..models.import_result import ImportResult
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_attempt_service import WorkflowRunAttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.statistics_service import StatisticsService
from ..services.workflow_export_import_service import WorkflowRunExportImportService


def _parse_datetime(date_str: str) -> datetime:
    """
    Parse a datetime string in either YYYY-MM-DD or ISO format.
    Returns a timezone-aware UTC datetime.

    Args:
        date_str: Date string in YYYY-MM-DD or ISO format

    Returns:
        timezone-aware datetime in UTC
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


def _fmt_run(run: WorkflowRun) -> str:
    conclusion = run.conclusion.value if run.conclusion else "—"
    updated = run.updated_at.isoformat() if run.updated_at else "—"
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
        f"  updated_at       : {updated}\n"
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


def _fmt_statistics_report(report: StatisticsReport) -> str:
    lines = ["--- Statistics Report ---\n"]

    lines.append("Count by Conclusion:")
    if report.count_by_conclusion:
        for conclusion, count in sorted(report.count_by_conclusion.items()):
            lines.append(f"  {conclusion}: {count}")
    else:
        lines.append("  (none)")

    lines.append(f"\nAverage Duration: {report.average_duration_seconds:.2f} seconds")
    lines.append(f"Average Attempts per Run: {report.average_attempts_per_run:.2f}")
    lines.append(f"Min Duration: {report.min_duration_seconds if report.min_duration_seconds is not None else '—'} seconds")
    lines.append(f"Max Duration: {report.max_duration_seconds if report.max_duration_seconds is not None else '—'} seconds")

    lines.append("\nDuration by Status:")
    for status, duration in sorted(report.duration_by_status.items()):
        lines.append(f"  {status}: {duration:.2f} seconds")

    return "\n".join(lines) + "\n"


def _print_import_result(result: ImportResult) -> None:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workflow-tracker",
        description="GitHub Workflow Run Tracker",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    add_p = sub.add_parser("add", help="Add a new workflow run")
    add_p.add_argument("--id", dest="run_id", default=None, help="Custom run ID (UUID generated if omitted)")
    add_p.add_argument("--name", required=True, help="Workflow name")
    add_p.add_argument("--branch", required=True, help="Branch name")
    add_p.add_argument(
        "--status",
        required=True,
        choices=[s.value for s in WorkflowStatus],
        help="Run status",
    )
    add_p.add_argument(
        "--conclusion",
        default=None,
        choices=[c.value for c in WorkflowConclusion],
        help="Run conclusion (optional)",
    )
    add_p.add_argument("--run-number", type=int, default=None)
    add_p.add_argument("--commit-sha", default=None)
    add_p.add_argument("--duration-seconds", type=float, default=0.0, help="Duration in seconds (default: 0.0)")

    # list
    list_p = sub.add_parser("list", help="List all runs")
    list_p.add_argument("--branch", default=None, help="Filter by branch")
    list_p.add_argument(
        "--status",
        default=None,
        choices=[s.value for s in WorkflowStatus],
        help="Filter by status",
    )
    list_p.add_argument(
        "--conclusion",
        default=None,
        choices=[c.value for c in WorkflowConclusion],
        help="Filter by conclusion",
    )
    list_p.add_argument("--created-after", default=None, help="Filter runs created on or after this date (YYYY-MM-DD or ISO format)")
    list_p.add_argument("--created-before", default=None, help="Filter runs created on or before this date (YYYY-MM-DD or ISO format)")
    list_p.add_argument("--duration-min", type=float, default=None, help="Filter runs with duration >= this value (seconds)")
    list_p.add_argument("--duration-max", type=float, default=None, help="Filter runs with duration <= this value (seconds)")
    list_p.add_argument("--has-attempts", action="store_true", help="Include only runs with attempts")
    list_p.add_argument("--no-attempts", action="store_true", help="Include only runs without attempts")

    # detail
    detail_p = sub.add_parser("detail", help="Show details for a single run")
    detail_p.add_argument("run_id", help="Run ID")

    # check
    check_p = sub.add_parser("check", help="Check run state")
    check_p.add_argument("run_id", help="Run ID")
    check_p.add_argument("--is-terminal", action="store_true", help="Check if run is terminal")
    check_p.add_argument("--is-successful", action="store_true", help="Check if run succeeded")
    check_p.add_argument("--is-failed", action="store_true", help="Check if run failed")
    check_p.add_argument("--is-running", action="store_true", help="Check if run is active")
    check_p.add_argument("--is-cancelled", action="store_true", help="Check if run was cancelled")

    # attempt add
    attempt_add_p = sub.add_parser("attempt-add", help="Add a new workflow run attempt")
    attempt_add_p.add_argument("--id", dest="attempt_id", type=int, required=True, help="Attempt ID")
    attempt_add_p.add_argument("--run-id", type=int, required=True, help="Parent run ID")
    attempt_add_p.add_argument("--attempt-number", type=int, required=True, help="Attempt number (positive integer)")
    attempt_add_p.add_argument("--status", required=True, help="Attempt status")
    attempt_add_p.add_argument("--conclusion", default=None, help="Attempt conclusion (optional)")
    attempt_add_p.add_argument("--duration-seconds", type=float, default=0.0, help="Duration in seconds (default: 0.0)")

    # attempt list
    attempt_list_p = sub.add_parser("attempt-list", help="List workflow run attempts")
    attempt_list_p.add_argument("--run-id", type=int, default=None, help="Filter by parent run ID")
    attempt_list_p.add_argument("--no-sort", action="store_true", help="Don't sort by attempt number (default: sorted)")

    # attempt detail
    attempt_detail_p = sub.add_parser("attempt-detail", help="Show details for a single attempt")
    attempt_detail_p.add_argument("attempt_id", type=int, help="Attempt ID")

    # stats
    stats_p = sub.add_parser("stats", help="Get aggregated statistics over workflow runs")
    stats_p.add_argument("--branch", default=None, help="Filter by branch")
    stats_p.add_argument(
        "--status",
        default=None,
        choices=[s.value for s in WorkflowStatus],
        help="Filter by status",
    )
    stats_p.add_argument(
        "--conclusion",
        default=None,
        choices=[c.value for c in WorkflowConclusion],
        help="Filter by conclusion",
    )
    stats_p.add_argument("--created-after", default=None, help="Filter runs created on or after this date (YYYY-MM-DD or ISO format)")
    stats_p.add_argument("--created-before", default=None, help="Filter runs created on or before this date (YYYY-MM-DD or ISO format)")
    stats_p.add_argument("--duration-min", type=float, default=None, help="Filter runs with duration >= this value (seconds)")
    stats_p.add_argument("--duration-max", type=float, default=None, help="Filter runs with duration <= this value (seconds)")
    stats_p.add_argument("--has-attempts", action="store_true", help="Include only runs with attempts")
    stats_p.add_argument("--no-attempts", action="store_true", help="Include only runs without attempts")

    # export
    export_p = sub.add_parser("export", help="Export workflow runs to JSON file")
    export_p.add_argument("--filepath", required=True, help="Output file path")
    export_p.add_argument("--include-attempts", action="store_true", help="Also export attempts to <filepath>_attempts.json")

    # import
    import_p = sub.add_parser("import", help="Import workflow runs from JSON file")
    import_p.add_argument("--filepath", required=True, help="Input file path")
    import_p.add_argument("--overwrite", action="store_true", help="Allow replacing runs with same id")
    import_p.add_argument("--dry-run", action="store_true", help="Validate without persisting")

    return parser


def run_cli(
    service: WorkflowRunService,
    attempt_service: WorkflowRunAttemptService,
    args=None,
) -> None:
    parser = build_parser()
    ns = parser.parse_args(args)
    tracker = WorkflowRunTracker(service)

    if ns.command == "add":
        run = tracker.track(
            workflow_name=ns.name,
            branch=ns.branch,
            status=WorkflowStatus(ns.status),
            conclusion=WorkflowConclusion(ns.conclusion) if ns.conclusion else None,
            run_number=ns.run_number,
            commit_sha=ns.commit_sha,
            run_id=ns.run_id,
            duration_seconds=ns.duration_seconds,
        )
        print(f"Added run {run.id}")

    elif ns.command == "list":
        # Validate duration arguments
        if ns.duration_min is not None and ns.duration_min < 0:
            print("Error: --duration-min must be non-negative.", file=sys.stderr)
            sys.exit(1)
        if ns.duration_max is not None and ns.duration_max < 0:
            print("Error: --duration-max must be non-negative.", file=sys.stderr)
            sys.exit(1)

        # Check mutual exclusivity of attempt flags
        if ns.has_attempts and ns.no_attempts:
            print("Error: --has-attempts and --no-attempts are mutually exclusive.", file=sys.stderr)
            sys.exit(1)

        # Parse datetime arguments
        created_after = None
        created_before = None
        if ns.created_after:
            try:
                created_after = _parse_datetime(ns.created_after)
            except ValueError as e:
                print(f"Error parsing --created-after: {e}", file=sys.stderr)
                sys.exit(1)
        if ns.created_before:
            try:
                created_before = _parse_datetime(ns.created_before)
            except ValueError as e:
                print(f"Error parsing --created-before: {e}", file=sys.stderr)
                sys.exit(1)

        # Determine has_attempts filter value
        has_attempts_filter = None
        if ns.has_attempts:
            has_attempts_filter = True
        elif ns.no_attempts:
            has_attempts_filter = False

        # Call query method with all filters
        runs = service.query(
            branch=ns.branch,
            status=WorkflowStatus(ns.status) if ns.status else None,
            conclusion=WorkflowConclusion(ns.conclusion) if ns.conclusion else None,
            created_after=created_after,
            created_before=created_before,
            duration_min=ns.duration_min,
            duration_max=ns.duration_max,
            has_attempts=has_attempts_filter,
            attempt_service=attempt_service,
        )

        if not runs:
            print("No runs found.")
            return
        for run in runs:
            print(_fmt_run(run))

    elif ns.command == "detail":
        run = service.get_run_detail(ns.run_id)
        if run is None:
            print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
            sys.exit(1)
        print(_fmt_run(run))

    elif ns.command == "check":
        run = service.get_run_detail(ns.run_id)
        if run is None:
            print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
            sys.exit(1)

        # If no flag specified, show all states
        if not any([ns.is_terminal, ns.is_successful, ns.is_failed, ns.is_running, ns.is_cancelled]):
            print(f"id               : {run.id}")
            print(f"is_terminal      : {run.is_terminal()}")
            print(f"is_successful    : {run.is_successful()}")
            print(f"is_failed        : {run.is_failed()}")
            print(f"is_running       : {run.is_running()}")
            print(f"is_cancelled     : {run.is_cancelled()}")
        else:
            # Check only requested flags
            if ns.is_terminal:
                print(f"{run.id}: is_terminal = {run.is_terminal()}")
            if ns.is_successful:
                print(f"{run.id}: is_successful = {run.is_successful()}")
            if ns.is_failed:
                print(f"{run.id}: is_failed = {run.is_failed()}")
            if ns.is_running:
                print(f"{run.id}: is_running = {run.is_running()}")
            if ns.is_cancelled:
                print(f"{run.id}: is_cancelled = {run.is_cancelled()}")

    elif ns.command == "attempt-add":
        attempt = WorkflowRunAttempt(
            id=ns.attempt_id,
            run_id=ns.run_id,
            attempt_number=ns.attempt_number,
            status=ns.status,
            conclusion=ns.conclusion,
            created_at=datetime.now(timezone.utc),
            duration_seconds=ns.duration_seconds,
        )
        attempt_service.add_attempt(attempt)
        print(f"Added attempt {attempt.id}")

    elif ns.command == "attempt-list":
        sorted_param = not ns.no_sort
        if ns.run_id is not None:
            attempts = attempt_service.get_attempts_for_run(ns.run_id, sorted=sorted_param)
        else:
            attempts = attempt_service.list_attempts(sorted=sorted_param)

        if not attempts:
            print("No attempts found.")
            return
        for attempt in attempts:
            print(_fmt_attempt(attempt))

    elif ns.command == "attempt-detail":
        attempt = attempt_service.get_attempt(ns.attempt_id)
        if attempt is None:
            print(f"No attempt found with id {ns.attempt_id}.", file=sys.stderr)
            sys.exit(1)
        print(_fmt_attempt(attempt))

    elif ns.command == "stats":
        # Validate duration arguments
        if ns.duration_min is not None and ns.duration_min < 0:
            print("Error: --duration-min must be non-negative.", file=sys.stderr)
            sys.exit(1)
        if ns.duration_max is not None and ns.duration_max < 0:
            print("Error: --duration-max must be non-negative.", file=sys.stderr)
            sys.exit(1)

        # Check mutual exclusivity of attempt flags
        if ns.has_attempts and ns.no_attempts:
            print("Error: --has-attempts and --no-attempts are mutually exclusive.", file=sys.stderr)
            sys.exit(1)

        # Parse datetime arguments
        created_after = None
        created_before = None
        if ns.created_after:
            try:
                created_after = _parse_datetime(ns.created_after)
            except ValueError as e:
                print(f"Error parsing --created-after: {e}", file=sys.stderr)
                sys.exit(1)
        if ns.created_before:
            try:
                created_before = _parse_datetime(ns.created_before)
            except ValueError as e:
                print(f"Error parsing --created-before: {e}", file=sys.stderr)
                sys.exit(1)

        # Determine has_attempts filter value
        has_attempts_filter = None
        if ns.has_attempts:
            has_attempts_filter = True
        elif ns.no_attempts:
            has_attempts_filter = False

        # Call query method with all filters
        runs = service.query(
            branch=ns.branch,
            status=WorkflowStatus(ns.status) if ns.status else None,
            conclusion=WorkflowConclusion(ns.conclusion) if ns.conclusion else None,
            created_after=created_after,
            created_before=created_before,
            duration_min=ns.duration_min,
            duration_max=ns.duration_max,
            has_attempts=has_attempts_filter,
            attempt_service=attempt_service,
        )

        # Calculate and print statistics
        stats_service = StatisticsService()
        report = stats_service.calculate_statistics(runs, attempt_service)
        print(_fmt_statistics_report(report))

    elif ns.command == "export":
        try:
            export_service = WorkflowRunExportImportService()
            export_service.export_to_file(
                ns.filepath,
                service,
                attempt_service=attempt_service if ns.include_attempts else None,
                include_attempts=ns.include_attempts,
            )
            runs_count = len(service.list_runs())
            print(f"Exported {runs_count} run(s) to {ns.filepath}")
        except IOError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif ns.command == "import":
        try:
            import_service = WorkflowRunExportImportService()
            result = import_service.import_from_file(
                ns.filepath,
                service,
                attempt_service=attempt_service,
                overwrite=ns.overwrite,
                dry_run=ns.dry_run,
            )
            _print_import_result(result)
            if ns.dry_run:
                print("\n(dry run: no changes persisted)")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
