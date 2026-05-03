import argparse
import json
import sys
from datetime import datetime, timezone

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


def _fmt_run(run: WorkflowRun) -> str:
    conclusion = run.conclusion.value if run.conclusion else "—"
    updated = run.updated_at.isoformat() if run.updated_at else "—"
    return (
        f"  id              : {run.id}\n"
        f"  workflow        : {run.workflow_name}\n"
        f"  branch          : {run.branch}\n"
        f"  status          : {run.status.value}\n"
        f"  conclusion      : {conclusion}\n"
        f"  run_number      : {run.run_number or '—'}\n"
        f"  commit_sha      : {run.commit_sha or '—'}\n"
        f"  created_at      : {run.created_at.isoformat()}\n"
        f"  updated_at      : {updated}\n"
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
    add_p.add_argument("--duration-seconds", type=float, default=0.0, help="Duration in seconds (optional)")

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
    list_p.add_argument(
        "--duration-min",
        type=float,
        default=None,
        help="Minimum duration in seconds",
    )
    list_p.add_argument(
        "--duration-max",
        type=float,
        default=None,
        help="Maximum duration in seconds",
    )
    list_p.add_argument(
        "--created-before",
        default=None,
        help="Filter by created_at before (ISO format, e.g., 2026-05-03T10:00:00)",
    )
    list_p.add_argument(
        "--created-after",
        default=None,
        help="Filter by created_at after (ISO format, e.g., 2026-05-03T10:00:00)",
    )
    list_p.add_argument(
        "--updated-before",
        default=None,
        help="Filter by updated_at before (ISO format, e.g., 2026-05-03T10:00:00)",
    )
    list_p.add_argument(
        "--updated-after",
        default=None,
        help="Filter by updated_at after (ISO format, e.g., 2026-05-03T10:00:00)",
    )
    list_p.add_argument(
        "--with-attempts",
        action="store_true",
        help="Filter to only runs with attempts",
    )
    list_p.add_argument(
        "--without-attempts",
        action="store_true",
        help="Filter to only runs without attempts",
    )
    list_p.add_argument(
        "--timezone",
        default="UTC",
        help="Timezone for timestamp input (default: UTC, e.g., Europe/Paris)",
    )

    # detail
    detail_p = sub.add_parser("detail", help="Show details for a single run")
    detail_p.add_argument("run_id", help="Run ID")

    # query-state
    query_p = sub.add_parser("query-state", help="Query workflow run state")
    query_p.add_argument("run_id", help="Run ID")

    # attempt commands
    attempt_p = sub.add_parser("attempt", help="Manage workflow attempts")
    attempt_sub = attempt_p.add_subparsers(dest="attempt_command", required=True)

    # attempt add
    attempt_add_p = attempt_sub.add_parser("add", help="Add a new workflow attempt")
    attempt_add_p.add_argument("--id", dest="attempt_id", default=None, help="Custom attempt ID (UUID generated if omitted)")
    attempt_add_p.add_argument("--run-id", required=True, help="Run ID")
    attempt_add_p.add_argument("--attempt-number", type=int, required=True, help="Attempt number")
    attempt_add_p.add_argument(
        "--status",
        required=True,
        choices=[s.value for s in WorkflowStatus],
        help="Attempt status",
    )
    attempt_add_p.add_argument(
        "--conclusion",
        default=None,
        choices=[c.value for c in WorkflowConclusion],
        help="Attempt conclusion (optional)",
    )
    attempt_add_p.add_argument("--completed-at", default=None, help="Completion timestamp (ISO format, optional)")
    attempt_add_p.add_argument("--duration-seconds", type=float, default=0.0, help="Duration in seconds (optional)")
    attempt_add_p.add_argument("--logs-url", default=None, help="Logs URL (optional)")

    # attempt list
    attempt_list_p = attempt_sub.add_parser("list", help="List all attempts")
    attempt_list_p.add_argument("--run-id", default=None, help="Filter by run ID")
    attempt_list_p.add_argument(
        "--status",
        default=None,
        choices=[s.value for s in WorkflowStatus],
        help="Filter by status",
    )
    attempt_list_p.add_argument(
        "--conclusion",
        default=None,
        choices=[c.value for c in WorkflowConclusion],
        help="Filter by conclusion",
    )
    attempt_list_p.add_argument(
        "--duration-min",
        type=float,
        default=None,
        help="Minimum duration in seconds",
    )
    attempt_list_p.add_argument(
        "--duration-max",
        type=float,
        default=None,
        help="Maximum duration in seconds",
    )
    attempt_list_p.add_argument(
        "--started-before",
        default=None,
        help="Filter by started_at before (ISO format, e.g., 2026-05-03T10:00:00)",
    )
    attempt_list_p.add_argument(
        "--started-after",
        default=None,
        help="Filter by started_at after (ISO format, e.g., 2026-05-03T10:00:00)",
    )
    attempt_list_p.add_argument(
        "--completed-before",
        default=None,
        help="Filter by completed_at before (ISO format, e.g., 2026-05-03T10:00:00)",
    )
    attempt_list_p.add_argument(
        "--completed-after",
        default=None,
        help="Filter by completed_at after (ISO format, e.g., 2026-05-03T10:00:00)",
    )
    attempt_list_p.add_argument(
        "--timezone",
        default="UTC",
        help="Timezone for timestamp input (default: UTC, e.g., Europe/Paris)",
    )

    # attempt detail
    attempt_detail_p = attempt_sub.add_parser("detail", help="Show details for a single attempt")
    attempt_detail_p.add_argument("attempt_id", help="Attempt ID")

    # attempt query-state
    attempt_query_p = attempt_sub.add_parser("query-state", help="Query workflow attempt state")
    attempt_query_p.add_argument("attempt_id", help="Attempt ID")

    # report
    report_p = sub.add_parser("report", help="Generate workflow statistics report")
    report_p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # export
    export_p = sub.add_parser("export", help="Export workflow data to JSON file")
    export_sub = export_p.add_subparsers(dest="export_command", required=True)

    export_runs_p = export_sub.add_parser("runs", help="Export all runs")
    export_runs_p.add_argument("--output", "-o", required=True, help="Output JSON file path")

    export_attempts_p = export_sub.add_parser("attempts", help="Export all attempts")
    export_attempts_p.add_argument("--output", "-o", required=True, help="Output JSON file path")

    # import
    import_p = sub.add_parser("import", help="Import workflow data from JSON file")
    import_sub = import_p.add_subparsers(dest="import_command", required=True)

    import_runs_p = import_sub.add_parser("runs", help="Import runs from file")
    import_runs_p.add_argument("--input", "-i", required=True, help="Input JSON file path")
    import_runs_p.add_argument(
        "--skip-duplicates",
        action="store_true",
        help="Skip runs with duplicate IDs instead of raising error",
    )

    import_attempts_p = import_sub.add_parser("attempts", help="Import attempts from file")
    import_attempts_p.add_argument("--input", "-i", required=True, help="Input JSON file path")
    import_attempts_p.add_argument(
        "--skip-duplicates",
        action="store_true",
        help="Skip attempts with duplicate IDs instead of raising error",
    )

    return parser


def run_cli(
    service: WorkflowRunService,
    attempt_service: WorkflowAttemptService = None,
    stats_service: WorkflowStatisticsService = None,
    portability_service=None,
    args=None,
) -> None:
    parser = build_parser()
    ns = parser.parse_args(args)
    tracker = WorkflowRunTracker(service, attempt_service)

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
        # Parse timestamp filters with timezone support
        created_before = None
        created_after = None
        updated_before = None
        updated_after = None

        try:
            if ns.created_before:
                created_before = parse_datetime_with_timezone(ns.created_before, ns.timezone)
            if ns.created_after:
                created_after = parse_datetime_with_timezone(ns.created_after, ns.timezone)
            if ns.updated_before:
                updated_before = parse_datetime_with_timezone(ns.updated_before, ns.timezone)
            if ns.updated_after:
                updated_after = parse_datetime_with_timezone(ns.updated_after, ns.timezone)
        except ValueError as e:
            print(f"Error parsing timestamp: {e}", file=sys.stderr)
            sys.exit(1)

        # Handle mutually exclusive attempts filters
        with_attempts = None
        if ns.with_attempts and ns.without_attempts:
            print("Error: --with-attempts and --without-attempts are mutually exclusive.", file=sys.stderr)
            sys.exit(1)
        if ns.with_attempts:
            with_attempts = True
        elif ns.without_attempts:
            with_attempts = False

        # Use composite filter
        runs = service.filter_runs(
            branch=ns.branch,
            status=WorkflowStatus(ns.status) if ns.status else None,
            conclusion=WorkflowConclusion(ns.conclusion) if ns.conclusion else None,
            duration_min_seconds=ns.duration_min,
            duration_max_seconds=ns.duration_max,
            created_before=created_before,
            created_after=created_after,
            updated_before=updated_before,
            updated_after=updated_after,
            with_attempts=with_attempts,
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

    elif ns.command == "query-state":
        run = service.get_run_detail(ns.run_id)
        if run is None:
            print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
            sys.exit(1)
        print(f"Run ID: {run.id}")
        print(f"Terminal: {'yes' if run.is_terminal() else 'no'}")
        print(f"Running: {'yes' if run.is_running() else 'no'}")
        print(f"Successful: {'yes' if run.is_successful() else 'no'}")
        print(f"Failed: {'yes' if run.is_failed() else 'no'}")
        print(f"Cancelled: {'yes' if run.is_cancelled() else 'no'}")

    elif ns.command == "attempt":
        if attempt_service is None:
            print("Attempt service not initialized.", file=sys.stderr)
            sys.exit(1)

        if ns.attempt_command == "add":
            completed_at = None
            if ns.completed_at:
                completed_at = datetime.fromisoformat(ns.completed_at)

            attempt = tracker.create_attempt(
                run_id=ns.run_id,
                attempt_number=ns.attempt_number,
                status=WorkflowStatus(ns.status),
                conclusion=WorkflowConclusion(ns.conclusion) if ns.conclusion else None,
                completed_at=completed_at,
                duration_seconds=ns.duration_seconds,
                logs_url=ns.logs_url,
                attempt_id=ns.attempt_id,
            )
            print(f"Added attempt {attempt.id}")

        elif ns.attempt_command == "list":
            # Parse timestamp filters with timezone support
            started_before = None
            started_after = None
            completed_before = None
            completed_after = None

            try:
                if ns.started_before:
                    started_before = parse_datetime_with_timezone(ns.started_before, ns.timezone)
                if ns.started_after:
                    started_after = parse_datetime_with_timezone(ns.started_after, ns.timezone)
                if ns.completed_before:
                    completed_before = parse_datetime_with_timezone(ns.completed_before, ns.timezone)
                if ns.completed_after:
                    completed_after = parse_datetime_with_timezone(ns.completed_after, ns.timezone)
            except ValueError as e:
                print(f"Error parsing timestamp: {e}", file=sys.stderr)
                sys.exit(1)

            # Use composite filter
            attempts = attempt_service.filter_attempts(
                run_id=ns.run_id,
                status=WorkflowStatus(ns.status) if ns.status else None,
                conclusion=WorkflowConclusion(ns.conclusion) if ns.conclusion else None,
                duration_min_seconds=ns.duration_min,
                duration_max_seconds=ns.duration_max,
                started_before=started_before,
                started_after=started_after,
                completed_before=completed_before,
                completed_after=completed_after,
            )

            if not attempts:
                print("No attempts found.")
                return
            for attempt in attempts:
                print(_fmt_attempt(attempt))

        elif ns.attempt_command == "detail":
            attempt = attempt_service.get_attempt_detail(ns.attempt_id)
            if attempt is None:
                print(f"No attempt found with id '{ns.attempt_id}'.", file=sys.stderr)
                sys.exit(1)
            print(_fmt_attempt(attempt))

        elif ns.attempt_command == "query-state":
            attempt = attempt_service.get_attempt_detail(ns.attempt_id)
            if attempt is None:
                print(f"No attempt found with id '{ns.attempt_id}'.", file=sys.stderr)
                sys.exit(1)
            print(f"Attempt ID: {attempt.id}")
            print(f"Terminal: {'yes' if attempt.is_terminal() else 'no'}")
            print(f"Running: {'yes' if attempt.is_running() else 'no'}")
            print(f"Successful: {'yes' if attempt.is_successful() else 'no'}")
            print(f"Failed: {'yes' if attempt.is_failed() else 'no'}")
            print(f"Cancelled: {'yes' if attempt.is_cancelled() else 'no'}")

    elif ns.command == "report":
        if stats_service is None:
            print("Statistics service not initialized.", file=sys.stderr)
            sys.exit(1)

        report = stats_service.compute_report()

        if ns.format == "json":
            print(json.dumps(report.to_dict(), indent=2))
        else:  # text format
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

    elif ns.command == "export":
        if portability_service is None:
            print("Data portability service not initialized.", file=sys.stderr)
            sys.exit(1)

        try:
            if ns.export_command == "runs":
                count = portability_service.export_runs(ns.output)
                print(f"Exported {count} run(s) to {ns.output}")
            elif ns.export_command == "attempts":
                count = portability_service.export_attempts(ns.output)
                print(f"Exported {count} attempt(s) to {ns.output}")
        except Exception as e:
            print(f"Error exporting data: {e}", file=sys.stderr)
            sys.exit(1)

    elif ns.command == "import":
        if portability_service is None:
            print("Data portability service not initialized.", file=sys.stderr)
            sys.exit(1)

        try:
            if ns.import_command == "runs":
                result = portability_service.import_runs(ns.input, skip_duplicates=ns.skip_duplicates)
                print(f"Imported {result['successful']} run(s)")
                if result['skipped']:
                    print(f"Skipped {len(result['skipped'])} duplicate run(s)")
                if result['failed'] > 0:
                    print(f"Failed to import {result['failed']} run(s)")
            elif ns.import_command == "attempts":
                result = portability_service.import_attempts(ns.input, skip_duplicates=ns.skip_duplicates)
                print(f"Imported {result['successful']} attempt(s)")
                if result['skipped']:
                    print(f"Skipped {len(result['skipped'])} duplicate attempt(s)")
                if result['failed'] > 0:
                    print(f"Failed to import {result['failed']} attempt(s)")
        except Exception as e:
            print(f"Error importing data: {e}", file=sys.stderr)
            sys.exit(1)
