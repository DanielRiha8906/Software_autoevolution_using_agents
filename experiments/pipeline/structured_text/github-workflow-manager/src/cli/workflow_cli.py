import argparse
import sys
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_attempt_service import WorkflowAttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker


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

    # attempt detail
    attempt_detail_p = attempt_sub.add_parser("detail", help="Show details for a single attempt")
    attempt_detail_p.add_argument("attempt_id", help="Attempt ID")

    # attempt query-state
    attempt_query_p = attempt_sub.add_parser("query-state", help="Query workflow attempt state")
    attempt_query_p.add_argument("attempt_id", help="Attempt ID")

    return parser


def run_cli(service: WorkflowRunService, attempt_service: WorkflowAttemptService = None, args=None) -> None:
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
        runs = service.list_runs()
        if ns.branch:
            runs = service.filter_by_branch(ns.branch)
        elif ns.status:
            runs = service.filter_by_status(WorkflowStatus(ns.status))
        elif ns.conclusion:
            runs = service.filter_by_conclusion(WorkflowConclusion(ns.conclusion))

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
            attempts = attempt_service.list_attempts()
            if ns.run_id:
                attempts = attempt_service.filter_by_run_id(ns.run_id)
            elif ns.status:
                attempts = attempt_service.filter_by_status(WorkflowStatus(ns.status))
            elif ns.conclusion:
                attempts = attempt_service.filter_by_conclusion(WorkflowConclusion(ns.conclusion))

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
