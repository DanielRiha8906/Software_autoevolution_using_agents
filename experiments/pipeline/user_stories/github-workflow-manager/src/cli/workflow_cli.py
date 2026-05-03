import argparse
import sys
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..models.workflow_run_attempt import WorkflowRunAttempt
from ..services.workflow_run_service import WorkflowRunService
from ..services.workflow_run_attempt_service import WorkflowRunAttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker


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

    # attempt detail
    attempt_detail_p = sub.add_parser("attempt-detail", help="Show details for a single attempt")
    attempt_detail_p.add_argument("attempt_id", type=int, help="Attempt ID")

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
        if ns.run_id is not None:
            attempts = attempt_service.get_attempts_for_run(ns.run_id)
        else:
            attempts = attempt_service.list_attempts()

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
