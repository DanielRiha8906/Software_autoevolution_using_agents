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
    return (
        f"  id              : {attempt.id}\n"
        f"  run_id          : {attempt.run_id}\n"
        f"  attempt_number  : {attempt.attempt_number}\n"
        f"  status          : {attempt.status}\n"
        f"  conclusion      : {conclusion}\n"
        f"  created_at      : {attempt.created_at.isoformat()}\n"
        f"  duration_seconds: {attempt.duration_seconds}\n"
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

    # check-state
    check_p = sub.add_parser("check-state", help="Check run state")
    check_p.add_argument("run_id", help="Run ID")
    check_p.add_argument(
        "--check",
        required=True,
        choices=["terminal", "running", "successful", "failed", "cancelled"],
        help="State to check",
    )

    # create-attempt
    create_attempt_p = sub.add_parser("create-attempt", help="Create a new workflow attempt")
    create_attempt_p.add_argument("--run-id", type=int, required=True, help="Run ID")
    create_attempt_p.add_argument("--attempt-number", type=int, required=True, help="Attempt number")
    create_attempt_p.add_argument("--status", required=True, help="Attempt status")
    create_attempt_p.add_argument("--conclusion", default=None, help="Attempt conclusion (optional)")
    create_attempt_p.add_argument("--duration-seconds", type=float, default=0.0, help="Duration in seconds")

    # list-attempts
    list_attempts_p = sub.add_parser("list-attempts", help="List all attempts or attempts for a run")
    list_attempts_p.add_argument("--run-id", type=int, default=None, help="Filter by run ID (optional)")

    return parser


def run_cli(service: WorkflowRunService, attempt_service: AttemptService, args=None) -> None:
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

    elif ns.command == "check-state":
        run = service.get_run_detail(ns.run_id)
        if run is None:
            print(f"No run found with id '{ns.run_id}'.", file=sys.stderr)
            sys.exit(1)

        check_type = ns.check
        if check_type == "terminal":
            result = run.is_terminal()
        elif check_type == "running":
            result = run.is_running()
        elif check_type == "successful":
            result = run.is_successful()
        elif check_type == "failed":
            result = run.is_failed()
        elif check_type == "cancelled":
            result = run.is_cancelled()

        print(f"Run {ns.run_id} is_{check_type}: {result}")
        sys.exit(0 if result else 1)

    elif ns.command == "create-attempt":
        attempt = WorkflowRunAttempt(
            id=0,  # Will be assigned by the service if needed
            run_id=ns.run_id,
            attempt_number=ns.attempt_number,
            status=ns.status,
            conclusion=ns.conclusion,
            created_at=datetime.now(timezone.utc),
            duration_seconds=ns.duration_seconds,
        )
        try:
            attempt_service.add_workflow_attempt(attempt)
            print(f"Added attempt {ns.attempt_number} for run {ns.run_id}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

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
