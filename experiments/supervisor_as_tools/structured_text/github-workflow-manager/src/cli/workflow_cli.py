import argparse
import json
import sys
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.attempt_service import AttemptService
from ..services.statistics_service import StatisticsService


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
    conclusion = attempt.conclusion or "—"
    return (
        f"  id              : {attempt.id}\n"
        f"  run_id          : {attempt.run_id}\n"
        f"  attempt_number  : {attempt.attempt_number}\n"
        f"  status          : {attempt.status}\n"
        f"  conclusion      : {conclusion}\n"
        f"  created_at      : {attempt.created_at.isoformat()}\n"
        f"  duration_seconds: {attempt.duration_seconds}\n"
    )


def _fmt_statistics(statistics) -> str:
    """Format WorkflowStatistics for text output."""
    lines = [
        "Workflow Statistics:",
        f"  total_runs                 : {statistics.total_runs}",
        "  count_by_conclusion        :",
    ]
    for conclusion, count in sorted(statistics.count_by_conclusion.items()):
        lines.append(f"    {conclusion}: {count}")
    lines.extend([
        f"  average_duration_seconds   : {statistics.average_duration_seconds:.2f}",
        f"  min_duration_seconds       : {statistics.min_duration_seconds or '—'}",
        f"  max_duration_seconds       : {statistics.max_duration_seconds or '—'}",
        f"  average_attempts_per_run   : {statistics.average_attempts_per_run:.2f}",
    ])
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
    add_p.add_argument(
        "--duration-seconds",
        type=float,
        default=0.0,
        help="Run duration in seconds (default: 0.0, must be non-negative)"
    )

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
    list_p.add_argument("--duration-min", type=float, default=None, help="Minimum duration in seconds")
    list_p.add_argument("--duration-max", type=float, default=None, help="Maximum duration in seconds")
    list_p.add_argument(
        "--created-after",
        type=str,
        default=None,
        help="Filter runs created after this datetime (ISO 8601 format)",
    )
    list_p.add_argument(
        "--created-before",
        type=str,
        default=None,
        help="Filter runs created before this datetime (ISO 8601 format)",
    )
    list_p.add_argument(
        "--updated-after",
        type=str,
        default=None,
        help="Filter runs updated after this datetime (ISO 8601 format)",
    )
    list_p.add_argument(
        "--updated-before",
        type=str,
        default=None,
        help="Filter runs updated before this datetime (ISO 8601 format)",
    )
    list_p.add_argument(
        "--has-attempts",
        action="store_true",
        help="Show only runs with attempts",
    )
    list_p.add_argument(
        "--no-attempts",
        action="store_true",
        help="Show only runs without attempts",
    )

    # detail
    detail_p = sub.add_parser("detail", help="Show details for a single run")
    detail_p.add_argument("run_id", help="Run ID")

    # check-state
    check_state_p = sub.add_parser("check-state", help="Check the state flags of a run")
    check_state_p.add_argument("run_id", help="Run ID")

    # add-attempt
    add_attempt_p = sub.add_parser("add-attempt", help="Add a new workflow run attempt")
    add_attempt_p.add_argument("--run-id", type=int, required=True, help="Run ID")
    add_attempt_p.add_argument("--attempt-number", type=int, required=True, help="Attempt number")
    add_attempt_p.add_argument("--status", required=True, help="Attempt status")
    add_attempt_p.add_argument("--conclusion", default=None, help="Attempt conclusion (optional)")
    add_attempt_p.add_argument(
        "--duration-seconds",
        type=float,
        default=0.0,
        help="Attempt duration in seconds (default: 0.0, must be non-negative)"
    )

    # list-attempts
    list_attempts_p = sub.add_parser("list-attempts", help="List all attempts")
    list_attempts_p.add_argument("--run-id", type=int, default=None, help="Filter by run ID")

    # attempt-detail
    attempt_detail_p = sub.add_parser("attempt-detail", help="Show details for a single attempt")
    attempt_detail_p.add_argument("attempt_id", type=int, help="Attempt ID")

    # stats
    stats_p = sub.add_parser("stats", help="Display workflow statistics")
    stats_p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    return parser


