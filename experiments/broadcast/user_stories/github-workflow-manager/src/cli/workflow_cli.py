import argparse
import sys
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.attempt_service import AttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.workflow_query import DurationRange, TimestampRange
from ..services.workflow_statistics_service import WorkflowStatisticsService
from ..services.workflow_run_export_service import WorkflowRunExportService


def _fmt_run(run: WorkflowRun) -> str:
    conclusion = run.conclusion.value if run.conclusion else "—"
    updated = run.updated_at.isoformat() if run.updated_at else "—"
    return (
        f"  id          : {run.id}\n"
        f"  workflow    : {run.workflow_name}\n"
        f"  branch      : {run.branch}\n"
        f"  status      : {run.status.value}\n"
        f"  conclusion  : {conclusion}\n"
        f"  run_number  : {run.run_number or '—'}\n"
        f"  commit_sha  : {run.commit_sha or '—'}\n"
        f"  created_at  : {run.created_at.isoformat()}\n"
        f"  updated_at  : {updated}\n"
    )


def _fmt_attempt(attempt: WorkflowRunAttempt) -> str:
    conclusion = attempt.conclusion or "—"
    duration = f"{attempt.duration_seconds}s" if attempt.duration_seconds is not None else "—"
    return (
        f"  id              : {attempt.id}\n"
        f"  run_id          : {attempt.run_id}\n"
        f"  attempt_number  : {attempt.attempt_number}\n"
        f"  status          : {attempt.status}\n"
        f"  conclusion      : {conclusion}\n"
        f"  created_at      : {attempt.created_at.isoformat()}\n"
        f"  duration_seconds: {duration}\n"
    )


def _fmt_statistics(stats) -> str:
    """Format WorkflowRunStatistics for display.

    Args:
        stats: A WorkflowRunStatistics object.

    Returns:
        Formatted string representation.
    """
    lines = ["--- Workflow Run Statistics ---"]

    lines.append("\nCount by Conclusion:")
    if stats.count_by_conclusion:
        for conclusion, count in sorted(stats.count_by_conclusion.items()):
            lines.append(f"  {conclusion}: {count}")
    else:
        lines.append("  (no data)")

    lines.append(f"\nDuration Statistics:")
    lines.append(f"  Average: {stats.average_duration_seconds:.2f}s")
    lines.append(f"  Min: {stats.min_duration_seconds:.2f}s" if stats.min_duration_seconds is not None else f"  Min: —")
    lines.append(f"  Max: {stats.max_duration_seconds:.2f}s" if stats.max_duration_seconds is not None else f"  Max: —")

    lines.append(f"\nAverage Attempts per Run: {stats.average_attempts_per_run:.2f}")

    if stats.per_status_breakdown:
        lines.append("\nDuration Breakdown by Status:")
        for status, avg_duration in sorted(stats.per_status_breakdown.items()):
            lines.append(f"  {status}: {avg_duration:.2f}s")
    else:
        lines.append("\nDuration Breakdown by Status:")
        lines.append("  (no data)")

    return "\n".join(lines)


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

    # detail
    detail_p = sub.add_parser("detail", help="Show details for a single run")
    detail_p.add_argument("run_id", help="Run ID")

    # state
    state_p = sub.add_parser("state", help="Check state of a workflow run")
    state_p.add_argument("run_id", help="Run ID")

    # attempt-create
    attempt_create_p = sub.add_parser("attempt-create", help="Create a workflow run attempt")
    attempt_create_p.add_argument("--run-id", type=int, required=True, help="Run ID for this attempt")
    attempt_create_p.add_argument("--attempt-id", type=int, required=True, help="Attempt ID")
    attempt_create_p.add_argument("--attempt-number", type=int, required=True, help="Attempt number")
    attempt_create_p.add_argument("--status", required=True, help="Attempt status (e.g., in_progress, completed)")
    attempt_create_p.add_argument("--conclusion", default=None, help="Attempt conclusion (optional)")
    attempt_create_p.add_argument("--duration", type=float, default=None, help="Duration in seconds (optional)")

    # attempt-list
    attempt_list_p = sub.add_parser("attempt-list", help="List all attempts for a run")
    attempt_list_p.add_argument("--run-id", type=int, required=True, help="Run ID to filter attempts")

    # query
    query_p = sub.add_parser("query", help="Query workflow runs with advanced filtering")
    query_p.add_argument(
        "--min-duration",
        type=float,
        default=None,
        help="Minimum duration in seconds (inclusive)",
    )
    query_p.add_argument(
        "--max-duration",
        type=float,
        default=None,
        help="Maximum duration in seconds (inclusive)",
    )
    query_p.add_argument(
        "--created-after",
        type=str,
        default=None,
        help="Filter runs created after this datetime (ISO format, exclusive)",
    )
    query_p.add_argument(
        "--created-before",
        type=str,
        default=None,
        help="Filter runs created before this datetime (ISO format, exclusive)",
    )
    query_p.add_argument(
        "--has-attempts",
        type=lambda x: x.lower() == "true",
        default=None,
        help="Filter by attempt presence (true/false)",
    )

    # stats
    stats_p = sub.add_parser("stats", help="Show aggregated workflow statistics")

    # export
    export_p = sub.add_parser("export", help="Export all workflow runs to a JSON file")
    export_p.add_argument("--filepath", required=True, help="Path to output JSON file")

    # import
    import_p = sub.add_parser("import", help="Import workflow runs from a JSON file")
    import_p.add_argument("--filepath", required=True, help="Path to input JSON file")

    return parser


