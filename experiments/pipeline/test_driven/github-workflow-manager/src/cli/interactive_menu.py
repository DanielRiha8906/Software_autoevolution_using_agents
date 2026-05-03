import sys
from typing import Optional
from datetime import datetime

from ..models.workflow_status import WorkflowStatus
from ..models.workflow_conclusion import WorkflowConclusion
from ..models.workflow_run import WorkflowRun
from ..services.workflow_run_service import WorkflowRunService
from ..services.attempt_service import AttemptService
from ..services.workflow_run_tracker import WorkflowRunTracker


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
        f"  id          : {run.id}\n"
        f"  workflow    : {run.workflow_name}\n"
        f"  branch      : {run.branch}\n"
        f"  status      : {run.status.value}\n"
        f"  conclusion  : {conclusion}\n"
        f"  run_number  : {run.run_number or '—'}\n"
        f"  commit_sha  : {run.commit_sha or '—'}\n"
        f"  created_at  : {run.created_at.isoformat()}\n"
        f"  updated_at  : {run.updated_at.isoformat() if run.updated_at else '—'}\n"
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

    run_number = int(run_number_raw) if run_number_raw else None
    conclusion = WorkflowConclusion(conclusion_val) if conclusion_val else None

    run = tracker.track(
        workflow_name=name,
        branch=branch,
        status=WorkflowStatus(status_val),
        conclusion=conclusion,
        run_number=run_number,
        commit_sha=commit_sha,
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


def _filter_menu(service: WorkflowRunService) -> None:
    filter_by = _choose("Filter by", ["branch", "status", "conclusion"])
    if filter_by == "branch":
        branch = _prompt("Branch name")
        runs = service.filter_by_branch(branch)
    elif filter_by == "status":
        status_val = _choose("Status", [s.value for s in WorkflowStatus])
        runs = service.filter_by_status(WorkflowStatus(status_val))
    else:
        conclusion_val = _choose("Conclusion", [c.value for c in WorkflowConclusion])
        runs = service.filter_by_conclusion(WorkflowConclusion(conclusion_val))

    if not runs:
        print("\nNo matching runs.")
        return
    print(f"\n--- {len(runs)} matching run(s) ---")
    for run in runs:
        print(_fmt_run(run))


def _query_runs(service: WorkflowRunService, attempt_service: AttemptService) -> None:
    print("\n--- Query Workflow Runs ---")
    min_duration_raw = _prompt("Min duration (seconds, leave blank for none)", "")
    max_duration_raw = _prompt("Max duration (seconds, leave blank for none)", "")
    created_after_raw = _prompt("Created after (ISO 8601 datetime, leave blank for none)", "")
    created_before_raw = _prompt("Created before (ISO 8601 datetime, leave blank for none)", "")
    has_attempts_raw = _choose(
        "Attempt filter",
        ["No filter", "Has attempts", "No attempts"],
        allow_blank=False,
    )

    try:
        min_duration = float(min_duration_raw) if min_duration_raw else None
        max_duration = float(max_duration_raw) if max_duration_raw else None
        created_after = datetime.fromisoformat(created_after_raw) if created_after_raw else None
        created_before = datetime.fromisoformat(created_before_raw) if created_before_raw else None

        if has_attempts_raw == "Has attempts":
            has_attempts = True
        elif has_attempts_raw == "No attempts":
            has_attempts = False
        else:
            has_attempts = None

        runs = service.query(
            min_duration=min_duration,
            max_duration=max_duration,
            created_after=created_after,
            created_before=created_before,
            has_attempts=has_attempts,
            attempt_service=attempt_service if has_attempts is not None else None,
        )

        if not runs:
            print("\nNo matching runs.")
            return
        print(f"\n--- {len(runs)} matching run(s) ---")
        for run in runs:
            print(_fmt_run(run))
    except ValueError as e:
        print(f"\nQuery error: {e}")
    except TypeError as e:
        print(f"\nQuery error: {e}")


def run_interactive(service: WorkflowRunService, attempt_service: AttemptService = None) -> None:
    if attempt_service is None:
        attempt_service = AttemptService()

    menu = [
        ("Add workflow run", _add_run),
        ("List all runs", _list_runs),
        ("Get run detail", _detail_run),
        ("Filter runs", _filter_menu),
        ("Query runs", lambda svc: _query_runs(svc, attempt_service)),
        ("Exit", None),
    ]
    print("\nGitHub Workflow Tracker — Interactive Menu")
    while True:
        print("\n" + "=" * 44)
        for i, (label, _) in enumerate(menu, 1):
            print(f"  {i}. {label}")
        raw = input("\nSelect option: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(menu)):
            print("Invalid selection.")
            continue
        label, handler = menu[int(raw) - 1]
        if handler is None:
            print("Goodbye.")
            sys.exit(0)
        try:
            handler(service)
        except KeyboardInterrupt:
            print()