def run_cli(
    service: WorkflowRunService,
    attempt_service: AttemptService,
    statistics_service: StatisticsService,
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
        # Validate and parse datetime flags
        created_after = None
        created_before = None
        updated_after = None
        updated_before = None

        if ns.created_after:
            try:
                created_after = datetime.fromisoformat(ns.created_after)
            except ValueError:
                print(
                    f"Invalid --created-after format: '{ns.created_after}'. Use ISO 8601 format (e.g., 2026-05-03T12:00:00).",
                    file=sys.stderr,
                )
                sys.exit(1)

        if ns.created_before:
            try:
                created_before = datetime.fromisoformat(ns.created_before)
            except ValueError:
                print(
                    f"Invalid --created-before format: '{ns.created_before}'. Use ISO 8601 format (e.g., 2026-05-03T12:00:00).",
                    file=sys.stderr,
                )
                sys.exit(1)

        if ns.updated_after:
            try:
                updated_after = datetime.fromisoformat(ns.updated_after)
            except ValueError:
                print(
                    f"Invalid --updated-after format: '{ns.updated_after}'. Use ISO 8601 format (e.g., 2026-05-03T12:00:00).",
                    file=sys.stderr,
                )
                sys.exit(1)

        if ns.updated_before:
            try:
                updated_before = datetime.fromisoformat(ns.updated_before)
            except ValueError:
                print(
                    f"Invalid --updated-before format: '{ns.updated_before}'. Use ISO 8601 format (e.g., 2026-05-03T12:00:00).",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Validate duration ranges
        if ns.duration_min is not None and ns.duration_min < 0:
            print(
                f"--duration-min must be non-negative, got {ns.duration_min}.",
                file=sys.stderr,
            )
            sys.exit(1)

        if ns.duration_max is not None and ns.duration_max < 0:
            print(
                f"--duration-max must be non-negative, got {ns.duration_max}.",
                file=sys.stderr,
            )
            sys.exit(1)

        if (
            ns.duration_min is not None
            and ns.duration_max is not None
            and ns.duration_min > ns.duration_max
        ):
            print(
                f"--duration-min ({ns.duration_min}) must be <= --duration-max ({ns.duration_max}).",
                file=sys.stderr,
            )
            sys.exit(1)

        # Validate attempts flags
        if ns.has_attempts and ns.no_attempts:
            print(
                "--has-attempts and --no-attempts cannot be used together.",
                file=sys.stderr,
            )
            sys.exit(1)

        has_attempts_filter = None
        if ns.has_attempts:
            has_attempts_filter = True
        elif ns.no_attempts:
            has_attempts_filter = False

        # Call filter_runs with all criteria
        try:
            runs = service.filter_runs(
                attempt_service=attempt_service,
                branch=ns.branch,
                status=WorkflowStatus(ns.status) if ns.status else None,
                conclusion=WorkflowConclusion(ns.conclusion) if ns.conclusion else None,
                min_duration_seconds=ns.duration_min,
                max_duration_seconds=ns.duration_max,
                created_after=created_after,
                created_before=created_before,
                updated_after=updated_after,
                updated_before=updated_before,
                has_attempts=has_attempts_filter,
            )
        except ValueError as e:
            print(f"Filter error: {e}", file=sys.stderr)
            sys.exit(1)

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

    elif ns.command == "check-state":
        run = service.get_run_detail(ns.run_id)
        if run is None:
            print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
            sys.exit(1)
        print(_fmt_run(run))
        print("  State flags:")
        print(f"    is_running  : {run.is_running()}")
        print(f"    is_terminal : {run.is_terminal()}")
        print(f"    is_successful: {run.is_successful()}")
        print(f"    is_failed   : {run.is_failed()}")
        print(f"    is_cancelled: {run.is_cancelled()}")

    elif ns.command == "add-attempt":
        attempt = attempt_service.create_attempt(
            run_id=ns.run_id,
            attempt_number=ns.attempt_number,
            status=ns.status,
            conclusion=ns.conclusion,
            created_at=datetime.now(timezone.utc),
            duration_seconds=ns.duration_seconds,
        )
        print(f"Added attempt {attempt.id}")

    elif ns.command == "list-attempts":
        if ns.run_id is not None:
            attempts = attempt_service.get_attempts_by_run_id(ns.run_id)
        else:
            attempts = attempt_service.list_attempts()

        if not attempts:
            print("No attempts found.")
            return
        for attempt in attempts:
            print(_fmt_attempt(attempt))

    elif ns.command == "attempt-detail":
        attempt = attempt_service.get_attempt_detail(ns.attempt_id)
        if attempt is None:
            print(f"No attempt found with id {ns.attempt_id}.", file=sys.stderr)
            sys.exit(1)
        print(_fmt_attempt(attempt))

    elif ns.command == "stats":
        statistics = statistics_service.compute_statistics()
        if ns.format == "json":
            print(json.dumps(statistics.to_dict(), indent=2))
        else:
            print(_fmt_statistics(statistics))
