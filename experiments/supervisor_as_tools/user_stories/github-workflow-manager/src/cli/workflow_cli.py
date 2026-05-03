import argparse
import sys
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_attempt_status import WorkflowAttemptStatus
from ..models.workflow_attempt_conclusion import WorkflowAttemptConclusion
from ..models.workflow_run import WorkflowRun
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_tracker import WorkflowRunTracker
from ..services.attempt_service import AttemptService


def _parse_iso8601(timestamp_str: str) -> datetime:
    """Parse ISO 8601 timestamp string to datetime with UTC timezone.

    Args:
        timestamp_str: ISO 8601 formatted string (e.g., "2024-06-01T00:00:00Z")

    Returns:
        datetime object in UTC timezone

    Raises:
        ValueError: If timestamp format is invalid
    """
    # Handle 'Z' suffix by replacing with '+00:00'
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1] + '+00:00'

    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        raise ValueError(f"Invalid ISO 8601 timestamp: {timestamp_str}") from e


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
        f"  duration_seconds : {run.duration_seconds}\n"
    )


def _fmt_status_report(run: WorkflowRun) -> str:
    """Format run status report with state-checking method results."""
    return (
        f"Run Status Report for {run.id}:\n"
        f"  is_terminal: {run.is_terminal()}\n"
        f"  is_running: {run.is_running()}\n"
        f"  is_successful: {run.is_successful()}\n"
        f"  is_failed: {run.is_failed()}\n"
        f"  is_cancelled: {run.is_cancelled()}\n"
    )


def _fmt_attempt(attempt) -> str:
    """Format a single attempt for display."""
    conclusion = attempt.conclusion.value if attempt.conclusion else "—"
    return (
        f"  id               : {attempt.id}\n"
        f"  attempt_number   : {attempt.attempt_number}\n"
        f"  status           : {attempt.status.value}\n"
        f"  conclusion       : {conclusion}\n"
        f"  created_at       : {attempt.created_at.isoformat()}\n"
        f"  duration_seconds : {attempt.duration_seconds or '—'}\n"
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
    add_p.add_argument("--duration-seconds", type=float, default=0.0, help="Duration in seconds")

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
        help="Minimum duration in seconds (inclusive)",
    )
    list_p.add_argument(
        "--duration-max",
        type=float,
        default=None,
        help="Maximum duration in seconds (inclusive)",
    )
    list_p.add_argument(
        "--created-after",
        type=str,
        default=None,
        help="Filter runs created after this ISO 8601 timestamp",
    )
    list_p.add_argument(
        "--created-before",
        type=str,
        default=None,
        help="Filter runs created before this ISO 8601 timestamp",
    )
    list_p.add_argument(
        "--updated-after",
        type=str,
        default=None,
        help="Filter runs updated after this ISO 8601 timestamp",
    )
    list_p.add_argument(
        "--updated-before",
        type=str,
        default=None,
        help="Filter runs updated before this ISO 8601 timestamp",
    )
    list_p.add_argument(
        "--has-attempts",
        action="store_true",
        help="Filter to only show runs with attempts",
    )

    # detail
    detail_p = sub.add_parser("detail", help="Show details for a single run")
    detail_p.add_argument("run_id", help="Run ID")

    # status
    status_p = sub.add_parser("status", help="Check run status")
    status_p.add_argument("--id", dest="run_id", required=True, help="Run ID")

    # attempt
    attempt_p = sub.add_parser("attempt", help="Manage workflow run attempts")
    attempt_sub = attempt_p.add_subparsers(dest="attempt_command", required=True)

    # attempt create
    attempt_create = attempt_sub.add_parser("create", help="Create a new attempt for a run")
    attempt_create.add_argument("--run-id", required=True, help="Run ID")
    attempt_create.add_argument("--attempt-number", type=int, required=True, help="Attempt number")
    attempt_create.add_argument(
        "--status",
        required=True,
        choices=[s.value for s in WorkflowAttemptStatus],
        help="Attempt status",
    )
    attempt_create.add_argument(
        "--conclusion",
        default=None,
        choices=[c.value for c in WorkflowAttemptConclusion],
        help="Attempt conclusion (optional)",
    )
    attempt_create.add_argument("--duration-seconds", type=float, default=None, help="Duration in seconds")
    attempt_create.add_argument("--id", type=int, default=0, help="Attempt ID (auto-generated if omitted)")

    # attempt list
    attempt_list = attempt_sub.add_parser("list", help="List attempts for a run")
    attempt_list.add_argument("--run-id", required=True, help="Run ID")
    attempt_list.add_argument("--sort", action="store_true", help="Sort by attempt_number ascending")

    return parser


def run_cli(service: WorkflowRunService, args=None) -> None:
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
        # Build kwargs dict for filter_runs()
        filter_kwargs = {}

        if ns.branch is not None:
            filter_kwargs["branch"] = ns.branch

        if ns.status is not None:
            filter_kwargs["status"] = WorkflowStatus(ns.status)

        if ns.conclusion is not None:
            filter_kwargs["conclusion"] = WorkflowConclusion(ns.conclusion)

        if ns.duration_min is not None:
            filter_kwargs["duration_min"] = ns.duration_min

        if ns.duration_max is not None:
            filter_kwargs["duration_max"] = ns.duration_max

        if ns.created_after is not None:
            try:
                filter_kwargs["created_after"] = _parse_iso8601(ns.created_after)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        if ns.created_before is not None:
            try:
                filter_kwargs["created_before"] = _parse_iso8601(ns.created_before)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        if ns.updated_after is not None:
            try:
                filter_kwargs["updated_after"] = _parse_iso8601(ns.updated_after)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        if ns.updated_before is not None:
            try:
                filter_kwargs["updated_before"] = _parse_iso8601(ns.updated_before)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        if ns.has_attempts:
            filter_kwargs["has_attempts"] = True

        runs = service.filter_runs(**filter_kwargs)

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

    elif ns.command == "status":
        run = service.get_run_detail(ns.run_id)
        if run is None:
            print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
            sys.exit(1)
        print(_fmt_status_report(run))

    elif ns.command == "attempt":
        attempt_service = AttemptService(service)

        if ns.attempt_command == "create":
            attempt_data = {
                "id": ns.id,
                "run_id": ns.run_id,
                "attempt_number": ns.attempt_number,
                "status": ns.status,
                "conclusion": ns.conclusion,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": ns.duration_seconds,
            }
            try:
                attempt = attempt_service.create_attempt(ns.run_id, attempt_data)
                print(f"Added attempt {attempt.attempt_number} to run {ns.run_id}")
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        elif ns.attempt_command == "list":
            try:
                attempts = attempt_service.get_attempts_by_run(ns.run_id, sort_by_number=ns.sort)
                if not attempts:
                    print(f"No attempts found for run '{ns.run_id}'.")
                    return
                print(f"\n--- {len(attempts)} attempt(s) for run {ns.run_id} ---")
                for attempt in attempts:
                    print(_fmt_attempt(attempt))
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