def run_cli(workflow_service: WorkflowRunService, attempt_service: AttemptService, args=None) -> None:
    parser = build_parser()
    ns = parser.parse_args(args)
    tracker = WorkflowRunTracker(workflow_service)

    if ns.command == "add":
        run = tracker.track(
            workflow_name=ns.name,
            branch=ns.branch,
            status=WorkflowStatus(ns.status),
            conclusion=WorkflowConclusion(ns.conclusion) if ns.conclusion else None,
            run_number=ns.run_number,
            commit_sha=ns.commit_sha,
            run_id=ns.run_id,
        )
        print(f"Added run {run.id}")

    elif ns.command == "list":
        runs = workflow_service.list_runs()
        if ns.branch:
            runs = workflow_service.filter_by_branch(ns.branch)
        elif ns.status:
            runs = workflow_service.filter_by_status(WorkflowStatus(ns.status))
        elif ns.conclusion:
            runs = workflow_service.filter_by_conclusion(WorkflowConclusion(ns.conclusion))

        if not runs:
            print("No runs found.")
            return
        for run in runs:
            print(_fmt_run(run))

    elif ns.command == "detail":
        run = workflow_service.get_run_detail(ns.run_id)
        if run is None:
            print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
            sys.exit(1)
        print(_fmt_run(run))

    elif ns.command == "state":
        run = workflow_service.get_run_detail(ns.run_id)
        if run is None:
            print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
            sys.exit(1)
        print(f"  Run ID         : {run.id}")
        print(f"  is_running()   : {run.is_running()}")
        print(f"  is_terminal()  : {run.is_terminal()}")
        print(f"  is_successful(): {run.is_successful()}")
        print(f"  is_failed()    : {run.is_failed()}")
        print(f"  is_cancelled() : {run.is_cancelled()}")

    elif ns.command == "attempt-create":
        attempt = WorkflowRunAttempt(
            id=ns.attempt_id,
            run_id=ns.run_id,
            attempt_number=ns.attempt_number,
            status=ns.status,
            conclusion=ns.conclusion,
            created_at=datetime.now(timezone.utc),
            duration_seconds=ns.duration,
        )
        try:
            created_attempt = attempt_service.create_attempt(attempt)
            print(f"Created attempt {created_attempt.attempt_number} for run {created_attempt.run_id}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif ns.command == "attempt-list":
        attempts = attempt_service.get_attempts_for_run(ns.run_id)
        if not attempts:
            print(f"No attempts found for run {ns.run_id}.")
            return
        print(f"\n--- {len(attempts)} attempt(s) for run {ns.run_id} ---")
        for attempt in attempts:
            print(_fmt_attempt(attempt))

    elif ns.command == "query":
        query = workflow_service.create_query(attempt_service)

        created_after = None
        if ns.created_after:
            try:
                created_after = datetime.fromisoformat(ns.created_after)
            except ValueError:
                print(f"Error: Invalid datetime format for --created-after: {ns.created_after}", file=sys.stderr)
                sys.exit(1)

        created_before = None
        if ns.created_before:
            try:
                created_before = datetime.fromisoformat(ns.created_before)
            except ValueError:
                print(f"Error: Invalid datetime format for --created-before: {ns.created_before}", file=sys.stderr)
                sys.exit(1)

        duration_range = None
        if ns.min_duration is not None or ns.max_duration is not None:
            duration_range = DurationRange(
                min_seconds=ns.min_duration,
                max_seconds=ns.max_duration
            )

        timestamp_range = None
        if created_after is not None or created_before is not None:
            timestamp_range = TimestampRange(
                before=created_before,
                after=created_after
            )

        try:
            result = query.query(
                duration_range=duration_range,
                timestamp_range=timestamp_range,
                has_attempts=ns.has_attempts
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if not result:
            print("No runs match the query criteria.")
            return

        print(f"\n--- {len(result)} matching run(s) ---")
        for run in result:
            print(_fmt_run(run))

    elif ns.command == "stats":
        stats_service = WorkflowStatisticsService()
        runs = workflow_service.list_runs()
        attempts = attempt_service.list_all_attempts()
        stats = stats_service.compute_statistics(runs, attempts)
        print("\n" + _fmt_statistics(stats))

    elif ns.command == "export":
        try:
            count = WorkflowRunExportService.export_to_file(workflow_service, ns.filepath)
            print(f"Exported {count} workflow run(s) to {ns.filepath}")
        except Exception as e:
            print(f"Error exporting: {e}", file=sys.stderr)
            sys.exit(1)

    elif ns.command == "import":
        try:
            imported, skips = WorkflowRunExportService.import_from_file(workflow_service, ns.filepath)
            print(f"Imported {imported} workflow run(s) from {ns.filepath}")
            if skips:
                print(f"\n{len(skips)} entries skipped:")
                for reason in skips:
                    print(f"  - {reason}")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error importing: {e}", file=sys.stderr)
            sys.exit(1)
