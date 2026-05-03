import argparse
import sys
from datetime import datetime, timezone

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
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

    # query
    query_p = sub.add_parser("query", help="Query runs by duration, timestamps, and attempts")
    query_p.add_argument("--min-duration", type=float, default=None, help="Minimum duration in seconds")
    query_p.add_argument("--max-duration", type=float, default=None, help="Maximum duration in seconds")
    query_p.add_argument("--created-after", default=None, help="Created after (ISO 8601 timezone-aware datetime)")
    query_p.add_argument("--created-before", default=None, help="Created before (ISO 8601 timezone-aware datetime)")
    query_p.add_argument(
        "--has-attempts",
        default=None,
        choices=["true", "false"],
        help="Filter by attempt presence (true=has attempts, false=no attempts)",
    )

    return parser


def run_cli(service: WorkflowRunService, attempt_service: AttemptService = None, args=None) -> None:
    if attempt_service is None:
        attempt_service = AttemptService()
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

    elif ns.command == "query":
        created_after = None
        created_before = None
        has_attempts_val = None

        if ns.created_after:
            try:
                created_after = datetime.fromisoformat(ns.created_after)
            except ValueError:
                print(f"Invalid created_after datetime: {ns.created_after}", file=sys.stderr)
                sys.exit(1)

        if ns.created_before:
            try:
                created_before = datetime.fromisoformat(ns.created_before)
            except ValueError:
                print(f"Invalid created_before datetime: {ns.created_before}", file=sys.stderr)
                sys.exit(1)

        if ns.has_attempts:
            has_attempts_val = ns.has_attempts.lower() == "true"

        try:
            runs = service.query(
                min_duration=ns.min_duration,
                max_duration=ns.max_duration,
                created_after=created_after,
                created_before=created_before,
                has_attempts=has_attempts_val,
                attempt_service=attempt_service if has_attempts_val is not None else None,
            )
        except (TypeError, ValueError) as e:
            print(f"Query error: {e}", file=sys.stderr)
            sys.exit(1)

        if not runs:
            print("No runs match the query criteria.")
            return
        print(f"Found {len(runs)} matching run(s):")
        for run in runs:
            print(_fmt_run(run))
